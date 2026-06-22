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

## Section 8a — Data Description (update)

- Effective analysis window: 1970–2019 (constrained by V-Party expert-coded variables starting 1970).
- Final panel after inner join: ~8,400 country-years, 182 countries.
- 1,629 senior governing party observations with both populism and corruption available.

## Section 8b — Weaknesses (update)

- V-Party expert-coded vars start in 1970, not 1900.
- V-Party is dense only in election years (~25–41 countries/year); requires a forward-fill
  assumption to build an annual panel.
- Coverage ends in 2019, missing the recent populist surge (Meloni in Italy, Trump's second term,
  etc.).

## Methodology Decisions (for Section 9)

- Primary measure of populist governance: `v2xpa_popul` of the senior governing party
  (`v2pagovsup == 0`).
- Robustness check: seat-share-weighted mean across all parties.
- Temporal extension: forward-fill from elections to the next election.
- Data quality filter: exclude cells with fewer than 4 coders (`_nr <= 3`).
- Final dataset: inner join on (`country_id`, `year`), restricting the panel to 1970–2019.

### Populism measurement

- Distribution: N=1,628 senior governing party-years, mean=0.330,
  median=0.274, 75th pct=0.470, skewness ≈ 0.85
- Shape: unimodal, right-skewed, NO bimodal break point
- DECISION: Populism is treated as a **continuous variable** throughout the primary
  analysis (regression, lead-lag, decomposition) — no arbitrary binary cutoff, no
  threshold enters any model specification.
- The 0.47 (75th percentile) threshold is used **only** as a visual label for
  top-quartile "high-populism governments" in Section 4 (descriptive comparisons) —
  it is a presentation device, not a modeling choice, and does not feed into any
  regression or robustness check.

### Direction fix for legislative/judicial corruption (Section 4a, Section 5)

- `v2lgcrrpt`/`v2jucorrdc` plain values are latent z-scale estimates (~-3...+4,
  *higher = cleaner*) — opposite convention from the 0-1 `v2x_*` D-indices
  (*higher = more corrupt*). Fixed by rescaling the `_ord` (0-4) versions to
  `(4 - ord) / 4`, giving 0-1 variables where higher always means more corrupt.
- ⚠️ **Caveat discovered in Section 5's case-study plots:** `v2jucorrdc_ord` is too
  coarse (only 0-4 discrete levels) to show within-country variation for several of
  the case-study countries over 1970-2019 — Venezuela, Bolivia, and Ecuador each take
  only a **single** distinct `v2jucorrdc_ord` value across the entire 50-year window;
  Hungary only 2 distinct values; Turkey only 3. The flat `v2jucorrdc_01` line in
  those plots reflects this coding resolution, not an actual absence of judicial
  corruption change — do not read "flat line" as "no change" for this variable.
  Affects any model that uses `v2jucorrdc` (or its `_ord`/rescaled version) as a
  within-country (fixed-effects) outcome: there may be too little time variation to
  identify a country-FE coefficient for some units.

## Findings

- Cross-sectional correlation matrix shows judicial corruption (v2jucorrdc) correlates
  most strongly with governing populism — consistent with literature on institutional
  capture (Hungary, Poland, Venezuela, Turkey). This is a strong starting hypothesis for
  the FE regression (Section 3 of methodology). However, this is correlational; causal
  direction remains to be tested via lead-lag analysis (Section 4 of methodology).

## Variables of Interest

⚠️ **Note:** corruption variables are coded with 0 = low corruption, 1 = high corruption
(opposite of most V-Dem indices).

- `v2x_corr` — composite political corruption.
- `v2x_execorr` — executive corruption.
- `v2x_pubcorr` — public sector corruption.
- `v2lgcrrpt` — legislative corruption (missing where no legislature exists).
- `v2jucorrdc` — judicial corruption.
- `v2xpa_popul` — populism index (V-Party).
- `v2pagovsup` — party government status (V-Party).

## Potential additional controls (for robustness)

- `v2x_electoral_integrity` (NEW in v16): populist governments often degrade electoral
  processes; controlling for this would help isolate the populism→corruption channel from
  broader democratic backsliding.
- `v2x_lidem_stock`, `v2x_polyarchy_stock` (NEW in v16): democratic maturity controls.
- `e_ovexist` (NEW in v16): political instability control.

These were not included in the primary panel for simplicity but can be easily joined from
the V-Dem CSV for robustness checks.

**Example — raw CSV snippet** (`V-Dem-CY-Full+Others-v16.csv`, join keys `country_id`+`year`):

```csv
country_id,year,v2x_electoral_integrity,v2x_lidem_stock,v2x_polyarchy_stock,e_ovexist
2,1970,0.812,0.452,0.601,0
2,1971,0.798,0.460,0.598,0
20,1970,0.343,0.110,0.205,1
20,1971,0.337,0.112,0.201,1
```

**Example join (Polars, mirrors the join pattern in `notebooks/02_preprocessing.ipynb` Section 3):**

```python
import polars as pl

extra_controls = pl.read_csv(
    "data/raw/V-Dem-CY-Full+Others-v16.csv",
    columns=["country_id", "year", "v2x_electoral_integrity",
             "v2x_lidem_stock", "v2x_polyarchy_stock", "e_ovexist"],
)

panel = panel.join(extra_controls, on=["country_id", "year"], how="left")
```
