# V-Dem Variable Documentation

Source: *V-Dem Codebook v16* (V-Dem Institute, March 2026), Country-Year: Full+Others. Pure
documentation: definitions, scales, aggregation, coverage. Unit: country–year, 1789–2025
(usable overlap with V-Party = 1970–2019).

## Dataset facts
- **Full+Others** contains all 531 V-Dem indicators, 251 indices, plus 62 external (E) indicators
  (incl. GDP, population, education). **Core** has only the 5 high-level indices, 93 sub-indices,
  and 179 constituent indicators — and lacks the corruption sub-indices and external controls, so
  this project needs Full+Others.
- Variable types: A*/A (factual), B (factual, country coordinator), C (expert-coded, ≥5 coders
  target), A,C (expert + RA cross-check), D (indices), E (imported external). See `measurement-model.md`.
- Suffix versions on C and D variables: plain / `_osp` / `_ord` / `_codelow` / `_codehigh` / `_sd` /
  `_mean` / `_nr`. See `measurement-model.md`.

## ⚠️ Reverse-coding: the corruption family
The corruption index and its sub-indices run **less corrupt (0) → more corrupt (1)** — the opposite
of nearly every other V-Dem index (which runs less → more democratic). The codebook states this for
`v2x_corr`, `v2x_execorr`, `v2x_pubcorr`. Track orientation carefully when combining with other indices.

## Corruption (Section 5.7)
- `v2x_corr` — Political corruption index (D, 0–1). Average of four equally weighted spheres:
  `v2x_pubcorr`, `v2x_execorr`, `v2lgcrrpt`, `v2jucorrdc`. Where there is no legislature, average of
  the other three. Covers petty/grand, bribery/theft, law-making vs implementation. (McMann et al. 2016.)
- `v2x_execorr` — Executive corruption index (D, 0–1). Average of `v2exbribe` (executive bribery) and
  `v2exembez` (executive embezzlement).
- `v2x_pubcorr` — Public-sector corruption index (D, 0–1). Average of `v2excrptps` (bribery) and
  `v2exthftps` (theft).
- `v2lgcrrpt` — Legislature corrupt activities (C). Ordinal 0–4 → interval. Since Dec 2014, reversed
  so 0 = most corrupt ("Commonly") … 4 = least ("Never/hardly ever"). Set missing if `v2lgbicam`==0.
- `v2jucorrdc` — Judicial corruption decision (C). 0=Always (bribes) … 4=Never.
- Related country-level corruption-adjacent indices (Section 5.4):
  `v2x_neopat` — Neopatrimonial Rule index (D); `v2xnp_client` — Clientelism index (D);
  `v2xnp_regcorr` — regime corruption (component). Useful robustness/alternative outcomes.

## High-level democracy indices (Section 2.1; all D, interval 0–1, low→high democracy)
- `v2x_polyarchy` — Electoral democracy index. Inputs: `v2x_freexp_altinf`, `v2x_frassoc_thick`,
  `v2x_suffr`, `v2xel_frefair`, `v2x_elecoff`.
- `v2x_libdem` — Liberal democracy. Inputs: `v2x_liberal`, `v2x_polyarchy`.
- `v2x_partipdem` — Participatory. Inputs: `v2x_polyarchy`, `v2x_partip`.
- `v2x_delibdem` — Deliberative. Inputs: `v2xdl_delib`, `v2x_polyarchy`.
- `v2x_egaldem` — Egalitarian. Inputs: `v2x_egal`, `v2x_polyarchy`.
- Additive variants: `v2x_api` (additive polyarchy), `v2x_mpi` (multiplicative polyarchy).

## Mid-level component indices (Section 2.2) — strong EDA/control material
- `v2x_liberal` — Liberal component index. Inputs: `v2xcl_rol`, `v2x_jucon`, `v2xlg_legcon`.
- `v2xcl_rol` — Equality before the law and individual liberty.
- `v2x_jucon` — Judicial constraints on the executive.
- `v2xlg_legcon` — Legislative constraints on the executive.
- `v2x_freexp_altinf` — Freedom of expression & alternative information.
- `v2x_frassoc_thick` — Freedom of association (thick).
- `v2xel_frefair` — Clean elections index.
- `v2x_cspart` — Civil society participation index. (Convergence-flagged in v16 — use HPD.)
- `v2x_suffr` — Share of population with suffrage. `v2x_elecoff` — elected officials.

## Rule of law, accountability, civil liberties (Section 5)
- `v2x_rule` — Rule of law index (D).
- `v2x_accountability` — Accountability index (D); sub-indices `v2x_veracc` (vertical),
  `v2x_diagacc` (diagonal), `v2x_horacc` (horizontal). Horizontal accountability is conceptually
  close to anti-corruption constraints.
- `v2x_civlib` — Civil liberties index; `v2x_clphy` (physical violence), `v2x_clpol` (political),
  `v2x_clpriv` (private) sub-indices.
- `v2x_freexp` — Freedom of expression index (5.12).
- `v2xca_academ` — Academic Freedom Index (5.15).
- `v2x_gender` — Women's political empowerment index (5.8); sub-indices `v2x_gencl` (civil liberties),
  `v2x_gencs` (civil society), `v2x_genpp` (political participation).

## Regime classification (Section 5.1)
- `v2x_regime` — Regimes of the World (RoW), ordinal: 0 Closed autocracy; 1 Electoral autocracy;
  2 Electoral democracy; 3 Liberal democracy. Built from electoral-regime, multiparty, free/fair,
  and liberal-component inputs. Useful as a categorical moderator/stratifier.
- `v2x_regime_amb` — RoW with extra categories for ambiguous (confidence-interval-overlapping) cases.

## External structural variables (Type E, `e_` prefix; Full+Others only)
- GDP per capita and population are bundled here (exact tags vary by release — inspect the
  Full+Others header / codebook "External Variables" section; common style: `e_gdppc`, `e_pop`).
- Education, area, and other Quality-of-Government-sourced controls also appear with `e_` tags.
- Regions: `e_regionpol` (10-cat), `e_regionpol_6C` (6-cat), `e_regiongeo` (19-cat).

## Identifiers
- `country_id` (numeric — join key, same scheme as V-Party), `country_text_id`, `year`, `COWcode`,
  `histname` (time-specific country name), `codingstart` / `codingend` (and `_contemp` / `_hist`
  variants), `gapstart` / `gapend` (coding gaps). See `country-coding.md` for what these encode.