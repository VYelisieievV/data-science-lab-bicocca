# V-Party Variable Documentation

Source: *Codebook Varieties of Party Identity and Organization (V-Party) V2* (V-Dem Institute,
Feb 2022). This file is pure documentation: definitions, scales, coverage, index formulas.

## Dataset facts
- **Unit of observation:** country–party–(election) date/year ("Country-Party-Date" file).
- **Coverage:** factual data (vote/seat) on parliamentary parties for all V-Dem countries 1900–2019;
  expert-coded identity/organization for most parties 1970–2019 (Cuba from 1965).
- **Scope rule:** experts coded every party that won >5% of the vote at a given election (seat share
  used where vote share is unavailable). Includes alliances/coalitions.
- **Scale of the project:** 3,467 parties, 3,151 elections, 178 countries, 11,898 party-election-year
  units. Typically ≥4 coders per observation (model assumes ≥5).
- **Aggregation:** expert ratings combined with V-Dem's Bayesian IRT measurement model.
- **Variable totals (per codebook Table 1):** 78 variables — 27 identifiers, 2 indices, 11 party
  basics, 17 party identity, 9 party organization, 12 external party-level.

## Identifier variables (selected)
- `v2paid` — numeric party identifier (Party Facts core-party id). `pf_party_id`, `CHES_ID`,
  `GPS_ID` — cross-walk ids to other party datasets.
- `v2paenname` / `v2paorname` / `v2pashname` — party name (English / original / short).
- `country_id` — V-Dem numeric country id (**the join key to V-Dem**); `country_text_id` — abbrev.
- `year` — election/observation year; `historical_date` — YYYY-MM-DD (date file).
- `party_gaps`, `gap_index` — periods a party was out of the legislature.
- `e_regiongeo` (19-cat geographic), `e_regionpol` (10-cat politico-geographic),
  `e_regionpol_6C` (6-cat) — region groupings, useful for stratified EDA and error clustering.
- `COWcode` — Correlates of War country code.

## Indices (Type D, interval 0–1, low→high)

### `v2xpa_popul` — Populism index
- Concept: extent of populist rhetoric (narrowly defined).
- Inputs: `v2paanteli` (anti-elitism) + `v2papeople` (people-centrism).
- Formula: harmonic mean of rescaled `_osp` components —
  `v2xpa_popul = 2 / (1/x + 1/y)` with `x = v2paanteli_osp/4`, `y = v2papeople_osp/4`.
- Versions: `_codelow`, `_codehigh`.

### `v2xpa_antiplural` — Anti-pluralism index
- Concept: lacking commitment to democratic norms prior to elections.
- Inputs: `v2paopresp`, `v2paplur`, `v2paminor`, `v2paviol`.
- Formula: `1 - Φ( (0.5·v2paopresp + 2·v2paplur + v2paminor + v2paviol) / 4.5 )`, Φ = standard
  normal CDF. (Renamed from `v2xpa_illiberal` in V1.)
- Versions: `_codelow`, `_codehigh`.

## Party Identity indicators (Type C; ordinal 0–4 unless noted; plain version is interval)
- `v2paanteli` — Anti-elitism (importance of anti-elite rhetoric). 0=Not at all … 4=Very important.
- `v2papeople` — People-centrism (glorifies "ordinary people"). 0=Never … 4=Always.
- `v2paopresp` — Political opponents: demonization/personal attacks. 0=Always … 4=Never.
- `v2paplur` — Political pluralism: commitment to free/fair multiparty elections, speech, assembly.
  0=Not at all committed … 4=Fully committed. (Convergence caution — high expert disagreement.)
- `v2paminor` — Minority rights: how often majority will should override minority rights.
  0=Always override … 4=Never.
- `v2paviol` — Rejection of political violence. 0=Encourages … 4=Consistently discourages.
- `v2paimmig` — Immigration position. 0=Strongly opposes … 4=Strongly supports.
- `v2palgbt` — LGBT social equality. 0=Strongly opposes … 4=Strongly supports.
- `v2paculsup` — Cultural superiority (promotes superiority of a social group / the nation).
  0=Strongly promotes … 4=Strongly opposes. (Closest single nativist/nationalism indicator.)
- `v2parelig` — Religious principles (invokes religion to justify positions). 0=Always … 4=Never.
- `v2pagender` — Gender equality: share of women in party national leadership. 0=None … 4=Balanced.
- `v2pawomlab` — Working women: supports equal labor-market participation. 0=Strongly opposes … 4=…supports.
- `v2pariglef` — Economic left-right. 0=Far-left … 6=Far-right.
- `v2pawelf` — Welfare: means-tested vs universalistic. 0=opposes any … 5=solely universalistic.
- `v2paclient` — Clientelism: targeted/excludable goods for votes. 0=Not at all … 4=Main effort.
- `v2pasalie` — Salience & mobilization: multi-select issue dummies `v2pasalie_0..17` (0=No,1=Yes),
  including `_12` environmental protection, `_15` anti-corruption, `_6` cultural superiority,
  `_16` intimidation/violence. Aggregated by mean.
- `v2paaspoth` — other salient issues (text; on request).

## Party Basics (Type A factual + some C)
- `v2paseatshare`, `v2panumbseat`, `v2patotalseat` — seat share / number / chamber total.
- `v2pavote` — vote share. (All A-type, from Döring & Düpont 2020.)
- `v2pagovsup` — Government support (A,C): 0=senior governing partner (Head of Gov from this party);
  1=junior partner; 2=supports, not in government; 3=opposition; 4=no government formed.
- `v2paallian` — temporary pre-electoral alliance flag (0=no; 1=party in alliance; 2=entity is an
  alliance). Alliance vote/seats: `v2pavallian`, `v2panoallian`.
- `v2paelcont` — party continuation across elections. `v2papariah` — pariah party (others distance
  themselves). (Convergence caution on `v2papariah`.)

## Party Organisation (Type C; useful as party-strength / capture features)
- `v2palocoff` — permanent local offices (0=none … 4=all municipalities).
- `v2paactcom` — local organizational strength (activist presence).
- `v2pasoctie` — affiliate organizations / ties to social organizations (0=none … 4=controls them).
- `v2panom` — candidate nomination process (0=leader decides … 4=open primaries). Centralization signal.
- `v2padisa` — internal cohesion (elite disagreement). `v2paind` — personalization (vehicle for one leader).
- `v2pagroup` — party support group (multi-select `v2pagroup_0..14`: aristocracy, business elites,
  military, ethnic/racial, religious, working/middle classes, separatists, women, …).
- `v2pafunds` — funding sources (multi-select `v2pafunds_0..7`: state subsidies, individual/company
  donations, CSO donations, membership fees, **informal use of state resources as incumbent**,
  party-leader funds, candidate funds). `_5` is a corruption-relevant signal.

## External party-level data (Type E) — alternative populism/nationalism scales
Distributed inside the V-Party file (so usable without breaking "V-Party only"); from CHES (Bakker
et al.) and the Global Party Survey (Norris 2020). Coverage sparser (mostly Europe / GPS countries).
- `ep_antielite_salience` — salience of anti-establishment rhetoric (0–10, CHES).
- `ep_corrupt_salience` — salience of reducing political corruption (0–10, CHES).
- `ep_people_vs_elite` — direct vs representative democracy position (0–10, CHES).
- `ep_type_populism` (1 Strongly pluralist … 4 Strongly populist), `ep_type_populist_values`
  (1 Pluralist-Liberal … 4 Populist-Conservative), `ep_v8_popul_rhetoric` (0–10),
  `ep_v9_popul_saliency` (0–10) — Norris GPS populism measures.
- `ep_galtan` — GAL–TAN: 0=Libertarian/Postmaterialist … 10=Traditional/Authoritarian/Nationalist
  (CHES); `ep_galtan_salience`; `ep_v6_lib_cons`, `ep_v7_lib_cons_saliency` (GPS social-values).

## Note on a nationalism measure
There is **no `v2xpa_nationalism` index**. The relevant building blocks are `v2paculsup` (cultural
superiority), `v2paminor` (minority rights), `v2paimmig` (immigration), and the external `ep_galtan`
TAN pole. Any nationalism construct is the analyst's own composite and should be documented.