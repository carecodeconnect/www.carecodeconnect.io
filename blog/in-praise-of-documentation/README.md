# In Praise of Documentation (uv project)

This subproject uses `uv` and a dedicated Jupyter kernel named `pydata`.

## Setup

```bash
cd blog/in-praise-of-documentation
uv sync
uv run python -m ipykernel install --user --name pydata --display-name "Python (pydata)"
```

## Verify

```bash
python -m jupyter kernelspec list
```

You should see `pydata` in the kernels list.
