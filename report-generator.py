"""A small, general-purpose generator for reports.

Use write_report() from Python, or run this module with a JSON input file:

    python3 -m pip install reportlab
    python3 report_generator.py report.json report.pdf

A minimal report.json:

    {
      "title": "Workshop notes",
      "pages": [{
        "title": "Motor test",
        "metrics": [["12 V", "Supply voltage"]],
        "sections": [["Observation", "The shaft turned freely under load."]]
      }]
    }

Each page can have a descriptor, summary, metrics, sections, sources and
theme. Metrics use (value, label) pairs; sections use (heading, paragraph);
sources use (source title, URL). Set theme.columns to 1 or 2. Python callers
can also supply a function to draw a header motif.
All positions and sizes are in points (72 per inch) because US system is weird.

This system is pretty adaptable; maybe I'll build a plugin system one day.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 40
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN
GUTTER = 24
INK = HexColor("#22252A")
GRAY = HexColor("#60656A")
Pair = tuple[str, str]


@dataclass(frozen=True)
class Fonts:
    sans: str = "Helvetica"
    bold: str = "Helvetica-Bold"
    serif: str = "Times-Roman"
    serif_bold: str = "Times-Bold"


@dataclass(frozen=True)
class Palette:
    primary: Color
    accent: Color
    tint: Color


@dataclass(frozen=True)
class Theme:
    primary: str = "#284B63"
    accent: str = "#B36A41"
    columns: int = 1
    title_font: str | None = None
    title_x: float = MARGIN
    header_top: float = 727
    metrics_top: float = 607
    decorate: Callable[[Canvas, Palette], None] | None = None

    def palette(self) -> Palette:
        main = HexColor(self.primary)
        tint = Color(*(v * .07 + .93 for v in (main.red, main.green, main.blue)))
        return Palette(main, HexColor(self.accent), tint)


@dataclass(frozen=True)
class Page:
    title: str
    descriptor: str = ""
    summary: str = ""
    metrics: Sequence[Pair] = ()
    sections: Sequence[Pair] = ()
    sources: Sequence[Pair] = ()
    theme: Theme = field(default_factory=Theme)


@dataclass(frozen=True)
class Report:
    title: str
    pages: Sequence[Page]
    author: str = ""
    kicker: str = ""
    source_heading: str = "SOURCES"
    footer: str = ""


def rule(pdf, x1, y1, x2, y2, color, width=1):
    """Draw a line. Also available to custom header motifs."""
    pdf.setStrokeColor(color)
    pdf.setLineWidth(width)
    pdf.line(x1, y1, x2, y2)


def _label(pdf, x, y, text, font, size, color):
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, text)


def _paragraph(pdf, markup, x, top, width, font, size, leading, color=INK):
    """Draw a measured paragraph and return its bottom edge."""
    style = ParagraphStyle("body", fontName=font, fontSize=size,
                           leading=leading, textColor=color)
    paragraph = Paragraph(markup, style)
    _, height = paragraph.wrap(width, PAGE_HEIGHT + 8)
    paragraph.drawOn(pdf, x, top - height)
    return top - height


def _header(pdf, report, page, palette, fonts):
    theme = page.theme
    top, x = theme.header_top, theme.title_x
    pdf.setFillColor(white)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    pdf.setFillColor(palette.primary)
    if theme.decorate:
        theme.decorate(pdf, palette)

    if report.kicker:
        _label(pdf, x, top, report.kicker, fonts.bold, 8, GRAY)
    title_face = theme.title_font or (fonts.serif_bold if theme.columns == 1 else fonts.bold)
    title_size = 34 if len(page.title) < 15 else 28
    available = PAGE_WIDTH - MARGIN - x
    text_width = pdfmetrics.stringWidth(page.title, title_face, title_size)
    if text_width > available:
        title_size *= available / text_width
    _label(pdf, x, top - 43, page.title, title_face, title_size, palette.primary)
    if page.descriptor:
        pdf.setFont(fonts.sans, 9.2)
        pdf.setFillColor(INK)
        pdf.drawString(x, top - 65, page.descriptor)
    bottom = top - 65
    if page.summary:
        bottom = _paragraph(pdf, escape(page.summary), x, top - 77, min(430, available),
                            fonts.serif, 11.3, 14, palette.primary)
    return bottom


def _metrics(pdf, page, palette, fonts, header_bottom):
    """Lay out any number of metrics in equal-width cells."""
    top = min(page.theme.metrics_top, header_bottom - 14)
    if not page.metrics:
        return top + 9
    gap = 17
    count = len(page.metrics)
    width = (TEXT_WIDTH - 6 - gap * (count - 1)) / count
    if width < 40:
        raise ValueError(f"{page.title}: too many metrics for one row.")
    lowest = top
    for i, (value, label) in enumerate(page.metrics):
        x = MARGIN + i * (width + gap)
        color = palette.accent if i == 1 else palette.primary
        rule(pdf, x, top + 9, x + width, top + 9, color, 2)
        size = min(25, 25 * width / max(1, pdfmetrics.stringWidth(value, fonts.bold, 25)))
        _label(pdf, x, top - 21, value, fonts.bold, size, palette.primary)
        bottom = _paragraph(pdf, escape(label).replace("\n", "<br/>"), x, top - 31,
                            width + 3, fonts.sans, 8.8, 11.5, GRAY)
        lowest = min(lowest, bottom)
    return min(top - 79, lowest - 25)


def _sections(pdf, page, palette, fonts, top):
    """One row loop handles both the single-column and two-column templates."""
    columns = page.theme.columns
    width = (TEXT_WIDTH - GUTTER * (columns - 1)) / columns
    for first in range(0, len(page.sections), columns):
        bottoms = []
        for column, (heading, body) in enumerate(page.sections[first:first + columns]):
            x = MARGIN + column * (width + GUTTER)
            if columns == 1:
                if pdfmetrics.stringWidth(heading, fonts.bold, 10.7) <= width:
                    _label(pdf, x, top, heading, fonts.bold, 10.7, palette.primary)
                    body_top = top - 9
                else:
                    body_top = _paragraph(pdf, escape(heading), x, top + 11, width,
                                          fonts.bold, 10.7, 14, palette.primary) - 8
            else:
                body_top = _paragraph(pdf, escape(heading), x, top + 2, width,
                                      fonts.bold, 11.4, 14, palette.primary) - 8
            bottom = _paragraph(pdf, escape(body), x, body_top, width,
                                fonts.sans, 11.2, 15.5)
            bottoms.append(bottom)
        top = min(bottoms) - (17 if columns == 1 else 23)
    return top


def _sources(pdf, report, page, palette, fonts, body_bottom):
    if page.sources:
        # Expand the reserved area upward for a longer reference list
        top = max(130, 53 + 12.1 * len(page.sources))
        if body_bottom < top + 10:
            raise ValueError(f"{page.title}: sections run into the source list.")
        rule(pdf, MARGIN, top + 8, PAGE_WIDTH - MARGIN, top + 8, palette.primary, .7)
        _label(pdf, MARGIN, top - 5, report.source_heading, fonts.bold, 8, palette.primary)
        y = top - 14
        for i, (title, url) in enumerate(page.sources, 1):
            host = escape(urlsplit(url).netloc)
            link = (f'{i}. <link href={quoteattr(url)} color={quoteattr(page.theme.primary)}>'
                    f'{escape(title)}</link> <font color="#73777B">| {host}</font>')
            y = _paragraph(pdf, link, MARGIN, y, TEXT_WIDTH, fonts.sans, 8, 10.1) - 2
        if y < 41:
            raise ValueError(f"{page.title}: the source list is too long for one page.")
    elif body_bottom < 41:
        raise ValueError(f"{page.title}: sections are too long for one page.")
    if report.footer:
        _label(pdf, MARGIN, 32, report.footer, fonts.sans, 7, GRAY)


def write_report(output: str | Path, report: Report, *, fonts: Fonts = Fonts()) -> Path:
    """Write one Letter page per Page record; refuse content that won't fit."""
    if not report.pages:
        raise ValueError("A report needs at least one page.")
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = Canvas(str(path), pagesize=letter)
    pdf.setTitle(report.title)
    pdf.setAuthor(report.author)
    for page in report.pages:
        if page.theme.columns not in (1, 2):
            raise ValueError(f"{page.title}: choose one or two columns.")
        palette = page.theme.palette()
        header_bottom = _header(pdf, report, page, palette, fonts)
        top = _metrics(pdf, page, palette, fonts, header_bottom)
        bottom = _sections(pdf, page, palette, fonts, top)
        _sources(pdf, report, page, palette, fonts, bottom)
        pdf.showPage()
    pdf.save()
    return path


def main():
    parser = argparse.ArgumentParser(description="Render a JSON report to a Letter-size PDF.")
    parser.add_argument("input", type=Path, help="JSON report (see the module docstring).")
    parser.add_argument("output", type=Path, help="Destination PDF.")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    pages = [Page(**{**item, "theme": Theme(**item.get("theme", {}))}) for item in data["pages"]]
    report = Report(**{**data, "pages": pages})
    print(write_report(args.output, report))


if __name__ == "__main__":
    main()
