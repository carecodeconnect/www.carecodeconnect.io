## care-code-connect website

This repository contains the source for `www.carecodeconnect.io`, built with [Quarto](https://quarto.org).

The site is a Quarto website project configured in `_quarto.yml` and rendered to `docs/`.

## Runtime model (important)

The website uses two separate Python environments:

- **`mapmind` (Conda):** executes `projects/mapmind/*.qmd` (`jupyter: python3`)
- **Root `uv` / `.venv`:** executes pages that need the shared site stack (including `posts/in-praise-of-documentation/*.qmd` with `jupyter: python3` and `QUARTO_PYTHON` pointing at this interpreter).

Quarto CLI must be installed (`quarto --version`).

**Using uv from the repository root (recommended for `uv run quarto render`)**

1. From the repository root, create the virtual environment and install dependencies:

   ```bash
   uv sync
   ```

2. Point Quarto at that interpreter so Jupyter cells use the same packages as the `python3` kernel:

   ```bash
   export QUARTO_PYTHON="$PWD/.venv/bin/python"
   uv run quarto render
   ```

   Without `QUARTO_PYTHON`, Quarto may use a different Python than `.venv`, and you can see `ModuleNotFoundError` (for example `prettytable` on MapMind pages).

Dependencies are listed in the root `pyproject.toml`. The post bundle under `posts/in-praise-of-documentation/` also has its own `pyproject.toml` if you want a dedicated `uv` env for that bundle—then set `QUARTO_PYTHON` to that environment’s `python` when rendering those files. An optional Conda spec for MapMind alone remains in `projects/mapmind/conda-mapmind.yml`.

## Cross-platform setup (Linux/macOS)

### 1) Prerequisites

Install these first:

- Quarto CLI (`quarto --version`)
- Conda (Miniconda/Anaconda)
- `uv` (`uv --version`)

### 2) Create/update the MapMind Conda environment

From repository root:

```bash
conda env create -f projects/mapmind/conda-mapmind-portable.yml || \
conda env update -f projects/mapmind/conda-mapmind-portable.yml --prune
```

Then activate it:

```bash
conda activate mapmind
```

### 3) Optional: separate `uv` env for the “In Praise” bundle only

If you use `posts/in-praise-of-documentation/pyproject.toml` instead of only the root `uv sync`, install deps there and point Quarto at that interpreter when working on those files:

```bash
cd posts/in-praise-of-documentation
uv sync
export QUARTO_PYTHON="$PWD/.venv/bin/python"
cd ../..
```

### 4) Verify Jupyter kernels from the MapMind interpreter

```bash
conda run -n mapmind python -m jupyter kernelspec list
```

You should see at least `python3`. (Older setups sometimes used a custom kernel name; documents in this repo use `jupyter: python3` plus `QUARTO_PYTHON` so kernel paths do not go stale when directories move.)

## Preview and render

**Blog posts and other pages that use the root `.venv`** (recommended for `posts/in-praise-of-documentation/`):

```bash
export QUARTO_PYTHON="$PWD/.venv/bin/python"
quarto preview
```

**MapMind project pages** (`projects/mapmind/*.qmd`): use the MapMind Conda interpreter for Quarto/Jupyter discovery:

```bash
MAPMIND_PYTHON=$(conda run -n mapmind which python)
QUARTO_PYTHON="$MAPMIND_PYTHON" quarto check jupyter
QUARTO_PYTHON="$MAPMIND_PYTHON" quarto preview
```

Notes:

- `quarto preview` is incremental by default; it does not force a full rebuild.
- To force full render before preview:

```bash
QUARTO_PYTHON="$MAPMIND_PYTHON" quarto preview --render all
```

Or render once explicitly:

```bash
QUARTO_PYTHON="$MAPMIND_PYTHON" quarto render
```

## Deployment notes

- Production site is served from `docs/` on `main` (GitHub Pages).
- If you are only testing locally, you do not need to commit regenerated `docs/` output.
- If you intend to deploy content changes, run `quarto render` and include updated `docs/` in the commit.

## Environment files in this repo

- `projects/mapmind/conda-mapmind-portable.yml`: cross-platform environment spec for Linux/macOS (recommended).
- `projects/mapmind/conda-mapmind.yml`: historical platform-locked export (not recommended for cross-platform setup).
