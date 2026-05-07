# Essay Template

A nice & fancy essay format I use for all of my school assignments.

## Format

This project uses Markdown with LaTeX formatting:

- **Source**: [`Essay.md`](Essay.md) — written in Markdown with YAML frontmatter for PDF generation
- **Output**: [`Essay.pdf`](Essay.pdf) — compiled academic paper
- **Compile**: Run `./compile.sh` to regenerate the PDF (requires pandoc and xelatex)

The paper includes word count markers that are automatically replaced during compilation:

```markdown
<!-- START_WORD_COUNT -->
...content...
<!-- END_WORD_COUNT -->
```

## Setup

After cloning, install the git hook to auto-compile on commit:

```bash
./setup-hooks.sh
```

This ensures the PDF is always up-to-date before pushing to Github. Feel free to ignore if not using version control.
