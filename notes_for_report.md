# Notes for Report — Populism and Political Corruption (V-Dem / V-Party)

## Research question

Do countries governed by populist (and/or nationalist / anti-pluralist) parties exhibit higher
political corruption — which dimension of corruption (executive, legislative, judicial,
public-sector) is most affected, and in which temporal direction does the relationship run?

**Stakeholders:** anti-corruption agencies, election watchdogs, voters.

**Data constraint:** V-Dem family only — V-Dem Country-Year: Full+Others and V-Party
Country-Party-Date. Both join on `country_id` + `year`.

## 1. Corruption variables — `vdem.raw.vdem_country_year`

⚠️ Reverse-coded relative to most V-Dem indices: **0 = clean → 1 = most corrupt**.

| Variable | Description | Type | Non-null (1789–2025) |
|---|---|---|---|
| `v2x_corr` | Political Corruption Index (composite) = mean of the four spheres below | D, 0–1 | 27,199 / 28,092 |
| `v2x_execorr` | Executive corruption index = mean(`v2exbribe` bribery, `v2exembez` embezzlement) | D, 0–1 | 27,396 |
| `v2x_pubcorr` | Public-sector corruption index = mean(`v2excrptps` bribery, `v2exthftps` theft) | D, 0–1 | 27,548 |
| `v2lgcrrpt` | Legislature corrupt activities (set missing if `v2lgbicam`==0, i.e. no legislature) | C, ordinal 0–4 | 18,650 (lower — expected) |
| `v2jucorrdc` | Judicial corruption decisions (bribery in court rulings) | C, ordinal 0–4 | 27,716 |

Within the 1970–2019 overlap with V-Party: `v2x_corr` 8,388/8,454 rows, 182 countries —
good coverage.

## 2. Populism + government status — `vdem.raw.vparty_country_party_date`

- **Populism index:** `v2xpa_popul` (D, 0–1) = harmonic mean of rescaled `_osp` versions of
  `v2paanteli` (anti-elitism) and `v2papeople` (people-centrism). Uncertainty versions:
  `v2xpa_popul_codelow` / `v2xpa_popul_codehigh`.
- **Government status:** `v2pagovsup` — 0 = senior governing partner (PM's party), 1 = junior
  governing partner, 2 = supports government without holding office, 3 = opposition,
  4 = no government formed.
- (Pivot option) Anti-pluralism: `v2xpa_antiplural`. No single nationalism index exists; closest
  proxy is `v2paculsup` (cultural superiority) or external `ep_galtan` (CHES TAN pole).

## 3. Coverage checks (DuckDB queries against `data/duckdb/vdem.duckdb`)

- V-Party: 11,898 rows, 178 countries, years 1900–2019, but expert-coded fields
  (`v2pagovsup`, `v2xpa_popul`, etc.) are **0% populated before 1970** — coding starts exactly
  in 1970 as documented.
- Within 1970–2019: `v2pagovsup` is 83.5% non-null (6,280 / 7,518 rows).
- Senior governing parties (`v2pagovsup == 0`): 1,633 rows, of which 1,629 have a non-null
  `v2xpa_popul` score → governing-party aggregation has very good coverage.
- V-Party observations are dense only in **election years** per country (~25–41 countries
  observed in any single year, not the full 178) — confirms the need for temporal expansion
  (forward-fill) when merging onto V-Dem's annual panel.

## 4. Aggregation strategy: V-Party (party-date) → country-year

1. Filter low-coder cells (`_nr <= 3`) on party-level variables *before* aggregating.
2. Cross-party aggregation: use the **governing-party score** (`v2pagovsup == 0`) as the
   primary measure (matches "populists in power" framing); cross-check with a
   **seat-share-weighted mean** across all parties as a robustness variant.
3. Temporal expansion: **forward-fill within country** from each election year to the next
   election year (assumes governing party's populism score is constant between elections —
   state this explicitly as a modeling assumption).
4. Merge with V-Dem country-year via `inner join` on `country_id` + `year`. This naturally
   restricts the analysis panel to **1970–2019**, the V-Party expert-coding window.

## Analysis plan (next steps)

1. **Association** — two-way fixed-effects panel regression: `v2x_corr ~ v2xpa_popul + controls`,
   with country + year FE (within-country question).
2. **Direction** — lead-lag regressions: populism(t) → corruption(t+1, t+2) vs.
   corruption(t) → populism(t+1), to test causal direction.
3. **Decomposition** — repeat on the four corruption sub-measures (`v2x_execorr`, `v2x_pubcorr`,
   `v2lgcrrpt`, `v2jucorrdc`) to see which dimension is most affected. Caveat: sub-measures share
   inputs and are correlated, so treat as suggestive, not independent confirmations.

**Decision rule:** if fixed-effects regression cannot beat a naive persistence baseline, lean
into the direction/interpretation framing, where the contribution does not require a strong
predictive result.
