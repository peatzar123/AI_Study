#!/usr/bin/env python3
"""รันชุดทดสอบกรณีแปลก (edge cases) แล้วรวมผลเป็น edge_results.json

วิธีใช้ (เปลี่ยนนามสกุลไฟล์นี้เป็น .py ก่อน):
  python run_edge_tests.py edge_cases_authA.json "python summarize.py {in}"
  python run_edge_tests.py edge_cases_nmapA.json "python nmap_parse.py {in} {in2}"

{in} = ไฟล์ input แรกของแต่ละเคส, {in2} = ไฟล์ที่สอง (ถ้ามี)
กติกา: ถ้า input ใช้ไม่ได้ โปรแกรมต้องพิมพ์ {"error": "..."} ออก stdout และจบด้วย exit code ที่ไม่ใช่ 0
"""
import json, os, shlex, subprocess, sys, tempfile

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        bundle = json.load(f)
    template = shlex.split(sys.argv[2], posix=(os.name != "nt"))
    out = {"suite": bundle["suite"], "command": sys.argv[2], "results": {}}
    with tempfile.TemporaryDirectory() as d:
        for case in bundle["cases"]:
            paths = []
            for name, content in case["files"]:
                p = os.path.join(d, case["id"] + "_" + name)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(content)
                paths.append(p)
            second = paths[1] if len(paths) > 1 else ""
            args = [a.replace("{in2}", second).replace("{in}", paths[0]) for a in template]
            try:
                r = subprocess.run(args, capture_output=True, timeout=60)  # ไม่ใช้ shell=True
                res = {"exit_code": r.returncode,
                       "stdout": r.stdout.decode("utf-8", "replace")[-20000:],
                       "stderr": r.stderr.decode("utf-8", "replace")[-4000:]}
            except subprocess.TimeoutExpired:
                res = {"exit_code": None, "stdout": "", "stderr": "TIMEOUT (เกิน 60 วินาที)"}
            except FileNotFoundError as e:
                res = {"exit_code": None, "stdout": "", "stderr": "เรียกคำสั่งไม่ได้: " + str(e)}
            out["results"][case["id"]] = res
            print("[" + case["id"] + "] " + case["title"] + " -> exit " + str(res["exit_code"]))
    with open("edge_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("บันทึกผลที่ edge_results.json แล้ว นำไปอัปโหลดในหน้าแผนได้เลย")

if __name__ == "__main__":
    main()
