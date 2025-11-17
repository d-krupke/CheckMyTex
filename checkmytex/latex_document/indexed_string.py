import typing
from bisect import bisect

from flachtex import TraceableString
from flachtex.utils import compute_row_index


class TextPosition:
    """
    Position in a multi-line text.
    """

    def __init__(self, index: int, line: int, line_offset: int):
        self.index = index
        self.line = line
        self.line_offset = line_offset

    def serialize(self) -> dict:
        return {"index": self.index, "line": self.line, "line_offset": self.line_offset}

    def __eq__(self, other):
        # line and line offset should depend on the position.
        return self.index == other.index

    def __lt__(self, other):
        # line and line offset should depend on the position.
        return self.index < other.index

    def __le__(self, other):
        return self.index <= other.index

    def virtual_next(self):
        return TextPosition(
            self.index + 1 if self.index is not None else None,
            self.line,
            self.line_offset + 1 if self.line_offset is not None else None,
        )

    def __repr__(self):
        return f"[{self.index}:{self.line}:{self.line_offset}]"


class IndexedText:
    """
    An indexed text allows you to get better position information.
    """

    def __init__(self, text: str | TraceableString):
        self.text = text
        self._content = text if isinstance(text, str) else str(text)  # string version
        self._index = compute_row_index(self._content)

    def get_detailed_position(
        self, i: TextPosition | tuple[int, int] | int
    ) -> TextPosition:
        if isinstance(i, TextPosition):
            if i.index is not None:
                return self.get_detailed_position(i.index)
            if i.line is not None and i.line_offset is not None:
                return self.get_detailed_position((i.line, i.line_offset))
            msg = f"Position {i} insufficiently defined."
            raise ValueError(msg)
        if isinstance(i, int):
            i = min(i, len(self._content))
            line = bisect(self._index, i) - 1
            line_offset = i - self._index[line]
            return TextPosition(i, line, line_offset)
        if i[0] >= self.num_lines():
            return self.get_detailed_position(len(self._content))
        return TextPosition(self._index[i[0]] + i[1], i[0], i[1])

    def num_lines(self):
        return len(self._index)

    def get_line(self, i) -> str | TraceableString:
        begin = self.get_detailed_position((i, 0)).index
        end = self.get_detailed_position((i + 1, 0)).index
        return self[begin:end]

    def __str__(self):
        return self._content

    def __getitem__(self, item):
        return self.text[item]


def simplify_text_range(
    positions: typing.Iterable[TextPosition | None],
) -> tuple[TextPosition, TextPosition] | None:
    """
    Returns a simple, single-line range based on a list of positions.
    This means, that it can be shortened.
    :param positions: An iterable of inclusive text positions.
    :return: A range that contains a part of the input. The end is exclusive.
    """
    positions_ = [p for p in positions if p is not None]  # remove potential nones
    if not positions_:
        return None
    max_line = max(p.line for p in positions_)
    last_line = [p for p in positions_ if p.line == max_line]
    if len(last_line) == 1:
        if len([p for p in positions_ if p.line == max_line - 1]) <= 1:
            return last_line[0], last_line[0].virtual_next()
        # use the line before, which is longer
        last_line = [p for p in positions_ if p.line == max_line - 1]
    return min(last_line), max(last_line).virtual_next()
