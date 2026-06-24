# Task 5 — Corruption-dimension decomposition

## Objective

Determine whether the results obtained for the composite V-Dem political-corruption index
(`v2x_corr`) also hold for executive, public-sector, legislative, and judicial corruption.
The task is confirmatory with respect to the existing Task 3/4 specifications: it compares
pre-declared dimensions and does not search across models for significant results.

## Outcomes and orientation

| Dimension | Primary model column | Orientation in source | Model orientation |
|---|---|---|---|
| Composite benchmark | `v2x_corr` | higher = more corrupt | unchanged |
| Executive | `v2x_execorr` | higher = more corrupt | unchanged |
| Public sector | `v2x_pubcorr` | higher = more corrupt | unchanged |
| Legislative | `v2lgcrrpt` | higher = cleaner | multiplied by -1 |
| Judicial | `v2jucorrdc` | higher = cleaner | multiplied by -1 |

The continuous latent legislative/judicial estimates are the primary regression outcomes.
Their orientation-harmonised `_01` versions have only five levels and are retained for descriptive
plots/robustness, not substituted for the continuous estimates. After orientation, a positive
coefficient always means more corruption.

## Primary specifications

### Contemporaneous association

For every dimension, estimate M1–M3 on one frozen stability sample:

1. M1: populism + country FE + year FE;
2. M2: M1 + log GDP per capita;
3. M3: M2 + electoral democracy (`v2x_polyarchy`).

Country-clustered standard errors are used. M3 on each outcome's available sample is the primary
association estimate. The same models are repeated on a common complete-case sample. Comparisons
across dimensions use within-standardised effects:

`beta * within-SD(populism) / within-SD(outcome)`.

### Temporal direction

Both directions are tested with two annual lags:

- populism -> corruption dimension;
- corruption dimension -> governing populism.

The lead-lag model is descriptive. The primary temporal test is Granger-style: it includes two lags
of the dependent variable as well as two lags of the proposed cause. A joint Wald test evaluates
whether both proposed-cause lags are zero. Models include log GDP, polyarchy, country FE, year FE,
and country-clustered standard errors.

## Multiplicity and robustness

- Benjamini–Hochberg FDR correction is applied to the four M3 subtype tests.
- For the primary Granger family, FDR is applied jointly to the eight tests (four dimensions by two
  directions). The composite is a benchmark and is not counted as a fifth discovery test.
- Outcome-specific estimates are checked against a common sample.
- Pre-declared secondary checks: placebo leads, first differences, democracy interactions, and
  election/forward-fill samples.
- A secondary result cannot overturn the primary Granger conclusion by itself.

## Required outputs

- `src/decomposition/`: isolated, reusable analysis and plotting code;
- `notebooks/05_corruption_decomposition.ipynb`: executable narrative notebook;
- `tests/test_decomposition.py`: orientation, sample, lag, model, and multiplicity tests;
- `docs/tables/decomposition/`: reproducible CSV and Markdown tables;
- `docs/figures/decomposition/`: reproducible report figures;
- `docs/explanation/corruption_decomposition_explained.md`: plain-language record and report text.

## Interpretation rules

- Fixed effects estimate within-country co-movement, not a causal effect.
- Granger-style significance means incremental temporal predictability, not causality.
- Raw coefficients are never ranked across differently scaled outcomes; standardised effects are
  used for dimension comparisons.
- Legislative missingness and low within-country movement are reported explicitly.
- Subdimensions are correlated components of one composite, not independent replications.
- Null results are reported as absence of robust evidence, not proof of no effect.
