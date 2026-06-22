"""Fitting functions for the association analysis (Task 3).

Each function takes a plain ``pandas.DataFrame`` (the regression-ready panel, one row per
country-year) and returns a fitted model or a small result object. No I/O, no plotting, no
global state. See ``specs/panel-regression-association.md`` for the design and the plain-
language rationale behind every modelling choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from linearmodels.panel import (
    BetweenOLS,
    FirstDifferenceOLS,
    PanelOLS,
    PooledOLS,
    RandomEffects,
)
from linearmodels.panel.results import PanelEffectsResults
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, GroupKFold, StratifiedGroupKFold
from xgboost import XGBRegressor

ENTITY = "country_id"
TIME = "year"
PRIMARY_OUTCOME = "v2x_corr"
PREDICTOR = "populism_governing"

# M1–M3 share one estimand and one frozen sample: rows complete on these vars, so coefficient
# movement across M1→M3 reflects added controls, not a shifting sample (audit #10 / spec B2).
TWFE_STABILITY_VARS = [PRIMARY_OUTCOME, PREDICTOR, "log_gdppc", "v2x_polyarchy"]
# M4 (the dynamic spec) additionally needs the lag; it is fit on its OWN complete-case sample so
# it does not shrink the M1–M3 stability sample (which would drop each country's first year).
TWFE_M4_VARS = [*TWFE_STABILITY_VARS, "v2x_corr_lag1"]
# Back-compat alias (used by older callers/notebooks).
TWFE_GRID_VARS = TWFE_STABILITY_VARS

# Predictive-model feature set: populism + the two controls. Raw (undemeaned) features so
# GroupKFold hold-outs stay honest (spec B3).
XGB_FEATURES = [PREDICTOR, "log_gdppc", "v2x_polyarchy"]

# e_regiongeo (19 UN-geoscheme codes) collapsed to macro-regions, used only to stratify CV
# folds so each fold spans the globe (spec: sparse-regions risk).
_MACRO_REGION: dict[int, str] = {
    1: "Europe",
    2: "Europe",
    3: "Europe",
    4: "Europe",
    5: "MENA",
    10: "MENA",
    6: "SSAfrica",
    7: "SSAfrica",
    8: "SSAfrica",
    9: "SSAfrica",
    11: "Asia",
    12: "Asia",
    13: "Asia",
    14: "Asia",
    15: "Oceania",
    16: "Americas",
    17: "Americas",
    18: "Americas",
    19: "Americas",
}


def _panel_indexed(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` indexed by (entity, time) — the form ``linearmodels`` requires."""
    return df.set_index([ENTITY, TIME])


def _fit_twfe(formula: str, data: pd.DataFrame) -> PanelEffectsResults:
    """Fit one two-way FE spec with country-clustered SEs (the project default)."""
    return PanelOLS.from_formula(formula, data).fit(cov_type="clustered", cluster_entity=True)


def within_between_variance(df: pd.DataFrame, col: str = PREDICTOR) -> dict[str, float]:
    """Split a column's variance into between-country and within-country shares.

    FE identifies only off *within*-country variation. If most of ``col``'s variance is
    between countries, the FE estimator has little signal — this quantifies that up front
    (spec Goal 1 / B5).
    """
    series = df[[ENTITY, col]].dropna()
    country_mean = series.groupby(ENTITY)[col].transform("mean")
    grand_mean = series[col].mean()
    within = float(((series[col] - country_mean) ** 2).mean())
    between = float(((country_mean - grand_mean) ** 2).mean())
    total = within + between
    return {
        "within_var": within,
        "between_var": between,
        "within_share": within / total if total else float("nan"),
        "between_share": between / total if total else float("nan"),
        "n_obs": int(len(series)),
        "n_countries": int(series[ENTITY].nunique()),
    }


def fit_persistence_baseline(df: pd.DataFrame) -> dict[str, object]:
    """Country-FE-only regression of corruption on last year's corruption.

    Documents how *persistent* (sticky) corruption is — it is **not** a performance bar the static
    M1–M3 models must beat (audit #8): it is a dynamic model with a lagged outcome, a different
    specification and a different estimand, so its within-R² is not comparable to theirs.
    """
    sample = df.dropna(subset=[PRIMARY_OUTCOME, "v2x_corr_lag1"])
    res = _fit_twfe(
        f"{PRIMARY_OUTCOME} ~ 1 + v2x_corr_lag1 + EntityEffects", _panel_indexed(sample)
    )
    return {
        "model": res,
        "within_r2": float(res.rsquared_within),
        "lag_coef": float(res.params["v2x_corr_lag1"]),
        "n_obs": int(sample.shape[0]),
        "n_countries": int(sample[ENTITY].nunique()),
    }


@dataclass
class TWFEGridResult:
    """M1–M3 fit on a shared stability sample; M4 fit separately on its own sample (audit #10)."""

    models: dict[str, PanelEffectsResults]
    n_obs: int  # M1–M3 stability sample
    n_countries: int
    m4_n_obs: int  # M4's own complete-case sample (includes the lag)
    m4_n_countries: int
    stability_models: tuple[str, ...] = ("M1", "M2", "M3")
    dynamic_model: str = "M4"


def fit_twfe_grid(df: pd.DataFrame) -> TWFEGridResult:
    """Fit the static grid M1–M3 on one shared sample, and M4 on its own complete-case sample.

    M1–M3 share the same estimand (level association) and the same rows, so movement across them
    reflects added controls, not a shifting sample. M4 adds the lagged outcome — a *different*
    (short-run) estimand — so it is fit separately on its own complete-case sample rather than
    forcing M1–M3 to drop each country's first year for a lag they do not use (audit #10).
    """
    base = f"{PRIMARY_OUTCOME} ~ 1 + {PREDICTOR}"
    stability = df.dropna(subset=TWFE_STABILITY_VARS)
    sdata = _panel_indexed(stability)
    models = {
        "M1": _fit_twfe(f"{base} + EntityEffects + TimeEffects", sdata),
        "M2": _fit_twfe(f"{base} + log_gdppc + EntityEffects + TimeEffects", sdata),
        "M3": _fit_twfe(f"{base} + log_gdppc + v2x_polyarchy + EntityEffects + TimeEffects", sdata),
    }
    m4_sample = df.dropna(subset=TWFE_M4_VARS)
    models["M4"] = _fit_twfe(
        f"{base} + log_gdppc + v2x_polyarchy + v2x_corr_lag1 + EntityEffects + TimeEffects",
        _panel_indexed(m4_sample),
    )
    return TWFEGridResult(
        models=models,
        n_obs=int(stability.shape[0]),
        n_countries=int(stability[ENTITY].nunique()),
        m4_n_obs=int(m4_sample.shape[0]),
        m4_n_countries=int(m4_sample[ENTITY].nunique()),
    )


def fit_twfe_interaction(df: pd.DataFrame) -> PanelEffectsResults:
    """M2 + a populism×polyarchy interaction (and the polyarchy main effect).

    Tests whether the populism-corruption association is stronger where democracy is weaker.
    """
    sample = df.dropna(subset=[PRIMARY_OUTCOME, PREDICTOR, "log_gdppc", "v2x_polyarchy"])
    formula = (
        f"{PRIMARY_OUTCOME} ~ 1 + {PREDICTOR} + log_gdppc + v2x_polyarchy"
        f" + {PREDICTOR}:v2x_polyarchy + EntityEffects + TimeEffects"
    )
    return _fit_twfe(formula, _panel_indexed(sample))


def fit_between_within_comparison(df: pd.DataFrame) -> dict[str, PanelEffectsResults]:
    """Estimate populism→corruption four ways to locate where the correlation lives (audit #6).

    Same single-predictor specification under: pooled OLS (between+within), between-country only,
    entity FE (within), and two-way FE (within+year). This is the committed, reproducible source
    for the "between-vs-within" table/figure — it must not be a hand-built artifact.

    **Dependence-adjusted SEs throughout** (audit re-#1): repeated country-years are not
    independent, so pooled OLS uses country-clustered SEs and the between regression uses
    heteroskedasticity-robust SEs. With unadjusted SEs the pooled/between intervals are
    misleadingly narrow; once adjusted, the positive cross-country point estimates are *not*
    clearly distinguishable from zero.
    """
    sample = df.dropna(subset=[PRIMARY_OUTCOME, PREDICTOR])
    data = _panel_indexed(sample)
    rhs = f"{PRIMARY_OUTCOME} ~ 1 + {PREDICTOR}"
    return {
        "Pooled OLS (between+within)": PooledOLS.from_formula(rhs, data).fit(
            cov_type="clustered", cluster_entity=True
        ),
        "Between-country": BetweenOLS.from_formula(rhs, data).fit(cov_type="robust"),
        "Entity FE (within)": PanelOLS.from_formula(f"{rhs} + EntityEffects", data).fit(
            cov_type="clustered", cluster_entity=True
        ),
        "Two-way FE (within+year)": PanelOLS.from_formula(
            f"{rhs} + EntityEffects + TimeEffects", data
        ).fit(cov_type="clustered", cluster_entity=True),
    }


def interaction_marginal_effects(
    df: pd.DataFrame, polyarchy_quantiles: tuple[float, ...] = (0.1, 0.5, 0.9)
) -> pd.DataFrame:
    """Marginal effect of populism at representative democracy levels (audit #2).

    The interaction model gives one interaction coefficient; on its own that is not
    substantively interpretable. The marginal effect of populism is
    ``β_populism + β_interaction · polyarchy`` and its SE follows from the delta method
    ``var = var(β_p) + poly²·var(β_i) + 2·poly·cov(β_p, β_i)``. We evaluate it at low / median /
    high polyarchy so the report can say where (if anywhere) the association is non-zero.
    """
    model = fit_twfe_interaction(df)
    inter = f"{PREDICTOR}:v2x_polyarchy"
    b_p, b_i = float(model.params[PREDICTOR]), float(model.params[inter])
    cov = model.cov
    v_p = float(cov.loc[PREDICTOR, PREDICTOR])
    v_i = float(cov.loc[inter, inter])
    c_pi = float(cov.loc[PREDICTOR, inter])
    poly = df["v2x_polyarchy"].dropna()
    rows = []
    for q in polyarchy_quantiles:
        pv = float(poly.quantile(q))
        me = b_p + b_i * pv
        se = float(np.sqrt(v_p + pv**2 * v_i + 2 * pv * c_pi))
        rows.append(
            {
                "polyarchy_quantile": f"p{int(q * 100)}",
                "polyarchy_value": round(pv, 3),
                "marginal_effect": round(me, 4),
                "ci_low": round(me - 1.96 * se, 4),
                "ci_high": round(me + 1.96 * se, 4),
                "excludes_zero": bool((me - 1.96 * se) * (me + 1.96 * se) > 0),
            }
        )
    return pd.DataFrame(rows)


def fit_twfe_robustness(df: pd.DataFrame) -> dict[str, object]:
    """Re-estimate the M2 association under alternative SE estimators and first-differencing.

    This is a *robustness ensemble*, not a model-selection leaderboard: the goal is to show the
    within-country conclusion is stable across reasonable choices, not to pick a "best" fit. The
    coefficient is identical across the SE variants (only the interval changes); first-difference
    removes the country effects a different way (differencing instead of demeaning) and gives an
    independent check on the point estimate.
    """
    sample = df.dropna(subset=[PRIMARY_OUTCOME, PREDICTOR, "log_gdppc"])
    data = _panel_indexed(sample)
    twfe = PanelOLS.from_formula(
        f"{PRIMARY_OUTCOME} ~ 1 + {PREDICTOR} + log_gdppc + EntityEffects + TimeEffects", data
    )
    fd = FirstDifferenceOLS.from_formula(f"{PRIMARY_OUTCOME} ~ {PREDICTOR} + log_gdppc", data)
    return {
        "TWFE — cluster by country": twfe.fit(cov_type="clustered", cluster_entity=True),
        "TWFE — two-way cluster (country & year)": twfe.fit(
            cov_type="clustered", cluster_entity=True, cluster_time=True
        ),
        "TWFE — Driscoll–Kraay (HAC)": twfe.fit(cov_type="kernel"),
        "First-difference (country effects differenced out)": fd.fit(
            cov_type="clustered", cluster_entity=True
        ),
    }


def hausman_fe_re(
    df: pd.DataFrame, controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy")
) -> dict[str, object]:
    """Hausman test of entity-FE vs entity-RE — reported only as a weak diagnostic (audit #7).

    Compares the FE and RE coefficient vectors. **Important caveat:** when the covariance
    difference is not positive-definite (which it is *not* here), the statistic does **not** have
    a dependable chi-square interpretation, so the p-value must **not** be read as a formal
    rejection of random effects. The function returns ``reliable=False`` in that case. Our choice
    of FE does not rest on this test — it follows directly from the within-country research
    question (we would use FE regardless). The statistic is reported for completeness only.
    """
    sample = df.dropna(subset=[PRIMARY_OUTCOME, PREDICTOR, *controls])
    data = _panel_indexed(sample)
    rhs = " + ".join([PREDICTOR, *controls])
    fe = PanelOLS.from_formula(f"{PRIMARY_OUTCOME} ~ 1 + {rhs} + EntityEffects", data).fit()
    re = RandomEffects.from_formula(f"{PRIMARY_OUTCOME} ~ 1 + {rhs}", data).fit()

    terms = [PREDICTOR, *controls]
    b_diff = (fe.params[terms] - re.params[terms]).to_numpy()
    v_diff = (fe.cov.loc[terms, terms] - re.cov.loc[terms, terms]).to_numpy()
    pos_def = bool((np.linalg.eigvalsh(v_diff) > 0).all())
    stat = float(b_diff @ np.linalg.pinv(v_diff) @ b_diff)
    dof = len(terms)
    return {
        "stat": stat,
        "dof": dof,
        # Only a valid chi-square p-value when the covariance difference is positive-definite.
        "pvalue": float(stats.chi2.sf(stat, dof)) if pos_def else float("nan"),
        "cov_pos_def": pos_def,
        "reliable": pos_def,
        "n_obs": int(sample.shape[0]),
    }


@dataclass
class XGBoostCVResult:
    """Out-of-fold metrics + SHAP importances from the GroupKFold predictive check."""

    oof_r2_mean: float
    oof_r2_std: float
    linear_oof_r2: float
    feature_importances: dict[str, float]
    features: list[str] = field(default_factory=lambda: list(XGB_FEATURES))
    n_obs: int = 0
    n_countries: int = 0


def fit_xgboost_cv(df: pd.DataFrame, n_splits: int = 5, random_state: int = 0) -> XGBoostCVResult:
    """Predictive cross-national check: XGBoost on raw features, GroupKFold by country.

    Holds out whole countries (StratifiedGroupKFold stratified by macro-region) and reports
    out-of-fold R². A plain linear model is run on the identical folds for an apples-to-apples
    OOF comparison. The headline is the SHAP rank of populism, not the R² horse-race (spec B3/B4).
    """
    sample = df.dropna(subset=[*XGB_FEATURES, PRIMARY_OUTCOME, ENTITY, "e_regiongeo"]).copy()
    X = sample[XGB_FEATURES].to_numpy(dtype=float)
    y = sample[PRIMARY_OUTCOME].to_numpy(dtype=float)
    groups = sample[ENTITY].to_numpy()
    strata = sample["e_regiongeo"].map(_MACRO_REGION).fillna("Other").to_numpy()

    # lazy import: shap pulls in a slow numba/llvmlite stack, only needed here.
    import shap

    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    oof_xgb: list[float] = []
    oof_lin: list[float] = []
    shap_abs: list[np.ndarray] = []
    for train_idx, test_idx in cv.split(X, strata, groups):
        booster = XGBRegressor(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            random_state=random_state,
            n_jobs=-1,
        )
        booster.fit(X[train_idx], y[train_idx])
        oof_xgb.append(r2_score(y[test_idx], booster.predict(X[test_idx])))

        linear = LinearRegression().fit(X[train_idx], y[train_idx])
        oof_lin.append(r2_score(y[test_idx], linear.predict(X[test_idx])))

        values = shap.TreeExplainer(booster).shap_values(X[test_idx])
        shap_abs.append(np.abs(values).mean(axis=0))

    mean_abs_shap = np.mean(shap_abs, axis=0)
    return XGBoostCVResult(
        oof_r2_mean=float(np.mean(oof_xgb)),
        oof_r2_std=float(np.std(oof_xgb)),
        linear_oof_r2=float(np.mean(oof_lin)),
        feature_importances={f: float(v) for f, v in zip(XGB_FEATURES, mean_abs_shap)},
        n_obs=int(sample.shape[0]),
        n_countries=int(sample[ENTITY].nunique()),
    )


def tune_xgboost_nested_cv(
    df: pd.DataFrame, n_splits: int = 5, random_state: int = 0
) -> dict[str, object]:
    """Nested-CV hyperparameter search for the XGBoost predictive check.

    The fixed-hyperparameter ``fit_xgboost_cv`` is a sanity check, not a tuned model. This
    function answers "would tuning change the verdict?" honestly: an **inner** GroupKFold tunes
    hyperparameters on each outer training fold, and the **outer** StratifiedGroupKFold scores the
    tuned model on held-out countries — so tuning never sees the test countries (no leakage). We
    report the tuned out-of-fold R² (to compare against the untuned 0.45), the chosen params, and
    **SHAP importances recomputed under the tuned models** — so the "populism stays the weakest
    feature after tuning" statement is actually backed by the tuned fit, not merely the untuned one
    (audit #9). The expectation is that tuning moves OOF-R² only marginally and does not change the
    ranking.
    """
    import shap

    sample = df.dropna(subset=[*XGB_FEATURES, PRIMARY_OUTCOME, ENTITY, "e_regiongeo"]).copy()
    X = sample[XGB_FEATURES].to_numpy(dtype=float)
    y = sample[PRIMARY_OUTCOME].to_numpy(dtype=float)
    groups = sample[ENTITY].to_numpy()
    strata = sample["e_regiongeo"].map(_MACRO_REGION).fillna("Other").to_numpy()

    param_grid = {
        "max_depth": [2, 3, 4],
        "learning_rate": [0.03, 0.1],
        "n_estimators": [200, 400],
    }
    outer = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    oof_r2: list[float] = []
    best_params: list[dict] = []
    shap_abs: list[np.ndarray] = []
    for train_idx, test_idx in outer.split(X, strata, groups):
        search = GridSearchCV(
            XGBRegressor(
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=random_state,
                n_jobs=-1,
            ),
            param_grid,
            scoring="r2",
            cv=GroupKFold(n_splits=3),
        )
        search.fit(X[train_idx], y[train_idx], groups=groups[train_idx])
        oof_r2.append(r2_score(y[test_idx], search.predict(X[test_idx])))
        best_params.append(search.best_params_)
        values = shap.TreeExplainer(search.best_estimator_).shap_values(X[test_idx])
        shap_abs.append(np.abs(values).mean(axis=0))
    mean_abs_shap = np.mean(shap_abs, axis=0)
    return {
        "tuned_oof_r2_mean": float(np.mean(oof_r2)),
        "tuned_oof_r2_std": float(np.std(oof_r2)),
        "best_params_per_fold": best_params,
        "feature_importances": {f: float(v) for f, v in zip(XGB_FEATURES, mean_abs_shap)},
    }
