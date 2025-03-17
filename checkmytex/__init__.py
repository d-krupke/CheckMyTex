"""
A library to check LaTeX-documents by a set of established tools and some
further rules and refinements.
"""

# flake8: noqa F401
from .analyzed_document import AnalyzedDocument
from .document_analyzer import DocumentAnalyzer
from .latex_document import LatexDocument

__all__ = (AnalyzedDocument, DocumentAnalyzer, LatexDocument)
