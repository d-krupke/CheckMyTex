"""
The LatexDocument provides easy access to the latex document to be fed to
a checker and to trace the checker's report back to the original document.
"""
import logging
import os.path
import re
import typing

from .detex import DetexedText
from .indexed_string import TextPosition
from .origin import Origin, OriginPointer
from .source import FilePosition, LatexSource


class LatexDocument:
    """
    A latex document that provides a coherent source string (using flachtex) and a
    compiled text string (using yalafi). This tools primarily combines the two tools
    and provides a unified interface to query the origin of a part in the source or
    the compiled text.
    """

    def __init__(self, source: LatexSource, detexed_text: DetexedText):
        self.sources: LatexSource = source
        self.detexed_text = detexed_text

    def files(self) -> typing.Iterable[str]:
        """
        A list of all files in the latex document.
        Sorted by inclusion.
        :return:
        """
        return self.sources.file_names

    def get_source(self, line=None) -> str:
        """
        returns the flattened LaTeX source.
        :return: Single string of the latex source.
        """
        if line is not None:
            return self.sources.flat_source.get_line(line)
        return str(self.sources.flat_source)

    def get_text(self) -> str:
        """
        Returns the compiled text.
        :return: Compiled text as (unicode) string.
        """
        if not self.detexed_text:
            raise ValueError("No detex available!")
        return str(self.detexed_text.text)

    def get_file_content(self, path: str, line: typing.Optional[int] = None) -> str:
        """
        Return the content of a file. Does not perform any file reads but
        returns from cache.
        :param path: Path to the file.
        :return: Content of file as string.
        """
        return self.sources.get_file(path, line)

    def get_simplified_origin_of_text(
        self,
        begin: typing.Union[int, typing.Tuple[int, int]],
        end: typing.Union[int, typing.Tuple[int, int]],
    ) -> Origin:
        """
        Investigates a simplified origin of the corresponding range.
        Simplified means that the origin will be of the same file and the same line.
        This makes it much easier comprehensible by humans and also for visualization.
        :param begin: Index or line&offset. Inclusive.
        :param end: Index or line&offset. Exclusive.
        :return:
        """
        begin = self.detexed_text.get_detailed_position(begin)
        end = self.detexed_text.get_detailed_position(end)
        if begin >= end:
            raise ValueError("Incorrect range. End before begin.")
        begin_source = self.detexed_text.get_position_in_source(begin.index)
        end_source = self.detexed_text.get_position_in_source(end.index - 1) + 1
        assert begin_source < end_source
        origin = self.get_simplified_origin_of_source(begin_source, end_source)
        origin.begin.text = begin
        origin.end.text = end
        return origin

    def get_source_context(self, origin: Origin, n: int = 20) -> str:
        """
        Returns the surrounding source. Can be better suited to whitelist
        some problems.
        :param origin: The origin of the problem
        :param n: +-n characters
        :return: The source context of the problem's origin.
        """
        text = self.get_file_content(origin.get_file())
        s_span = origin.get_source_span()
        return text[max(0, s_span[0] - n) : min(len(text), s_span[1] + n)]

    def get_simplified_origin_of_source(
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
        source = self.sources.flat_source
        begin: TextPosition = source.get_detailed_position(begin)
        end: TextPosition = source.get_detailed_position(end)
        if begin > end:
            raise ValueError("End is before begin.")
        if end.index - begin.index > 1000:  # reduce very large ranges.
            logging.getLogger("CheckMyTex").info(f"Reducing long range {begin}-{end}.")
            begin = source.get_detailed_position(end.index - 1000)
        assert begin < end
        r = self.sources.get_simplified_origin_range(begin.index, end.index)
        assert isinstance(r[0], FilePosition)
        return Origin(OriginPointer(r[0], begin), OriginPointer(r[1], end))

    def find_in_text(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_text()):
            yield self.get_simplified_origin_of_text(match.start(), match.end())

    def find_in_source(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_source()):
            yield self.get_simplified_origin_of_source(match.start(), match.end())

    def serialize(self) -> typing.Dict:
        return {"sources": self.sources.serialize(), "text": str(self.detexed_text)}
