"""Simple FastAPI web interface for CheckMyTex."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
import json

from checkmytex import DocumentAnalyzer
from checkmytex.cli.terminal_html_printer import TerminalHtmlPrinter
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreWordsFromBibliography,
    MathMode,
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

app = FastAPI(title="CheckMyTex Web Interface")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/")
async def index(request: Request):
    """Show upload form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/licenses")
async def licenses(request: Request):
    """Show licenses page."""
    return templates.TemplateResponse("licenses.html", {"request": request})


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    checkers: str = Form(default='["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard"]'),
    filters: str = Form(default='["includegraphics", "refs", "repeated", "mathmode", "authornames", "bibliography"]')
):
    """Analyze uploaded ZIP file and return HTML report."""

    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a ZIP file")

    # Parse checkers configuration
    try:
        enabled_checkers = json.loads(checkers)
    except json.JSONDecodeError:
        enabled_checkers = ["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard"]

    # Parse filters configuration
    try:
        enabled_filters = json.loads(filters)
    except json.JSONDecodeError:
        enabled_filters = ["includegraphics", "refs", "repeated", "mathmode", "authornames", "bibliography"]

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix='checkmytex_'))

    try:
        # Save and extract ZIP
        zip_path = temp_dir / 'upload.zip'
        content = await file.read()
        zip_path.write_bytes(content)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir / 'extracted')

        extract_dir = temp_dir / 'extracted'

        # Find main .tex file
        main_tex = find_main_tex(extract_dir)
        if not main_tex:
            raise HTTPException(status_code=400, detail="No .tex file found in ZIP")

        # Create analyzer with selected checkers and filters
        analyzer = create_analyzer(enabled_checkers, enabled_filters)

        # Parse and analyze
        parser = LatexParser()
        latex_document = parser.parse(str(main_tex))
        analyzed_document = analyzer.analyze(latex_document)

        # Generate HTML using TerminalHtmlPrinter
        printer = TerminalHtmlPrinter(analyzed_document, shorten=5)
        html_path = temp_dir / 'report.html'
        printer.to_html(str(html_path))

        # Return the terminal-styled HTML
        return FileResponse(
            html_path,
            media_type='text/html',
            filename='checkmytex_report.html'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")


def create_analyzer(
    enabled_checkers: list[str] = None,
    enabled_filters: list[str] = None
) -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with configurable checkers and filters.

    Args:
        enabled_checkers: List of checker names to enable.
                         Valid values: 'aspell', 'languagetool', 'chktex',
                                      'siunitx', 'cleveref', 'proselint', 'nphard'
        enabled_filters: List of filter names to enable.
                        Valid values: 'includegraphics', 'refs', 'repeated',
                                     'mathmode', 'authornames', 'bibliography'
    """
    if enabled_checkers is None:
        enabled_checkers = ["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard"]

    if enabled_filters is None:
        enabled_filters = ["includegraphics", "refs", "repeated", "mathmode", "authornames", "bibliography"]

    analyzer = DocumentAnalyzer()

    # Add checkers based on configuration
    if "aspell" in enabled_checkers:
        try:
            analyzer.add_checker(AspellChecker())
        except Exception:
            try:
                analyzer.add_checker(CheckSpell())
            except Exception:
                pass

    if "languagetool" in enabled_checkers:
        try:
            analyzer.add_checker(Languagetool())
        except Exception:
            pass

    if "chktex" in enabled_checkers:
        try:
            analyzer.add_checker(ChkTex())
        except Exception:
            pass

    if "siunitx" in enabled_checkers:
        try:
            analyzer.add_checker(SiUnitx())
        except Exception:
            pass

    if "nphard" in enabled_checkers:
        try:
            analyzer.add_checker(UniformNpHard())
        except Exception:
            pass

    if "cleveref" in enabled_checkers:
        try:
            analyzer.add_checker(Cleveref())
        except Exception:
            pass

    if "proselint" in enabled_checkers:
        try:
            analyzer.add_checker(Proselint())
        except Exception:
            pass

    # Add filters based on configuration
    if "includegraphics" in enabled_filters:
        analyzer.add_filter(IgnoreIncludegraphics())

    if "refs" in enabled_filters:
        analyzer.add_filter(IgnoreRefs())

    if "repeated" in enabled_filters:
        analyzer.add_filter(IgnoreRepeatedWords())

    if "mathmode" in enabled_filters:
        analyzer.add_filter(MathMode())

    if "authornames" in enabled_filters:
        analyzer.add_filter(IgnoreLikelyAuthorNames())

    if "bibliography" in enabled_filters:
        analyzer.add_filter(IgnoreWordsFromBibliography())

    return analyzer


def find_main_tex(directory: Path) -> Path | None:
    """Find the main .tex file in a directory."""
    # Common main file names
    common_names = ["main.tex", "document.tex", "thesis.tex", "paper.tex", "report.tex"]

    for name in common_names:
        candidate = directory / name
        if candidate.exists():
            return candidate

    # Search recursively for files with \documentclass
    for tex_file in directory.rglob("*.tex"):
        try:
            content = tex_file.read_text(encoding="utf-8", errors="ignore")
            if "\\documentclass" in content:
                return tex_file
        except Exception:
            continue

    # Return first .tex file found
    tex_files = list(directory.rglob("*.tex"))
    return tex_files[0] if tex_files else None


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
