"""Reproducible sensitivity analyses that need the raw V-Dem / V-Party data (audit #4, #5).

Unlike ``models.py`` (pure, DataFrame-in / model-out), these functions read the raw DuckDB
tables to build *alternative* predictors and controls, then re-estimate the M2 within-country
association. They are the committed, reproducible source for two robustness questions:

- #5 aggregation: does the result depend on representing the government by the PM's party alone?
- #4 controls: does it survive the originally-specified controls (rule of law, regime type)?
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import polars as pl

from association.models import ENTITY, PRIMARY_OUTCOME, TIME, _fit_twfe, _panel_indexed

DEFAULT_DB = Path("data/duckdb/vdem.duckdb")
START_YEAR, END_YEAR = 1970, 2019


def _forward_fill_annual(elections: pl.DataFrame, value_cols: list[str]) -> pl.DataFrame:
    """Expand election-year aggregates to an annual panel by within-country forward fill."""
    years = pl.DataFrame({"year": range(START_YEAR, END_YEAR + 1)})
    grid = elections.select(ENTITY).unique().join(years, how="cross")
    filled = grid.join(elections, on=[ENTITY, TIME], how="left").sort([ENTITY, TIME])
    for col in value_cols:
        filled = filled.with_columns(pl.col(col).forward_fill().over(ENTITY))
    return filled.filter(pl.col(value_cols[0]).is_not_null())


def fallback_rate(parties: pl.DataFrame, weight: str) -> tuple[int, int]:
    """Count election groups where the weighted mean falls back to an unweighted mean (audit #8).

    Fallback happens when any weight in a country-year group is missing or the weights sum to ≤ 0.
    Pure (operates on an in-memory frame) so it is unit-testable without DuckDB. Returns
    ``(n_fallback_groups, n_total_groups)``.
    """
    grouped = parties.group_by([ENTITY, TIME]).agg(
        pl.col(weight).null_count().alias("_nnull"),
        pl.col(weight).sum().alias("_wsum"),
    )
    n_fallback = grouped.filter((pl.col("_nnull") > 0) | (pl.col("_wsum") <= 0)).height
    return n_fallback, grouped.height


def aggregation_fallback_rates(db_path: Path = DEFAULT_DB) -> dict[str, float]:
    """Report the weight-fallback share for each alternative aggregation (audit #8)."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        vp = pl.read_database(
            f"""
            SELECT country_id, year, v2pagovsup, v2pavote, v2paseatshare
            FROM raw.vparty_country_party_date
            WHERE year BETWEEN {START_YEAR} AND {END_YEAR}
              AND v2xpa_popul IS NOT NULL AND v2paanteli_nr > 3 AND v2papeople_nr > 3
            """,
            con,
        )
    finally:
        con.close()
    cf, ct = fallback_rate(vp.filter(pl.col("v2pagovsup").is_in([0, 1])), "v2pavote")
    pf, pt = fallback_rate(vp, "v2paseatshare")
    return {"coalition_vote_fallback": cf / ct, "parliament_seat_fallback": pf / pt}


def build_alternative_populism(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Alternative country-year populism scores beyond the senior-governing-party measure (#5).

    Returns ``country_id, year`` plus:
    - ``populism_gov_coalition`` — vote-weighted mean over *all* government parties
      (``v2pagovsup in (0, 1)``: senior + junior partners), so coalitions are not reduced to the
      PM's party;
    - ``populism_seatshare`` — seat-share-weighted mean over all coded parties (the "parliamentary
      climate"), capturing a populist opposition too.
    Both use the same coder-count filter as the main pipeline and the same forward-fill.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        vp = pl.read_database(
            f"""
            SELECT country_id, year, v2pagovsup, v2xpa_popul, v2pavote, v2paseatshare
            FROM raw.vparty_country_party_date
            WHERE year BETWEEN {START_YEAR} AND {END_YEAR}
              AND v2xpa_popul IS NOT NULL AND v2paanteli_nr > 3 AND v2papeople_nr > 3
            """,
            con,
        )
    finally:
        con.close()

    def _wmean(value: str, weight: str) -> pl.Expr:
        # vote/seat-weighted mean, falling back to a simple mean when weights are missing/zero.
        num = (pl.col(value) * pl.col(weight)).sum()
        den = pl.col(weight).sum()
        return (
            pl.when((pl.col(weight).null_count() == 0) & (den > 0))
            .then(num / den)
            .otherwise(pl.col(value).mean())
        )

    coalition = (
        vp.filter(pl.col("v2pagovsup").is_in([0, 1]))
        .group_by([ENTITY, TIME])
        .agg(_wmean("v2xpa_popul", "v2pavote").alias("populism_gov_coalition"))
    )
    parliament = vp.group_by([ENTITY, TIME]).agg(
        _wmean("v2xpa_popul", "v2paseatshare").alias("populism_seatshare")
    )
    merged = coalition.join(parliament, on=[ENTITY, TIME], how="full", coalesce=True)
    filled = _forward_fill_annual(
        merged.sort([ENTITY, TIME]), ["populism_gov_coalition", "populism_seatshare"]
    )
    return filled.to_pandas()


def fit_aggregation_robustness(
    panel_df: pd.DataFrame, db_path: Path = DEFAULT_DB
) -> dict[str, object]:
    """Re-estimate the M2 association with alternative populism aggregations (#5).

    Same spec (``v2x_corr ~ populism + log_gdppc + country & year FE``, clustered SEs), swapping
    the predictor for the coalition and seat-share versions. Shows whether the conclusion depends
    on representing the government solely by the prime minister's party.
    """
    alt = build_alternative_populism(db_path)
    merged = panel_df.merge(alt, on=[ENTITY, TIME], how="left")
    out: dict[str, object] = {}
    for label, pred in {
        "Senior governing party (baseline)": "populism_governing",
        "All government parties (coalition, vote-wtd)": "populism_gov_coalition",
        "All parties (seat-share-wtd)": "populism_seatshare",
    }.items():
        sample = merged.dropna(subset=[PRIMARY_OUTCOME, pred, "log_gdppc"])
        formula = f"{PRIMARY_OUTCOME} ~ 1 + {pred} + log_gdppc + EntityEffects + TimeEffects"
        out[label] = _fit_twfe(formula, _panel_indexed(sample))
    return out


def fit_control_set_robustness(
    panel_df: pd.DataFrame, db_path: Path = DEFAULT_DB
) -> dict[str, object]:
    """Re-estimate M2 under alternative control sets, incl. the originally-specified ones (#4).

    The design named GDP, ``v2x_regime`` and ``v2x_rule``; the implementation used GDP and
    ``v2x_polyarchy``. We compare three control sets so the substitution is transparent:
    minimal (GDP only), the implemented set (GDP + polyarchy), and the original design
    (GDP + rule of law + regime type). **Caveat:** rule of law, democracy and regime type may
    themselves be affected by populist government, i.e. they may be *post-treatment* controls —
    conditioning on them can absorb part of the very relationship under study. So these are
    sensitivity checks, not a "more controls = better" ladder.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        extra = pl.read_database(
            f"""
            SELECT country_id, year, v2x_rule, v2x_regime
            FROM raw.vdem_country_year
            WHERE year BETWEEN {START_YEAR} AND {END_YEAR}
            """,
            con,
        ).to_pandas()
    finally:
        con.close()

    merged = panel_df.merge(extra, on=[ENTITY, TIME], how="left")
    base = f"{PRIMARY_OUTCOME} ~ 1 + populism_governing"
    control_sets = {
        "Minimal (GDP only)": "log_gdppc",
        "Implemented (GDP + polyarchy)": "log_gdppc + v2x_polyarchy",
        "Original design (GDP + rule + regime)": "log_gdppc + v2x_rule + C(v2x_regime)",
    }
    out: dict[str, object] = {}
    for label, controls in control_sets.items():
        needed = ["log_gdppc"]
        if "polyarchy" in controls:
            needed.append("v2x_polyarchy")
        if "rule" in controls:
            needed += ["v2x_rule", "v2x_regime"]
        sample = merged.dropna(subset=[PRIMARY_OUTCOME, "populism_governing", *needed])
        formula = f"{base} + {controls} + EntityEffects + TimeEffects"
        out[label] = _fit_twfe(formula, _panel_indexed(sample))
    return out
