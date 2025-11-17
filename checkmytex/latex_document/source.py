"""
Container for the LaTeX-sources.
"""

from __future__ import annotations

import typing

from flachtex import TraceableString

from checkmytex.latex_document.indexed_string import (
    IndexedText,
    TextPosition,
    simplify_text_range,
)


class FilePosition:
    def __init__(self, file: str, pos: TextPosition) -> None:
        self.path = file  # file name/path
        self.position = pos  # position in the file

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FilePosition):
            return NotImplemented
        return self.path == other.path and self.position == other.position

    def __repr__(self) -> str:
        return f"{self.path}{self.position}"

    def serialize(self) -> dict:
        return {"path": self.path, "position": self.position.serialize()}


class LatexSource:
    def __init__(self, source: TraceableString, structure: dict[str, dict]):
        self.flat_source: IndexedText = IndexedText(source)
        self.files: dict[str, IndexedText] = {}
        self.includes: dict[str, list[str]] = {}
        for path, data in structure.items():
            self.files[path] = IndexedText(data["content"])
            self.includes[path] = list(data["includes"])
        self.file_names: list[str] = list(self.files.keys())
        self.file_order = {f: i for i, f in enumerate(self.file_names)}

    def get_file(self, file: str, line: int | None) -> str:
        if line is not None:
            return str(self.files[file].get_line(line))
        return str(self.files[file])

    def investigate_origin(self, index: int) -> FilePosition | None:
        # TraceableString has get_origin, plain str does not
        if isinstance(self.flat_source.text, str):
            return None
        file, index = self.flat_source.text.get_origin(index)
        if file not in self.files:
            return None
        text_pos = self.files[file].get_detailed_position(index)
        return FilePosition(file, text_pos)

    def get_simplified_origin_range(
        self, begin: int, end: int
    ) -> tuple[FilePosition, FilePosition] | None:
        origins = [self.investigate_origin(i) for i in range(begin, end)]
        origins_filtered = [o for o in origins if o is not None]
        if not origins_filtered:
            return None
        # Type narrowing: after filtering None values, all items are FilePosition
        origins_typed = typing.cast(list[FilePosition], origins_filtered)
        files = [o.path for o in origins_typed]
        files.sort(key=lambda f: self.file_order[f])
        if (
            files.count(files[-1]) <= 1
            and len(files) > 1
            and files.count(files[-2]) > 1
        ):
            # if the deepest file only contains a single character but the second one
            # has more, use the second one. Maybe the end has just set wrongly.
            focus_on_file = files[-2]
        else:
            focus_on_file = files[-1]
        origins_typed = [o for o in origins_typed if o.path == focus_on_file]
        file_range = simplify_text_range(o.position for o in origins_typed)
        if file_range is None:
            msg = f"Could not determine origin of '{begin} -- {end}'."
            raise ValueError(msg)
        file_begin, file_end = file_range
        return (
            FilePosition(focus_on_file, file_begin),
            FilePosition(focus_on_file, file_end),
        )

    def serialize(self) -> dict:
        return {
            "flat": str(self.flat_source),
            "files": {path: str(content) for path, content in self.files.items()},
        }
