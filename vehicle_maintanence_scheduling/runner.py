import json
from pathlib import Path

from vehicle_maintanence_scheduling.service import build_vehicle_schedule_snapshot


OUTPUT_FILE = Path(__file__).resolve().parent / "output.json"


def write_schedule_snapshot() -> Path:
    snapshot = build_vehicle_schedule_snapshot()
    OUTPUT_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return OUTPUT_FILE


if __name__ == "__main__":
    write_schedule_snapshot()
