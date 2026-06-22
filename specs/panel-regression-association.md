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

1. Quantify how much within-country variation exists in `populism_governing` (a
   between-vs-within variance decomposition). Because the variable is a forward-filled step
   function that changes only at elections (~10–12 times in 50 years), within-country
   variation is thin by design. This sets realistic expectations: if the within share is
   small, the FE estimator has little signal to work with and imprecise estimates are the
   expected, reportable outcome — not a failure.
2. Fit a fixed-effects regression and report the coefficient on `populism_governing` with
   a confidence interval and `rsquared_within` (the R² for within-country variation only).
3. Check whether that coefficient remains stable as economic and democracy controls are
   added for M1–M3 (coefficient stability = the result is not an artefact of omitted
   variables). M4 (lagged outcome) is a separate short-run specification, not a stability
   check.
4. Confirm that the fixed-effects model is the right choice over a simpler alternative
   (random-effects model) using the Hausman diagnostic test.
5. Run XGBoost as a cross-national generalization check, evaluated with GroupKFold CV
   grouped by country. The headline output is the SHAP rank of `populism_governing`; OOF
   R² is context, not a horse-race with the FE model.

> **Out of scope.** The per-sphere decomposition (executive / public-sector / legislative /
> judicial — "Task 5") is a separate teammate deliverable and is **not** part of this work.
> Preprocessing still emits `v2lgcrrpt_01` / `v2jucorrdc_01` for that teammate to use.

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
    models.py        # pure fitting fns: baseline, TWFE grid, interaction, between-within, robustness, XGBoost CV, nested-CV tuning, Hausman, marginal effects
    plots.py         # coefficient stability plot, benchmark table, robustness table, SHAP importance plot
    sensitivity.py   # raw-data robustness (I/O): alternative aggregations (#5), control-set (#4), weight-fallback rates (#8)
scripts/
  generate_artifacts.py  # regenerates every committed docs/figures/*.png and docs/tables/*.{md,csv}
notebooks/
  03_association.ipynb   # imports from src/association; markdown cells explain outputs
tests/
  test_association.py    # core FE/grid/between-within/marginal-effect/Hausman tests
  test_sensitivity.py    # weight-fallback logic + marginal-effect formula
```

Note: `transforms.py` was removed. The `within_demean` helper it contained is not used —
XGBoost receives raw features so GroupKFold hold-outs remain honest (see `fit_xgboost_cv` spec).

Each function in `src/association/` takes a plain `pandas.DataFrame` and returns a result
object (fitted model or dict of metrics). No I/O, no global state, no plotting inside `models.py`.

---

## Input

`data/processed/panel_populism_corruption.parquet` — produced by `src/preprocessing.py` (or equivalently `02_preprocessing.ipynb`).

Columns used:

| Column | Role |
|---|---|
| `country_id`, `year` | Panel index |
| `populism_governing` | Predictor (forward-filled governing-party populism score) |
| `v2x_corr` | Primary (and only) outcome here (0 = clean, 1 = most corrupt) |
| `v2x_corr_lag1` | Lagged outcome for persistence baseline |
| `log_gdppc`, `v2x_polyarchy` | Control variables |
| `e_regiongeo` | 19-category region code; used to stratify CV folds |

---

## `src/association/` spec

~~`transforms.py`~~ — **removed**. The `within_demean` helper originally intended for XGBoost
pre-processing has been dropped; see the `fit_xgboost_cv` spec below for the rationale.

---

### `models.py`

**`fit_persistence_baseline(panel_df)`**

Fits a country-fixed-effects-only regression:
`v2x_corr ~ v2x_corr_lag1 + country fixed effects`

*Plain explanation for the report*: "Does knowing last year's corruption level predict
this year's?" This **documents how sticky corruption is** — it is *not* a performance bar the
static M1–M3 models must beat (it is a dynamic model with a lagged outcome, a different
specification and a different estimand, so its within-R² is not comparable to theirs).

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

*Estimation samples (audit #10)*: the **static models M1–M3 share one stability sample** — rows
non-missing on the M1–M3 variables (`v2x_corr`, `populism_governing`, `log_gdppc`, `v2x_polyarchy`),
so coefficient movement across M1→M3 reflects added controls, not a shifting sample (~3,940 obs, 95
countries). **M4 is fit separately on its own complete-case sample** (it additionally needs
`v2x_corr_lag1`, a different/dynamic estimand) so M1–M3 do not lose each country's first year for a lag
they don't use (~3,845 obs). Report both sample sizes.

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

**`fit_twfe_robustness(panel_df)`**

Re-estimates the M2 association under three standard-error estimators (cluster-by-country,
two-way cluster, Driscoll–Kraay) and a `FirstDifferenceOLS` estimator. A *robustness
ensemble*, not a model-selection leaderboard: shows the within-country conclusion is stable
across SE choices (same point estimate, different intervals) and across identification routes
(demeaning vs differencing). `plots.robustness_table` formats it. *Why this and not "pick the
best model": for an inferential question, best-fit selects the confounded pooled answer.*

Returns: dict of `{estimator_label: fitted_model}`.

---

**`fit_xgboost_cv(panel_df, n_splits=5)`**

Runs XGBoost with **raw (undemeaned) features** and `GroupKFold(n_splits=5)` grouped by
`country_id`.

*Why GroupKFold, not TimeSeriesSplit*: The research goal is to find a relationship that
holds across countries, not to forecast the future. GroupKFold holds out entire countries
from training and tests whether the model generalises to countries it has never seen —
the honest validity test for a cross-national research claim. Folds are constructed so
each contains countries from all major world regions (stratify by coarsened `e_regiongeo`
collapsed to 7 macro-regions).

*Why not demean before CV*: Within-demeaning each country by its own mean and then holding
that country out is self-contradictory — the held-out country's features were computed
using its own mean (leakage), and the cross-country signal the hold-out is meant to test
has been removed. Using raw features keeps the test honest. The consequence: XGBoost can
exploit *between*-country variation ("richer countries tend to be cleaner") that fixed
effects deliberately strips. Its R² will therefore exceed the FE within-R² by design,
**not** because it is a better model of the research question.

*Headline output*: the **SHAP rank of `populism_governing`** — if populism ranks low even
in this generous cross-country model, that reinforces a weak within-country association.
The OOF R² is reported alongside it as context, not as a horse-race winner.

Also fits and evaluates a plain **linear model under the identical GroupKFold** so the
benchmark table has one apples-to-apples OOF comparison.

Returns: dict with `oof_r2_mean`, `oof_r2_std`, `linear_oof_r2`, `feature_importances`
(SHAP values averaged across folds).

---

**`tune_xgboost_nested_cv(panel_df, n_splits=5)`**

Nested cross-validation hyperparameter search for the predictive check: an inner `GroupKFold`
tunes (`max_depth`, `learning_rate`, `n_estimators`) on each outer training fold, the outer
`StratifiedGroupKFold` scores on held-out countries — tuning never sees the test countries (no
leakage). Answers "would tuning change the verdict?": it nudges OOF R² up modestly, prefers the
most-regularised model, and does not revive a within-country populism effect.

Returns: dict with `tuned_oof_r2_mean`, `tuned_oof_r2_std`, `best_params_per_fold`.

---

### `plots.py`

**`coefficient_stability_plot(models_dict)`**

One horizontal axis, **three** point estimates + 95% CIs for **M1–M3** only, coefficient
on `populism_governing`. If the estimate barely moves as controls are added, the result is
robust to omitted variables.

M4 is intentionally excluded from this plot. M4 adds the lagged outcome (`v2x_corr_lag1`),
which changes the question: the populism coefficient now measures only the short-run movement
*not* already captured by yesterday's corruption level. Because corruption is highly persistent
(year-to-year autocorrelation ~0.95), this lag absorbs most of the level, so the M4 coefficient
will mechanically shrink. A smaller M4 coefficient is a change of estimand, not evidence of
fragility. Present M4 separately in a dedicated notebook row, labelled "short-run / dynamic
specification."

**`benchmark_table(baseline_r2, twfe_r2, linear_oof_r2, xgb_r2_mean, xgb_r2_std)`**

Four-row summary table: persistence baseline (within-R²) / TWFE M2 (within-R²) /
Linear GroupKFold OOF R² / XGBoost GroupKFold OOF R². Printed as a formatted DataFrame.

The two metric types are not directly comparable (within-R² measures in-sample fit on
demeaned data; OOF R² measures out-of-sample cross-national generalization). Label both
metric types explicitly in the table. The apples-to-apples comparison is Linear OOF vs
XGBoost OOF; the TWFE within-R² is context for the econometric model.

Always label the FE figure as `rsquared_within` in code; `linearmodels` also exposes
between and overall R² which measure different quantities and must not be confused with it.

**`shap_importance_plot(shap_values, feature_names, top_n=10)`**

Horizontal bar chart of mean absolute SHAP values for the top N features. Highlights
whether `populism_governing` ranks among the most important predictors or not.

---

## Notebook structure (`notebooks/03_association.ipynb`)

The notebook only: loads data, calls `src/association` functions, renders results, and
provides markdown commentary. No model-fitting, transformation, or I/O logic inline.

> **Documentation principle**: every uncommon method or test in this notebook (fixed effects,
> clustered SEs, within-R², Hausman, GroupKFold, SHAP, the variance decomposition, first-difference,
> Driscoll–Kraay SEs, nested-CV tuning) must have a
> 2–3 sentence plain-language callout — *what it is / why we use it / what it can and can't tell us*
> — pitched at a data-science student who is not strong in statistics. Do not assume the reader knows
> what "fixed effects" or "clustered standard errors" means; explain it in the markdown cell that
> precedes the output.

| Section | Contents |
|---|---|
| 0 — Setup | Load parquet, verify shape, print panel dimensions; report the **M1–M3 stability sample** (rows non-missing on M1–M3 variables) and **M4's separate sample** (adds the lag) with their N and country counts |
| 1 — Within-variance decomposition | Decompose `populism_governing` into between-country and within-country variance shares. Markdown explains: *"FE uses only within-country variation — how much a country's populism deviates from its own average over time. If most of the variance in populism is between countries ('Sweden is always low, Hungary is always high') and little is within countries ('Hungary rose sharply in 2010–2015'), the FE estimator has little signal to learn from. This table shows how much within-variation we actually have — it sets expectations for the precision of the coefficient."* |
| 2 — Persistence baseline | Call `fit_persistence_baseline`; markdown explains what this tests and what the result means |
| 3 — TWFE grid (M1–M3) | Call `fit_twfe_grid`; show coefficient table and M1–M3 stability plot; markdown explains fixed effects, clustered SEs, and how to read the result. Markdown also explains: *"We cluster standard errors by country because observations from the same country across years are not independent — they share history and institutions. Without clustering, our confidence intervals would be artificially narrow. We report the number of clusters (countries); fewer than ~40 makes cluster-robust inference less reliable."* |
| 4 — M4 short-run specification | Show M4 result separately; markdown explains: *"M4 adds last year's corruption level as a predictor. This changes the question: the populism coefficient now measures only the short-run year-to-year movement in corruption not already explained by last year's value. Because corruption is very sticky (it barely changes year to year), last year's value explains most of this year's, and the populism coefficient shrinks. This is expected — M4 is not a stability check, it is a different, more conservative specification."* |
| 5 — FE vs RE diagnostic | Run Hausman test; show result; markdown provides the full plain-language explanation (see B6 in the `fit_twfe_grid` spec above) |
| 6 — Interaction | Call `fit_twfe_interaction`; markdown interprets interaction coefficient: does the association strengthen in weaker democracies? |
| 7 — XGBoost comparison | Call `fit_xgboost_cv`; show benchmark table (four rows, two labeled metric types) and SHAP plot; markdown explains GroupKFold choice, why demeaning was not applied, what SHAP rank means, and what out-of-fold R² means. State explicitly that SHAP rank describes the fitted XGBoost only and is not statistical significance. |
| 8 — Robustness | Call `fit_twfe_robustness` + `robustness_table` (SE variants + first-difference) and `tune_xgboost_nested_cv`; markdown frames this as a *robustness ensemble, not a best-model leaderboard* (best-fit would select the confounded pooled answer), and notes the conclusion is stable across estimators and tuning. |
| 9 — Findings | Markdown-only cell: a scope note (per-sphere decomposition = Task 5, direction = Task 4, both out of scope), then direction and magnitude of main result, stability across M1–M3, robustness, M4 short-run comparison, XGBoost SHAP rank verdict, caveats (slow-moving predictor, observational data, no causal claim) |

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
- [ ] `src/preprocessing.py` emits `v2lgcrrpt_01` and `v2jucorrdc_01` in the parquet; `validate_panel` orientation assertion passes.
- [ ] Notebook runs top-to-bottom without errors against the existing parquet.
- [ ] Section 0: M1–M3 stability sample and M4's own sample both built; surviving N + country counts reported.
- [ ] Section 1: between-vs-within variance table for `populism_governing` present.
- [ ] Sections 3–4: TWFE M1–M3 stability plot (not M4); M4 shown separately with its own markdown explanation.
- [ ] M1–M3 share the stability sample; M4 uses its own complete-case sample (not one frozen sample for all four).
- [ ] Between-within comparison uses dependence-adjusted SEs (pooled clustered, between robust).
- [ ] Section 5: Hausman test output present; markdown uses the full plain-language explanation from B6.
- [ ] Section 7: XGBoost GroupKFold on raw features completes; benchmark table has four rows with labeled metric types; SHAP importance plot present; `populism_governing` rank explicitly noted.
- [ ] Section 8 findings cell is written (not left blank), with the Task 4/5 scope note.
- [ ] Every uncommon method in the notebook has a 2–3 sentence plain-language callout.
- [ ] Notebook committed **executed, with outputs stored** (policy updated, audit re-#13: the results
      tables/plots are part of the deliverable and reviewers should see them without re-running; the slow
      nested-CV cell makes re-execution costly). Re-runnable from the project `uv` kernel.
- [ ] Committed artifact generator `scripts/generate_artifacts.py` reproduces all figures + tables.
- [ ] `src/association/sensitivity.py` provides the aggregation (#5) and control-set (#4) robustness,
      reproducibly from the raw DuckDB tables.

---

## Open questions / risks

- **Sub-measure `_01` columns (for the Task 5 teammate)**: `src/preprocessing.py` produces
  `v2lgcrrpt_01` / `v2jucorrdc_01` with the orientation reversal baked in and a
  positive-correlation assertion in `validate_panel`. These are **not used in this Task 3
  notebook** (the per-sphere decomposition is Task 5) — they are emitted so the teammate
  owning that branch has orientation-harmonised outcomes ready.
- **Sparse regions in GroupKFold**: `e_regiongeo` has 19 categories; some have fewer than
  5 countries. Collapse to 7 macro-regions (Western/Eastern Europe, Americas, Sub-Saharan
  Africa, MENA, Asia, Oceania) before stratifying folds.
- **Bimodal residuals**: `v2x_corr` is bimodal (clean-democracy cluster vs. corrupt-state
  cluster). TWFE residuals may inherit this shape. Flag it in Section 8 as a modelling
  limitation; no corrective action required for this task.
- **M4 lag bias**: see Section 4; document in the notebook, no corrective action required.
- **Cross-sectional dependence**: clustered SEs handle within-country serial correlation but
  not regional/global corruption waves (e.g. EU accession years, post-2008). Report the
  cluster count; if thin after the governing-party filter, note Driscoll–Kraay as a
  robustness option in Section 8.
- **TWFE negative-weights**: these critiques target staggered *binary* treatments. With a
  continuous populism score they do not apply; one sentence in Section 8 suffices to preempt
  the question.
