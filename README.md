# Data Science Lab: Populism and Corruption

Data Science Lab project for Bicocca semester 2, analysing whether populist
party power is associated with political corruption using the **V-Dem** and
**V-Party** datasets.

<p align="center">
  <img
    src="https://www.shutterstock.com/image-vector/illustration-businessman-hands-giving-taking-600nw-2480386373.jpg"
    alt="Illustration of money changing hands"
    width="360"
    height="220"
  />
  <img
    src="https://c.files.bbci.co.uk/132DF/production/_100295587_thepopulists2.jpg"
    alt="Illustration about populism"
    width="360"
    height="220"
  />
</p>

## Research Question

Do countries governed by populist parties exhibit higher political corruption,
which dimension of corruption is most affected, and in which direction does the
relationship run over time?

The core challenge is causal direction. Two competing stories are plausible:

- Populists cause corruption by capturing institutions and weakening oversight
  once in power.
- Corruption causes populism when voters back anti-elite parties in response to
  corrupt establishments.

Relevant stakeholders include anti-corruption agencies, election watchdogs, and
voters evaluating populist candidates' anti-establishment claims.

## Data

The project uses native V-Dem and V-Party variables:

| Role | Variable(s) | Notes |
|------|-------------|-------|
| Predictor | V-Party `v2xpa_popul` | Aggregated to country-year as governing-party or weighted parliamentary populism score |
| Outcome | V-Dem `v2x_corr` | Main political corruption index |
| Sub-outcomes | `v2x_execorr`, `v2lgcrrpt`, `v2jucorrdc`, `v2x_pubcorr` | Executive, legislative, judicial, and public-sector corruption |
| Controls | GDP per capita, `v2x_regime`, `v2x_rule` | Economic conditions, regime type, and rule of law |
| Join keys | `country_id`, `year` | V-Party country-year panel joined to V-Dem country-year data |

The **V-Dem** and **V-Party** datasets are not committed because they are large
and regenerable. Download the CSV/Stata releases from
[v-dem.net](https://www.v-dem.net/data/the-v-dem-dataset/) and place them under
`data/raw/`.

```python
import polars as pl

vdem = pl.read_csv("data/raw/V-Dem-CY-Full+Others-v14.csv")
```

`data/raw/` is git-ignored; keep raw downloads local. After loading the
datasets, report the actual analysis window from the downloaded releases rather
than assuming a fixed end year:

```python
vparty.select(pl.min("year"), pl.max("year"))
```

### DuckDB

The two raw CSVs can also be loaded into a local DuckDB database through Docker.
The setup uses the official `duckdb/duckdb:1.5.4` image. The generated database
lives at `data/duckdb/vdem.duckdb` and is ignored by git.

Expected local CSV paths:

- `data/raw/V-Dem/V-Dem-CY-Full+Others-v16.csv`
- `data/raw/V-Party/V-Dem-CPD-Party-V2.csv`

Import the CSVs into DuckDB and open a DuckDB shell:

```bash
docker compose run --rm duckdb
```

This command uses the default Compose command:

```bash
/duckdb /data/duckdb/vdem.duckdb -init /duckdb-init/init.sql
```

`docker/duckdb/init.sql` recreates the raw tables from the CSVs every time this
command runs.

The import recreates these tables:

- `raw.vdem_country_year`
- `raw.vparty_country_party_date`

Useful checks inside the DuckDB shell:

```sql
SELECT * FROM meta.import_summary;
SELECT * FROM meta.analysis_window;
```

Import the CSVs and run a SQL query directly from the terminal:

```bash
docker compose run --rm duckdb /data/duckdb/vdem.duckdb \
  -init /duckdb-init/init.sql \
  -c "SELECT * FROM meta.import_summary;"
```

Run a SQL query against the existing database without rerunning the import:

```bash
docker compose run --rm duckdb /data/duckdb/vdem.duckdb \
  -c "SELECT * FROM meta.import_summary;"
```

Open the existing database without rerunning the import:

```bash
docker compose run --rm duckdb /data/duckdb/vdem.duckdb
```

## Methodology

1. Build the country-year panel and aggregate party-level populism to the
   country level.
2. Explore cross-sectional correlations between populism and corruption.
3. Estimate panel regressions with country and year fixed effects.
4. Use lead-lag / Granger-style checks to probe directionality.
5. Decompose corruption by subtype to identify which dimension moves most.

## Analysis Notes

- `v2x_corr` runs from cleaner to more corrupt. A positive coefficient on
  populism means higher estimated corruption, not better integrity.
- V-Party is party-level and election-dated, while V-Dem is country-year. The
  party-to-country aggregation choice is substantive: governing party,
  seat-share weighted mean, vote-share weighted mean, or maximum/populist
  presence answer slightly different questions.
- For expert-coded C-type variables, use the plain point estimate for the main
  regression and keep `_codelow`, `_codehigh`, or `_sd` variants for uncertainty
  checks.
- Filter low-coder expert estimates where possible. V-Dem guidance is to
  discard cells with `_nr <= 3` before aggregation.
- Cite the exact V-Dem and V-Party releases used. Scores are recomputed between
  releases, so absolute values should not be compared across versions.

## Limitations

- Both variables are expert-coded, so shared expert-coding bias is possible.
- V-Dem and V-Party releases can have different temporal coverage; the merged
  analytical window should be defined by the loaded data after the join.
- Governing-party aggregation is a judgment call, especially in coalition
  governments.
- Fixed effects help with confounding, but the design is not a true experiment.

## Setup

### 1. Install uv

`uv` is the package manager this project uses. It also manages the Python interpreter,
so you don't need to install Python separately.

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal after installing so `uv` is on your `PATH`.

### 2. Install dependencies

```bash
uv sync --extra dev
```

This installs runtime dependencies plus dev tools (pytest, ruff, pre-commit). Add
`--extra analysis` too if you want the notebook/plotting stack (jupyter, plotly,
matplotlib, seaborn):

```bash
uv sync --extra dev --extra analysis
```

`uv` creates a `.venv` folder automatically. You don't need to activate it; just
prefix any command with `uv run` and it runs inside the right environment.

### 3. Register the git hooks

```bash
uv run pre-commit install
```

Run this once after cloning. It sets up automatic formatting checks on every `git commit`.
You don't need to run it again on future pulls.

---

## Tools

Python stack managed with [`uv`](https://github.com/astral-sh/uv); linting and
formatting with [`ruff`](https://docs.astral.sh/ruff/) via
[`pre-commit`](https://pre-commit.com/); dataframes with
[`polars`](https://pola.rs/).

### uv

`uv` pins exact package versions in `uv.lock` so everyone on the team gets the same
environment. When someone adds or updates a
dependency and pushes the updated lock file, the rest of the team just runs `uv sync`
again to get in sync.

```bash
uv sync --extra dev      # install / update all dependencies
uv run <command>         # run any command inside the project's virtual environment
uv add <package>         # add a new dependency (updates pyproject.toml + uv.lock)
```

### pre-commit + ruff

`pre-commit` runs checks automatically every time you `git commit`. This project
uses it to run `ruff` for linting and formatting. ruff is included in the dev
dependencies, so you don't need to install it separately.

**What happens on commit:**
- ruff checks your code for style issues and import ordering
- if it finds something fixable, it fixes the files in place and the commit is aborted
- you re-stage the fixed files (`git add`) and commit again; it should pass the second time
- if ruff finds something it can't fix, it prints the error and you fix it manually

To run the checks manually across all files without committing:

```bash
uv run pre-commit run --all-files
```

### pytest

`pytest` is the test runner. Tests live under `tests/`. Run it through `uv run` so it uses
the project's environment:

```bash
uv run pytest            # run all tests
uv run pytest -x         # stop on first failure
uv run pytest -k name    # run only tests whose name matches a pattern
```

---

## Layout

| Path          | Purpose                                              |
|---------------|------------------------------------------------------|
| `src/`        | Project source code                                  |
| `notebooks/`  | Jupyter notebooks for exploration and analysis       |
| `data/raw/`   | Local raw datasets (git-ignored)                     |
| `docs/`       | Design notes and documentation                       |
| `specs/`      | Feature specs                                         |
| `report/`     | Final report / write-up                              |
| `tests/`      | Test suite                                            |
