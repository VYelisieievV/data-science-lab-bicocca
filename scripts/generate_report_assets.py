"""Build the self-contained figures used by the final LaTeX report."""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data/processed/panel_populism_corruption.parquet"
OUTPUT = ROOT / "report/images"


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )


def distribution_figure(panel: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.7))
    variables = [
        ("populism_governing", "Governing-party populism", "#0072B2"),
        ("v2x_corr", "Composite political corruption", "#D55E00"),
    ]
    for axis, (column, title, color) in zip(axes, variables, strict=True):
        values = panel[column].dropna()
        axis.hist(values, bins=30, color=color, alpha=0.82, edgecolor="white", linewidth=0.4)
        axis.axvline(values.median(), color="#222222", linestyle="--", linewidth=1.3)
        axis.text(
            values.median(),
            axis.get_ylim()[1] * 0.93,
            f" median = {values.median():.2f}",
            ha="left",
            va="top",
            fontsize=9,
        )
        axis.set_title(title)
        axis.set_xlabel("Index value (0-1)")
        axis.set_ylabel("Country-years")
        axis.grid(axis="y", alpha=0.2)
    fig.suptitle("Distributions in the strict modelling panel (1970-2019)", y=1.02, weight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT / "eda_distributions.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def research_design_figure() -> None:
    fig, axis = plt.subplots(figsize=(11.2, 4.0))
    axis.set_xlim(0, 12)
    axis.set_ylim(0, 5)
    axis.axis("off")

    def box(x: float, y: float, width: float, height: float, text: str, color: str) -> None:
        patch = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor=color,
            edgecolor="#333333",
            linewidth=1.0,
        )
        axis.add_patch(patch)
        axis.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=9.5)

    box(
        0.2,
        3.1,
        2.6,
        1.2,
        "V-Party V2\nparty-election data\npopulism + government status",
        "#DCEAF7",
    )
    box(0.2, 0.7, 2.6, 1.2, "V-Dem v16\ncountry-year data\ncorruption + controls", "#FBE5D6")
    box(
        3.5,
        1.9,
        2.7,
        1.2,
        "Validated country-year panel\n3,965 rows | 96 countries\n1970-2019",
        "#E2F0D9",
    )
    box(7.0, 3.35, 2.2, 1.05, "RQ1: Association\nTwo-way fixed effects", "#FFF2CC")
    box(7.0, 1.95, 2.2, 1.05, "RQ2: Direction\nLead-lag + Granger", "#FFF2CC")
    box(7.0, 0.55, 2.2, 1.05, "RQ3: Decomposition\nFour corruption spheres", "#FFF2CC")
    box(
        9.8,
        1.9,
        2.0,
        1.2,
        "Robustness\nplacebos | FD | events\nFDR | alternative samples",
        "#E4DFEC",
    )

    arrow = dict(arrowstyle="->", color="#444444", linewidth=1.4, shrinkA=3, shrinkB=3)
    axis.annotate("", xy=(3.5, 2.55), xytext=(2.8, 3.65), arrowprops=arrow)
    axis.annotate("", xy=(3.5, 2.45), xytext=(2.8, 1.3), arrowprops=arrow)
    for y in (3.88, 2.48, 1.08):
        axis.annotate("", xy=(7.0, y), xytext=(6.2, 2.5), arrowprops=arrow)
    for y in (3.88, 2.48, 1.08):
        axis.annotate("", xy=(9.8, 2.5), xytext=(9.2, y), arrowprops=arrow)
    axis.set_title("Research design and analytical workflow", fontsize=13, weight="bold", pad=8)
    fig.tight_layout()
    fig.savefig(OUTPUT / "research_design.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def copy_existing_figures() -> None:
    sources = {
        ROOT
        / "docs/figures/association/fig1_coefficient_stability.png": "association_stability.png",
        ROOT / "docs/figures/association/fig2_shap_importance.png": "shap_importance.png",
        ROOT / "docs/figures/association/fig3_between_vs_within.png": "between_within.png",
        (
            ROOT / "docs/figures/causal-direction/fig4_causal_direction_coefficients.png"
        ): "causal_direction.png",
        (
            ROOT / "docs/figures/causal-direction/fig7_event_study_populist_entry.png"
        ): "populist_entry_event.png",
        ROOT / "docs/figures/causal-direction/fig10_democracy_split_lags.png": "democracy_lags.png",
        ROOT / "docs/figures/decomposition/fig2_twfe_decomposition.png": "decomposition_twfe.png",
        ROOT / "docs/figures/decomposition/fig5_granger_fdr.png": "decomposition_granger_fdr.png",
    }
    for source, destination in sources.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, OUTPUT / destination)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _style()
    panel = pd.read_parquet(PANEL)
    distribution_figure(panel)
    research_design_figure()
    copy_existing_figures()
    print(f"Generated {len(list(OUTPUT.glob('*.png')))} report images in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
