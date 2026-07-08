## care-code-connect website

This repository contains the source for [`www.carecodeconnect.io`](https://www.carecodeconnect.io),
built with [Quarto](https://quarto.org).

The site is a Quarto website project configured in `_quarto.yml` and rendered to `docs/`
(served by GitHub Pages from `main`).

## Python environment

Pages that execute code (e.g. `posts/in-praise-of-documentation/`, `projects/mapmind/`)
use `jupyter: python3` and run against the project's root virtual environment `.venv`,
managed with [`uv`](https://docs.astral.sh/uv/). A single environment covers the whole
site.

Set up (or refresh) the environment from the repository root:

```bash
uv sync
```

## Render and preview

Point Quarto at the `.venv` interpreter with `QUARTO_PYTHON` so Jupyter cells use the
same packages as the `python3` kernel. This one command renders the **entire** site:

```bash
QUARTO_PYTHON="$PWD/.venv/bin/python" quarto render
```

Live preview with auto-reload:

```bash
QUARTO_PYTHON="$PWD/.venv/bin/python" quarto preview
```

Without `QUARTO_PYTHON`, Quarto may fall back to a different Python than `.venv` and
executable pages fail with `ModuleNotFoundError`. Equivalently, activate the venv first
(`source .venv/bin/activate`) and drop the prefix.

Dependencies are listed in the root `pyproject.toml`.

## Theming

- The HTML theme is configured in `_quarto.yml` under `format.html.theme`, split into
  `light:` (gruvbox light) and `dark:` (gruvbox dark) — Quarto adds the navbar
  light/dark toggle automatically.
- Custom styling lives in `theme.scss` (light) and `theme-dark.scss` (dark): serif prose
  (EB Garamond) with IBM Plex Mono for code, headings, and metadata.
- Web fonts load via `format.html.include-in-header`; code syntax highlighting uses the
  bundled `gruvbox-light` / `gruvbox-dark` styles (`format.html.highlight-style`).

## Deployment

- Production is served from `docs/` on `main` (GitHub Pages).
- For local-only testing you do not need to commit regenerated `docs/`.
- To deploy content changes, run `quarto render` and include the updated `docs/` in the commit.
