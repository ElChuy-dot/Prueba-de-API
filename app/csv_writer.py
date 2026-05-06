import csv
from pathlib import Path
from app.schemas import OBDSnapshot

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "obd_log.csv"

_FIELDNAMES = ["timestamp", "command", "value", "unit"]


def _ensure_csv():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
            writer.writeheader()


def append_snapshot(snapshot: OBDSnapshot) -> int:
    _ensure_csv()
    rows_written = 0
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        for record in snapshot.records:
            writer.writerow({
                "timestamp": record.timestamp.isoformat(),
                "command": record.command,
                "value": record.value,
                "unit": record.unit,
            })
            rows_written += 1
    return rows_written
