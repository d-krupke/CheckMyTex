"""Helper utilities for FastAPI handlers."""

from __future__ import annotations

import json
from collections.abc import Iterable

from fastapi import HTTPException, Request


def find_main_tex_in_dict(file_dict: dict[str, str]) -> str | None:
    """Find the main .tex file from provided mapping."""
    common_names = [
        "main.tex",
        "document.tex",
        "thesis.tex",
        "paper.tex",
        "report.tex",
    ]

    for name in common_names:
        for filename in file_dict:
            if filename.endswith(f"/{name}") or filename == name:
                return filename

    for filename, content in file_dict.items():
        if filename.endswith(".tex") and "\\documentclass" in content:
            return filename

    for filename in file_dict:
        if filename.endswith(".tex"):
            return filename

    return None


def get_client_ip(request: Request) -> str:
    """Extract client IP (aware of proxy headers)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def parse_selection_payload(
    payload: str | None,
    allowed_values: Iterable[str],
    field_name: str,
    default_values: list[str],
) -> list[str]:
    """Parse JSON payload describing enabled checkers/filters."""
    allowed_set = set(allowed_values)
    if not payload:
        return list(default_values)

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail=f"Malformed {field_name} configuration"
        ) from None

    if not isinstance(parsed, list) or not all(
        isinstance(item, str) for item in parsed
    ):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name.capitalize()} must be a list of strings",
        )

    normalized = []
    invalid = []
    for item in parsed:
        item_lower = item.lower()
        if item_lower not in allowed_set:
            invalid.append(item)
            continue
        if item_lower not in normalized:
            normalized.append(item_lower)

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown {field_name}: {', '.join(invalid)}",
        )

    return normalized
