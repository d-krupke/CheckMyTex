import typing


class Origin:
    """
    The origin of a part of the parse latex document.
    """

    class Position:
        """
        A position in a text file.
        """

        def __init__(
            self,
            pos: int,
            row: int,
            col: int,
            spos: typing.Optional[int] = None,
            tpos: typing.Optional[int] = None,
        ):
            self.pos = pos  # position in the file. Starting at zero.
            self.row = row  # row or line in the file. Starting at zero.
            self.col = col  # column in the line. Starting at zero.
            self.spos = spos  # position in the source string
            self.tpos = tpos  # position in the text string

        def __eq__(self, other):
            if not isinstance(other, Origin.Position):
                raise ValueError("Can only compare positions.")
            return (
                self.pos == other.pos
                and self.row == other.row
                and self.col == other.col
            )

        def __lt__(self, other):
            if not isinstance(other, Origin.Position):
                raise ValueError("Can only compare positions.")
            return self.pos < other.pos

    def __lt__(self, other):
        return (self.begin, self.end) < (other.begin, other.end)

    def __init__(self, file: str, begin: Position, end: Position):
        self.file: str = file
        self.begin: Origin.Position = begin
        self.end: Origin.Position = end
        assert begin != end, "This would be empty"

    def __repr__(self):
        return (
            f"{self.file}"
            f"[{self.begin.pos}:{self.begin.row}:{self.begin.col}"
            f"-{self.end.pos}:{self.end.row}:{self.end.col}]"
        )

    def __eq__(self, other):
        if not isinstance(other, Origin):
            raise ValueError("Can only compare origins.")
        return (
            self.file == other.file
            and self.begin == other.begin
            and self.end == other.end
        )
