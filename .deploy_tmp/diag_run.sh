#!/bin/bash
cd /usr/local/geometry-ai && echo 'ab640815.' | sudo -S /usr/local/geometry-ai/venv/bin/python3 /tmp/diag_kb.py 2>&1 | grep -vE "telemetry|HTTP Request" | head -30
