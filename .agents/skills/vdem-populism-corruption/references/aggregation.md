# Aggregating Party-Level Data to Country Level

Pure domain knowledge: V-Party is observed at **country–party–election** granularity, but most
country-level analysis (and any merge with V-Dem's country–year data) needs **one value per
country–year**. There is no single "correct" aggregation — the choice encodes a substantive
assumption about *whose* populism matters. Document the choice and test sensitivity to it.

## The two transformations involved
1. **Cross-party aggregation** — collapse the several parties observed at an election into one
   country number.
2. **Temporal expansion** — turn election-year observations into an annual series (V-Party only has
   election years; V-Dem is annual).

## Cross-party aggregation methods (the substantive menu)

### 1. Governing-party / incumbent score
Take the party in power (`v2pagovsup == 0` = senior governing partner, Head of Government from this
party). The country's populism = the governing party's score.
- *Assumes:* what matters is who holds executive power (natural for "do populists in power raise
  corruption?").
- *Edge cases:* coalition governments (multiple parties with `v2pagovsup ∈ {0,1}`); caretaker
  cabinets (excluded by the codebook's wording); periods with no government formed (`==4`).
- *Variant:* weight governing + junior partners by their seat share within the government.

### 2. Seat-share-weighted mean across all parties
Weight every party's score by `v2paseatshare` (or `v2panumbseat / v2patotalseat`).
- *Assumes:* the "populism of the legislature/political climate" matters, not just the leader.
- *Robust to* which party happens to lead; captures a populist opposition too.

### 3. Vote-share-weighted mean across all parties
Same as (2) but weight by `v2pavote`.
- *Use when* seat data is missing, or to capture electoral support rather than translated seats
  (the two differ under disproportional electoral systems).

### 4. Maximum / presence indicators
- *Max populism* among parties above a threshold — captures the most populist relevant actor.
- *Binary:* "is any party with populism above cutoff X in government?" — simplest, most robust,
  loses gradation. Good as a robustness check or for a logit framing.

### 5. Unweighted mean across coded parties
Simplest; treats all >5%-vote parties equally. Usually dominated by (2)/(3) but useful as a baseline.

## Weighting and edge-case considerations
- **Alliances/coalitions** (`v2paallian`): longstanding alliances (e.g. CDU/CSU) are coded "as if"
  one party — their `v2paseatshare` already reflects the bloc; do not also add component parties.
  Temporary alliances are coded as individual parties with alliance totals in `v2pavallian` /
  `v2panoallian`; weighting by party seat share avoids double counting.
- **One-party regimes** (e.g. communist states without competitive elections): the ruling party is
  coded at intervals, not at elections. Keep but flag; weighting schemes that assume vote shares may
  not apply.
- **Missing weights:** some elections lack vote share; fall back to seat share, and vice versa.
- **Coder filtering first:** apply the `_nr ≤ 3` filter to party-level cells *before* aggregating so
  unreliable party scores do not enter the country mean (see `measurement-model.md`).
- **Uncertainty propagation:** if the country score is a weighted mean of party point estimates,
  uncertainty can be propagated by aggregating over the parties' posterior draws or by carrying the
  parties' HPD/SD into the weighted combination, rather than discarding it.

## Temporal expansion methods (election-year → annual)
- **Forward fill within country:** carry an election's value to subsequent years until the next
  election. *Assumes* the governing party's identity/populism is constant between elections — a
  reasonable approximation for the governing-party method, an assumption to state explicitly.
- **Step function at government changes:** if mid-term government changes are known, update at the
  change rather than only at elections (more precise, more data work).
- **Keep election years only:** restrict the panel to election years and merge V-Dem at those years —
  fewer rows, no interpolation assumption, but loses the annual structure useful for lead-lag.
- **Interpolation** between elections is generally *not* advisable for a categorical/identity score
  (a party does not become "half populist" between elections); forward-fill is preferred.

## Aggregation level already provided by V-Party
V-Party itself provides each expert-coded variable aggregated to **country-party-year** (the `_mean`
and measurement-model versions). The analyst's remaining job is the **party → country** step above;
the **coder → party-year** step is already done by the measurement model.

## How V-Dem itself aggregates over time (for reference)
V-Dem's own country-year values use **day-weighted means** of country-date observations (a value that
holds for more days in the year gets more weight). This is why V-Dem country-year scores can differ
slightly from a simple end-of-year snapshot — relevant if cross-checking against the country-date file.