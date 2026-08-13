#!/bin/bash
echo "=== 1. articles 目录内容（前40个文件） ==="
ls /usr/local/geometry-ai/articles/ | head -40
echo "文件总数: $(ls /usr/local/geometry-ai/articles/ | wc -l)"
echo ""
echo "=== 2. 检查旧体系特征（0.10/FSD/旧编号） ==="
ls /usr/local/geometry-ai/articles/ | grep -iE "0\.10|FSD|旧|legacy" | head -10 || echo "无 0.10/FSD 文件"
echo ""
echo "=== 3. 检查当前体系特征（0.0.0/7.x/10.x） ==="
ls /usr/local/geometry-ai/articles/ | grep -E "^0\.[0-9]|^7\.|^10\." | head -15
echo ""
echo "=== 4. admin_routes.py 中的 rebuild 端点 ==="
grep -nE "rebuild|reindex|re_embed|重建" /usr/local/geometry-ai/admin_routes.py | head -10
grep -nE "rebuild|reindex|re_embed|重建" /usr/local/geometry-ai/server.py | head -10
echo ""
echo "=== 5. start.py 启动逻辑（自动重建？） ==="
grep -nE "rebuild|reindex|sync|同步|articles" /usr/local/geometry-ai/start.py | head -15
echo ""
echo "=== 6. knowledge.py 中的向量化/重建函数 ==="
grep -nE "def .*rebuild|def .*reindex|def .*build|class .*Vector|def .*embed" /usr/local/geometry-ai/knowledge.py | head -15
echo ""
echo "=== 7. articles 最近修改时间 ==="
ls -lt /usr/local/geometry-ai/articles/ | head -8
echo ""
echo "=== 8. articles_old 内容（旧体系参考） ==="
ls /usr/local/geometry-ai/articles_old/ | head -10
