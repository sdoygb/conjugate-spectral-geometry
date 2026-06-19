# Geometry AI Server

几何论 AI 中间层服务 -- 基于 KIMI 大模型的几何论知识问答系统。

## 项目说明

这是一个帮助学习几何论的 AI 系统。它通过中间层服务连接 Open WebUI 和 KIMI 大模型，在对话中注入几何论知识库、活体信息场动力学和教学反馈机制，让 AI 能够基于几何论框架回答问题。

**知识库已内置**：`chroma_db/` 目录包含预构建的向量索引（72篇几何论文章），克隆后即可使用，无需额外准备文章。

## 架构

```
用户 → Open WebUI → 本中间层 → KIMI API
                    ↓
              ChromaDB 向量数据库（知识检索）
              LivingInfoField（活体信息场）
              TeachingSystem（教学反馈）
```

## 核心特性

- **向量语义检索**：ChromaDB 存储几何论知识库，支持语义匹配而非关键词匹配
- **活体信息场**：eta 角动力学驱动回答风格，每个会话独立演化
- **教学反馈系统**：通过纠正 API、反模式库、知识补丁，让系统"越聊越懂"
- **输出质量门控**：自动检测低质量回复并重试
- **文件自动注入**：从 Open WebUI uploads 目录自动读取上传文件
- **零外部数据库依赖**：只需 Python + ChromaDB，无需 MySQL

## 快速开始

### 环境要求

- Python 3.11+
- KIMI API Key（[申请地址](https://platform.moonshot.cn/)）
- macOS 用户如需语音输入功能，需安装 ffmpeg：`brew install ffmpeg`
- **已知问题**：macOS 上 Open WebUI 的语音输入功能可能触发 segmentation fault 崩溃，这是 Open WebUI 与 macOS Python 3.11 multiprocessing 的兼容性问题，与本中间层无关。建议暂时使用文字输入，或尝试 `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` 后启动 Open WebUI

### 安装

```bash
git clone https://github.com/sdoygb/geometry-ai-server.git
cd geometry-ai-server
pip install flask openai chromadb
```

### 配置

```bash
export KIMI_API_KEY="你的API Key"
```

### 启动

```bash
python3 geometry_ai_server_v5_12.py
```

服务启动在 `http://localhost:5000`。

### 首次启动

如果 `chroma_db/` 目录为空，会自动从 `articles/` 目录构建向量索引（约 1-2 分钟）。如果 `chroma_db/` 已存在，直接加载，跳过构建。

## Open WebUI 接入

在 Open WebUI 中添加自定义模型：

- **API Base URL**: `http://localhost:5000/v1`
- **API Key**: 任意非空字符串
- **模型名称**: `kimi-k2.7-code`

**重要设置**：关闭 Open WebUI 的"联网搜索"和"引用"功能，否则会干扰正常对话。

## API 文档

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容的对话接口 |
| GET | `/v1/models` | 列出可用模型 |
| GET | `/health` | 健康检查 |

### 教学系统

通过教学 API 可以纠正 AI 的错误、标记禁止模式、补充知识，让系统逐步学习。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/teach/correct` | 纠正 KIMI 的错误回答 |
| POST | `/v1/teach/antipattern` | 标记禁止的回复模式 |
| POST | `/v1/teach/patch` | 补充几何论知识 |
| GET | `/v1/teach/stats` | 查看教学统计 |
| GET | `/v1/teach/history` | 查看教学历史 |

#### 纠正示例

```bash
curl -X POST http://localhost:5000/v1/teach/correct \
  -H "Content-Type: application/json" \
  -d '{
    "wrong": "eta是数据库写死的数",
    "correct": "eta是信息场软模激发度的实时读出",
    "reason": "活体调度规则2"
  }'
```

纠正后，系统会在后续对话中自动注入这条纠正，避免重复犯错。随着纠正被成功应用，信任等级自动提升。

#### 反模式示例

```bash
curl -X POST http://localhost:5000/v1/teach/antipattern \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "未找到任何引用来源",
    "description": "禁止说找不到引用，必须基于核心公理回答",
    "severity": "high"
  }'
```

#### 知识补丁示例

```bash
curl -X POST http://localhost:5000/v1/teach/patch \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "eta角的几何含义",
    "content": "eta角是信息场软模激发度的度量，取值范围[30度, 72.53度]",
    "source": "文章33 §3.1"
  }'
```

### 向量知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/vector/status` | 向量库状态（文章数、学习记忆数） |
| POST | `/v1/vector/rebuild` | 重建文章索引 |
| POST | `/v1/vector/learned/clear` | 清空学习记忆 |

### 活体信息场

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/living/status` | 全局状态 |
| GET | `/v1/living/sessions` | 活跃会话列表 |
| GET | `/v1/living/session/<id>` | 单个会话详情 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `KIMI_API_KEY` | （必填） | KIMI API 密钥 |
| `KIMI_BASE_URL` | `https://api.moonshot.cn/v1` | KIMI API 地址 |
| `KIMI_MODEL` | `kimi-k2.7-code` | 模型名称 |
| `UPLOAD_FOLDER` | `~/AI/articles` | 文章目录 |
| `CHROMA_DB_DIR` | `~/AI/chroma_db` | 向量数据库目录 |
| `OPENWEBUI_UPLOAD_DIR` | 自动检测 | Open WebUI 上传目录 |
| `GT_EMBEDDING_MODE` | `default` | Embedding 模式（default/kimi） |
| `QUALITY_GATE_ENABLED` | `true` | 输出质量门控开关 |

## 目录结构

```
geometry-ai-server/
├── geometry_ai_server_v5_12.py   # 主程序
├── .gitignore
├── README.md
├── articles/                     # 几何论文章源文件（可选，用于重建索引）
└── chroma_db/                    # 向量数据库（预构建，开箱即用）
```

## License

MIT
