#!/bin/bash
echo "=== 1. /v1/vector/rebuild 代码（860-960行） ==="
sed -n '860,960p' /usr/local/geometry-ai/admin_routes.py
echo ""
echo "=== 2. /v1/index/rebuild 代码（595-680行） ==="
sed -n '595,680p' /usr/local/geometry-ai/admin_routes.py
