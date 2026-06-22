"""Regenerate every committed figure and table for the association analysis (audit re-#12).

One documented workflow that reproduces `docs/figures/*.png` and `docs/tables/*.{md,csv}` from the
committed `src/association` functions, so the artifacts are not hand-built.

    uv run --extra analysis python scripts/generate_artifacts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import polars as pl  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import association as A  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data/processed/panel_populism_corruption.parquet"
FIG = ROOT / "docs/figures"
TBL = ROOT / "docs/tables"


def _to_md(dfr: pd.DataFrame) -> str:
    cols = list(dfr.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in dfr.itertuples(index=False)]
    return "\n".join(lines)


def _save_table(dfr: pd.DataFrame, name: str, caption: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TBL.mkdir(parents=True, exist_ok=True)
    dfr.to_csv(TBL / f"{name}.csv", index=False)
    (TBL / f"{name}.md").write_text(f"**{caption}**\n\n{_to_md(dfr)}\n")


def main() -> int:
    df = pl.read_parquet(PANEL).to_pandas()
    grid = A.fit_twfe_grid(df)
    bw = A.fit_between_within_comparison(df)
    xgb = A.fit_xgboost_cv(df)

    # --- Figure 1: M1–M3 coefficient stability ---
    fig, ax = plt.subplots(figsize=(7, 2.6))
    A.coefficient_stability_plot(grid, ax=ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_coefficient_stability.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Figure 2: SHAP importance ---
    fig, ax = plt.subplots(figsize=(7, 2.4))
    A.shap_importance_plot(xgb, ax=ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_shap_importance.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Figure 3: between vs within (dependence-adjusted SEs) ---
    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    names = list(bw)[::-1]
    for i, n in enumerate(names):
        m = bw[n]
        c = float(m.params["populism_governing"])
        ci = m.conf_int().loc["populism_governing"]
        color = "firebrick" if "FE" in n else "steelblue"
        ax.errorbar(
            c, i, xerr=[[c - ci["lower"]], [ci["upper"] - c]], fmt="o", capsize=5, color=color
        )
    ax.axvline(0, color="grey", ls="--", lw=1)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.set_xlabel("populism -> corruption coefficient (95% CI, dependence-adjusted)")
    ax.set_title("Point estimates: positive between, negative within (all imprecise)")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_between_vs_within.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Tables ---
    def grow(n: str, m) -> dict:
        ci = m.conf_int().loc["populism_governing"]
        controls = {
            "M1": "country+year FE",
            "M2": "+ log GDP",
            "M3": "+ polyarchy",
            "M4": "+ lagged corr",
        }
        return {
            "Model": n,
            "Controls": controls[n],
            "Populism coef": round(m.params["populism_governing"], 4),
            "95% CI": f"[{ci['lower']:.3f}, {ci['upper']:.3f}]",
            "p": round(m.pvalues["populism_governing"], 4),
            "within-R2": round(m.rsquared_within, 3),
        }

    _save_table(
        pd.DataFrame([grow(n, grid.models[n]) for n in ["M1", "M2", "M3", "M4"]]),
        "table1_twfe_grid",
        f"Table 1 - Two-way FE grid (M1-M3: {grid.n_obs} obs/{grid.n_countries} countries; "
        f"M4 own sample: {grid.m4_n_obs}/{grid.m4_n_countries})",
    )

    def erow(n: str, m) -> dict:
        ci = m.conf_int().loc["populism_governing"]
        return {
            "Estimator": n,
            "Populism coef": round(float(m.params["populism_governing"]), 4),
            "95% CI": f"[{ci['lower']:.3f}, {ci['upper']:.3f}]",
            "p": round(float(m.pvalues["populism_governing"]), 3),
        }

    _save_table(
        pd.DataFrame([erow(n, m) for n, m in bw.items()]),
        "table2_between_vs_within",
        "Table 2 - Between vs within (dependence-adjusted SEs: pooled clustered, between robust)",
    )
    _save_table(
        A.benchmark_table(
            A.fit_persistence_baseline(df)["within_r2"], grid.models["M2"].rsquared_within, xgb
        ).round(3),
        "table3_benchmark",
        "Table 3 - Model benchmark (within-R2 vs OOF-R2; not directly comparable)",
    )
    _save_table(
        A.robustness_table(A.fit_twfe_robustness(df)).round(4),
        "table4_robustness",
        "Table 4 - Robustness of M2 within coefficient (SE variants + first-difference)",
    )
    _save_table(
        A.interaction_marginal_effects(df),
        "table5_interaction_marginal",
        "Table 5 - Model-implied marginal effect of populism at low/median/high polyarchy",
    )
    print("Regenerated figures (docs/figures) and tables (docs/tables).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
