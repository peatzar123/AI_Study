import pytest
from pydantic import ValidationError
from summarize_log import AuthSummary, summarize_auth_log


def test_normal_log_summary(tmp_path):
    """กรณีที่ 1: ทดสอบการสรุปยอดปกติ การเรียง IP ที่จำนวนเท่ากัน และการเติม 0 ให้ครบ 24 ชม."""
    csv_file = tmp_path / "auth.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        "2026-10-01T02:00:00,u1,10.0.0.9,failure\n"
        "2026-10-01T02:05:00,u1,10.0.0.5,failure\n"
        "2026-10-01T02:10:00,u2,10.0.0.5,failure\n"
        "2026-10-01T02:15:00,u3,10.0.0.9,failure\n"
        "2026-10-01T14:30:00,u1,10.0.0.1,success\n",
        encoding="utf-8",
    )

    res = summarize_auth_log(csv_file)

    assert res.failed_logins == 4
    # 10.0.0.5 กับ 10.0.0.9 มี 2 ครั้งเท่ากัน 10.0.0.5 ต้องขึ้นก่อนตามตัวอักษร
    assert [x.model_dump() for x in res.top_source_ips] == [
        {"ip": "10.0.0.5", "count": 2},
        {"ip": "10.0.0.9", "count": 2},
    ]
    assert len(res.hourly_failures) == 24
    assert res.hourly_failures["02"] == 4
    assert res.hourly_failures["14"] == 0


def test_no_failures_edge_case(tmp_path):
    """กรณีที่ 2: ทดสอบกรณีไม่มี failure เลย (มีแต่ success) ต้องไม่พังและได้ 0 ครบ 24 ชม."""
    csv_file = tmp_path / "clean.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        "2026-10-01T08:00:00,u1,10.0.0.1,success\n",
        encoding="utf-8",
    )

    res = summarize_auth_log(csv_file)

    assert res.failed_logins == 0
    assert res.top_source_ips == []
    assert len(res.hourly_failures) == 24
    assert all(v == 0 for v in res.hourly_failures.values())


def test_pydantic_schema_rejects_missing_hours():
    """กรณีที่ 3: ทดสอบว่า Pydantic ปฏิเสธข้อมูลทันทีหาก hourly_failures มีไม่ครบ 24 ชั่วโมง"""
    with pytest.raises(ValidationError):
        AuthSummary(
            failed_logins=1,
            top_source_ips=[{"ip": "10.0.0.1", "count": 1}],
            hourly_failures={"00": 1},  # ขาดชั่วโมง 01-23
        )