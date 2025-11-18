"""
A library to check LaTeX-documents by a set of established tools and some
further rules and refinements.
"""

from __future__ import annotations

from .analyzed_document import AnalyzedDocument
from .document_analyzer import DocumentAnalyzer
from .latex_document import LatexDocument

__version__ = "1.0.0"
__all__ = ("AnalyzedDocument", "DocumentAnalyzer", "LatexDocument")
