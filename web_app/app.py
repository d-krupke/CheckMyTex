"""Simple FastAPI web interface for CheckMyTex."""

from __future__ import annotations

import asyncio
import io
import logging
import uuid
from datetime import datetime

import checkmytex
import flachtex
from analyzer_factory import create_analyzer
from checkmytex.latex_document.parser import LatexParser
from checkmytex.reporting.extensions import (
    BasicMessageExtension,
    ChatGptLinkExtension,
)
from checkmytex.reporting.html_report import HtmlReportGenerator
from config import (
    ALLOWED_CHECKERS,
    ALLOWED_FILTERS,
    ANALYSIS_TIMEOUT,
    DEFAULT_CHECKERS,
    DEFAULT_FILTERS,
    DEFAULT_IMPRINT_TEMPLATE,
    IMPRINT_TEMPLATE,
    MAX_FILE_SIZE,
    MAX_TEXT_CHARACTERS,
    MAX_TOTAL_LATEX_CHARACTERS,
    PASTED_MAIN_FILENAME,
    TEMPLATE_DIR,
)
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from helpers import find_main_tex_in_dict, get_client_ip, parse_selection_payload
from jinja2 import TemplateNotFound
from zip_handler import extract_latex_files_to_dict, validate_zip_file

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CheckMyTex Web Interface")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Helpers


def enforce_project_length_limit(
    file_dict: dict[str, str], request_id: str, client_ip: str
) -> None:
    """Raise if combined LaTeX sources exceed configured character limit."""
    total_chars = sum(len(content or "") for content in file_dict.values())
    if total_chars > MAX_TOTAL_LATEX_CHARACTERS:
        approx_pages = max(1, total_chars // 2600)
        logger.warning(
            "[%s] Project too large from %s (%d chars ~%d pages)",
            request_id,
            client_ip,
            total_chars,
            approx_pages,
        )
        raise HTTPException(
            status_code=413,
            detail=(
                "Project appears to exceed roughly 300 pages. "
                "Please trim the submission or run CheckMyTex locally."
            ),
        )


# API Endpoints


@app.get("/")
async def index(request: Request):
    """Show upload form."""
    return templates.TemplateResponse(
        "index.html", {"request": request, "version": checkmytex.__version__}
    )


@app.get("/licenses")
async def licenses(request: Request):
    """Show licenses page."""
    return templates.TemplateResponse("licenses.html", {"request": request})


@app.get("/imprint")
async def imprint(request: Request):
    """Show imprint/legal notice."""
    template_name = IMPRINT_TEMPLATE
    try:
        return templates.TemplateResponse(template_name, {"request": request})
    except TemplateNotFound:
        logger.warning(
            "Imprint template '%s' not found; falling back to default", template_name
        )
        return templates.TemplateResponse(
            DEFAULT_IMPRINT_TEMPLATE, {"request": request}
        )


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "checkmytex"}


@app.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile | None = File(None),  # noqa: B008
    latex_text: str = Form(""),
    input_mode: str = Form("zip"),
    checkers: str = Form(
        default='["aspell", "languagetool", "chktex", "siunitx", "cleveref", "proselint", "nphard", "linelength", "todo"]'
    ),
    filters: str = Form(
        default='["includegraphics", "refs", "repeated", "spellingwithmath", "mathmode", "authornames", "bibliography", "codelistings"]'
    ),
):
    """Analyze uploaded ZIP file and return HTML report."""
    # Generate unique request ID for tracking and abuse detection
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    client_ip = get_client_ip(request)

    sanitized_mode = (input_mode or "zip").strip().lower()
    if sanitized_mode not in {"zip", "text"}:
        raise HTTPException(
            status_code=400, detail="Invalid input_mode (expected 'zip' or 'text')"
        )

    filename = file.filename if file else None
    logger.info(
        "[%s] Analysis request from %s using %s input (filename=%s)",
        request_id,
        client_ip,
        sanitized_mode,
        filename or "pasted-text",
    )

    preloaded_file_dict: dict[str, str] | None = None
    preloaded_main_tex: str | None = None
    zip_buffer: io.BytesIO | None = None
    pasted_line_count = 0

    if sanitized_mode == "zip":
        if not file or not file.filename:
            logger.warning("[%s] No file provided from %s", request_id, client_ip)
            raise HTTPException(status_code=400, detail="Please upload a ZIP file")

        if not file.filename.lower().endswith(".zip"):
            logger.warning(
                "[%s] Invalid file type from %s: %s",
                request_id,
                client_ip,
                file.filename,
            )
            raise HTTPException(status_code=400, detail="Please upload a ZIP file")

        # Read at most MAX_FILE_SIZE + 1 bytes to prevent memory exhaustion
        content = await file.read(MAX_FILE_SIZE + 1)

        # If we got more than MAX_FILE_SIZE, the file is too large
        if len(content) > MAX_FILE_SIZE:
            logger.warning(
                "[%s] File too large from %s (max %.0fMB)",
                request_id,
                client_ip,
                MAX_FILE_SIZE / 1024 / 1024,
            )
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)",
            )

        # Create in-memory ZIP file (no disk I/O)
        zip_buffer = io.BytesIO(content)

        logger.debug(
            "[%s] Validating ZIP file: %.1fKB", request_id, len(content) / 1024
        )

        # Validate ZIP file (security checks: compression ratio, size)
        validate_zip_file(zip_buffer, len(content))

        # Reset buffer position after validation
        zip_buffer.seek(0)

    else:
        latex_text = (latex_text or "").strip()
        if not latex_text:
            raise HTTPException(
                status_code=400, detail="Please paste LaTeX content to analyze"
            )

        if len(latex_text) > MAX_TEXT_CHARACTERS:
            raise HTTPException(
                status_code=413,
                detail=f"Pasted content too large (max {MAX_TEXT_CHARACTERS:,} characters)",
            )

        file_size_total = len(latex_text)
        if file_size_total > MAX_TOTAL_LATEX_CHARACTERS:
            approx_pages = max(1, file_size_total // 2600)
            logger.warning(
                "[%s] Pasted LaTeX too large from %s (%d chars ~%d pages)",
                request_id,
                client_ip,
                file_size_total,
                approx_pages,
            )
            raise HTTPException(
                status_code=413,
                detail=(
                    "Pasted LaTeX exceeds the supported size (~300 pages). "
                    "Please run CheckMyTex locally for very large documents."
                ),
            )

        preloaded_file_dict = {PASTED_MAIN_FILENAME: latex_text}
        preloaded_main_tex = PASTED_MAIN_FILENAME
        pasted_line_count = latex_text.count("\n") + 1

    # Parse and validate client configuration
    enabled_checkers = parse_selection_payload(
        checkers, ALLOWED_CHECKERS, "checkers", DEFAULT_CHECKERS
    )
    enabled_filters = parse_selection_payload(
        filters, ALLOWED_FILTERS, "filters", DEFAULT_FILTERS
    )

    logger.info(
        "[%s] Configuration from %s: checkers=%s, filters=%s",
        request_id,
        client_ip,
        enabled_checkers,
        enabled_filters,
    )

    try:
        # Create analyzer with selected checkers and filters
        analyzer = create_analyzer(enabled_checkers, enabled_filters)

        # Parse, extract, and analyze with timeout (fully in-memory using flachtex dictionary)
        try:
            async with asyncio.timeout(ANALYSIS_TIMEOUT):
                if sanitized_mode == "zip":
                    if zip_buffer is None:
                        raise HTTPException(
                            status_code=400, detail="No ZIP file content provided"
                        )

                    logger.debug(
                        "[%s] Extracting .tex and .bib files to memory", request_id
                    )
                    file_dict = await asyncio.to_thread(
                        extract_latex_files_to_dict, zip_buffer
                    )

                    # Find main .tex file in dictionary
                    main_tex_filename = find_main_tex_in_dict(file_dict)
                    if not main_tex_filename:
                        logger.warning(
                            "[%s] No .tex file found in ZIP from %s",
                            request_id,
                            client_ip,
                        )
                        raise HTTPException(
                            status_code=400, detail="No .tex file found in ZIP"
                        )

                    logger.info(
                        "[%s] Found main .tex file in ZIP: %s (%d files total)",
                        request_id,
                        main_tex_filename,
                        len(file_dict),
                    )
                    enforce_project_length_limit(file_dict, request_id, client_ip)
                else:
                    file_dict = preloaded_file_dict
                    main_tex_filename = preloaded_main_tex
                    logger.info(
                        "[%s] Using pasted LaTeX input (%d lines)",
                        request_id,
                        pasted_line_count,
                    )
                    enforce_project_length_limit(file_dict, request_id, client_ip)

                if not file_dict or not main_tex_filename:
                    raise HTTPException(
                        status_code=400,
                        detail="No LaTeX sources available for analysis",
                    )

                # Run analysis in thread pool to avoid blocking
                def run_analysis():
                    # Create file finder with in-memory file system
                    file_finder = flachtex.FileFinder(
                        project_root=".", file_system=file_dict
                    )
                    parser = LatexParser(file_finder=file_finder)
                    latex_document = parser.parse(main_tex_filename)
                    return analyzer.analyze(latex_document)

                analyzed_document = await asyncio.to_thread(run_analysis)

        except TimeoutError:
            logger.error(
                "[%s] Analysis timeout from %s after %ds",
                request_id,
                client_ip,
                ANALYSIS_TIMEOUT,
            )
            raise HTTPException(
                status_code=504,
                detail=f"Analysis took too long (timeout: {ANALYSIS_TIMEOUT}s)",
            ) from None

        # Generate HTML report in memory with extensions
        extensions = [
            BasicMessageExtension(),  # Always include the basic message
            ChatGptLinkExtension(model="gpt-4o"),  # ChatGPT + docs + copy buttons
        ]

        report = HtmlReportGenerator(
            analyzed_document, extensions=extensions, shorten=5
        )
        html_content = report.render()

        # Log success
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "[%s] Analysis completed for %s in %.1fs (%d problems found)",
            request_id,
            client_ip,
            duration,
            len(analyzed_document.get_problems()),
        )

        # Return the terminal-styled HTML
        return HTMLResponse(content=html_content, media_type="text/html")

    except HTTPException:
        raise
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            "[%s] Analysis failed for %s after %.1fs: %s: %s",
            request_id,
            client_ip,
            duration,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Error analyzing document"
        ) from None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
