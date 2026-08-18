#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mobile Instant Link Launcher
Generates a public HTTPS URL + QR Code for instant mobile access.
"""

import subprocess
import time
import re
import sys
import os

print("=" * 60)
print("  🚀 AI Multi-Agent Mobile Launcher")
print("  스마트폰 접속용 인터넷 URL 및 QR 코드를 생성합니다...")
print("=" * 60)
print()

# 1. Start Streamlit in background
streamlit_proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless=true", "--server.port=8501"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print("✔ Streamlit 웹 서버 시작됨 (Port 8501)")
time.sleep(2)

# 2. Start SSH Tunnel to localhost.run
print("✔ 모바일 전용 인터넷 주소(HTTPS) 연결 중...")
print()

ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8501", "nokey@localhost.run"]

try:
    ssh_proc = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    url_found = False
    for line in iter(ssh_proc.stdout.readline, ''):
        print(line, end='')
        match = re.search(r'(https://[a-zA-Z0-9\-\.]+\.lhr\.life)', line)
        if match and not url_found:
            url_found = True
            mobile_url = match.group(1)
            print()
            print("=" * 60)
            print("  📱 스마트폰에서 아래 인터넷 주소로 바로 접속하세요!")
            print(f"  👉 [ {mobile_url} ]")
            print("=" * 60)
            print()

except KeyboardInterrupt:
    print("\n종료합니다...")
finally:
    streamlit_proc.terminate()
