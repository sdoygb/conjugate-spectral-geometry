#!/bin/bash
echo "=== WHOAMI ==="; whoami; id
echo "=== HOST ==="; hostname; uname -a
echo "=== OS ==="; cat /etc/os-release | head -3
echo "=== PYTHON ==="; python3 --version 2>&1
echo "=== DISK ==="; df -h / | tail -1
echo "=== EXISTING INSTALL ==="; ls -la /opt/geometry-ai 2>&1 | head -5
echo "=== SUDO CHECK ==="
sudo -n true 2>&1 && echo "SUDO_NOPASS_OK" || echo "SUDO_NEEDS_PASS"
echo "=== MEM ==="; free -h | head -2
