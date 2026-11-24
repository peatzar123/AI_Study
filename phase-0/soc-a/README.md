# Phase 0 (SOC - Option A): SIEM Authentication Log Summarizer

Pipeline สำหรับสรุปข้อมูลเหตุการณ์ Authentication Log ด้วย `pandas` และตรวจสอบความถูกต้องของโครงสร้างข้อมูลขาออก (JSON Schema) ด้วย `Pydantic`

## โครงสร้างไฟล์
- `summarize_log.py` — สคริปต์หลักสำหรับอ่านไฟล์ CSV, สรุปยอด Failed Login, Top 5 Source IPs, เหตุการณ์รายชั่วโมง 24 ชม. และ Validate ผ่าน Pydantic
- `test_summarize_log.py` — ชุดทดสอบ `pytest` (ครอบคลุมกรณีปกติ, กรณีไม่มี failure และกรณี Schema ไม่ครบ 24 ชั่วโมง)
- `sample_auth_log.csv` — ข้อมูล Log จำลองสำหรับทดสอบการทำงาน

## วิธีใช้งาน

### 1. ติดตั้งไลบรารีที่จำเป็น
```bash
pip install pandas pydantic pytest pytest-json-report

python summarize_log.py sample_auth_log.csv > output.json

python -m pytest -v

ตัวอย่างรูปแบบ .json
{
  "failed_logins": 8,
  "top_source_ips": [
    { "ip": "203.0.113.45", "count": 3 },
    { "ip": "192.0.2.10", "count": 2 }
  ],
  "hourly_failures": {
    "00": 3,
    "01": 0,
    "02": 2,
    "...": 0,
    "23": 1
  }
}
---

#### 4. คำสั่งส่งขึ้น GitHub (รันใน Git Bash ที่โฟลเดอร์ `AI_Study`)
```bash
git add .
git commit -m "phase 0 soc-a: add log summarizer, tests, and README"
git push