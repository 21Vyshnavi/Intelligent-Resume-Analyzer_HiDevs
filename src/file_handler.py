"""
file_handler.py
---------------
All JSON-based persistence for the Resume Analyzer.
Provides save, load, list, and delete helpers for candidate records.
"""

from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


OUTPUT_DIR = Path("data/output")


# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------
def _ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def save_candidate(
    candidate_data: dict,
    match_result: dict,
    filename: Optional[str] = None,
    output_dir: Path = OUTPUT_DIR,
) -> str:
    """
    Save a candidate analysis to a JSON file.

    Parameters
    ----------
    candidate_data : dict   – parsed resume dict
    match_result   : dict   – match scores dict
    filename       : str    – optional custom filename (without extension)
    output_dir     : Path   – where to write; defaults to OUTPUT_DIR

    Returns
    -------
    str : full path of the saved file
    """
    _ensure_dir(output_dir)

    if not filename:
        name_slug = (
            candidate_data.get("name", "unknown")
            .lower()
            .replace(" ", "_")
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name_slug}_{timestamp}"

    record = {
        "id":           str(uuid.uuid4()),
        "analyzed_at":  datetime.now().isoformat(),
        "candidate":    candidate_data,
        "match_result": match_result,
    }

    filepath = output_dir / f"{filename}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_candidate(filepath: str | Path) -> dict:
    """
    Load a single candidate JSON record.

    Raises
    ------
    FileNotFoundError : if the file does not exist
    ValueError        : if the file is not valid JSON
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filepath}: {exc}") from exc


def list_candidates(output_dir: Path = OUTPUT_DIR) -> list[dict]:
    """
    Return a summary list of all saved candidate records.

    Each item contains: id, name, email, overall_score, verdict, analyzed_at, filepath.
    """
    _ensure_dir(output_dir)
    records = []

    for json_file in sorted(output_dir.glob("*.json")):
        try:
            data = load_candidate(json_file)
            candidate = data.get("candidate", {})
            match     = data.get("match_result", {})
            records.append({
                "id":            data.get("id", ""),
                "name":          candidate.get("name", "Unknown"),
                "email":         candidate.get("email", ""),
                "overall_score": match.get("overall_score", 0),
                "verdict":       match.get("verdict", ""),
                "analyzed_at":   data.get("analyzed_at", ""),
                "filepath":      str(json_file),
            })
        except (ValueError, KeyError):
            continue   # skip corrupted files

    return records


def delete_candidate(filepath: str | Path) -> bool:
    """
    Delete a candidate JSON record.

    Returns True if deleted, False if not found.
    """
    path = Path(filepath)
    if path.exists():
        path.unlink()
        return True
    return False


def save_batch(
    results: list[dict],
    filename: str = "batch_analysis",
    output_dir: Path = OUTPUT_DIR,
) -> str:
    """
    Save multiple candidate analyses into a single JSON array file.

    Returns the path of the written file.
    """
    _ensure_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath  = output_dir / f"{filename}_{timestamp}.json"

    payload = {
        "batch_id":    str(uuid.uuid4()),
        "generated_at": datetime.now().isoformat(),
        "total":       len(results),
        "results":     results,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_json(filepath: str | Path) -> Any:
    """Generic JSON loader (used for config files, etc.)."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, filepath: str | Path, indent: int = 2) -> None:
    """Generic JSON writer."""
    path = Path(filepath)
    _ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
