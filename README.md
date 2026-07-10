# Geometry AI Server

几何论 AI 中间层服务 — 基于 DeepSeek 大模型的几何论知识问答系统。

## 架构

```
用户 → Open WebUI → 本中间层(:5000) → DeepSeek API
                      ↓
                ChromaDB 向量数据库（SiliconFlow 1024维）
                LivingInfoField（活体信息场）
                TeachingSystem（教学反馈）
```

另有独立的主库AI验证系统 (`master_ai/`)，做公式推导的自动溯源、Berny相位验证和依赖图管理。

## 快速开始

### 环境要求

- **Python 3.11+**
- **DeepSeek API Key** — [注册](https://platform.deepseek.com/)
- **SiliconFlow API Key**（可选） — [注册](https://cloud.siliconflow.cn/)

### 一键安装

| 平台 | 命令 |
|------|------|
| **macOS** | `bash build_mac/install_mac.sh` |
| **Linux (Ubuntu/Debian)** | `sudo bash build_linux_new/install.sh` |
| **Windows** | 右键 `build_win_new/install.bat` → 以管理员身份运行 |
| **Docker** | `docker-compose up -d` |

> 各平台安装包也可通过 `python3 build_linux_new.py` / `python3 build_win_new.py` 重新构建。

### 手动安装

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 GAI_API_KEY
python3 server.py
```

管理页面：`http://localhost:5000/admin`

### Docker

```bash
docker-compose up -d
# 或
docker build -t geometry-ai-server .
docker run -p 5000:5000 --env-file .env geometry-ai-server
```

## Open WebUI 接入

```bash
pip install open-webui
open-webui serve --port 8080
```

然后在 Open WebUI 设置 → Connections 中：
- **OpenAI API URL**: `http://localhost:5000/v1`
- **API Key**: 任意非空（如 `sk-123`）
- 模型 Function Calling 必须设为 **Native** 模式

## 核心特性

- **向量语义检索** — ChromaDB + SiliconFlow Embedding (1024维)
- **活体信息场** — eta 角动力学驱动回答风格，每个会话独立演化
- **教学反馈系统** — 纠正 API + 反模式库 + 知识补丁
- **输出质量门控** — 自动检测低质量回复并重试
- **Function Calling 工具** — AI 可主动读写文章、向量搜索、个人数据库
- **智能模型路由** — 简单问题自动切换到轻量模型节省 token
- **DSML 格式兼容** — 自动解析 DeepSeek 的 DSML 标签
- **主库AI验证** (`master_ai/`) — 公式推导的自动溯源、Berny相位验证、依赖图管理

## 项目结构

```
geometry-ai-server/
├── app/                          # 主服务
│   ├── server.py                 # Flask 路由 / API 端点
│   ├── config.py                 # 环境变量 / 日志
│   ├── stream.py                 # 流式生成 / SSE / 重试
│   ├── knowledge.py              # ChromaDB 向量库
│   ├── models.py                 # eta 动力学 / 对话记录
│   ├── prompts.py                # System prompt / 教学系统
│   ├── tools.py                  # 10个 Function Calling 工具
│   ├── admin_routes.py           # 管理后台
│   ├── share_routes.py           # 分享功能
│   ├── auto_teach.py             # 自动教学
│   ├── master_client.py          # 主库AI通信
│   ├── articles/                 # 几何论文章 (130+篇)
│   └── templates/                # HTML 模板
├── master_ai/                    # 主库AI验证系统
│   ├── server.py                 # 验证服务 (端口 5001)
│   ├── verifier.py               # 三重验证引擎
│   ├── master_db.py              # 真理层数据库
│   ├── dependency_graph.py       # 依赖图 / 互锁检测
│   ├── berry_checker.py          # Berry 相位验证
│   ├── falsification.py          # 主动证伪
│   ├── math_foundations.py       # 数学基础
│   └── config.py                 # 主库配置
├── build_mac/                    # macOS 安装包
├── build_linux_new/              # Linux 安装包 (install/upgrade/uninstall)
├── build_win_new/                # Windows 安装包 (install/uninstall)
├── build_linux.py                # Linux 构建脚本
├── build_win.py                  # Windows 构建脚本 (旧版)
├── build_mac.py                  # macOS 构建脚本
├── build_linux_new.py            # Linux 构建脚本 (新版)
├── build_win_new.py              # Windows 构建脚本 (新版)
├── docker-compose.yml            # Docker 部署
└── linux/                        # Linux 辅助脚本
```

## 升级

```bash
# Linux — 保留 .env / venv / chroma_db / logs
sudo bash build_linux_new/upgrade.sh
```

## API 接口

### 核心

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | 对话（流式/非流式） |
| GET | `/v1/models` | 列出模型 |
| POST | `/v1/embeddings` | Embedding |
| GET | `/health` | 健康检查 |

### 教学

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/teach/correct` | 纠正错误回答 |
| POST | `/v1/teach/antipattern` | 标记禁止模式 |
| POST | `/v1/teach/patch` | 补充知识 |
| GET | `/v1/teach/stats` | 教学统计 |

### 向量知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/vector/rebuild` | 重建索引 |
| GET | `/v1/vector/status` | 向量库状态 |

### 管理后台

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin` | 管理页面 |
| GET | `/admin/config` | 读取配置 |
| POST | `/admin/config` | 保存配置 |
| GET | `/admin/logs` | 查看日志 |

管理后台 token 由 `GAI_ADMIN_TOKEN` 配置（默认 `geometry-ai-admin`）。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GAI_API_KEY` | （必填） | DeepSeek API Key |
| `GAI_BASE_URL` | `https://api.deepseek.com/v1` | API 地址 |
| `GAI_MODEL` | `deepseek-v4-pro` | 主模型 |
| `GAI_MODEL_LITE` | `deepseek-v4-flash` | 轻量模型 |
| `GAI_MODEL_VISION` | `deepseek-v4-flash` | 视觉模型 |
| `GAI_EMBEDDING_MODE` | `siliconflow` | embedding 模式 |
| `SILICONFLOW_API_KEY` | — | SiliconFlow Key |
| `GAI_ADMIN_TOKEN` | `geometry-ai-admin` | 管理后台 token |
| `MASTER_AI_URL` | `http://localhost:5001` | 主库AI地址 |
| `MASTER_AI_TOKEN` | `master-ai-verify` | 主库AI token |

## License

CC BY-NC-SA 4.0 — 禁止商业用途，修改后须以相同协议共享，须署名原作者。
