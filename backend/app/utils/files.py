import re
import uuid
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name  # strip any directory traversal components
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "file"


def unique_stored_name(original_filename: str) -> str:
    safe = sanitize_filename(original_filename)
    stem = Path(safe).stem
    suffix = Path(safe).suffix
    return f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
