"""Tests for the association module (Task 3).

Uses a synthetic panel with a *known* structure — positive between-country, negative
within-country — so we can check the estimators recover that divergence and the result
objects have the expected shape. The XGBoost/tuning functions are not unit-tested here
(slow, stochastic); the econometric core is.
"""

import numpy as np
import pandas as pd
import pytest
from association import (
    fit_between_within_comparison,
    fit_twfe_grid,
    fit_twfe_robustness,
    hausman_fe_re,
    interaction_marginal_effects,
    within_between_variance,
)
from association.plots import robustness_table


@pytest.fixture
def synthetic_panel() -> pd.DataFrame:
    """Balanced panel: corruption rises with a country's baseline populism (between, +),
    but falls when a country's own populism rises over time (within, −)."""
    rng = np.random.default_rng(0)
    n_countries, n_years = 40, 25
    rows = []
    for cid in range(n_countries):
        base_pop = rng.uniform(0.1, 0.8)  # country's typical populism
        base_corr = 0.2 + 0.6 * base_pop  # between-country: more populist -> more corrupt
        for t in range(n_years):
            year = 1990 + t
            pop = np.clip(base_pop + rng.normal(0, 0.1), 0, 1)  # within wiggle
            within_dev = pop - base_pop
            corr = np.clip(
                base_corr - 0.3 * within_dev + 0.002 * t + rng.normal(0, 0.03), 0, 1
            )  # within: negative
            rows.append(
                {
                    "country_id": cid,
                    "year": year,
                    "populism_governing": pop,
                    "v2x_corr": corr,
                    "log_gdppc": rng.normal(8, 1),
                    "v2x_polyarchy": np.clip(rng.uniform(0, 1), 0, 1),
                    "e_regiongeo": (cid % 6) + 1,
                    "is_election_year": (t % 4 == 0),
                }
            )
    df = pd.DataFrame(rows).sort_values(["country_id", "year"])
    df["v2x_corr_lag1"] = df.groupby("country_id")["v2x_corr"].shift(1)
    return df


def test_within_between_variance_shares_sum_to_one(synthetic_panel):
    vb = within_between_variance(synthetic_panel, "populism_governing")
    assert vb["within_share"] + vb["between_share"] == pytest.approx(1.0)
    assert 0 < vb["within_share"] < 1
    assert vb["n_countries"] == 40


def test_twfe_grid_returns_four_models_and_two_samples(synthetic_panel):
    grid = fit_twfe_grid(synthetic_panel)
    assert set(grid.models) == {"M1", "M2", "M3", "M4"}
    # M4 needs the lag, so its sample is smaller than the M1-M3 stability sample.
    assert grid.m4_n_obs < grid.n_obs
    assert grid.stability_models == ("M1", "M2", "M3")


def test_within_estimate_is_negative_despite_positive_between(synthetic_panel):
    """The headline property: pooled/between positive, within negative."""
    bw = fit_between_within_comparison(synthetic_panel)
    pooled = float(bw["Pooled OLS (between+within)"].params["populism_governing"])
    within = float(bw["Two-way FE (within+year)"].params["populism_governing"])
    assert pooled > 0  # between-country signal dominates the pooled estimate
    assert within < 0  # within-country relationship is negative by construction


def test_interaction_marginal_effects_shape(synthetic_panel):
    me = interaction_marginal_effects(synthetic_panel)
    assert list(me["polyarchy_quantile"]) == ["p10", "p50", "p90"]
    assert {"marginal_effect", "ci_low", "ci_high", "excludes_zero"} <= set(me.columns)


def test_robustness_table_has_row_per_estimator(synthetic_panel):
    table = robustness_table(fit_twfe_robustness(synthetic_panel))
    assert len(table) == 4
    assert {"estimator", "populism_coef", "ci_low", "ci_high", "p_value"} <= set(table.columns)


def test_hausman_reports_reliability_flag(synthetic_panel):
    h = hausman_fe_re(synthetic_panel)
    assert "reliable" in h and isinstance(h["reliable"], bool)
    # pvalue is NaN exactly when the covariance difference is not positive-definite.
    assert h["reliable"] == (h["pvalue"] == h["pvalue"])  # NaN != NaN
