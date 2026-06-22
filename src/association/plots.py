"""Plotting + table helpers for the association analysis (Task 3).

These read fitted-model objects / result dicts produced by ``association.models`` and render
figures or formatted tables. Kept out of ``models.py`` so the fitting logic stays
plot-free and testable.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from linearmodels.panel.results import PanelEffectsResults

from association.models import PREDICTOR, TWFEGridResult, XGBoostCVResult


def _coef_ci(model: PanelEffectsResults, term: str) -> tuple[float, float, float]:
    """Return (point estimate, lower 95%, upper 95%) for one term of a fitted model."""
    point = float(model.params[term])
    ci = model.conf_int().loc[term]
    return point, float(ci["lower"]), float(ci["upper"])


def coefficient_stability_plot(
    grid: TWFEGridResult, term: str = PREDICTOR, ax: plt.Axes | None = None
) -> plt.Axes:
    """Point estimate + 95% CI on ``term`` across the stability models M1–M3 only.

    M4 is excluded by design: it adds the lagged outcome, changing the estimand, so a drop
    there is not omitted-variable fragility (spec B1).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 2.6))
    names = list(grid.stability_models)
    rows = [(name, *_coef_ci(grid.models[name], term)) for name in names]
    ys = range(len(rows))
    points = [r[1] for r in rows]
    lowers = [r[1] - r[2] for r in rows]
    uppers = [r[3] - r[1] for r in rows]
    ax.errorbar(points, list(ys), xerr=[lowers, uppers], fmt="o", capsize=4, color="firebrick")
    ax.axvline(0, color="grey", lw=1, ls="--")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(names)
    ax.set_xlabel(f"coefficient on {term} (95% CI)")
    ax.set_title("Coefficient stability across controls (M1–M3)")
    ax.invert_yaxis()
    return ax


def benchmark_table(
    baseline_within_r2: float,
    twfe_within_r2: float,
    xgb: XGBoostCVResult,
) -> pd.DataFrame:
    """Four-row benchmark with the two metric types labelled (spec B4).

    Within-R² (econometric, in-sample on demeaned data) and OOF-R² (predictive,
    out-of-sample) are not the same yardstick — the like-for-like comparison is the
    Linear-OOF vs XGBoost-OOF rows. Interpret across metric types directionally only.
    """
    return pd.DataFrame(
        [
            ("Persistence baseline (corr ~ lag + country FE)", "within-R²", baseline_within_r2),
            ("TWFE M2 (populism + log GDP)", "within-R²", twfe_within_r2),
            ("Linear, GroupKFold", "OOF-R²", xgb.linear_oof_r2),
            ("XGBoost, GroupKFold", "OOF-R²", xgb.oof_r2_mean),
        ],
        columns=["model", "metric_type", "r2"],
    )


def shap_importance_plot(
    xgb: XGBoostCVResult, top_n: int = 10, ax: plt.Axes | None = None
) -> plt.Axes:
    """Horizontal bar chart of mean |SHAP| per feature; populism highlighted.

    SHAP describes the fitted XGBoost only — it is not statistical significance (spec C2).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.5 * min(top_n, len(xgb.feature_importances)) + 1))
    items = sorted(xgb.feature_importances.items(), key=lambda kv: kv[1])[-top_n:]
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = ["firebrick" if k == PREDICTOR else "steelblue" for k in labels]
    ax.barh(labels, values, color=colors)
    ax.set_xlabel("mean |SHAP value| (out-of-fold)")
    ax.set_title("XGBoost feature importance")
    return ax


def robustness_table(robustness: dict, term: str = PREDICTOR) -> pd.DataFrame:
    """Format `fit_twfe_robustness` output: one row per estimator with coef, SE, 95% CI, p.

    Read it as a stability check — the SE variants share a point estimate (only the interval
    moves); first-difference is an independent estimate via a different identification route.
    """
    rows = []
    for name, model in robustness.items():
        ci = model.conf_int().loc[term]
        rows.append(
            {
                "estimator": name,
                "populism_coef": float(model.params[term]),
                "std_err": float(model.std_errors[term]),
                "ci_low": float(ci["lower"]),
                "ci_high": float(ci["upper"]),
                "p_value": float(model.pvalues[term]),
            }
        )
    return pd.DataFrame(rows)
