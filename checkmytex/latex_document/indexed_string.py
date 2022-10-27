import typing
import unittest
from bisect import bisect, bisect_left

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

    def serialize(self) -> typing.Dict:
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

    def __init__(self, text: typing.Union[str, TraceableString]):
        self.text = text
        self._content = text if isinstance(text, str) else str(text)  # string version
        self._index = compute_row_index(self._content)

    def get_detailed_position(
        self, i: typing.Union[TextPosition, typing.Tuple[int, int], int]
    ) -> TextPosition:
        if isinstance(i, TextPosition):
            if i.index is not None:
                return self.get_detailed_position(i.index)
            elif i.line is not None and i.line_offset is not None:
                return self.get_detailed_position((i.line, i.line_offset))
            else:
                raise ValueError(f"Position {i} insufficiently defined.")
        if isinstance(i, int):
            i = min(i, len(self._content))
            line = bisect(self._index, i) - 1
            line_offset = i - self._index[line]
            return TextPosition(i, line, line_offset)
        else:
            if i[0] >= self.num_lines():
                return self.get_detailed_position(len(self._content))
            return TextPosition(self._index[i[0]] + i[1], i[0], i[1])

    def num_lines(self):
        return len(self._index)

    def get_line(self, i) -> typing.Union[str, TraceableString]:
        begin = self.get_detailed_position((i, 0)).index
        end = self.get_detailed_position((i + 1, 0)).index
        return self[begin:end]

    def __str__(self):
        return self._content

    def __getitem__(self, item):
        return self.text[item]


def simplify_text_range(
    positions: typing.Iterable[typing.Optional[TextPosition]],
) -> typing.Optional[typing.Tuple[TextPosition, TextPosition]]:
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


class IndexedStringTest(unittest.TestCase):
    def test_1(self):
        text = "123\n456\n789"
        inds = IndexedText(text)
        self.assertEqual(inds._index, [0, 4, 8])

        def to_tuple(pos):
            return pos.line, pos.line_offset

        self.assertEqual(to_tuple(inds.get_detailed_position(0)), (0, 0))
        self.assertEqual(to_tuple(inds.get_detailed_position(2)), (0, 2))
        self.assertEqual(to_tuple(inds.get_detailed_position(4)), (1, 0))
        self.assertEqual(to_tuple(inds.get_detailed_position(5)), (1, 1))
        self.assertEqual(to_tuple(inds.get_detailed_position(8)), (2, 0))
        self.assertEqual(to_tuple(inds.get_detailed_position(9)), (2, 1))

    def test_2(self):
        text = "123\n456\n789"
        inds = IndexedText(text)
        self.assertEqual(inds.get_line(0), "123\n")
        self.assertEqual(inds.get_line(1), "456\n")
        self.assertEqual(inds.get_line(2), "789")
