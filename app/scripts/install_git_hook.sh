#!/bin/zsh
# ============================================================
# 安装 Git pre-commit hook - 自动维护目录总纲版本号
# ============================================================

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_DIR="$BASE_DIR/.git/hooks"
HOOK_FILE="$HOOK_DIR/pre-commit"

# 检测是否在 Git 仓库中
if [ ! -d "$BASE_DIR/.git" ]; then
    echo "[ERROR] 当前目录不是 Git 仓库: $BASE_DIR"
    exit 1
fi

# 创建 hook 文件
cat > "$HOOK_FILE" << 'HOOKEOF'
#!/bin/zsh
# ============================================================
# Git Pre-Commit Hook — 自动维护目录总纲版本号
# 安装路径: .git/hooks/pre-commit
# ============================================================

BASE_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
CATALOG_FILE="目录_总览与文件管理_CN_260626.6.md"
CATALOG_PATH="$BASE_DIR/articles/$CATALOG_FILE"

# 只在 articles/ 目录有变更时执行
CHANGED=$(git status --short -- "articles/" 2>/dev/null)
if [ -z "$CHANGED" ]; then
    exit 0
fi

echo ""
echo "━━━ Git Pre-Commit Hook: 自动维护目录总纲 ━━━"
echo ""

# 1. 检测当前版本号
CURRENT_VERSION=$(grep -m1 '文件打包版本' "$CATALOG_PATH" 2>/dev/null | grep -oE '[0-9]{6}\.[0-9]+')
TODAY=$(date +"%y%m%d")

if [ -n "$CURRENT_VERSION" ]; then
    VERSION_DATE="${CURRENT_VERSION%.*}"
    MINOR="${CURRENT_VERSION##*.}"
    if [ "$VERSION_DATE" = "$TODAY" ]; then
        MINOR=$((MINOR + 1))
        NEW_VERSION="${TODAY}.${MINOR}"
    else
        NEW_VERSION="${TODAY}.1"
    fi
else
    NEW_VERSION="${TODAY}.1"
fi

# 2. 备份
cp "$CATALOG_PATH" "${CATALOG_PATH}.bak"

# 3. 更新版本号
sed -i '' "s/文件打包版本：[0-9]\{6\}\.[0-9]\+/文件打包版本：${NEW_VERSION}/" "$CATALOG_PATH"
sed -i '' "s/目录_总览与文件管理_CN_[0-9]\{6\}\.[0-9]\+\.md/目录_总览与文件管理_CN_${NEW_VERSION}.md/" "$CATALOG_PATH"

# 4. 将目录总纲的变更加入本次提交
git add -- "articles/$CATALOG_FILE"

echo "  ✅ 目录总纲版本号自动更新: ${CURRENT_VERSION:-未知} → ${NEW_VERSION}"
echo "  📝 已加入本次提交"

# 清理备份
rm -f "${CATALOG_PATH}.bak"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
HOOKEOF

chmod +x "$HOOK_FILE"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║  ✅ Git Hook 安装完成！               ║"
echo "╠═══════════════════════════════════════╣"
echo "║  路径: $HOOK_FILE"
echo "║  功能: 每次 git commit 时自动更新     ║"
echo "║         目录总纲版本号                 ║"
echo "║                                       ║"
echo "║  如需卸载: rm $HOOK_FILE  ║"
echo "╚═══════════════════════════════════════╝"
echo ""