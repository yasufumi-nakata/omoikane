# Contributing

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Checks

```bash
python -m unittest discover -s tests -t .
python -m omoikane.cli demo --json
python -m omoikane.cli gap-report --json
python -m build
```

## Project Rules

- Treat `docs/`, `specs/`, `evals/`, and `src/` as one contract.
- Do not claim consciousness, identity continuity, or production readiness from reference-runtime outputs.
- Keep generated artifacts out of git unless they are explicitly named evidence fixtures.
- Add or update tests when changing `src/omoikane` behavior.

## Release Notes

Release tags must match `pyproject.toml` as `vMAJOR.MINOR.PATCH`. The existing package and release workflows verify the tag, build the wheel/sdist, and produce release assets.

