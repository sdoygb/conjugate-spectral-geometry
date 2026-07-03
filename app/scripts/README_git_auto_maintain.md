# 几何论文章目录 — Git 全自动维护方案

## 方案概览

提供两套自动化维护方案：

| 方案 | 文件 | 触发方式 | 适用场景 |
|------|------|----------|----------|
| **方案A：手动脚本** | `scripts/auto_git_maintain.sh` | 命令行调用 | 主动批量维护 |
| **方案B：Git Hook** | `.git/hooks/pre-commit` | 每次 `git commit` 自动触发 | 每次提交自动更新版本号 |

---

## 方案A：手动脚本

### 基本用法

```bash
# 1. 查看当前状态（只读）
./scripts/auto_git_maintain.sh --status

# 2. 检测变更并提交（交互式确认）
./scripts/auto_git_maintain.sh

# 3. 检测、提交并推送到远程
./scripts/auto_git_maintain.sh --push

# 4. 只检测不变更（dry-run）
./scripts/auto_git_maintain.sh --dry-run

# 5. 查看帮助
./scripts/auto_git_maintain.sh --help
```

### 交互流程

```
1. 显示当前 Git 状态
2. 检测 articles/ 目录变更（新增/修改/删除）
3. 询问是否继续（Y/n）
4. 自动更新目录总纲的版本号
5. 生成规范 commit message
6. 执行 git commit
7. 可选：git push
```

### Commit Message 规范

自动生成格式：
```
新增/修改/删除 N 篇文章 | v260630.1 | 共 70 篇文章
```

---

## 方案B：Git Hook（自动触发）

### 安装方法

```bash
# 一键安装 pre-commit hook
./scripts/install_git_hook.sh
```

### 功能

每次执行 `git commit` 时自动：
1. 检测 `articles/` 目录下是否有变更
2. 如果有变更，自动更新目录总纲中的版本号
3. 将目录总纲的变更自动加入本次提交
4. 输出更新摘要

### 卸载方法

```bash
rm .git/hooks/pre-commit
```

---

## 版本号规则

版本格式：`YYMMDD.N`

| 字段 | 含义 | 示例 |
|------|------|------|
| `YYMMDD` | 打包日期 | 260630 = 2026年6月30日 |
| `N` | 当日第N次打包 | 1, 2, 3... |

- **同一天多次维护**：`260630.1` → `260630.2` → `260630.3`
- **跨天维护**：`260630.5` → `260701.1`

---

## 目录总纲文件

| 项目 | 说明 |
|------|------|
| 文件 | `articles/目录_总览与文件管理_CN_260626.6.md` |
| 格式 | Markdown |
| 大小 | ~48KB, 1118行 |
| 维护内容 | 版本号、时间戳、自引用文件名 |

---

## 示例自动化工作流

### 日常维护

```bash
# 1. 先看看有什么变化
./scripts/auto_git_maintain.sh --status

# 2. 一键提交
./scripts/auto_git_maintain.sh

# 3. 如需推送
./scripts/auto_git_maintain.sh --push
```

### 完全自动化（cron 定时任务）

```bash
# 每天凌晨2点自动检测并提交
0 2 * * * cd /path/to/APP && ./scripts/auto_git_maintain.sh --push >> logs/auto_git_$(date +\%Y\%m\%d).log 2>&1
```

---

## 注意事项

1. **首次使用**：确保 Git 用户已配置：
   ```bash
   git config user.name "您的名字"
   git config user.email "您的邮箱"
   ```

2. **远程仓库**：如需自动推送，需先配置：
   ```bash
   git remote add origin <仓库地址>
   ```

3. **安全**：脚本不会删除任何文件，更新目录总纲时会自动备份（`.bak`）并在提交后清理。

4. **适用范围**：当前仅自动维护 `articles/` 下的文件变更，`server.py` 等核心文件变更也会一并纳入提交。