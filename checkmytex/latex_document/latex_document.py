"""
The LatexDocument provides easy access to the latex document to be fed to
a checker and to trace the checker's report back to the original document.
"""

import logging
import re
import typing

from flachtex import TraceableString

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

    def get_source(self, line=None) -> str | TraceableString:
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
            msg = "No detex available!"
            raise ValueError(msg)
        return str(self.detexed_text.text)

    def get_file_content(self, path: str, line: int | None = None) -> str:
        """
        Return the content of a file. Does not perform any file reads but
        returns from cache.
        :param path: Path to the file.
        :return: Content of file as string.
        """
        return self.sources.get_file(path, line)

    def get_simplified_origin_of_text(
        self,
        begin: int | tuple[int, int],
        end: int | tuple[int, int],
    ) -> Origin:
        """
        Investigates a simplified origin of the corresponding range.
        Simplified means that the origin will be of the same file and the same line.
        This makes it much easier comprehensible by humans and also for visualization.
        :param begin: Index or line&offset. Inclusive.
        :param end: Index or line&offset. Exclusive.
        :return:
        """
        begin_ = self.detexed_text.get_detailed_position(begin)
        end_ = self.detexed_text.get_detailed_position(end)
        if begin_ >= end_:
            msg = "Incorrect range. End before begin."
            raise ValueError(msg)
        begin_source_idx = self.detexed_text.get_position_in_source(begin_.index)
        end_source_idx = self.detexed_text.get_position_in_source(end_.index - 1) + 1
        if begin_source_idx >= end_source_idx:
            msg = f"Invalid source range: begin ({begin_source_idx}) >= end ({end_source_idx})"
            raise ValueError(msg)
        origin = self.get_simplified_origin_of_source(begin_source_idx, end_source_idx)
        origin.begin.text = begin_
        origin.end.text = end_
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
        begin: int | tuple[int, int],
        end: int | tuple[int, int],
    ) -> Origin:
        """
        Returns the origin of the flattened source (`get_source`).
        :param begin: (Inclusive) begin either as position or line+column
        :param end: (Exclusive) end either as position or line+column
        :return: Origin of the part.
        """
        source = self.sources.flat_source
        begin_: TextPosition = source.get_detailed_position(begin)
        end_: TextPosition = source.get_detailed_position(end)
        if begin_ > end_:
            msg = "End is before begin."
            raise ValueError(msg)
        if end_.index - begin_.index > 1000:  # reduce very large ranges.
            logging.getLogger("CheckMyTex").info(
                f"Reducing long range {begin_}-{end_}."
            )
            begin_ = source.get_detailed_position(end_.index - 1000)
        if begin_ >= end_:
            msg = f"Invalid range after reduction: begin ({begin_}) >= end ({end_})"
            raise ValueError(msg)
        r = self.sources.get_simplified_origin_range(begin_.index, end_.index)
        if r is None:
            msg = f"Could not find origin for range ({begin_.index}, {end_.index})"
            raise RuntimeError(msg)
        if not isinstance(r[0], FilePosition):
            msg = f"Expected FilePosition but got {type(r[0])}"
            raise TypeError(msg)
        return Origin(OriginPointer(r[0], begin_), OriginPointer(r[1], end_))

    def find_in_text(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_text()):
            yield self.get_simplified_origin_of_text(match.start(), match.end())

    def find_in_source(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, str(self.get_source())):
            yield self.get_simplified_origin_of_source(match.start(), match.end())

    def serialize(self) -> dict:
        return {"sources": self.sources.serialize(), "text": str(self.detexed_text)}
