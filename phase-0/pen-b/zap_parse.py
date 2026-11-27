import argparse
import sys
import json
from pydantic import BaseModel

class finding(BaseModel):
    plugin_id: str
    title: str          #alert 
    severity: str       #
    cwe: str            #cweid
    uri: str
    evidence: str = ''

class zap_parse_report(BaseModel):
    findings: list[finding] = []

class severity_map:
    mapping = {
            "0" : "Informational",
            "1" : "Low",
            "2" : "Medium",
            "3" : "High",
    }
    def __init__(self, riskcode:str|int):
        self.riskcode = str(riskcode)

    def zap_map(self) -> str:   
        if self.riskcode not in self.mapping:
            raise ValueError(f"Unknown riskcode: {self.riskcode}")
        return self.mapping[self.riskcode]
    
def parse_zap_json(json_file: str):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or "site" not in data or not isinstance(data["site"], list):
        raise ValueError("Invalid ZAP JSON: missing 'site' list")

    alerts = [
        alert
        for site in data["site"]
        if isinstance(site, dict)
        for alert in site.get("alerts", [])
    ]

    result = []
    for item in alerts:
        plugin_id = str(item.get('pluginid',""))
        title = str(item.get('alert', ""))
        severity = severity_map(item.get('riskcode', '0')).zap_map()
        cwe = str(item.get("cweid", ""))

        for ins in item.get("instances", []):
            result.append({
                'plugin_id': plugin_id,
                'title': title ,
                'severity': severity,
                'cwe': cwe,
                'uri': str(ins.get("uri","")),
                'evidence': str(ins.get("evidence","")),
            })
    return result

def compare_scan(before: list[dict], after: list[dict]):
    seen = set()
    merged_findings = []

    for item in before + after:
        key = (item["plugin_id"], item["uri"])
        if key not in seen:
            seen.add(key)
            merged_findings.append(item)
    return merged_findings


# 3. บันทึกเป็นไฟล์ JSON ออกมา
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    
    parser = argparse.ArgumentParser(description="โปรแกรมค้นหาความเสี่ยงจาก zap")
    parser.add_argument("zap_path1", help="Path to zap1.json")
    parser.add_argument("zap_path2", help="Path to zap2.json")
    args = parser.parse_args()

    try:
        zap_before = parse_zap_json(args.zap_path1)
        zap_after = parse_zap_json(args.zap_path2)

        report = zap_parse_report(
            findings=compare_scan(zap_before, zap_after),
        )
        print(report.model_dump_json(indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)