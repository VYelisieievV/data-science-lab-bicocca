---
name: vdem-populism-corruption
description: >
  Domain reference and working guide for a Data Science Lab project on whether populist / nationalist
  party power is associated with political corruption, using only V-Dem and V-Party (both V-Dem
  Institute products, the allowed sources). Use this skill whenever working on the project: loading or
  merging V-Dem Country-Year and V-Party Country-Party-Date data, doing EDA, selecting populism /
  anti-pluralism / nationalism / corruption / democracy variables, aggregating party-level data to
  country-year, handling the measurement-model suffixes (_codelow/_codehigh/_sd/_osp/_ord/_nr/_mean),
  filtering low-coder cells, reasoning about how successor states (USSR, Yugoslavia, ex-colonies) are
  coded, or writing the regression / lead-lag / decomposition analysis. Consult the reference files
  before naming variables (easy to misremember) or writing any merge/aggregation code, and whenever
  considering a pivot to an adjacent question inside these two datasets.
---

# V-Dem × V-Party: Populism and Corruption — Working Guide

The `references/` files are **pure dataset documentation and domain knowledge** (no project-specific
code or opinions) so they stay reusable if the project pivots. This SKILL.md holds the
project-specific framing, the analysis plan, and code skeletons.

## What this project is

**Research question.** Do countries governed by populist (and/or nationalist / anti-pluralist)
parties exhibit higher political corruption — which dimension of corruption (executive, legislative,
judicial, public-sector) is most affected, and in which temporal direction does the relationship run?

**Why it is a "good question" (course rubric).** The live tension is *causal direction*: populists
may capture institutions and raise corruption once in power, OR corruption may push voters toward
anti-elite parties. A lead-lag / Granger framing tests the direction instead of asserting a
correlation. A partial or null result is acceptable and explicitly rewarded, provided the question is
relevant and the method is sound.

**Stakeholders.** Anti-corruption bodies (Transparency International, the EU's GRECO), election
watchdogs, voters weighing "drain-the-swamp" claims.

**Hard constraint.** V-Dem family only: **V-Dem Country-Year: Full+Others** and **V-Party
Country-Party-Date**. Both join on `country_id` + `year`. (ERT, also a V-Dem Institute product, is
available if episode labels are ever needed.)

## Analysis plan (one coherent thread, not a battery of models)

1. **Association** — country + year fixed-effects panel regression of corruption on a country-level
   populism score. FE makes it a within-country question: "when a country's populism rises, does
   corruption rise?"
2. **Direction** — lead-lag regressions / panel Granger: populism(t) -> corruption(t+1,t+2) vs
   corruption(t) -> populism(t+1). Compare the two.
3. **Decomposition** — re-run on the four corruption sub-measures; a "strong on executive, null on
   judicial" pattern is a mechanism story. Caveat: sub-measures share inputs and are correlated.

**Decision rule.** If FE cannot beat a naive persistence baseline, lean into the direction /
interpretation framing where the contribution does not need a strong predictive result.

## Variable cheat-sheet (always verify exact names in the reference files)

- Outcome (V-Dem): `v2x_corr` (composite, **runs less->more corrupt**), `v2x_execorr`, `v2x_pubcorr`,
  `v2lgcrrpt`, `v2jucorrdc`. Full defs: `references/vdem-variables.md`.
- Predictor (V-Party): `v2xpa_popul` (populism index), `v2xpa_antiplural` (anti-pluralism). For
  nationalism use `v2paculsup` / `ep_galtan` (no single nationalism index exists). Full list and
  index formulas: `references/vparty-variables.md`.
- Controls/moderators: `v2x_regime`, `v2x_rule`, `v2x_polyarchy`, `v2x_libdem`; GDP/pop are Type E
  (`e_` prefix) in Full+Others.
- Join keys: `country_id` (numeric), `year`. Successor-state subtleties: `references/country-coding.md`.

## The gotchas that will bite (full detail in references)

1. **Corruption is reverse-coded** - `v2x_corr` runs clean->corrupt, opposite to most indices. A
   positive populism->`v2x_corr` coefficient = more corruption. Harmonize orientation once, document it.
2. **Filter `_nr <= 3`** for every C-type variable (coder count). See `references/measurement-model.md`.
3. **Right version for the job** - plain estimate for regression; `_osp`/`_ord` for interpretation;
   `_codelow/_codehigh/_sd` for uncertainty. See `references/measurement-model.md`.
4. **Window = 1970-2019** - V-Party expert codings end 2019; V-Dem runs to 2025. `how="inner"` enforces it.
5. **V-Party is party-level + election-dated** - must aggregate parties -> country-year and carry
   election values to non-election years. See `references/aggregation.md` for the full menu of methods.

## Code skeletons (project-specific; references stay code-free)

```python
import pandas as pd
from linearmodels.panel import PanelOLS

# 1. filter low-coder V-Party cells (see references/measurement-model.md for the rule)
for v in ["v2paanteli", "v2papeople", "v2paculsup", "v2paminor", "v2paimmig"]:
    nr = v + "_nr"
    if nr in vparty: vparty.loc[vparty[nr] <= 3, v] = pd.NA

# 2. aggregate parties -> country-year (governing-party variant; see references/aggregation.md)
gov = vparty[vparty["v2pagovsup"] == 0]
cpop = gov.groupby(["country_id", "year"])["v2xpa_popul"].mean().reset_index()

# 3. election-year -> annual panel via within-country forward fill (document the assumption)
cpop = (cpop.set_index("year").groupby("country_id")
        .apply(lambda s: s.reindex(range(1970, 2020)).ffill()).reset_index())

# 4. merge with V-Dem country-year (inner join enforces the 1970-2019 overlap)
panel = vdem_cy.merge(cpop, on=["country_id", "year"], how="inner")

# 5. two-way FE association
p = panel.set_index(["country_id", "year"])
m1 = PanelOLS.from_formula(
    "v2x_corr ~ v2xpa_popul + v2x_rule + EntityEffects + TimeEffects", p
).fit(cov_type="clustered", cluster_entity=True)
```

## Pivot options inside the allowed data
- Swap predictor: `v2xpa_antiplural` or `v2paculsup` instead of populism.
- Swap outcome: `v2paclient` (clientelism, party-level) as a corruption-like outcome **inside V-Party**
  (no cross-dataset join).
- Talk-vs-outcome: `ep_corrupt_salience` (party's stated anti-corruption emphasis) vs actual
  `v2x_corr` - fully internal gap study.

## Reference files (pure documentation + domain knowledge)
- `references/variable-taxonomy.md` - the dataset's OWN section structure (official variable groups
  + tag-stem map); start here to locate a family before drilling into the detailed files below.
- `references/vparty-variables.md` - every V-Party variable group with definitions, scales, index formulas.
- `references/vdem-variables.md` - V-Dem variable groups useful for this project AND for EDA broadly.
- `references/measurement-model.md` - variable types, suffixes, the IRT model, coder-count filtering.
- `references/aggregation.md` - domain knowledge on collapsing party-level data to country level.
- `references/country-coding.md` - how countries, successor states, and ex-colonies are coded.
- `references/cautionary-notes.md` - measurement caveats for the report's data-quality section.
- `references/eda-checklist.md` - dataset-grounded EDA starting points and useful derived features.