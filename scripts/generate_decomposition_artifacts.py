"""Regenerate every committed Task 5 table and figure from the processed panel.

Run from the repository root:

    uv run --extra analysis python scripts/generate_decomposition_artifacts.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import decomposition as D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data/processed/panel_populism_corruption.parquet"
FIGURE_DIR = ROOT / "docs/figures/decomposition"
TABLE_DIR = ROOT / "docs/tables/decomposition"


def _display_value(value: object) -> str:
    if pd.isna(value):
        return "—"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.4f}"
    return str(value).replace("|", "\\|")


def _to_markdown(table: pd.DataFrame) -> str:
    columns = list(table.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for row in table.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_display_value(value) for value in row) + " |")
    return "\n".join(lines)


def _save_table(table: pd.DataFrame, name: str, caption: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE_DIR / f"{name}.csv", index=False)
    (TABLE_DIR / f"{name}.md").write_text(
        f"**{caption}**\n\n{_to_markdown(table)}\n", encoding="utf-8"
    )


def _cross_dimension_summary(results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    association = results["association"]
    association = association[
        (association["model"] == "M3") & (association["sample_mode"] == "outcome_specific")
    ].set_index("outcome_key")
    granger = results["direction_models"]
    granger = granger[
        (granger["model"] == "granger") & (granger["sample_mode"] == "outcome_specific")
    ]
    rows = []
    for outcome in D.OUTCOMES:
        association_row = association.loc[outcome.key]
        forward = granger[
            (granger["outcome_key"] == outcome.key)
            & (granger["direction"] == "populism_to_corruption")
        ].iloc[0]
        reverse = granger[
            (granger["outcome_key"] == outcome.key)
            & (granger["direction"] == "corruption_to_populism")
        ].iloc[0]
        rows.append(
            {
                "outcome_key": outcome.key,
                "outcome": outcome.label,
                "association_std_beta": association_row["standardized_coefficient"],
                "association_ci_low": association_row["standardized_ci_low"],
                "association_ci_high": association_row["standardized_ci_high"],
                "association_p": association_row["p_value"],
                "association_fdr_q": association_row["fdr_q_value"],
                "pop_to_corr_granger_p": forward["joint_p_value"],
                "pop_to_corr_fdr_q": forward["fdr_q_value"],
                "corr_to_pop_granger_p": reverse["joint_p_value"],
                "corr_to_pop_fdr_q": reverse["fdr_q_value"],
                "association_n": int(association_row["n_obs"]),
                "direction_n_forward": int(forward["n_obs"]),
                "direction_n_reverse": int(reverse["n_obs"]),
            }
        )
    return pd.DataFrame(rows)


def _save_tables(results: dict[str, pd.DataFrame]) -> None:
    diagnostics_columns = [
        "outcome",
        "primary_source",
        "n_obs",
        "n_missing",
        "n_countries",
        "n_unique_values",
        "within_sd",
        "within_variance_share",
        "lag1_autocorrelation",
        "lag2_autocorrelation",
        "countries_no_within_variation",
        "median_unique_values_per_country",
    ]
    _save_table(
        results["diagnostics"][diagnostics_columns],
        "table1_outcome_diagnostics",
        "Table 1 — Coverage, identifying variation, persistence, and resolution",
    )

    association = results["association"]
    association_m3 = association[association["model"] == "M3"]
    association_columns = [
        "outcome",
        "sample_mode",
        "coefficient",
        "ci_low",
        "ci_high",
        "p_value",
        "fdr_q_value",
        "standardized_coefficient",
        "standardized_ci_low",
        "standardized_ci_high",
        "n_obs",
        "n_countries",
    ]
    _save_table(
        association_m3[association_columns],
        "table2_twfe_m3",
        "Table 2 — Controlled two-way fixed-effects decomposition (M3)",
    )
    _save_table(
        association,
        "table3_twfe_stability",
        "Table 3 — M1–M3 coefficient stability on frozen samples",
    )

    direction_models = results["direction_models"]
    _save_table(
        direction_models,
        "table4_direction_joint_tests",
        "Table 4 — Lead-lag and Granger-style joint Wald tests",
    )
    _save_table(
        results["direction_terms"],
        "table5_direction_lag_coefficients",
        "Table 5 — Individual temporal coefficients with within-standardised effects",
    )
    _save_table(
        results["placebo"],
        "table6_placebo_leads",
        "Table 6 — Joint placebo-lead tests",
    )
    _save_table(
        results["first_differences"],
        "table7_first_differences",
        "Table 7 — First-difference directional robustness",
    )
    _save_table(
        results["democracy_interactions"],
        "table8_democracy_interactions",
        "Table 8 — Model-implied contemporaneous slopes by democracy level",
    )
    _save_table(
        results["electoral_robustness"],
        "table9_electoral_robustness",
        "Table 9 — Populism-to-corruption estimates under electoral/forward-fill samples",
    )
    _save_table(
        results["association_robustness"],
        "table10_association_robustness",
        "Table 10 — Association covariance and first-difference robustness",
    )
    _save_table(
        results["measurement_robustness"],
        "table11_measurement_robustness",
        "Table 11 — Continuous versus coarse ordinal measurement robustness",
    )
    _save_table(
        _cross_dimension_summary(results),
        "table12_cross_dimension_summary",
        "Table 12 — Primary cross-dimension synthesis",
    )


def _save_figures(results: dict[str, pd.DataFrame]) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(8, 3.3))
    D.variation_diagnostics_plot(results["diagnostics"], axis)
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "fig1_within_variation.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 3.5))
    D.association_forest_plot(results["association"], "outcome_specific", axis)
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "fig2_twfe_decomposition.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 4.0))
    D.association_sample_comparison_plot(results["association"], axis)
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "fig3_common_sample_robustness.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure = D.direction_lag_plot(results["direction_terms"], "granger", "outcome_specific")
    figure.savefig(FIGURE_DIR / "fig4_granger_lags.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7.5, 3.8))
    D.direction_fdr_heatmap(results["direction_models"], "granger", "outcome_specific", axis)
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "fig5_granger_fdr.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    if not PANEL.is_file():
        raise FileNotFoundError(f"Processed panel not found: {PANEL}")
    started = time.perf_counter()
    panel = pd.read_parquet(PANEL)
    results = D.run_complete_analysis(panel)
    _save_tables(results)
    _save_figures(results)
    elapsed = time.perf_counter() - started
    print(f"Generated Task 5 artifacts in {elapsed:.1f}s")
    print(_cross_dimension_summary(results).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
