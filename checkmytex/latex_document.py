import re
import typing
import unittest

import flachtex
from flachtex import FileFinder
from yalafi.tex2txt import Options, tex2txt

from flachtex.rules import RegexSkipRule, Range, BASIC_SKIP_RULES

def _compute_row_index(content: str)->typing.List[int]:
    index = [0]
    i = content.find("\n")
    while i>=0:
        index.append(i+1)
        i = content.find("\n",i+1)
    return index

class IgnoreRule(RegexSkipRule):
    def __init__(self):
        super().__init__(r"((^\s*%%PAUSE-CHECKING)(?P<skipped_part>.*?)(^\s*%%CONTINUE-CHECKING))")

    def determine_skip(self, match: re.Match):
        span_to_be_skipped = Range(match.start("skipped_part"), match.end("skipped_part"))
        return span_to_be_skipped


class Origin:
    class Position:
        def __init__(self, pos, row, col):
            self.pos = pos
            self.row = row
            self.col = col

        def __eq__(self, other):
            return self.pos == other.pos and self.row == other.row and self.col == other.col

        def __lt__(self, other):
            return self.pos < other.pos

    def __init__(self, file: str, begin: Position, end: Position):
        self.file: str = file
        self.begin: Origin.Position = begin
        self.end: Origin.Position = end
        assert begin != end, "This would be empty"

    def __repr__(self):
        return f"{self.file}[{self.begin.pos}:{self.begin.row}:{self.begin.col}-{self.end.pos}:{self.end.row}:{self.end.col}]"

    def __eq__(self, other):
        return self.file == other.file and self.begin == other.begin and self.end == other.end


class LatexDocument:
    def __init__(self):
        self._source: flachtex.TraceableString = None
        self._sources_row_indices = {}
        self._files = None
        self._detex = None
        self._detex_charmap = None
        self._detex_line_index = None

    def parse(self, path: str, detex=True, file_finder=None):
        flat_source, sources = flachtex.expand_file_and_attach_sources(path,
                                                                       skip_rules=BASIC_SKIP_RULES + [IgnoreRule()],
                                                                       file_finder=file_finder)
        self._source = flachtex.remove_comments(flat_source)
        self._files = sources
        if detex:
            opts = Options()
            self._detex, self._detex_charmap = tex2txt(str(self._source), opts)
            self._detex_line_index = _compute_row_index(self._detex)

    def files(self) -> typing.Iterable[str]:
        for f in self._files.keys():
            yield f



    def get_source(self) -> str:
        return str(self._source)

    def get_text(self) -> str:
        if not self._detex:
            raise ValueError("No detex available!")
        return self._detex

    def get_file_content(self, path: str) -> str:
        return self._files[path]["content"]

    def get_origin_of_text(self, begin, end) -> Origin:
        if isinstance(begin, tuple):
            begin = self._detex_line_index[begin[0]] + begin[1]
            end = self._detex_line_index[end[0]] + end[1]
        end -= 1
        b = self._detex_charmap[begin] - 1
        e = self._detex_charmap[end] - 1
        if b == e:
            e += 1
        return self.get_origin_of_source(b, e)

    def _create_origin(self, path, begin: int, end: int) -> Origin:
        if path not in self._sources_row_indices:
            self._sources_row_indices[path] = _compute_row_index(self.get_file_content(path))
        row_index = self._sources_row_indices[path]
        row_begin = 0
        while row_begin + 1 < len(row_index) and begin >= row_index[row_begin + 1]:
            row_begin += 1
        # row_begin -= 1
        assert row_begin >= 0
        col_begin = begin - row_index[row_begin]
        assert col_begin >= 0
        row_end = row_begin
        while row_end + 1 < len(row_index) and end >= row_index[row_end + 1]:
            row_end += 1
        # row_end -= 1
        assert row_end >= row_begin
        col_end = end - row_index[row_end]
        assert col_end >= 0
        return Origin(file=path,
                      begin=Origin.Position(begin, row_begin, col_begin),
                      end=Origin.Position(end, row_end, col_end))

    def get_origin_of_source(self,
                             begin: typing.Union[int, typing.Tuple[int, int]],
                             end: typing.Union[int, typing.Tuple[int, int]]) -> Origin:
        if isinstance(begin, int):
            begin = (0, begin)
            end = (0, end)
        assert begin < end
        origin_begin = self._source.get_origin_of_line(begin[0], begin[1])
        origin_end = self._source.get_origin_of_line(end[0], end[1])
        # if not same file, reduce range. Worst case: begin=end-1
        while origin_begin[0] != origin_end[0]:
            end = (end[0], end[1] - 1)
            origin_end = self._source.get_origin_of_line(end[0], end[1] - 1)
        return self._create_origin(origin_begin[0], origin_begin[1], origin_end[1])


class LatexDocumentTest(unittest.TestCase):
    def test_1(self):
        sources = {
            "/main.tex": "0123\n\tBCD\nXYZ\n"
        }
        document = LatexDocument()
        document.parse("/main.tex", file_finder=FileFinder("/", "/main.tex", sources))
        self.assertEqual(document.get_source(), sources["/main.tex"])
        self.assertEqual(document.get_text(), sources["/main.tex"])
        for i in range(4):
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin("/main.tex", Origin.Position(i, 0, i), Origin.Position(i + 1, 0, i + 1))
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)
        for i in range(5, 8):
            j = i - 5
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin("/main.tex", Origin.Position(i, 1, j), Origin.Position(i + 1, 1, j + 1))
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)

    def test_2(self):

        sources = {
            "/main.tex": "0123\n\\input{sub.tex}\nXYZ\n",
            "/sub.tex":"ABC\n"
        }
        document = LatexDocument()
        document.parse("/main.tex", file_finder=FileFinder("/", "/main.tex", sources))
        for i in range(4):
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin("/main.tex", Origin.Position(i, 0, i), Origin.Position(i + 1, 0, i + 1))
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)
        for i in range(5, 8):
            j = i - 5
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin("/sub.tex", Origin.Position(j, 0, j), Origin.Position(j + 1, 0, j + 1))
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)

    def test_3(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "B0\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        document = LatexDocument()
        document.parse("/main.tex", file_finder=FileFinder("/", "/main.tex", sources))
        for f in ["A", "B", "C"]:
            for i in range(0,3):
                key = f"{f}{i}"
                origin = Origin("/"+f+".tex", Origin.Position(3*i, i, 0), Origin.Position(3*i+1, i, 1))
                p = document.get_text().find(key)
                self.assertEqual(origin, document.get_origin_of_source(p, p+1))
                self.assertEqual(origin, document.get_origin_of_text(p, p+1))

    def test_4(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        document = LatexDocument()
        document.parse("/main.tex", file_finder=FileFinder("/", "/main.tex", sources))
        for f in ["A", "B", "C"]:
            for i in range(0,3):
                key = f"{f}{i}"
                if key=="B0":
                    continue
                if f=="B":
                    origin = Origin("/" + f + ".tex", Origin.Position(3 * i-2, i, 0), Origin.Position(3 * i + 1-2, i, 1))
                else:
                    origin = Origin("/"+f+".tex", Origin.Position(3*i, i, 0), Origin.Position(3*i+1, i, 1))
                p = document.get_text().find(key)
                self.assertEqual(origin, document.get_origin_of_source(p, p+1))
                self.assertEqual(origin, document.get_origin_of_text(p, p+1))

