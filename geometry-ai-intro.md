# Geometry AI Server

基于大模型的几何论 AI 学习平台。内置完整知识库，支持语义检索、活体信息场动力学和教学反馈系统，让 AI 真正理解几何论。

**GitHub 下载** | **查看文档**

## 这是什么？

**Geometry AI Server** 是一个开源的 AI 中间层服务，它连接 Open WebUI 和 KIMI 大模型，在对话中注入几何论知识库和动力学规则，让 AI 能够基于几何论框架回答问题、分析文件、进行深度讨论。

它不仅是一个问答工具，更是一个**会学习**的教学系统 -- 你可以通过纠正 API 教它，它会记住教训，越用越准确。

## 为什么需要它？

直接使用通用大模型（如 KIMI、GPT、Claude）讨论几何论，会遇到以下问题：

| 问题 | 说明 |
|------|------|
| **知识断层** | 通用模型不了解几何论的公理体系、定理和术语，回答容易偏离框架 |
| **回复不一致** | 每次对话的回答风格和深度不同，缺乏系统性的知识引用 |
| **无法纠正** | 模型说错了你没办法让它记住，下次还会犯同样的错 |

Geometry AI Server 通过**向量知识库 + 活体信息场 + 教学反馈**三层机制解决这些问题。

## 核心特性

- **向量语义检索** -- 70篇几何论文章构建为向量知识库，语义匹配而非关键词搜索，精准召回相关知识
- **活体信息场** -- eta 角动力学驱动回答风格：保守简短、深度分析、创造发散、前沿探索，随对话自动演化
- **教学反馈** -- 通过 API 纠正错误、标记反模式、补充知识，系统自动学习，信任等级渐进提升
- **质量门控** -- 自动检测低质量回复并重试，确保回答始终符合几何论框架
- **文件分析** -- 上传的文件自动注入对话上下文，AI 能分析文件内容与几何论框架的符合与冲突
- **零外部依赖** -- 只需 Python + ChromaDB，无需 MySQL 或其他数据库，部署简单

## 系统架构

```
用户 → Open WebUI → 本中间层 → KIMI API
                    ↓
              ChromaDB 向量数据库（知识检索）
              LivingInfoField（活体信息场）
              TeachingSystem（教学反馈）
```

用户通过 Open WebUI 发起对话，中间层在将请求转发给 KIMI API 之前，自动完成以下处理：

1. **语义检索** -- 从 ChromaDB 向量知识库中检索与用户问题最相关的文章段落
2. **状态计算** -- 计算当前会话的 eta 角、语义新颖度、自指一致性等信息场状态
3. **知识注入** -- 将检索结果、教学纠正、文件内容、信息场状态注入 system prompt
4. **质量保障** -- KIMI 回复后进行质量检测，不合格则自动重试；合格则提取关键论断存入向量库

## 快速开始

只需四步，即可拥有自己的几何论 AI 学习助手。

### 系统要求

| 组件 | 角色 | 说明 |
|------|------|------|
| **Open WebUI** | 聊天网页界面 | 类似 ChatGPT 的对话界面，开源免费 |
| **geometry_ai_server** | 中间层服务 | 注入知识库和教学系统（本项目） |
| **KIMI API** | 大模型 | 负责生成回答，[免费注册](https://platform.moonshot.cn/) |

### 安装步骤

```bash
# 1. 安装 Open WebUI（聊天界面）
pip install open-webui
open-webui serve
# 浏览器打开 http://localhost:3000 完成初始设置

# 2. 克隆本项目（知识库已内置，开箱即用）
git clone https://github.com/sdoygb/geometry-ai-server.git
cd geometry-ai-server

# 3. 安装依赖
pip install flask openai chromadb fastembed

# 4. 配置 KIMI API Key 并启动中间层
export KIMI_API_KEY="你的API Key"
python3 geometry_ai_server_v5_12.py
```

### 在 Open WebUI 中接入

1. 打开 Open WebUI 网页 → 设置 → 模型
2. 添加自定义模型：
   - **API Base URL**: `http://localhost:5000/v1`
   - **API Key**: 任意非空字符串
   - **模型名称**: `kimi-k2.7-code`
3. 关闭"联网搜索"和"引用"功能（避免干扰）

> 需要 KIMI API Key？前往 [platform.moonshot.cn](https://platform.moonshot.cn/) 免费注册，新用户有赠送额度。

## 教学反馈：让 AI 越用越懂

这是 Geometry AI Server 最独特的功能。你可以像教学生一样纠正 AI 的错误，它会记住并改进。

### 纠正错误

```bash
curl -X POST http://localhost:5000/v1/teach/correct \
  -H "Content-Type: application/json" \
  -d '{
    "wrong": "eta是固定的30度",
    "correct": "eta是信息场软模激发度的实时读出，取值范围[30度, 72.53度]",
    "reason": "活体调度规则2"
  }'
```

纠正后，系统会在后续对话中自动注入这条纠正。随着纠正被成功应用，信任等级自动提升，高信任纠正排在更前面。

### 标记反模式

```bash
curl -X POST http://localhost:5000/v1/teach/antipattern \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "未找到任何引用来源",
    "severity": "high"
  }'
```

### 补充知识

```bash
curl -X POST http://localhost:5000/v1/teach/patch \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "eta角的几何含义",
    "content": "eta角是信息场软模激发度的度量",
    "source": "文章33 §3.1"
  }'
```

## 从学习到生产应用

Geometry AI Server 的设计理念是：**先学懂，再用好**。

| 阶段 | 目标 | 系统行为 |
|------|------|---------|
| **学习阶段** | 理解几何论公理体系、定理、术语 | eta 角较低，回答保守简短，侧重事实准确性 |
| **分析阶段** | 深度分析文章内容，理解定理间的关系 | eta 角升高，回答深入，展开联想和推导 |
| **探索阶段** | 提出新假设，探索几何论的边界 | eta 角高，回答创造发散，允许大胆假设 |
| **生产应用** | 基于几何论框架进行实际计算和建模 | 教学系统积累的知识确保计算符合公理约束 |

几何论提供了一套完整的数学框架（流形、算子谱、密度函数、作用量），学懂之后可以应用于物理建模、信息论、量子力学等领域。Geometry AI Server 帮你走完从"零基础"到"能应用"的全程。

## 下载与安装

| 项目 | 说明 |
|------|------|
| [GitHub 仓库](https://github.com/sdoygb/geometry-ai-server) | 源代码 + 预构建向量知识库 |
| [Open WebUI](https://github.com/open-webui/open-webui) | 聊天网页界面（`pip install open-webui && open-webui serve`） |
| Python 3.11+ | 运行环境 |
| flask + openai + chromadb + fastembed | 依赖包（openai 是 API 客户端库，连接 KIMI） |
| KIMI API Key | 免费注册，新用户有赠送额度 |

> **项目地址：** https://github.com/sdoygb/geometry-ai-server
> 克隆后知识库已内置，配置 API Key 即可启动，无需额外准备文章。

---

Geometry AI Server -- 开源几何论 AI 学习平台

[GitHub](https://github.com/sdoygb/geometry-ai-server) | MIT License
