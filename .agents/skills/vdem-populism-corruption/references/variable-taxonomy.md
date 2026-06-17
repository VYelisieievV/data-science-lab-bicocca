# Official Variable Taxonomy (Dataset Section Structure)

Pure documentation: the codebooks organize variables into named thematic sections. This is the
dataset's own map — use it to locate variable families without enumerating all ~530 V-Dem / 78
V-Party variables. Section numbers are codebook references (V-Dem v16; V-Party v2). Variables in a
section share a tag stem (e.g. media variables use `v2me*`, electoral `v2el*`, party `v2pa*`).

## V-Dem — top-level structure
- **1. Explanatory Notes** — variable types, suffixes, identifiers, country table.
- **2. High- and Mid-Level Democracy Indices** (the headline `v2x_*` indices).
- **3. Indicators** (the raw A/B/C building blocks, grouped by political domain).
- **4. Historical V-Dem** (`v3*` variables, pre-1900 and overlap-period coding).
- **5. Other Indices Created Using V-Dem Data** (derived/composite indices, incl. corruption, RoW).
- **6. Party Systems** (party-system-level measures).
- **7. Digital Society Survey** (the Digital Society Project module).
- **8. Varieties of Indoctrination** (V-Indoc module: education/media indoctrination).

### Section 2 — democracy indices
- 2.1 **High-Level Democracy Indices** — `v2x_polyarchy`, `v2x_libdem`, `v2x_partipdem`,
  `v2x_delibdem`, `v2x_egaldem`, plus additive/multiplicative variants.
- 2.2 **Mid-Level Indices (Components)** — e.g. `v2x_liberal`, `v2xcl_rol`, `v2x_jucon`,
  `v2xlg_legcon`, `v2x_freexp_altinf`, `v2x_frassoc_thick`, `v2xel_frefair`, `v2x_cspart`.

### Section 3 — indicators by domain (raw A/B/C; tag stems in parentheses)
- 3.1 **Elections** (`v2el*`) — electoral conduct, fraud, suffrage, EMB autonomy.
- 3.2 **Political Parties** (`v2ps*`) — party institutionalization, branches, linkages.
- 3.3 **Direct Democracy** (`v2dd*`) — referendums, initiatives, plebiscites.
- 3.4 **The Executive** (`v2ex*`) — incl. executive bribery `v2exbribe`, embezzlement `v2exembez`.
- 3.5 **Regime** — regime-type building blocks.
- 3.6 **The Legislature** (`v2lg*`) — incl. legislative corruption `v2lgcrrpt`, `v2lgbicam`.
- 3.7 **Deliberation** (`v2dl*`) — reasoned justification, common good, respect for counterarguments.
- 3.8 **The Judiciary** (`v2ju*`) — judicial independence, compliance, incl. `v2jucorrdc`.
- 3.9 **Civil Liberty** (`v2cl*`) — physical, political, private liberties; equality before the law.
- 3.10 **Sovereignty/State** (`v2sv*`) — state authority over territory, monopoly of force.
- 3.11 **Civil Society** (`v2cs*`) — CSO entry/exit, repression, participation.
- 3.12 **The Media** (`v2me*`) — censorship, harassment of journalists, bias, self-censorship.
- 3.13 **Political Equality** (`v2pe*`) — power distributed by group/gender/SES.
- 3.14 **Exclusion** (`v2xpe*` / `v2pe*`) — political exclusion by social group, gender, SES.
- 3.15 **Civic and Academic Space** (`v2ca*`) — academic freedom indicators, civic mobilization.

### Section 4 — Historical V-Dem (`v3*`)
Mirrors section 3 domains for the historical period (Elections, Parties, Legislature, Judiciary,
Civil Liberty, Sovereignty/State, Political Equality), plus "Modified" and "Overlap-Period
Discrepancy" subsections. Relevant only for pre-1970 / long-historical analysis.

### Section 5 — derived/other indices (selected)
- 5.1 **Regimes of the World** — `v2x_regime`, `v2x_regime_amb`.
- 5.2 **Accountability** — `v2x_accountability`, `v2x_veracc`, `v2x_horacc`, `v2x_diagacc`.
- 5.3 **Executive Bases of Power**.
- 5.4 **Neopatrimonialism** — `v2x_neopat`, `v2xnp_client`, `v2xnp_regcorr` (corruption-adjacent).
- 5.5 **Civil liberties** — `v2x_civlib`, `v2x_clphy`, `v2x_clpol`, `v2x_clpriv`.
- 5.6 **Exclusion** — `v2xpe_exlsocgr` etc. (reverse-directioned; some low-coder cells removed).
- 5.7 **Corruption** — `v2x_corr`, `v2x_execorr`, `v2x_pubcorr` (+ indicators `v2lgcrrpt`,
  `v2jucorrdc`). **Reverse-coded** (high = corrupt).
- 5.8 **Women's Empowerment** — `v2x_gender`, `v2x_gencl`, `v2x_gencs`, `v2x_genpp`.
- 5.9 **Rule of Law** — `v2x_rule`.
- 5.10 Direct Democracy · 5.11 Civil Society · 5.12 Elections (`v2x_freexp`, `v2xel_frefair`) ·
  5.13 Party Institutionalization · 5.14 Consensual Democracy · 5.15 **Academic Freedom**
  (`v2xca_academ`) · 5.16 Electoral Integrity · 5.17 Stock Versions of indices.

### Section 7 — Digital Society Project (DSP)
- 7.1 **Coordinated Information Operations** — government/party disinformation, foreign influence
  (`v2smgovdom`, `v2smgovab`, `v2smpardom`, `v2smparab`, `v2smfordom`).
- 7.2 **Digital Media Freedom** — online media freedom, government internet filtering.
- 7.3 **State Internet Regulation Capacity and Approach** — censorship, shutdowns, surveillance.
- 7.4 **Online Media Polarization**. 7.5 **Social Cleavages** (online).

### Section 8 — Varieties of Indoctrination (V-Indoc)
Education and media indoctrination indices (curriculum control, teacher control, education
centralization, state media). Separate companion module.

## V-Party — section structure (V-Party v2 codebook)
- **1. Explanatory Notes** — types, suffixes, identifiers, country coverage.
- **2. Indices** — `v2xpa_antiplural` (anti-pluralism), `v2xpa_popul` (populism).
- **3. Indicators**:
  - 3.1 **Party Basics** (`v2pa*` factual) — seat/vote share, alliances, government support, pariah.
  - 3.2 **Party Identity** (`v2pa*` C) — anti-elitism, people-centrism, pluralism, minority rights,
    violence, immigration, LGBT, cultural superiority, religion, gender, economic L-R, welfare,
    clientelism, salience.
  - 3.3 **Party Organisation** (`v2pa*` C) — local offices, organizational strength, social ties,
    candidate nomination, cohesion, personalization, support group, funding sources.
- **4. External Party-Level Data** (`ep_*`, Type E) — CHES & Global Party Survey populism / GAL-TAN
  / social-values scales.

## How to use this map
- The **tag stem identifies the family** (`v2me*` = media, `v2ju*` = judiciary, `v2cl*` = civil
  liberty, `v2el*` = elections, `v2pa*` = party survey, `v2sm*` = social media/DSP, `v2ca*` =
  civic/academic, `v2x*` = an index). Grep the dataset header by stem to enumerate a family.
- For this project, the directly relevant families are **5.7 Corruption** + **5.4
  Neopatrimonialism** (outcomes), **V-Party §2/§3.2** (predictors), **2.1/2.2 + 5.9 + 5.2**
  (controls). Everything else is pivot/EDA territory — named here so it can be found, not described
  variable-by-variable (the codebook is the exhaustive reference).