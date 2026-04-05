## care-code-connect website

This repository contains the source for `www.carecodeconnect.io`, built with [Quarto](https://quarto.org).

The site is a Quarto website project configured in `_quarto.yml` and rendered to `docs/`.

## Runtime model (important)

The website uses two separate Python environments:

- **`mapmind` (Conda):** executes `projects/mapmind/*.qmd` (`jupyter: python3`)
- **Root `uv` / `.venv`:** executes pages that need the shared site stack (including `posts/in-praise-of-documentation/*.qmd` when using the repo-wide environment and `jupyter: pydata`).

Quarto CLI must be installed (`quarto --version`).

**Using uv from the repository root (recommended for `uv run quarto render`)**

1. From the repository root, create the virtual environment and install dependencies:

   ```bash
   uv sync
   ```

2. Point Quarto at that interpreter so Jupyter cells use the same packages as your kernels declare (`python3`, `pydata`, etc.):

   ```bash
   export QUARTO_PYTHON="$PWD/.venv/bin/python"
   uv run quarto render
   ```

   Without `QUARTO_PYTHON`, Quarto may use a different Python than `.venv`, and you can see `ModuleNotFoundError` (for example `prettytable` on MapMind pages).

Dependencies are listed in the root `pyproject.toml`. The post bundle under `posts/in-praise-of-documentation/` also has its own `pyproject.toml` if you want a dedicated `uv` env and `pydata` kernel for that bundle only. An optional Conda spec for MapMind alone remains in `projects/mapmind/conda-mapmind.yml`.

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

### 3) Create the blog post `uv` environment and register `pydata` kernel (optional)

If you use the per-post project instead of only the root `uv sync`:

```bash
cd posts/in-praise-of-documentation
uv sync
uv run python -m ipykernel install --user --name pydata --display-name "Python (pydata)"
cd ../..
```

### 4) Verify Jupyter kernels from the MapMind interpreter

```bash
conda run -n mapmind python -m jupyter kernelspec list
```

You should see both:

- `python3`
- `pydata`

## Preview and render

Use MapMind Python for Quarto/Jupyter discovery:

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
