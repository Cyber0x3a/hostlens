# Releasing

HostLens publishes to PyPI from a version tag

The trusted publisher is tied to `Cyber0x3a/hostlens` and `.github/workflows/workflow.yml`

No PyPI password or long-lived upload token is stored in GitHub

## Prepare the release

1. Choose the next version
2. Update `version` in `pyproject.toml`
3. Update `__version__` in `src/hostlens/__init__.py`
4. Add the release notes to `CHANGELOG.md`
5. Run every quality, package, and documentation check
6. Commit and push the release changes to `main`
7. Wait for the normal `main` workflow to pass

The two version strings must match

PyPI does not allow replacing an existing release file, so do not reuse a published version

## Build locally

```bash
python -m build
```

The command should create a source archive and a universal Python wheel under `dist/`

Inspect the names before tagging

```text
hostlens-X.Y.Z.tar.gz
hostlens-X.Y.Z-py3-none-any.whl
```

## Tag the release

Create an annotated tag from the tested commit

```bash
git tag -a vX.Y.Z -m "HostLens X.Y.Z"
git push origin vX.Y.Z
```

Tags beginning with `v` start the release workflow

The workflow runs formatting, linting, Pyright, tests on every supported Python version, and a package build before the publish job receives an OpenID Connect token

## Verify the release

Check the GitHub Actions run first

Then check the PyPI project page and install from PyPI in a fresh environment

```bash
python -m venv release-check
release-check/bin/python -m pip install hostlens==X.Y.Z
release-check/bin/python -c "import hostlens; print(hostlens.__version__)"
```

On Windows, use `release-check\Scripts\python.exe`

The imported file path should point inside the fresh environment, not the repository checkout

## Documentation deployment

Changes under `docs/`, `mkdocs.yml`, the docs dependency group, or the Pages workflow start `.github/workflows/docs.yml`

The workflow builds with `mkdocs build --strict` and sends the generated `site/` artifact to GitHub Pages

GitHub Pages must use GitHub Actions as its publishing source in the repository settings

The site URL is `https://cyber0x3a.github.io/hostlens/`

Documentation deployment and PyPI publishing are separate workflows, so a Pages failure cannot publish or alter a package release

## Failed publish

Read the failed job before creating another tag

If tests or the build failed, fix the repository and release a new version

If trusted publishing failed, confirm the owner, repository, workflow filename, and optional environment in PyPI

Do not move a tag after users may have fetched it
