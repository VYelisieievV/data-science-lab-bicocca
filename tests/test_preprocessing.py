from pathlib import Path

import duckdb
import polars as pl
import pytest
from preprocessing import (
    OUTPUT_COLUMNS,
    PreprocessingError,
    add_lags_and_leads,
    aggregate_governing_parties,
    filter_governing_parties,
    forward_fill_election_years,
    run,
    validate_panel,
    validate_required_columns,
)


def _vparty_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "country_id": [1, 1, 2, 2, 3],
            "year": [2000, 2000, 2000, 2000, 2000],
            "country_name": ["A", "A", "B", "B", "C"],
            "v2paenname": ["Alpha", "Beta", "Delta", "Gamma", "Opposition"],
            "v2pagovsup": [0, 0, 0, 0, 3],
            "v2xpa_popul": [0.2, 0.8, 0.3, 0.7, 0.9],
            "v2pavote": [25.0, 75.0, None, 60.0, 90.0],
            "v2paanteli_nr": [4, 5, 4, 4, 5],
            "v2papeople_nr": [4, 5, 4, 3, 5],
        }
    )


def test_filter_and_coalition_aggregation() -> None:
    filtered = filter_governing_parties(_vparty_frame())
    assert filtered["v2paenname"].to_list() == ["Alpha", "Beta", "Delta"]

    aggregated = aggregate_governing_parties(filtered).sort("country_id")
    assert aggregated["populism_governing"].to_list() == pytest.approx([0.65, 0.3])
    assert aggregated["party_names"].to_list() == ["Alpha / Beta", "Delta"]


def test_coalition_falls_back_to_simple_mean_when_a_vote_is_missing() -> None:
    governing = (
        _vparty_frame()
        .filter(pl.col("country_id") == 2)
        .with_columns(pl.lit(4).alias("v2papeople_nr"))
    )
    aggregated = aggregate_governing_parties(filter_governing_parties(governing))
    assert aggregated.item(0, "populism_governing") == pytest.approx(0.5)


def test_forward_fill_starts_at_first_observation() -> None:
    governing = pl.DataFrame(
        {
            "country_id": [1, 1],
            "year": [2001, 2003],
            "country_name": ["A", "A"],
            "party_names": ["Alpha", "Beta"],
            "n_senior_gov_parties": [1, 1],
            "populism_governing": [0.2, 0.8],
        }
    )
    panel = forward_fill_election_years(governing, 2000, 2004)

    assert panel["year"].to_list() == [2001, 2002, 2003, 2004]
    assert panel["populism_governing"].to_list() == [0.2, 0.2, 0.8, 0.8]
    assert panel["is_election_year"].to_list() == [True, False, True, False]
    assert panel["years_since_last_election"].to_list() == [0, 1, 0, 1]


def test_lags_and_leads_follow_annual_rows() -> None:
    # Use only the non-lag/lead base columns so the test is not sensitive to
    # the order or count of columns in OUTPUT_COLUMNS.
    base_cols = [
        c
        for c in OUTPUT_COLUMNS
        if not any(c.endswith(f"_lag{k}") for k in (1, 2, 3, 5))
        and not any(c.endswith(f"_lead{k}") for k in (1, 2, 3))
    ]
    panel = pl.DataFrame(
        {
            column: (
                [1] * 6
                if column == "country_id"
                else list(range(2000, 2006))
                if column == "year"
                else [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
                if column == "populism_governing"
                else [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
                if column == "v2x_corr"
                else [None] * 6
            )
            for column in base_cols
        },
        schema_overrides={"country_name": pl.String, "party_names": pl.String},
    )
    result = add_lags_and_leads(panel)

    assert result.columns == OUTPUT_COLUMNS
    assert result.item(5, "populism_governing_lag5") == pytest.approx(0.1)
    assert result.item(0, "populism_governing_lead3") == pytest.approx(0.4)
    assert result.item(2, "v2x_corr_lag2") == pytest.approx(1.0)


def test_validate_panel_rejects_duplicate_keys_and_year_gaps() -> None:
    with pytest.raises(PreprocessingError, match="empty"):
        validate_panel(pl.DataFrame({"country_id": [], "year": []}))

    with pytest.raises(PreprocessingError, match="duplicate"):
        validate_panel(pl.DataFrame({"country_id": [1, 1], "year": [2000, 2000]}))

    with pytest.raises(PreprocessingError, match="gaps"):
        validate_panel(pl.DataFrame({"country_id": [1, 1], "year": [2000, 2002]}))


def test_missing_database_and_columns_have_clear_errors(tmp_path: Path) -> None:
    with pytest.raises(PreprocessingError, match="does not exist"):
        run(tmp_path / "missing.duckdb", tmp_path / "output")

    database = tmp_path / "incomplete.duckdb"
    connection = duckdb.connect(str(database))
    connection.execute("CREATE SCHEMA raw")
    connection.execute("CREATE TABLE raw.example (country_id INTEGER)")
    with pytest.raises(PreprocessingError, match="Required table"):
        validate_required_columns(connection, "raw.missing", {"country_id"})
    with pytest.raises(PreprocessingError, match="missing required columns: year"):
        validate_required_columns(connection, "raw.example", {"country_id", "year"})
    connection.close()
