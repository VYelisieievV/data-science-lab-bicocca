"""Panel lead-lag and Granger-style models for causal-direction analysis.

The scope is deliberately narrow: this module studies temporal ordering between
governing-party populism and the overall V-Dem political corruption index, ``v2x_corr``."""

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
CORRUPTION = "v2x_corr"

Direction = Literal["populism_to_corruption", "corruption_to_populism"]
RobustnessSample = Literal[
    "all",
    "election_years",
    "government_change_years",
    "ffill_le5",
    "ffill_le10",
]

REQUIRED_COLUMNS = [
    ENTITY,
    "country_name",
    TIME,
    POPULISM,
    CORRUPTION,
    "log_gdppc",
    "v2x_polyarchy",
    "years_since_last_election",
]


@dataclass
class DirectionFit:
    """One fitted directional panel model plus metadata needed for report tables."""

    model_id: str
    direction: Direction
    dependent: str
    proposed_cause: str
    lag_order: int
    model_type: str
    controls: tuple[str, ...]
    result: PanelEffectsResults
    sample: pd.DataFrame
    cause_terms: tuple[str, ...]
    own_lag_terms: tuple[str, ...]

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())


@dataclass
class PlaceboFit:
    """Lead placebo model with past and future proposed-cause terms."""

    model_id: str
    direction: Direction
    dependent: str
    proposed_cause: str
    lag_terms: tuple[str, ...]
    lead_terms: tuple[str, ...]
    controls: tuple[str, ...]
    result: PanelEffectsResults
    sample: pd.DataFrame

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())


@dataclass
class EventStudyFit:
    """Event-study model around directional events."""

    model_id: str
    direction: Direction
    dependent: str
    event_definition: str
    event_terms: tuple[str, ...]
    event_times: tuple[int, ...]
    reference_time: int
    controls: tuple[str, ...]
    result: PanelEffectsResults
    sample: pd.DataFrame
    events: pd.DataFrame

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())

    @property
    def n_events(self) -> int:
        return int(self.events.shape[0])


@dataclass
class FirstDifferenceFit:
    """First-difference directional check with year effects."""

    model_id: str
    direction: Direction
    dependent_delta: str
    cause_delta_lag: str
    controls: tuple[str, ...]
    result: PanelEffectsResults
    sample: pd.DataFrame

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())


@dataclass
class InteractionFit:
    """Populism-lag model allowing the slope to vary with electoral democracy."""

    model_id: str
    lag_order: int
    controls: tuple[str, ...]
    result: PanelEffectsResults
    sample: pd.DataFrame
    lag_terms: tuple[str, ...]
    interaction_terms: tuple[str, ...]

    @property
    def n_obs(self) -> int:
        return int(self.sample.shape[0])

    @property
    def n_countries(self) -> int:
        return int(self.sample.index.get_level_values(ENTITY).nunique())


def validate_panel(df: pd.DataFrame, required_cols: list[str] | None = None) -> dict[str, int]:
    """Validate the country-year panel and return a compact diagnostic summary."""
    required = required_cols or REQUIRED_COLUMNS
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    duplicate_count = int(df.duplicated([ENTITY, TIME]).sum())
    if duplicate_count:
        raise ValueError(f"Panel contains {duplicate_count} duplicate country-year rows")

    ordered = df.sort_values([ENTITY, TIME])
    year_diff = ordered.groupby(ENTITY)[TIME].diff()
    gap_count = int(year_diff[(year_diff.notna()) & (year_diff != 1)].shape[0])
    if gap_count:
        raise ValueError(f"Panel contains {gap_count} internal non-annual gaps")

    return {
        "n_rows": int(df.shape[0]),
        "n_countries": int(df[ENTITY].nunique()),
        "min_year": int(df[TIME].min()),
        "max_year": int(df[TIME].max()),
        "duplicates": duplicate_count,
        "internal_year_gaps": gap_count,
    }


def ensure_panel_lags(
    df: pd.DataFrame,
    variables: tuple[str, ...] = (POPULISM, CORRUPTION),
    lags: tuple[int, ...] = (1, 2, 3, 5),
    leads: tuple[int, ...] = (1, 2),
) -> pd.DataFrame:
    """Return a copy with within-country lag/lead columns for the requested variables."""
    out = df.sort_values([ENTITY, TIME]).copy()
    for variable in variables:
        for lag in lags:
            col = f"{variable}_lag{lag}"
            out[col] = out.groupby(ENTITY)[variable].shift(lag)
        for lead in leads:
            col = f"{variable}_lead{lead}"
            out[col] = out.groupby(ENTITY)[variable].shift(-lead)
    return out


def panel_autocorrelation(df: pd.DataFrame, variable: str, lag: int = 1) -> float:
    """Pooled within-panel autocorrelation between ``variable_t`` and ``variable_t-lag``."""
    lagged = (
        df.sort_values([ENTITY, TIME])
        .assign(_lag=lambda x: x.groupby(ENTITY)[variable].shift(lag))
        [[variable, "_lag"]]
        .dropna()
    )
    return float(lagged[variable].corr(lagged["_lag"]))


def _direction_columns(direction: Direction) -> tuple[str, str]:
    if direction == "populism_to_corruption":
        return CORRUPTION, POPULISM
    if direction == "corruption_to_populism":
        return POPULISM, CORRUPTION
    raise ValueError(f"Unknown direction: {direction}")


def _lag_terms(variable: str, lag_order: int) -> tuple[str, ...]:
    return tuple(f"{variable}_lag{lag}" for lag in range(1, lag_order + 1))


def _lead_terms(variable: str, lead_order: int) -> tuple[str, ...]:
    return tuple(f"{variable}_lead{lead}" for lead in range(1, lead_order + 1))


def _fit_panel_ols(sample: pd.DataFrame, y_col: str, x_cols: list[str]) -> PanelEffectsResults:
    indexed = sample.set_index([ENTITY, TIME])
    model = PanelOLS(
        indexed[y_col],
        indexed[x_cols],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    return model.fit(cov_type="clustered", cluster_entity=True)


def _with_government_change_flag(df: pd.DataFrame, threshold: float = 1e-8) -> pd.DataFrame:
    out = df.sort_values([ENTITY, TIME]).copy()
    out["governing_populism_change"] = out.groupby(ENTITY)[POPULISM].diff().abs() > threshold
    return out


def _filter_robustness_sample(
    df: pd.DataFrame, sample_name: RobustnessSample
) -> pd.DataFrame:
    if sample_name == "all":
        return df.copy()
    if sample_name == "election_years":
        return df[df["is_election_year"].astype(bool)].copy()
    if sample_name == "government_change_years":
        flagged = _with_government_change_flag(df)
        return flagged[flagged["governing_populism_change"]].copy()
    if sample_name == "ffill_le5":
        return df[df["years_since_last_election"] <= 5].copy()
    if sample_name == "ffill_le10":
        return df[df["years_since_last_election"] <= 10].copy()
    raise ValueError(f"Unknown robustness sample: {sample_name}")


def fit_lead_lag(
    df: pd.DataFrame,
    direction: Direction,
    lag_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
    max_years_since_election: int | None = None,
) -> DirectionFit:
    """Fit a two-way-FE lead-lag model in one proposed direction."""
    dependent, cause = _direction_columns(direction)
    cause_terms = _lag_terms(cause, lag_order)
    x_cols = [*cause_terms, *controls]
    cols = [ENTITY, TIME, dependent, *x_cols]
    sample = df.copy()
    if max_years_since_election is not None:
        sample = sample[sample["years_since_last_election"] <= max_years_since_election]
    sample = sample.dropna(subset=[dependent, *x_cols])
    result = _fit_panel_ols(sample[cols], dependent, x_cols)
    return DirectionFit(
        model_id=f"lead_lag_{direction}_L{lag_order}",
        direction=direction,
        dependent=dependent,
        proposed_cause=cause,
        lag_order=lag_order,
        model_type="lead_lag_fe",
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
        cause_terms=cause_terms,
        own_lag_terms=(),
    )


def fit_granger_style(
    df: pd.DataFrame,
    direction: Direction,
    lag_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
    max_years_since_election: int | None = None,
) -> DirectionFit:
    """Fit a Granger-style two-way-FE model with own lags and proposed-cause lags."""
    dependent, cause = _direction_columns(direction)
    cause_terms = _lag_terms(cause, lag_order)
    own_lag_terms = _lag_terms(dependent, lag_order)
    x_cols = [*own_lag_terms, *cause_terms, *controls]
    cols = [ENTITY, TIME, dependent, *x_cols]
    sample = df.copy()
    if max_years_since_election is not None:
        sample = sample[sample["years_since_last_election"] <= max_years_since_election]
    sample = sample.dropna(subset=[dependent, *x_cols])
    result = _fit_panel_ols(sample[cols], dependent, x_cols)
    return DirectionFit(
        model_id=f"granger_{direction}_L{lag_order}",
        direction=direction,
        dependent=dependent,
        proposed_cause=cause,
        lag_order=lag_order,
        model_type="granger_style_fe",
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
        cause_terms=cause_terms,
        own_lag_terms=own_lag_terms,
    )


def fit_placebo_lead_test(
    df: pd.DataFrame,
    direction: Direction = "populism_to_corruption",
    lag_order: int = 2,
    lead_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> PlaceboFit:
    """Fit a placebo model with future proposed-cause leads.

    The proposed cause's future values should not causally affect the current outcome. Significant
    lead terms are read as a warning sign for pre-trends, anticipation, or omitted confounding.
    """
    dependent, cause = _direction_columns(direction)
    working = ensure_panel_lags(
        df,
        variables=(cause,),
        lags=tuple(range(1, lag_order + 1)),
        leads=tuple(range(1, lead_order + 1)),
    )
    lag_terms = _lag_terms(cause, lag_order)
    lead_terms = _lead_terms(cause, lead_order)
    x_cols = [*lag_terms, *lead_terms, *controls]
    cols = [ENTITY, TIME, dependent, *x_cols]
    sample = working.dropna(subset=[dependent, *x_cols])
    result = _fit_panel_ols(sample[cols], dependent, x_cols)
    return PlaceboFit(
        model_id=f"placebo_{direction}_L{lag_order}_F{lead_order}",
        direction=direction,
        dependent=dependent,
        proposed_cause=cause,
        lag_terms=lag_terms,
        lead_terms=lead_terms,
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
    )


def placebo_results_table(fit: PlaceboFit) -> pd.DataFrame:
    """Report-ready table for the placebo lead test."""
    rows = []
    for kind, terms in (("lag", fit.lag_terms), ("lead_placebo", fit.lead_terms)):
        for order, term in enumerate(terms, start=1):
            stats_ = _term_stats(fit.result, term)
            rows.append(
                {
                    "model": fit.model_id,
                    "direction": fit.direction,
                    "outcome": fit.dependent,
                    "proposed_cause": fit.proposed_cause,
                    "term_type": kind,
                    "order": order,
                    "term": term,
                    "coef": stats_["coef"],
                    "se": stats_["se"],
                    "p": stats_["p"],
                    "ci_low": stats_["ci_low"],
                    "ci_high": stats_["ci_high"],
                    "n_obs": fit.n_obs,
                    "n_countries": fit.n_countries,
                }
            )
    lead_wald = joint_wald_test(fit.result, fit.lead_terms)
    out = pd.DataFrame(rows)
    out["lead_joint_p"] = lead_wald["joint_p"]
    out["lead_joint_df"] = lead_wald["joint_df"]
    out["placebo_warning"] = lead_wald["joint_p"] < 0.05
    return out


def populist_entry_events(
    df: pd.DataFrame,
    min_increase: float = 0.10,
    min_level: float = 0.50,
    first_event_only: bool = True,
) -> pd.DataFrame:
    """Identify large election-year jumps into a high-populism government."""
    working = df.sort_values([ENTITY, TIME]).copy()
    working["populism_change"] = working.groupby(ENTITY)[POPULISM].diff()
    events = working[
        (working["is_election_year"].astype(bool))
        & (working["populism_change"] >= min_increase)
        & (working[POPULISM] >= min_level)
    ][[ENTITY, "country_name", TIME, POPULISM, "populism_change"]].copy()
    events = events.rename(columns={TIME: "event_year", POPULISM: "event_populism"})
    if first_event_only:
        events = events.sort_values([ENTITY, "event_year"]).groupby(ENTITY, as_index=False).head(1)
    return events.reset_index(drop=True)


def corruption_shock_events(
    df: pd.DataFrame,
    min_increase: float = 0.05,
    first_event_only: bool = True,
) -> pd.DataFrame:
    """Identify large within-country increases in overall corruption."""
    working = df.sort_values([ENTITY, TIME]).copy()
    working["corruption_change"] = working.groupby(ENTITY)[CORRUPTION].diff()
    events = working[working["corruption_change"] >= min_increase][
        [ENTITY, "country_name", TIME, CORRUPTION, "corruption_change"]
    ].copy()
    events = events.rename(columns={TIME: "event_year", CORRUPTION: "event_corruption"})
    if first_event_only:
        events = events.sort_values([ENTITY, "event_year"]).groupby(ENTITY, as_index=False).head(1)
    return events.reset_index(drop=True)


def _event_term(event_time: int) -> str:
    return f"event_m{abs(event_time)}" if event_time < 0 else f"event_p{event_time}"


def fit_event_study(
    df: pd.DataFrame,
    window: tuple[int, int] = (-3, 5),
    reference_time: int = -1,
    min_increase: float = 0.10,
    min_level: float = 0.50,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> EventStudyFit:
    """Fit a TWFE event-study around first large populist-government entry events."""
    events = populist_entry_events(df, min_increase=min_increase, min_level=min_level)
    event_year_map = events.set_index(ENTITY)["event_year"].to_dict()
    event_panel = df.copy()
    event_panel["event_year"] = event_panel[ENTITY].map(event_year_map)
    event_panel["event_time"] = event_panel[TIME] - event_panel["event_year"]
    event_times = tuple(t for t in range(window[0], window[1] + 1) if t != reference_time)
    event_terms = tuple(_event_term(t) for t in event_times)
    sample = event_panel.dropna(subset=[CORRUPTION, *controls]).copy()
    for event_time, term in zip(event_times, event_terms):
        sample[term] = (sample["event_time"] == event_time).astype(float)
    x_cols = [*event_terms, *controls]
    cols = [ENTITY, TIME, CORRUPTION, *x_cols]
    result = _fit_panel_ols(sample[cols], CORRUPTION, x_cols)
    definition = (
        f"first election-year increase in governing populism >= {min_increase:.2f} "
        f"ending at populism >= {min_level:.2f}"
    )
    return EventStudyFit(
        model_id="event_study_populist_entry",
        direction="populism_to_corruption",
        dependent=CORRUPTION,
        event_definition=definition,
        event_terms=event_terms,
        event_times=event_times,
        reference_time=reference_time,
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
        events=events,
    )


def fit_corruption_shock_event_study(
    df: pd.DataFrame,
    window: tuple[int, int] = (-3, 2),
    reference_time: int = -1,
    min_increase: float = 0.05,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> EventStudyFit:
    """Fit a TWFE event-study around first large corruption increases."""
    events = corruption_shock_events(df, min_increase=min_increase)
    event_year_map = events.set_index(ENTITY)["event_year"].to_dict()
    event_panel = df.copy()
    event_panel["event_year"] = event_panel[ENTITY].map(event_year_map)
    event_panel["event_time"] = event_panel[TIME] - event_panel["event_year"]
    event_times = tuple(t for t in range(window[0], window[1] + 1) if t != reference_time)
    event_terms = tuple(_event_term(t) for t in event_times)
    sample = event_panel.dropna(subset=[POPULISM, *controls]).copy()
    for event_time, term in zip(event_times, event_terms):
        sample[term] = (sample["event_time"] == event_time).astype(float)
    x_cols = [*event_terms, *controls]
    cols = [ENTITY, TIME, POPULISM, *x_cols]
    result = _fit_panel_ols(sample[cols], POPULISM, x_cols)
    definition = f"first within-country increase in v2x_corr >= {min_increase:.2f}"
    return EventStudyFit(
        model_id="event_study_corruption_shock",
        direction="corruption_to_populism",
        dependent=POPULISM,
        event_definition=definition,
        event_terms=event_terms,
        event_times=event_times,
        reference_time=reference_time,
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
        events=events,
    )


def event_study_results_table(fit: EventStudyFit) -> pd.DataFrame:
    """Report-ready event-study coefficients, including the omitted reference period."""
    rows = [
        {
            "event_time": fit.reference_time,
            "term": "reference",
            "model": fit.model_id,
            "direction": fit.direction,
            "outcome": fit.dependent,
            "coef": 0.0,
            "se": np.nan,
            "p": np.nan,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "reference": True,
            "n_obs": fit.n_obs,
            "n_countries": fit.n_countries,
            "n_events": fit.n_events,
            "event_definition": fit.event_definition,
        }
    ]
    for event_time, term in zip(fit.event_times, fit.event_terms):
        stats_ = _term_stats(fit.result, term)
        rows.append(
            {
                "event_time": event_time,
                "term": term,
                "model": fit.model_id,
                "direction": fit.direction,
                "outcome": fit.dependent,
                "coef": stats_["coef"],
                "se": stats_["se"],
                "p": stats_["p"],
                "ci_low": stats_["ci_low"],
                "ci_high": stats_["ci_high"],
                "reference": False,
                "n_obs": fit.n_obs,
                "n_countries": fit.n_countries,
                "n_events": fit.n_events,
                "event_definition": fit.event_definition,
            }
        )
    out = pd.DataFrame(rows).sort_values("event_time").reset_index(drop=True)
    pre_terms = tuple(
        term for term, event_time in zip(fit.event_terms, fit.event_times) if event_time < 0
    )
    post_terms = tuple(
        term for term, event_time in zip(fit.event_terms, fit.event_times) if event_time >= 0
    )
    pre_wald = joint_wald_test(fit.result, pre_terms)
    post_wald = joint_wald_test(fit.result, post_terms)
    out["pretrend_joint_p"] = pre_wald["joint_p"]
    out["post_joint_p"] = post_wald["joint_p"]
    return out


def lag_order_information_criteria(
    df: pd.DataFrame,
    direction: Direction,
    max_lag: int = 5,
    model_type: Literal["lead_lag", "granger"] = "granger",
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> pd.DataFrame:
    """Compare lag windows using approximate Gaussian AIC/BIC with shrinking lag samples."""
    rows = []
    for lag_order in range(1, max_lag + 1):
        fit = (
            fit_granger_style(df, direction=direction, lag_order=lag_order, controls=controls)
            if model_type == "granger"
            else fit_lead_lag(df, direction=direction, lag_order=lag_order, controls=controls)
        )
        resid = np.asarray(fit.result.resids)
        n_obs = fit.n_obs
        rss = float(np.sum(resid**2))
        n_time_periods = fit.sample.index.get_level_values(TIME).nunique()
        k = int(len(fit.result.params) + fit.n_countries + n_time_periods)
        aic = n_obs * np.log(rss / n_obs) + 2 * k
        bic = n_obs * np.log(rss / n_obs) + np.log(n_obs) * k
        rows.append(
            {
                "direction": direction,
                "model_type": model_type,
                "lag_order": lag_order,
                "n_obs": n_obs,
                "n_countries": fit.n_countries,
                "rss": rss,
                "n_parameters_approx": k,
                "aic": float(aic),
                "bic": float(bic),
            }
        )
    out = pd.DataFrame(rows)
    out["best_aic"] = out["aic"] == out["aic"].min()
    out["best_bic"] = out["bic"] == out["bic"].min()
    return out


def fit_electoral_sample_robustness(
    df: pd.DataFrame,
    direction: Direction = "populism_to_corruption",
    lag_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
    samples: tuple[RobustnessSample, ...] = (
        "all",
        "election_years",
        "government_change_years",
        "ffill_le5",
        "ffill_le10",
    ),
) -> pd.DataFrame:
    """Re-estimate the lead-lag model on samples less exposed to forward-filled years."""
    rows = []
    for sample_name in samples:
        sample_df = _filter_robustness_sample(df, sample_name)
        try:
            fit = fit_lead_lag(
                sample_df,
                direction=direction,
                lag_order=lag_order,
                controls=controls,
            )
        except Exception as exc:  # pragma: no cover - defensive for very small custom samples
            rows.append(
                {
                    "sample": sample_name,
                    "direction": direction,
                    "lag_order": lag_order,
                    "error": str(exc),
                }
            )
            continue
        row = {
            "sample": sample_name,
            "direction": direction,
            "lag_order": lag_order,
            "n_obs": fit.n_obs,
            "n_countries": fit.n_countries,
            "controls": ", ".join(controls) if controls else "none",
            "error": "",
        }
        for idx, term in enumerate(fit.cause_terms, start=1):
            stats_ = _term_stats(fit.result, term)
            row[f"coef_lag{idx}"] = stats_["coef"]
            row[f"p_lag{idx}"] = stats_["p"]
            row[f"ci_low_lag{idx}"] = stats_["ci_low"]
            row[f"ci_high_lag{idx}"] = stats_["ci_high"]
        rows.append(row)
    return pd.DataFrame(rows)


def fit_first_difference_direction(
    df: pd.DataFrame,
    direction: Direction,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> FirstDifferenceFit:
    """Fit delta outcome on lagged delta proposed-cause, delta controls, and year effects."""
    dependent, cause = _direction_columns(direction)
    working = df.sort_values([ENTITY, TIME]).copy()
    dependent_delta = f"delta_{dependent}"
    cause_delta_lag = f"delta_{cause}_lag1"
    working[dependent_delta] = working.groupby(ENTITY)[dependent].diff()
    working[f"delta_{cause}"] = working.groupby(ENTITY)[cause].diff()
    working[cause_delta_lag] = working.groupby(ENTITY)[f"delta_{cause}"].shift(1)
    delta_controls = []
    for control in controls:
        delta_col = f"delta_{control}"
        working[delta_col] = working.groupby(ENTITY)[control].diff()
        delta_controls.append(delta_col)
    x_cols = [cause_delta_lag, *delta_controls]
    sample = working.dropna(subset=[dependent_delta, *x_cols]).copy()
    indexed = sample.set_index([ENTITY, TIME])
    model = PanelOLS(
        indexed[dependent_delta],
        indexed[x_cols],
        entity_effects=False,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    result = model.fit(cov_type="clustered", cluster_entity=True)
    return FirstDifferenceFit(
        model_id=f"first_difference_{direction}",
        direction=direction,
        dependent_delta=dependent_delta,
        cause_delta_lag=cause_delta_lag,
        controls=tuple(delta_controls),
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
    )


def first_difference_results_table(fits: list[FirstDifferenceFit]) -> pd.DataFrame:
    """Report-ready table for first-difference checks."""
    rows = []
    for fit in fits:
        stats_ = _term_stats(fit.result, fit.cause_delta_lag)
        rows.append(
            {
                "model": fit.model_id,
                "direction": fit.direction,
                "dependent_delta": fit.dependent_delta,
                "cause_delta_lag": fit.cause_delta_lag,
                "coef": stats_["coef"],
                "se": stats_["se"],
                "p": stats_["p"],
                "ci_low": stats_["ci_low"],
                "ci_high": stats_["ci_high"],
                "n_obs": fit.n_obs,
                "n_countries": fit.n_countries,
                "controls": ", ".join(fit.controls) if fit.controls else "none",
            }
        )
    return pd.DataFrame(rows)


def fit_democracy_interaction(
    df: pd.DataFrame,
    lag_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> InteractionFit:
    """Estimate whether lagged populism slopes differ by electoral democracy."""
    working = df.copy()
    lag_terms = _lag_terms(POPULISM, lag_order)
    interaction_terms = []
    for term in lag_terms:
        interaction = f"{term}_x_v2x_polyarchy"
        working[interaction] = working[term] * working["v2x_polyarchy"]
        interaction_terms.append(interaction)
    x_cols = [*lag_terms, *interaction_terms, *controls]
    sample = working.dropna(subset=[CORRUPTION, *x_cols]).copy()
    result = _fit_panel_ols(sample[[ENTITY, TIME, CORRUPTION, *x_cols]], CORRUPTION, x_cols)
    return InteractionFit(
        model_id=f"democracy_interaction_populism_to_corruption_L{lag_order}",
        lag_order=lag_order,
        controls=controls,
        result=result,
        sample=sample.set_index([ENTITY, TIME]),
        lag_terms=lag_terms,
        interaction_terms=tuple(interaction_terms),
    )


def democracy_interaction_table(
    fit: InteractionFit,
    democracy_values: tuple[float, ...] | None = None,
) -> pd.DataFrame:
    """Marginal lagged-populism slopes at low/median/high democracy values."""
    if democracy_values is None:
        poly = fit.sample["v2x_polyarchy"]
        democracy_values = tuple(float(poly.quantile(q)) for q in (0.10, 0.50, 0.90))
    labels = ("low_p10", "median_p50", "high_p90")
    rows = []
    for label, value in zip(labels, democracy_values):
        row = {
            "democracy_level": label,
            "v2x_polyarchy_value": value,
            "n_obs": fit.n_obs,
            "n_countries": fit.n_countries,
        }
        for idx, (lag_term, interaction_term) in enumerate(
            zip(fit.lag_terms, fit.interaction_terms), start=1
        ):
            params = fit.result.params
            cov = fit.result.cov
            coef = float(params[lag_term] + value * params[interaction_term])
            var = float(
                cov.loc[lag_term, lag_term]
                + value**2 * cov.loc[interaction_term, interaction_term]
                + 2 * value * cov.loc[lag_term, interaction_term]
            )
            se = float(np.sqrt(max(var, 0.0)))
            z = coef / se if se > 0 else np.nan
            p = float(2 * stats.norm.sf(abs(z))) if np.isfinite(z) else np.nan
            row[f"marginal_coef_lag{idx}"] = coef
            row[f"marginal_se_lag{idx}"] = se
            row[f"marginal_p_lag{idx}"] = p
            row[f"marginal_ci_low_lag{idx}"] = coef - 1.96 * se
            row[f"marginal_ci_high_lag{idx}"] = coef + 1.96 * se
        rows.append(row)
    return pd.DataFrame(rows)


def democracy_split_robustness(
    df: pd.DataFrame,
    lag_order: int = 2,
    controls: tuple[str, ...] = ("log_gdppc", "v2x_polyarchy"),
) -> pd.DataFrame:
    """Estimate populism-to-corruption lags separately in low/high democracy countries."""
    country_poly = df.groupby(ENTITY)["v2x_polyarchy"].mean()
    cutoff = float(country_poly.median())
    rows = []
    for group_name, countries in (
        ("low_democracy_countries", country_poly[country_poly <= cutoff].index),
        ("high_democracy_countries", country_poly[country_poly > cutoff].index),
    ):
        sub = df[df[ENTITY].isin(countries)].copy()
        fit = fit_lead_lag(
            sub,
            direction="populism_to_corruption",
            lag_order=lag_order,
            controls=controls,
        )
        row = {
            "democracy_group": group_name,
            "country_mean_polyarchy_cutoff": cutoff,
            "lag_order": lag_order,
            "n_obs": fit.n_obs,
            "n_countries": fit.n_countries,
        }
        for idx, term in enumerate(fit.cause_terms, start=1):
            stats_ = _term_stats(fit.result, term)
            row[f"coef_lag{idx}"] = stats_["coef"]
            row[f"p_lag{idx}"] = stats_["p"]
            row[f"ci_low_lag{idx}"] = stats_["ci_low"]
            row[f"ci_high_lag{idx}"] = stats_["ci_high"]
        rows.append(row)
    return pd.DataFrame(rows)


def joint_wald_test(result: PanelEffectsResults, terms: tuple[str, ...]) -> dict[str, float]:
    """Manual Wald test that all selected terms are zero."""
    present = [term for term in terms if term in result.params.index]
    if not present:
        return {"joint_stat": np.nan, "joint_p": np.nan, "joint_df": 0}
    beta = result.params.loc[present].to_numpy()
    cov = result.cov.loc[present, present].to_numpy()
    stat = float(beta.T @ np.linalg.pinv(cov) @ beta)
    df = len(present)
    return {"joint_stat": stat, "joint_p": float(stats.chi2.sf(stat, df)), "joint_df": df}


def _term_stats(result: PanelEffectsResults, term: str) -> dict[str, float]:
    if term not in result.params.index:
        return {"coef": np.nan, "se": np.nan, "p": np.nan, "ci_low": np.nan, "ci_high": np.nan}
    ci = result.conf_int().loc[term]
    return {
        "coef": float(result.params[term]),
        "se": float(result.std_errors[term]),
        "p": float(result.pvalues[term]),
        "ci_low": float(ci["lower"]),
        "ci_high": float(ci["upper"]),
    }


def _interpret_direction(direction: Direction, lag_stats: list[dict[str, float]]) -> str:
    significant = [s for s in lag_stats if s["p"] < 0.05]
    if not significant:
        return "No robust lag coefficient at p < 0.05"
    signs = {np.sign(s["coef"]) for s in significant}
    if direction == "populism_to_corruption":
        if signs == {1.0}:
            return "Lagged populism predicts higher later corruption"
        if signs == {-1.0}:
            return "Lagged populism predicts lower later corruption"
    if direction == "corruption_to_populism":
        if signs == {1.0}:
            return "Lagged corruption predicts higher later populism"
        if signs == {-1.0}:
            return "Lagged corruption predicts lower later populism"
    return "Mixed lag signs among significant coefficients"


def lead_lag_results_table(fits: list[DirectionFit]) -> pd.DataFrame:
    """Report-ready table with lag coefficients for lead-lag models."""
    rows = []
    for fit in fits:
        lag_stats = [_term_stats(fit.result, term) for term in fit.cause_terms]
        row = {
            "model": fit.model_id,
            "direction": fit.direction,
            "outcome": fit.dependent,
            "predictor": fit.proposed_cause,
            "lag_spec": f"1-{fit.lag_order}",
            "n_obs": fit.n_obs,
            "n_countries": fit.n_countries,
            "country_fe": True,
            "year_fe": True,
            "controls": ", ".join(fit.controls) if fit.controls else "none",
            "interpretation": _interpret_direction(fit.direction, lag_stats),
        }
        for idx, stats_ in enumerate(lag_stats, start=1):
            row[f"coef_lag{idx}"] = stats_["coef"]
            row[f"se_lag{idx}"] = stats_["se"]
            row[f"p_lag{idx}"] = stats_["p"]
            row[f"ci_low_lag{idx}"] = stats_["ci_low"]
            row[f"ci_high_lag{idx}"] = stats_["ci_high"]
        rows.append(row)
    return pd.DataFrame(rows)


def granger_results_table(fits: list[DirectionFit]) -> pd.DataFrame:
    """Report-ready table with joint tests on proposed-cause lags."""
    rows = []
    for fit in fits:
        wald = joint_wald_test(fit.result, fit.cause_terms)
        rows.append(
            {
                "direction": fit.direction,
                "dependent_variable": fit.dependent,
                "proposed_cause": fit.proposed_cause,
                "lag_order": fit.lag_order,
                "joint_test_stat": wald["joint_stat"],
                "joint_test_p": wald["joint_p"],
                "joint_df": wald["joint_df"],
                "n_obs": fit.n_obs,
                "n_countries": fit.n_countries,
                "controls": ", ".join(fit.controls) if fit.controls else "none",
                "interpretation": "reject H0" if wald["joint_p"] < 0.05 else "do not reject H0",
            }
        )
    return pd.DataFrame(rows)
