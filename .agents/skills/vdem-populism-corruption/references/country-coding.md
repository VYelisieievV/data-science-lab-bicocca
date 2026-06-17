# Country Coding: Units, Successor States, Colonies, Gaps

Pure documentation from the V-Dem v16 codebook (identifier variables + country table) and the V-Party
V2 Coding Units document. This governs *which rows exist* and how political units that were created,
absorbed, or dissolved are represented — essential for any panel built across the 20th century.

## What counts as a "country" in V-Dem
A V-Dem country is **a political unit enjoying at least some degree of functional and/or formal
sovereignty**. This is deliberately broader than "UN member state": it includes historical polities,
colonies coded prior to independence in some cases, and units that later ceased to exist. Each unit
has a stable numeric `country_id` and a time-specific name `histname`.

## Coding period variables (the rows that exist for a unit)
- `codingstart` — first year coded: 1789, or when the unit first had some sovereignty. Variants:
  `codingstart_contemp` (Contemporary V-Dem start) and `codingstart_hist` (Historical V-Dem start).
- `codingend` — last year coded: a maximum, or the year the unit lost sovereignty / ceased to exist.
- `gapstart` / `gapend` — a unit can have **gaps** (years it did not meet the sovereignty criterion,
  e.g. occupation or loss of independence); `gapstart` = last date before the gap, `gapend` = first
  date after. Gaps mean a country's series can be non-contiguous.

## How creation / absorption / dissolution is handled
The general logic: **each distinct sovereign unit gets its own `country_id` and its own coding
window**, and one of several units may be designated the **continuing state** that carries the prior
entity's `country_id`.

### Ex-USSR (illustrative `country_id` and coverage windows)
- **Russia (11): 1789–2025** — Russia carries the continuous series and is treated as the continuing
  state of the Soviet Union (the USSR period sits inside Russia's series; V-Party lists a "Soviet
  Union" party block under Russia).
- The other republics get **separate ids starting at (re)independence**, e.g. **Armenia (105):
  1990–2025**, **Ukraine (100): 1990–2025**, **Estonia (161): 1918–2025** (independence, with a
  Soviet-era gap), **Latvia (84): 1920–2025**, **Lithuania (173): 1918–2025**. Interwar-independent
  Baltic states thus show an early window, a gap during Soviet annexation, then a resumed window.

### Ex-Yugoslavia
- **Serbia (198): 1804–2025** tends to carry the longer continuing series (Serbia/SFR Yugoslavia /
  Serbia & Montenegro lineage); V-Party lists "Yugoslavia"-era party blocks under the relevant unit.
- Successor republics get their own ids from independence: **Croatia (154)**, **Slovenia (202):
  1989–2025**, **North Macedonia (176): 1991–2025**, **Bosnia and Herzegovina (150): 1992–2025**,
  **Montenegro (183)**, **Kosovo (43): 1999–2025**.

### Czechoslovakia
- **Czechia (157): 1918–2025** and **Slovakia (201): 1939–2025** appear as separate units; the
  interwar/federal period is represented within these lineages rather than as a single "Czechoslovakia"
  contemporary row.

### Ex-colonies
- Many post-colonial states are coded **from a date tied to first sovereignty / national declaration
  rather than 1789**, e.g. most African and Asian states start **1900** or at independence
  (Algeria 103: 1900–2025; Senegal 31: 1904–2025; Burkina Faso 54: 1919–2025; Burundi 69: 1916–2025;
  Gabon 116: 1910–2025). V-Party's per-country tables list parties "elected to the national
  legislative body at least once starting 1900 or the year the country was declared."
- Some colonial-era / sub-sovereign units are coded too (e.g. **Hong Kong (167): 1900–2025**).

### Historical sub-national / pre-unification units
- Pre-unification German states appear as their own historical ids with closed windows, e.g.
  **Baden (349): 1789–1871**, **Bavaria (350): 1789–1871**, **Hamburg (362): 1789–1867**,
  **Hanover (357): 1789–1866** — they end when absorbed into the German Empire.
- **German Democratic Republic (137): 1949–1990** is its own unit, ending at reunification, separate
  from **Germany (77): 1789–2025**.

## Practical implications for a panel
- **Joining V-Party to V-Dem on `country_id` is safe** because both use the same id scheme; successor
  states line up automatically.
- **The series are not all the same length or contiguous.** Expect: short post-1970 windows for many
  ex-colonies and post-Soviet/Yugoslav states; gaps for occupied/annexed periods; closed windows for
  historical units irrelevant to a 1970–2019 study.
- **A 1970–2019 window** (the V-Party expert-coding overlap) sidesteps most historical-unit
  complications, but still includes the post-1989/1991 birth of many Eastern European units — those
  countries simply enter the panel at independence, which is correct, not missingness to be imputed.
- **`histname` vs `country_name`:** use `country_id` for joins/grouping (stable); `histname` for
  display in the year in question.
- **Watch the historical/contemporary overlap (~1900–1920)** for A-type variables — contemporary
  scores are used by default there and can show artificial jumps at the boundary (irrelevant to a
  1970+ window; see `cautionary-notes.md`). `v3`-prefixed variables hold original historical coding
  where it differs.

> The authoritative source for any specific unit's window, gaps, and lineage is the **V-Dem Country
> Coding Units** document (and the **V-Party Party Coding Units** document for party-level coverage).
> The `country_id` values above are stable identifiers; treat exact start years as illustrative and
> verify against the codebook country table for a given release.