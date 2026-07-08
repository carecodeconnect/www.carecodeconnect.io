# carecodeconnect.io

Quarto website. Source is `.qmd`; rendered HTML goes to `docs/` (served by GitHub Pages).

## Rendering the whole site

Several pages (e.g. `posts/in-praise-of-documentation/`, `projects/mapmind/`) run Python
via `jupyter: python3` and need the project's single root `.venv` (polars, great_tables,
prettytable, pyyaml, …). A separate Conda `mapmind` env was used historically but is no
longer required — everything builds against `.venv`. If the venv isn't used,
`quarto render` falls back to system Python and fails with
`ModuleNotFoundError: No module named 'yaml'`.

Render the entire site in one command by pointing Quarto at the venv's Python —
no `source .venv/bin/activate` needed:

```bash
QUARTO_PYTHON=$PWD/.venv/bin/python quarto render
```

Equivalently, activate first: `source .venv/bin/activate && quarto render`.

Preview locally with live reload:

```bash
QUARTO_PYTHON=$PWD/.venv/bin/python quarto preview
```

## Theming

- HTML theme is configured in `_quarto.yml` under `format.html.theme`.
- Custom styling lives in `theme.scss` (Sass, layered on a Bootswatch base).
  It has `/*-- scss:defaults --*/` (Sass variables) and `/*-- scss:rules --*/`
  (plain CSS) sections.
- Web fonts are loaded via `format.html.include-in-header` in `_quarto.yml`
  (`$web-font-path` in the SCSS is not reliably honored — use the header link).
