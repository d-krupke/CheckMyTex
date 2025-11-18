"""Problem display extensions for HTML reports."""

from __future__ import annotations

from .basic_message import BasicMessageExtension
from .chatgpt_link import ChatGptLinkExtension
from .lookup_url import LookupUrlExtension

__all__ = [
    "BasicMessageExtension",
    "ChatGptLinkExtension",
    "LookupUrlExtension",
]
