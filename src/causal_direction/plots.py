"""Plot helpers for causal-direction outputs."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def coefficient_direction_plot(table: pd.DataFrame, output_path: str | None = None) -> plt.Figure:
    """Plot lag-1 and lag-2 coefficients for both causal-direction models."""
    rows = []
    for _, row in table.iterrows():
        for lag in (1, 2):
            coef_col = f"coef_lag{lag}"
            if coef_col not in row or pd.isna(row[coef_col]):
                continue
            rows.append(
                {
                    "direction": row["direction"],
                    "lag": lag,
                    "coef": row[coef_col],
                    "ci_low": row.get(f"ci_low_lag{lag}"),
                    "ci_high": row.get(f"ci_high_lag{lag}"),
                }
            )
    plot_df = pd.DataFrame(rows)
    directions = ["populism_to_corruption", "corruption_to_populism"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=False)
    for ax, direction in zip(axes, directions):
        sub = plot_df[plot_df["direction"] == direction]
        y = sub["lag"].to_numpy()
        x = sub["coef"].to_numpy()
        xerr = [x - sub["ci_low"].to_numpy(), sub["ci_high"].to_numpy() - x]
        ax.errorbar(x, y, xerr=xerr, fmt="o", capsize=4, color="firebrick")
        ax.axvline(0, color="grey", linestyle="--", linewidth=1)
        ax.set_yticks([1, 2])
        ax.set_ylabel("lag")
        if direction == "populism_to_corruption":
            ax.set_title("Past populism -> current corruption")
            ax.set_xlabel("coefficient on populism lag")
        else:
            ax.set_title("Past corruption -> current populism")
            ax.set_xlabel("coefficient on corruption lag")
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return fig


def placebo_lead_plot(
    table: pd.DataFrame,
    output_path: str | None = None,
    title: str = "Placebo lead test: past vs future proposed cause",
) -> plt.Figure:
    """Plot past-populism lags and future-populism placebo leads."""
    plot_df = table.copy()
    plot_df["signed_time"] = plot_df.apply(
        lambda row: -int(row["order"]) if row["term_type"] == "lag" else int(row["order"]),
        axis=1,
    )
    plot_df = plot_df.sort_values("signed_time")
    colors = plot_df["term_type"].map({"lag": "firebrick", "lead_placebo": "steelblue"})
    fig, ax = plt.subplots(figsize=(7, 4))
    x = plot_df["signed_time"].to_numpy()
    y = plot_df["coef"].to_numpy()
    yerr = [y - plot_df["ci_low"].to_numpy(), plot_df["ci_high"].to_numpy() - y]
    ax.errorbar(x, y, yerr=yerr, fmt="o", capsize=4, color="black", ecolor="black")
    ax.scatter(x, y, c=colors)
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linewidth=1)
    ax.set_xticks(x)
    ax.set_xlabel("time relative to current corruption outcome")
    ax.set_ylabel("coefficient on proposed cause")
    ax.set_title(title)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return fig


def event_study_plot(
    table: pd.DataFrame,
    output_path: str | None = None,
    title: str = "Event study",
    ylabel: str = "outcome difference vs year -1",
) -> plt.Figure:
    """Plot event-time coefficients around populist-government entry."""
    plot_df = table.sort_values("event_time")
    fig, ax = plt.subplots(figsize=(8, 4))
    x = plot_df["event_time"].to_numpy()
    y = plot_df["coef"].to_numpy()
    yerr = [y - plot_df["ci_low"].to_numpy(), plot_df["ci_high"].to_numpy() - y]
    ax.errorbar(x, y, yerr=yerr, fmt="o-", capsize=4, color="firebrick")
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linewidth=1)
    ax.set_xticks(x)
    ax.set_xlabel("years from populist-government entry")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return fig


def lag_information_plot(table: pd.DataFrame, output_path: str | None = None) -> plt.Figure:
    """Plot AIC/BIC by lag order for the Granger-style specification."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
    for ax, criterion in zip(axes, ["aic", "bic"]):
        for direction, sub in table.groupby("direction"):
            ax.plot(sub["lag_order"], sub[criterion], marker="o", label=direction)
        ax.set_title(criterion.upper())
        ax.set_xlabel("lag order")
        ax.set_ylabel(criterion.upper())
        ax.legend(fontsize=8)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return fig


def democracy_split_plot(table: pd.DataFrame, output_path: str | None = None) -> plt.Figure:
    """Plot lagged populism coefficients in low/high democracy country groups."""
    rows = []
    for _, row in table.iterrows():
        for lag in (1, 2):
            coef_col = f"coef_lag{lag}"
            if coef_col not in row or pd.isna(row[coef_col]):
                continue
            rows.append(
                {
                    "group": row["democracy_group"],
                    "lag": lag,
                    "coef": row[coef_col],
                    "ci_low": row[f"ci_low_lag{lag}"],
                    "ci_high": row[f"ci_high_lag{lag}"],
                }
            )
    plot_df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7, 4))
    y_positions = range(len(plot_df))
    x = plot_df["coef"].to_numpy()
    xerr = [x - plot_df["ci_low"].to_numpy(), plot_df["ci_high"].to_numpy() - x]
    labels = [f"{row.group}, lag {row.lag}" for row in plot_df.itertuples()]
    ax.errorbar(x, list(y_positions), xerr=xerr, fmt="o", capsize=4, color="firebrick")
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels)
    ax.set_xlabel("coefficient on lagged governing populism")
    ax.set_title("Populism -> corruption by democracy group")
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return fig
