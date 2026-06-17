# EDA Starting Points & Useful Derived Features

Pure domain knowledge: dataset-grounded things worth checking and constructing when exploring V-Dem
and V-Party for any project (not just populism→corruption). Code-free by design.

## Structural EDA (do this before any modelling)
- **Panel shape:** count distinct `country_id`, year range, rows per country. Expect an *unbalanced*
  panel — many units start after 1970 (post-colonial, post-Soviet/Yugoslav). See `country-coding.md`.
- **Coverage heatmap:** country × year grid of non-missingness for the key variables; reveals where
  the usable sample actually is. V-Party expert data effectively begins 1970.
- **Coder counts:** distribution of `_nr` for each C variable; how many cells fall at `_nr ≤ 3`
  (these should be filtered). Coder counts also vary by region/era.
- **Uncertainty width:** distribution of `_codehigh − _codelow`; wide intervals flag low-confidence
  cells and are concentrated in small/early/contested countries.
- **Election spacing (V-Party):** gaps between coded election years per country; informs the
  temporal-expansion choice (see `aggregation.md`).

## Distributional EDA
- Indices (`v2x_*`) are bounded **0–1**; raw C estimates are on a **~z-scale (≈ −5…+5)**. Don't mix
  scales in one plot or model without standardizing.
- The corruption family is **reverse-coded** (high = corrupt) — orient plots consistently.
- Many identity items are ordinal 0–4 (or 0–6 for left-right); the `_ord` version is best for
  bar/cross-tab views, the plain version for continuous summaries.

## Substantive EDA that tends to be informative
- **Time trends:** global mean of `v2x_libdem` / `v2x_polyarchy` shows the post-2010 autocratization
  wave; corruption and populism trends over the same window provide context.
- **Regime stratification:** group by `v2x_regime` (0–3) — relationships often differ sharply across
  closed autocracy → liberal democracy.
- **Regional stratification:** `e_regionpol_6C` for 6 broad regions; useful for fixed effects /
  clustered errors and for spotting region-specific patterns.
- **Cross-index correlation matrix:** the high-level indices are highly collinear (all share
  `v2x_polyarchy`); pick deliberately rather than dumping all five into one model.

## Useful derived features
- **Within-country deltas:** year-over-year change in any index — separates "level" from "change"
  effects; central to early-warning and lead-lag framings.
- **Lags/leads:** lagged predictors (e.g. populism at t−1…t−3) to address simultaneity and to test
  temporal direction.
- **Standardized (z-scored) indices:** put 0–1 indices and ~z-scale estimates on a comparable footing.
- **Governing-party flags (V-Party):** from `v2pagovsup` — incumbent vs opposition; populist-in-power
  indicator.
- **Party-system aggregates (V-Party → country-year):** seat-weighted mean populism, effective number
  of parties (from `v2paseatshare`), share of seats held by parties above a populism threshold,
  max-populism in parliament. See `aggregation.md`.
- **Composite nationalism score:** standardized average of `v2paculsup`, `v2paminor`, `v2paimmig`
  (+ `ep_galtan` where available) — there is no off-the-shelf nationalism index.
- **Uncertainty-aware weights:** down-weight high-`_sd` / wide-HPD observations in regressions, or
  run measurement-error models, instead of treating all estimates as equally precise.
- **Regime-change episodes:** if labels are needed, the ERT dataset (V-Dem Institute) marks
  autocratization/democratization episodes derived from `v2x_polyarchy`/`v2x_libdem`.

## Sanity checks that catch real bugs
- A clean Nordic country should be **low** on `v2x_corr` (confirms you have the reverse-coding right).
- `country_id` for a few known countries (Italy, Germany, France) should match across V-Dem and V-Party.
- Row count after an inner merge ≈ (countries in both) × (overlap years) − missing; eyeball it.
- A known case (e.g. rising populism in Hungary/Poland after 2010) should be visible in the
  governing-party populism series.
- Successor states (e.g. Baltic states) should show the expected birth/gaps, not be silently dropped.