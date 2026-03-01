# AGENTS.md

This is the repository for a presentation on documentation in data science and software engineering.

## Project setup

- Use the `docs` folder to store all presentation-related source code

- Store all images in the `docs/images` folder because Typst requires the images to be accessible from its root folder (`docs`)

- Use `uv` for Python environment and package management

- Use [Quarto](https://quarto.org/docs/guide/) to create a PDF of the script for the presentation.

To render the PDF, use:

```
quarto render docs/talk.qmd
```

## Project files

- `docs/talk_script.qmd` is the written text of the talk

- `docs/presentation.qmd` is the slide deck for the talk