import sys
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class SourceIPStat(BaseModel):
    ip: str
    count: int = Field(ge=0)


class AuthSummary(BaseModel):
    failed_logins: int = Field(ge=0)
    top_source_ips: list[SourceIPStat] = Field(max_length=5)
    hourly_failures: dict[str, int]

    @field_validator("hourly_failures")
    @classmethod
    def validate_24_hours(cls, v: dict[str, int]) -> dict[str, int]:
        expected_keys = {f"{h:02d}" for h in range(24)}
        if set(v.keys()) != expected_keys:
            raise ValueError("hourly_failures must contain all 24 hours ('00' to '23')")
        if any(count < 0 for count in v.values()):
            raise ValueError("Failure counts cannot be negative")
        return v


def summarize_auth_log(csv_path: str | Path) -> AuthSummary:
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # กรองเฉพาะเหตุการณ์ที่ login ไม่สำเร็จ
    failures = df[df["result"] == "failure"].copy()

    # 1. ยอดรวม failed logins ทั้งหมด
    failed_logins = int(len(failures))

    # 2. Top 5 Source IPs (เรียง count มาก->น้อย, ถ้าเท่ากันเรียง ip น้อย->มาก)
    top_source_ips = (
        failures.groupby("src_ip")
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "src_ip"], ascending=[False, True])
        .head(5)
        .rename(columns={"src_ip": "ip"})
        .to_dict(orient="records")
    )

    # 3. เหตุการณ์รายชั่วโมงครบ 00-23 (ชั่วโมงที่ไม่มีให้เป็น 0)
    hourly_series = (
        failures.groupby(failures["timestamp"].dt.hour)
        .size()
        .reindex(range(24), fill_value=0)
    )
    hourly_series.index = hourly_series.index.map(lambda h: f"{h:02d}")
    hourly_failures = hourly_series.astype(int).to_dict()

    # Validate ผ่าน Pydantic Schema ก่อนส่งออก
    return AuthSummary(
        failed_logins=failed_logins,
        top_source_ips=top_source_ips,
        hourly_failures=hourly_failures,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <path_to_auth_log.csv>", file=sys.stderr)
        sys.exit(1)

    summary = summarize_auth_log(sys.argv[1])
    print(summary.model_dump_json(indent=2))