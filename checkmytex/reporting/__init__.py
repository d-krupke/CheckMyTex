"""Reporting module for CheckMyTex."""

from __future__ import annotations

from .extension_base import ExtensionContext, ProblemExtension
from .html_report import HtmlReportGenerator

__all__ = [
    "ExtensionContext",
    "HtmlReportGenerator",
    "ProblemExtension",
]
