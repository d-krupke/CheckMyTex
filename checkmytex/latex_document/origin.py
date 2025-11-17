from __future__ import annotations

from .indexed_string import TextPosition
from .source import FilePosition


class OriginPointer:
    """
    A position in a text file.
    """

    def __init__(
        self,
        file: FilePosition,
        source: TextPosition,
        text: TextPosition | None = None,
    ):
        self.file = file  # position in file
        self.source = source  # position in flat source
        self.text = text  # position in detexed text

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OriginPointer):
            return NotImplemented
        return self.file == other.file

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, OriginPointer):
            return NotImplemented
        return self.source < other.source

    def __repr__(self) -> str:
        return f"FILE:{self.file}|SOURCE:{self.source}|text::{self.text}"

    def serialize(self) -> dict:
        return {
            "file": self.file.serialize(),
            "source": self.source.serialize(),
            "text": self.text.serialize() if self.text else None,
        }


class Origin:
    """
    The origin of a part of the parse latex document.
    """

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Origin):
            return NotImplemented
        return (self.begin, self.end) < (other.begin, other.end)

    def __init__(self, begin: OriginPointer, end: OriginPointer) -> None:
        if begin.file.path != end.file.path:
            msg = f"Begin and end must be in the same file: {begin.file.path} != {end.file.path}"
            raise ValueError(msg)
        self.begin: OriginPointer = begin
        self.end: OriginPointer = end
        if not begin < end:
            msg = f"Begin must be before end (this would be empty): {begin} >= {end}"
            raise ValueError(msg)

    def get_file(self) -> str:
        return self.begin.file.path

    def get_text_span(self) -> tuple[int, int] | None:
        if self.begin.text is None:
            return None
        if self.end.text is None:
            msg = "Inconsistent state: begin.text is set but end.text is None"
            raise RuntimeError(msg)
        return self.begin.text.index, self.end.text.index

    def get_source_span(self) -> tuple[int, int]:
        return self.begin.source.index, self.end.source.index

    def get_file_span(self) -> tuple[int, int]:
        return self.begin.file.position.index, self.end.file.position.index

    def get_text_line(self) -> int:
        if self.begin.text is None:
            msg = "Cannot get text line: begin.text is None"
            raise RuntimeError(msg)
        return self.begin.text.line

    def get_source_line(self) -> int:
        return self.begin.source.line

    def get_file_line(self) -> int:
        return self.begin.file.position.line

    def __repr__(self) -> str:
        return f"{self.get_file()}[{self.begin.file.position}-{self.end.file.position}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Origin):
            return NotImplemented
        return self.begin == other.begin and self.end == other.end

    def serialize(self) -> dict:
        return {"begin": self.begin.serialize(), "end": self.end.serialize()}
