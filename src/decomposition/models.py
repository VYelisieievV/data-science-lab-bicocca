"""Panel models for Task 5: decomposition of political corruption by institutional sphere.

This module is intentionally independent from ``association`` and ``causal_direction`` so the
completed work of other teammates remains unchanged. It reproduces their core estimands with an
explicit outcome parameter, adds comparable within-standardised effects, and controls the false
discovery rate across the pre-declared dimension families.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from linearmodels.panel.results import PanelEffectsResults
from scipy import stats

ENTITY = "country_id"
TIME = "year"
POPULISM = "populism_governing"
CONTROLS = ("log_gdppc", "v2x_polyarchy")

Direction = Literal["populism_to_corruption", "corruption_to_populism"]
SampleMode = Literal["outcome_specific", "common"]


@dataclass(frozen=True)
class OutcomeSpec:
    """One corruption outcome and the transformation needed for a common interpretation."""

    key: str
    label: str
    source_column: str
    model_column: str
    orientation: int
    descriptive_column: str
    is_composite: bool = False


OUTCOMES = (
    OutcomeSpec(
        "composite",
        "Composite",
        "v2x_corr",
        "corruption_composite",
        1,
        "v2x_corr",
        True,
    ),
    OutcomeSpec(
        "executive",
        "Executive",
        "v2x_execorr",
        "corruption_executive",
        1,
        "v2x_execorr",
    ),
    OutcomeSpec(
        "public_sector",
        "Public sector",
        "v2x_pubcorr",
        "corruption_public_sector",
        1,
        "v2x_pubcorr",
    ),
    OutcomeSpec(
        "legislative",
        "Legislative",
        "v2lgcrrpt",
        "corruption_legislative",
        -1,
        "v2lgcrrpt_01",
    ),
    OutcomeSpec(
        "judicial",
        "Judicial",
        "v2jucorrdc",
        "corruption_judicial",
        -1,
        "v2jucorrdc_01",
    ),
)
OUTCOME_BY_KEY = {outcome.key: outcome for outcome in OUTCOMES}
SUBTYPE_KEYS = tuple(outcome.key for outcome in OUTCOMES if not outcome.is_composite)
MODEL_OUTCOMES = tuple(outcome.model_column for outcome in OUTCOMES)

REQUIRED_COLUMNS = (
    ENTITY,
    TIME,
    "country_name",
    POPULISM,
    *CONTROLS,
    "is_election_year",
    "years_since_last_election",
    *(outcome.source_column for outcome in OUTCOMES),
    "v2lgcrrpt_01",
    "v2jucorrdc_01",
)


@dataclass
class ModelFit:
    """A fitted panel model with the metadata required for auditable tables."""

    outcome_key: str
    outcome_label: str
    model_column: str
    model_type: str
    sample_mode: SampleMode
    result: PanelEffectsResults
    sample: pd.DataFrame
    focal_terms: tuple[str, ...]
    direction: Direction | None = None
    cause_column: str | None = None

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())


def validate_panel(df: pd.DataFrame) -> dict[str, int]:
    """Validate columns, unique country-years, and annual ordering."""
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    duplicates = int(df.duplicated([ENTITY, TIME]).sum())
    if duplicates:
        raise ValueError(f"Panel contains {duplicates} duplicate country-year rows")
    ordered = df.sort_values([ENTITY, TIME])
    differences = ordered.groupby(ENTITY)[TIME].diff()
    gaps = int(((differences.notna()) & (differences != 1)).sum())
    if gaps:
        raise ValueError(f"Panel contains {gaps} internal non-annual gaps")
    return {
        "n_rows": int(df.shape[0]),
        "n_countries": int(df[ENTITY].nunique()),
        "min_year": int(df[TIME].min()),
        "max_year": int(df[TIME].max()),
        "duplicates": duplicates,
        "internal_year_gaps": gaps,
    }


def prepare_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy with continuous outcomes oriented higher=more-corrupt."""
    validate_panel(df)
    out = df.sort_values([ENTITY, TIME]).copy()
    for outcome in OUTCOMES:
        out[outcome.model_column] = outcome.orientation * out[outcome.source_column]

    composite = OUTCOME_BY_KEY["composite"].model_column
    for outcome in OUTCOMES:
        pair = out[[composite, outcome.model_column]].dropna()
        correlation = pair.corr().iloc[0, 1]
        if outcome.key != "composite" and np.isfinite(correlation) and correlation < 0:
            raise ValueError(
                f"Outcome {outcome.key!r} is negatively oriented relative to the composite"
            )
    return out


def _within_values(df: pd.DataFrame, column: str) -> pd.Series:
    values = df[column]
    return values - values.groupby(df[ENTITY]).transform("mean")


def within_sd(df: pd.DataFrame, column: str) -> float:
    """Sample SD after removing each country's mean."""
    valid = df[[ENTITY, column]].dropna()
    if valid.empty:
        return float("nan")
    return float(_within_values(valid, column).std(ddof=1))


def panel_autocorrelation(df: pd.DataFrame, column: str, lag: int) -> float:
    """Pooled correlation between a variable and its within-country annual lag."""
    ordered = df.sort_values([ENTITY, TIME])
    lagged = ordered.groupby(ENTITY)[column].shift(lag)
    return float(ordered[column].corr(lagged))


def outcome_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """Coverage, variation, persistence, and resolution for all outcomes."""
    prepared = prepare_panel(df)
    rows: list[dict[str, object]] = []
    for outcome in OUTCOMES:
        column = outcome.model_column
        valid = prepared.dropna(subset=[column])
        demeaned = _within_values(valid[[ENTITY, column]], column)
        overall_var = float(valid[column].var(ddof=1))
        within_var = float(demeaned.var(ddof=1))
        country_unique = valid.groupby(ENTITY)[column].nunique()
        rows.append(
            {
                "outcome_key": outcome.key,
                "outcome": outcome.label,
                "primary_source": outcome.source_column,
                "orientation_multiplier": outcome.orientation,
                "n_obs": int(valid.shape[0]),
                "n_missing": int(prepared[column].isna().sum()),
                "n_countries": int(valid[ENTITY].nunique()),
                "n_unique_values": int(valid[column].nunique()),
                "overall_sd": float(np.sqrt(overall_var)),
                "within_sd": float(np.sqrt(within_var)),
                "within_variance_share": within_var / overall_var if overall_var > 0 else np.nan,
                "lag1_autocorrelation": panel_autocorrelation(prepared, column, 1),
                "lag2_autocorrelation": panel_autocorrelation(prepared, column, 2),
                "countries_no_within_variation": int((country_unique <= 1).sum()),
                "median_unique_values_per_country": float(country_unique.median()),
            }
        )
    return pd.DataFrame(rows)


def add_panel_shifts(
    df: pd.DataFrame,
    variables: tuple[str, ...] = (POPULISM, *MODEL_OUTCOMES),
    lags: tuple[int, ...] = (1, 2),
    leads: tuple[int, ...] = (1, 2),
) -> pd.DataFrame:
    """Add shifts within country; validation guarantees a row shift equals a calendar shift."""
    out = df.sort_values([ENTITY, TIME]).copy()
    for variable in variables:
        for lag in lags:
            out[f"{variable}_lag{lag}"] = out.groupby(ENTITY)[variable].shift(lag)
        for lead in leads:
            out[f"{variable}_lead{lead}"] = out.groupby(ENTITY)[variable].shift(-lead)
    return out


def _fit_panel(
    sample: pd.DataFrame,
    dependent: str,
    predictors: list[str],
    *,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> tuple[PanelEffectsResults, pd.DataFrame]:
    columns = [ENTITY, TIME, dependent, *predictors]
    clean = sample[columns].dropna().copy()
    if clean[ENTITY].nunique() < 2:
        raise ValueError("A panel model requires at least two countries")
    indexed = clean.set_index([ENTITY, TIME])
    model = PanelOLS(
        indexed[dependent],
        indexed[predictors],
        entity_effects=entity_effects,
        time_effects=time_effects,
        drop_absorbed=True,
        check_rank=False,
    )
    result = model.fit(cov_type="clustered", cluster_entity=True)
    return result, indexed


def _common_association_columns() -> list[str]:
    return [*MODEL_OUTCOMES, POPULISM, *CONTROLS]


def fit_association_models(
    df: pd.DataFrame, sample_mode: SampleMode = "outcome_specific"
) -> list[ModelFit]:
    """Fit M1–M3 for every outcome on frozen outcome-specific or common samples."""
    if sample_mode not in ("outcome_specific", "common"):
        raise ValueError(f"Unknown sample mode: {sample_mode}")
    prepared = prepare_panel(df)
    fits: list[ModelFit] = []
    specifications = {
        "M1": [POPULISM],
        "M2": [POPULISM, "log_gdppc"],
        "M3": [POPULISM, *CONTROLS],
    }
    for outcome in OUTCOMES:
        stability_columns = (
            _common_association_columns()
            if sample_mode == "common"
            else [outcome.model_column, POPULISM, *CONTROLS]
        )
        stability = prepared.dropna(subset=stability_columns).copy()
        for model_type, predictors in specifications.items():
            result, sample = _fit_panel(stability, outcome.model_column, predictors)
            fits.append(
                ModelFit(
                    outcome_key=outcome.key,
                    outcome_label=outcome.label,
                    model_column=outcome.model_column,
                    model_type=model_type,
                    sample_mode=sample_mode,
                    result=result,
                    sample=sample,
                    focal_terms=(POPULISM,),
                )
            )
    return fits


def _term_statistics(result: PanelEffectsResults, term: str) -> dict[str, float]:
    if term not in result.params.index:
        return {
            "coefficient": np.nan,
            "std_error": np.nan,
            "p_value": np.nan,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
    confidence = result.conf_int().loc[term]
    return {
        "coefficient": float(result.params[term]),
        "std_error": float(result.std_errors[term]),
        "p_value": float(result.pvalues[term]),
        "ci_low": float(confidence["lower"]),
        "ci_high": float(confidence["upper"]),
    }


def _standardisation_factor(sample: pd.DataFrame, cause: str, dependent: str) -> float:
    flat = sample.reset_index()
    denominator = within_sd(flat, dependent)
    numerator = within_sd(flat, cause)
    if not np.isfinite(denominator) or denominator <= 0:
        return np.nan
    return numerator / denominator


def association_results_table(fits: list[ModelFit]) -> pd.DataFrame:
    """Return raw and within-standardised association estimates."""
    rows = []
    for fit in fits:
        term = fit.focal_terms[0]
        estimates = _term_statistics(fit.result, term)
        factor = _standardisation_factor(fit.sample, POPULISM, fit.model_column)
        rows.append(
            {
                "outcome_key": fit.outcome_key,
                "outcome": fit.outcome_label,
                "model": fit.model_type,
                "sample_mode": fit.sample_mode,
                **estimates,
                "standardized_coefficient": estimates["coefficient"] * factor,
                "standardized_ci_low": estimates["ci_low"] * factor,
                "standardized_ci_high": estimates["ci_high"] * factor,
                "within_r2": float(fit.result.rsquared_within),
                "n_obs": fit.n_obs,
                "n_countries": fit.n_countries,
                "country_fe": True,
                "year_fe": True,
                "clustered_by_country": True,
            }
        )
    return pd.DataFrame(rows)


def _direction_columns(outcome: OutcomeSpec, direction: Direction) -> tuple[str, str]:
    if direction == "populism_to_corruption":
        return outcome.model_column, POPULISM
    if direction == "corruption_to_populism":
        return POPULISM, outcome.model_column
    raise ValueError(f"Unknown direction: {direction}")


def _lag_terms(column: str, order: int) -> tuple[str, ...]:
    return tuple(f"{column}_lag{lag}" for lag in range(1, order + 1))


def _lead_terms(column: str, order: int) -> tuple[str, ...]:
    return tuple(f"{column}_lead{lead}" for lead in range(1, order + 1))


def _common_direction_columns(direction: Direction, model_type: str, lag_order: int) -> list[str]:
    outcome_lags = [
        f"{outcome.model_column}_lag{lag}"
        for outcome in OUTCOMES
        for lag in range(1, lag_order + 1)
    ]
    if direction == "populism_to_corruption":
        columns = [*MODEL_OUTCOMES, *_lag_terms(POPULISM, lag_order), *CONTROLS]
        if model_type == "granger":
            columns.extend(outcome_lags)
        return list(dict.fromkeys(columns))
    columns = [POPULISM, *outcome_lags, *CONTROLS]
    if model_type == "granger":
        columns.extend(_lag_terms(POPULISM, lag_order))
    return list(dict.fromkeys(columns))


def fit_direction_models(
    df: pd.DataFrame,
    sample_mode: SampleMode = "outcome_specific",
    lag_order: int = 2,
) -> list[ModelFit]:
    """Fit lead-lag and Granger-style models in both directions for every outcome."""
    if sample_mode not in ("outcome_specific", "common"):
        raise ValueError(f"Unknown sample mode: {sample_mode}")
    shifted = add_panel_shifts(prepare_panel(df), lags=tuple(range(1, lag_order + 1)))
    fits: list[ModelFit] = []
    for outcome in OUTCOMES:
        for direction in ("populism_to_corruption", "corruption_to_populism"):
            dependent, cause = _direction_columns(outcome, direction)
            cause_terms = _lag_terms(cause, lag_order)
            for model_type in ("lead_lag", "granger"):
                own_terms = _lag_terms(dependent, lag_order) if model_type == "granger" else ()
                predictors = [*own_terms, *cause_terms, *CONTROLS]
                if sample_mode == "common":
                    required = _common_direction_columns(direction, model_type, lag_order)
                    base_sample = shifted.dropna(subset=required)
                else:
                    base_sample = shifted
                result, sample = _fit_panel(base_sample, dependent, predictors)
                fits.append(
                    ModelFit(
                        outcome_key=outcome.key,
                        outcome_label=outcome.label,
                        model_column=outcome.model_column,
                        model_type=model_type,
                        sample_mode=sample_mode,
                        result=result,
                        sample=sample,
                        focal_terms=cause_terms,
                        direction=direction,
                        cause_column=cause,
                    )
                )
    return fits


def joint_wald_test(result: PanelEffectsResults, terms: tuple[str, ...]) -> dict[str, float]:
    """Wald test of the joint null that all selected coefficients are zero."""
    present = [term for term in terms if term in result.params.index]
    if not present:
        return {"joint_statistic": np.nan, "joint_p_value": np.nan, "joint_df": 0}
    coefficients = result.params.loc[present].to_numpy()
    covariance = result.cov.loc[present, present].to_numpy()
    statistic = float(coefficients.T @ np.linalg.pinv(covariance) @ coefficients)
    degrees = len(present)
    return {
        "joint_statistic": statistic,
        "joint_p_value": float(stats.chi2.sf(statistic, degrees)),
        "joint_df": degrees,
    }


def direction_results_tables(fits: list[ModelFit]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return one model-level joint-test table and one term-level coefficient table."""
    model_rows: list[dict[str, object]] = []
    term_rows: list[dict[str, object]] = []
    for fit in fits:
        if fit.direction is None or fit.cause_column is None:
            raise ValueError("Direction metadata is required")
        joint = joint_wald_test(fit.result, fit.focal_terms)
        dependent = fit.model_column if fit.direction == "populism_to_corruption" else POPULISM
        # Standardise by the actual lagged cause present in the estimation sample. This avoids
        # importing contemporaneous values that were not part of the fitted design matrix.
        factor = _standardisation_factor(fit.sample, fit.focal_terms[0], dependent)
        model_rows.append(
            {
                "outcome_key": fit.outcome_key,
                "outcome": fit.outcome_label,
                "direction": fit.direction,
                "model": fit.model_type,
                "sample_mode": fit.sample_mode,
                **joint,
                "within_r2": float(fit.result.rsquared_within),
                "n_obs": fit.n_obs,
                "n_countries": fit.n_countries,
                "country_fe": True,
                "year_fe": True,
                "clustered_by_country": True,
            }
        )
        for lag, term in enumerate(fit.focal_terms, start=1):
            estimates = _term_statistics(fit.result, term)
            term_rows.append(
                {
                    "outcome_key": fit.outcome_key,
                    "outcome": fit.outcome_label,
                    "direction": fit.direction,
                    "model": fit.model_type,
                    "sample_mode": fit.sample_mode,
                    "lag": lag,
                    "term": term,
                    **estimates,
                    "standardized_coefficient": estimates["coefficient"] * factor,
                    "standardized_ci_low": estimates["ci_low"] * factor,
                    "standardized_ci_high": estimates["ci_high"] * factor,
                    "n_obs": fit.n_obs,
                    "n_countries": fit.n_countries,
                }
            )
    return pd.DataFrame(model_rows), pd.DataFrame(term_rows)


def fit_placebo_leads(df: pd.DataFrame, lag_order: int = 2, lead_order: int = 2) -> pd.DataFrame:
    """Test whether future proposed-cause values jointly predict the current outcome."""
    shifted = add_panel_shifts(
        prepare_panel(df),
        lags=tuple(range(1, lag_order + 1)),
        leads=tuple(range(1, lead_order + 1)),
    )
    rows = []
    for outcome in OUTCOMES:
        for direction in ("populism_to_corruption", "corruption_to_populism"):
            dependent, cause = _direction_columns(outcome, direction)
            lag_terms = _lag_terms(cause, lag_order)
            lead_terms = _lead_terms(cause, lead_order)
            predictors = [*lag_terms, *lead_terms, *CONTROLS]
            result, sample = _fit_panel(shifted, dependent, predictors)
            joint = joint_wald_test(result, lead_terms)
            rows.append(
                {
                    "outcome_key": outcome.key,
                    "outcome": outcome.label,
                    "direction": direction,
                    **joint,
                    "n_obs": int(sample.shape[0]),
                    "n_countries": int(sample.index.get_level_values(ENTITY).nunique()),
                }
            )
    return pd.DataFrame(rows)


def fit_first_differences(df: pd.DataFrame) -> pd.DataFrame:
    """First-difference robustness: delta outcome on lagged delta proposed cause."""
    prepared = prepare_panel(df)
    rows = []
    for outcome in OUTCOMES:
        for direction in ("populism_to_corruption", "corruption_to_populism"):
            dependent, cause = _direction_columns(outcome, direction)
            working = prepared.sort_values([ENTITY, TIME]).copy()
            dependent_delta = f"delta_{dependent}"
            cause_delta = f"delta_{cause}"
            cause_delta_lag = f"{cause_delta}_lag1"
            working[dependent_delta] = working.groupby(ENTITY)[dependent].diff()
            working[cause_delta] = working.groupby(ENTITY)[cause].diff()
            working[cause_delta_lag] = working.groupby(ENTITY)[cause_delta].shift(1)
            delta_controls = []
            for control in CONTROLS:
                delta = f"delta_{control}"
                working[delta] = working.groupby(ENTITY)[control].diff()
                delta_controls.append(delta)
            predictors = [cause_delta_lag, *delta_controls]
            result, sample = _fit_panel(
                working,
                dependent_delta,
                predictors,
                entity_effects=False,
                time_effects=True,
            )
            estimates = _term_statistics(result, cause_delta_lag)
            sample_flat = sample.reset_index()
            cause_sd = float(sample_flat[cause_delta_lag].std(ddof=1))
            dependent_sd = float(sample_flat[dependent_delta].std(ddof=1))
            factor = cause_sd / dependent_sd if dependent_sd > 0 else np.nan
            rows.append(
                {
                    "outcome_key": outcome.key,
                    "outcome": outcome.label,
                    "direction": direction,
                    **estimates,
                    "standardized_coefficient": estimates["coefficient"] * factor,
                    "n_obs": int(sample.shape[0]),
                    "n_countries": int(sample.index.get_level_values(ENTITY).nunique()),
                }
            )
    return pd.DataFrame(rows)


def fit_association_robustness(df: pd.DataFrame) -> pd.DataFrame:
    """M3 association under alternative covariance estimators and first differences."""
    prepared = prepare_panel(df)
    rows = []
    for outcome in OUTCOMES:
        columns = [ENTITY, TIME, outcome.model_column, POPULISM, *CONTROLS]
        sample = prepared[columns].dropna().copy()
        indexed = sample.set_index([ENTITY, TIME])
        predictors = [POPULISM, *CONTROLS]
        model = PanelOLS(
            indexed[outcome.model_column],
            indexed[predictors],
            entity_effects=True,
            time_effects=True,
            drop_absorbed=True,
            check_rank=False,
        )
        estimates = {
            "cluster_country": model.fit(cov_type="clustered", cluster_entity=True),
            "cluster_country_year": model.fit(
                cov_type="clustered", cluster_entity=True, cluster_time=True
            ),
            "driscoll_kraay": model.fit(cov_type="kernel", kernel="bartlett"),
        }
        factor = _standardisation_factor(indexed, POPULISM, outcome.model_column)
        for estimator, result in estimates.items():
            statistics = _term_statistics(result, POPULISM)
            rows.append(
                {
                    "outcome_key": outcome.key,
                    "outcome": outcome.label,
                    "estimator": estimator,
                    **statistics,
                    "standardized_coefficient": statistics["coefficient"] * factor,
                    "n_obs": int(indexed.shape[0]),
                    "n_countries": int(indexed.index.get_level_values(ENTITY).nunique()),
                }
            )

        working = prepared.sort_values([ENTITY, TIME]).copy()
        dependent_delta = f"delta_{outcome.model_column}"
        working[dependent_delta] = working.groupby(ENTITY)[outcome.model_column].diff()
        delta_predictors = []
        for column in (POPULISM, *CONTROLS):
            delta = f"delta_{column}"
            working[delta] = working.groupby(ENTITY)[column].diff()
            delta_predictors.append(delta)
        result, difference_sample = _fit_panel(
            working,
            dependent_delta,
            delta_predictors,
            entity_effects=False,
            time_effects=True,
        )
        focal = f"delta_{POPULISM}"
        statistics = _term_statistics(result, focal)
        flat = difference_sample.reset_index()
        dependent_sd = float(flat[dependent_delta].std(ddof=1))
        predictor_sd = float(flat[focal].std(ddof=1))
        difference_factor = predictor_sd / dependent_sd if dependent_sd > 0 else np.nan
        rows.append(
            {
                "outcome_key": outcome.key,
                "outcome": outcome.label,
                "estimator": "first_difference",
                **statistics,
                "standardized_coefficient": statistics["coefficient"] * difference_factor,
                "n_obs": int(difference_sample.shape[0]),
                "n_countries": int(difference_sample.index.get_level_values(ENTITY).nunique()),
            }
        )

    table = pd.DataFrame(rows)
    table["fdr_q_value"] = np.nan
    for estimator in table["estimator"].unique():
        mask = (table["estimator"] == estimator) & table["outcome_key"].isin(SUBTYPE_KEYS)
        table.loc[mask, "fdr_q_value"] = benjamini_hochberg(table.loc[mask, "p_value"])
    table["reject_fdr_05"] = table["fdr_q_value"] < 0.05
    return table


def fit_measurement_robustness(df: pd.DataFrame) -> pd.DataFrame:
    """Compare continuous and coarse ordinal legislative/judicial M3 outcomes."""
    prepared = prepare_panel(df)
    rows = []
    for key in ("legislative", "judicial"):
        outcome = OUTCOME_BY_KEY[key]
        measures = {
            "continuous_latent_primary": outcome.model_column,
            "five_level_ordinal_01": outcome.descriptive_column,
        }
        frozen = prepared.dropna(subset=[*measures.values(), POPULISM, *CONTROLS])
        for measure, dependent in measures.items():
            result, sample = _fit_panel(frozen, dependent, [POPULISM, *CONTROLS])
            statistics = _term_statistics(result, POPULISM)
            factor = _standardisation_factor(sample, POPULISM, dependent)
            rows.append(
                {
                    "outcome_key": key,
                    "outcome": outcome.label,
                    "measure": measure,
                    **statistics,
                    "standardized_coefficient": statistics["coefficient"] * factor,
                    "n_obs": int(sample.shape[0]),
                    "n_countries": int(sample.index.get_level_values(ENTITY).nunique()),
                }
            )
    return pd.DataFrame(rows)


def fit_democracy_interactions(
    df: pd.DataFrame, quantiles: tuple[float, ...] = (0.1, 0.5, 0.9)
) -> pd.DataFrame:
    """Contemporaneous M3 slopes of populism at representative democracy levels."""
    prepared = prepare_panel(df)
    rows = []
    interaction = "populism_x_polyarchy"
    prepared[interaction] = prepared[POPULISM] * prepared["v2x_polyarchy"]
    predictors = [POPULISM, interaction, *CONTROLS]
    for outcome in OUTCOMES:
        result, sample = _fit_panel(prepared, outcome.model_column, predictors)
        covariance = result.cov
        for quantile in quantiles:
            level = float(sample.reset_index()["v2x_polyarchy"].quantile(quantile))
            slope = float(result.params[POPULISM] + level * result.params[interaction])
            variance = float(
                covariance.loc[POPULISM, POPULISM]
                + level**2 * covariance.loc[interaction, interaction]
                + 2 * level * covariance.loc[POPULISM, interaction]
            )
            standard_error = float(np.sqrt(max(variance, 0)))
            z_value = slope / standard_error if standard_error > 0 else np.nan
            p_value = float(2 * stats.norm.sf(abs(z_value))) if np.isfinite(z_value) else np.nan
            rows.append(
                {
                    "outcome_key": outcome.key,
                    "outcome": outcome.label,
                    "polyarchy_quantile": quantile,
                    "polyarchy_value": level,
                    "marginal_slope": slope,
                    "std_error": standard_error,
                    "ci_low": slope - 1.96 * standard_error,
                    "ci_high": slope + 1.96 * standard_error,
                    "p_value": p_value,
                    "interaction_coefficient": float(result.params[interaction]),
                    "interaction_p_value": float(result.pvalues[interaction]),
                    "n_obs": int(sample.shape[0]),
                    "n_countries": int(sample.index.get_level_values(ENTITY).nunique()),
                }
            )
    return pd.DataFrame(rows)


def fit_electoral_sample_robustness(df: pd.DataFrame, lag_order: int = 2) -> pd.DataFrame:
    """Populism-to-corruption lead-lag estimates under forward-fill-related samples."""
    prepared = add_panel_shifts(prepare_panel(df), lags=tuple(range(1, lag_order + 1)))
    prepared["government_change_year"] = prepared.groupby(ENTITY)[POPULISM].diff().abs() > 1e-8
    samples = {
        "all": prepared,
        "election_years": prepared[prepared["is_election_year"].astype(bool)],
        "government_change_years": prepared[prepared["government_change_year"]],
        "ffill_le5": prepared[prepared["years_since_last_election"] <= 5],
        "ffill_le10": prepared[prepared["years_since_last_election"] <= 10],
    }
    rows = []
    cause_terms = _lag_terms(POPULISM, lag_order)
    for outcome in OUTCOMES:
        predictors = [*cause_terms, *CONTROLS]
        for sample_name, data in samples.items():
            result, sample = _fit_panel(data, outcome.model_column, predictors)
            joint = joint_wald_test(result, cause_terms)
            lag1 = _term_statistics(result, cause_terms[0])
            rows.append(
                {
                    "outcome_key": outcome.key,
                    "outcome": outcome.label,
                    "sample": sample_name,
                    **joint,
                    "lag1_coefficient": lag1["coefficient"],
                    "lag1_ci_low": lag1["ci_low"],
                    "lag1_ci_high": lag1["ci_high"],
                    "lag1_p_value": lag1["p_value"],
                    "n_obs": int(sample.shape[0]),
                    "n_countries": int(sample.index.get_level_values(ENTITY).nunique()),
                }
            )
    return pd.DataFrame(rows)


def benjamini_hochberg(p_values: pd.Series | np.ndarray | list[float]) -> np.ndarray:
    """Benjamini–Hochberg adjusted p-values, preserving NaNs and input order."""
    values = np.asarray(p_values, dtype=float)
    adjusted = np.full(values.shape, np.nan, dtype=float)
    valid_positions = np.flatnonzero(np.isfinite(values))
    if not len(valid_positions):
        return adjusted
    valid = values[valid_positions]
    order = np.argsort(valid)
    ranked = valid[order]
    m = len(ranked)
    ranked_adjusted = ranked * m / np.arange(1, m + 1)
    ranked_adjusted = np.minimum.accumulate(ranked_adjusted[::-1])[::-1]
    ranked_adjusted = np.clip(ranked_adjusted, 0, 1)
    restored = np.empty(m, dtype=float)
    restored[order] = ranked_adjusted
    adjusted[valid_positions] = restored
    return adjusted


def add_association_fdr(table: pd.DataFrame) -> pd.DataFrame:
    """Add four-subtype FDR q-values separately for each sample mode's M3 family."""
    out = table.copy()
    out["fdr_q_value"] = np.nan
    for sample_mode in out["sample_mode"].unique():
        mask = (
            (out["sample_mode"] == sample_mode)
            & (out["model"] == "M3")
            & out["outcome_key"].isin(SUBTYPE_KEYS)
        )
        out.loc[mask, "fdr_q_value"] = benjamini_hochberg(out.loc[mask, "p_value"])
    out["reject_fdr_05"] = out["fdr_q_value"] < 0.05
    return out


def add_direction_fdr(table: pd.DataFrame, p_column: str = "joint_p_value") -> pd.DataFrame:
    """Add FDR over the eight subtype-by-direction tests for every model/sample family."""
    out = table.copy()
    out["fdr_q_value"] = np.nan
    group_columns = [column for column in ("model", "sample_mode") if column in out.columns]
    groups = out.groupby(group_columns, dropna=False) if group_columns else [(None, out)]
    for _, group in groups:
        mask = out.index.isin(group.index) & out["outcome_key"].isin(SUBTYPE_KEYS)
        out.loc[mask, "fdr_q_value"] = benjamini_hochberg(out.loc[mask, p_column])
    out["reject_fdr_05"] = out["fdr_q_value"] < 0.05
    return out


def run_complete_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Execute every pre-declared Task 5 model and return reproducible result tables."""
    diagnostics = outcome_diagnostics(df)
    association_fits = [
        *fit_association_models(df, "outcome_specific"),
        *fit_association_models(df, "common"),
    ]
    association = add_association_fdr(association_results_table(association_fits))

    direction_fits = [
        *fit_direction_models(df, "outcome_specific"),
        *fit_direction_models(df, "common"),
    ]
    direction_models, direction_terms = direction_results_tables(direction_fits)
    direction_models = add_direction_fdr(direction_models)

    placebo = fit_placebo_leads(df)
    placebo["model"] = "placebo_leads"
    placebo["sample_mode"] = "outcome_specific"
    placebo = add_direction_fdr(placebo)

    first_differences = fit_first_differences(df)
    first_differences["model"] = "first_difference"
    first_differences["sample_mode"] = "outcome_specific"
    first_differences = add_direction_fdr(first_differences, "p_value")

    return {
        "diagnostics": diagnostics,
        "association": association,
        "direction_models": direction_models,
        "direction_terms": direction_terms,
        "placebo": placebo,
        "first_differences": first_differences,
        "association_robustness": fit_association_robustness(df),
        "measurement_robustness": fit_measurement_robustness(df),
        "democracy_interactions": fit_democracy_interactions(df),
        "electoral_robustness": fit_electoral_sample_robustness(df),
    }
