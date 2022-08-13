import typing
import unittest
from bisect import bisect_left,bisect

from flachtex import TraceableString
from flachtex.utils import compute_row_index


class IndexedString:
    def __init__(self, text: typing.Union[str, TraceableString]):
        self.text = text
        self.content = text if isinstance(text, str) else str(text)
        self._index = compute_row_index(self.content)

    def get_position(self, line: int, offset: int):
        return self._index[line] + offset

    def get_line_and_offset(self, pos: int):
        line = bisect(self._index, pos)-1
        offset = pos-self._index[line]
        return (line, offset)

    def to_position(self, lo_or_pos: typing.Union[typing.Tuple[int, int], int]):
        if isinstance(lo_or_pos, int):
            return lo_or_pos
        return self.get_position(lo_or_pos[0], lo_or_pos[1])

    def __str__(self):
        return self.content

    def __getitem__(self, item):
        return self.text[item]


class IndexedStringTest(unittest.TestCase):
    def test_1(self):
        text = "123\n456\n789"
        inds = IndexedString(text)
        self.assertEqual(inds._index, [0, 4, 8])
        self.assertEqual(inds.get_line_and_offset(0), (0, 0))
        self.assertEqual(inds.get_line_and_offset(2), (0, 2))
        self.assertEqual(inds.get_line_and_offset(4), (1, 0))
        self.assertEqual(inds.get_line_and_offset(5), (1, 1))
        self.assertEqual(inds.get_line_and_offset(8), (2, 0))
        self.assertEqual(inds.get_line_and_offset(9), (2, 1))