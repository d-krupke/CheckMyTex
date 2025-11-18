"""ZIP handling utilities for CheckMyTex web app."""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

from config import (
    MAX_COMPRESSION_RATIO,
    MAX_INDIVIDUAL_FILE_SIZE,
    MAX_LATEX_FILE_COUNT,
    MAX_UNCOMPRESSED_SIZE,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def validate_zip_file(zip_file: io.BytesIO | Path, file_size: int) -> None:
    """Validate ZIP archive size and compression ratio."""
    try:
        with zipfile.ZipFile(zip_file, "r") as zf:
            compressed_size = file_size
            uncompressed_size = sum(info.file_size for info in zf.infolist())

            if compressed_size == 0:
                raise HTTPException(status_code=400, detail="Empty ZIP file")

            ratio = uncompressed_size / compressed_size
            if ratio > MAX_COMPRESSION_RATIO:
                logger.warning(
                    "Suspicious ZIP file detected: compression ratio %.1fx", ratio
                )
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Suspicious ZIP file detected "
                        f"(compression ratio too high: {ratio:.0f}x)"
                    ),
                )

            if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                logger.warning(
                    "Uncompressed content too large: %.1fMB",
                    uncompressed_size / 1024 / 1024,
                )
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Uncompressed content too large "
                        f"({uncompressed_size / 1024 / 1024:.1f}MB, "
                        f"max {MAX_UNCOMPRESSED_SIZE / 1024 / 1024:.0f}MB)"
                    ),
                )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file") from None


def extract_latex_files_to_dict(zip_file: io.BytesIO | Path) -> dict[str, str]:
    """Extract .tex and .bib files from ZIP archive into memory."""
    allowed_extensions = {".tex", ".bib"}
    file_dict: dict[str, str] = {}

    with zipfile.ZipFile(zip_file, "r") as zf:
        allowed_members = [
            info
            for info in zf.infolist()
            if Path(info.filename).suffix.lower() in allowed_extensions
        ]

        if len(allowed_members) > MAX_LATEX_FILE_COUNT:
            logger.warning(
                "Rejected ZIP with %s LaTeX files (max %s)",
                len(allowed_members),
                MAX_LATEX_FILE_COUNT,
            )
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Too many LaTeX files ({len(allowed_members)} > "
                    f"{MAX_LATEX_FILE_COUNT})"
                ),
            )

        for info in allowed_members:
            member = info.filename

            if ".." in member or member.startswith("/"):
                continue

            if info.file_size > MAX_INDIVIDUAL_FILE_SIZE:
                logger.warning(
                    "Rejected file %s (size %.1fMB > %.1fMB)",
                    member,
                    info.file_size / 1024 / 1024,
                    MAX_INDIVIDUAL_FILE_SIZE / 1024 / 1024,
                )
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File {member} is too large "
                        f"({info.file_size / 1024 / 1024:.1f}MB, "
                        f"max {MAX_INDIVIDUAL_FILE_SIZE / 1024 / 1024:.1f}MB)"
                    ),
                )

            try:
                content = zf.read(member).decode("utf-8", errors="replace")
            except Exception:
                continue

            file_dict[member] = content

    return file_dict
