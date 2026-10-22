"""Minimal HTML table extraction for www.maitabi.jp detail pages (stdlib only).

The detail page carries the tour record itself in an embedded JSON literal and
only three things in tables: the itinerary, the travel conditions, and the
departure/price matrix. This module does the table half — markup in, cells out —
so the parsers can key on Japanese column headers instead of DOM positions.

Deliberately not a general HTML library: it captures the outermost tables of a
page, nothing else.
"""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import override


@dataclass
class Cell:
    """One <td>/<th>: its text, plus the <span> texts and <a href>s inside it."""

    tag: str
    text: str
    spans: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def clean(self) -> str:
        """Whitespace-collapsed text."""
        return re.sub(r"\s+", " ", self.text).strip()


@dataclass
class Table:
    """A table as header rows plus body rows of cells."""

    headers: list[list[Cell]]
    rows: list[list[Cell]]

    @property
    def header_names(self) -> list[str]:
        return [cell.clean() for cell in (self.headers[0] if self.headers else [])]

    def column(self, name: str) -> int | None:
        """Index of a column by its header text, or None when absent."""
        names = self.header_names
        return names.index(name) if name in names else None

    def cell(self, row: list[Cell], name: str) -> Cell | None:
        """The cell under column `name` in `row`, or None when absent/short."""
        index = self.column(name)
        if index is None or index >= len(row):
            return None
        return row[index]


class _TableParser(HTMLParser):
    """Collect every outermost <table> as a `Table`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[Table] = []
        self._depth = 0
        self._in_thead = False
        self._headers: list[list[Cell]] = []
        self._rows: list[list[Cell]] = []
        self._row: list[Cell] | None = None
        self._cell_tag: str | None = None
        self._cell_parts: list[str] = []
        self._cell_spans: list[str] = []
        self._cell_links: list[str] = []
        self._span_parts: list[str] | None = None

    @override
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Route self-closing tags through the normal start handling."""
        self.handle_starttag(tag, attrs)

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self._headers, self._rows = [], []
            return
        if self._depth != 1:
            return
        if tag == "thead":
            self._in_thead = True
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell_tag = tag
            self._cell_parts, self._cell_spans, self._cell_links = [], [], []
        elif tag == "br" and self._cell_tag is not None:
            self._cell_parts.append("\n")
        elif tag == "span" and self._cell_tag is not None:
            self._span_parts = []
        elif tag == "a" and self._cell_tag is not None:
            href = dict(attrs).get("href")
            if href is not None:
                self._cell_links.append(href)

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._flush_row()
            self._depth = max(0, self._depth - 1)
            if self._depth == 0:
                self.tables.append(Table(self._headers, self._rows))
            return
        if self._depth != 1:
            return
        if tag == "thead":
            self._flush_row()
            self._in_thead = False
        elif tag in ("td", "th") and self._cell_tag is not None:
            cell = Cell(
                tag=self._cell_tag,
                text="".join(self._cell_parts),
                spans=[" ".join(part.split()) for part in self._cell_spans if "".join(part.split())],
                links=list(self._cell_links),
            )
            if self._row is None:
                self._row = []
            self._row.append(cell)
            self._cell_tag = None
            self._span_parts = None
        elif tag == "tr":
            self._flush_row()
        elif tag == "span" and self._span_parts is not None:
            text = "".join(self._span_parts)
            self._cell_spans.append(text)
            self._span_parts = None

    def _flush_row(self) -> None:
        """Commit the row under construction (pages omit </tr> more than once)."""
        if self._row is None:
            return
        if self._row:
            (self._headers if self._in_thead else self._rows).append(self._row)
        self._row = None

    @override
    def handle_data(self, data: str) -> None:
        if self._cell_tag is None:
            return
        self._cell_parts.append(data)
        if self._span_parts is not None:
            self._span_parts.append(data)


def extract_tables(html: str) -> list[Table]:
    """All outermost tables of `html`, in document order."""
    parser = _TableParser()
    parser.feed(html)
    parser.close()
    return parser.tables


def find_table(tables: list[Table], *header_names: str) -> Table | None:
    """First table whose header row contains every given name."""
    for table in tables:
        names = table.header_names
        if all(name in names for name in header_names):
            return table
    return None


def find_key_value_table(tables: list[Table], *labels: str) -> Table | None:
    """First table containing rows that start with every given <th> label."""
    for table in tables:
        seen = {row[0].clean() for row in table.rows if len(row) >= 2 and row[0].tag == "th"}
        if all(label in seen for label in labels):
            return table
    return None
