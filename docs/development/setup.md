# Development setup

## Clone and install

```bash
git clone https://github.com/Cyber0x3a/hostlens.git
cd hostlens
python -m venv .venv
```

Activate the environment

=== "Windows PowerShell"

    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```

=== "Linux and macOS"

    ```bash
    source .venv/bin/activate
    ```

Install the package and development tools

```bash
python -m pip install -e ".[dev,docs]"
```

Editable installation means imports use the code in `src/hostlens`

## Run the checks

```bash
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pytest
python -m build
python -m mkdocs build --strict
```

These match the checks used by GitHub Actions, apart from the Python version matrix

## Pre-commit

Install the repository hooks if you want Ruff to run before each commit

```bash
pre-commit install
pre-commit run --all-files
```

The hook runs Ruff lint fixes and Ruff formatting

Pyright, tests, package builds, and documentation builds remain explicit commands

## Preview the docs

```bash
python -m mkdocs serve
```

Open `http://127.0.0.1:8000`

The generated `site/` directory is ignored and should not be committed

## Run an example

Examples make real network requests

Use only a network you own or have permission to scan

```bash
python examples/identify.py
python examples/discover.py
python examples/scan.py
python examples/passive.py
```

The example addresses are placeholders, so edit them for the test network

## Working agreement

Keep changes focused and keep protocol I/O separate from parsing and identity decisions

Normal unit tests must work without a live network

Add a dependency only when the standard library and installed dependencies cannot do the job clearly

Do not configure an application's root logger from library code
