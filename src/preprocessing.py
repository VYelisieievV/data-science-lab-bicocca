"""Reproduce the regression-ready panel built in notebook 02.

The notebook remains the explanatory record. This script is the deterministic,
testable entry point for rebuilding its processed data artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import duckdb
import polars as pl

ANALYSIS_START_YEAR = 1970
ANALYSIS_END_YEAR = 2019
LAG_YEARS = (1, 2, 3, 5)
LEAD_YEARS = (1, 2, 3)

VPARTY_TABLE = "raw.vparty_country_party_date"
VDEM_TABLE = "raw.vdem_country_year"

VPARTY_COLUMNS = {
    "country_id",
    "year",
    "country_name",
    "v2paenname",
    "v2pagovsup",
    "v2xpa_popul",
    "v2pavote",
    "v2paanteli_nr",
    "v2papeople_nr",
}
VDEM_COLUMNS = {
    "country_id",
    "year",
    "country_name",
    "v2x_corr",
    "v2x_execorr",
    "v2x_pubcorr",
    "v2lgcrrpt",
    "v2jucorrdc",
    "e_gdppc",
    "v2x_polyarchy",
    "e_regiongeo",
    "e_pop",
}

OUTPUT_COLUMNS = [
    "country_id",
    "year",
    "country_name",
    "party_names",
    "n_senior_gov_parties",
    "populism_governing",
    "is_election_year",
    "years_since_last_election",
    "v2x_corr",
    "v2x_execorr",
    "v2x_pubcorr",
    "v2lgcrrpt",
    "v2jucorrdc",
    "e_gdppc",
    "v2x_polyarchy",
    "e_regiongeo",
    "e_pop",
    "log_gdppc",
    *[column for k in LAG_YEARS for column in (f"populism_governing_lag{k}", f"v2x_corr_lag{k}")],
    *[f"populism_governing_lead{k}" for k in LEAD_YEARS],
]


class PreprocessingError(RuntimeError):
    """Raised when input data cannot produce a valid analysis panel."""


def _qualified_table_parts(table: str) -> tuple[str, str]:
    schema, name = table.split(".", maxsplit=1)
    return schema, name


def validate_required_columns(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    required_columns: set[str],
) -> None:
    """Raise a readable error when a required table or column is absent."""
    schema, name = _qualified_table_parts(table)
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, name],
    ).fetchall()
    if not rows:
        raise PreprocessingError(f"Required table {table!r} was not found in the DuckDB database")

    available = {row[0] for row in rows}
    missing = sorted(required_columns - available)
    if missing:
        raise PreprocessingError(
            f"Table {table!r} is missing required columns: {', '.join(missing)}"
        )


def filter_governing_parties(vparty: pl.DataFrame) -> pl.DataFrame:
    """Apply notebook 02's senior-government and strict coder-count filters."""
    return vparty.filter(
        (pl.col("v2pagovsup") == 0)
        & pl.col("v2xpa_popul").is_not_null()
        & (pl.col("v2paanteli_nr") > 3)
        & (pl.col("v2papeople_nr") > 3)
    )


def aggregate_governing_parties(governing: pl.DataFrame) -> pl.DataFrame:
    """Collapse senior governing parties to one country-year populism score."""
    return (
        governing.group_by(["country_id", "year"])
        .agg(
            pl.col("country_name").first(),
            pl.col("v2paenname").sort().str.join(" / ").alias("party_names"),
            pl.len().alias("n_senior_gov_parties"),
            pl.col("v2xpa_popul").mean().alias("_popul_simple_mean"),
            pl.col("v2pavote").null_count().alias("_n_null_vote"),
            pl.col("v2pavote").sum().alias("_vote_sum"),
            (pl.col("v2xpa_popul") * pl.col("v2pavote")).sum().alias("_weighted_num"),
        )
        .with_columns(
            pl.when((pl.col("_n_null_vote") == 0) & (pl.col("_vote_sum") > 0))
            .then(pl.col("_weighted_num") / pl.col("_vote_sum"))
            .otherwise(pl.col("_popul_simple_mean"))
            .alias("populism_governing")
        )
        .select(
            "country_id",
            "year",
            "country_name",
            "party_names",
            "n_senior_gov_parties",
            "populism_governing",
        )
        .sort(["country_id", "year"])
    )


def forward_fill_election_years(
    governing: pl.DataFrame,
    start_year: int = ANALYSIS_START_YEAR,
    end_year: int = ANALYSIS_END_YEAR,
) -> pl.DataFrame:
    """Expand election observations annually without filling before the first observation."""
    year_grid = pl.DataFrame({"year": range(start_year, end_year + 1)})
    full_grid = governing.select("country_id").unique().join(year_grid, how="cross")

    return (
        full_grid.join(governing, on=["country_id", "year"], how="left")
        .sort(["country_id", "year"])
        .with_columns(pl.col("populism_governing").is_not_null().alias("is_election_year"))
        .with_columns(
            pl.when(pl.col("is_election_year")).then(pl.col("year")).alias("_last_election_year")
        )
        .with_columns(
            pl.col("populism_governing").forward_fill().over("country_id"),
            pl.col("party_names").forward_fill().over("country_id"),
            pl.col("n_senior_gov_parties").forward_fill().over("country_id"),
            pl.col("country_name").forward_fill().over("country_id"),
            pl.col("_last_election_year").forward_fill().over("country_id"),
        )
        .with_columns(
            (pl.col("year") - pl.col("_last_election_year")).alias("years_since_last_election")
        )
        .drop("_last_election_year")
        .filter(pl.col("populism_governing").is_not_null())
    )


def join_vdem(populism_panel: pl.DataFrame, vdem: pl.DataFrame) -> pl.DataFrame:
    """Inner-join V-Dem outcomes and controls, matching notebook 02."""
    return (
        populism_panel.join(
            vdem.rename({"country_name": "country_name_vdem"}),
            on=["country_id", "year"],
            how="inner",
        )
        .with_columns(
            pl.col("e_gdppc").log().alias("log_gdppc"),
            pl.col("country_name_vdem").alias("country_name"),
        )
        .drop("country_name_vdem")
        .sort(["country_id", "year"])
    )


def validate_panel(panel: pl.DataFrame) -> None:
    """Ensure shifts correspond to calendar years and keys are model-safe."""
    if panel.is_empty():
        raise PreprocessingError("Panel is empty after filtering and joining the input tables")

    duplicate_count = panel.select(pl.struct(["country_id", "year"]).is_duplicated().sum()).item()
    if duplicate_count:
        raise PreprocessingError(
            f"Panel contains {duplicate_count} rows with duplicate country-year keys"
        )

    max_gap = (
        panel.sort(["country_id", "year"])
        .group_by("country_id")
        .agg(pl.col("year").diff().drop_nulls().max().alias("max_gap"))
        .select(pl.col("max_gap").max())
        .item()
    )
    if max_gap is not None and max_gap != 1:
        raise PreprocessingError(
            "Panel contains gaps within country histories; row shifts would not equal calendar lags"
        )


def add_lags_and_leads(panel: pl.DataFrame) -> pl.DataFrame:
    """Add the lag and lead columns used by the planned direction analysis."""
    panel = panel.sort(["country_id", "year"])
    for years in LAG_YEARS:
        panel = panel.with_columns(
            pl.col("populism_governing")
            .shift(years)
            .over("country_id")
            .alias(f"populism_governing_lag{years}"),
            pl.col("v2x_corr").shift(years).over("country_id").alias(f"v2x_corr_lag{years}"),
        )
    for years in LEAD_YEARS:
        panel = panel.with_columns(
            pl.col("populism_governing")
            .shift(-years)
            .over("country_id")
            .alias(f"populism_governing_lead{years}")
        )
    return panel.select(OUTPUT_COLUMNS)


def build_panel(connection: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """Build the complete regression-ready panel from validated DuckDB inputs."""
    validate_required_columns(connection, VPARTY_TABLE, VPARTY_COLUMNS)
    validate_required_columns(connection, VDEM_TABLE, VDEM_COLUMNS)

    vparty = pl.read_database(
        f"""
        SELECT {", ".join(sorted(VPARTY_COLUMNS))}
        FROM {VPARTY_TABLE}
        WHERE year BETWEEN {ANALYSIS_START_YEAR} AND {ANALYSIS_END_YEAR}
        """,
        connection,
    )
    vdem = pl.read_database(
        f"""
        SELECT {", ".join(sorted(VDEM_COLUMNS))}
        FROM {VDEM_TABLE}
        WHERE year BETWEEN {ANALYSIS_START_YEAR} AND {ANALYSIS_END_YEAR}
        """,
        connection,
    )

    governing = aggregate_governing_parties(filter_governing_parties(vparty))
    populism_panel = forward_fill_election_years(governing)
    panel = join_vdem(populism_panel, vdem)
    validate_panel(panel)
    return add_lags_and_leads(panel)


def run(db_path: Path, output_dir: Path) -> pl.DataFrame:
    """Build, validate, and write the parquet plus 100-row CSV preview."""
    if not db_path.is_file():
        raise PreprocessingError(f"DuckDB database does not exist: {db_path}")

    try:
        connection = duckdb.connect(str(db_path), read_only=True)
    except duckdb.Error as error:
        raise PreprocessingError(f"Could not open DuckDB database {db_path}: {error}") from error

    try:
        panel = build_panel(connection)
    finally:
        connection.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(output_dir / "panel_populism_corruption.parquet")
    panel.head(100).write_csv(output_dir / "panel_preview.csv")
    return panel


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/duckdb/vdem.duckdb"),
        help="DuckDB database containing the raw V-Dem tables",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for the parquet panel and CSV preview",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        panel = run(args.db_path, args.output_dir)
    except PreprocessingError as error:
        raise SystemExit(f"preprocessing failed: {error}") from error

    print(
        "wrote regression-ready panel: "
        f"{panel.height} rows, {panel['country_id'].n_unique()} countries, "
        f"{panel['year'].min()}-{panel['year'].max()}, {panel.width} columns"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
