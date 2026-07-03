#!/bin/zsh
# ============================================================
# 几何论文章目录 — Git全自动维护脚本
# auto_git_maintain.sh
#
# 功能：
#   1. 自动检测 articles/ 目录下的文件变更（新增、修改、删除）
#   2. 自动更新 目录_总览与文件管理 中的版本号和时间戳
#   3. 自动生成规范的 commit message
#   4. 自动推送到远程仓库（可选）
#
# 用法：
#   ./scripts/auto_git_maintain.sh              # 仅检测并提交
#   ./scripts/auto_git_maintain.sh --push       # 检测、提交并推送
#   ./scripts/auto_git_maintain.sh --dry-run    # 只检测，不做任何修改
#   ./scripts/auto_git_maintain.sh --status     # 只显示状态
#
# 依赖：
#   - git, sed, awk, date (macOS/Unix)
# ============================================================

# ---------- 配置 ----------
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CATALOG_FILE="目录_总览与文件管理_CN_260626.6.md"
CATALOG_PATH="$BASE_DIR/articles/$CATALOG_FILE"
REMOTE_NAME="origin"
BRANCH_NAME="main"

# ---------- 函数 ----------
log_info()  { echo "[INFO]  $1"; }
log_warn()  { echo "[WARN]  $1"; }
log_error() { echo "[ERROR] $1"; }
log_step()  { echo ""; echo "━━━ $1 ━━━"; }

# 显示当前状态
show_status() {
    log_step "Git 仓库状态"
    cd "$BASE_DIR" || exit 1
    echo "  仓库路径: $BASE_DIR"
    echo "  当前分支: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "  最新提交: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo ""
    
    log_step "未提交的变更"
    local untracked=$(git status --short | wc -l | tr -d ' ')
    if [ "$untracked" -eq 0 ]; then
        echo "  ✅ 工作区干净，无未提交变更"
    else
        git status --short
    fi
    
    echo ""
    log_step "目录总纲文件状态"
    if [ -f "$CATALOG_PATH" ]; then
        echo "  路径: $CATALOG_PATH"
        echo "  大小: $(wc -c < "$CATALOG_PATH" | tr -d ' ') 字节"
        echo "  行数: $(wc -l < "$CATALOG_PATH" | tr -d ' ')"
        local tracked=$(cd "$BASE_DIR" && git ls-files --error-unmatch "articles/$CATALOG_FILE" 2>/dev/null && echo "yes" || echo "no")
        if [ "$tracked" = "yes" ]; then
            local diff=$(cd "$BASE_DIR" && git diff -- "articles/$CATALOG_FILE" | wc -l | tr -d ' ')
            if [ "$diff" -gt 0 ]; then
                echo "  状态: ⚠️ 有未提交的修改 ($diff 行变更)"
            else
                echo "  状态: ✅ 已跟踪且无未提交变更"
            fi
        else
            echo "  状态: ⚠️ 未被 Git 跟踪"
        fi
    else
        echo "  ❌ 文件不存在: $CATALOG_PATH"
    fi
}

# 检测文章目录变更
detect_article_changes() {
    log_step "检测文章目录变更"
    cd "$BASE_DIR" || exit 1
    
    # 获取 staged + unstaged 中 articles/ 的变更
    local changed_files=$(git status --short -- "articles/" 2>/dev/null)
    
    if [ -z "$changed_files" ]; then
        echo "  ℹ️  articles/ 目录无任何变更"
        return 1
    fi
    
    # 分类统计
    local added=0 modified=0 deleted=0 renamed=0
    while IFS= read -r line; do
        local status_code="${line:0:2}"
        case "$status_code" in
            "??"|"A ") added=$((added + 1)) ;;
            "M "|" M") modified=$((modified + 1)) ;;
            "D "|" D") deleted=$((deleted + 1)) ;;
            "R"*) renamed=$((renamed + 1)) ;;
        esac
    done <<< "$changed_files"
    
    echo "  新增: $added  修改: $modified  删除: $deleted  重命名: $renamed"
    echo ""
    echo "  变更清单:"
    echo "$changed_files" | while IFS= read -r line; do
        local filepath="${line:3}"
        echo "    [${line:0:2}] ${filepath#articles/}"
    done
    
    return 0
}

# 检查版本号是否需要更新
check_version() {
    local today=$(date +"%y%m%d")
    local current_version=$(grep -m1 '文件打包版本' "$CATALOG_PATH" 2>/dev/null | grep -oE '[0-9]{6}\.[0-9]+')
    
    if [ -n "$current_version" ]; then
        local version_date="${current_version%.*}"
        if [ "$version_date" = "$today" ]; then
            # 同一天，递增小版本号
            local minor="${current_version##*.}"
            minor=$((minor + 1))
            NEW_VERSION="${today}.${minor}"
            log_info "同一天打包: $current_version → $NEW_VERSION"
        else
            # 不同天，重置小版本号为1
            NEW_VERSION="${today}.1"
            log_info "新一天打包: $current_version → $NEW_VERSION"
        fi
    else
        NEW_VERSION="${today}.1"
        log_warn "未找到版本号，初始化: $NEW_VERSION"
    fi
}

# 更新目录总纲中的版本号和时间戳
update_catalog_version() {
    log_step "更新目录总纲版本号"
    
    if [ ! -f "$CATALOG_PATH" ]; then
        log_error "目录总纲文件不存在: $CATALOG_PATH"
        return 1
    fi
    
    # 备份
    local backup="${CATALOG_PATH}.bak"
    cp "$CATALOG_PATH" "$backup"
    
    # 1. 更新"文件打包版本"行
    sed -i '' "s/文件打包版本：[0-9]\{6\}\.[0-9]\+/文件打包版本：${NEW_VERSION}/" "$CATALOG_PATH"
    log_info "  文件打包版本 → ${NEW_VERSION}"
    
    # 2. 更新文件名示例中的版本号（目录_总览与文件管理_CN_YYMMDD.N.md）
    sed -i '' "s/目录_总览与文件管理_CN_[0-9]\{6\}\.[0-9]\+\.md/目录_总览与文件管理_CN_${NEW_VERSION}.md/" "$CATALOG_PATH"
    log_info "  自引用文件名版本 → ${NEW_VERSION}"
    
    # 3. 更新目录总纲文件名自身（保留原文件，只在内容中更新引用）
    #    文件本身的版本号在内容中更新，方便下次检测
    
    # 4. 如果是同一天：在已有版本更新日志中追加条目
    local today=$(date +"%Y%m%d")
    local version_entry="${NEW_VERSION//./.} 修订"
    
    if grep -q "^### ${today}" "$CATALOG_PATH" 2>/dev/null; then
        log_info "  今日已有版本日志条目，将在其下追加"
    fi
    
    echo ""
    log_info "  版本号已更新，旧版本备份至: ${CATALOG_PATH}.bak"
    return 0
}

# 生成规范的 commit message
generate_commit_message() {
    cd "$BASE_DIR" || exit 1
    
    # 统计变更详情
    local added_files=$(git status --short -- "articles/" | grep -E "^\?\?|^A " | wc -l | tr -d ' ')
    local modified_files=$(git status --short -- "articles/" | grep -E "^ M|^M " | wc -l | tr -d ' ')
    local deleted_files=$(git status --short -- "articles/" | grep -E "^ D|^D " | wc -l | tr -d ' ')
    
    # 获取变更的文章列表（排除目录总纲自身）
    local changed_articles=$(git status --short -- "articles/" | grep -v "目录_总览" | sed 's/.*articles\///' | head -5)
    local article_count=$(git status --short -- "articles/" | grep -v "目录_总览" | wc -l | tr -d ' ')
    
    # 构建 commit message
    local msg=""
    
    if git diff --cached --quiet 2>/dev/null; then
        # 无 staged 变更，使用所有变更
        if [ "$added_files" -gt 0 ]; then
            msg+="新增 ${added_files} 篇文章"
            [ "$modified_files" -gt 0 -o "$deleted_files" -gt 0 ] && msg+="；"
        fi
        if [ "$modified_files" -gt 0 ]; then
            msg+="修改 ${modified_files} 篇"
            [ "$deleted_files" -gt 0 ] && msg+="；"
        fi
        if [ "$deleted_files" -gt 0 ]; then
            msg+="删除 ${deleted_files} 篇"
        fi
    fi
    
    # 如果没有明确的变更描述，用通用描述
    if [ -z "$msg" ]; then
        msg="文章目录自动维护"
    fi
    
    # 添加版本号和文章数量信息
    local total_articles=$(ls "$BASE_DIR/articles/"*.md 2>/dev/null | grep -v "目录_总览" | wc -l | tr -d ' ')
    msg+=" | v${NEW_VERSION} | 共 ${total_articles} 篇文章"
    
    echo "$msg"
}

# 执行 Git 提交
do_commit() {
    log_step "执行 Git 提交"
    cd "$BASE_DIR" || exit 1
    
    # 1. 添加所有 articles/ 下的变更
    log_info "添加 articles/ 目录变更到暂存区..."
    git add -- "articles/"
    
    # 2. 如果有其他重要变更也添加（server.py, config.py等），但排除临时文件
    for extra_file in server.py config.py start.py tools.py knowledge.py; do
        if [ -f "$extra_file" ] && ! git diff --quiet -- "$extra_file" 2>/dev/null; then
            git add -- "$extra_file"
            log_info "  添加额外变更: $extra_file"
        fi
    done
    
    # 3. 检查是否有东西可提交
    if git diff --cached --quiet 2>/dev/null; then
        log_warn "没有需要提交的变更"
        return 1
    fi
    
    # 4. 生成 commit message
    local commit_msg=$(generate_commit_message)
    
    # 5. 提交
    git commit -m "$commit_msg"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_info "✅ 提交成功！"
        echo ""
        git log -1 --oneline
        return 0
    else
        log_error "提交失败（退出码: $exit_code）"
        return 1
    fi
}

# 推送到远程
do_push() {
    log_step "推送到远程仓库"
    cd "$BASE_DIR" || exit 1
    
    # 检查远程仓库是否存在
    local remote_exists=$(git remote -v 2>/dev/null | grep "$REMOTE_NAME" | head -1)
    if [ -z "$remote_exists" ]; then
        log_warn "远程仓库 '$REMOTE_NAME' 未配置，跳过推送"
        return 1
    fi
    
    log_info "正在推送到 $REMOTE_NAME/$BRANCH_NAME ..."
    git push "$REMOTE_NAME" "$BRANCH_NAME"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_info "✅ 推送成功！"
        return 0
    else
        log_error "推送失败（退出码: $exit_code）"
        return 1
    fi
}

# 清理备份文件
cleanup_backups() {
    local backup="${CATALOG_PATH}.bak"
    if [ -f "$backup" ]; then
        rm "$backup"
        log_info "已清理备份文件: ${backup}"
    fi
}

# ---------- 主流程 ----------
main() {
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║    几何论 · 文章目录 Git 自动维护工具       ║"
    echo "║          版本 1.0 | $(date '+%Y-%m-%d %H:%M')         ║"
    echo "╚══════════════════════════════════════════════╝"
    
    # 解析参数
    local do_push_flag=false
    local dry_run=false
    
    for arg in "$@"; do
        case "$arg" in
            --push)     do_push_flag=true ;;
            --dry-run)  dry_run=true ;;
            --status)   show_status; exit 0 ;;
            --help|-h)
                echo "用法: $0 [--push] [--dry-run] [--status] [--help]"
                echo ""
                echo "  (无参数)   检测变更并提交"
                echo "  --push     检测、提交并推送到远程"
                echo "  --dry-run  只检测变更，不实际执行任何写入操作"
                echo "  --status   显示仓库状态"
                echo "  --help     显示本帮助"
                exit 0
                ;;
            *)
                log_error "未知参数: $arg"
                exit 1
                ;;
        esac
    done
    
    # 检查是否在 git 仓库中
    cd "$BASE_DIR" || exit 1
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "当前目录不是 Git 仓库: $BASE_DIR"
        exit 1
    fi
    
    # 显示状态
    show_status
    
    # 检测文章变更
    if ! detect_article_changes; then
        log_info "articles/ 目录无变更，无需维护"
        exit 0
    fi
    
    if [ "$dry_run" = true ]; then
        echo ""
        log_info "🔍 Dry-Run 模式：检测完成，未做任何修改"
        exit 0
    fi
    
    # 确认执行
    echo ""
    echo -n "是否继续执行自动维护？(Y/n) "
    read -r confirm
    if [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
        echo "已取消"
        exit 0
    fi
    
    # 更新版本号
    check_version
    update_catalog_version
    
    # 执行提交
    if do_commit; then
        # 推送
        if [ "$do_push_flag" = true ]; then
            do_push
        fi
    fi
    
    # 清理
    cleanup_backups
    
    echo ""
    log_info "🎉 自动维护完成！"
    echo ""
    echo "  最新提交: $(git log -1 --oneline)"
    echo "  版本号:   ${NEW_VERSION}"
}

main "$@"