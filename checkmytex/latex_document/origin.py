import typing

from checkmytex.latex_document.indexed_string import TextPosition
from checkmytex.latex_document.source import FilePosition


class OriginPointer:
    """
    A position in a text file.
    """

    def __init__(
        self,
        file: FilePosition,
        source: TextPosition,
        text: typing.Optional[TextPosition] = None,
    ):
        self.file = file  # position in file
        self.source = source  # position in flat source
        self.text = text  # position in detexed text

    def __eq__(self, other):
        if not isinstance(other, OriginPointer):
            raise ValueError("Can only compare positions.")
        return self.file == other.file

    def __lt__(self, other):
        if not isinstance(other, OriginPointer):
            raise ValueError("Can only compare positions.")
        return self.source < other.source

    def __repr__(self):
        return f"FILE:{self.file}|SOURCE:{self.source}|text::{self.text}"


class Origin:
    """
    The origin of a part of the parse latex document.
    """

    def __lt__(self, other):
        return (self.begin, self.end) < (other.begin, other.end)

    def __init__(self, begin: OriginPointer, end: OriginPointer):
        self.file: str = begin.file.path
        assert begin.file.path == end.file.path
        self.begin: OriginPointer = begin
        self.end: OriginPointer = end
        assert begin < end, "This would be empty"

    def __repr__(self):
        return f"{self.file}" f"[{self.begin.file.position}-{self.end.file.position}]"

    def __eq__(self, other):
        if not isinstance(other, Origin):
            raise ValueError("Can only compare origins.")
        return (
            self.file == other.file
            and self.begin == other.begin
            and self.end == other.end
        )
