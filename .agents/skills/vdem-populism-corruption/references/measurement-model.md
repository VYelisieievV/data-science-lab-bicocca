# Measurement Model, Variable Types & Suffixes

Pure documentation drawn from the V-Party V2 codebook (§1.5) and V-Dem v16 cautionary notes. This
governs how every expert-coded variable should be read and filtered, in both datasets.

## Variable types (the letter tag in the codebook)
- **A\*** — coded by Research Assistants from extant sources; factual. Experts state confidence.
- **A** — coded by Project Managers / RAs from extant sources; factual.
- **B** — coded by Country Coordinators / RAs; factual. (In V16 most B merged into A.)
- **C** — coded by Country Experts (≥5 target); evaluative. Aggregated by the measurement model.
- **A,C** — expert-coded then cross-checked by an RA (e.g. `v2pagovsup`).
- **D** — indices built from A/B/C variables.
- **E** — imported external variables (no original V-Dem coding beyond possible imputation).

## Variable tag structure
`prefix + (index marker) + section + abbreviated title`. Prefixes:
- `v2` — contemporary V-Dem variables (A/B/C). `v3` — historical-only V-Dem variables.
- `v2x_` — main and component indices. `v2x[two-letter]_` — area-specific indices
  (e.g. `v2xel_` electoral, `v2xpa_` party, `v2xcl_` civil liberties, `v2xeg_` egalitarian,
  `v2xnp_` neopatrimonial).
- `e_` — external (E) variables and ordinal versions of indices (exception: `COWcode`).
- `pa` section = party survey (V-Party).

## The measurement model (why scores look the way they do)
Multiple experts rate each C variable on an ordinal scale (e.g. 0–4). A **Bayesian item-response-
theory (IRT) measurement model** combines them, correcting for differing expert thresholds and
reliability, and outputs a posterior distribution per country-(party-)year. This is why:
- the plain estimate is on a continuous **~z-scale (roughly −5 to +5, mean ≈ 0)**, not 0–4, and can
  be negative;
- every estimate has associated uncertainty (the HPD and SD versions).

## Suffix versions (what to use when)
For a base C variable `X`:
- **`X`** (no suffix) — measurement-model point estimate (median of posterior), ~z-scale.
  *Preferred for regression and most estimation.*
- **`X_osp`** — linearized **original-scale posterior** prediction: mapped back to the 0–k ordinal
  scale as an interval (e.g. 1.25 ≈ between ordinal 1 and 2). Heuristic; correlates ~0.98 with the
  plain version. Good for marginal-effect storytelling on the original scale, but confirm results
  replicate with the plain version.
- **`X_ord`** — most-likely **integer ordinal** category. Use for ordinal models / cross-tabs.
- **`X_codelow` / `X_codehigh`** — bounds of the **68% highest-posterior-density (HPD) interval**
  (≈ ±1 SD; asymmetric if the posterior is skewed). Each scale (plain / `_osp` / `_ord`) has its own
  HPD pair, e.g. `X_osp_codelow`.
- **`X_sd`** — posterior standard deviation (for frequentist-style CIs / measurement-error models).
- **`X_mean`** — arithmetic mean of coder answers (simpler aggregation, for merging conventions).
- **`X_nr`** — **number of coders** for that cell.

D-type indices typically have `_codelow`/`_codehigh`/`_sd` (uncertainty propagated by recomputing
the index over posterior draws) but not `_nr`.

## Coder-count filtering (the `_nr` rule)
The model assumes ≥5 coders. Cells with few coders can swing on a single expert rather than real
change. **V-Dem strongly advises discarding cells with `_nr ≤ 3`.** For an index without its own
`_nr`, filter via its component variables' `_nr`, or flag cells with wide HPD intervals. V-Dem has
already pre-removed some low-coder cells for certain Exclusion / Civic-Academic-Space indicators.

## Cross-version comparability
Scores are recomputed each dataset release (simulation-based estimation + expert turnover), so point
estimates can shift slightly between versions. **Never compare absolute scores across releases**;
cite the exact versions used (here: V-Dem v16, V-Party v2).

## Convergence
Most C variables met strict convergence (Gelman-Rubin ≤ 1.01 for ≥95% of parameters). Exceptions
flagged in the codebook should be used with HPD bounds and noted (see `cautionary-notes.md` for the
specific lists, e.g. V-Party `v2paplur`, `v2papariah`).