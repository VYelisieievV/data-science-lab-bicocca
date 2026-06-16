# Data Science Lab — Bicocca (semester 2)

Data Science Lab project analysing the **V-Dem** and **V-Party** datasets.

Python stack managed with [`uv`](https://github.com/astral-sh/uv); linting/formatting
with [`ruff`](https://docs.astral.sh/ruff/) via [`pre-commit`](https://pre-commit.com/);
dataframes with [`polars`](https://pola.rs/).

---

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

`uv` creates a `.venv` folder automatically. You don't need to activate it — just prefix
any command with `uv run` and it runs inside the right environment.

### 3. Register the git hooks

```bash
uv run pre-commit install
```

Run this once after cloning. It sets up automatic formatting checks on every `git commit`.
You don't need to run it again on future pulls.

---

## Data

The **V-Dem** and **V-Party** datasets are not committed (they're large and regenerable).
Download the CSV/Stata releases from [v-dem.net](https://www.v-dem.net/data/the-v-dem-dataset/)
and place them under `data/raw/`. Read them with polars, e.g.:

```python
import polars as pl

vdem = pl.read_csv("data/raw/V-Dem-CY-Full+Others-v14.csv")
```

`data/raw/` is git-ignored — keep raw downloads local.

---

## Tools

### uv

`uv` pins exact package versions in `uv.lock` so everyone on the team gets the same
environment — no "works on my machine" surprises. When someone adds or updates a
dependency and pushes the updated lock file, the rest of the team just runs `uv sync`
again to get in sync.

```bash
uv sync --extra dev      # install / update all dependencies
uv run <command>         # run any command inside the project's virtual environment
uv add <package>         # add a new dependency (updates pyproject.toml + uv.lock)
```

### pre-commit + ruff

`pre-commit` runs checks automatically every time you `git commit`. This project uses it
to run `ruff` for linting and formatting. ruff is included in the dev dependencies, so you
don't need to install it separately.

**What happens on commit:**
- ruff checks your code for style issues and import ordering
- if it finds something fixable, it fixes the files in place and the commit is aborted
- you re-stage the fixed files (`git add`) and commit again — it should pass the second time
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
