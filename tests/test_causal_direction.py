"""Tests for the causal-direction module.

Synthetic panels let us check the mechanics without depending on the real parquet: lags must
respect country boundaries, duplicate panels must fail loudly, and a known lagged effect should
come back with the expected sign.
"""

import numpy as np
import pandas as pd
import pytest

from causal_direction import (
    CORRUPTION,
    POPULISM,
    corruption_shock_events,
    democracy_interaction_table,
    democracy_split_robustness,
    ensure_panel_lags,
    event_study_results_table,
    first_difference_results_table,
    fit_corruption_shock_event_study,
    fit_democracy_interaction,
    fit_electoral_sample_robustness,
    fit_event_study,
    fit_first_difference_direction,
    fit_granger_style,
    fit_lead_lag,
    fit_placebo_lead_test,
    granger_results_table,
    lag_order_information_criteria,
    lead_lag_results_table,
    placebo_results_table,
    populist_entry_events,
    validate_panel,
)


@pytest.fixture
def synthetic_direction_panel() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for cid in range(35):
        country_baseline = rng.normal(0, 0.15)
        pop_prev = rng.uniform(0.15, 0.75)
        corr_prev = 0.35 + country_baseline + rng.normal(0, 0.04)
        for offset, year in enumerate(range(1980, 2008)):
            pop = np.clip(0.65 * pop_prev + rng.normal(0, 0.08), 0, 1)
            # Known data-generating process: lagged populism increases current corruption.
            corr = np.clip(
                0.55 * corr_prev + 0.22 * pop_prev + country_baseline + rng.normal(0, 0.03),
                0,
                1,
            )
            rows.append(
                {
                    "country_id": cid,
                    "country_name": f"C{cid}",
                    "year": year,
                    POPULISM: pop,
                    CORRUPTION: corr,
                    "log_gdppc": 8 + rng.normal(0, 0.1),
                    "v2x_polyarchy": np.clip(0.5 + rng.normal(0, 0.1), 0, 1),
                    "years_since_last_election": offset % 4,
                }
            )
            pop_prev = pop
            corr_prev = corr
    return ensure_panel_lags(pd.DataFrame(rows))


@pytest.fixture
def synthetic_event_panel() -> pd.DataFrame:
    rows = []
    for cid in range(18):
        baseline = 0.25 + 0.01 * cid
        for year in range(1995, 2010):
            event_year = 2002 if cid < 9 else 2004
            pre_pop = 0.22 + 0.01 * (cid % 4)
            post_pop = 0.62 + 0.01 * (cid % 5)
            pop = pre_pop if year < event_year else post_pop
            event_time = year - event_year
            corr = baseline + 0.015 * max(event_time, 0) + 0.002 * (year - 1995)
            rows.append(
                {
                    "country_id": cid,
                    "country_name": f"E{cid}",
                    "year": year,
                    POPULISM: pop,
                    CORRUPTION: corr,
                    "log_gdppc": 8 + 0.01 * (year - 1995),
                    "v2x_polyarchy": 0.35 + 0.03 * (cid % 8),
                    "years_since_last_election": (year - event_year) % 4,
                    "is_election_year": year == event_year or (year - 1995) % 4 == 0,
                }
            )
    return ensure_panel_lags(pd.DataFrame(rows), leads=(1, 2))


def test_lags_are_computed_within_country_boundaries():
    df = pd.DataFrame(
        [
            {"country_id": 1, "country_name": "A", "year": 2000, POPULISM: 0.1, CORRUPTION: 0.2},
            {"country_id": 1, "country_name": "A", "year": 2001, POPULISM: 0.3, CORRUPTION: 0.4},
            {"country_id": 2, "country_name": "B", "year": 2000, POPULISM: 0.8, CORRUPTION: 0.7},
        ]
    )
    out = ensure_panel_lags(df, variables=(POPULISM,), lags=(1,))
    first_country_2 = out[(out["country_id"] == 2) & (out["year"] == 2000)].iloc[0]
    assert np.isnan(first_country_2[f"{POPULISM}_lag1"])
    country_1_2001 = out[(out["country_id"] == 1) & (out["year"] == 2001)].iloc[0]
    assert country_1_2001[f"{POPULISM}_lag1"] == pytest.approx(0.1)


def test_validate_panel_rejects_duplicate_country_year(synthetic_direction_panel):
    duplicate = pd.concat([synthetic_direction_panel, synthetic_direction_panel.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate country-year"):
        validate_panel(duplicate)


def test_lead_lag_recovers_known_populism_to_corruption_sign(synthetic_direction_panel):
    fit = fit_lead_lag(
        synthetic_direction_panel,
        direction="populism_to_corruption",
        lag_order=1,
        controls=(),
    )
    coef = fit.result.params[f"{POPULISM}_lag1"]
    assert coef > 0
    table = lead_lag_results_table([fit])
    assert {"coef_lag1", "p_lag1", "n_obs", "n_countries"} <= set(table.columns)


def test_granger_style_includes_own_lags_and_cause_lags(synthetic_direction_panel):
    fit = fit_granger_style(
        synthetic_direction_panel,
        direction="populism_to_corruption",
        lag_order=2,
        controls=(),
    )
    assert fit.own_lag_terms == (f"{CORRUPTION}_lag1", f"{CORRUPTION}_lag2")
    assert fit.cause_terms == (f"{POPULISM}_lag1", f"{POPULISM}_lag2")
    table = granger_results_table([fit])
    assert {"joint_test_stat", "joint_test_p", "joint_df"} <= set(table.columns)
    assert table.loc[0, "joint_df"] == 2


def test_placebo_lead_test_reports_future_terms(synthetic_direction_panel):
    fit = fit_placebo_lead_test(
        synthetic_direction_panel,
        lag_order=2,
        lead_order=2,
        controls=(),
    )
    table = placebo_results_table(fit)
    assert set(table["term_type"]) == {"lag", "lead_placebo"}
    assert {"lead_joint_p", "placebo_warning"} <= set(table.columns)
    assert fit.lead_terms == (f"{POPULISM}_lead1", f"{POPULISM}_lead2")

    reverse = fit_placebo_lead_test(
        synthetic_direction_panel,
        direction="corruption_to_populism",
        lag_order=1,
        lead_order=1,
        controls=(),
    )
    reverse_table = placebo_results_table(reverse)
    assert reverse.dependent == POPULISM
    assert reverse.proposed_cause == CORRUPTION
    assert set(reverse_table["direction"]) == {"corruption_to_populism"}


def test_event_study_detects_populist_entry_events(synthetic_event_panel):
    events = populist_entry_events(synthetic_event_panel, min_increase=0.10, min_level=0.50)
    assert events["country_id"].nunique() == synthetic_event_panel["country_id"].nunique()
    fit = fit_event_study(
        synthetic_event_panel,
        window=(-3, 3),
        min_increase=0.10,
        min_level=0.50,
        controls=(),
    )
    table = event_study_results_table(fit)
    assert -1 in set(table["event_time"])
    assert table.loc[table["event_time"].eq(-1), "reference"].iloc[0]
    assert {"pretrend_joint_p", "post_joint_p", "n_events"} <= set(table.columns)


def test_corruption_shock_event_study_detects_reverse_events(synthetic_event_panel):
    events = corruption_shock_events(synthetic_event_panel, min_increase=0.01)
    assert not events.empty
    fit = fit_corruption_shock_event_study(
        synthetic_event_panel,
        window=(-2, 2),
        min_increase=0.01,
        controls=(),
    )
    table = event_study_results_table(fit)
    assert fit.direction == "corruption_to_populism"
    assert fit.dependent == POPULISM
    assert {"pretrend_joint_p", "post_joint_p", "outcome"} <= set(table.columns)


def test_electoral_sample_robustness_has_requested_samples(synthetic_event_panel):
    table = fit_electoral_sample_robustness(
        synthetic_event_panel,
        direction="populism_to_corruption",
        lag_order=1,
        controls=(),
        samples=("all", "election_years", "government_change_years", "ffill_le5"),
    )
    assert set(table["sample"]) == {"all", "election_years", "government_change_years", "ffill_le5"}
    assert {"coef_lag1", "p_lag1", "n_obs", "error"} <= set(table.columns)


def test_first_difference_direction_returns_delta_model(synthetic_direction_panel):
    fit = fit_first_difference_direction(
        synthetic_direction_panel,
        direction="populism_to_corruption",
        controls=(),
    )
    table = first_difference_results_table([fit])
    assert fit.dependent_delta == f"delta_{CORRUPTION}"
    assert fit.cause_delta_lag == f"delta_{POPULISM}_lag1"
    assert {"coef", "p", "n_countries"} <= set(table.columns)


def test_lag_order_information_criteria_compares_lags(synthetic_direction_panel):
    table = lag_order_information_criteria(
        synthetic_direction_panel,
        direction="populism_to_corruption",
        max_lag=3,
        model_type="granger",
        controls=(),
    )
    assert list(table["lag_order"]) == [1, 2, 3]
    assert table["best_aic"].sum() == 1
    assert table["best_bic"].sum() == 1


def test_democracy_heterogeneity_tables(synthetic_direction_panel):
    interaction = fit_democracy_interaction(
        synthetic_direction_panel,
        lag_order=1,
        controls=(),
    )
    marginal = democracy_interaction_table(interaction)
    split = democracy_split_robustness(
        synthetic_direction_panel,
        lag_order=1,
        controls=(),
    )
    assert {"marginal_coef_lag1", "marginal_p_lag1"} <= set(marginal.columns)
    assert set(split["democracy_group"]) == {
        "low_democracy_countries",
        "high_democracy_countries",
    }
