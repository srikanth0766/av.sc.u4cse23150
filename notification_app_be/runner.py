import json
from pathlib import Path

from notification_app_be.notifications import build_priority_snapshot


OUTPUT_FILE = Path(__file__).resolve().parent / "output.json"


def write_priority_snapshot(limit: int = 10) -> Path:
    snapshot = build_priority_snapshot(limit=limit)
    OUTPUT_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return OUTPUT_FILE


if __name__ == "__main__":
    write_priority_snapshot()
