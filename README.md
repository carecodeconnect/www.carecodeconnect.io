## care-code-connect website

This repository contains the source for the `www.carecodeconnect.io` website, built with [Quarto](https://quarto.org) and deployed via GitHub Pages.

The project is a Quarto **website project** with its main configuration in `_quarto.yml`. The site is rendered to the `docs/` directory, which GitHub Pages serves from the `main` branch.

---

### Prerequisites

- Quarto CLI installed (`quarto --version` should work).
- A working Python environment for pages that execute Python code (e.g. a Conda `mapmind` environment built with the `projects/mapmind/conda-mapmind.yml` setup).
- You can recreate the full MapMind analysis environment from:

- `projects/mapmind/conda-mapmind.yml` (Conda environment file).

---

### Local development workflow

From the project root (this directory):

1. **Preview the site locally (with live reload)**

   ```bash
   quarto preview
   ```

   - Quarto builds the site into `docs/` and starts a local web server (typically at `http://localhost:4200`).
   - Edit any `.qmd` file (`index.qmd`, `about.qmd`, `projects.qmd`, `blog.qmd`, etc.) and the preview will update automatically.

2. **Stop the preview**

   - Press `Ctrl+C` in the terminal running `quarto preview`.

---

### Building the site

To produce the static site into `docs/` (without starting a server), run:

```bash
quarto render
```

This:

- Reads `_quarto.yml` and all `.qmd` files.
- Renders the website into the `docs/` directory.
- Regenerates HTML pages such as:
  - `docs/index.html`
  - `docs/about.html`
  - `docs/projects.html`
  - `docs/blog.html`
  - `docs/testimonials.html`

**Note:** The old `_site/` output directory is no longer used. The live site is served entirely from `docs/`.

---

### Deployment via GitHub Pages

Deployment is handled by GitHub Pages using the `docs/` folder on the `main` branch.

In the GitHub repository settings:

- Go to **Settings → Pages**.
- Under **Source**, select:
  - **Branch**: `main`
  - **Folder**: `/docs`

When you push changes to `main` (including the updated `docs/`), GitHub Pages automatically deploys the new version of the site.

---

### Typical workflow for updating the website

1. **Edit content**

   - Modify one or more of the source files, for example:
     - `index.qmd` (landing page)
     - `about.qmd`
     - `projects.qmd`
     - `testimonials.qmd`
     - `blog.qmd` (blog listing)
     - Files under `blog/` (individual blog posts)
     - Assets under `projects/...` (project-specific images and HTML artifacts)

2. **Preview locally (optional, recommended)**

   ```bash
   quarto preview
   ```

   - Verify that pages render correctly and that navigation, images, and links behave as expected.

3. **Render the site**

   ```bash
   quarto render
   ```

   - This updates the contents of the `docs/` directory based on the latest source files.

4. **Commit your changes**

   Add both the **source** and the **generated site**:

   ```bash
   git add \
     _quarto.yml \
     *.qmd \
     blog/ \
     projects/ \
     docs/

   git commit -m "Update site content"
   ```

   - Adjust the paths in `git add` as needed for the files you actually changed.

5. **Push to GitHub**

   ```bash
   git push
   ```

   - Pushing to `main` updates the `docs/` folder on GitHub.
   - GitHub Pages detects the change and redeploys the site.

6. **Verify deployment**

   - Visit `https://www.carecodeconnect.io` (or the repository’s Pages URL) after a short delay.
   - Confirm that your changes (including new content and blog posts) are visible.

---

### Notes and conventions

- **Do not commit `_site/`**: the site is now built into `docs/` only. If `_site/` is created locally, it can be safely ignored or deleted.
- **Images and assets**:
  - Project images live under `projects/...` and are referenced from `.qmd` files using relative paths like `projects/dengai/scatter-cases-time.png`.
  - MapMind images live under `projects/mapmind/images/`.
- **Blog**:
  - The blog listing page is `blog.qmd`.
  - Individual posts live under `blog/` as `.qmd` files.
  - New posts are automatically included in the listing when rendered.

