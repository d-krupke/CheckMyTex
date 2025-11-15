"""Analysis wrapper for running CheckMyTex with progress tracking."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from checkmytex import DocumentAnalyzer
from checkmytex.filtering import (
    Filter,
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreWordsFromBibliography,
    MathMode,
    Whitelist,
)
from checkmytex.finding import (
    AspellChecker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    Proselint,
    SiUnitx,
    UniformNpHard,
)
from checkmytex.latex_document.parser import LatexParser


def create_default_analyzer(
    whitelist_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> DocumentAnalyzer:
    """
    Create a DocumentAnalyzer with default checkers and filters.

    Args:
        whitelist_path: Path to whitelist file
        progress_callback: Optional callback for progress updates

    Returns:
        Configured DocumentAnalyzer
    """

    def log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    analyzer = DocumentAnalyzer(log=log)

    # Add checkers
    if progress_callback:
        progress_callback("Adding spell checker...")
    try:
        analyzer.add_checker(AspellChecker())
    except Exception:
        # Fallback to pyspellchecker if aspell not available
        analyzer.add_checker(CheckSpell())

    if progress_callback:
        progress_callback("Adding grammar checker...")
    try:
        analyzer.add_checker(Languagetool())
    except Exception:
        # Languagetool might not be available
        pass

    if progress_callback:
        progress_callback("Adding LaTeX checkers...")
    analyzer.add_checker(ChkTex())
    analyzer.add_checker(SiUnitx())
    analyzer.add_checker(UniformNpHard())
    analyzer.add_checker(Cleveref())

    if progress_callback:
        progress_callback("Adding style checker...")
    try:
        analyzer.add_checker(Proselint())
    except Exception:
        pass

    # Add filters
    if progress_callback:
        progress_callback("Adding filters...")

    analyzer.add_filter(IgnoreIncludegraphics())
    analyzer.add_filter(IgnoreRefs())
    analyzer.add_filter(IgnoreRepeatedWords())
    analyzer.add_filter(MathMode())
    analyzer.add_filter(IgnoreLikelyAuthorNames())
    analyzer.add_filter(IgnoreWordsFromBibliography())

    if whitelist_path and whitelist_path.exists():
        whitelist = Whitelist(str(whitelist_path))
        whitelist.load()
        analyzer.add_filter(whitelist)

    return analyzer


def run_analysis(
    tex_file_path: Path,
    whitelist_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
):
    """
    Run CheckMyTex analysis on a LaTeX document.

    Args:
        tex_file_path: Path to main .tex file
        whitelist_path: Path to whitelist file
        progress_callback: Optional callback for progress updates

    Returns:
        AnalyzedDocument object
    """
    if progress_callback:
        progress_callback(f"Analyzing {tex_file_path.name}...")

    # Create analyzer
    analyzer = create_default_analyzer(whitelist_path, progress_callback)

    if progress_callback:
        progress_callback("Parsing LaTeX document...")

    # Parse document
    parser = LatexParser()
    latex_document = parser.parse(str(tex_file_path))

    if progress_callback:
        progress_callback("Running checks...")

    # Analyze
    analyzed_document = analyzer.analyze(latex_document)

    if progress_callback:
        progress_callback(f"Analysis complete! Found {len(analyzed_document.problems)} problems.")

    return analyzed_document
