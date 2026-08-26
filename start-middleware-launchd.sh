#!/bin/bash
echo "[LAUNCHD-START] $(date)" >> /tmp/geometryai_launchd_debug.log
unset PYTHONHOME PYTHONPATH
cd /Users/oygb/Downloads/GeometryAI-Mac-Build/app
echo "[LAUNCHD-CD] done" >> /tmp/geometryai_launchd_debug.log
exec /usr/local/bin/python3.11 server.py 2>&1
