"""
The LatexDocument provides easy access to the latex document to be fed to
a checker and to trace the checker's report back to the original document.
"""
import re
import typing

import flachtex
from flachtex.rules import BASIC_SKIP_RULES, Range, RegexSkipRule
from flachtex.utils import compute_row_index
from yalafi.tex2txt import Options, tex2txt

from .origin import Origin


class _IgnoreRule(RegexSkipRule):
    """
    A skip rule for flachtex to remove parts delimited by `%%PAUSE-CHECKING`
    and `%%CONTINUE-CHECKING`.
    """

    def __init__(self):
        super().__init__(
            r"((^\s*%%PAUSE-CHECKING)"
            r"(?P<skipped_part>.*?)"
            r"(^\s*%%CONTINUE-CHECKING))"
        )

    def determine_skip(self, match: re.Match):
        span_to_be_skipped = Range(
            match.start("skipped_part"), match.end("skipped_part")
        )
        return span_to_be_skipped


class LatexDocument:
    """
    A latex document that provides a coherent source string (using flachtex) and a
    compiled text string (using yalafi). This tools primarily combines the two tools
    and provides a unified interface to query the origin of a part in the source or
    the compiled text.
    """

    def __init__(self, path: str, detex=True, file_finder=None, yalafi_opts=None):
        self._source: flachtex.TraceableString = None
        self._sources_row_indices: typing.Dict[str, typing.List[int]] = {}
        self._files = None
        self._detex = None
        self._detex_charmap = None
        self._detex_line_index = None
        self._source_line_index = None
        self._yalafi_opts = yalafi_opts if yalafi_opts else Options()
        self._parse(path, detex, file_finder)

    def _parse(self, path: str, detex=True, file_finder=None):
        """
        Parses and detexes a latex document. Automatically includes all
        includes files in the path.
        :param path: Path to the main file of the latex document.
        :param detex: Set to false if you do not need to detex the document.
        :param file_finder: A file finder. Can be set explicitly for testing.
        :return: Returns itself.
        """
        expand = flachtex.expand_file_and_attach_sources
        flat_source, sources = expand(
            path, skip_rules=BASIC_SKIP_RULES + [_IgnoreRule()], file_finder=file_finder
        )
        self._source = flachtex.remove_comments(flat_source)
        self._source_line_index = compute_row_index(str(self._source))
        self._files = sources
        if detex:
            opts = self._yalafi_opts
            self._detex, self._detex_charmap = tex2txt(str(self._source), opts)
            self._detex_line_index = compute_row_index(self._detex)
        return self

    def files(self) -> typing.Iterable[str]:
        """
        A list of all files in the latex document.
        Sorted by inclusion.
        :return:
        """
        for f in self._files.keys():
            yield f

    def get_source(self) -> str:
        """
        returns the flattened LaTeX source.
        :return: Single string of the latex source.
        """
        return str(self._source)

    def get_text(self) -> str:
        """
        Returns the compiled text.
        :return: Compiled text as (unicode) string.
        """
        if not self._detex:
            raise ValueError("No detex available!")
        return self._detex

    def get_file_content(self, path: str) -> str:
        """
        Return the content of a file. Does not perform any file reads but
        returns from cache.
        :param path: Path to the file.
        :return: Content of file as string.
        """
        return self._files[path]["content"]

    def get_origin_of_text(
        self,
        begin: typing.Union[int, typing.Tuple[int, int]],
        end: typing.Union[int, typing.Tuple[int, int]],
    ) -> Origin:
        """
        Returns the origin of the compiled text (`get_text`).
        :param begin: (Inclusive) begin either as position or line+column
        :param end: (Exclusive) end either as position or line+column
        :return: Origin of the part.
        """
        if isinstance(begin, tuple):
            begin = self._detex_line_index[begin[0]] + begin[1]
            end = self._detex_line_index[end[0]] + end[1]
        b = self._detex_charmap[begin] - 1
        e = self._detex_charmap[end - 1]
        origin = self.get_origin_of_source(b, e)
        origin.begin.tpos = begin
        origin.end.tpos = end
        return origin

    def get_source_context(self, origin: Origin, n: int = 20) -> str:
        """
        Returns the surrounding source. Can be better suited to whitelist
        some problems.
        :param origin: The origin of the problem
        :param n: +-n characters
        :return: The source context of the problem's origin.
        """
        text = self.get_file_content(origin.file)
        begin = max(0, origin.begin.pos - n)
        end = min(len(text), origin.end.pos + n)
        return text[begin:end]

    def _create_origin(self, path, begin: int, end: int) -> Origin:
        if path not in self._sources_row_indices:
            self._sources_row_indices[path] = compute_row_index(
                self.get_file_content(path)
            )
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
        return Origin(
            file=path,
            begin=Origin.Position(begin, row_begin, col_begin),
            end=Origin.Position(end, row_end, col_end),
        )

    def get_origin_of_source(
        self,
        begin: typing.Union[int, typing.Tuple[int, int]],
        end: typing.Union[int, typing.Tuple[int, int]],
    ) -> Origin:
        """
        Returns the origin of the flattened source (`get_source`).
        :param begin: (Inclusive) begin either as position or line+column
        :param end: (Exclusive) end either as position or line+column
        :return: Origin of the part.
        """
        if isinstance(begin, tuple):
            begin = self._source_line_index[begin[0]] + begin[1]
            end = self._source_line_index[end[0]] + end[1]
        assert begin < end
        origin_begin = self._source.get_origin(begin)
        origin_end = self._source.get_origin(end)
        # if not same file, reduce range. Worst case: begin=end-1
        while origin_begin[0] != origin_end[0]:
            end -= 1
            origin_end = self._source.get_origin(end)
        origin = self._create_origin(origin_begin[0], origin_begin[1], origin_end[1])
        origin.begin.spos = begin
        origin.end.spos = end
        return origin

    def find_in_text(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_text()):
            yield self.get_origin_of_text(match.start(), match.end())

    def find_in_source(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_source()):
            yield self.get_origin_of_source(match.start(), match.end())
