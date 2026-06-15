"""Dump the FastAPI OpenAPI schema to openapi.json (no running server needed).

The frontend generates its type-safe client from this file:
    python scripts/export_openapi.py
    cd web && npm run gen:api
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

OUT = ROOT / "openapi.json"


def main() -> None:
    OUT.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
