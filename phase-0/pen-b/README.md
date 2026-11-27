# Phase 0 — Pentest (แบบ B): แปลงรายงาน OWASP ZAP เข้าสู่ Schema กลาง

## ภาพรวม
สคริปต์สำหรับรวมและแปลงรายงานช่องโหว่จาก OWASP ZAP หลายไฟล์ให้เป็น JSON Schema กลางของแพลตฟอร์ม เพื่อให้สามารถนำไปวิเคราะห์ร่วมกับผลสแกนจากเครื่องมืออื่นได้ โดยมีคลาส `severity_map` สำหรับแปลงระดับความรุนแรง การแตกข้อมูลระดับ `instances[]` การตัดรายการซ้ำซ้อน การรองรับข้อความภาษาไทย (UTF-8) การจัดการข้อผิดพลาดอย่างปลอดภัย (Graceful Error Handling) และชุดทดสอบอัตโนมัติครอบคลุมทั้ง 8 กรณี (`Z1`–`Z8`)

## โครงสร้างไฟล์
```text
phase-0/pen-b/
├── zap_parse.py              # สคริปต์หลักสำหรับแปลงและรวมรายงาน OWASP ZAP
├── zap_report1.json          # ไฟล์รายงาน ZAP ตัวอย่างที่ 1
├── zap_report2.json          # ไฟล์รายงาน ZAP ตัวอย่างที่ 2
├── output.json               # ผลลัพธ์ JSON ที่รวมและตัดรายการซ้ำแล้ว
├── edge_cases_zapB.json      # ชุดข้อมูลทดสอบ Edge Cases 8 เคส (Z1–Z8)
├── run_edge_tests.py         # สคริปต์รันชุดทดสอบอัตโนมัติ
├── edge_results.json         # ผลลัพธ์การรันทดสอบ Edge Cases
└── README.md
```

## ตาราง Mapping Severity (OWASP ZAP `riskcode` → Schema กลาง)
ระบบแปลงรหัสความรุนแรง (`riskcode`) จากรายงานของ OWASP ZAP เข้าสู่ฟิลด์ `severity` ใน Schema กลางตามตารางด้านล่าง (รองรับทั้งค่าชนิด `str` และ `int` และตัดส่วนระดับความมั่นใจในวงเล็บของ `riskdesc` ออก):

| ZAP `riskcode` | ความหมายใน ZAP (`riskdesc`) | ค่าใน Schema กลาง (`severity`) |
| :---: | :--- | :--- |
| `"3"` / `3` | High | `"High"` |
| `"2"` / `2` | Medium | `"Medium"` |
| `"1"` / `1` | Low | `"Low"` |
| `"0"` / `0` | Informational | `"Informational"` |

## การติดตั้งและวิธีรันใช้งาน
```bash
# ติดตั้งไลบรารีที่จำเป็น
pip install pydantic

# 1. รันรวมรายงาน ZAP 2 ไฟล์และส่งออกเป็น output.json
python zap_parse.py zap_report1.json zap_report2.json > output.json

# 2. รันชุดทดสอบ Edge Cases ทั้ง 8 เคส (Z1–Z8) เพื่อสร้าง edge_results.json
python run_edge_tests.py edge_cases_zapB.json "python zap_parse.py {in} {in2}"
```

## รูปแบบ Output และ Error Handling

### 1. กรณีประมวลผลสำเร็จ (`output.json`)
แตกทุกรายการใน `instances[]` ออกเป็น 1 finding แยกกัน ตัดรายการซ้ำข้ามไฟล์ด้วยคู่ `(plugin_id, uri)` และยังคงข้อมูล `evidence` ดิบไว้ครบถ้วน:
```json
{
  "findings": [
    {
      "plugin_id": "40012",
      "title": "Cross Site Scripting (Reflected)",
      "severity": "High",
      "cwe": "79",
      "uri": "http://lab.local/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E",
      "evidence": "<script>alert(1)</script>"
    }
  ]
}
```

### 2. กรณีไฟล์ Input ไม่สมบูรณ์หรือผิดโครงสร้าง (Error Handling)
หากไฟล์ JSON เสียหาย อ่านไม่ได้ หรือไม่มีโครงสร้างคีย์ `site` โปรแกรมจะไม่แสดง Traceback (ไม่ crash) แต่จะส่งออก JSON ข้อความผิดพลาดทาง `stdout` และจบการทำงานด้วย `exit code 1`:
```json
{
  "error": "Invalid ZAP JSON: missing 'site' list"
}
```

## รายละเอียดชุดทดสอบ Edge Cases (`Z1`–`Z8`)
| รหัสเคส | หัวข้อการทดสอบ | เงื่อนไขและผลลัพธ์ที่คาดหวัง |
| :---: | :--- | :--- |
| **Z1** | ข้อมูลปกติ | แปลง alert ระดับ High 1 รายการได้อย่างถูกต้อง |
| **Z2** | `riskcode` เป็นตัวเลข (`int`) | รองรับ `riskcode` ที่เป็นตัวเลข `3` และ `1` แทนข้อความ `"3"` และ `"1"` |
| **Z3** | `alert` ที่ `instances` ว่าง (`[]`) | ข้าม alert ที่ไม่มี instance โดยไม่เกิดรายการว่างหรือ error |
| **Z4** | `instance` ไม่มีคีย์ `evidence` | กำหนดค่าเริ่มต้นของ `evidence` เป็นข้อความว่าง `""` |
| **Z5** | รายการซ้ำข้ามสองรายงาน | ตัดรายการซ้ำด้วยคู่ `(plugin_id, uri)` ให้เหลือเพียง 1 finding |
| **Z6** | ข้อความภาษาไทย (UTF-8) | แสดงผลภาษาไทยตรงตามต้นฉบับ ไม่เพี้ยนเป็น `\u0e23...` หรือ mojibake |
| **Z7** | JSON ไม่สมบูรณ์ | ตอบ `{"error": "..."}` ทาง stdout และจบด้วย exit code != 0 โดยไม่ crash |
| **Z8** | JSON ไม่มีคีย์ `site` | ตอบ `{"error": "..."}` ทาง stdout และจบด้วย exit code != 0 โดยไม่ crash |
