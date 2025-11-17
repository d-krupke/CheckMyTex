from yalafi.tex2txt import Options, tex2txt

from checkmytex.latex_document.indexed_string import IndexedText


class DetexedText(IndexedText):
    """
    Container for the detexed text. It just wraps yalafi.
    """

    def __init__(self, source: str, yalafi_opts: Options | None = None):
        yalafi_opts = yalafi_opts if yalafi_opts else Options()
        text, self._charmap = tex2txt(str(source), yalafi_opts)
        super().__init__(text)

    def get_position_in_source(self, index: int) -> int:
        """
        Given an index in the detexed text, return the index in the source code, the
        corresponding character stems from.
        :param index: Detexed text index
        :return: Corresponding source index
        """
        pos = self.get_detailed_position(index)
        return self._charmap[pos.index] - 1  # the map is somehow starting at 1
