"""
opencode_proxy.py — OpenCode 中间层代理

为 OpenCode 提供子AI的知识库能力，同时保留 OpenCode 自身的编程工具。

架构：
  OpenCode → 本代理(5002) → DeepSeek API
                ↓
          ChromaDB向量检索（与子AI完全一致的embedding方式）
          主库真理查询

工作原理：
  1. 接收 OpenCode 的 OpenAI 兼容请求
  2. 保留 OpenCode 的 system prompt（编程上下文）
  3. 用 SiliconFlow BAAI/bge-m3 embedding 检索知识库（1024维，和子AI对齐）
  4. 将知识库结果追加到 system prompt（不替换）
  5. 转发给 DeepSeek API
  6. 原样返回响应（含 tool_calls、streaming 等）
"""

import os
import sys
import json
import time
import re
import logging
import requests
import openai
from flask import Flask, request, Response, jsonify

# ── 配置 ──────────────────────────────────────────────
PROXY_PORT = int(os.getenv("OPENCODE_PROXY_PORT", "5002"))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 上游 LLM API（DeepSeek）
LLM_BASE_URL = os.getenv("GAI_API_BASE", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("GAI_API_KEY", "")

# ChromaDB 路径（直接读取子AI的知识库）
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(PROJECT_ROOT, "chroma_db"))

# SiliconFlow embedding 配置（和子AI完全一致）
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
EMBEDDING_MODEL = "BAAI/bge-m3"  # 1024维，和子AI一致

# 注入参数
KNOWLEDGE_TOP_K = int(os.getenv("KNOWLEDGE_TOP_K", "5"))
TRUTH_TOP_K = int(os.getenv("TRUTH_TOP_K", "5"))
MAX_KNOWLEDGE_CHARS = int(os.getenv("MAX_KNOWLEDGE_CHARS", "6000"))

# ── 日志 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROXY %(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("opencode-proxy")

# ── Flask ─────────────────────────────────────────────
app = Flask(__name__)


# ── SiliconFlow Embedding（和子AI knowledge.py 完全一致）────────
class SiliconFlowEmbeddingFunction:
    """使用 SiliconFlow API 的中文 Embedding（BAAI/bge-m3, 1024维, 8192 tokens）
    与子AI knowledge.py 中的实现完全一致。"""

    def __init__(self, api_key: str = "", model: str = "BAAI/bge-m3"):
        self.client = openai.OpenAI(
            api_key=api_key or "not-needed",
            base_url="https://api.siliconflow.cn/v1",
        )
        self.model = model
        self._dim = 1024

    def name(self) -> str:
        return f"siliconflow({self.model})"

    def __call__(self, input):
        """ChromaDB add 时调用（批量）"""
        all_embeddings = []
        cleaned = []
        for t in input:
            t = t.replace('\x00', '').replace('\r', '')
            t = re.sub(r'\s+', ' ', t).strip()
            if len(t) > 2000:
                t = t[:2000]
            cleaned.append(t)
        for i, text in enumerate(cleaned):
            if not text:
                all_embeddings.append([0.0] * self._dim)
                continue
            try:
                resp = self.client.embeddings.create(model=self.model, input=[text])
                all_embeddings.extend([d.embedding for d in resp.data])
            except Exception as e:
                logger.warning(f"[EMBEDDING-SF] 第{i}条失败(len={len(text)}): {e}")
                all_embeddings.append([0.0] * self._dim)
        return all_embeddings

    def embed_query(self, input: str):
        """ChromaDB查询时调用（单条文本embedding）"""
        text = input if isinstance(input, str) else str(input)
        text = text.replace('\x00', '').replace('\r', '')
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 2000:
            text = text[:2000]
        try:
            resp = self.client.embeddings.create(model=self.model, input=[text])
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.warning(f"[EMBEDDING-SF] 查询embedding失败: {e}")
            return [[0.0] * self._dim]


# ── ChromaDB 直接访问（与子AI对齐）────────────────────
_kb_client = None
_kb_collection = None
_truth_collection = None
_embedding_fn = None
_init_lock = False


def _init_chromadb():
    """初始化 ChromaDB，使用与子AI完全一致的 embedding 方式"""
    global _kb_client, _kb_collection, _truth_collection, _embedding_fn, _init_lock
    if _kb_client is not None:
        return
    if _init_lock:
        return  # 防止并发初始化
    _init_lock = True

    try:
        import chromadb

        # 1. 创建 embedding function（和子AI一致：SiliconFlow BAAI/bge-m3 1024维）
        _embedding_fn = SiliconFlowEmbeddingFunction(
            api_key=SILICONFLOW_API_KEY,
            model=EMBEDDING_MODEL,
        )
        logger.info(f"[CHROMA] Embedding: {_embedding_fn.name()} (1024维, 与子AI对齐)")

        # 2. 打开 ChromaDB
        _kb_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

        # 3. 获取 collection（带 embedding_function，这样 query 时自动用 SiliconFlow）
        try:
            _kb_collection = _kb_client.get_collection(
                name="articles",
                embedding_function=_embedding_fn,
            )
            logger.info(f"[CHROMA] articles collection: {_kb_collection.count()} 条")
        except Exception as e:
            _kb_collection = None
            logger.warning(f"[CHROMA] articles collection 不存在: {e}")

        try:
            _truth_collection = _kb_client.get_collection(
                name="master_truth",
                embedding_function=_embedding_fn,
            )
            logger.info(f"[CHROMA] master_truth collection: {_truth_collection.count()} 条")
        except Exception as e:
            _truth_collection = None
            logger.warning(f"[CHROMA] master_truth collection 不存在: {e}")

    except Exception as e:
        logger.error(f"[CHROMA] 初始化失败: {e}")
        _kb_client = None
    finally:
        _init_lock = False


def search_knowledge_base(query: str, top_k: int = KNOWLEDGE_TOP_K) -> list:
    """检索文章知识库（使用 SiliconFlow embedding，和子AI一致）"""
    _init_chromadb()
    if not query or len(query.strip()) < 3 or _kb_collection is None:
        return []
    try:
        # query 时 ChromaDB 自动调用 embedding_fn.embed_query
        results = _kb_collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                items.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })
        return items
    except Exception as e:
        logger.warning(f"知识库检索失败: {e}")
    return []


def search_master_truth(query: str, top_k: int = TRUTH_TOP_K) -> list:
    """检索主库已验证真理"""
    _init_chromadb()
    if not query or len(query.strip()) < 3 or _truth_collection is None:
        return []
    try:
        results = _truth_collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                items.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": meta,
                    "permanent_number": meta.get("permanent_number", "?"),
                    "formula_name": meta.get("formula_name", ""),
                })
        return items
    except Exception as e:
        logger.warning(f"主库真理检索失败: {e}")
    return []


def build_knowledge_context(query: str) -> str:
    """构建注入的知识上下文"""
    kb_results = search_knowledge_base(query)
    truth_results = search_master_truth(query)

    if not kb_results and not truth_results:
        return ""

    parts = []
    total_chars = 0

    if truth_results:
        parts.append("## 已验证定理（主库真理层）")
        for t in truth_results:
            num = t.get("permanent_number", "?")
            name = t.get("formula_name", "?")
            doc = t.get("content", "")[:300]
            entry = f"  #{num} {name}: {doc}"
            if total_chars + len(entry) > MAX_KNOWLEDGE_CHARS:
                break
            parts.append(entry)
            total_chars += len(entry)

    if kb_results:
        parts.append("\n## 知识库相关内容")
        for r in kb_results:
            source = r.get("metadata", {}).get("file_name", r.get("metadata", {}).get("source", "?"))
            content = r.get("content", "")[:400]
            entry = f"  [{source}]: {content}"
            if total_chars + len(entry) > MAX_KNOWLEDGE_CHARS:
                break
            parts.append(entry)
            total_chars += len(entry)

    if len(parts) <= 2:
        return ""

    return "\n".join(parts)


def extract_user_query(messages: list) -> str:
    """从消息列表中提取最后一条用户消息作为检索query"""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
    return ""


def inject_knowledge(messages: list) -> list:
    """在保留 OpenCode system prompt 的基础上，追加共扼谱几何知识"""
    query = extract_user_query(messages)
    if not query:
        return messages

    knowledge = build_knowledge_context(query)
    if not knowledge:
        return messages

    knowledge_block = f"""

## 共扼谱几何知识库参考（自动注入）
以下是与当前任务相关的共扼谱几何定理和知识库内容，供参考：

{knowledge}

---
注意：以上内容来自共扼谱几何知识库自动检索，可能与当前编程任务相关也可能无关。请根据实际需要使用。
"""

    new_messages = []
    injected = False
    for msg in messages:
        if msg.get("role") == "system" and not injected:
            new_msg = dict(msg)
            new_msg["content"] = msg["content"] + knowledge_block
            new_messages.append(new_msg)
            injected = True
        else:
            new_messages.append(msg)

    if not injected:
        new_messages.insert(0, {"role": "system", "content": knowledge_block})

    logger.info(f"知识注入完成: query='{query[:50]}...'")
    return new_messages


# ── API 端点 ──────────────────────────────────────────
@app.route("/v1/models", methods=["GET"])
@app.route("/openai/models", methods=["GET"])
def list_models():
    """返回可用模型列表"""
    models = [
        {"id": "deepseek-v4-flash"},
        {"id": "deepseek-v4-pro"},
        {"id": "kimi-k2.6"},
        {"id": "gpt-5.4"},
        {"id": "claude-sonnet-4-20250514"},
    ]
    return jsonify({
        "object": "list",
        "data": [{"id": m["id"], "object": "model", "owned_by": "geometryai-proxy"} for m in models],
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """核心代理：注入知识 → 转发 DeepSeek"""
    body = request.get_json(force=True)
    messages = body.get("messages", [])
    is_stream = body.get("stream", False)
    model = body.get("model", "?")

    logger.info(f"[REQUEST] model={model} stream={is_stream} messages={len(messages)} from={request.remote_addr}")

    # 注入知识库上下文
    messages = inject_knowledge(messages)
    body["messages"] = messages

    # API Key
    api_key = request.headers.get("Authorization", f"Bearer {LLM_API_KEY}")
    if not api_key.startswith("Bearer "):
        api_key = f"Bearer {api_key}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key,
    }

    try:
        if is_stream:
            def generate():
                import uuid
                _resp_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
                _created = int(time.time())
                _model = model

                def _sse_chunk(delta, finish_reason=None):
                    """构建干净的SSE chunk（和子AI格式一致）"""
                    chunk = {
                        "id": _resp_id,
                        "object": "chat.completion.chunk",
                        "created": _created,
                        "model": _model,
                        "choices": [{
                            "index": 0,
                            "delta": delta,
                        }]
                    }
                    if finish_reason:
                        chunk["choices"][0]["finish_reason"] = finish_reason
                    return b"data: " + json.dumps(chunk, ensure_ascii=False).encode("utf-8") + b"\n\n"

                # 发送初始 role chunk
                yield _sse_chunk({"role": "assistant"})

                with requests.post(
                    f"{LLM_BASE_URL}/chat/completions",
                    json=body,
                    headers=headers,
                    stream=True,
                    timeout=120,
                ) as upstream:
                    fr = None
                    for line in upstream.iter_lines():
                        if not line:
                            continue
                        if line.startswith(b"data: ") and not line.startswith(b"data: [DONE]"):
                            try:
                                raw = json.loads(line[6:])
                                choices = raw.get("choices", [])
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})
                                cfr = choices[0].get("finish_reason")
                                if cfr:
                                    fr = cfr
                                # 只转发content，丢弃reasoning_content（思考过程不输出给用户）
                                content = delta.get("content")
                                if content:
                                    yield _sse_chunk({"content": content})
                            except Exception:
                                pass
                    # 发送结束 chunk
                    yield _sse_chunk({}, finish_reason=fr or "stop")
                yield b"data: [DONE]\n\n"
            resp = Response(generate(), content_type="text/event-stream")
            resp.headers["Cache-Control"] = "no-cache"
            resp.headers["X-Accel-Buffering"] = "no"
            resp.headers["Connection"] = "keep-alive"
            return resp
        else:
            resp = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                json=body,
                headers=headers,
                timeout=120,
            )
            # 修复非流式：把reasoning_content合并到content
            try:
                data = resp.json()
                for choice in data.get("choices", []):
                    msg = choice.get("message", {})
                    # 丢弃reasoning_content，只保留content
                    msg.pop("reasoning_content", None)
                return jsonify(data), resp.status_code
            except Exception:
                return Response(resp.content, status=resp.status_code, content_type="application/json")
    except requests.exceptions.Timeout:
        return jsonify({"error": {"message": "上游API超时", "type": "timeout"}}), 504
    except Exception as e:
        logger.error(f"代理失败: {e}")
        return jsonify({"error": {"message": str(e), "type": "proxy_error"}}), 502


@app.route("/health", methods=["GET"])
def health():
    _init_chromadb()
    kb_count = _kb_collection.count() if _kb_collection else 0
    truth_count = _truth_collection.count() if _truth_collection else 0
    return jsonify({
        "status": "ok",
        "service": "opencode-proxy",
        "port": PROXY_PORT,
        "llm_backend": LLM_BASE_URL,
        "chroma_db": CHROMA_DB_DIR,
        "kb_articles": kb_count,
        "truth_count": truth_count,
        "embedding": f"siliconflow({EMBEDDING_MODEL}, 1024维)",
        "embedding_aligned_with_subai": True,
    })


# ── 入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"OpenCode代理启动 | 端口={PROXY_PORT} | LLM={LLM_BASE_URL}")
    logger.info(f"ChromaDB: {CHROMA_DB_DIR} | Embedding: siliconflow({EMBEDDING_MODEL})")
    logger.info(f"SiliconFlow Key: {SILICONFLOW_API_KEY[:10]}..." if SILICONFLOW_API_KEY else "⚠️ 无SiliconFlow Key")
    # 启动时预加载ChromaDB（避免首次请求阻塞3秒导致OpenCode无输出）
    _init_chromadb()
    app.run(host="0.0.0.0", port=PROXY_PORT, threaded=True)
