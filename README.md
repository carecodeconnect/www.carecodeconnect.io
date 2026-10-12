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
  `light:` and `dark:` — Quarto adds the navbar light/dark toggle automatically.
- Custom styling lives in `theme-minimal.scss` (light) and `theme-minimal-dark.scss`
  (dark), layered on Quarto's `default` base; Inter for prose, with
  `github` / `github-dark` syntax highlighting. The older gruvbox `theme.scss` and
  `theme-dark.scss` are kept but no longer referenced.
- Web fonts load via `format.html.include-in-header` (`$web-font-path` in the SCSS is
  not reliably honoured — use the header link).
- The compiled theme lands in `docs/site_libs/` under a content-hashed filename, so a
  theme change produces new `bootstrap-*.min.css` files. **They must be committed**, or
  every page links to a stylesheet that is not on the server and the site renders
  unstyled.

## Deployment

**A push to `main` is the deploy.** There is no GitHub Actions workflow and no build step
between the commit and production: Pages serves `docs/` from `main` directly, so whatever
is in `docs/` when you push is live within a minute.

- Render before committing, and include the updated `docs/` in the commit.
- For local-only testing you do not need to commit regenerated `docs/`.
- Do not push rendered output for a page that is not ready to be public — there is
  nothing between the push and the live site.

## What gets published

`project.render` in `_quarto.yml` is a **positive** list (`*.qmd` plus the `posts/` and
`projects/` trees). Quarto's default sweeps up every `.md` in the project, which had been
publishing the repo's own notes at `/CLAUDE.html` and an image-credits file at
`/projects/ai-data-job-skills/images/external/SOURCES.html`. Excluding them with
`"!CLAUDE.md"` does not work in Quarto 1.8 — the entry is accepted and ignored — hence the
positive list. **A new page must be `.qmd`, or be added to that list.**
