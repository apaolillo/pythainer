# Releasing pythainer

This document records the exact steps to publish a new release of pythainer.

Prereqs:
- You have push access to the repo and the PyPI project.
- `CHANGELOG.md` follows Keep a Changelog and Semantic Versioning.
- Version in `pyproject.toml` is maintained manually (PEP 440).
- CI is green on `main`.

Versioning Tag format: `v0.X.Y`

Date format: `YYYY-MM-DD`.

---

## 1) Prepare the release

1. Pick the version number `0.X.Y`.

2. Update `CHANGELOG.md`:
   - Add a new section `## [0.X.Y] - YYYY-MM-DD` under `[Unreleased]`.
   - Move curated changes from `[Unreleased]` into `0.X.Y`.

3. Bump the version in `pyproject.toml`:
   ```toml
   [project]
   version = "0.X.Y"
    ```

4. Sanity checks locally:

   ```bash
   ./scripts/all_checks.sh
   pytest -q
   git clean -ndx
   git status
   ```

5. Create a short-lived release branch and commit:
    ```bash
    git checkout -b release
    git add -u
    git commit -s -m "Release 0.X.Y"
    git push -u origin release
    ```

6. Open the corresponding PR on GitHub. When CI is green, merge.

---

## 2) Tag the release

After the PR is merged:

```bash
git checkout main
git pull --prune
git tag -a "v0.X.Y" -m "Release v0.X.Y"
git push origin v0.X.Y
```

---

## 3) Build artifacts locally

Use a fresh clone and venv to avoid leaking deps:

```bash
git clone https://github.com/apaolillo/pythainer.git
cd pythainer/
python3 -m venv .venv-release
. .venv-release/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build twine
python3 -m build          # creates dist/*.whl and dist/*.tar.gz
python3 -m twine check dist/*
```

Quick inspection:

* Confirm wheel exists (preferably `py3-none-any.whl` for pure Python).
* Confirm tarball contains only expected files.

---

## 4) Publish to PyPI

```bash
# still in the .venv-release
python3 -m twine upload dist/*
```

You will need a `~/.pypirc` or to paste your `__token__` API token when prompted.

---

## 5) Verify the release

* PyPI page: [https://pypi.org/project/pythainer/](https://pypi.org/project/pythainer/)
* Clean venv install:

  ```bash
  python3 -m venv /tmp/venv-verify && . /tmp/venv-verify/bin/activate
  pip install -U pip
  pip install pythainer==0.X.Y
  pythainer --help
  deactivate
  ```
* Check that README renders correctly on PyPI.
* Profit.
