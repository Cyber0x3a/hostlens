# Contributing

Create a focused branch, add observable-behavior tests, and run

```bash
ruff check .
ruff format --check .
pyright
pytest
python -m build
```

Keep collection, parsing, fingerprinting, fusion, and presentation separate

Unit tests should not need network access
