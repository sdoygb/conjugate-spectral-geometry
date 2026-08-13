#!/bin/bash
echo "=== SERVICE STATUS ==="
systemctl status geometry-ai --no-pager 2>&1 | head -12
echo ""
echo "=== HEALTH ==="
curl -s --max-time 10 http://localhost:5000/health; echo ""
echo "=== VERSION ==="
cat /usr/local/geometry-ai/version.py 2>/dev/null
echo "=== ENV KEY NAMES ==="
grep -oE "^[A-Z_]+=" /usr/local/geometry-ai/.env 2>/dev/null
echo "=== ARTICLES ==="
echo -n "active: "; ls /usr/local/geometry-ai/articles 2>/dev/null | wc -l
echo -n "total md: "; find /usr/local/geometry-ai/articles -name "*.md" 2>/dev/null | wc -l
if [ -d /usr/local/geometry-ai/articles_old ]; then echo -n "old backup md: "; find /usr/local/geometry-ai/articles_old -name "*.md" | wc -l; fi
echo "=== RECENT LOG ==="
journalctl -u geometry-ai --no-pager -n 12 2>&1 | tail -12
