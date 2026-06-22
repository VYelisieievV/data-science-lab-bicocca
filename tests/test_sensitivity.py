"""Tests for the sensitivity layer (audit re-#15).

Covers the weight-fallback logic (pure, no DuckDB) and the numerical correctness of the
interaction marginal-effect formula. The DuckDB-backed builders are exercised end-to-end in the
notebook; here we test the parts that can be checked deterministically in memory.
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest
from association import interaction_marginal_effects
from association.models import fit_twfe_interaction
from association.sensitivity import fallback_rate


def test_fallback_rate_counts_missing_and_zero_weights():
    # group (1,2000): one weight missing -> fallback. group (2,2000): weights present, sum>0 -> ok.
    # group (3,2000): weights sum to zero -> fallback.
    parties = pl.DataFrame(
        {
            "country_id": [1, 1, 2, 2, 3, 3],
            "year": [2000, 2000, 2000, 2000, 2000, 2000],
            "v2pavote": [50.0, None, 40.0, 60.0, 0.0, 0.0],
        }
    )
    n_fallback, n_total = fallback_rate(parties, "v2pavote")
    assert n_total == 3
    assert n_fallback == 2  # groups 1 (missing) and 3 (zero sum)


@pytest.fixture
def interaction_panel() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    rows = []
    for cid in range(30):
        base = rng.uniform(0.1, 0.8)
        for t in range(20):
            poly = np.clip(rng.uniform(0, 1), 0, 1)
            pop = np.clip(base + rng.normal(0, 0.1), 0, 1)
            corr = np.clip(0.4 - 0.2 * pop + 0.3 * pop * poly + rng.normal(0, 0.03), 0, 1)
            rows.append(
                {
                    "country_id": cid,
                    "year": 1990 + t,
                    "populism_governing": pop,
                    "v2x_corr": corr,
                    "log_gdppc": rng.normal(8, 1),
                    "v2x_polyarchy": poly,
                }
            )
    return pd.DataFrame(rows)


def test_marginal_effect_matches_manual_formula(interaction_panel):
    """ME(populism | polyarchy=p) must equal b_populism + b_interaction * p."""
    model = fit_twfe_interaction(interaction_panel)
    b_p = float(model.params["populism_governing"])
    b_i = float(model.params["populism_governing:v2x_polyarchy"])
    me = interaction_marginal_effects(interaction_panel)
    for _, row in me.iterrows():
        expected = b_p + b_i * row["polyarchy_value"]
        assert row["marginal_effect"] == pytest.approx(expected, abs=1e-3)
