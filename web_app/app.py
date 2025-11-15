"""Simple FastAPI web interface for CheckMyTex."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from checkmytex import DocumentAnalyzer
from checkmytex.cli.rich_printer import RichPrinter
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


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Analyze uploaded ZIP file and return HTML report."""

    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a ZIP file")

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

        # Create analyzer
        analyzer = create_analyzer()

        # Parse and analyze
        parser = LatexParser()
        latex_document = parser.parse(str(main_tex))
        analyzed_document = analyzer.analyze(latex_document)

        # Generate HTML using RichPrinter
        printer = RichPrinter(analyzed_document, shorten=5)
        html_path = temp_dir / 'report.html'
        printer.to_html(str(html_path))

        # Return the HTML file
        return FileResponse(
            html_path,
            media_type='text/html',
            filename='checkmytex_report.html'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")


def create_analyzer() -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with default configuration."""
    analyzer = DocumentAnalyzer()

    # Add checkers
    try:
        analyzer.add_checker(AspellChecker())
    except Exception:
        analyzer.add_checker(CheckSpell())

    try:
        analyzer.add_checker(Languagetool())
    except Exception:
        pass

    analyzer.add_checker(ChkTex())
    analyzer.add_checker(SiUnitx())
    analyzer.add_checker(UniformNpHard())
    analyzer.add_checker(Cleveref())

    try:
        analyzer.add_checker(Proselint())
    except Exception:
        pass

    # Add filters
    analyzer.add_filter(IgnoreIncludegraphics())
    analyzer.add_filter(IgnoreRefs())
    analyzer.add_filter(IgnoreRepeatedWords())
    analyzer.add_filter(MathMode())
    analyzer.add_filter(IgnoreLikelyAuthorNames())
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
