import argparse
import xml.etree.ElementTree as ET
from pydantic import BaseModel

RISKY_SERVICE = {'ftp', 'telnet', 'microsoft-ds', 'ms-wbt-server'}

class finding(BaseModel):
    host: str
    port: int
    service: str
    version: str

class nmap_parse_report(BaseModel):
    findings: list[finding] = []
    diff : dict[str, list[str]] = {"opened": [], "closed": []}
    risky: list[str] = []

def parse_nmap_xml(xml_file: str) -> nmap_parse_report:
    root = ET.parse(xml_file).getroot()
    result = []

    for host in root.findall('host'):
        ip_addr = host.find('address[@addrtype="ipv4"]').attrib["addr"]
        ports = host.find('ports')
        if ports is not None: # none คือ กรณีที่ไม่มี tag นี้
            for port in ports.findall('port'):
                if port.find("state") is None or port.find("state").attrib.get("state") != "open": continue
                port_id = int(port.attrib['portid'])
                service = port.find('service')
                if service is not None:
                    service_name = service.attrib.get('name', '') #ถ้าไม่เจอ name ให้คืนค่าว่าง
                    service_version = service.attrib.get('version', '')
                    service_product = service.attrib.get('product','')
                    result.append({
                        "host": ip_addr,
                        "port": port_id,
                        "service": service_name,
                        "version": f"{service_product} {service_version}".strip()
                    })
    return result
    #return nmap_parse_report(findings=findings_list)

# 2.3 เทียบผลสองรอบสแกนได้ว่า port ไหนเปิดใหม่หรือปิดไป
def compare_scan(before: list[dict], after: list[dict]) -> dict[str, list[str]]: #a, b
    before_port = {f"{item['host']}:{item['port']}" for item in before} #c
    after_port = {f"{item['host']}:{item['port']}" for item in after } #d
    return {
        "opened": sorted(after_port-before_port), #d-c
        "closed": sorted(before_port-after_port) #c-d
    }

def risk(after: list[dict]) -> list[str]: #ftp, telnet, microsoft-ds, ms-wbt-server
    return sorted(
        f"{item['host']}:{item['port']}" for item in after if item['service'] in RISKY_SERVICE
    )

# 3. บันทึกเป็นไฟล์ JSON ออกมา
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="โปรแกรมค้นหา port ที่เปิดอยู่และความเสี่ยง")
    parser.add_argument("xml_path1", help="Path to scan1.xml")
    parser.add_argument("xml_path2", help="Path to scan2.xml")
    args = parser.parse_args()
    nmap_before = parse_nmap_xml(args.xml_path1)
    nmap_after = parse_nmap_xml(args.xml_path2)

    report = nmap_parse_report(
        findings= nmap_after, 
        diff= compare_scan(nmap_before, nmap_after),
        risky = risk(nmap_after),
    )
    print(report.model_dump_json(indent=2))