import argparse
import json
import sys
from schemas import ControlCatalog


def lookup_control_name(catalog: ControlCatalog, ref: str) -> str:
    if ":" not in ref:
        return ""
    std, cid = ref.split(":", 1)
    source = getattr(catalog, std.lower(), [])
    for item in source:
        if item.id == cid:
            return item.name
    return ""


def search_control(catalog: ControlCatalog, target: str):
    target_clean = target.strip().lower()
    if ":" not in target_clean:
        print(f"รูปแบบรหัสไม่ถูกต้อง: '{target}' (ตัวอย่างที่ถูก: iso27001:5.34 หรือ pdpa:37)")
        sys.exit(1)

    std, cid = target_clean.split(":", 1)
    items = getattr(catalog, std, None)
    if items is None:
        print(f"ไม่พบมาตรฐาน '{std}' ใน catalog (รองรับ: iso27001, iso42001, pdpa)")
        sys.exit(1)

    found_item = next((x for x in items if x.id.lower() == cid), None)
    if not found_item:
        print(f"ไม่พบรหัส '{cid}' ในมาตรฐาน {std}")
        sys.exit(1)

    theme_text = f" (Theme: {found_item.theme})" if hasattr(found_item, "theme") else ""
    print(f"[{std}:{found_item.id}] {found_item.name}{theme_text}")
    print(f"คำอธิบาย: {found_item.description}\n")

    related = [
        m for m in catalog.mappings
        if m.from_ref.lower() == target_clean or m.to_ref.lower() == target_clean
    ]

    if not related:
        print("ไม่พบความเชื่อมโยงข้ามมาตรฐานโดยตรงสำหรับข้อนี้")
        return

    print(f"ความเชื่อมโยงข้ามมาตรฐานที่พบ ({len(related)} รายการ):")
    for idx, m in enumerate(related, 1):
        other_ref = m.to_ref if m.from_ref.lower() == target_clean else m.from_ref
        other_name = lookup_control_name(catalog, other_ref)
        name_label = f" ({other_name})" if other_name else ""
        print(f"{idx}. {std}:{found_item.id} <--> {other_ref}{name_label}")
        print(f"   เหตุผล: {m.reason}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Validate and search cross-standard control catalog")
    parser.add_argument("--validate", metavar="FILE", help="Validate a catalog JSON file with Pydantic")
    parser.add_argument("--control", metavar="REF", help="Search cross-mappings by control ref (e.g., iso27001:5.34)")
    parser.add_argument("--file", default="catalog.json", help="Path to catalog.json (default: catalog.json)")
    args = parser.parse_args()

    if not args.validate and not args.control:
        parser.print_help()
        sys.exit(1)

    catalog_path = args.validate if args.validate else args.file

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = ControlCatalog.model_validate(json.load(f))
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)

    if args.validate:
        print(f"✓ Validation passed: {catalog_path}")
        print(f"  - Versions: {' | '.join(catalog.versions.values())}")
        print(f"  - ISO 27001: {len(catalog.iso27001)} controls")
        print(f"  - ISO 42001: {len(catalog.iso42001)} controls")
        print(f"  - PDPA: {len(catalog.pdpa)} sections")
        print(f"  - Cross-mappings: {len(catalog.mappings)} pairs")

    if args.control:
        search_control(catalog, args.control)