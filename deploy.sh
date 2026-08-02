#!/bin/bash
# ============================================
# GeometryAI GitHub Pages 部署脚本
# 用法: bash deploy.sh
# 注意: 请先修改下面的 GITHUB_REPO 变量
# ============================================

# 你的 GitHub 仓库地址（替换为你的实际仓库）
GITHUB_REPO="https://github.com/sdoygb/conjugate-spectral-geometry.git"
# 分支名
BRANCH="gh-pages"

echo "=== 部署到 GitHub Pages ==="
echo "目标仓库: $GITHUB_REPO"
echo "目标分支: $BRANCH"
echo ""

cd "$(dirname "$0")"

# 初始化 git 仓库（如果尚未初始化）
if [ ! -d ".git" ]; then
    git init
    echo "  ✓ Git 仓库已初始化"
fi

# 添加所有文件
git add -A
echo "  ✓ 文件已添加"

# 提交
git commit -m "Deploy to GitHub Pages $(date +'%Y-%m-%d %H:%M')"
echo "  ✓ 已提交"

# 推送到 gh-pages 分支
git push -f "$GITHUB_REPO" HEAD:"$BRANCH"
echo "  ✓ 已推送到 $BRANCH 分支"
echo ""
echo "=== 部署完成！==="
echo "网站地址: https://sdoygb.github.io/conjugate-spectral-geometry/"
echo ""
echo "注意: 首次部署后，请在 GitHub 仓库 Settings → Pages 中确认："
echo "  - Source 设置为 'Deploy from a branch'"
echo "  - Branch 选择 '$BRANCH'"
echo "  - 路径选择 '/ (root)'"
