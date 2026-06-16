This file provides guidance to AI agents when working with code in this repository.

---

## Intended tooling

Python stack managed with `uv`.

```bash
uv sync --extra dev                  # install deps from lock file
uv run pre-commit install            # install git hooks (once after clone)
uv run pre-commit run --all-files    # lint/format manually
uv run pytest                        # run tests
```

Pre-commit runs `ruff --fix` + `ruff-format`.

---

## Key constraints

- All `rm` commands are blocked by a pre-tool hook (`.claude/hooks/block_dangerous_commands.sh`).
- Never read `.env`, `secrets/`, `*credential*`, `*.pem`, `*.key` — denied in agent settings.
