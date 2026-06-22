"""Association analysis (Task 3): does within-country populism track corruption?

Pure modelling + plotting helpers for `notebooks/03_association.ipynb`. The statistical
logic lives here; the notebook only loads data, calls these functions, and writes
commentary. See `specs/panel-regression-association.md` for the full design and rationale.
"""

from association.models import (
    TWFE_GRID_VARS,
    TWFE_M4_VARS,
    TWFE_STABILITY_VARS,
    TWFEGridResult,
    XGBoostCVResult,
    fit_between_within_comparison,
    fit_persistence_baseline,
    fit_twfe_grid,
    fit_twfe_interaction,
    fit_twfe_robustness,
    fit_xgboost_cv,
    hausman_fe_re,
    interaction_marginal_effects,
    tune_xgboost_nested_cv,
    within_between_variance,
)
from association.plots import (
    benchmark_table,
    coefficient_stability_plot,
    robustness_table,
    shap_importance_plot,
)

__all__ = [
    "TWFE_GRID_VARS",
    "TWFE_M4_VARS",
    "TWFE_STABILITY_VARS",
    "TWFEGridResult",
    "XGBoostCVResult",
    "benchmark_table",
    "coefficient_stability_plot",
    "fit_between_within_comparison",
    "fit_persistence_baseline",
    "fit_twfe_grid",
    "fit_twfe_interaction",
    "fit_twfe_robustness",
    "fit_xgboost_cv",
    "hausman_fe_re",
    "interaction_marginal_effects",
    "robustness_table",
    "shap_importance_plot",
    "tune_xgboost_nested_cv",
    "within_between_variance",
]
