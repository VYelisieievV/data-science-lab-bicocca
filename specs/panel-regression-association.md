# Panel Regression Association Analysis

## Summary

Implement the association analysis (Task 3) as a `src/` module + a thin notebook
(`notebooks/03_association.ipynb`) that imports from it. All statistical logic lives in
`src/association/`; the notebook is for reproducing results and writing commentary.

The analysis asks: *when a country's governing-party populism rises, does its corruption
rise too?* — a within-country question, answered with a panel fixed-effects regression.
An XGBoost model is run alongside it as a predictive sanity-check, evaluated with
GroupKFold cross-validation grouped by country.

Also add `linearmodels`, `xgboost`, and `shap` to the `analysis` extras in
`pyproject.toml`.

---

## Goals

1. Fit a fixed-effects regression and report the coefficient on `populism_governing` with
   a confidence interval and an R² for the within-country variation.
2. Check whether that coefficient remains stable as economic and democracy controls are
   added (coefficient stability = the result is not an artefact of omitted variables).
3. Confirm that the fixed-effects model is the right choice over a simpler alternative
   (random-effects model) using a statistical test for that choice.
4. Run XGBoost as a predictive comparison, evaluated with GroupKFold CV grouped by
   country. Compare its out-of-fold R² to a naive persistence baseline and to the
   fixed-effects R².
5. Re-run the main regression on each of the four corruption sub-measures to see which
   institutional domain (executive, public-sector, legislative, judicial) shows the
   strongest association.

---

## Non-Goals

- Causal claims or lead-lag regressions (those belong in Task 4, a separate notebook).
- Imputing missing values — drop rows with any null in the variables used.
- Model deployment or serving.
- Any data source outside V-Dem / V-Party.

---

## Code layout

```
src/
  association/
    __init__.py
    models.py      # fitting functions: baseline, TWFE grid, XGBoost CV
    transforms.py  # within-transformation (demeaning) for XGBoost
    plots.py       # coefficient stability plot, benchmark table, decomposition plot
notebooks/
  03_association.ipynb   # imports from src/association; markdown cells explain outputs
```

Each function in `src/association/` takes a plain `pandas.DataFrame` and returns a result
object (fitted model or dict of metrics). No I/O, no global state, no plotting inside
`models.py` or `transforms.py`.

---

## Input

`data/processed/panel_regression_ready.parquet` — produced by `02_preprocessing.ipynb`.

Columns used:

| Column | Role |
|---|---|
| `country_id`, `year` | Panel index |
| `populism_governing` | Predictor (forward-filled governing-party populism score) |
| `v2x_corr` | Primary outcome (0 = clean, 1 = most corrupt) |
| `v2x_execorr`, `v2x_pubcorr`, `v2lgcrrpt_01`, `v2jucorrdc_01` | Sub-measure outcomes (all rescaled to 0–1, higher = more corrupt) |
| `v2x_corr_lag1` | Lagged outcome for persistence baseline |
| `log_gdppc`, `v2x_polyarchy` | Control variables |
| `e_regiongeo` | 19-category region code; used to stratify CV folds |

---

## `src/association/` spec

### `transforms.py`

**`within_demean(df, entity_col, time_col, cols)`**

Subtract each column's country mean and year mean, then add back the grand mean. This is
the same transformation that fixed-effects regression applies internally. Doing it
explicitly lets XGBoost operate on the same "variation" as the econometric model, rather
than learning country-level baseline differences that FE would strip out anyway.

Returns a new DataFrame with the demeaned columns replacing the originals.

---

### `models.py`

**`fit_persistence_baseline(panel_df)`**

Fits a country-fixed-effects-only regression:
`v2x_corr ~ v2x_corr_lag1 + country fixed effects`

*Plain explanation for the report*: "Does knowing last year's corruption level predict
this year's? If yes, any model that ignores this is not a fair benchmark." This is the
minimum bar every other model must beat to claim that populism adds something.

Returns: fitted model object, within-R², coefficient on the lag.

---

**`fit_twfe_grid(panel_df)`**

Fits four models in sequence, each adding one more control:

- **M1** — populism only + country FE + year FE
- **M2** — M1 + log GDP per capita
- **M3** — M2 + polyarchy (democracy score)
- **M4** — M3 + lagged corruption (last year's level)

*What "country + year fixed effects" means*: before estimating, subtract each country's
own average over time (removes "Denmark is always clean") and subtract each year's global
average (removes "2008 was a shock year for everyone"). What remains is within-country,
within-year variation. The regression then asks whether that residual variation in
populism correlates with residual variation in corruption.

All models use standard errors clustered by country. *What "clustered standard errors"
means*: observations from the same country across years are not independent — they share
history and institutions. Clustering corrects for this so confidence intervals are not
artificially narrow.

*Note on M4*: including last year's corruption as a predictor alongside country FE can
slightly distort (bias downward) the lag coefficient when the number of years per country
is short. With ~50 years of data per country this effect is small; flag it in the
notebook commentary but do not attempt to correct it.

Returns: dict of `{model_name: fitted_model}`.

---

**`fit_twfe_interaction(panel_df)`**

Fits M2 plus an interaction term `populism_governing × v2x_polyarchy`. Tests whether the
populism-corruption association is stronger in countries with weaker democracy.

*Plain explanation*: "Does a populist government do more damage to clean governance in a
weak democracy than in a strong one?"

Returns: fitted model object.

---

**`fit_xgboost_cv(panel_df, n_splits=5)`**

Applies `within_demean` first, then runs XGBoost with `GroupKFold(n_splits=5)` grouped
by `country_id`.

*Why GroupKFold, not TimeSeriesSplit*: The research goal is to find a relationship that
holds across countries, not to forecast the future. GroupKFold holds out entire countries
from training and tests whether the model generalises to countries it has never seen —
the honest validity test for a cross-national research claim. Folds are constructed so
each contains countries from all major world regions (stratify by coarsened `e_regiongeo`
collapsed to 7 macro-regions).

Returns: dict with `oof_r2_mean`, `oof_r2_std`, `feature_importances` (SHAP values
averaged across folds).

---

**`fit_submeasure_decomposition(panel_df)`**

Runs the M2 specification (populism + log GDP + country FE + year FE) on each of the
four sub-measures. Returns a dict of `{outcome_name: fitted_model}`.

*Note on sign direction*: `v2lgcrrpt_01` and `v2jucorrdc_01` should already be rescaled
to 0–1 higher-is-more-corrupt in the input parquet (see `02_preprocessing.ipynb` Section
3). Verify before running; if raw latent scores are present instead, rescale here.

---

### `plots.py`

**`coefficient_stability_plot(models_dict)`**

One horizontal axis, four point estimates + 95% CIs for M1–M4, coefficient on
`populism_governing`. If the estimate barely moves as controls are added, the result is
robust to omitted variables.

**`benchmark_table(baseline_r2, twfe_r2, xgb_r2_mean, xgb_r2_std)`**

Three-row summary table: persistence baseline / TWFE M2 / XGBoost. Printed as a
formatted DataFrame. The comparison is between within-country R² for the econometric
models and out-of-fold R² for XGBoost; note in the notebook that these are not identical
metrics and interpret directionally only.

**`decomposition_plot(decomp_dict)`**

Single coefficient plot: four rows (one per sub-measure), each showing the point estimate
and 95% CI for `populism_governing`. Makes it easy to see at a glance whether the effect
is concentrated in one institutional domain.

**`shap_importance_plot(shap_values, feature_names, top_n=10)`**

Horizontal bar chart of mean absolute SHAP values for the top N features. Highlights
whether `populism_governing` ranks among the most important predictors or not.

---

## Notebook structure (`notebooks/03_association.ipynb`)

The notebook only: loads data, calls `src/association` functions, renders results, and
provides markdown commentary. No model-fitting or transformation logic inline.

| Section | Contents |
|---|---|
| 0 — Setup | Load parquet, verify shape, print panel dimensions |
| 1 — Persistence baseline | Call `fit_persistence_baseline`; markdown explains what this tests and what the result means |
| 2 — TWFE grid | Call `fit_twfe_grid`; show coefficient table and stability plot; markdown explains fixed effects, clustered SEs, and how to read the result |
| 3 — FE vs RE choice | Run Hausman-style test (provided by `linearmodels`); markdown explains: "This test checks whether unobserved country characteristics are correlated with the populism score. If yes, fixed effects is the right model. If no, a simpler model (random effects) would also work. The test tells us which assumption holds." |
| 4 — Interaction | Call `fit_twfe_interaction`; markdown interprets interaction coefficient |
| 5 — XGBoost comparison | Call `fit_xgboost_cv`; show benchmark table and SHAP plot; markdown explains GroupKFold choice and what out-of-fold R² means |
| 6 — Sub-measure decomposition | Call `fit_submeasure_decomposition`; show decomposition plot; markdown links back to EDA finding that judicial/legislative had the largest descriptive gap |
| 7 — Findings | Markdown-only cell: direction and magnitude of main result, stability, XGBoost comparison verdict, sub-measure pattern, caveats |

---

## Dependency changes (`pyproject.toml`)

Add to `[project.optional-dependencies]` under `analysis`:
- `linearmodels>=6.0` — fixed-effects panel regression
- `xgboost>=2.0` — gradient boosted trees
- `shap>=0.46` — feature importance (SHAP values)

---

## Acceptance criteria

- [ ] `uv sync --extra analysis` resolves cleanly with the three new packages.
- [ ] `src/association/` is importable (`from src.association.models import fit_twfe_grid`).
- [ ] Notebook runs top-to-bottom without errors against the existing parquet.
- [ ] TWFE results table is present for M1–M4 with coefficient, 95% CI, within-R².
- [ ] Coefficient stability plot is present.
- [ ] FE-vs-RE test output is present with a one-sentence interpretation.
- [ ] XGBoost GroupKFold completes; benchmark table is present.
- [ ] SHAP importance plot is present; `populism_governing` rank is noted.
- [ ] Decomposition plot covers all four sub-measures.
- [ ] Section 7 findings cell is written (not left blank).
- [ ] Notebook committed with outputs cleared.

---

## Open questions / risks

- **Sign direction on sub-measures**: `v2lgcrrpt` / `v2jucorrdc` raw values mean higher =
  cleaner, opposite to `v2x_corr`. Confirm the `_01` rescaled versions are in the parquet
  before the decomposition step; add a rescaling step in `transforms.py` if not.
- **Sparse regions in GroupKFold**: `e_regiongeo` has 19 categories; some have fewer than
  5 countries. Collapse to 7 macro-regions (Western/Eastern Europe, Americas, Sub-Saharan
  Africa, MENA, Asia, Oceania) before stratifying folds.
- **Bimodal residuals**: `v2x_corr` is bimodal (clean-democracy cluster vs. corrupt-state
  cluster). TWFE residuals may inherit this shape. Flag it in Section 7 as a modelling
  limitation; no corrective action required for this task.
- **M4 lag bias**: noted above; document in the notebook, no corrective action required.
