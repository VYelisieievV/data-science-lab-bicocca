> ## ⚠️ Resolution status (this file is a historical review log)
>
> **All items raised in the audits below have since been addressed in the code and docs.** This file is
> kept only as a record of the review process; it no longer reflects the current state of the repository.
> Specifically resolved after this re-audit was written: Table 2 / Figure 3 now use dependence-adjusted
> SEs (pooled clustered, between robust); README column count (31) and control descriptions; the
> GLOSSARY (`populism_governing`, Hausman, stability sample, persistence, `_osp` scale, BFA); committed
> artifact generation (`scripts/generate_artifacts.py`); the M1–M3 vs M4 sample wording in the notebook,
> spec, doc and glossary; the persistence-as-bar framing; magnitude denominators (overall + within); the
> interaction described as model-implied slopes at polyarchy *levels*; weight-fallback rates reported;
> `sensitivity.py` added to the spec code layout; and association + sensitivity tests committed.
> The current accepted conclusion is summarised in `docs/association_explained.md`.
>
> *(For the canonical, up-to-date narrative see `docs/association_explained.md`, not this log.)*

---

# Task 3 Association Analysis — Re-audit

## Overall verdict

The work is substantially improved. Most of the original statistical blockers were addressed
correctly, and the core country-and-year fixed-effects analysis is now broadly credible.

It is still not submission-ready. One important inference problem remains in the
between-versus-within comparison, and several changed documentation files still contradict the
revised implementation.

This re-audit covered all 31 staged files. At the time of review, there were no unstaged or untracked
files.

## Remaining analytical blocker

### 1. Table 2 uses invalidly narrow pooled-OLS uncertainty

`fit_between_within_comparison` fits pooled OLS and BetweenOLS with their default unadjusted
covariance estimators:

```python
"Pooled OLS (between+within)": PooledOLS.from_formula(rhs, data).fit(),
"Between-country": BetweenOLS.from_formula(rhs, data).fit(),
```

That is not adequate for a country-year panel. Repeated observations from the same country are not
independent, and the between-country regression may be heteroskedastic.

Independent recomputation gives:

| Model | Current 95% CI | Dependence-adjusted 95% CI |
|---|---:|---:|
| Pooled OLS | `[0.107, 0.184]` | Country-clustered: `[-0.024, 0.315]`, p=0.093 |
| Between-country | `[-0.095, 0.546]` | Heteroskedastic-robust: `[-0.065, 0.516]`, p=0.127 |

Consequences:

- The positive pooled point estimate is reproducible.
- The positive between-country point estimate is reproducible.
- Neither is clearly distinguishable from zero once dependence or heteroskedasticity is handled.
- Figure 3's pooled confidence interval is misleadingly narrow.
- Statements such as "clearly positive" and "entirely a between-country fact" are too strong.

The defensible interpretation is:

> The point estimates show a positive-between/negative-within sign reversal, but the cross-country
> association is imprecisely estimated after accounting for panel dependence.

Relevant files:

- `src/association/models.py`
- `docs/tables/table2_between_vs_within.csv`
- `docs/tables/table2_between_vs_within.md`
- `docs/figures/fig3_between_vs_within.png`
- `notebooks/03_association.ipynb`

## Remaining documentation contradictions

### 2. M1–M3 and M4 sample handling is described incorrectly

The code now correctly estimates:

- M1–M3 on 3,940 country-years and 95 countries;
- M4 separately on 3,845 country-years and 95 countries.

However, several files still say all four models use one frozen sample:

- `docs/association_explained.md`
- `notebooks/03_association.ipynb`, Section 0
- `GLOSSARY.md`, definition of `frozen sample`
- `specs/panel-regression-association.md`, model specification and acceptance criteria

The implementation is correct. These descriptions are stale and should state that only M1–M3 share
the stability sample, while M4 uses its own dynamic-model sample.

### 3. Persistence is still called a "bar to beat"

Some notebook prose correctly explains that the persistence model is not comparable to the static
models. Other locations still call it the minimum performance bar:

- `docs/association_explained.md`, Step B
- `notebooks/03_association.ipynb`, Section 2 heading and introductory text
- `GLOSSARY.md`, definition of `persistence baseline`
- `specs/panel-regression-association.md`
- `src/association/models.py::fit_persistence_baseline` docstring

The persistence model documents outcome persistence. It is not a performance threshold for the
static FE models because it uses a lagged outcome, a different specification, and a different
estimand.

### 4. Causal and temporal overstatement remains

`docs/association_explained.md` still states that a country "turning populist doesn't then become more
corrupt" and describes the positive relationship as "entirely" between countries.

Task 3 compares same-year populism and corruption. It cannot establish what happens "then," temporal
ordering, causal effects, or that selection entirely explains the cross-country pattern.

The revised notebook is generally more careful, but any remaining use of "entirely between" should
be replaced with a point-estimate description and an uncertainty caveat.

### 5. `GLOSSARY.md` contains several material inaccuracies

Current problems include:

- `populism_governing` is described as vote-weighted across coalition partners, but the primary
  pipeline includes senior governing parties only. Junior coalition partners appear only in the
  sensitivity analysis.
- The Hausman definition still implies that a large statistic is sufficient to reject RE, without
  mentioning the non-positive-definite covariance failure.
- The frozen-sample definition says all M1–M4 models use the same rows.
- The persistence model is called a minimum bar other models must beat.
- The between-versus-within result is described as positive across countries and approximately null
  within, whereas the revised point estimates are negative within and M2/M3 are narrowly significant.

### 6. README schema and control descriptions are stale

The processed panel has 31 columns, but README still says 29.

README also presents region and population as controls. They are present as descriptive/CV columns,
but neither enters the fixed-effects regressions. Region is time-invariant and absorbed by country FE;
population is simply not included in the reported association models.

### 7. The specification no longer describes the implementation

`specs/panel-regression-association.md` still requires:

- a single common sample for all M1–M4 models;
- persistence as the minimum bar;
- notebook outputs to be cleared.

The code deliberately uses separate M4 and stability samples, while the staged notebook contains 23
output blocks. The specification also omits the newly added `sensitivity.py` workflow and its outputs.

Either the implementation or specification must be authoritative; currently they disagree.

## Sensitivity-analysis caveats

### 8. Weight fallback is common and unreported

The alternative aggregation code falls back to an unweighted mean whenever any weight in a group is
missing or the weight sum is zero.

Raw-data verification found:

- Coalition aggregation falls back in 221 of 977 election groups: **22.6%**.
- Parliamentary aggregation falls back in 53 of 1,025 election groups: **5.2%**.

Therefore, the alternative measures are not always vote- or seat-weighted. These fallback rates
should be reported, especially for the coalition result.

The sensitivity model samples themselves are comparable: all three aggregation models and all three
control-set models use the same 3,940 country-years and 95 countries. Sample shifting is not causing
their coefficient differences.

### 9. Parliamentary populism changes the estimand

The all-party seat-share measure includes opposition parties and captures the parliamentary political
climate. It does not estimate precisely the same relationship as governing-party populism.

It is a useful alternative substantive definition, but its null result should not be described simply
as failure of robustness for the governing-party effect.

### 10. "Likely over-controlling" is too certain

Adding rule of law and regime type attenuates the coefficient. Post-treatment conditioning is one
plausible explanation because populist governments may affect those variables. The analysis does not
demonstrate that this is the reason.

Other explanations include collinearity and estimating a genuinely different conditional
association. The documentation should say "possibly over-controlling" or "consistent with
over-control," not "likely over-controlling."

## Magnitude issue

### 11. The standardized magnitude uses the overall outcome SD

The notebook reports that a one-within-country-SD increase in populism changes corruption by about
3.4% of a corruption SD. The calculation divides by the overall corruption standard deviation.

Independent verification gives:

- one within-country SD of populism: `0.1587`;
- implied M3 outcome change: approximately `-0.0101`;
- overall corruption SD: `0.2956`, giving **-3.4%**;
- within-country corruption SD: `0.1043`, giving **-9.7%**.

The effect remains modest, but the denominator must be named. For a within-country estimator, the
within-country outcome SD is an especially relevant comparison. Saying only "3% of a corruption SD"
is ambiguous and understates the within-standardized magnitude.

## Reproducibility and engineering quality

### 12. Figure and table artifact generation is incomplete

The estimator producing Table 2 now has committed source code. However, no committed plotting helper
or notebook cell generates and saves Figure 3, and no code exports the CSV/Markdown tables.

The statistical estimates are more reproducible than before, but the exact committed artifacts are
not fully regenerable from one documented workflow.

### 13. Notebook-output policy is inconsistent

The specification requires notebook outputs to be cleared, but the staged association notebook has 23
output blocks. Either clear them or change the repository policy to require executed notebooks with
stored outputs.

### 14. Ruff is not clean across all changed Python files

Verification results:

- `tests/test_association.py`: six tests passed.
- `src/association` and `tests/test_association.py`: Ruff passed.
- `git diff --check`: passed.
- Full `ruff check src tests`: failed because `tests/test_preprocessing.py` has an unsorted import
  block.

The full pytest suite could not be executed in the audit sandbox because its filesystem policy blocks
a Polars package path containing `credential_provider`. This is an environment restriction, not
evidence that the preprocessing tests fail.

### 15. Sensitivity behavior is not tested

The new association tests cover the fixed-effects grid, between/within sign pattern, marginal-effect
shape, robustness-table shape, and Hausman reliability flag. They do not test:

- alternative aggregation construction;
- missing-weight fallback behavior;
- control-set construction;
- common-sample guarantees across sensitivity models;
- numerical correctness of the marginal-effect formula.

These omissions do not invalidate the current results, but they leave the new sensitivity layer less
protected than the core model code.

## What was successfully fixed

The following original concerns are now substantially addressed:

- M2 and M3 significance is reported correctly.
- M1–M3 no longer lose observations because of M4's lag.
- The interaction is interpreted through correctly calculated marginal effects.
- Hausman now returns `NaN` rather than a misleading p-value when its covariance condition fails.
- Pooled, between-country, entity-FE, and TWFE estimators now have committed source code.
- Tuned SHAP importances are recomputed under the tuned models.
- Original controls and alternative aggregation definitions are examined.
- Association tests were added and pass.
- The main conclusion generally acknowledges specification-sensitive significance and no causal
  direction.

## Verified core results

Independent recomputation matched the staged tables for the principal FE and interaction results:

| Model | Populism coefficient | 95% CI | p-value |
|---|---:|---:|---:|
| M1 | -0.0677 | `[-0.1394, 0.0040]` | 0.0644 |
| M2 | -0.0715 | `[-0.1408, -0.0023]` | 0.0428 |
| M3 | -0.0638 | `[-0.1234, -0.0042]` | 0.0358 |
| M4 | -0.0033 | `[-0.0163, 0.0097]` | 0.6148 |

Verified interaction marginal effects:

| Polyarchy level | Marginal effect | 95% CI |
|---|---:|---:|
| 10th percentile | -0.1635 | `[-0.2815, -0.0456]` |
| Median | -0.0755 | `[-0.1392, -0.0118]` |
| 90th percentile | 0.0265 | `[-0.0399, 0.0929]` |

These calculations are correct for the specified linear interaction model. They should be described
as model-implied slopes at low, median, and high polyarchy levels—not as separate estimates obtained
only from low-, medium-, and high-democracy countries.

## Defensible conclusion

The strongest conclusion supported by the current evidence is:

> Governing-party populism has a small negative contemporaneous within-country point estimate. It is
> statistically significant in the GDP- and polyarchy-controlled TWFE specifications but not in the
> uncontrolled, first-difference, alternative-aggregation, or original-control specifications. The
> negative sign is consistent across the examined specifications, while significance is fragile.
> Cross-country point estimates are positive but imprecise after accounting appropriately for panel
> dependence. Nothing in Task 3 establishes causal or temporal direction.

## Final assessment

The core FE analysis is now broadly credible. The remaining statistical blocker is the unadjusted
pooled/between inference supporting the "entirely between countries" headline. The remaining
repository blocker is extensive stale documentation that contradicts the corrected code.

The analysis should not be presented as fully correct and adequate until those points are resolved.
