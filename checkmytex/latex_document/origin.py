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

    def serialize(self) -> typing.Dict:
        return {
            "file": self.file.serialize(),
            "source": self.source.serialize(),
            "text": self.text.serialize() if self.text else None,
        }


class Origin:
    """
    The origin of a part of the parse latex document.
    """

    def __lt__(self, other):
        return (self.begin, self.end) < (other.begin, other.end)

    def __init__(self, begin: OriginPointer, end: OriginPointer):
        assert begin.file.path == end.file.path
        self.begin: OriginPointer = begin
        self.end: OriginPointer = end
        assert begin < end, "This would be empty"

    def get_file(self):
        return self.begin.file.path

    def get_text_span(self) -> typing.Optional[typing.Tuple[int, int]]:
        if self.begin.text is None:
            return None
        return self.begin.text.index, self.end.text.index

    def get_source_span(self) -> typing.Tuple[int, int]:
        return self.begin.source.index, self.end.source.index

    def get_file_span(self) -> typing.Tuple[int, int]:
        return self.begin.file.position.index, self.end.file.position.index

    def get_text_line(self) -> int:
        return self.begin.text.line

    def get_source_line(self) -> int:
        return self.begin.source.line

    def get_file_line(self) -> int:
        return self.begin.file.position.line

    def __repr__(self):
        return (
            f"{self.get_file()}"
            f"[{self.begin.file.position}-{self.end.file.position}]"
        )

    def __eq__(self, other):
        if not isinstance(other, Origin):
            raise ValueError("Can only compare origins.")
        return self.begin == other.begin and self.end == other.end

    def serialize(self) -> typing.Dict:
        return {"begin": self.begin.serialize(), "end": self.end.serialize()}
