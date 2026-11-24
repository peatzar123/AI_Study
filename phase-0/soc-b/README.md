# Phase 0 (SOC - Option B): Brute-Force Detection & ISO/IEC 27001 Control Mapping

[ภาษาไทย](#ภาษาไทย) | [English](#english)

---

## ภาษาไทย

### ภาพรวมโปรเจกต์
สคริปต์ตรวจจับพฤติกรรมการโจมตีแบบ **Brute Force** จากไฟล์ Authentication Log (`CSV`) ด้วย `pandas` โดยวิเคราะห์ช่วงเวลาการล็อกอินที่ล้มเหลวสะสมตามเกณฑ์ที่กำหนด (ค่าเริ่มต้น: ล้มเหลวตั้งแต่ 5 ครั้งภายใน 10 นาทีต่อ 1 บัญชีผู้ใช้) พร้อมผูกเหตุการณ์เข้ากับ Control ของมาตรฐาน **ISO/IEC 27001:2022** จากไฟล์ Catalog ภายนอก และตรวจสอบความถูกต้องของข้อมูลขาออกด้วย **Pydantic**

### คุณสมบัติหลัก
- **วิเคราะห์ช่วงเวลาด้วย Sliding Window:** ใช้ `pandas` จัดกลุ่มตาม `user` เรียงลำดับเวลา และคำนวณระยะห่างระหว่างความล้มเหลวครั้งที่ $i$ ถึง $i + (\text{count} - 1)$
- **ปรับค่าเกณฑ์ได้ (Configurable Thresholds):** ตั้งค่าจำนวนครั้ง (`--count`) และกรอบเวลา (`--minutes`) ผ่าน Command-Line Arguments ได้โดยไม่ Hardcode ในโค้ด
- **External Control Catalog Mapping:** ดึงข้อมูลการจับคู่มาตรฐาน ISO/IEC 27001:2022 (`8.5 Secure authentication` และ `8.16 Monitoring activities`) จากไฟล์ `catalog.json`
- **Schema Validation 100%:** ตรวจสอบโครงสร้างและชนิดข้อมูล JSON ขาออกผ่านโมเดล `BruteForceReport` ของ Pydantic
- **Automated Testing:** มีชุดทดสอบ `pytest` ครอบคลุมกรณีขอบ (Boundary Cases: 9 นาที, 10 นาทีพอดี, 11 นาที), การปรับเปลี่ยนเกณฑ์ และการอ่านข้อมูลจาก Catalog

### โครงสร้างไฟล์
```text
phase-0/soc-b/
├── detect_bruteforce.py        # สคริปต์หลักสำหรับตรวจจับ Brute Force และValidate JSON
├── test_detect_bruteforce.py   # ชุดทดสอบ Unit Tests ด้วย pytest
├── catalog.json                # ไฟล์ mapping เหตุการณ์กับ ISO/IEC 27001:2022 Controls
└── README.md                   # เอกสารอธิบายการใช้งาน
```

### วิธีติดตั้งและใช้งาน

1. **ติดตั้งไลบรารีที่จำเป็น**
   ```bash
   python -m pip install pandas pydantic pytest pytest-json-report
   ```

2. **รันตรวจจับ Brute Force และส่งออกเป็นไฟล์ JSON**
   ```bash
   python detect_bruteforce.py auth_log.csv --count 5 --minutes 10 > output.json
   ```

3. **รันชุดทดสอบ (Unit Tests)**
   ```bash
   # รันดูผลบน Command Line
   python -m pytest -v

   # รันพร้อมสร้างรายงานผล JSON สำหรับระบบตรวจอัตโนมัติ / CI
   python -m pytest --json-report --json-report-file=report.json
   ```

---

## English

### Overview
A Python CLI pipeline built with `pandas` and `Pydantic` to detect **Brute-Force** authentication attempts from SIEM/authentication logs (`CSV`). By default, it flags user accounts experiencing 5 or more failed logins within a 10-minute sliding window, maps detected incidents to **ISO/IEC 27001:2022** controls via an external catalog file, and enforces strict JSON schema validation.

### Key Features
- **Sliding Window Analysis:** Groups authentication failures by `user`, sorts events chronologically, and computes exact time deltas in minutes between the $i$-th and $(i + \text{count} - 1)$-th failure.
- **Configurable Thresholds:** Accepts `--count`, `--minutes`, and `--catalog` via CLI flags without hardcoding detection rules.
- **External Control Mapping:** Dynamically loads **ISO/IEC 27001:2022** mappings (`8.5 Secure authentication` and `8.16 Monitoring activities`) from `catalog.json`.
- **Strict Pydantic Validation:** Validates output structure and data types via `BruteForceReport` prior to serialization.
- **Comprehensive Unit Tests:** Includes `pytest` test cases covering boundary conditions (9 min vs. exact 10 min vs. 11 min), custom thresholds, catalog lookups, and clean logs.

### Directory Structure
```text
phase-0/soc-b/
├── detect_bruteforce.py        # Main brute-force detection & Pydantic validation script
├── test_detect_bruteforce.py   # Pytest unit test suite
├── catalog.json                # External ISO/IEC 27001:2022 control catalog
└── README.md                   # Project documentation
```

### Installation & Usage

1. **Install Dependencies**
   ```bash
   python -m pip install pandas pydantic pytest pytest-json-report
   ```

2. **Run Brute-Force Detection**
   ```bash
   python detect_bruteforce.py auth_log.csv --count 5 --minutes 10 > output.json
   ```

3. **Run Unit Tests**
   ```bash
   # Run tests in terminal
   python -m pytest -v

   # Generate JSON test report for CI / automated grading
   python -m pytest --json-report --json-report-file=report.json
   ```

### Sample Output (`output.json`)
```json
{
  "flagged_users": [
    "krit",
    "noi"
  ],
  "related_controls": [
    {
      "standard": "ISO/IEC 27001:2022",
      "control_id": "8.5",
      "name": "Secure authentication"
    },
    {
      "standard": "ISO/IEC 27001:2022",
      "control_id": "8.16",
      "name": "Monitoring activities"
    }
  ]
}
```