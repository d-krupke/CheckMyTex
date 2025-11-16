"""Simple FastAPI web interface for CheckMyTex."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
import zipfile
from contextlib import contextmanager, suppress
from datetime import datetime
from pathlib import Path

from checkmytex import DocumentAnalyzer
from checkmytex.cli.terminal_html_printer import TerminalHtmlPrinter
from checkmytex.filtering import (
    IgnoreCodeListings,
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    MathMode,
)
from checkmytex.finding import (
    AspellChecker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    LineLengthChecker,
    Proselint,
    SiUnitx,
    TodoChecker,
    UniformNpHard,
)
from checkmytex.latex_document.parser import LatexParser
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB uncompressed
MAX_COMPRESSION_RATIO = 100  # Prevent zip bombs
ANALYSIS_TIMEOUT = 120  # 2 minutes

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CheckMyTex Web Interface")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


# Utility functions


@contextmanager
def temp_workspace():
    """Create a temporary workspace that is always cleaned up."""
    temp_dir = Path(tempfile.mkdtemp(prefix="checkmytex_"))
    try:
        logger.debug(f"Created temporary workspace: {temp_dir}")
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temporary workspace: {temp_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary directory {temp_dir}: {e}")


def validate_zip_file(zip_path: Path) -> None:
    """Validate ZIP file for security issues.

    Raises:
        HTTPException: If the ZIP file is suspicious or too large.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Calculate compression ratio
            compressed_size = zip_path.stat().st_size
            uncompressed_size = sum(info.file_size for info in zf.infolist())

            # Check for zip bombs
            if compressed_size == 0:
                raise HTTPException(status_code=400, detail="Empty ZIP file")

            ratio = uncompressed_size / compressed_size
            if ratio > MAX_COMPRESSION_RATIO:
                logger.warning(
                    f"Suspicious ZIP file detected: compression ratio {ratio:.1f}x "
                    f"(threshold: {MAX_COMPRESSION_RATIO}x)"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Suspicious ZIP file detected (compression ratio too high: {ratio:.0f}x)",
                )

            # Check uncompressed size
            if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Uncompressed content too large ({uncompressed_size / 1024 / 1024:.1f}MB, max {MAX_UNCOMPRESSED_SIZE / 1024 / 1024:.0f}MB)",
                )

            logger.info(
                f"ZIP validation passed: {compressed_size / 1024:.1f}KB compressed, "
                f"{uncompressed_size / 1024:.1f}KB uncompressed (ratio: {ratio:.1f}x)"
            )

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")


# API Endpoints


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
    request: Request,
    file: UploadFile = File(...),
    checkers: str = Form(
        default='["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard", "linelength", "todo"]'
    ),
    filters: str = Form(
        default='["includegraphics", "refs", "repeated", "spellingwithmath", "mathmode", "authornames", "bibliography", "codelistings"]'
    ),
):
    """Analyze uploaded ZIP file and return HTML report."""
    start_time = datetime.now()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"Analysis request from {client_ip} for file: {file.filename}")

    # Validate file extension
    if not file.filename or not file.filename.endswith(".zip"):
        logger.warning(f"Invalid file type from {client_ip}: {file.filename}")
        raise HTTPException(status_code=400, detail="Please upload a ZIP file")

    # Parse checkers configuration
    try:
        enabled_checkers = json.loads(checkers)
    except json.JSONDecodeError:
        enabled_checkers = [
            "aspell",
            "languagetool",
            "chktex",
            "siunitx",
            "cleveref",
            "proselint",
            "nphard",
        ]

    # Parse filters configuration
    try:
        enabled_filters = json.loads(filters)
    except json.JSONDecodeError:
        enabled_filters = [
            "includegraphics",
            "refs",
            "repeated",
            "spellingwithmath",
            "mathmode",
            "authornames",
            "bibliography",
        ]

    logger.info(
        f"Configuration from {client_ip}: "
        f"checkers={enabled_checkers}, filters={enabled_filters}"
    )

    # Use temporary workspace with guaranteed cleanup
    with temp_workspace() as temp_dir:
        try:
            # Read and validate file size
            zip_path = temp_dir / "upload.zip"
            content = await file.read()

            if len(content) > MAX_FILE_SIZE:
                logger.warning(
                    f"File too large from {client_ip}: {len(content) / 1024 / 1024:.1f}MB "
                    f"(max {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large ({len(content) / 1024 / 1024:.1f}MB, max {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)",
                )

            # Save ZIP file
            zip_path.write_bytes(content)
            logger.debug(f"Saved ZIP file: {len(content) / 1024:.1f}KB")

            # Validate ZIP file (security checks)
            validate_zip_file(zip_path)

            # Extract ZIP with timeout protection
            try:
                async with asyncio.timeout(30):  # 30 second timeout for extraction
                    await asyncio.to_thread(
                        lambda: zipfile.ZipFile(zip_path, "r").extractall(
                            temp_dir / "extracted"
                        )
                    )
            except TimeoutError:
                logger.error(f"ZIP extraction timeout from {client_ip}")
                raise HTTPException(
                    status_code=504, detail="ZIP extraction took too long"
                )

            extract_dir = temp_dir / "extracted"
            logger.debug(f"Extracted ZIP to: {extract_dir}")

            # Find main .tex file
            main_tex = find_main_tex(extract_dir)
            if not main_tex:
                logger.warning(f"No .tex file found in ZIP from {client_ip}")
                raise HTTPException(status_code=400, detail="No .tex file found in ZIP")

            logger.info(f"Found main .tex file: {main_tex.name}")

            # Create analyzer with selected checkers and filters
            analyzer = create_analyzer(enabled_checkers, enabled_filters)

            # Parse and analyze with timeout
            try:
                async with asyncio.timeout(ANALYSIS_TIMEOUT):
                    # Run analysis in thread pool to avoid blocking
                    analyzed_document = await asyncio.to_thread(
                        lambda: (
                            parser := LatexParser(),
                            latex_document := parser.parse(str(main_tex)),
                            analyzer.analyze(latex_document),
                        )[-1]
                    )

            except TimeoutError:
                logger.error(
                    f"Analysis timeout from {client_ip} after {ANALYSIS_TIMEOUT}s"
                )
                raise HTTPException(
                    status_code=504,
                    detail=f"Analysis took too long (timeout: {ANALYSIS_TIMEOUT}s)",
                )

            # Generate HTML report in memory (no need to write to disk)
            printer = TerminalHtmlPrinter(analyzed_document, shorten=5)
            printer.html_parts = []
            printer._generate_html()
            html_content = "\n".join(printer.html_parts)

            # Log success
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Analysis completed for {client_ip} in {duration:.1f}s "
                f"({len(analyzed_document.get_problems())} problems found)"
            )

            # Return the terminal-styled HTML
            return HTMLResponse(content=html_content, media_type="text/html")

        except HTTPException:
            raise
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Analysis failed for {client_ip} after {duration:.1f}s: {type(e).__name__}: {e!s}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Error analyzing document: {e!s}"
            )


def create_analyzer(
    enabled_checkers: list[str] | None = None, enabled_filters: list[str] | None = None
) -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with configurable checkers and filters.

    Args:
        enabled_checkers: List of checker names to enable.
                         Valid values: 'aspell', 'languagetool', 'chktex',
                                      'siunitx', 'cleveref', 'proselint', 'nphard',
                                      'linelength', 'todo'
        enabled_filters: List of filter names to enable.
                        Valid values: 'includegraphics', 'refs', 'repeated',
                                     'spellingwithmath', 'mathmode', 'authornames',
                                     'bibliography', 'codelistings'
    """
    if enabled_checkers is None:
        enabled_checkers = [
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

    if enabled_filters is None:
        enabled_filters = [
            "includegraphics",
            "refs",
            "repeated",
            "spellingwithmath",
            "mathmode",
            "authornames",
            "bibliography",
            "codelistings",
        ]

    analyzer = DocumentAnalyzer()

    # Add checkers based on configuration
    if "aspell" in enabled_checkers:
        try:
            analyzer.add_checker(AspellChecker())
        except Exception:
            with suppress(Exception):
                analyzer.add_checker(CheckSpell())

    if "languagetool" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(Languagetool())

    if "chktex" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(ChkTex())

    if "siunitx" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(SiUnitx())

    if "nphard" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(UniformNpHard())

    if "cleveref" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(Cleveref())

    if "proselint" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(Proselint())

    if "linelength" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(LineLengthChecker(max_length=200))

    if "todo" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(TodoChecker())

    # Add filters based on configuration
    if "includegraphics" in enabled_filters:
        analyzer.add_filter(IgnoreIncludegraphics())

    if "refs" in enabled_filters:
        analyzer.add_filter(IgnoreRefs())

    if "repeated" in enabled_filters:
        analyzer.add_filter(IgnoreRepeatedWords())

    if "spellingwithmath" in enabled_filters:
        analyzer.add_filter(IgnoreSpellingWithMath())

    if "mathmode" in enabled_filters:
        analyzer.add_filter(MathMode())

    if "authornames" in enabled_filters:
        analyzer.add_filter(IgnoreLikelyAuthorNames())

    if "bibliography" in enabled_filters:
        analyzer.add_filter(IgnoreWordsFromBibliography())

    if "codelistings" in enabled_filters:
        analyzer.add_filter(IgnoreCodeListings())

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
