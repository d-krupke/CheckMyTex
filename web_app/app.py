"""Simple Flask web interface for CheckMyTex."""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, render_template, request, send_file, redirect, url_for

from checkmytex import DocumentAnalyzer
from checkmytex.cli.rich_printer import RichPrinter
from checkmytex.filtering import (
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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max


@app.route('/')
def index():
    """Show upload form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded ZIP file and return HTML report."""
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    if not file.filename.endswith('.zip'):
        return 'Please upload a ZIP file', 400

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix='checkmytex_'))

    try:
        # Save and extract ZIP
        zip_path = temp_dir / 'upload.zip'
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir / 'extracted')

        extract_dir = temp_dir / 'extracted'

        # Find main .tex file
        main_tex = find_main_tex(extract_dir)
        if not main_tex:
            return 'No .tex file found in ZIP', 400

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
        return send_file(html_path, mimetype='text/html')

    except Exception as e:
        return f'Error analyzing document: {str(e)}', 500

    finally:
        # Cleanup in background (optional - temp files will be cleaned by OS eventually)
        pass


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
    app.run(host='0.0.0.0', port=5000, debug=True)
