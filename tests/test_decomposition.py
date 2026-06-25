from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from decomposition import (
    OUTCOME_BY_KEY,
    add_panel_shifts,
    association_results_table,
    benjamini_hochberg,
    direction_results_tables,
    fit_association_models,
    fit_association_robustness,
    fit_direction_models,
    fit_measurement_robustness,
    outcome_diagnostics,
    prepare_panel,
    validate_panel,
)


@pytest.fixture
def synthetic_decomposition_panel() -> pd.DataFrame:
    rng = np.random.default_rng(20260624)
    rows = []
    for country_id in range(1, 13):
        country_effect = rng.normal(scale=0.15)
        populism_previous = rng.uniform(0.15, 0.75)
        corruption_previous = 0.25 + country_effect
        for year in range(2000, 2018):
            populism = np.clip(0.35 * populism_previous + rng.uniform(0.0, 0.65), 0, 1)
            corruption = (
                0.25 * corruption_previous
                + 0.55 * populism_previous
                + country_effect
                + 0.004 * (year - 2000)
                + rng.normal(scale=0.025)
            )
            executive = corruption + rng.normal(scale=0.02)
            public = 0.85 * corruption + rng.normal(scale=0.02)
            legislative_oriented = 1.15 * corruption + rng.normal(scale=0.025)
            judicial_oriented = 0.95 * corruption + rng.normal(scale=0.02)
            rows.append(
                {
                    "country_id": country_id,
                    "year": year,
                    "country_name": f"Country {country_id}",
                    "populism_governing": populism,
                    "log_gdppc": 8.0 + 0.02 * (year - 2000) + rng.normal(scale=0.04),
                    "v2x_polyarchy": np.clip(
                        0.65 - 0.05 * country_effect + rng.normal(0, 0.03), 0, 1
                    ),
                    "is_election_year": (year - 2000) % 4 == 0,
                    "years_since_last_election": (year - 2000) % 4,
                    "v2x_corr": corruption,
                    "v2x_execorr": executive,
                    "v2x_pubcorr": public,
                    # Source latent estimates increase with cleanliness, hence the minus sign.
                    "v2lgcrrpt": -legislative_oriented,
                    "v2jucorrdc": -judicial_oriented,
                    "v2lgcrrpt_01": np.clip(np.round(legislative_oriented * 4) / 4, 0, 1),
                    "v2jucorrdc_01": np.clip(np.round(judicial_oriented * 4) / 4, 0, 1),
                }
            )
            populism_previous = populism
            corruption_previous = corruption
    return pd.DataFrame(rows)


def test_prepare_panel_uses_continuous_outcomes_and_harmonises_orientation(
    synthetic_decomposition_panel,
):
    prepared = prepare_panel(synthetic_decomposition_panel)
    assert OUTCOME_BY_KEY["legislative"].source_column == "v2lgcrrpt"
    assert OUTCOME_BY_KEY["judicial"].source_column == "v2jucorrdc"
    assert OUTCOME_BY_KEY["legislative"].descriptive_column == "v2lgcrrpt_01"
    assert prepared["corruption_legislative"].equals(-prepared["v2lgcrrpt"])
    assert prepared["corruption_judicial"].equals(-prepared["v2jucorrdc"])
    assert prepared["corruption_legislative"].nunique() > prepared["v2lgcrrpt_01"].nunique()


def test_validate_panel_rejects_duplicate_country_year(synthetic_decomposition_panel):
    duplicated = pd.concat(
        [synthetic_decomposition_panel, synthetic_decomposition_panel.iloc[[0]]], ignore_index=True
    )
    with pytest.raises(ValueError, match="duplicate"):
        validate_panel(duplicated)


def test_shifts_never_cross_country_boundaries(synthetic_decomposition_panel):
    prepared = prepare_panel(synthetic_decomposition_panel)
    shifted = add_panel_shifts(prepared, variables=("populism_governing",), lags=(1,), leads=(1,))
    first_rows = shifted.groupby("country_id", sort=False).head(1)
    last_rows = shifted.groupby("country_id", sort=False).tail(1)
    assert first_rows["populism_governing_lag1"].isna().all()
    assert last_rows["populism_governing_lead1"].isna().all()


def test_diagnostics_report_continuous_resolution(synthetic_decomposition_panel):
    diagnostics = outcome_diagnostics(synthetic_decomposition_panel).set_index("outcome_key")
    assert diagnostics.loc["legislative", "n_unique_values"] > 5
    assert diagnostics.loc["judicial", "n_unique_values"] > 5
    assert (diagnostics["within_sd"] > 0).all()
    assert (diagnostics["lag1_autocorrelation"].between(-1, 1)).all()


def test_association_grid_uses_frozen_samples_and_recovers_positive_sign(
    synthetic_decomposition_panel,
):
    panel = synthetic_decomposition_panel.copy()
    panel.loc[panel.index[:8], "v2lgcrrpt"] = np.nan
    specific = fit_association_models(panel, "outcome_specific")
    common = fit_association_models(panel, "common")
    table = association_results_table([*specific, *common])

    for (_, sample_mode, outcome), group in table.groupby(
        ["sample_mode", "outcome_key", "outcome"], observed=True
    ):
        assert group["n_obs"].nunique() == 1, (sample_mode, outcome)

    common_n = table[table["sample_mode"] == "common"].groupby("outcome_key")["n_obs"].first()
    assert common_n.nunique() == 1
    m3 = table[(table["model"] == "M3") & (table["sample_mode"] == "outcome_specific")]
    assert (m3["coefficient"] > 0).all()


def test_granger_models_include_own_history_and_recover_forward_signal(
    synthetic_decomposition_panel,
):
    fits = fit_direction_models(synthetic_decomposition_panel, lag_order=2)
    models, terms = direction_results_tables(fits)
    target = models[
        (models["outcome_key"] == "composite")
        & (models["direction"] == "populism_to_corruption")
        & (models["model"] == "granger")
    ].iloc[0]
    assert target["joint_df"] == 2
    target_terms = terms[
        (terms["outcome_key"] == "composite")
        & (terms["direction"] == "populism_to_corruption")
        & (terms["model"] == "granger")
    ]
    assert set(target_terms["lag"]) == {1, 2}
    assert target_terms.loc[target_terms["lag"] == 1, "coefficient"].item() > 0


def test_benjamini_hochberg_is_monotone_and_preserves_nan():
    raw = pd.Series([0.01, 0.04, 0.03, np.nan, 0.20])
    adjusted = benjamini_hochberg(raw)
    assert adjusted[:3] == pytest.approx([0.04, 0.0533333333, 0.0533333333])
    assert np.isnan(adjusted[3])
    assert adjusted[4] == pytest.approx(0.20)
    assert np.all(adjusted[np.isfinite(adjusted)] >= raw[np.isfinite(raw)])


def test_association_robustness_covers_covariance_and_measurement_choices(
    synthetic_decomposition_panel,
):
    robustness = fit_association_robustness(synthetic_decomposition_panel)
    assert set(robustness["estimator"]) == {
        "cluster_country",
        "cluster_country_year",
        "driscoll_kraay",
        "first_difference",
    }
    assert robustness.groupby("outcome_key")["estimator"].nunique().eq(4).all()

    measurement = fit_measurement_robustness(synthetic_decomposition_panel)
    assert set(measurement["measure"]) == {
        "continuous_latent_primary",
        "five_level_ordinal_01",
    }
    assert set(measurement["outcome_key"]) == {"legislative", "judicial"}
    assert measurement.groupby("outcome_key")["n_obs"].nunique().eq(1).all()
