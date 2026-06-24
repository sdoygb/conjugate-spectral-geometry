# Geometry AI Server

> **当前版本**: v1.0.0.74 (2026-06-23)

几何论 AI 中间层服务 -- 基于 DeepSeek 大模型的几何论知识问答系统。

## 项目说明

这是一个帮助学习几何论的 AI 系统。它通过中间层服务连接 Open WebUI 和 DeepSeek 大模型，在对话中注入几何论知识库、活体信息场动力学和教学反馈机制，让 AI 能够基于几何论框架回答问题。

**首次启动自动构建知识库**：`chroma_db/` 目录在首次运行时自动从 `articles/` 目录构建，无需手动准备。

## 架构

```
用户 → Open WebUI → 本中间层(:5000) → DeepSeek API
                      ↓
                ChromaDB 向量数据库（SiliconFlow 1024维）
                LivingInfoField（活体信息场）
                TeachingSystem（教学反馈）
```

## 模块结构

```
geometry-ai-server/
├── app/                    # 主源码目录
│   ├── server.py           # Flask 路由、API 端点（主入口）
│   ├── config.py           # 环境变量、日志配置
│   ├── stream.py           # 流式生成、SSE、DSML 解析、API 重试
│   ├── knowledge.py        # ChromaDB 向量库、SiliconFlow Embedding
│   ├── models.py           # eta 动力学、personal_db、对话记录
│   ├── prompts.py          # system prompt、教学系统、质量检查
│   ├── tools.py            # Function Calling 工具定义与执行
│   ├── admin_routes.py     # 管理后台（token 认证）
│   ├── share_routes.py     # 分享功能
│   ├── auto_teach.py       # 自动教学脚本
│   ├── start.py            # 一键启动（watchdog 热重载）
│   ├── version.py          # 版本号
│   ├── .env.example        # 配置模板
│   ├── requirements.txt    # Python 依赖
│   ├── templates/          # HTML 模板
│   │   ├── admin.html
│   │   └── share.html
│   └── articles/           # 几何论文章（80+篇）
├── mac/                    # macOS 安装资源
│   ├── install_mac.sh
│   └── uninstall_mac.sh
├── windows/                # Windows 安装资源
│   ├── install_win.bat
│   ├── install.bat
│   ├── installer.iss
│   ├── start.bat
│   ├── install_service.bat
│   ├── uninstall_service.bat
│   └── uninstall_win.bat
├── docker/                 # Docker 部署
│   └── entrypoint.sh
├── docker-compose.yml
├── build_mac.py            # Mac 构建脚本
├── build_win.py            # Win 构建脚本
├── geometry-ai-intro.md    # 项目介绍
├── geometry-ai-intro/     # 介绍网页
├── README.md
└── README.txt
```

## 核心特性

- **向量语义检索**：ChromaDB + SiliconFlow Embedding（1024维），语义匹配而非关键词匹配
- **活体信息场**：eta 角动力学驱动回答风格，每个会话独立演化
- **教学反馈系统**：通过纠正 API、反模式库、知识补丁，让系统"越聊越懂"
- **输出质量门控**：自动检测低质量回复并重试
- **Function Calling 工具**：AI 可主动读写文章、向量搜索、管理个人数据库、查询历史对话
- **个人数据库**：JSON + ChromaDB 双存储，支持性格/感情/想法/记忆的持久化和语义检索
- **DSML 格式兼容**：自动解析 DeepSeek v4-pro 的 DSML 文本工具调用
- **API 自动重试**：TransferEncodingError 等网络错误自动重试（最多3次）
- **DSML 文本过滤**：流式输出中实时过滤 DSML 标签，不显示给用户
- **维度自动检测**：启动时自动检测向量库维度不匹配并重建
- **OpenAI 规范兼容**：完整的 OpenAI API 格式（流式/非流式/embeddings）
- **智能模型路由**：简单问题自动使用轻量模型，节省 token
- **零外部数据库依赖**：只需 Python + ChromaDB，无需 MySQL

## 快速开始

### 环境要求

- Python 3.9+（推荐 3.11）
- DeepSeek API Key（[注册获取](https://platform.deepseek.com/)）
- macOS / Linux / Windows（跨平台）

### macOS 一键安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/sdoygb/geometry-ai-server.git
cd geometry-ai-server

# 运行安装脚本（自动安装依赖、配置环境变量、注册开机自启）
bash mac/install_mac.sh
```

安装完成后，重启电脑即可使用。打开浏览器访问 `http://localhost:8080`。

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/sdoygb/geometry-ai-server.git
cd geometry-ai-server/app

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 4. 启动
python3 server.py
```

> macOS 用户如遇权限错误，加 `--break-system-packages` 或使用虚拟环境。

### 一键启动（含热重载）

```bash
cd app
python3 start.py
```

`start.py` 包含 watchdog，检测到代码变更自动重启服务器。

### Docker 部署

```bash
# 使用 docker-compose
docker-compose up -d

# 或手动构建
docker build -t geometry-ai-server .
docker run -p 5000:5000 --env-file .env geometry-ai-server
```

## Open WebUI 接入

### 安装 Open WebUI

```bash
pip install open-webui
open-webui serve
# 浏览器打开 http://localhost:8080 完成初始设置
```

### 配置连接

在 Open WebUI → 设置 → Connections 中：

- **OpenAI API URL**: `http://localhost:5000/v1`
- **API Key**: 任意非空字符串（如 `sk-123`）

### Function Calling 设置

模型的 Function Calling 必须设为 **Native** 模式：

1. Admin Panel → Settings → Models
2. 找到对应模型，点击编辑
3. Advanced Params → Function Calling → **Native**
4. 保存

## AI 工具系统

中间层通过 OpenAI Function Calling 协议为 AI 提供 10 个工具：

| 工具 | 说明 |
|------|------|
| `view_article` | 读取指定文章（支持 offset/limit 分页） |
| `vector_search` | 向量语义搜索知识库 |
| `write_article` | 写入/修改文章，自动更新向量索引 |
| `manage_articles` | 文章管理（列表、删除、归档） |
| `personal_read` | 读取个人数据库（性格/感情/想法/记忆） |
| `personal_write` | 写入个人数据库 |
| `chat_history` | 查询历史对话列表 |
| `chat_read` | 读取指定对话的完整消息链 |
| `git_commit` | 提交文章修改到 Git |
| `git_history` | 查看 Git 提交历史 |

## API 文档

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容对话接口（流式/非流式） |
| GET | `/v1/models` | 列出可用模型 |
| POST | `/v1/embeddings` | OpenAI 兼容 Embedding 接口 |
| GET | `/health` | 健康检查 |

### 教学系统

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/teach/correct` | 纠正 AI 的错误回答 |
| POST | `/v1/teach/antipattern` | 标记禁止的回复模式 |
| POST | `/v1/teach/patch` | 补充几何论知识 |
| GET | `/v1/teach/stats` | 查看教学统计 |
| GET | `/v1/teach/history` | 查看教学历史 |

### 向量知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/vector/status` | 向量库状态 |
| POST | `/v1/vector/rebuild` | 重建文章索引 |
| POST | `/v1/vector/learned/clear` | 清空学习记忆 |

### 管理后台

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin` | 管理页面（需 token 认证） |
| GET | `/admin/config` | 读取配置 |
| POST | `/admin/config` | 保存配置 |
| GET | `/admin/logs` | 查看日志 |
| POST | `/admin/restart` | 重启服务 |

管理后台认证：通过环境变量 `GAI_ADMIN_TOKEN` 配置（默认 `geometry-ai-admin`），支持 `Authorization: Bearer <token>` 头或 `?token=<token>` URL 参数。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GAI_API_KEY` | （必填） | DeepSeek API 密钥 |
| `GAI_BASE_URL` | `https://api.deepseek.com/v1` | LLM API 地址 |
| `GAI_MODEL` | `deepseek-v4-pro` | 主模型 |
| `GAI_MODEL_LITE` | `deepseek-v4-flash` | 轻量模型（简单问题自动路由） |
| `GAI_MODEL_VISION` | `deepseek-v4-flash` | 视觉模型 |
| `GAI_EMBEDDING_MODE` | `siliconflow` | Embedding 模式（siliconflow/local/api） |
| `SILICONFLOW_API_KEY` | （siliconflow 模式必填） | SiliconFlow API 密钥（[注册获取](https://cloud.siliconflow.cn/)） |
| `GAI_ADMIN_TOKEN` | `geometry-ai-admin` | 管理后台认证 token |
| `UPLOAD_FOLDER` | `app/articles` | 文章目录 |
| `CHROMA_DB_DIR` | `app/chroma_db` | 向量数据库目录 |
| `OPENWEBUI_UPLOAD_DIR` | 自动检测 | Open WebUI 上传目录 |
| `OPENWEBUI_DB_PATH` | 自动检测 | Open WebUI SQLite 数据库路径 |

## macOS 开机自启

安装脚本自动配置两个 LaunchAgent 服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| `com.geometryai.server` | 5000 | Geometry AI 中间层 |
| `com.geometryai.webui` | 8080 | Open WebUI 聊天界面 |

两个服务均配置 `RunAtLoad`（开机启动）和 `KeepAlive`（崩溃自动重启），通过 `bash -c "unset PYTHONHOME PYTHONPATH; exec ..."` 避免 IDE 环境变量污染。

管理服务：
```bash
# 查看状态
launchctl list | grep geometryai

# 停止服务
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.geometryai.server.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.geometryai.webui.plist

# 启动服务
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.geometryai.server.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.geometryai.webui.plist
```

## License

CC BY-NC-SA 4.0 -- 禁止商业用途，修改后必须以相同协议共享，需署名原作者。
