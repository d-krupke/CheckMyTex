"""ZIP handling utilities for CheckMyTex web app."""

from __future__ import annotations

import io
import logging
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

from config import (
    MAX_COMPRESSION_RATIO,
    MAX_INDIVIDUAL_FILE_SIZE,
    MAX_LATEX_FILE_COUNT,
    MAX_UNCOMPRESSED_SIZE,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _is_symlink(zip_info: zipfile.ZipInfo) -> bool:
    """
    Check if a ZipInfo object represents a symbolic link.

    Uses external_attr to detect Unix symlinks, which is more
    compatible across Python versions than is_symlink() method.

    Args:
        zip_info: ZipInfo object to check

    Returns:
        True if the entry is a symlink, False otherwise
    """
    # Unix file attributes are stored in the high 16 bits of external_attr
    # If external_attr is 0, the file was likely created on a non-Unix system
    unix_attr = zip_info.external_attr >> 16
    if unix_attr == 0:
        return False

    # Check if the file mode indicates a symbolic link
    return stat.S_ISLNK(unix_attr)


def _is_safe_path(path: str) -> bool:
    """
    Validate that a ZIP member path is safe to extract.

    Prevents path traversal attacks by checking for:
    - Absolute paths (starting with / or drive letters)
    - Parent directory references (..)
    - Backslash separators (Windows-style)
    - Path components that normalize to dangerous values

    Args:
        path: The file path from ZIP member

    Returns:
        True if path is safe, False otherwise
    """
    if not path or not path.strip():
        return False

    # Normalize Unicode to prevent Unicode-based bypasses
    normalized = unicodedata.normalize("NFKC", path)

    # Reject absolute paths
    if normalized.startswith(("/", "\\")):
        return False

    # Reject Windows absolute paths (e.g., C:\ or \\server\share)
    if len(normalized) >= 2 and normalized[1] == ":":
        return False
    if normalized.startswith("\\\\"):
        return False

    # Use PurePosixPath to safely parse the path
    try:
        posix_path = PurePosixPath(normalized)

        # Check if any path component is '..'
        if ".." in posix_path.parts:
            return False

        # Reject if the resolved path would escape current directory
        # PurePosixPath doesn't resolve .. so we check parts explicitly
        for part in posix_path.parts:
            if part in (".", "..") or not part:
                return False

    except (ValueError, TypeError):
        return False

    # Additional check: reject backslashes entirely (even in filenames)
    return "\\" not in normalized


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
    """
    Extract .tex and .bib files from ZIP archive into memory.

    Security measures:
    - Path traversal prevention (absolute paths, .., Unicode tricks)
    - Symlink detection and rejection
    - File size limits (individual and total)
    - File count limits
    - Extension whitelisting (.tex, .bib only)

    Args:
        zip_file: BytesIO buffer or Path to ZIP file

    Returns:
        Dictionary mapping normalized filenames to their UTF-8 content

    Raises:
        HTTPException: If security checks fail or limits are exceeded
    """
    allowed_extensions = {".tex", ".bib"}
    file_dict: dict[str, str] = {}
    total_extracted_size = 0

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

            # Normalize Unicode in filename to prevent Unicode-based attacks
            normalized_member = unicodedata.normalize("NFKC", member)

            # Security: Check for path traversal attempts
            if not _is_safe_path(normalized_member):
                logger.warning(
                    "Rejected unsafe path in ZIP: %s (normalized: %s)",
                    member,
                    normalized_member,
                )
                continue

            # Security: Reject symbolic links (potential path traversal)
            if _is_symlink(info):
                logger.warning("Rejected symlink in ZIP: %s", member)
                continue

            # Security: Reject files that are actually directories
            if info.is_dir():
                continue

            # Check individual file size
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

            # Track cumulative extracted size to prevent memory exhaustion
            total_extracted_size += info.file_size
            if total_extracted_size > MAX_UNCOMPRESSED_SIZE:
                logger.warning(
                    "Total extracted size exceeds limit: %.1fMB > %.1fMB",
                    total_extracted_size / 1024 / 1024,
                    MAX_UNCOMPRESSED_SIZE / 1024 / 1024,
                )
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"Total extracted content too large "
                        f"({total_extracted_size / 1024 / 1024:.1f}MB, "
                        f"max {MAX_UNCOMPRESSED_SIZE / 1024 / 1024:.1f}MB)"
                    ),
                )

            try:
                # Read and decode file content
                content = zf.read(member).decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning("Failed to read/decode file %s: %s", member, e)
                continue

            # Use normalized filename as key
            file_dict[normalized_member] = content

    return file_dict
