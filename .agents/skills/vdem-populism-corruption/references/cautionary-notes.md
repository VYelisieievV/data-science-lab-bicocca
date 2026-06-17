# Measurement Cautions (for the report's data-quality section)

Pure documentation from the V-Dem v16 *Cautionary Notes* and the V-Party V2 codebook §1.3. These are
the caveats a careful reviewer expects acknowledged.

## Expert-coded latent estimates, not measurements
All C-type scores are expert judgments aggregated by a Bayesian IRT model — estimates with
uncertainty, not facts. The `_codelow`/`_codehigh` (68% HPD) and `_sd` versions exist to carry that
uncertainty; prefer propagating it over discarding it.

## The ≥5-coder assumption and the `_nr` filter
The model assumes ≥5 coders per cell. Fewer coders → estimates can swing on one expert's change
rather than real-world change. V-Dem strongly advises discarding cells with `_nr ≤ 3`. V-Dem has
already pre-removed some low-coder cells (Exclusion §3.14/3.15 & indices §5.6; Civic & Academic Space
§3.16 — all with `_nr < 3`).

## Convergence-flagged variables
Most variables met strict convergence (Gelman-Rubin ≤ 1.01 for ≥95% of parameters). Use HPD bounds
and flag in robustness for the exceptions:
- **V-Party:** `v2paplur` (political pluralism) and `v2papariah` (pariah party) — large expert
  disagreement in several countries.
- **V-Dem v16 (selected, relevant or adjacent):** `v2x_cspart`, `v2peedueq`, `v2pepwrses`,
  `v2xeg_eqaccess`, `v2xeg_eqdr`, `v2caviol`, `v2csgender`, and others — check each codebook entry.

## Percentage variables (no reliability modelling)
`v2mefemjrn` (female journalists), `v2svstterr` (state authority over territory), `v2clsnlpct`
(weaker-civil-liberties population) do not model expert reliability/scale perception — miscoding can
cause large swings. Avoid as key variables.

## Reverse-coded / orientation hazards
- Corruption (`v2x_corr` family) runs low=clean → high=corrupt, opposite to most indices.
- Several V-Party identity indicators are worded so higher = more democratic/tolerant
  (`v2paopresp`, `v2paminor`, `v2paviol`, `v2paculsup`, `v2paimmig`). Combining these with the
  reversed corruption outcome makes sign errors easy — harmonize orientation once and document it.

## Cross-version incomparability
Scores are recomputed each release (simulation + expert turnover), so point estimates shift slightly
between versions. Never compare absolute scores across releases; cite exact versions (V-Dem v16,
V-Party v2).

## Temporal coverage mismatch
- V-Party expert codings: 1970–2019 (factual vote/seat: 1900–2019).
- V-Dem: 1789–2025 (contemporary 1900–2025).
- Merged analytical window: 1970–2019. Post-2019 populist developments are out of scope — a stated
  limitation and a direction for future data.

## Historical/contemporary overlap (only matters if the project goes pre-1970)
For Historical V-Dem A-type variables, contemporary scores are used by default in the ~1900–1920
overlap, which can create artificial jumps at the boundary not reflecting real change. `v3`-prefixed
variables hold the original historical coding where it differs.

## Causal-inference ceiling
Country + year fixed effects remove time-invariant confounders and common shocks, but this is
observational panel data: reverse causality (corruption → populism) and time-varying confounders
remain. The honest strongest claim is directional, with confounding explicitly not ruled out. A
cautious/partial conclusion is acceptable and expected by the course rubric.

## Citations to include
- V-Dem v16 dataset + V-Dem Codebook v16 (Coppedge et al. 2026).
- V-Party V2 dataset + Codebook (Lindberg et al. 2022).
- V-Dem Measurement Model (Pemstein et al., V-Dem Working Paper No. 21).
- Corruption indices methodology: McMann et al. (2016), "Strategies of Validation."
- Country units: V-Dem Country Coding Units; V-Party Party Coding Units (2022).