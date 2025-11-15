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
async def analyze(
    file: UploadFile = File(...),
    checkers: str = Form(default='["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard"]')
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

        # Create analyzer with selected checkers
        analyzer = create_analyzer(enabled_checkers)

        # Parse and analyze
        parser = LatexParser()
        latex_document = parser.parse(str(main_tex))
        analyzed_document = analyzer.analyze(latex_document)

        # Generate HTML using RichPrinter
        printer = RichPrinter(analyzed_document, shorten=5)
        html_path = temp_dir / 'report.html'
        printer.to_html(str(html_path))

        # Wrap Rich HTML in terminal-styled container
        rich_html = html_path.read_text(encoding='utf-8')

        # Extract the content between <body> tags
        import re
        body_match = re.search(r'<body>(.*)</body>', rich_html, re.DOTALL)
        if body_match:
            content = body_match.group(1)
        else:
            content = rich_html

        # Create terminal-styled HTML
        terminal_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CheckMyTex Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: #1e1e1e;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: #d4d4d4;
            padding: 20px;
            line-height: 1.6;
        }}

        .terminal-container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: #1e1e1e;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }}

        .terminal-header {{
            background: linear-gradient(to bottom, #3c3c3c, #2d2d2d);
            padding: 12px 16px;
            border-bottom: 1px solid #404040;
            display: flex;
            align-items: center;
        }}

        .terminal-buttons {{
            display: flex;
            gap: 8px;
        }}

        .terminal-button {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        .terminal-button.close {{
            background-color: #ff5f56;
        }}

        .terminal-button.minimize {{
            background-color: #ffbd2e;
        }}

        .terminal-button.maximize {{
            background-color: #27c93f;
        }}

        .terminal-title {{
            flex: 1;
            text-align: center;
            color: #b4b4b4;
            font-size: 13px;
            font-weight: 500;
        }}

        .terminal-content {{
            padding: 20px;
            background-color: #1e1e1e;
            overflow-x: auto;
        }}

        pre {{
            margin: 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
        }}

        code {{
            font-family: inherit;
        }}

        /* Override any white backgrounds from Rich */
        .terminal-content * {{
            background-color: transparent !important;
        }}

        .terminal-content pre,
        .terminal-content code {{
            background-color: transparent !important;
        }}
    </style>
</head>
<body>
    <div class="terminal-container">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <div class="terminal-button close"></div>
                <div class="terminal-button minimize"></div>
                <div class="terminal-button maximize"></div>
            </div>
            <div class="terminal-title">CheckMyTex Analysis Report</div>
            <div style="width: 60px;"></div>
        </div>
        <div class="terminal-content">
{content}
        </div>
    </div>
</body>
</html>"""

        # Write the wrapped HTML
        final_html_path = temp_dir / 'final_report.html'
        final_html_path.write_text(terminal_html, encoding='utf-8')

        # Return the styled HTML file
        return FileResponse(
            final_html_path,
            media_type='text/html',
            filename='checkmytex_report.html'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")


def create_analyzer(enabled_checkers: list[str] = None) -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with configurable checkers.

    Args:
        enabled_checkers: List of checker names to enable.
                         Valid values: 'aspell', 'languagetool', 'chktex',
                                      'siunitx', 'cleveref', 'proselint', 'nphard'
    """
    if enabled_checkers is None:
        enabled_checkers = ["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard"]

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

    # Add filters (always enabled for best results)
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
