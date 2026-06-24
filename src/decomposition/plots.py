"""Report-quality visualisations for the corruption decomposition."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTCOME_ORDER = ["Composite", "Executive", "Public sector", "Legislative", "Judicial"]
OUTCOME_COLORS = {
    "Composite": "#4C4C4C",
    "Executive": "#0072B2",
    "Public sector": "#56B4E9",
    "Legislative": "#D55E00",
    "Judicial": "#CC79A7",
}


def _ordered(table: pd.DataFrame) -> pd.DataFrame:
    out = table.copy()
    out["outcome"] = pd.Categorical(out["outcome"], OUTCOME_ORDER, ordered=True)
    return out.sort_values("outcome")


def variation_diagnostics_plot(diagnostics: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Within-country variance share, the identifying signal for fixed effects."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 3.3))
    data = _ordered(diagnostics).iloc[::-1]
    colors = [OUTCOME_COLORS[str(value)] for value in data["outcome"]]
    ax.barh(data["outcome"].astype(str), data["within_variance_share"], color=colors)
    ax.set_xlabel("Share of total variance occurring within countries")
    ax.set_xlim(0, max(0.22, float(data["within_variance_share"].max()) * 1.25))
    ax.set_title("Fixed-effects identifying variation by corruption dimension")
    for index, (_, row) in enumerate(data.iterrows()):
        ax.text(
            float(row["within_variance_share"]) + 0.008,
            index,
            f"{row['within_variance_share']:.1%}",
            va="center",
            fontsize=9,
        )
    return ax


def association_forest_plot(
    association: pd.DataFrame,
    sample_mode: str = "outcome_specific",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """M3 effects in comparable within-SD units."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 3.5))
    data = association[(association["model"] == "M3") & (association["sample_mode"] == sample_mode)]
    data = _ordered(data).iloc[::-1].reset_index(drop=True)
    for position, row in data.iterrows():
        point = float(row["standardized_coefficient"])
        lower = float(row["standardized_ci_low"])
        upper = float(row["standardized_ci_high"])
        label = str(row["outcome"])
        ax.errorbar(
            point,
            position,
            xerr=[[point - lower], [upper - point]],
            fmt="o",
            capsize=4,
            color=OUTCOME_COLORS[label],
        )
    ax.axvline(0, color="grey", lw=1, ls="--")
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(data["outcome"].astype(str))
    ax.set_xlabel("Within-standardised populism coefficient (95% CI)")
    ax.set_title(f"Controlled two-way fixed-effects association — {sample_mode.replace('_', ' ')}")
    return ax


def association_sample_comparison_plot(
    association: pd.DataFrame, ax: plt.Axes | None = None
) -> plt.Axes:
    """Compare M3 estimates under maximum and common complete-case samples."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4.0))
    data = association[association["model"] == "M3"].copy()
    data = _ordered(data)
    positions = np.arange(len(OUTCOME_ORDER))
    offsets = {"outcome_specific": -0.10, "common": 0.10}
    markers = {"outcome_specific": "o", "common": "s"}
    labels = {"outcome_specific": "Maximum sample", "common": "Common sample"}
    for sample_mode in ("outcome_specific", "common"):
        subset = data[data["sample_mode"] == sample_mode].set_index("outcome")
        points = np.array(
            [float(subset.loc[outcome, "standardized_coefficient"]) for outcome in OUTCOME_ORDER]
        )
        lower = np.array(
            [float(subset.loc[outcome, "standardized_ci_low"]) for outcome in OUTCOME_ORDER]
        )
        upper = np.array(
            [float(subset.loc[outcome, "standardized_ci_high"]) for outcome in OUTCOME_ORDER]
        )
        ax.errorbar(
            points,
            positions + offsets[sample_mode],
            xerr=[points - lower, upper - points],
            fmt=markers[sample_mode],
            capsize=3,
            label=labels[sample_mode],
        )
    ax.axvline(0, color="grey", lw=1, ls="--")
    ax.set_yticks(positions)
    ax.set_yticklabels(OUTCOME_ORDER)
    ax.invert_yaxis()
    ax.set_xlabel("Within-standardised populism coefficient (95% CI)")
    ax.set_title("Controlled association: sample-composition robustness")
    ax.legend(frameon=False)
    return ax


def direction_lag_plot(
    terms: pd.DataFrame,
    model: str = "granger",
    sample_mode: str = "outcome_specific",
) -> plt.Figure:
    """Standardised lag coefficients for both temporal directions."""
    data = terms[(terms["model"] == model) & (terms["sample_mode"] == sample_mode)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    titles = {
        "populism_to_corruption": "Populism → later corruption",
        "corruption_to_populism": "Corruption → later populism",
    }
    for axis, direction in zip(axes, titles, strict=True):
        subset = data[data["direction"] == direction]
        subset = _ordered(subset)
        base = np.arange(len(OUTCOME_ORDER))
        for lag, offset, marker in ((1, -0.10, "o"), (2, 0.10, "s")):
            lagged = subset[subset["lag"] == lag].set_index("outcome")
            points = np.array(
                [
                    float(lagged.loc[outcome, "standardized_coefficient"])
                    for outcome in OUTCOME_ORDER
                ]
            )
            lower = np.array(
                [float(lagged.loc[outcome, "standardized_ci_low"]) for outcome in OUTCOME_ORDER]
            )
            upper = np.array(
                [float(lagged.loc[outcome, "standardized_ci_high"]) for outcome in OUTCOME_ORDER]
            )
            axis.errorbar(
                points,
                base + offset,
                xerr=[points - lower, upper - points],
                fmt=marker,
                capsize=2.5,
                label=f"Lag {lag}",
            )
        axis.axvline(0, color="grey", lw=1, ls="--")
        axis.set_title(titles[direction])
        axis.set_xlabel("Within-standardised coefficient (95% CI)")
        axis.set_yticks(base)
        axis.set_yticklabels(OUTCOME_ORDER)
        axis.invert_yaxis()
        axis.legend(frameon=False)
    fig.suptitle(f"{model.replace('_', ' ').title()} estimates — {sample_mode.replace('_', ' ')}")
    fig.tight_layout()
    return fig


def direction_fdr_heatmap(
    models: pd.DataFrame,
    model: str = "granger",
    sample_mode: str = "outcome_specific",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """FDR-adjusted joint-test evidence across dimensions and directions."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7.5, 3.8))
    data = models[
        (models["model"] == model)
        & (models["sample_mode"] == sample_mode)
        & (models["outcome_key"] != "composite")
    ].copy()
    directions = ["populism_to_corruption", "corruption_to_populism"]
    labels = ["Populism → corruption", "Corruption → populism"]
    outcomes = OUTCOME_ORDER[1:]
    matrix = np.full((len(outcomes), len(directions)), np.nan)
    annotations = np.empty(matrix.shape, dtype=object)
    for row_index, outcome in enumerate(outcomes):
        for column_index, direction in enumerate(directions):
            row = data[(data["outcome"] == outcome) & (data["direction"] == direction)].iloc[0]
            q_value = float(row["fdr_q_value"])
            matrix[row_index, column_index] = -np.log10(max(q_value, 1e-12))
            annotations[row_index, column_index] = f"q={q_value:.3f}"
    image = ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(outcomes)))
    ax.set_yticklabels(outcomes)
    ax.set_title("Primary Granger-style joint tests (Benjamini–Hochberg FDR)")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            color = "white" if matrix[row_index, column_index] > 1.3 else "black"
            ax.text(
                column_index,
                row_index,
                annotations[row_index, column_index],
                ha="center",
                va="center",
                color=color,
            )
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("−log10(q)")
    return ax
