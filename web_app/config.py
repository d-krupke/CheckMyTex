"""Configuration constants for the CheckMyTex FastAPI service."""

from __future__ import annotations

import os
from pathlib import Path

# Upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB uncompressed
MAX_COMPRESSION_RATIO = 100  # Prevent zip bombs
MAX_LATEX_FILE_COUNT = 400  # Prevent excessive per-archive files
MAX_INDIVIDUAL_FILE_SIZE = 2 * 1024 * 1024  # 2MB per .tex/.bib file
MAX_TEXT_CHARACTERS = 200_000  # 200k characters for pasted input
PASTED_MAIN_FILENAME = "pasted_document.tex"

# Runtime settings
ANALYSIS_TIMEOUT = 120  # 2 minutes
LANGUAGETOOL_MAX_CHARACTERS = int(
    os.environ.get("LANGUAGETOOL_MAX_CHARACTERS", "80000")
)
LANGUAGETOOL_TIMEOUT = int(os.environ.get("LANGUAGETOOL_TIMEOUT", "120"))
TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_IMPRINT_TEMPLATE = "imprint_placeholder.html"
IMPRINT_TEMPLATE = os.environ.get("IMPRINT_TEMPLATE", DEFAULT_IMPRINT_TEMPLATE)

# Feature toggles
DEFAULT_CHECKERS = [
    "aspell",
    "languagetool",
    "chktex",
    "siunitx",
    "cleveref",
    "proselint",
    "nphard",
    "linelength",
    "todo",
]

DEFAULT_FILTERS = [
    "includegraphics",
    "refs",
    "repeated",
    "spellingwithmath",
    "mathmode",
    "authornames",
    "bibliography",
    "codelistings",
]

ALLOWED_CHECKERS = set(DEFAULT_CHECKERS)
ALLOWED_FILTERS = set(DEFAULT_FILTERS)

# Approximate global LaTeX length limit (~300 pages worth of content)
MAX_TOTAL_LATEX_CHARACTERS = int(os.environ.get("MAX_TOTAL_LATEX_CHARACTERS", "800000"))
