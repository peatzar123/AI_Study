import argparse
import json
import sys
from pathlib import Path
import pandas as pd
from pydantic import BaseModel


class BruteForceReport(BaseModel):
    flagged_users: list[str]
    related_controls: list[dict] = []

def load_controls(catalog_path: Path) -> list[dict]:
    """ดึง mapping ของเหตุการณ์ brute_force จากไฟล์ catalog (ไม่ hardcode)"""
    if not catalog_path.exists():
        return []
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    return data.get("brute_force", [])

def detect_bruteforce(
    csv_path: str | Path,
    count: int = 5,
    minutes: int = 10,
    catalog_path: Path = Path("catalog.json"),
) -> BruteForceReport:
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # 1. กรองเฉพาะ failure และเรียงเวลาของแต่ละ user จากน้อยไปมาก
    failures = df[df["result"] == "failure"].sort_values(["user", "timestamp"]).copy()

    # 2. คำนวณระยะห่างจากครั้งที่ i ถึงครั้งที่ i + (count - 1) เป็นหน่วยนาที
    failures["diff_minutes"] = (
        failures.groupby("user")["timestamp"].diff(count - 1).dt.total_seconds() / 60
    )

    # 3. คัดเฉพาะ user ที่ทำผิดครบตามจำนวนภายในเวลา <= minutes (เช่น <= 10 นาที)
    flagged = sorted(failures[failures["diff_minutes"] <= minutes]["user"].unique())

    # 4. ดึง ISO 27001 controls จากไฟล์ catalog เมื่อพบเหตุการณ์
    controls = load_controls(catalog_path) if flagged else []

    return BruteForceReport(
        flagged_users=flagged,
        related_controls=controls,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect brute-force login attempts")
    parser.add_argument("csv_path", help="Path to auth_log.csv")
    parser.add_argument("--count", type=int, default=5, help="Failure threshold count")
    parser.add_argument("--minutes", type=int, default=10, help="Time window in minutes")
    parser.add_argument("--catalog", default="catalog.json", help="Path to control catalog")
    args = parser.parse_args()

    report = detect_bruteforce(
        csv_path=args.csv_path,
        count=args.count,
        minutes=args.minutes,
        catalog_path=Path(args.catalog),
    )
    print(report.model_dump_json(indent=2))