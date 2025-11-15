"""Security utilities for safe file handling."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple


# Security constants
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_FILES = 10000

ALLOWED_EXTENSIONS = {
    # LaTeX files
    ".tex",
    ".bib",
    ".cls",
    ".sty",
    ".bst",
    # Images
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".eps",
    ".svg",
    # Text files
    ".txt",
    ".md",
    ".markdown",
    # Data files
    ".csv",
    ".json",
    # Common LaTeX auxiliary
    ".bbl",
    ".aux",
}

DANGEROUS_PATTERNS = [
    "../",
    "..\\",
    "~",
    "$",
]


def validate_zip(zip_file) -> Tuple[bool, Optional[str]]:
    """
    Validate a ZIP file for security issues.

    Args:
        zip_file: Uploaded file object

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    zip_file.seek(0, 2)  # Seek to end
    size = zip_file.tell()
    zip_file.seek(0)  # Reset to beginning

    if size > MAX_ZIP_SIZE:
        return False, f"ZIP file too large: {size / 1024 / 1024:.1f}MB (max: {MAX_ZIP_SIZE / 1024 / 1024}MB)"

    # Try to open as ZIP
    try:
        with zipfile.ZipFile(zip_file, "r") as zf:
            # Check number of files
            if len(zf.namelist()) > MAX_FILES:
                return False, f"Too many files in ZIP: {len(zf.namelist())} (max: {MAX_FILES})"

            # Check total extracted size
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > MAX_EXTRACTED_SIZE:
                return (
                    False,
                    f"Extracted size too large: {total_size / 1024 / 1024:.1f}MB (max: {MAX_EXTRACTED_SIZE / 1024 / 1024}MB)",
                )

            # Check for path traversal and dangerous files
            for name in zf.namelist():
                # Check for directory traversal
                if any(pattern in name for pattern in DANGEROUS_PATTERNS):
                    return False, f"Suspicious file path detected: {name}"

                # Check file extension if it's not a directory
                if not name.endswith("/"):
                    ext = Path(name).suffix.lower()
                    if ext and ext not in ALLOWED_EXTENSIONS:
                        return False, f"Disallowed file type: {name} ({ext})"

        zip_file.seek(0)  # Reset for later use
        return True, None

    except zipfile.BadZipFile:
        return False, "Invalid ZIP file"
    except Exception as e:
        return False, f"Error validating ZIP: {str(e)}"


def extract_zip_safely(zip_file, extract_to: Optional[Path] = None) -> Tuple[Path, List[str]]:
    """
    Safely extract a ZIP file to a temporary directory.

    Args:
        zip_file: Uploaded file object
        extract_to: Optional specific directory to extract to

    Returns:
        Tuple of (extraction_path, list_of_files)
    """
    if extract_to is None:
        extract_to = Path(tempfile.mkdtemp(prefix="checkmytex_"))

    extracted_files = []

    with zipfile.ZipFile(zip_file, "r") as zf:
        for member in zf.infolist():
            # Skip directories
            if member.filename.endswith("/"):
                continue

            # Resolve the target path and ensure it's within extract_to
            target_path = (extract_to / member.filename).resolve()

            # Security check: ensure path is within extract_to
            if not str(target_path).startswith(str(extract_to.resolve())):
                raise ValueError(f"Attempted path traversal: {member.filename}")

            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract file
            with zf.open(member) as source, open(target_path, "wb") as target:
                target.write(source.read())

            extracted_files.append(str(target_path.relative_to(extract_to)))

    return extract_to, extracted_files


def find_tex_files(directory: Path) -> List[Path]:
    """Find all .tex files in a directory."""
    return sorted(directory.rglob("*.tex"))


def find_main_tex(directory: Path) -> Optional[Path]:
    """
    Attempt to find the main .tex file in a directory.

    Looks for:
    1. main.tex
    2. document.tex
    3. thesis.tex
    4. Any .tex file containing \\documentclass

    Args:
        directory: Directory to search

    Returns:
        Path to main .tex file or None
    """
    # Common main file names
    common_names = ["main.tex", "document.tex", "thesis.tex", "paper.tex", "report.tex"]

    for name in common_names:
        candidate = directory / name
        if candidate.exists():
            return candidate

    # Search for files with \documentclass
    for tex_file in find_tex_files(directory):
        try:
            content = tex_file.read_text(encoding="utf-8", errors="ignore")
            if "\\documentclass" in content:
                return tex_file
        except Exception:
            continue

    # If still not found, return the first .tex file
    tex_files = find_tex_files(directory)
    return tex_files[0] if tex_files else None
