"""
Provides a LaTeX-document that allows you to access source and (detexed) text.
Most importantly, it allows you to retrace the origin of a fragment of source
and text, such that you can provide precise reports, like directly jumping
to the location and not just reporting that there is some problem somewhere
in the document (which is not useful for documents with hundreds of pages).
Equipped with this, we can easily apply some established tools such as
chktex or languagetool on the whole document and transform their reports into
a uniform report on individual files and lines.
"""

from .detex import DetexedText
from .latex_document import LatexDocument
from .origin import Origin
from .source import LatexSource

__all__ = ("DetexedText", "LatexDocument", "LatexSource", "Origin")
