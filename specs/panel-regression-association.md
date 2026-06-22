# Panel Regression Association Analysis

## Summary

Implement `notebooks/03_association.ipynb` — the primary statistical analysis establishing
whether within-country rises in governing-party populism correlate with higher political
corruption. Deliverables: a two-way fixed-effects (TWFE) panel regression as the core
inference model, a persistence baseline, an XGBoost comparison with GroupKFold-by-region
cross-validation, and a sub-measure decomposition across the four corruption dimensions.
Also add `linearmodels` and `xgboost` to the `analysis` extras in `pyproject.toml`.

---

## Goals

1. Produce a publishable TWFE coefficient table for `populism_governing → v2x_corr` with
   country + year fixed effects and clustered standard errors.
2. Quantify how much (if any) predictive signal populism adds beyond corruption's own
   persistence (AR baseline).
3. Compare TWFE inference with XGBoost predictive performance evaluated honestly via
   GroupKFold-by-region cross-validation.
4. Decompose the association across the four corruption sub-measures
   (`v2x_execorr`, `v2x_pubcorr`, `v2lgcrrpt`, `v2jucorrdc`) to identify which
   institutional domain is most affected.
5. Provide the foundation for Task 4 (lead-lag / causal direction), which reuses this
   notebook's panel.

---

## Non-Goals

- Causal claims or lead-lag regressions (Task 4, separate notebook).
- Imputing missing values — use complete cases only.
- Model deployment or prediction pipeline beyond the notebook.
- Any data source outside V-Dem / V-Party (constraint from project brief).

---

## Input

- `data/processed/panel_regression_ready.parquet` — output of `02_preprocessing.ipynb`.
  Columns used:
  - `country_id`, `year` (panel index)
  - `populism_governing` (predictor; forward-filled governing-party populism)
  - `v2x_corr`, `v2x_execorr`, `v2x_pubcorr`, `v2lgcrrpt`, `v2jucorrdc` (outcomes)
  - `log_gdppc`, `v2x_polyarchy` (controls)
  - `e_regiongeo` (19-category region; used for GroupKFold stratification)
  - `is_election_year`, `years_since_election` (forward-fill quality flags)

---

## Notebook Structure (`notebooks/03_association.ipynb`)

### Section 0 — Setup & deps check
Load the parquet, verify expected columns and row count. Print panel dimensions
(N countries × T years, total observations).

### Section 1 — Persistence baseline
Fit a country-FE-only AR(1) model: `v2x_corr ~ v2x_corr_lag1 + EntityEffects`.
Record within-R² and coefficient. This is the benchmark every other model must beat to
claim that populism adds explanatory power.

### Section 2 — Two-Way Fixed Effects (TWFE) regression

**2a. Model grid** — four specifications, each adding controls incrementally:
- M1: `v2x_corr ~ populism_governing + EntityEffects + TimeEffects`
- M2: M1 + `log_gdppc`
- M3: M2 + `v2x_polyarchy`
- M4: M3 + `v2x_corr_lag1` (dynamic panel; note Nickell bias caveat)

All models: `cov_type="clustered"`, `cluster_entity=True`.

**2b. Hausman test** — compare TWFE (M2) vs. random-effects equivalent; confirm FE is
the appropriate choice.

**2c. Results table** — coefficient on `populism_governing`, 95% CI, within-R²,
N observations, across M1–M4. Flag sign direction (positive = more corrupt, because
`v2x_corr` runs 0=clean → 1=corrupt).

**2d. Coefficient stability plot** — point estimates + CIs for M1–M4 on one axis;
visually check that the populism coefficient is stable as controls are added.

**2e. Residual diagnostics** — histogram of M2 residuals, residuals vs. fitted scatter.
Note if residuals inherit the bimodal structure of `v2x_corr`.

### Section 3 — Interaction: populism × democracy level
Add `populism_governing:v2x_polyarchy` interaction to M2. Report whether the populism
effect differs significantly across democratic vs. hybrid/autocratic regimes.

### Section 4 — XGBoost predictive comparison

**4a. Within-transformation** — demean all features and outcome by (country, year) means
to replicate the FE identification before feeding to XGBoost. This keeps ML and TWFE on
the same identification footing.

**4b. Cross-validation scheme** — `GroupKFold(n_splits=5, groups=country_id)`, stratified
so each fold preserves region balance. Report mean and std of out-of-fold R².

**4c. Benchmark table** — three rows:
- Persistence baseline (AR-1, Section 1): OOF R²
- TWFE M2 (within-R²)
- XGBoost (OOF R²)

**4d. Feature importance** — SHAP values for top 10 features. Confirm that
`populism_governing` ranks meaningfully (or document if it does not).

### Section 5 — Sub-measure decomposition
Re-run TWFE M2 specification on each of the four sub-measures. Produce a single
coefficient plot showing point estimates and 95% CIs for all four outcomes side-by-side.
Note the sign-flip issue for `v2lgcrrpt` / `v2jucorrdc` (higher = cleaner in the raw
variable; negate the coefficient for the plot or use `_01` rescaled versions).

### Section 6 — Findings & report notes
Markdown summary cell covering:
- Direction and magnitude of the populism coefficient across M1–M4.
- Whether it survives controlling for GDP and polyarchy.
- Comparison to EDA effect sizes (Cliff's delta 0.05–0.11).
- Which sub-measure shows the strongest association (expected: judicial or legislative per EDA).
- Whether XGBoost OOF R² beats the persistence baseline (decision rule from skill guide).
- Caveats: forward-fill assumption, Nickell bias in M4, bimodal residuals.

---

## Dependency changes (`pyproject.toml`)

Add to `[project.optional-dependencies]` under `analysis`:
- `linearmodels>=6.0` — TWFE, Hausman test
- `xgboost>=2.0` — gradient boosted trees
- `shap>=0.46` — SHAP feature importance

---

## Acceptance criteria

- [ ] `uv sync --extra analysis` resolves cleanly with the three new packages.
- [ ] All six sections of the notebook execute top-to-bottom without errors on the
      existing parquet.
- [ ] TWFE M2 result table is present with coefficient, CI, and within-R² for
      `populism_governing`.
- [ ] Hausman test output is present and FE is confirmed as appropriate.
- [ ] XGBoost GroupKFold CV completes with stratified region folds; OOF R² is reported.
- [ ] Benchmark table (baseline / TWFE / XGBoost) is present.
- [ ] Sub-measure decomposition coefficient plot covers all four dimensions.
- [ ] Section 6 findings cell is written (not left blank).
- [ ] Notebook is committed with all outputs cleared (pre-commit nbstripout or manual).

---

## Open questions / risks

- **Nickell bias in M4**: including `v2x_corr_lag1` with entity FE on a short T introduces
  downward bias on the lag coefficient. Document this limitation; consider the Arellano-Bond
  estimator (available in `linearmodels`) as a robustness check if time allows.
- **`v2lgcrrpt` sign**: ensure the rescaled `_01` version is used in the decomposition plot
  so all four dimensions share the same "higher = more corrupt" direction.
- **Region stratification in GroupKFold**: `e_regiongeo` has 19 categories but some are
  sparse (< 5 countries). May need to collapse to 7 macro-regions before stratifying.
- **Bimodal residuals**: if TWFE residuals remain bimodal, note this as a modelling
  limitation and consider whether a two-part / fractional-logit model is worth a
  sensitivity check.
