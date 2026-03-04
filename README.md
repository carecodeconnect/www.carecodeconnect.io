## care-code-connect website

This repository contains the source for `www.carecodeconnect.io`, built with [Quarto](https://quarto.org).

The site is a Quarto website project configured in `_quarto.yml` and rendered to `docs/`.

## Runtime model (important)

The website uses two separate Python environments:

- `mapmind` (Conda): executes `projects/mapmind/*.qmd` (`jupyter: python3`)
- `pydata` (uv): executes `blog/in-praise-of-documentation/docs/*.qmd` (`jupyter: pydata`)

This separation is intentional.

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

### 3) Create the blog uv environment and register `pydata` kernel

```bash
cd blog/in-praise-of-documentation
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
