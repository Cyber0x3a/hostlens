# Contributing

Start with the [developer setup guide](https://cyber0x3a.github.io/hostlens/development/setup/)

Create a focused branch, add tests for observable behavior, and run

```bash
ruff check .
ruff format --check .
pyright
pytest
python -m build
python -m mkdocs build --strict
```

Keep collection, parsing, fingerprinting, fusion, and presentation separate

Unit tests should not need network access

The [architecture guide](https://cyber0x3a.github.io/hostlens/development/architecture/)
explains the module boundaries
