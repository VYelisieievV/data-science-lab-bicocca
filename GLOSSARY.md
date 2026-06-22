# Glossary

Abbreviations, variable codes, and terms used across this project (code, notebooks, spec,
report). Grouped by kind. Variable definitions follow the V-Dem v16 and V-Party V2 codebooks;
see `.claude/skills/vdem-populism-corruption/references/` for fuller treatments.

---

## Datasets & sources

| Term | Meaning |
|---|---|
| **V-Dem** | Varieties of Democracy — here the **Country-Year: Full+Others (v16)** file (annual, country level). Outcomes + controls. |
| **V-Party** | V-Dem's **Country-Party-Date (V2)** file (party level, election-dated). Source of the populism predictor. |
| **ERT** | Episodes of Regime Transformation — another V-Dem product (not used; available if episode labels are ever needed). |
| **panel** | The merged regression-ready country-year table, `data/processed/panel_populism_corruption.parquet`. |

## Outcome variables (V-Dem corruption family — all run **higher = MORE corrupt** unless noted)

| Code | Meaning |
|---|---|
| `v2x_corr` | **Political corruption index** (composite, 0–1). Equal-weighted average of the four spheres below. Primary outcome. |
| `v2x_execorr` | Executive corruption index (0–1). Bribery + embezzlement by the executive. |
| `v2x_pubcorr` | Public-sector corruption index (0–1). Bribery + theft by the bureaucracy. |
| `v2lgcrrpt` | Legislature corrupt activities. **Latent estimate runs higher = CLEANER** (reversed). |
| `v2jucorrdc` | Judicial corruption decision. **Latent estimate runs higher = CLEANER** (reversed). |
| `v2lgcrrpt_01`, `v2jucorrdc_01` | **Our** orientation-harmonised 0–1 versions of the two above, built as `(4 − _ord) / 4` so higher = more corrupt. Coarse (5 levels); for plotting/descriptive use, not regression. |
| `v2ex…` (`v2exbribe`, `v2exembez`, `v2excrptps`, `v2exthftps`) | Component C-variables that build the executive/public indices. |

## Predictor & V-Party variables

| Code | Meaning |
|---|---|
| `v2xpa_popul` | **Populism index** (party level, 0–1, higher = more populist). Built from anti-elitism + people-centrism. |
| `populism_governing` | **Our** primary predictor: `v2xpa_popul` of the **senior governing party only** (`v2pagovsup==0`), forward-filled between elections. Vote-share weighting applies only when a country-year has more than one senior-governing-party record. Junior coalition partners and other parties enter only the *sensitivity* aggregations, not this measure. |
| `v2xpa_antiplural` | Anti-pluralism index (alternative predictor). |
| `v2pagovsup` | Government-support status of a party (`0` = senior governing party / head of government). |
| `v2pavote` | Party vote share (used as aggregation weight). |
| `v2paenname` | Party name (English). |
| `v2paanteli`, `v2papeople` | Anti-elitism, people-centrism — the C-variable components of `v2xpa_popul`. |
| `v2paculsup` | Cultural superiority / nativism (nationalism proxy). |

## Controls & keys

| Code | Meaning |
|---|---|
| `v2x_polyarchy` | Electoral democracy index (0–1, higher = more democratic). Control / moderator. |
| `log_gdppc` | Natural log of `e_gdppc` (GDP per capita) — the income control. |
| `country_id`, `year` | Join keys / panel index (numeric country id; calendar year). |
| `e_regiongeo` | UN-geoscheme region code (19 categories); used to stratify CV folds. |
| `e_pop`, `e_gdppc` | Population, GDP per capita (V-Dem external / Type-E variables). |

## Measurement-model suffixes & type prefixes (V-Dem)

| Token | Meaning |
|---|---|
| `v2x_…` | **D-type** index — a composite (continuous, usually 0–1). The aggregation rule varies: some are built by Bayesian factor analysis, but many are formula-based — e.g. `v2x_corr` is a simple **average** of its four corruption spheres, and V-Party's `v2xpa_popul` is a **harmonic mean** of its components. |
| `v2…` (no `x`) | **C-type** variable — directly expert-coded (point estimate is a latent IRT score). |
| `e_…` | **E-type** — external / "Others" data (GDP, population, region). |
| `_ord` | Ordinal version (the original 0–4 category, e.g. for legislative/judicial corruption). |
| `_osp` | Ordinal-scale posterior prediction — the latent estimate mapped back onto the variable's **original ordinal scale** (commonly 0–4, *not* 0–1), for interpretation. |
| `_codelow` / `_codehigh` | Lower / upper bound of the measurement-uncertainty interval. |
| `_sd` | Posterior standard deviation (measurement uncertainty). |
| `_nr` | Number of coders / ratings for that cell (we filter `_nr ≤ 3`). |
| `_mean` | Mean of the coder ratings (pre-IRT). |
| `_01` | **Project-specific:** orientation-harmonised 0–1 rescale (see corruption table above). |
| `_lag{1,2,3,5}` / `_lead{1,2,3}` | Within-country shift back / forward k years (for Task 4 direction work). |

## Statistical / methodological terms

| Term | Meaning |
|---|---|
| **FE** | Fixed effects — absorb each entity's (or year's) own baseline as a free parameter. |
| **RE** | Random effects — treat baselines as draws uncorrelated with the regressors (a stronger assumption). |
| **TWFE** | Two-way fixed effects (country **and** year FE together). |
| **OLS** | Ordinary least squares. **PooledOLS / BetweenOLS** = pooled / between-country estimators. |
| **within-R²** | Share of *within-country* variation explained (the relevant fit for FE); distinct from between/overall R². |
| **within / between** | The two parts of a variable's variance: movement of a country over time vs differences across countries. |
| **clustered SE** | Standard errors that allow correlation within a cluster (here, a country) across years. |
| **CI / SE** | Confidence interval / standard error. |
| **Hausman test** | Diagnostic comparing FE vs RE coefficients. Here the covariance difference is **not positive-definite**, so the statistic has no dependable chi-square interpretation and is **not** used as a formal rejection; FE is chosen from the research question, not this test. |
| **Nickell bias** | Small downward bias when a lagged outcome sits alongside entity FE; negligible at large T (~50 years here). |
| **IRT** | Item response theory — the latent-trait model V-Dem uses to turn coder ratings into scores. |
| **BFA** | Bayesian factor analysis — used to build *some* V-Dem `v2x_…` composites, but not all: several (including `v2x_corr`) are formula-based aggregates (averages), and V-Party's populism index uses a harmonic mean. |
| **CV** | Cross-validation. **GroupKFold / StratifiedGroupKFold** = CV that holds out whole groups (countries), optionally stratified (by region). **Nested CV** = an inner CV tunes hyperparameters, an outer CV scores — so tuning never sees the test data. |
| **OOF** | Out-of-fold — predictions/scores on held-out CV folds (honest out-of-sample R²). |
| **First-difference** | Removes country effects by subtracting consecutive years (Δy ~ Δx) instead of demeaning — an alternative FE identification used as a robustness check. |
| **Driscoll–Kraay** | A standard-error estimator robust to cross-sectional dependence (e.g. regional/global corruption waves), used as an SE robustness variant. |
| **Robustness ensemble** | Re-running the same model under alternative estimators to show a conclusion is *stable* — as opposed to a leaderboard that picks the best-fitting model (which we avoid). |
| **SHAP** | SHapley Additive exPlanations — per-feature contribution to a model's predictions (importance, **not** significance). |
| **XGBoost** | Gradient-boosted decision trees (`XGBRegressor`), used as the cross-national predictive check. |

## Project-specific terms

| Term | Meaning |
|---|---|
| **M1–M4** | The nested two-way-FE specifications: M1 populism only; M2 +log GDP; M3 +polyarchy; M4 +lagged corruption. M1–M3 are the stability set; M4 is the separate short-run (dynamic) spec. |
| **stability sample** | The rows non-missing on the **M1–M3** variables (populism, log GDP, polyarchy); the three static models share it so coefficient movement reflects controls, not a shifting sample. M4 uses its **own** complete-case sample (it additionally needs the lag). |
| **persistence baseline** | Country-FE regression of corruption on last year's corruption — **documents how sticky corruption is**, not a performance bar the static models must beat (it is a different, dynamic specification/estimand). |
| **between-vs-within divergence** | The Task 3 point-estimate pattern: **positive** across countries (pooled/between) but **negative** within countries (FE). With dependence-adjusted SEs the single-predictor estimates are imprecise; the within-negative is significant only once GDP/democracy are controlled (M2/M3). |
| **Task 3 / 4 / 5** | Association (this work) / direction (lead-lag, Granger — separate teammate) / per-sphere decomposition (separate teammate). |
