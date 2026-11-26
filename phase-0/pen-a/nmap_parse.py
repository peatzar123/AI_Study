import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pydantic import BaseModel

class nmap_parse_report(BaseModel):
    findings: list[finding] = []
    diff : dict[str, list[str]] = {"opened": [], "closed": []}
    risky: list[str] = []

class finding(BaseModel):
    host: str
    port: int
    service: str
    version: str

def parse_nmap_xml(xml_file: str) -> nmap_parse_report:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    result = []
    for host in root.findall('host'):
        ip_addr = host.find('address').attrib['addr']
        ports = host.find('ports')
        if ports is not None: # none คือ กรณีที่ไม่มี tag นี้
            for port in ports.findall('port'):
                port_id = int(port.attrib['portid'])
                state = port.find('state').attrib['state']
                service = port.find('service')
                if service is not None:
                    service_name = service.attrib.get('name', '') #ถ้าไม่เจอ name ให้คืนค่าว่าง
                    service_version = service.attrib.get('version', '')
                    service_product = service.attrib.get('product','')
                    result.append({
                        "host": ip_addr,
                        "port": port_id,
                        "state": state,
                        "service": service_name,
                        "version": service_product + ' '+ service_version
                    })
    return result
    #return nmap_parse_report(findings=findings_list)

# 2.3 เทียบผลสองรอบสแกนได้ว่า port ไหนเปิดใหม่หรือปิดไป
def compare_scan(before, after): #a, b
    before_port = {f"{item['host']}:{item['port']}" for item in before if item.get("state", "open") == "open"} #c
    after_port = {f"{item['host']}:{item['port']}" for item in after if item.get("state", "open") == "open"} #d
    return {
        "opened": sorted(after_port-before_port), #d-c
        "closed": sorted(before_port-after_port) #c-d
    }

def risk(after): #ftp, telnet, microsoft-ds, ms-wbt-server
    risk_ports = ['21', '23', '445', '3389']
    risky = []
    after_risk = {f"{item['host']}:{item['port']}" for item in after if item.get("state", "open") == "open"} #d
    for risk_port in after_risk:
        if risk_port.split(':')[1] in risk_ports:
            risky.append(risk_port)
    return sorted(risky)

def finding2(after):
    return [
        {'host':item['host'], 
        'port':int(item['port']),
        'service': item['service'],
        'version': item['version']} 
        for item in after if item.get("state", "open") == "open"]
# 3. บันทึกเป็นไฟล์ JSON ออกมา
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="โปรแกรมค้นหา port ที่เปิดอยู่และความเสี่ยง")
    parser.add_argument("xml_path1", help="Path to scan1.xml")
    parser.add_argument("xml_path2", help="Path to scan2.xml")
    args = parser.parse_args()
    nmap_before = parse_nmap_xml(sys.argv[1])
    nmap_after = parse_nmap_xml(sys.argv[2])

    report = nmap_parse_report(
        findings= finding2(nmap_after), 
        diff= compare_scan(nmap_before, nmap_after),
        risky = risk(nmap_after),
    )
    print(report.model_dump_json(indent=2))