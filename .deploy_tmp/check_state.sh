#!/bin/bash
echo "=== chroma_db ==="
du -sh /usr/local/geometry-ai/chroma_db 2>/dev/null || echo "NO chroma_db"
ls /usr/local/geometry-ai/chroma_db 2>/dev/null | head -5
echo "=== .env keys ==="
grep -oE "^[A-Za-z_]+=" /usr/local/geometry-ai/.env 2>/dev/null
echo "=== service ==="
systemctl is-active geometry-ai
echo "=== recent log ==="
journalctl -u geometry-ai --no-pager -n 20 2>/dev/null | tail -20
