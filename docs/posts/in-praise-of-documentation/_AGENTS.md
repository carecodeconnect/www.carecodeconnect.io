# AGENTS.md

This folder is a **self-contained bundle** for the “In Praise of Documentation” blog post and related slides.

## Layout

- `index.qmd` — long-form post (listed on the site Blog page)
- `slides/presentation.qmd` — RevealJS slide deck
- `data/` — Ngram CSV/JSON for executed code
- `images/` — figures and static images shared by the post and slides
- `refs.bib` / `refs.yaml` — bibliographies (Pandoc / Typst)
- `pyproject.toml` — Python dependencies (use `uv` from this directory)

## Render

From the **website repository root**:

```bash
quarto render
```

To render only this post:

```bash
quarto render posts/in-praise-of-documentation/index.qmd
```

To render only the slides:

```bash
quarto render posts/in-praise-of-documentation/slides/presentation.qmd
```

## Environment

Create or reuse a virtualenv in this folder (e.g. `uv sync`); register its Jupyter kernel as `pydata` if you use that name in the `.qmd` files.

For standalone Typst/PDF experiments, use `refs.yaml` in this bundle and render from the project root as needed.
