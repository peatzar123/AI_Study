import json
import pytest
from detect_bruteforce import detect_bruteforce


def test_boundary_cases_and_sorting(tmp_path):
    """กรณีที่ 1: ทดสอบกรณีขอบ 9 นาที / 10 นาทีพอดี / 11 นาที และข้อมูลที่เวลาสลับลำดับ"""
    csv_file = tmp_path / "auth.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        # user_a: พลาด 5 ครั้ง ห่าง 9 นาที (จงใจใส่เวลาสลับบรรทัด) -> ต้องถูก flag
        "2026-10-01T02:09:00,user_a,10.0.0.1,failure\n"
        "2026-10-01T02:00:00,user_a,10.0.0.1,failure\n"
        "2026-10-01T02:04:00,user_a,10.0.0.1,failure\n"
        "2026-10-01T02:02:00,user_a,10.0.0.1,failure\n"
        "2026-10-01T02:06:00,user_a,10.0.0.1,failure\n"
        # user_exact: พลาด 5 ครั้ง ห่าง 10 นาทีพอดี (600 วินาที) -> ต้องถูก flag
        "2026-10-01T03:00:00,user_exact,10.0.0.2,failure\n"
        "2026-10-01T03:02:30,user_exact,10.0.0.2,failure\n"
        "2026-10-01T03:05:00,user_exact,10.0.0.2,failure\n"
        "2026-10-01T03:07:30,user_exact,10.0.0.2,failure\n"
        "2026-10-01T03:10:00,user_exact,10.0.0.2,failure\n"
        # user_b: พลาด 5 ครั้ง ห่าง 11 นาที -> ต้องไม่ถูก flag
        "2026-10-01T04:00:00,user_b,10.0.0.3,failure\n"
        "2026-10-01T04:03:00,user_b,10.0.0.3,failure\n"
        "2026-10-01T04:06:00,user_b,10.0.0.3,failure\n"
        "2026-10-01T04:09:00,user_b,10.0.0.3,failure\n"
        "2026-10-01T04:11:00,user_b,10.0.0.3,failure\n"
        # user_mixed: พลาด 4 ครั้ง + สำเร็จ 1 ครั้ง -> ต้องไม่ถูก flag
        "2026-10-01T05:00:00,user_mixed,10.0.0.4,failure\n"
        "2026-10-01T05:01:00,user_mixed,10.0.0.4,failure\n"
        "2026-10-01T05:02:00,user_mixed,10.0.0.4,success\n"
        "2026-10-01T05:03:00,user_mixed,10.0.0.4,failure\n"
        "2026-10-01T05:04:00,user_mixed,10.0.0.4,failure\n",
        encoding="utf-8",
    )

    res = detect_bruteforce(csv_file, count=5, minutes=10)

    assert res.flagged_users == ["user_a", "user_exact"]


def test_configurable_thresholds(tmp_path):
    """กรณีที่ 2: ทดสอบปรับเปลี่ยนเกณฑ์จำนวนครั้งและช่วงเวลาผ่านพารามิเตอร์ (ไม่ hardcode)"""
    csv_file = tmp_path / "custom_threshold.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        "2026-10-01T08:00:00,krit,10.0.0.5,failure\n"
        "2026-10-01T08:02:00,krit,10.0.0.5,failure\n"
        "2026-10-01T08:04:00,krit,10.0.0.5,failure\n",
        encoding="utf-8",
    )

    # ถ้าใช้เกณฑ์ปกติ (5 ครั้งใน 10 นาที) ต้องไม่โดนจับ
    res_default = detect_bruteforce(csv_file, count=5, minutes=10)
    assert res_default.flagged_users == []

    # ถ้าปรับเกณฑ์เป็น 3 ครั้งใน 5 นาที ต้องโดนจับทันที
    res_strict = detect_bruteforce(csv_file, count=3, minutes=5)
    assert res_strict.flagged_users == ["krit"]


def test_catalog_mapping_from_external_file(tmp_path):
    """กรณีที่ 3: ทดสอบว่า mapping กับ ISO 27001 ดึงมาจากไฟล์ catalog.json จริง"""
    csv_file = tmp_path / "attack.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        "2026-10-01T01:00:00,somchai,10.0.0.9,failure\n"
        "2026-10-01T01:01:00,somchai,10.0.0.9,failure\n"
        "2026-10-01T01:02:00,somchai,10.0.0.9,failure\n",
        encoding="utf-8",
    )

    custom_catalog = tmp_path / "custom_catalog.json"
    custom_catalog.write_text(
        json.dumps(
            {
                "brute_force": [
                    {"control_id": "8.5", "name": "Secure authentication"},
                    {"control_id": "8.16", "name": "Monitoring activities"},
                ]
            }
        ),
        encoding="utf-8",
    )

    res = detect_bruteforce(csv_file, count=3, minutes=5, catalog_path=custom_catalog)

    assert res.flagged_users == ["somchai"]
    assert len(res.related_controls) == 2
    assert res.related_controls[0]["control_id"] == "8.5"
    assert res.related_controls[1]["control_id"] == "8.16"


def test_no_brute_force_returns_empty(tmp_path):
    """กรณีที่ 4: ทดสอบกรณีไม่พบพฤติกรรม Brute Force เลย"""
    csv_file = tmp_path / "normal.csv"
    csv_file.write_text(
        "timestamp,user,src_ip,result\n"
        "2026-10-01T09:00:00,anan,10.0.0.10,success\n"
        "2026-10-01T09:30:00,anan,10.0.0.10,failure\n",
        encoding="utf-8",
    )

    res = detect_bruteforce(csv_file)

    assert res.flagged_users == []
    assert res.related_controls == []


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-v", __file__]))