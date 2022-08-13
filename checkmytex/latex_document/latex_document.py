"""
The LatexDocument provides easy access to the latex document to be fed to
a checker and to trace the checker's report back to the original document.
"""
import os.path
import re
import typing

import flachtex
from flachtex import TraceableString, FileFinder
from flachtex.command_substitution import NewCommandSubstitution, find_new_commands
from yalafi.tex2txt import Options, tex2txt

from .indexed_string import IndexedString
from .origin import Origin


class Detex:
    """
    Container for the detexed text.
    """

    def __init__(self, source: str, yalafi_opts: dict):
        yalafi_opts = yalafi_opts if yalafi_opts else Options()
        self.text, self._charmap = tex2txt(str(source), yalafi_opts)
        self.indexed_text = IndexedString(self.text)

    def text_pos(self, line: int, column: int) -> int:
        """
        :param line: Line in source
        :param column: Column in line
        :return: The position in `self.text`.
        """
        return self.indexed_text.get_position(line, column)

    def source_pos(self, text_pos: int) -> int:
        """
        :param text_pos: The position in `self.text`.
        :return: The position in the original source string.
        """
        return self._charmap[text_pos]


class LatexDocument:
    """
    A latex document that provides a coherent source string (using flachtex) and a
    compiled text string (using yalafi). This tools primarily combines the two tools
    and provides a unified interface to query the origin of a part in the source or
    the compiled text.
    """

    def __init__(
            self, source: TraceableString, files: typing.Dict[str, typing.Dict],
            detex: Detex
    ):
        self._source = IndexedString(source)
        self._files = files
        for path, data in files.items():
            data["content"] = IndexedString(data["content"])
        self._detex = detex

    def _find_command_definitions(self, path: str,
                                  file_finder: typing.Optional[FileFinder]) \
            -> NewCommandSubstitution:
        """
        Parse the document once independently to extract new commands.
        :param path:
        :return:
        """
        preprocessor = flachtex.Preprocessor(os.path.dirname(path))
        if file_finder:
            preprocessor.file_finder = file_finder
        doc = preprocessor.expand_file(path)
        cmds = find_new_commands(doc)
        ncs = NewCommandSubstitution()
        for cmd in cmds:
            ncs.new_command(cmd)
        return ncs

    def files(self) -> typing.Iterable[str]:
        """
        A list of all files in the latex document.
        Sorted by inclusion.
        :return:
        """
        for file_path in self._files:
            yield file_path

    def get_source(self) -> str:
        """
        returns the flattened LaTeX source.
        :return: Single string of the latex source.
        """
        return str(self._source.text)

    def get_text(self) -> str:
        """
        Returns the compiled text.
        :return: Compiled text as (unicode) string.
        """
        if not self._detex:
            raise ValueError("No detex available!")
        return self._detex.text

    def get_file_content(self, path: str) -> str:
        """
        Return the content of a file. Does not perform any file reads but
        returns from cache.
        :param path: Path to the file.
        :return: Content of file as string.
        """
        return self._files[path]["content"].text

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
            begin = self._detex.text_pos(begin[0], begin[1])
        if isinstance(end, tuple):
            end = self._detex.text_pos(end[0], end[1])
        if begin > end:
            raise ValueError("Incorrect range. End before begin.")
        begin_source = self._detex.source_pos(begin) - 1
        end_source = self._detex.source_pos(end - 1)
        assert begin_source < end_source
        origin = self.get_origin_of_source(begin_source, end_source)
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

    def _create_origin(
            self, path: str, begin: int, end: int, sbegin: int, send: int
    ) -> Origin:
        assert 0 <= begin <= end
        assert 0 <= sbegin <= send
        f: IndexedString = self._files[path]["content"]
        lo_begin = f.get_line_and_offset(begin)
        lo_end = f.get_line_and_offset(end)
        assert lo_begin <= lo_end
        return Origin(
            file=path,
            begin=Origin.Position(begin, lo_begin[0], lo_begin[1], sbegin),
            end=Origin.Position(end, lo_end[0], lo_end[1], send),
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
        # TODO: This is an ugly solution!
        begin = self._source.to_position(begin)
        end = self._source.to_position(end)
        assert begin < end
        origins = [self._source.text.get_origin(i) for i in range(begin, end)]
        file_order = {f: i for i, f in enumerate(self.files())}
        max_file = max(origins, key=lambda f: file_order.get(f[0], -1))
        if max_file[0] not in file_order:
            raise ValueError("no origin found")
        origins = [o for o in origins if o[0] == max_file[0]]
        f = self._files[max_file[0]]["content"]
        l, offset = f.get_line_and_offset(origins[-1][1])
        origins = [o for o in origins if f.get_line_and_offset(o[1])[0]==l]
        #print(origins)
        origin_begin = origins[0]
        origin_end = origins[-1]
        origin_end = (origin_end[0], origin_end[1]+1)
        # if not same file, reduce range. Worst case: begin=end-1
        while origin_begin[0] != origin_end[0]:
            end -= 1
            origin_end = self._source.text.get_origin(end)
        assert origin_begin[0] == origin_end[0], "same file"
        assert origin_begin[1] <= origin_end[1], "begin before end"
        origin = self._create_origin(
            origin_begin[0], origin_begin[1], origin_end[1], sbegin=begin, send=end
        )
        return origin

    def find_in_text(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_text()):
            yield self.get_origin_of_text(match.start(), match.end())

    def find_in_source(self, pattern: str) -> typing.Iterable[Origin]:
        for match in re.finditer(pattern, self.get_source()):
            yield self.get_origin_of_source(match.start(), match.end())
