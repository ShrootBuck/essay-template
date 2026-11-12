# Essay Template

Edit [Essay.typ](Essay.typ) to write an essay. The variables at the top set the title, author, school, course, and date. The date defaults to today.

Write the essay inside the block containing `= Subheading`. Its headings and prose count toward the cover's word count. Add sources under **References**, with a blank line between entries for hanging indents.

## Build

Install the [Typst CLI](https://github.com/typst/typst#installation), then run:

```sh
./compile.sh
```

This generates [Essay.pdf](Essay.pdf). To rebuild as you write, run `typst watch Essay.typ`. You can also upload the single source file to the [Typst web app](https://typst.app/).

The template uses US Letter pages, one-inch margins, and 12-point Times New Roman. It falls back to Libertinus Serif when Times New Roman is unavailable. Page numbering starts on the first page of the essay.

## Optional pre-commit hook

Run `./setup-hooks.sh` to install the included hook locally. It rebuilds and stages the PDF before a commit.
