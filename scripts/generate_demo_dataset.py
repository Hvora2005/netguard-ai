"""CLI helper to write the synthetic demo dataset to data/demo_traffic.csv.

Usage (from the backend virtual environment, repo root):
    python scripts/generate_demo_dataset.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.demo_data import generate_demo_dataset  # noqa: E402

if __name__ == "__main__":
    out_path = REPO_ROOT / "data" / "demo_traffic.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_demo_dataset()
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} synthetic rows to {out_path}")
