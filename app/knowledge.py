from __future__ import annotations
"""
knowledge.py — 共扼谱几何AI调度中间层知识库模块
从 geometry_ai_server_v5_12.py 提取的嵌入函数、向量知识库和一致性评估。
"""

import os
import re
import math
import hashlib
import time
import json
import threading
import glob
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any

import openai
import requests

from config import (
    logger,
    GAI_API_KEY, GAI_BASE_URL, GAI_EMBEDDING_MODEL,
    EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,
    USE_WORKSPACE, UPLOAD_FOLDER,
    CHROMADB_AVAILABLE,
    MAX_INJECT_CHARS, CHUNK_SIZE, CHUNK_OVERLAP,
    GEOMETRY_CONSTANTS, TERM_SYNONYMS, SYNONYM_EXPAND,
)

try:
    from chromadb.api.types import Documents, Embeddings
except ImportError:
    Documents = list
    Embeddings = list


# ==================== Embedding 查询缓存（加速多角度检索与教学检索） ====================

class EmbeddingQueryCache:
    """
    查询 embedding 的线程安全 LRU 缓存。
    同一查询文本（多角度检索、同义词扩展、教学段落检索复用同一 query）
    在 TTL 内只调用一次远程 embedding API，其余命中缓存，显著降低延迟。
    """
    MAX_ENTRIES = 512
    TTL_SECONDS = 3600

    def __init__(self):
        self._cache = {}          # {norm_text: (timestamp, embedding)}
        self._lock = threading.Lock()

    def _norm(self, text: str) -> str:
        norm = text.replace('\x00', '').replace('\r', '').strip()
        return re.sub(r'\s+', ' ', norm)

    @staticmethod
    def _is_zero_vector(embedding) -> bool:
        """检测零向量（API 限流/失败时可能返回 200 但内容全零，会毒化缓存）"""
        try:
            vec = embedding[0] if embedding and isinstance(embedding, list) else embedding
            if not vec:
                return True
            return all(abs(float(v)) < 1e-8 for v in vec[:32])
        except Exception:
            return True

    def get(self, text: str):
        norm = self._norm(text)
        if not norm:
            return None
        now = time.time()
        with self._lock:
            entry = self._cache.get(norm)
            if entry and now - entry[0] < self.TTL_SECONDS:
                if self._is_zero_vector(entry[1]):
                    del self._cache[norm]  # 清除毒化条目，强制重新嵌入
                    return None
                return entry[1]
            if entry:  # 过期条目
                del self._cache[norm]
            return None

    def set(self, text: str, embedding):
        norm = self._norm(text)
        if not norm or self._is_zero_vector(embedding):
            return  # 零向量不缓存，避免污染后续查询
        now = time.time()
        with self._lock:
            if len(self._cache) >= self.MAX_ENTRIES:
                # 淘汰最旧条目
                oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
            self._cache[norm] = (now, embedding)

    def clear(self):
        with self._lock:
            self._cache.clear()


_EMBEDDING_QUERY_CACHE = EmbeddingQueryCache()

# 熔断器：embedding API 连续失败 >=3 次后熔断 60s，检索路径快速失败，避免重试风暴雪崩
_EMBED_FAIL_COUNT = 0
_EMBED_CIRCUIT_OPEN_UNTIL = 0.0
_EMBED_CIRCUIT_THRESHOLD = 3
_EMBED_CIRCUIT_COOLDOWN = 60.0


# ==================== API Embedding Function ====================

class APIEmbeddingFunction:
    """使用 LLM API 的 ChromaDB 自定义 Embedding Function"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)
        self.model = GAI_EMBEDDING_MODEL

    def name(self) -> str:
        return "api-embedding"

    def __call__(self, input: Documents) -> Embeddings:
        all_embeddings = []
        for i in range(0, len(input), 32):
            batch = input[i:i + 32]
            try:
                resp = self.client.embeddings.create(model=self.model, input=batch)
                all_embeddings.extend([d.embedding for d in resp.data])
            except Exception as e:
                logger.error(f"[EMBEDDING] embedding 批次 {i//32} 失败: {e}")
                for _ in batch:
                    all_embeddings.append([0.0] * 1536)
        return all_embeddings

    def embed_query(self, input: str) -> Embeddings:
        """ChromaDB查询时调用"""
        global _EMBED_FAIL_COUNT, _EMBED_CIRCUIT_OPEN_UNTIL
        text = input if isinstance(input, str) else str(input)
        cached = _EMBEDDING_QUERY_CACHE.get(text)
        if cached is not None:
            return cached
        if time.time() < _EMBED_CIRCUIT_OPEN_UNTIL:
            return [[0.0] * 1536]  # 熔断期内快速失败，不调 API
        last_err = None
        for attempt in range(2):
            try:
                resp = self.client.embeddings.create(model=self.model, input=[text])
                result = [d.embedding for d in resp.data]
                if result and all(abs(float(v)) < 1e-8 for v in result[0][:32]):
                    last_err = "API 返回零向量（限流或降级）"
                    _EMBED_FAIL_COUNT += 1
                    if _EMBED_FAIL_COUNT >= _EMBED_CIRCUIT_THRESHOLD:
                        _EMBED_CIRCUIT_OPEN_UNTIL = time.time() + _EMBED_CIRCUIT_COOLDOWN
                        logger.error(f"[EMBEDDING] 熔断开启 {_EMBED_CIRCUIT_COOLDOWN}s（连续失败 {_EMBED_FAIL_COUNT} 次）")
                    time.sleep(0.5)
                    continue
                _EMBED_FAIL_COUNT = 0
                _EMBEDDING_QUERY_CACHE.set(text, result)
                return result
            except Exception as e:
                last_err = e
                _EMBED_FAIL_COUNT += 1
                if _EMBED_FAIL_COUNT >= _EMBED_CIRCUIT_THRESHOLD:
                    _EMBED_CIRCUIT_OPEN_UNTIL = time.time() + _EMBED_CIRCUIT_COOLDOWN
                    logger.error(f"[EMBEDDING] 熔断开启 {_EMBED_CIRCUIT_COOLDOWN}s（连续失败 {_EMBED_FAIL_COUNT} 次）")
                time.sleep(0.5)
        logger.error(f"[EMBEDDING] embed_query失败(重试后): {last_err}")
        return [[0.0] * 1536]


# ==================== BM25 关键词检索（叠加在 ChromaDB 向量检索之上） ====================

class BM25Searcher:
    """
    轻量级 BM25 关键词检索器，用于补充 ChromaDB 向量检索。
    在 build_index 时同步构建倒排索引，search 时与向量结果 RRF 融合。
    """

    def __init__(self):
        self.inverted_index = {}    # {token: {chunk_id: tf}}
        self.doc_lengths = {}       # {chunk_id: token_count}
        self.chunk_count = 0
        self.avg_dl = 0.0
        self._initialized = False
        self._jieba_loaded = False

    def _ensure_jieba(self):
        """延迟加载 jieba，避免 import 时触发词典加载"""
        if not self._jieba_loaded:
            try:
                import jieba
                # 添加共扼谱几何领域自定义词典
                _dict_path = os.path.join(os.path.dirname(__file__), 'jieba_dict.txt')
                if os.path.exists(_dict_path):
                    jieba.load_userdict(_dict_path)
                self._jieba_loaded = True
            except ImportError:
                logger.warning("[BM25] jieba 未安装，关键词检索不可用")

    def _tokenize(self, text: str) -> list:
        """分词并过滤停用词"""
        if not self._jieba_loaded:
            return []
        import jieba
        # 搜索模式下分词更细粒度
        words = jieba.cut_for_search(text)
        # 过滤单字和常见停用词
        stopwords = {'的', '了', '是', '在', '有', '和', '与', '为', '被', '把',
                     '到', '从', '对', '上', '下', '中', '不', '也', '而', '就',
                     '能', '会', '可以', '这', '那', '它', '他', '她', '我们',
                     '其', '所', '以', '等', '个', '一', '之', '或', '但', '则'}
        return [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in stopwords]

    def build_index(self, chunks_data: list):
        """
        构建倒排索引。chunks_data: [{'id': chunk_id, 'text': chunk_text}, ...]
        """
        self._ensure_jieba()
        if not self._jieba_loaded:
            return

        self.inverted_index = {}
        self.doc_lengths = {}
        self.chunk_count = 0

        for chunk in chunks_data:
            chunk_id = chunk['id']
            text = chunk.get('text', '')
            tokens = self._tokenize(text)

            if not tokens:
                continue

            # 计算词频
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            self.doc_lengths[chunk_id] = len(tokens)
            for word, freq in tf.items():
                if word not in self.inverted_index:
                    self.inverted_index[word] = {}
                self.inverted_index[word][chunk_id] = freq

        self.chunk_count = len(self.doc_lengths)
        self.avg_dl = sum(self.doc_lengths.values()) / self.chunk_count if self.chunk_count > 0 else 1.0
        self._initialized = True
        logger.info(f"[BM25] 索引构建完成: {self.chunk_count} chunks, {len(self.inverted_index)} unique tokens")

    def search(self, query: str, top_k: int = 20) -> list:
        """
        BM25 评分检索。返回 [(chunk_id, score), ...] 按分数降序。
        """
        if not self._initialized or not self._jieba_loaded:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = {}
        N = self.chunk_count
        k1 = 1.5   # BM25 参数
        b = 0.75   # BM25 参数

        for word in tokens:
            if word not in self.inverted_index:
                continue
            df = len(self.inverted_index[word])
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

            for chunk_id, tf in self.inverted_index[word].items():
                dl = self.doc_lengths.get(chunk_id, 1)
                tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / self.avg_dl))
                scores[chunk_id] = scores.get(chunk_id, 0.0) + idf * tf_norm

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    @property
    def initialized(self):
        return self._initialized


class SiliconFlowEmbeddingFunction:
    """使用 SiliconFlow 免费 API 的中文 Embedding（BAAI/bge-m3, 1024维, 8192 tokens）"""

    def __init__(self, api_key: str = "", model: str = "BAAI/bge-m3"):
        self.client = openai.OpenAI(
            api_key=api_key or "not-needed",
            base_url="https://api.siliconflow.cn/v1"
        )
        self.model = model
        self._dim = 1024

    def name(self) -> str:
        return f"siliconflow({self.model})"

    def __call__(self, input: Documents) -> Embeddings:
        all_embeddings = []
        # 清理文本：去除null字节和特殊字符
        cleaned = []
        for t in input:
            t = t.replace('\x00', '').replace('\r', '')
            import re as _re
            t = _re.sub(r'\s+', ' ', t).strip()
            if len(t) > 2000:
                t = t[:2000]
            cleaned.append(t)
        # 批量发送（32条/批，减少API往返）；整批失败时降级为逐条（保持稳定性）
        for i in range(0, len(cleaned), 32):
            batch = cleaned[i:i + 32]
            try:
                resp = self.client.embeddings.create(model=self.model, input=batch)
                batch_embs = [d.embedding for d in resp.data]
                if len(batch_embs) != len(batch):
                    raise ValueError(f"返回条数 {len(batch_embs)} != 请求条数 {len(batch)}")
                all_embeddings.extend(batch_embs)
            except Exception as e:
                logger.warning(f"[EMBEDDING-SF] 批次{i//32}失败({e})，降级逐条")
                for j, text in enumerate(batch):
                    if not text:
                        all_embeddings.append([0.0] * self._dim)
                        continue
                    try:
                        resp = self.client.embeddings.create(model=self.model, input=[text])
                        all_embeddings.extend([d.embedding for d in resp.data])
                    except Exception as e2:
                        logger.warning(f"[EMBEDDING-SF] 第{i+j}条失败(len={len(text)}): {e2}")
                        all_embeddings.append([0.0] * self._dim)
        return all_embeddings

    def embed_query(self, input: str) -> Embeddings:
        """ChromaDB查询时调用（单条文本embedding）"""
        text = input if isinstance(input, str) else str(input)
        text = text.replace('\x00', '').replace('\r', '')
        import re as _re
        text = _re.sub(r'\s+', ' ', text).strip()
        if len(text) > 2000:
            text = text[:2000]
        cached = _EMBEDDING_QUERY_CACHE.get(text)
        if cached is not None:
            return cached
        global _EMBED_FAIL_COUNT, _EMBED_CIRCUIT_OPEN_UNTIL
        if time.time() < _EMBED_CIRCUIT_OPEN_UNTIL:
            return [[0.0] * self._dim]  # 熔断期内快速失败，不调 API
        last_err = None
        for attempt in range(2):
            try:
                resp = self.client.embeddings.create(model=self.model, input=[text])
                result = [d.embedding for d in resp.data]
                if result and all(abs(float(v)) < 1e-8 for v in result[0][:32]):
                    last_err = "API 返回零向量（限流或降级）"
                    _EMBED_FAIL_COUNT += 1
                    if _EMBED_FAIL_COUNT >= _EMBED_CIRCUIT_THRESHOLD:
                        _EMBED_CIRCUIT_OPEN_UNTIL = time.time() + _EMBED_CIRCUIT_COOLDOWN
                        logger.error(f"[EMBEDDING-SF] 熔断开启 {_EMBED_CIRCUIT_COOLDOWN}s（连续失败 {_EMBED_FAIL_COUNT} 次）")
                    time.sleep(0.5)
                    continue
                _EMBED_FAIL_COUNT = 0
                _EMBEDDING_QUERY_CACHE.set(text, result)
                return result
            except Exception as e:
                last_err = e
                _EMBED_FAIL_COUNT += 1
                if _EMBED_FAIL_COUNT >= _EMBED_CIRCUIT_THRESHOLD:
                    _EMBED_CIRCUIT_OPEN_UNTIL = time.time() + _EMBED_CIRCUIT_COOLDOWN
                    logger.error(f"[EMBEDDING-SF] 熔断开启 {_EMBED_CIRCUIT_COOLDOWN}s（连续失败 {_EMBED_FAIL_COUNT} 次）")
                time.sleep(0.5)
        logger.error(f"[EMBEDDING-SF] embed_query失败(重试后): {last_err}")
        return [[0.0] * self._dim]

    def embed_documents(self, input: Documents) -> Embeddings:
        """ChromaDB插入文档时调用（批量embedding）"""
        return self(input)


class LocalEmbeddingFunction:
    """本地 ONNX 嵌入模型，零 API 调用，延迟降低 8x+。

    bge-small-zh-v1.5 实测：单条查询 3.7ms (CPU) vs 30-50ms (SiliconFlow API)。
    GPU 可选：EMBEDDING_USE_GPU=1 启用 CoreML/Metal 后端（对小模型加速不明显，留给未来大模型使用）。
    """

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._dim = None
        self._backend = None
        self._get_model()

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding

                use_gpu = os.getenv('EMBEDDING_USE_GPU', '0') == '1'
                if use_gpu:
                    providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
                    self._backend = 'CoreML(Metal/GPU)'
                else:
                    providers = ['CPUExecutionProvider']
                    self._backend = 'CPU'

                logger.info(f"[EMBEDDING] 加载本地模型: {self.model_name}（后端: {self._backend}）")
                self._model = TextEmbedding(
                    model_name=self.model_name,
                    providers=providers
                )
                test_vec = list(self._model.embed(["维度探测"]))
                self._dim = len(test_vec[0])
                logger.info(f"[EMBEDDING] 本地模型就绪: {self.model_name}, {self._dim}维, 后端={self._backend}")
            except ImportError:
                logger.error("[EMBEDDING] fastembed 未安装，请运行: pip install fastembed")
                raise
            except Exception as e:
                logger.error(f"[EMBEDDING] 模型加载失败: {e}")
                raise
        return self._model

    def name(self) -> str:
        return f"local-{self.model_name}"

    def __call__(self, input: Documents) -> Embeddings:
        model = self._get_model()
        embeddings = list(model.embed(input))
        return [e.tolist() for e in embeddings]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)


# ==================== 本地 Reranker ====================

class LocalReranker:
    """本地 CrossEncoder 重排器，零 API 调用。

    bge-reranker-base 实测：16条候选 CPU 307ms（vs SiliconFlow API 500ms+ 往返）。
    bge-reranker-v2-m3（560M）在 MPS/GPU 上反而更慢，故不用 GPU。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is not None:
            return cls._instance
        cls._instance = super().__new__(cls)
        cls._instance._init()
        return cls._instance

    def _init(self):
        self._model = None
        self._model_path = os.getenv(
            'LOCAL_RERANKER_PATH',
            '/Users/oygb/Downloads/GeometryAI-Mac-Build/models_cache/'
            'models--BAAI--bge-reranker-base/snapshots/'
            '2cfc18c9415c912f9d8155881c133215df768a70'
        )
        self._load()

    def _load(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            use_gpu = os.getenv('RERANKER_USE_GPU', '0') == '1'
            device = 'mps' if use_gpu else 'cpu'
            logger.info(f"[RERANK-LOCAL] 加载 bge-reranker-base（后端: {device}）")
            self._model = CrossEncoder(self._model_path, max_length=512, device=device)
            self._device = device
            # 预热
            self._model.predict([("__warmup__", "__warmup__")])
            logger.info(f"[RERANK-LOCAL] 本地 reranker 就绪（后端: {device}）")
        except Exception as e:
            logger.warning(f"[RERANK-LOCAL] 加载失败({e})，回退远程 API")
            self._model = None

    def rerank(self, query: str, documents: list, top_n: int = 20) -> dict:
        """返回格式与 SiliconFlow rerank API 一致：
        {'results': [{'index': i, 'relevance_score': float}, ...]}
        """
        if not self._model or not documents:
            return None
        try:
            pairs = [(query, doc) for doc in documents]
            scores = self._model.predict(pairs)
            # 按 score 降序，取 top_n
            indexed = [(i, float(s)) for i, s in enumerate(scores)]
            indexed.sort(key=lambda x: -x[1])
            indexed = indexed[:top_n]
            return {'results': [{'index': i, 'relevance_score': s} for i, s in indexed]}
        except Exception as e:
            logger.warning(f"[RERANK-LOCAL] 推理失败({e})，回退远程 API")
            return None


# ==================== VectorKnowledgeBase（含教学集合） ====================

class VectorKnowledgeBase:
    """
    使用 ChromaDB 向量数据库的共扼谱几何知识库。
    五个集合：
    - articles: 静态70篇文章知识（从文件目录构建）
    - learned: 动态学习的QA对（高质量对话自动存入）
    - corrections: 教学纠正记录（v10 新增）
    - antipatterns: 反模式库（v10 新增）
    - patches: 知识补丁（v10 新增）
    """

    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self.client = None
        self.articles_collection = None
        self.learned_collection = None
        self.corrections_collection = None
        self.antipatterns_collection = None
        self.patches_collection = None
        self.master_truth_collection = None  # 主库下发的已验证真理（只读）
        self._initialized = False
        self._articles_count = 0
        self._learned_count = 0
        self._corrections_count = 0
        self._antipatterns_count = 0
        self._patches_count = 0
        self._dim_stale_collections = set()  # 维度过期的集合名，不参与搜索
        self.bm25_searcher = BM25Searcher()  # BM25 关键词检索器
        self._last_index_mtime = 0.0  # 记录上次索引时最新的文件修改时间
        self._corr_emb_cache = {}  # {correction_id: embedding} 纠正文本嵌入缓存（correct 文本不变，避免每轮全量嵌入）
        self._articles_dir = ""  # articles 目录路径
        self._use_workspace = USE_WORKSPACE  # Workspace 中间层开关（转正）
        self._ws = None  # 中间层：emb矩阵/docs/metas/aids/summary_map/graph/sig
        self._articles_text: Dict[str, str] = {}  # 全内存模式：文章全文缓存（key=文件名，mtime变更自动重载）

        # 根据配置选择 embedding function
        # 强制使用 SiliconFlow 1024 维，不允许回退到 ChromaDB 默认 384 维
        if EMBEDDING_MODE == 'siliconflow':
            sf_key = os.getenv('SILICONFLOW_API_KEY', '')
            self.embedding_fn = SiliconFlowEmbeddingFunction(api_key=sf_key)
            self._embedding_name = "siliconflow(BAAI/bge-large-zh-v1.5)"
            logger.info("[EMBEDDING] SiliconFlow embedding 就绪（1024维，中文优化）")
        elif EMBEDDING_MODE == 'api':
            self.embedding_fn = APIEmbeddingFunction()
            self._embedding_name = f"api({GAI_EMBEDDING_MODEL})"
        elif EMBEDDING_MODE == 'local':
            try:
                self.embedding_fn = LocalEmbeddingFunction(LOCAL_EMBEDDING_MODEL)
                self._embedding_name = f"local({LOCAL_EMBEDDING_MODEL})"
            except Exception as e:
                logger.warning(f"[EMBEDDING] 本地模型加载失败({e})，回退到SiliconFlow")
                sf_key = os.getenv('SILICONFLOW_API_KEY', '')
                self.embedding_fn = SiliconFlowEmbeddingFunction(api_key=sf_key)
                self._embedding_name = "siliconflow(BAAI/bge-large-zh-v1.5)"
                logger.info("[EMBEDDING] SiliconFlow embedding 就绪（1024维，中文优化）")
        else:
            # 未知模式，强制使用 SiliconFlow（不允许 384 维 ChromaDB 默认）
            logger.warning(f"[EMBEDDING] 未知 EMBEDDING_MODE='{EMBEDDING_MODE}'，强制使用 SiliconFlow 1024维")
            sf_key = os.getenv('SILICONFLOW_API_KEY', '')
            self.embedding_fn = SiliconFlowEmbeddingFunction(api_key=sf_key)
            self._embedding_name = "siliconflow(BAAI/bge-large-zh-v1.5)"

        # 最终保底：如果 embedding_fn 仍为 None，强制 SiliconFlow
        if self.embedding_fn is None:
            sf_key = os.getenv('SILICONFLOW_API_KEY', '')
            self.embedding_fn = SiliconFlowEmbeddingFunction(api_key=sf_key)
            self._embedding_name = "siliconflow(BAAI/bge-large-zh-v1.5)"
            logger.warning("[EMBEDDING] embedding_fn 为 None，强制使用 SiliconFlow 1024维")

    def _get_embedding_dim(self) -> int:
        """探测当前 embedding function 的输出维度"""
        if self.embedding_fn is None:
            raise RuntimeError("[VECTOR] embedding_fn 不能为 None（强制 1024 维 SiliconFlow）")
        try:
            result = self.embedding_fn(["探测维度"])
            if result and len(result) > 0:
                return len(result[0])
        except Exception as e:
            logger.warning(f"[VECTOR] 探测 embedding 维度失败: {e}")
        # 根据 embedding 类型返回已知默认值
        if hasattr(self.embedding_fn, '_dim'):
            return self.embedding_fn._dim
        return 1024

    def _rebuild_collection_if_dim_mismatch(self, collection_name: str, description: str) -> Any:
        """
        检查集合的 embedding 维度是否与当前 embedding function 匹配。
        维度不匹配时一律删除重建（所有集合统一 1024 维），不再保留旧数据。

        安全措施：
        1. 检测 test embedding 是否为全零向量（API 失败的回退值），若是则跳过重建
        2. 只有当两个维度都有效且确实不同时才重建
        3. 重建时记录详细日志
        """
        try:
            existing = self.client.get_collection(collection_name)
            count = existing.count()
            if count == 0:
                return existing
            test_emb = self.embedding_fn(["维度检测测试"])
            if not test_emb or not test_emb[0]:
                logger.warning(f"[VECTOR] 集合 '{collection_name}' 维度检测: embedding 返回空，跳过重建")
                return None
            current_dim = len(test_emb[0])
            # 检测全零向量（API 失败回退），跳过重建避免误删
            if isinstance(test_emb[0], list) and all(v == 0.0 for v in test_emb[0]):
                logger.warning(
                    f"[VECTOR] 集合 '{collection_name}' 维度检测: embedding 返回全零向量"
                    f"（API 可能不可用），跳过重建以避免误删数据"
                )
                return None
            stored_dim = 0
            if count > 0:
                try:
                    sample = existing.get(limit=1, include=["embeddings"])
                    embs = sample.get('embeddings')
                    if embs is not None and len(embs) > 0:
                        stored_dim = len(embs[0])
                except Exception as e:
                    logger.debug(f"[VECTOR] 获取集合 '{collection_name}' 维度时出错: {e}")
            if current_dim > 0 and stored_dim > 0 and stored_dim != current_dim:
                logger.warning(
                    f"[VECTOR] 集合 '{collection_name}' 维度不匹配 "
                    f"(存储={stored_dim}, 当前={current_dim})，删除旧数据重建（统一当前嵌入维度）"
                )
                self.client.delete_collection(collection_name)
                col_kwargs = {}
                if self.embedding_fn is not None:
                    col_kwargs["embedding_function"] = self.embedding_fn
                return self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": description, "embedding_dim": current_dim},
                    **col_kwargs
                )
            # 维度一致但持久化嵌入配置与当前不一致（如被外部重建为 Chroma 默认嵌入）：
            # 用当前维度探测一次查询，失败说明配置损坏，必须删除重建，否则启动会抛
            # "Embedding function conflict" 导致整个向量库初始化失败。
            if current_dim > 0 and count > 0 and stored_dim > 0 and stored_dim == current_dim:
                try:
                    existing.query(query_embeddings=[test_emb[0]], n_results=1)
                except Exception as _qe:
                    logger.warning(
                        f"[VECTOR] 集合 '{collection_name}' 维度一致({stored_dim})但持久化嵌入配置异常，"
                        f"查询探测失败({_qe})，删除重建（统一当前嵌入）"
                    )
                    self.client.delete_collection(collection_name)
                    col_kwargs = {}
                    if self.embedding_fn is not None:
                        col_kwargs["embedding_function"] = self.embedding_fn
                    return self.client.get_or_create_collection(
                        name=collection_name,
                        metadata={"description": description, "embedding_dim": current_dim},
                        **col_kwargs
                    )
        except Exception as e:
            logger.debug(f"[VECTOR] 检查集合 '{collection_name}' 维度时出错: {e}")
        return None

    def initialize(self) -> bool:
        """初始化 ChromaDB 客户端和集合"""
        if not CHROMADB_AVAILABLE:
            logger.error("[VECTOR] chromadb 未安装，向量检索不可用")
            return False

        # 启动时验证 embedding function 可用性
        if self.embedding_fn is not None:
            try:
                test = self.embedding_fn(["启动测试"])
                if not test or not test[0]:
                    logger.error("[VECTOR] embedding function 返回空结果，请检查 API 连接")
                    return False
                if isinstance(test[0], list) and all(v == 0.0 for v in test[0]):
                    logger.error("[VECTOR] embedding function 返回全零向量，API Key 无效或网络不通")
                    return False
            except Exception as e:
                logger.error(f"[VECTOR] embedding function 不可用: {e}")
                return False

        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            # 构建 collection 参数
            col_kwargs = {}
            if self.embedding_fn is not None:
                col_kwargs["embedding_function"] = self.embedding_fn

            # 定义所有集合
            collections_config = [
                ("articles", "共扼谱几何70篇文章静态知识库"),
                ("learned", "动态学习的QA对"),
                ("corrections", "教学纠正记录"),
                ("antipatterns", "反模式库"),
                ("patches", "教学知识补丁"),
                ("personal", "个人数据：性格、感情、想法、记忆"),
                ("master_truth", "主库下发的已验证真理（只读，不可修改）"),
            ]

            for col_name, col_desc in collections_config:
                # 检查维度不匹配并自动重建
                rebuilt = self._rebuild_collection_if_dim_mismatch(col_name, col_desc)
                if rebuilt is not None:
                    setattr(self, f"{col_name}_collection" if col_name != "personal" else "personal_collection", rebuilt)
                else:
                    # 正常获取或创建；若持久化嵌入配置与当前不一致（如被外部重建为
                    # Chroma 默认嵌入），get_or_create 会抛冲突 → 删除重建，避免整个初始化失败
                    try:
                        col = self.client.get_or_create_collection(
                            name=col_name,
                            metadata={"description": col_desc},
                            **col_kwargs
                        )
                    except Exception as _ce:
                        _msg = str(_ce)
                        if ('embedding function' in _msg.lower()
                                or 'conflict' in _msg.lower()
                                or 'ambiguous' in _msg.lower()):
                            logger.warning(
                                f"[VECTOR] 集合 '{col_name}' 嵌入配置冲突，删除重建: {_ce}"
                            )
                            self.client.delete_collection(col_name)
                            col = self.client.get_or_create_collection(
                                name=col_name,
                                metadata={"description": col_desc},
                                **col_kwargs
                            )
                        else:
                            raise
                    attr_name = f"{col_name}_collection"
                    setattr(self, attr_name, col)

            self._articles_count = self.articles_collection.count()
            self._learned_count = self.learned_collection.count()
            self._corrections_count = self.corrections_collection.count()
            self._antipatterns_count = self.antipatterns_collection.count()
            self._patches_count = self.patches_collection.count()
            self._initialized = True
            # Workspace 中间层（加速层：暴力检索+动态图；失败自动回退旧路径）
            try:
                self._workspace_init()
            except Exception as _wse:
                logger.warning(f"[WS] 中间层初始化异常（回退旧路径）: {_wse}")
                self._use_workspace = False
            logger.info(
                f"[VECTOR] ChromaDB 初始化成功 | "
                f"articles: {self._articles_count} | learned: {self._learned_count} | "
                f"corrections: {self._corrections_count} | antipatterns: {self._antipatterns_count} | "
                f"patches: {self._patches_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[VECTOR] ChromaDB 初始化失败: {e}")
            return False


    def _workspace_init(self) -> bool:
        """初始化 Workspace 中间层：全量 embeddings + 文本 + 摘要地图 + 动态引用图。
        加速层：失败时 _use_workspace=False 自动回退旧路径（HNSW + 静态引用图）。"""
        if not self._use_workspace:
            return False
        if self._ws is not None:
            return True
        try:
            all_data = self._safe_collection_call(
                'articles_collection', 'get',
                include=['embeddings', 'documents', 'metadatas'])
            if not all_data or not all_data.get('ids'):
                logger.warning("[WS] 全量加载失败（空集合），回退旧路径")
                self._use_workspace = False
                return False
            emb = np.array(all_data['embeddings'], dtype=np.float32)
            norm = np.linalg.norm(emb, axis=1, keepdims=True)
            norm[norm == 0] = 1.0
            emb = emb / norm
            docs = all_data['documents'] or []
            metas = all_data['metadatas'] or [{}] * len(docs)
            aids = []
            for _m in metas:
                _fn = (_m or {}).get('fname', '')
                _mm = re.match(r'^(\d{1,2})\.(\d{1,2})', _fn)
                # 完整 X.Y 编号（此前误用 group(1) 只取首位，导致 id_fname 键与图节点 X.Y 不一致）
                aids.append(f"{_mm.group(1)}.{_mm.group(2)}" if _mm else '')
            self._ws = {
                'emb': emb, 'docs': docs, 'metas': metas, 'aids': aids,
                'summary_map': None, 'graph': None, 'sig': None,
            }
            # ===== CPU 优化：一次性建立两类常用索引，查询 O(1)，避免每次全表扫 metas =====
            _fname_idx, _id_fname = {}, {}
            for _i, _m in enumerate(metas):
                _fn = (_m or {}).get('fname', '') or ''
                if _fn:
                    _fname_idx.setdefault(_fn, []).append(_i)
                _aid = aids[_i]
                if _aid and _aid not in _id_fname:
                    _id_fname[_aid] = _fn
            self._ws['fname_idx'] = _fname_idx
            self._ws['id_fname'] = _id_fname
            self._workspace_scan_articles()
            logger.info(
                f"[WS] 中间层就绪: {emb.shape[0]} chunks x {emb.shape[1]} 维 | "
                f"摘要 {(self._ws.get('summary_map') or {}) and len(self._ws['summary_map'])} 篇 | "
                f"引用图 {(self._ws.get('graph') or {}) and len(self._ws['graph'])} 篇")
            return True
        except Exception as e:
            logger.warning(f"[WS] 中间层初始化失败，回退旧路径: {e}")
            self._use_workspace = False
            self._ws = None
            return False

    def _workspace_scan_articles(self):
        """扫描文章目录：构建摘要地图 + 动态引用图（内存，mtime 自动失效）。"""
        articles_dir = self._articles_dir or UPLOAD_FOLDER
        if not articles_dir or not os.path.isdir(articles_dir):
            return
        files = sorted(glob.glob(os.path.join(articles_dir, '*.md')))
        if not files:
            return
        sig = tuple((f, os.path.getmtime(f)) for f in files)
        ws = self._ws
        if ws.get('sig') == sig and ws.get('summary_map') is not None:
            return  # 无变更，复用内存结果
        # 文章目录有变更：embeddings 矩阵标记过期（下次查询重载，保持与新文章一致）
        # 仅当已有旧快照（非首次加载）且发生变更时标记；首次加载不标记（无旧数据可失效）
        if ws.get('sig') is not None:
            ws['emb_stale'] = True
        _pat_xyz = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})\.(\d{1,2})(?![0-9.])')
        _pat_xy = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])')
        summaries, graph = {}, {}
        for f in files:
            base = os.path.basename(f)
            _m = re.match(r'^(\d{1,2})\.(\d{1,2})_', base)
            if not _m:
                continue
            aid = f"{_m.group(1)}.{_m.group(2)}"
            try:
                raw = open(f, encoding='utf-8').read()
            except Exception:
                continue
            self._articles_text[base] = raw  # 全内存：全文缓存（mtime 变更时 sig 失效自动重载覆盖）
            # 摘要（编号 + 标题 + 摘要首句，去公式）
            title = ''
            _tm = re.search(r'^#\s+(.+)$', raw, re.M)
            if _tm:
                title = _tm.group(1).strip()
            _am = re.search(r'##\s*摘要\s*\n+(.+?)(?:\n\n|\n---|\Z)', raw, re.DOTALL)
            _abs = ''
            if _am:
                _abs = re.sub(r'\s+', ' ', _am.group(1)).strip()
                _abs = re.sub(r'\$[^$]*\$', '', _abs)
                if len(_abs) > 120:
                    _abs = _abs[:120] + '…'
            summaries[aid] = f"{aid} {title}：{_abs}" if title else f"{aid}：{_abs}"
            # 引用出边（去目录/公式，引用计数）
            text = re.sub(r'##\s*目\s*录.*?(?=\n##|\n---|\Z)', '', raw, flags=re.DOTALL)
            text = re.sub(r'\$[^$]*\$', ' ', text)
            outs = {}
            consumed = set()
            for _mm in _pat_xyz.finditer(text):
                _ref = f"{_mm.group(1)}.{_mm.group(2)}"
                if _ref == aid:
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '\u3000':
                    continue
                if _mm.start() > 0 and text[_mm.start() - 1] in '§#':
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '%':
                    continue
                outs[_ref] = outs.get(_ref, 0) + 1
                consumed.add((_mm.start(), _mm.end()))
            for _mm in _pat_xy.finditer(text):
                if any(_s <= _mm.start() < _e for _s, _e in consumed):
                    continue
                _ref = f"{_mm.group(1)}.{_mm.group(2)}"
                if _ref == aid:
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '\u3000':
                    continue
                if _mm.start() > 0 and text[_mm.start() - 1] in '§#':
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '%':
                    continue
                outs[_ref] = outs.get(_ref, 0) + 1
            graph[aid] = outs
        ws['summary_map'] = summaries
        ws['graph'] = graph
        ws['sig'] = sig
        # ===== 关系运算预计算（CPU 优化：启动一次，查询常驻，避免每次重建） =====
        try:
            # 反索引 in_idx[article] -> set(依赖它的文章)，供多跳骨架 O(1) 反查
            in_idx = {}
            for src, outs_items in graph.items():
                for tgt in outs_items:
                    in_idx.setdefault(tgt, set()).add(src)
            # 双向互引（A⇄B 互证闭环）
            bidir_pairs = set()
            bidir_map = {}
            for a in graph:
                for b in graph[a]:
                    if b in graph and a in graph[b] and a < b:
                        bidir_pairs.add((a, b))
            bidir_map = {}
            for a, b in bidir_pairs:
                bidir_map.setdefault(a, []).append(b)
                bidir_map.setdefault(b, []).append(a)
            # 跳跃闭包：每个入口的 1/2/3 跳可达集（含中间层权重衰减结果）
            def _reachable_set(start, hops):
                seen = {start}
                frontier = {start}
                for _ in range(hops):
                    nxt = set()
                    for a in frontier:
                        nxt |= {b for b in graph.get(a, {}) if b not in seen}
                    if not nxt:
                        break
                    seen |= nxt
                    frontier = nxt
                seen.discard(start)
                return seen
            hop_closure = {a: {1: _reachable_set(a, 1),
                                2: _reachable_set(a, 2),
                                3: _reachable_set(a, 3)}
                           for a in graph}
            # 引用共现簇：两篇文章被同一批文章共同引用（同族联动），预计算 Top 对
            co = {}
            for src, outs_items in graph.items():
                refs = sorted(outs_items)
                for i in range(len(refs)):
                    for j in range(i + 1, len(refs)):
                        a, b = refs[i], refs[j]
                        if a == b:
                            continue
                        key = (a, b) if a < b else (b, a)
                        co[key] = co.get(key, 0) + 1
            top_co = sorted(co.items(), key=lambda x: -x[1])[:40]
            ws['_rel'] = {
                'in_idx': in_idx,
                'bidir': bidir_map,
                'bidir_pairs': len(bidir_pairs),
                'hops': hop_closure,
                'co': {f"{k[0]}↔{k[1]}": v for k, v in top_co},
            }
        except Exception as e:
            logger.error(f"[WS] 关系预计算失败: {e}")
            ws['_rel'] = None

    # ---------- 全内存模式（中间层） ----------
    def preload_all(self, articles_dir: str = "") -> dict:
        """全内存预热：文章全文 + 摘要图 + 引用图一次性载入内存。
        调用后，向量检索、文章读取、引用查询全部在内存完成。
        返回统计（供启动日志）。"""
        if articles_dir:
            self._articles_dir = articles_dir
        self.initialize()
        self._workspace_scan_articles()
        self._preload_recursive()  # 子目录 + 非编号文章全文也进内存
        chars = sum(len(t) for t in self._articles_text.values())
        ws = self._ws or {}
        return {
            "articles_in_memory": len(self._articles_text),
            "chars": chars,
            "mb": round(chars * 2 / 1e6, 1),  # UTF-8 中文约 2 字节/字符
            "chunks": self.total_docs,
            "summary_map": len(ws.get('summary_map', {})),
            "graph_edges": sum(len(v) for v in ws.get('graph', {}).values()),
            "articles_text_mb": round(chars * 2 / 1e6, 1),
        }

    def _preload_recursive(self) -> int:
        """递归扫描全部子目录 .md，全文缓存进内存（排除归档等目录）。"""
        base = self._articles_dir or UPLOAD_FOLDER
        skip = {'.obsidian', 'Attachments', 'Templates', 'copilot', 'archive',
                '.git', '__pycache__', 'articles_renumber_backup'}
        n = 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip]
            for f in files:
                if not f.endswith('.md'):
                    continue
                rel = os.path.relpath(os.path.join(root, f), base)
                if rel in self._articles_text:
                    continue
                try:
                    raw = open(os.path.join(root, f), encoding='utf-8').read()
                except Exception:
                    continue
                self._articles_text[rel] = raw
                n += 1
        return n

    def refresh_article_cache(self, fpath: str, filename: str) -> None:
        """文章已变更（write/append/edit 工具调用后）：刷新内存缓存。"""
        key = filename if filename in self._articles_text else os.path.basename(filename)
        if key not in self._articles_text:
            key = os.path.relpath(fpath, self._articles_dir or UPLOAD_FOLDER)
        try:
            raw = open(fpath, encoding='utf-8').read()
            self._articles_text[key] = raw
        except Exception:
            pass

    def get_article_text(self, filename: str) -> Optional[str]:
        """内存优先的文章全文读取（全内存模式）。
        先精确 key，再 basename 兼容；miss 时读盘并缓存。"""
        if filename in self._articles_text:
            return self._articles_text[filename]
        base = os.path.basename(filename)
        if base in self._articles_text:
            return self._articles_text[base]
        # 子目录兼容：遍历 key 找 basename 匹配（子目录文章，全内存）
        for _k, _v in self._articles_text.items():
            if os.path.basename(_k) == base:
                return _v
        p = os.path.join(self._articles_dir or UPLOAD_FOLDER, filename)
        if os.path.isfile(p):
            try:
                raw = open(p, encoding='utf-8').read()
                self._articles_text[base] = raw
                return raw
            except Exception:
                return None
        return None

    def memory_stats(self) -> dict:
        """全内存数据统计。"""
        chars = sum(len(t) for t in self._articles_text.values())
        return {
            "articles_in_memory": len(self._articles_text),
            "articles_text_mb": round(chars * 2 / 1e6, 1),
            "chunks": self.total_docs,
        }

    def _workspace_query_results(self, qvec, n) -> Optional[dict]:
        """暴力检索 top-n，返回 ChromaDB query 兼容格式 {'documents': [[..]], 'metadatas': [[..]], 'distances': [[..]]}。
        异常返回 None（上层回退 ChromaDB）。"""
        try:
            ws = self._ws
            if ws is None or qvec is None:
                return None
            # 文章目录变更后 embeddings 过期：重载（保持与新文章一致）
            if ws.get('emb_stale'):
                logger.info("[WS] 检测到文章变更，重载 embeddings 矩阵")
                self._ws = None
                self._workspace_init()
                ws = self._ws
                if ws is None:
                    return None
            q = np.asarray(qvec, dtype=np.float32)
            nq = np.linalg.norm(q)
            if nq > 0:
                q = q / nq
            sims = ws['emb'] @ q  # (N,) cosine 相似度
            top = np.argsort(-sims)[:n]
            docs, metas, dists = [], [], []
            for i in top:
                _m = ws['metas'][i] or {}
                docs.append(ws['docs'][i])
                metas.append(_m)
                dists.append(float(1.0 - sims[i]))
            return {'documents': [docs], 'metadatas': [metas], 'distances': [dists]}
        except Exception as e:
            logger.warning(f"[WS] 暴力检索异常: {e}")
            return None

    def _workspace_skeleton(self, entry_ids, max_skeleton=3, max_hops=2):
        """
        多跳引用图骨架：从入口文章出发，沿 out/in 依赖图逐层向外扩展 max_hops 跳。
        权重沿跳数衰减（out 2->1.4->1，in 1->0.7->0.5），每跳距离越远权重越低，
        从而"一层一层"拉取相关定理，而不再只停在直接邻居。
        返回 [(文章编号, 累积权重)]，已按权重降序截断为 max_skeleton 个。
        """
        graph = self._ws.get('graph') or {}
        # 反索引：启动时已预计算并常驻缓存（_rel.in_idx），O(1) 反查，避免每次重建
        _rel = self._ws.get('_rel') or {}
        in_idx = _rel.get('in_idx')
        if in_idx is None:
            # 兜底：缓存缺失时再现场构建
            in_idx = {}
            for src, outs_items in graph.items():
                for tgt in outs_items:
                    in_idx.setdefault(tgt, set()).add(src)
        _hops = getattr(self, '_graph_max_hops', 2)
        neigh: Dict[str, float] = {}
        frontier = set(entry_ids)
        visited = set(entry_ids)
        out_decay = 2.0 ** -0.5  # 1, 0.71, 0.5 ...
        in_decay = 1.0 ** -0.5   # 1, 1, 1 （in 已较轻，衰减放缓）
        cur_out_w, cur_in_w = 2.0, 1.0
        for hop in range(_hops):
            if not frontier:
                break
            next_frontier = set()
            for nid in frontier:
                # out 邻居：nid 依赖的文章（nid→tgt）
                for tgt, cnt in (graph.get(nid) or {}).items():
                    if tgt in visited:
                        continue
                    neigh[tgt] = neigh.get(tgt, 0) + cur_out_w * cnt
                    next_frontier.add(tgt)
                # in 邻居：依赖 nid 的文章（src→nid）
                for src in (in_idx.get(nid) or set()):
                    if src in visited:
                        continue
                    cnt = (graph.get(src) or {}).get(nid, 1)
                    neigh[src] = neigh.get(src, 0) + cur_in_w * cnt
                    next_frontier.add(src)
            visited |= next_frontier
            frontier = next_frontier
            cur_out_w *= out_decay
            cur_in_w *= in_decay
        skeleton = sorted(
            ((nid, c) for nid, c in neigh.items() if nid not in entry_ids),
            key=lambda x: -x[1])[:max_skeleton]
        return skeleton

    def get_relation_context(self, entry_ids, top=6) -> str:
        """把【启动时已预计算】的关系结构（入向/出向邻接、双向互引闭环、高共引关联）
        转成紧凑提示文本，供多跳推导注入 LLM 作为关系上下文——各文章引用千丝万缕，
        直接给出可用编号，模型照追即可，无需沿途反复 vector_search。"""
        if not entry_ids or self._ws is None:
            return ""
        _ws = self._ws
        _rel = _ws.get('_rel') or {}
        in_idx = _rel.get('in_idx') or {}
        graph = _ws.get('graph') or {}
        entry = set(entry_ids)
        lines = []
        in_srcs, out_tgts = set(), set()
        for e in entry:
            in_srcs |= (in_idx.get(e) or set())
            out_tgts |= (graph.get(e, {}) or {}).keys()
        in_srcs -= entry
        out_tgts -= entry
        if out_tgts:
            lines.append("这些入口文章依赖(出向): " + "、".join(sorted(out_tgts)[:top]))
        if in_srcs:
            lines.append("依赖这些入口文章(入向): " + "、".join(sorted(in_srcs)[:top]))
        bidir = _rel.get('bidir') or {}
        strict = [b for e in entry for b in bidir.get(e, [])]
        if strict:
            lines.append("双向互引闭环(互为前置): " + "、".join(sorted(set(strict))[:top]))
        co = _rel.get('co') or {}
        if co:
            lines.append("高共引关联(常被同批文章引用): " + "、".join(list(co.keys())[:top]))
        if not lines:
            return ""
        return "[引用关系图-预计算]" + " | ".join(lines)

    def _workspace_chunks_for(self, fname, qvec=None, chunks_per_article=1):
        """从内存全量 documents 按 fname 过滤，返回该文章 top 相关 chunk（骨架用）。"""
        ws = self._ws
        idxs = list((ws.get('fname_idx') or {}).get(fname) or [])
        if not idxs:
            return []
        if qvec is not None and len(idxs) > chunks_per_article:
            q = np.asarray(qvec, dtype=np.float32)
            nq = np.linalg.norm(q)
            if nq > 0:
                q = q / nq
            sims = ws['emb'][idxs] @ q
            order = np.argsort(-sims)[:chunks_per_article]
            idxs = [idxs[i] for i in order]
        else:
            idxs = idxs[:chunks_per_article]
        out = []
        for i in idxs:
            _m = ws['metas'][i] or {}
            out.append({
                'id': _m.get('chunk_id', ''),
                'text': ws['docs'][i],
                'source': 'articles',
                'metadata': _m,
                'distance': 0.0,
                '_skeleton': True,
                'label': f"[引用图骨架:{fname}] 文章库: {_m.get('fname', '未知')}"
            })
        return out

    def _enrich_with_workspace(self, results, query, max_skeleton=3, chunks_per_article=1):
        """Workspace 动态骨架增强：动态引用图（内存）+ 内存拉取骨架 chunk。"""
        if not results:
            return results, []
        entry_ids = set()
        for r in results:
            fname = r.get('metadata', {}).get('fname', '') or ''
            _m = re.match(r'^(\d{1,2}\.\d{1,2})', fname)
            if _m:
                entry_ids.add(_m.group(1))
        if not entry_ids:
            logger.info(f"[GRAPH-DIAG] 无入口编号(结果fname无可匹配 X.Y 前缀): n_results={len(results)}")
            return results, []
        skeleton = self._workspace_skeleton(entry_ids, max_skeleton)
        if not skeleton:
            logger.info(f"[GRAPH-DIAG] 骨架为空: 入口={sorted(entry_ids)} (引用图节点 {len(self._ws.get('graph') or {})})")
            return results, []
        id_to_fname = (self._ws.get('id_fname') or {})  # 启动时已预计算，免每查询 os.listdir
        _qvec = self._get_query_embedding(query)
        # 预计算关系上下文(入向/出向/双向互引/高共引)注入，帮模型照图追文
        _relctx = self.get_relation_context(entry_ids)
        logger.info(f"[GRAPH-DIAG] 入口={sorted(entry_ids)} 骨架={[n for n,_ in skeleton]} relctx_len={len(_relctx)}")
        new_chunks = []
        for nid, cnt in skeleton:
            fname = id_to_fname.get(nid)
            if not fname:
                logger.info(f"[GRAPH-DIAG] 骨架 {nid} 无 id_fname 映射")
                continue
            for c in self._workspace_chunks_for(fname, _qvec, chunks_per_article):
                c['label'] = f"[引用图骨架:{nid}({cnt}次)] 文章库: {c.get('metadata', {}).get('fname', fname)}"
                new_chunks.append(c)
        if not new_chunks:
            logger.info(f"[GRAPH-DIAG] 骨架chunk解析为空: 骨架={[n for n,_ in skeleton]} id_fname数={len(id_to_fname)}")
            return results, []
        existing_ids = set()
        for r in results:
            cid = r.get('id') or r.get('metadata', {}).get('chunk_id', '')
            if cid:
                existing_ids.add(cid)
        skeleton_chunks = [c for c in new_chunks if (c.get('id') or '') not in existing_ids]
        if _relctx:
            skeleton_chunks.insert(0, {
                'id': '', 'text': _relctx, 'source': 'logic_graph',
                'metadata': {'fname': ''}, 'distance': 0.0, '_skeleton': True,
                'label': '[引用关系图] 预计算关系上下文',
            })
        merged = skeleton_chunks + results
        return merged, [c['label'] for c in skeleton_chunks]


    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def _refresh_collection(self, attr_name: str) -> Any:
        """
        重新获取 collection 引用（当检测到陈旧引用时调用）。
        当另一个进程（如 sync_chromadb.py）删除并重建集合后，
        当前进程持有的 Collection 对象内部 UUID 会失效，
        此方法通过集合名称重新获取有效引用。
        """
        col_name = attr_name.replace('_collection', '')
        try:
            col_kwargs = {}
            if self.embedding_fn is not None:
                col_kwargs["embedding_function"] = self.embedding_fn
            fresh = self.client.get_or_create_collection(
                name=col_name,
                **col_kwargs
            )
            setattr(self, attr_name, fresh)
            logger.info(f"[VECTOR] 集合 '{col_name}' 引用已刷新 (新UUID)")
            return fresh
        except Exception as e:
            logger.error(f"[VECTOR] 刷新集合 '{col_name}' 失败: {e}")
            return getattr(self, attr_name, None)

    def _safe_collection_call(self, attr_name: str, method_name: str, *args, **kwargs):
        """
        安全执行 collection 操作，自动恢复陈旧引用。

        当另一个进程（如 sync_chromadb.py）删除并重建集合时，
        当前进程持有的 Collection 对象引用会失效，操作时会抛出
        "Collection [UUID] does not exist" 错误。
        此方法检测此类错误并自动刷新引用后重试一次。
        """
        collection = getattr(self, attr_name, None)
        if collection is None:
            return None
        try:
            return getattr(collection, method_name)(*args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "does not exist" in err_str or "not found" in err_str:
                logger.warning(
                    f"[VECTOR] 检测到陈旧集合引用 ({attr_name}.{method_name}): {e}，正在刷新..."
                )
                fresh = self._refresh_collection(attr_name)
                if fresh is not None:
                    logger.info(f"[VECTOR] 集合引用已刷新，重试操作 {attr_name}.{method_name}")
                    return getattr(fresh, method_name)(*args, **kwargs)
            raise

    @property
    def articles_count(self) -> int:
        if self.articles_collection:
            try:
                self._articles_count = self._safe_collection_call('articles_collection', 'count')
            except Exception:
                pass
        return self._articles_count

    @property
    def learned_count(self) -> int:
        if self.learned_collection:
            try:
                self._learned_count = self._safe_collection_call('learned_collection', 'count')
            except Exception:
                pass
        return self._learned_count

    @property
    def corrections_count(self) -> int:
        if self.corrections_collection:
            try:
                self._corrections_count = self._safe_collection_call('corrections_collection', 'count')
            except Exception:
                pass
        return self._corrections_count

    @property
    def antipatterns_count(self) -> int:
        if self.antipatterns_collection:
            try:
                self._antipatterns_count = self._safe_collection_call('antipatterns_collection', 'count')
            except Exception:
                pass
        return self._antipatterns_count

    @property
    def patches_count(self) -> int:
        if self.patches_collection:
            try:
                self._patches_count = self._safe_collection_call('patches_collection', 'count')
            except Exception:
                pass
        return self._patches_count

    @property
    def total_docs(self) -> int:
        return self.articles_count + self.learned_count

    def smart_chunk(self, content: str, article_id: str, fname: str) -> List[Dict]:
        """智能分块：优先在段落或句子边界处切分"""
        chunks = []
        start = 0
        length = len(content)
        while start < length:
            target_end = min(start + CHUNK_SIZE, length)
            if target_end < length:
                search_range = content[target_end:min(target_end + 200, length)]
                best_break = target_end
                para_match = re.search(r'\n\n', search_range)
                if para_match:
                    best_break = target_end + para_match.start()
                else:
                    sentence_end = re.search(r'[\u3002\.\?\!]\s', search_range)
                    if sentence_end:
                        best_break = target_end + sentence_end.start() + 2
                target_end = min(best_break, length)
            chunk_text = content[start:target_end]
            chunks.append({
                'article_id': article_id,
                'fname': fname,
                'text': chunk_text,
                'start': start,
                'end': target_end
            })
            start += max(target_end - start - CHUNK_OVERLAP, CHUNK_SIZE // 2)
        return chunks

    def build_index(self, articles_dir: str) -> Dict[str, Any]:
        """
        读取文章目录，分块后存入 articles 集合。
        如果 articles 集合已有数据，先清空再重建。
        """
        diag = {
            "dir_exists": False,
            "files_found": 0,
            "files_indexed": 0,
            "total_chunks": 0,
            "errors": []
        }
        if not self._initialized:
            diag["errors"].append("ChromaDB 未初始化")
            logger.error("[VECTOR] ChromaDB 未初始化，无法构建索引")
            return diag

        if not os.path.exists(articles_dir):
            diag["errors"].append(f"文章目录不存在: {articles_dir}")
            logger.error(f"[VECTOR] 文章目录不存在: {articles_dir}")
            return diag

        diag["dir_exists"] = True
        valid_exts = ('.md', '.txt', '.py', '.tex', '.rst', '.markdown')

        # 读取与分块
        all_chunks = []
        for fname in sorted(os.listdir(articles_dir)):
            fpath = os.path.join(articles_dir, fname)
            if not os.path.isfile(fpath):
                continue

            has_valid_ext = fname.endswith(valid_exts)
            is_text = False
            if not has_valid_ext:
                try:
                    with open(fpath, 'rb') as f:
                        sample = f.read(1024)
                        is_text = all(b < 128 or b >= 128 for b in sample) and b'\x00' not in sample
                except Exception:
                    pass
            if not (has_valid_ext or is_text):
                continue

            diag["files_found"] += 1
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                diag["errors"].append(f"读取失败 {fname}: {e}")
                continue

            article_id = fname
            file_chunks = self.smart_chunk(content, article_id, fname)
            all_chunks.extend(file_chunks)
            diag["files_indexed"] += 1

        if not all_chunks:
            diag["errors"].append("没有索引到任何有效文档")
            logger.warning("[VECTOR] 没有索引到任何文档")
            return diag

        # 安全重建策略：
        # 1. 先用第一批数据测试 embedding 是否可用
        # 2. 测试通过后才删除旧集合
        # 3. 如果中途失败，记录错误，旧集合已被删但至少日志中有记录
        batch_size = 500
        failed_batches = 0
        success_chunks = 0

        # 构建所有 chunk 数据
        all_ids = []
        all_documents = []
        all_metadatas = []
        for chunk in all_chunks:
            fname_hash = hashlib.md5(chunk['fname'].encode()).hexdigest()[:6]
            chunk_id = f"art_{chunk['article_id']}_{fname_hash}_{chunk['start']}_{chunk['end']}"
            all_ids.append(chunk_id)
            all_documents.append(chunk['text'])
            all_metadatas.append({
                "article_id": chunk['article_id'],
                "fname": chunk['fname'],
                "start": chunk['start'],
                "end": chunk['end'],
                "source": "articles",
                "chunk_id": chunk_id,
            })

        # 预检查：用第一批测试 embedding 可用性
        try:
            test_result = self.embedding_fn(all_documents[:1])
            # 检查返回值是否为有效 embedding（非全零）
            if test_result and isinstance(test_result[0], list):
                test_dim = len(test_result[0])
                if all(v == 0.0 for v in test_result[0]):
                    diag["errors"].append(f"Embedding API 返回全零向量（API Key 无效或网络不通），无法构建有效索引。请检查 SILICONFLOW_API_KEY 或 GAI_API_KEY 配置。")
                    logger.error(f"[VECTOR] Embedding 预检查失败：返回全零向量，API 不可用")
                    return diag
            elif test_result is None:
                diag["errors"].append("Embedding 返回 None，API 不可用")
                return diag
        except Exception as e:
            diag["errors"].append(f"Embedding 预检查失败（旧索引保留）: {e}")
            logger.error(f"[VECTOR] Embedding 预检查失败，放弃重建: {e}")
            return diag
        logger.info(f"[VECTOR] Embedding 预检查通过，开始重建索引 ({len(all_chunks)} 块)")

        # 删除旧集合
        try:
            self.client.delete_collection("articles")
        except Exception as e:
            logger.warning(f"[VECTOR] 清空 articles 集合时出错（可能为空）: {e}")

        self.articles_collection = self.client.get_or_create_collection(
            name="articles",
            metadata={"description": "共扼谱几何70篇文章静态知识库"},
            embedding_function=self.embedding_fn
        )

        # 批量插入
        for batch_start in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[batch_start:batch_start + batch_size]
            batch_docs = all_documents[batch_start:batch_start + batch_size]
            batch_meta = all_metadatas[batch_start:batch_start + batch_size]
            try:
                self._safe_collection_call(
                    'articles_collection', 'add',
                    ids=batch_ids, documents=batch_docs, metadatas=batch_meta
                )
                success_chunks += len(batch_ids)
            except Exception as e:
                failed_batches += 1
                diag["errors"].append(f"批量插入失败 (批次{batch_start//batch_size+1}): {e}")
                logger.error(f"[VECTOR] 批量插入失败 (批次{batch_start//batch_size+1}): {e}")

        self._articles_count = self._safe_collection_call('articles_collection', 'count')
        diag["total_chunks"] = self._articles_count
        logger.info(
            f"[VECTOR] 索引完成: {diag['files_indexed']} 个文件, "
            f"{self._articles_count} 个文本块"
        )

        # 构建 BM25 倒排索引（用于关键词检索补充）
        bm25_chunks = []
        if all_ids and all_documents:
            for i, cid in enumerate(all_ids):
                bm25_chunks.append({'id': cid, 'text': all_documents[i] if i < len(all_documents) else ''})
        if bm25_chunks:
            self.bm25_searcher.build_index(bm25_chunks)
            diag["bm25_indexed"] = self.bm25_searcher.chunk_count

        # 重放所有有效纠正到新索引
        replay = self._replay_all_corrections()
        diag["corrections_replayed"] = replay

        # 记录当前最新的文件修改时间
        self._articles_dir = articles_dir
        self._update_index_mtime(articles_dir)

        return diag

    def index_single_file(self, filepath: str) -> None:
        """增量索引单个文件（不重建整个索引）。如果文件不存在则清理旧索引。"""
        if not self._initialized:
            return
        fname = os.path.basename(filepath)

        # 如果文件不存在，只清理旧索引
        if not os.path.exists(filepath):
            logger.info(f"[VECTOR] 文件不存在，清理旧索引: {fname}")
            try:
                self._safe_collection_call('articles_collection', 'delete', where={"fname": fname})
            except Exception:
                pass
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"[VECTOR] 读取文件失败 {fname}: {e}")
            return

        article_id = fname

        # 先删除该文件的旧索引
        try:
            self._safe_collection_call('articles_collection', 'delete', where={"fname": fname})
        except Exception:
            pass

        # 分块并插入
        chunks = self.smart_chunk(content, article_id, fname)
        if not chunks:
            return

        fname_hash = hashlib.md5(fname.encode()).hexdigest()[:6]
        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"art_{article_id}_{fname_hash}_{chunk['start']}_{chunk['end']}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append({
                "article_id": chunk.get('article_id', article_id),
                "fname": chunk.get('fname', fname),
                "start": chunk.get('start', 0),
                "end": chunk.get('end', 0),
                "source": "articles",
                "chunk_id": chunk_id,
            })

        try:
            self._safe_collection_call('articles_collection', 'add',
                ids=ids, documents=documents, metadatas=metadatas)
            self._articles_count = self._safe_collection_call('articles_collection', 'count')
            logger.info(f"[VECTOR] 增量索引: {fname} ({len(chunks)} 块), 总计 {self._articles_count} 块")

            # 同步更新 BM25 倒排索引
            self._update_bm25_for_file(fname, ids, documents)
            # 更新文件修改时间戳
            if self._articles_dir:
                self._update_index_mtime(self._articles_dir)
        except Exception as e:
            logger.error(f"[VECTOR] 增量索引失败 {fname}: {e}")

    def _update_bm25_for_file(self, fname: str, chunk_ids: list, chunk_docs: list) -> None:
        """
        文件变更后重建 BM25 倒排索引。
        由于 BM25 不存 fname 映射，无法精确移除旧 chunk 的 token，
        所以直接从 ChromaDB 全量重建（纯内存操作，3000 chunks 约 3-5 秒）。
        """
        self.bm25_searcher._ensure_jieba()
        if not self.bm25_searcher._jieba_loaded:
            return
        try:
            all_data = self._safe_collection_call('articles_collection', 'get', include=['documents'])
            bm25_chunks = []
            for i, cid in enumerate(all_data['ids']):
                bm25_chunks.append({
                    'id': cid,
                    'text': all_data['documents'][i] if i < len(all_data['documents']) else ''
                })
            self.bm25_searcher.build_index(bm25_chunks)
            logger.info(f"[BM25] 全量重建完成: {self.bm25_searcher.chunk_count} chunks")
        except Exception as e:
            logger.debug(f"[BM25] 重建失败: {e}")

    def _update_index_mtime(self, articles_dir: str) -> None:
        """扫描 articles_dir 下所有文件，记录最新的修改时间"""
        try:
            valid_exts = ('.md', '.txt', '.py', '.tex', '.rst', '.markdown')
            max_mtime = 0.0
            for fname in os.listdir(articles_dir):
                if fname.endswith(valid_exts) and os.path.isfile(os.path.join(articles_dir, fname)):
                    mt = os.path.getmtime(os.path.join(articles_dir, fname))
                    if mt > max_mtime:
                        max_mtime = mt
            self._last_index_mtime = max_mtime
        except Exception:
            pass

    def check_and_sync_stale(self) -> int:
        """
        检查 articles 目录中是否有比索引更新的文件。
        如果有，自动增量索引这些文件并重建 BM25。
        返回同步的文件数。
        """
        if not self._initialized or not self._articles_dir:
            return 0
        try:
            valid_exts = ('.md', '.txt', '.py', '.tex', '.rst', '.markdown')
            stale_files = []
            for fname in os.listdir(self._articles_dir):
                fpath = os.path.join(self._articles_dir, fname)
                if fname.endswith(valid_exts) and os.path.isfile(fpath):
                    if os.path.getmtime(fpath) > self._last_index_mtime:
                        stale_files.append(fpath)

            if not stale_files:
                return 0

            synced = 0
            for fpath in stale_files:
                self.index_single_file(fpath)
                synced += 1

            # 重建 BM25（index_single_file 内部已调用，但多文件场景确保一次）
            if synced > 1:
                self._update_bm25_for_file(f"batch_{synced}_files", [], [])

            self._update_index_mtime(self._articles_dir)
            logger.info(f"[VECTOR] 自动同步了 {synced} 个变更文件")
            return synced
        except Exception as e:
            logger.debug(f"[VECTOR] 检查文件变更失败: {e}")
            return 0

    def _expand_query_synonyms(self, query: str) -> List[str]:
        """
        利用 TERM_SYNONYMS 对查询进行同义词扩展，生成变体查询。
        例如："精细结构常数 alpha" -> 扩展 "精细结构常数 s_e", "精细结构常数 137"
        """
        from config import TERM_SYNONYMS
        expanded = [query]
        replacements = []

        for term, syns in TERM_SYNONYMS.items():
            if term in query:
                # 每个同义词生成一个变体
                for s in syns:
                    if s not in query:
                        variant = query.replace(term, f"{term} {s}")
                        replacements.append((term, s, variant))
            else:
                for s in syns:
                    if s in query.lower():
                        variant = query.replace(s, f"{term} {s}")
                        replacements.append((s, term, variant))
                        break

        # 最多生成 3 个变体，避免过多 API 调用
        for _, _, variant in replacements[:3]:
            if variant not in expanded:
                expanded.append(variant)

        return expanded

    # 查询改写表：触发词 -> (替换词, 模式) 模式: replace=替换 / append=追加锚点词
    _TERM_MAP = [
        ("分形宇宙", "分形层级宇宙", "replace"),
        ("领卷", "零之动与区分", "replace"),
        ("精细结构常数", "精细结构常数 137.036 作用量 观测者位置", "append"),
        ("137.035999102", "137.036", "replace"),
        ("27分之1", "27分之1 B1 1/27 二十七分之一", "append"),
        ("分叉口", "分叉口 对称性破缺 分支选择", "append"),
        ("定理编号", "定理编号 编号规范 四段式", "append"),
    ]

    def _rewrite_query(self, query: str) -> str:
        """查询改写：口语/简称 → 文章标准术语，缓解术语鸿沟。"""
        if not query:
            return query
        q = query
        for trigger, repl, mode in self._TERM_MAP:
            if trigger in q:
                if mode == 'replace':
                    q = q.replace(trigger, repl)
                else:
                    q = q + ' ' + repl
        if q != query:
            logger.info(f"[VECTOR] 查询改写: {query} -> {q}")
        return q

    def _get_anchor_query(self, query: str) -> Optional[str]:
        """提取主题锚点词（append 模式的追加词作为纯主题查询）。

        当查询是"元任务+主题词"混合（如"把XX推广出去，精细结构常数比较有冲击力"），
        主题词被稀释，主查询难以命中承载文章。锚点查询独立检索可补救。
        replace 模式的主查询已含替换词，无需双查询。
        """
        if not query:
            return None
        for trigger, repl, mode in self._TERM_MAP:
            if mode == 'append' and trigger in query:
                if len(repl) >= 3:
                    return repl
        return None

    def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        """查询向量，带内存缓存：相同查询不重复调用 embedding API。"""
        if not hasattr(self, '_query_embedding_cache'):
            self._query_embedding_cache = {}
        if query in self._query_embedding_cache:
            return self._query_embedding_cache[query]
        try:
            vecs = self.embedding_fn([query])
            if vecs:
                self._query_embedding_cache[query] = vecs[0]
                return vecs[0]
        except Exception as e:
            logger.debug(f"[VECTOR] embedding 调用失败: {e}")
        return None

    _RERANK_TTL = 600.0  # rerank 结果缓存 TTL（秒）

    def _needs_rerank(self, query: str) -> bool:
        """推理类查询需要语义精排；纯事实查询用 RRF+距离确定性排序已足够。

        降频依据：rerank 是远程 API（~500ms），事实查询（"什么是X"/"X是多少"）
        的检索目标明确，向量距离+BM25+RRF 排序已可靠；推理类查询（推导/证明/
        对比/关系）语义跨度大，精排的边际收益才值得支付 API 延迟。
        """
        if not query:
            return False
        _reason_tokens = ('推导', '证明', '验证', '检验', '为什么', '如何', '怎样',
                          '关系', '对比', '区别', '联系', '链条', '推广', '适用',
                          '能否', '是否', '解释', '原因', '机制', '分析', '讨论',
                          '完整', '闭合', '成立')
        return any(t in query for t in _reason_tokens)

    def _rerank_disagreement(self, pool: List[Dict[str, Any]]) -> bool:
        """确定性分歧检测：RRF 混合排序与纯向量距离排序的 top5 重叠度。

        重叠度高（>=0.6）说明排序已稳定，远程 rerank 边际收益小，跳过省 ~600ms；
        重叠度低说明语义分歧大，值得精排。池子过小时保守返回 True（保持原行为）。
        """
        if len(pool) < 6:
            return True
        _top = 5
        rrf_top = [r.get('id') for r in sorted(
            pool, key=lambda x: -x.get('_rrf_score', 0.0))[:_top]]
        dist_top = [r.get('id') for r in sorted(
            pool, key=lambda x: x.get('distance', 999.0))[:_top]]
        if not rrf_top:
            return True
        overlap = len(set(rrf_top) & set(dist_top)) / float(_top)
        stable = overlap >= 0.6
        if stable:
            logger.info(f"[RERANK] 分歧检测: top{_top} 重叠 {overlap:.0%}，排序稳定，跳过远程精排")
        return not stable

    def _rerank(self, query: str, documents: List[str], top_n: int = 20):
        """重排：优先本地 CrossEncoder，失败回退 SiliconFlow API。

        对候选池按相关性重新排序，弥补向量检索在术语鸿沟上的不足。
        失败时返回 None，调用方保持原排序。
        带结果缓存：同查询同文档池 TTL 内不重复调用。
        """
        if not documents:
            return None
        _pool_sig = '|'.join(sorted(documents))[:1500]
        cache_key = query + '|' + str(len(documents)) + '|' + _pool_sig
        _now = time.time()
        if hasattr(self, '_rerank_cache'):
            _entry = self._rerank_cache.get(cache_key)
            if _entry and _now - _entry[0] < self._RERANK_TTL:
                logger.debug(f"[RERANK] 缓存命中: {len(documents)} docs")
                return _entry[1]

        # 优先：本地 reranker
        if not hasattr(self, '_local_reranker'):
            try:
                self._local_reranker = LocalReranker()
            except Exception as e:
                logger.warning(f"[RERANK] 本地 reranker 初始化失败: {e}")
                self._local_reranker = None
        if self._local_reranker and self._local_reranker._model is not None:
            _t0 = time.time()
            result = self._local_reranker.rerank(query, documents, top_n=top_n)
            _dt = (time.time() - _t0) * 1000
            if result:
                if not hasattr(self, '_rerank_cache'):
                    self._rerank_cache = {}
                self._rerank_cache[cache_key] = (_now, result)
                if len(self._rerank_cache) > 256:
                    _oldest = min(self._rerank_cache, key=lambda k: self._rerank_cache[k][0])
                    del self._rerank_cache[_oldest]
                logger.info(f"[RERANK] 本地 rerank 完成: {len(documents)} docs, {_dt:.0f}ms")
                return result
            logger.warning("[RERANK] 本地 rerank 失败，回退远程 API")

        # 回退：SiliconFlow API
        try:
            _sf_base = os.getenv('RAG_EMBEDDING_BASE_URL', 'https://api.siliconflow.cn/v1')
            _sf_key = os.getenv('SILICONFLOW_API_KEY', '')
            resp = requests.post(
                f"{_sf_base}/rerank",
                headers={"Authorization": f"Bearer {_sf_key}"},
                json={
                    "model": "BAAI/bge-reranker-v2-m3",
                    "query": query,
                    "documents": documents,
                    "top_n": top_n,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                _result = resp.json()
                if not hasattr(self, '_rerank_cache'):
                    self._rerank_cache = {}
                self._rerank_cache[cache_key] = (_now, _result)
                if len(self._rerank_cache) > 256:
                    _oldest = min(self._rerank_cache, key=lambda k: self._rerank_cache[k][0])
                    del self._rerank_cache[_oldest]
                return _result
            logger.debug(f"[RERANK] HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.debug(f"[RERANK] 远程调用失败: {e}")
        return None

    def search(self, query: str, top_k: int = 15, include_personal: bool = False) -> List[Dict[str, Any]]:
        """
        从 articles 集合检索，返回相关文本。
        learned 集合始终参与搜索，可通过 include_personal 附加个人记忆。
        每个结果包含 text, source, metadata 等信息。
        增加了 article_id 精确匹配：当向量搜索找不到或用户询问特定编号时，
        尝试按 article_id 或 fname 精确匹配。
        每次搜索前自动检查文件变更并同步索引。
        """
        if not self._initialized:
            return []

        results = []

        # 查询改写：术语/简称 → 文章标准术语（轻量规则版）
        raw_query = query
        query = self._rewrite_query(query)

        # BM25 索引懒构建：首次搜索时若未构建且文章集合非空，自动全量构建
        if not self.bm25_searcher.initialized and self.articles_count > 0:
            try:
                self._update_bm25_for_file('batch_auto', [], [])
                logger.info(f"[BM25] 懒构建完成: {self.bm25_searcher.chunk_count} chunks")
            except Exception as e:
                logger.debug(f"[BM25] 懒构建失败: {e}")

        # 检测是否在询问特定文章编号（用改写前的原始查询，避免追加词干扰）
        id_pattern = re.search(r'(\d+[\d\.]*)', raw_query)
        target_id = id_pattern.group(1) if id_pattern else None
        # 纯整数编号太模糊（"3"会匹配所有含3的文章，"12"匹配10.12/8.12/3.12...），
        # 只对含小数点的规范编号（如 3.10、10.14、0.9）做精确匹配
        if target_id and '.' not in target_id:
            target_id = None

        # 从 articles 集合检索（扩大召回范围，避免只取 top_k*2//3=10 条）
        try:
            n_articles = min(top_k * 2, self.articles_count) if self.articles_count > 0 else 0
            if n_articles > 0:
                # 优先用缓存向量（query_embeddings），避免重复调用 embedding API
                _qvec = self._get_query_embedding(query)
                if _qvec:
                    if self._use_workspace and self._ws is not None:
                        art_results = self._workspace_query_results(_qvec, n_articles)
                        if art_results is None:
                            # 中间层异常：回退 ChromaDB（只回退一次）
                            logger.warning("[WS] 暴力检索异常，回退 ChromaDB 路径")
                            self._use_workspace = False
                            art_results = self._safe_collection_call(
                                'articles_collection', 'query',
                                query_embeddings=[_qvec],
                                n_results=n_articles
                            )
                    else:
                        art_results = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_embeddings=[_qvec],
                            n_results=n_articles
                        )
                else:
                    art_results = self._safe_collection_call(
                        'articles_collection', 'query',
                        query_texts=[query],
                        n_results=n_articles
                    )
                if art_results and art_results['documents']:
                    for i, doc in enumerate(art_results['documents'][0]):
                        meta = art_results['metadatas'][0][i] if art_results['metadatas'] else {}
                        dist = art_results['distances'][0][i] if art_results['distances'] else 0.0
                        results.append({
                            'id': meta.get('chunk_id', ''),
                            'text': doc,
                            'source': 'articles',
                            'metadata': meta,
                            'distance': dist,
                            'label': f"文章库: {meta.get('fname', '未知')} ({meta.get('article_id', '?')})"
                        })

                # 双查询：锚点词独立检索（长查询中主题词被元任务词稀释时的补救）
                # 锚点结果 append 尾部，由 rerank 层统一重排（相关浮起、无关沉底）
                _anchor_q = self._get_anchor_query(raw_query) if len(raw_query) > 15 else None
                if _anchor_q and _anchor_q != query:
                    try:
                        _anchor_vec = self._get_query_embedding(_anchor_q)
                        if _anchor_vec:
                            if self._use_workspace and self._ws is not None:
                                _anchor_res = self._workspace_query_results(_anchor_vec, min(5, n_articles))
                                if _anchor_res is None:
                                    self._use_workspace = False
                                    _anchor_res = self._safe_collection_call(
                                        'articles_collection', 'query',
                                        query_embeddings=[_anchor_vec],
                                        n_results=min(5, n_articles)
                                    )
                            else:
                                _anchor_res = self._safe_collection_call(
                                    'articles_collection', 'query',
                                    query_embeddings=[_anchor_vec],
                                    n_results=min(5, n_articles)
                                )
                            if _anchor_res and _anchor_res['documents']:
                                _exist_cids = {r.get('id') for r in results}
                                _anchor_items = []
                                for _i, _doc in enumerate(_anchor_res['documents'][0]):
                                    _meta = _anchor_res['metadatas'][0][_i] if _anchor_res['metadatas'] else {}
                                    _cid = _meta.get('chunk_id', '')
                                    if _cid and _cid not in _exist_cids:
                                        _anchor_items.append({
                                            'id': _cid,
                                            'text': _doc,
                                            'source': 'articles',
                                            'metadata': _meta,
                                            'distance': _anchor_res['distances'][0][_i] if _anchor_res['distances'] else 0.0,
                                            'label': f"[主题锚定] 文章库: {_meta.get('fname', '未知')} ({_meta.get('article_id', '?')})"
                                        })
                                        _exist_cids.add(_cid)
                                if _anchor_items:
                                    results = results + _anchor_items
                                    logger.info(f"[VECTOR] 主题锚定: '{_anchor_q}' -> {len(_anchor_items)} 条")
                    except Exception as e:
                        logger.debug(f"[VECTOR] 主题锚定检索失败: {e}")

                # 同义词扩展查询：用 TERM_SYNONYMS 扩展 query，补充召回
                # 仅在主查询有少量结果（0<len<3）时执行：完全无结果多为 embedding 故障或查询与库无关，
                # 扩展只会雪崩式追加 API 调用且大概率仍无结果
                expanded_queries = self._expand_query_synonyms(query) if 0 < len(results) < 3 else []
                for eq in expanded_queries:
                    if eq == query:
                        continue
                    try:
                        eq_results = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_texts=[eq], n_results=min(5, n_articles)
                        )
                        if eq_results and eq_results['documents']:
                            existing_ids = set()
                            for r in results:
                                mid = r.get('metadata', {}).get('chunk_id', '')
                                if mid:
                                    existing_ids.add(mid)
                            for i, doc in enumerate(eq_results['documents'][0]):
                                meta = eq_results['metadatas'][0][i] if eq_results['metadatas'] else {}
                                cid = meta.get('chunk_id', '')
                                if cid not in existing_ids:
                                    dist = eq_results['distances'][0][i] if eq_results['distances'] else 0.0
                                    results.append({
                                        'id': meta.get('chunk_id', ''),
                                        'text': doc,
                                        'source': 'articles',
                                        'metadata': meta,
                                        'distance': dist,
                                        'label': f"[同义词扩展] 文章库: {meta.get('fname', '未知')} ({meta.get('article_id', '?')})"
                                    })
                                    existing_ids.add(cid)
                    except Exception as e:
                        logger.debug(f"[VECTOR] 同义词扩展查询失败: {e}")

        except Exception as e:
            logger.error(f"[VECTOR] articles 检索失败: {e}")

        # BM25 关键词检索补充 + RRF 融合
        if self.bm25_searcher.initialized:
            try:
                bm25_hits = self.bm25_searcher.search(query, top_k=min(top_k * 2, 20))
                if bm25_hits:
                    # 收集已有 chunk ids（用于去重）
                    existing_chunk_ids = set()
                    for r in results:
                        eid = r.get('metadata', {}).get('chunk_id', '')
                        if eid:
                            existing_chunk_ids.add(eid)

                    # BM25 分数归一化：将 BM25 分数映射到距离区间 [0.75, 1.0]
                    # BM25 只作补充：关键词命中的 chunk 距离应大于向量语义距离（0.3-0.6），
                    # 排在向量结果之后，避免霸榜干扰语义排序
                    bm25_scores_raw = [score for _, score in bm25_hits]
                    bm25_min = min(bm25_scores_raw) if bm25_scores_raw else 0
                    bm25_max = max(bm25_scores_raw) if bm25_scores_raw else 1
                    bm25_range = bm25_max - bm25_min if bm25_max > bm25_min else 1.0

                    # 从 ChromaDB 获取 BM25 命中的 chunk 文本和 metadata
                    bm25_ids = [cid for cid, _ in bm25_hits if cid not in existing_chunk_ids]
                    if bm25_ids:
                        chroma_data = self._safe_collection_call('articles_collection', 'get', ids=bm25_ids, include=['documents', 'metadatas'])
                        for i, cid in enumerate(chroma_data['ids']):
                            meta = chroma_data['metadatas'][i] if chroma_data['metadatas'] else {}
                            doc = chroma_data['documents'][i] if chroma_data['documents'] else ''
                            # 找到 BM25 分数并归一化为距离
                            bm25_score = 0.0
                            for hid, hscore in bm25_hits:
                                if hid == cid:
                                    bm25_score = hscore
                                    break
                            # 归一化：最高分 -> 0.75，最低分 -> 1.0
                            norm_score = (bm25_score - bm25_min) / bm25_range
                            bm25_distance = 1.0 - 0.25 * norm_score  # 范围 [0.75, 1.0]

                            results.append({
                                'id': meta.get('chunk_id', ''),
                                'text': doc,
                                'source': 'articles',
                                'metadata': meta,
                                'distance': round(bm25_distance, 4),
                                'label': f"[BM25] 文章库: {meta.get('fname', '未知')} ({meta.get('article_id', '?')})",
                                'bm25_score': round(bm25_score, 2),
                            })
                            existing_chunk_ids.add(cid)

                    # RRF 融合：重新排序所有 articles 结果
                    articles_results = [r for r in results if r.get('source') == 'articles']
                    non_articles = [r for r in results if r.get('source') != 'articles']

                    # 按 distance 排序后计算 RRF 分数
                    rrf_k = 60
                    rrf_scores = {}
                    sorted_arts = sorted(articles_results, key=lambda x: x.get('distance', 999))
                    for rank, r in enumerate(sorted_arts):
                        cid = r.get('metadata', {}).get('chunk_id', id(r))
                        rrf_scores[cid] = rrf_scores.get(cid, 0) + 1.0 / (rrf_k + rank + 1)

                    # 更新 _rrf_score
                    for r in articles_results:
                        cid = r.get('metadata', {}).get('chunk_id', id(r))
                        r['_rrf_score'] = rrf_scores.get(cid, 0)

                    # 按来源优先级 + RRF 分数排序
                    def _hybrid_sort_key(r):
                        is_bm25 = 0 if r.get('label', '').startswith('[BM25]') else 1
                        is_exact = 0 if r.get('label', '').startswith('[精确匹配]') else 1
                        is_syn = 0 if r.get('label', '').startswith('[同义词扩展]') else 1
                        rrf = r.get('_rrf_score', 0)
                        # RRF 分数越高越好（取负值用升序）
                        return (is_exact, -rrf, is_bm25, is_syn, r.get('distance', 999))

                    results = sorted(articles_results, key=_hybrid_sort_key) + non_articles

            except Exception as e:
                logger.debug(f"[BM25] 检索或融合失败: {e}")

        # 当向量搜索没结果，或用户明显在找特定编号时，尝试精确匹配
        # 精确匹配结果单独收集并前置：按编号查询时相关文章必在返回顶部，不被截断
        exact_results = []
        if target_id and self.articles_collection and self.articles_count > 0:
            try:
                # 按 article_id 模糊匹配（ChromaDB $contains 操作符）
                # ChromaDB 1.5.9 的 where $contains 对 metadata 字符串字段失效（返回空），
                # 改用 Python 端子串过滤（全量 get 毫秒级，频率低可接受）
                all_data = self._safe_collection_call(
                    'articles_collection', 'get',
                    include=['documents', 'metadatas']
                )
                if all_data and all_data['ids']:
                    existing_cids = {r.get('id') for r in results}
                    for i, doc in enumerate(all_data['documents']):
                        meta = all_data['metadatas'][i] if all_data['metadatas'] else {}
                        aid = meta.get('article_id', '')
                        if target_id in aid:
                            cid = meta.get('chunk_id', '')
                            if cid not in existing_cids:
                                exact_results.append({
                                    'id': cid,
                                    'text': doc,
                                    'source': 'articles',
                                    'metadata': meta,
                                    'distance': 0.0,
                                    'label': f"[精确匹配] 文章库: {meta.get('fname', '未知')} ({aid})"
                                })
                                existing_cids.add(cid)
            except Exception as e:
                logger.debug(f"[VECTOR] article_id 精确匹配失败: {e}")

        # 排序：精确匹配排前面，向量结果按距离排序
        def _sort_key(r):
            is_exact = 0 if r.get('label', '').startswith('[精确匹配]') else 1
            return (is_exact, r.get('distance', 999.0))
        results.sort(key=_sort_key)
        # 精确匹配结果前置（防止被 BM25 RRF 排序覆盖或截断）
        if exact_results:
            exact_ids = {e['id'] for e in exact_results}
            results = exact_results + [r for r in results if r.get('id') not in exact_ids]

        # Rerank：候选池重排（bge-reranker-v2-m3），精确匹配结果保持前置
        if len([r for r in results if r.get('source') == 'articles']) >= 3:
            try:
                exact_items = [r for r in results if r.get('label', '').startswith('[精确匹配]')]
                # 候选池扩容：容纳主题锚定补充（最多 +10 条），rerank 统一重排
                pool = [r for r in results if r.get('source') == 'articles' and r not in exact_items][:top_k * 2 + 10]
                if len(pool) >= 3:
                    docs = [r.get('text', '')[:600] for r in pool]
                    rr = None
                    if self._needs_rerank(query) and self._rerank_disagreement(pool):
                        rr = self._rerank(query, docs, top_n=min(top_k * 2, len(docs)))
                    if rr and rr.get('results'):
                        scores = {item['index']: item['relevance_score'] for item in rr['results']}
                        for i, r in enumerate(pool):
                            r['_rerank_score'] = scores.get(i, 0.0)
                        pool_sorted = sorted(pool, key=lambda r: r.get('_rerank_score', 0.0), reverse=True)
                        rest = [r for r in results if r.get('source') != 'articles' or r in exact_items]
                        results = exact_items + pool_sorted + rest
            except Exception as e:
                logger.debug(f"[VECTOR] rerank 失败: {e}")

        # 从 learned 集合检索
        try:
            n_learned = min(top_k // 3, self.learned_count) if self.learned_count > 0 else 0
            if n_learned > 0 and 'learned' not in self._dim_stale_collections:
                learned_results = self._safe_collection_call(
                    'learned_collection', 'query',
                    query_texts=[query],
                    n_results=n_learned
                )
                if learned_results and learned_results['documents']:
                    for i, doc in enumerate(learned_results['documents'][0]):
                        meta = learned_results['metadatas'][0][i] if learned_results['metadatas'] else {}
                        dist = learned_results['distances'][0][i] if learned_results['distances'] else 0.0
                        results.append({
                            'id': meta.get('chunk_id', '') or f"learned_{meta.get('question', '')[:40]}",
                            'text': doc,
                            'source': 'learned',
                            'metadata': meta,
                            'distance': dist,
                            'label': f"[学习{meta.get('type', '记忆')}] q={meta.get('question', doc[:50])[:50]} (质量:{meta.get('quality_score', '?')})"
                        })
        except Exception as e:
            logger.error(f"[VECTOR] learned 检索失败: {e}")

        # personal 集合单独追加
        if include_personal:
            try:
                if hasattr(self, 'personal_collection') and self.personal_collection:
                    n_personal = min(top_k // 2, self._safe_collection_call('personal_collection', 'count'))
                    if n_personal > 0:
                        personal_results = self._safe_collection_call(
                            'personal_collection', 'query',
                            query_texts=[query],
                            n_results=n_personal
                        )
                        if personal_results and personal_results['documents']:
                            for i, doc in enumerate(personal_results['documents'][0]):
                                meta = personal_results['metadatas'][0][i] if personal_results['metadatas'] else {}
                                dist = personal_results['distances'][0][i] if personal_results['distances'] else 0.0
                                results.append({
                                    'text': doc,
                                    'source': 'personal',
                                    'metadata': meta,
                                    'distance': dist,
                                    'label': f"[个人记忆] {meta.get('category', '?')} ({meta.get('timestamp', '?')})"
                                })
            except Exception as e:
                logger.error(f"[VECTOR] personal 检索失败: {e}")

        # 截断：为 learned 预留位置（learned 追加在尾部但必须保留在返回列表内，
        # 否则 articles 结果 >= top_k*2 时 learned 永远被截断，动态学习机制失效）
        learned_items = [r for r in results if r.get('source') == 'learned']
        if learned_items:
            article_items = [r for r in results if r.get('source') != 'learned']
            return article_items[:max(0, top_k * 2 - len(learned_items))] + learned_items
        return results[:top_k * 2]

    def search_master_truth(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        从主库真理层检索已验证公式（只读，不可修改）。

        这些公式是经过主库AI三重检查验证的"绝对真理"，
        可以作为推导的合法起点引用。
        """
        if not self._initialized or not self.master_truth_collection:
            return []
        try:
            count = self._safe_collection_call('master_truth_collection', 'count')
            if count == 0:
                return []
            n = min(top_k, count)
            results = self._safe_collection_call(
                'master_truth_collection', 'query',
                query_texts=[query],
                n_results=n
            )
            truths = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    dist = results['distances'][0][i] if results['distances'] else 0.0
                    truths.append({
                        'text': doc,
                        'source': 'master_truth',
                        'metadata': meta,
                        'distance': dist,
                        'label': f"[绝对真理] {meta.get('formula_name', '未知')} (已验证)"
                    })
            return truths
        except Exception as e:
            logger.error(f"[VECTOR] master_truth 检索失败: {e}")
            return []

    def get_master_truth_count(self) -> int:
        """获取主库真理层数量"""
        if not self._initialized or not self.master_truth_collection:
            return 0
        try:
            return self._safe_collection_call('master_truth_collection', 'count')
        except Exception:
            return 0


    def search_corrections(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        v10 新增：从 corrections 集合检索与当前查询相似的纠正。
        """
        if not self._initialized or not self.corrections_collection:
            return []
        if 'corrections' in self._dim_stale_collections:
            return []
        try:
            n = min(top_k, self.corrections_count) if self.corrections_count > 0 else 0
            if n == 0:
                return []
            results = self._safe_collection_call(
                'corrections_collection', 'query',
                query_texts=[query],
                n_results=n
            )
            corrections = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    dist = results['distances'][0][i] if results['distances'] else 0.0
                    corrections.append({
                        'text': doc,
                        'metadata': meta,
                        'distance': dist,
                    })
            return corrections
        except Exception as e:
            logger.error(f"[VECTOR] corrections 检索失败: {e}")
            return []

    def search_antipatterns(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        v10 新增：从 antipatterns 集合检索与回复相似的反模式。
        """
        if not self._initialized or not self.antipatterns_collection:
            return []
        if 'antipatterns' in self._dim_stale_collections:
            return []
        try:
            n = min(top_k, self.antipatterns_count) if self.antipatterns_count > 0 else 0
            if n == 0:
                return []
            results = self._safe_collection_call(
                'antipatterns_collection', 'query',
                query_texts=[query],
                n_results=n
            )
            patterns = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    dist = results['distances'][0][i] if results['distances'] else 0.0
                    patterns.append({
                        'text': doc,
                        'metadata': meta,
                        'distance': dist,
                    })
            return patterns
        except Exception as e:
            logger.error(f"[VECTOR] antipatterns 检索失败: {e}")
            return []

    def update_filename_in_metadata(self, old_filename: str, new_filename: str) -> int:
        """
        文件重命名后，更新向量索引中所有引用该文件名的 metadata。
        返回更新的文档数量。
        """
        if not self._initialized:
            return 0
        updated = 0
        for coll_name, attr_name in [
            ('articles', 'articles_collection'),
        ]:
            coll = getattr(self, attr_name, None)
            if not coll or coll_name in self._dim_stale_collections:
                continue
            try:
                all_data = self._safe_collection_call(attr_name, 'get', include=['metadatas'])
                ids_to_update = []
                metas_to_update = []
                docs_to_update = []
                if all_data and all_data['metadatas']:
                    for i, meta in enumerate(all_data['metadatas']):
                        if meta.get('fname') == old_filename:
                            meta['fname'] = new_filename
                            ids_to_update.append(all_data['ids'][i])
                            metas_to_update.append(meta)
                            docs_to_update.append(all_data['documents'][i])
                if ids_to_update:
                    self._safe_collection_call(
                        attr_name, 'update',
                        ids=ids_to_update,
                        metadatas=metas_to_update,
                        documents=docs_to_update,
                    )
                    updated += len(ids_to_update)
                    logger.info(f"[VECTOR] 已更新 {len(ids_to_update)} 条记录的 fname: {old_filename} -> {new_filename}")
            except Exception as e:
                logger.error(f"[VECTOR] 更新 fname 失败 ({coll_name}): {e}")
        return updated

    def search_patches(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        v10 新增：从 patches 集合检索与当前查询相关的知识补丁。
        """
        if not self._initialized or not self.patches_collection:
            return []
        if 'patches' in self._dim_stale_collections:
            return []
        try:
            n = min(top_k, self.patches_count) if self.patches_count > 0 else 0
            if n == 0:
                return []
            results = self._safe_collection_call(
                'patches_collection', 'query',
                query_texts=[query],
                n_results=n
            )
            patches = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    dist = results['distances'][0][i] if results['distances'] else 0.0
                    patches.append({
                        'text': doc,
                        'metadata': meta,
                        'distance': dist,
                    })
            return patches
        except Exception as e:
            logger.error(f"[VECTOR] patches 检索失败: {e}")
            return []

    def get_formatted_results(self, results: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        将检索结果格式化为可注入 prompt 的文本。
        返回 (formatted_text, chunk_labels)
        """
        contents = []
        total_chars = 0
        loaded_chunks = []

        for r in results:
            text = r['text']
            if total_chars + len(text) > MAX_INJECT_CHARS:
                remaining = MAX_INJECT_CHARS - total_chars
                if remaining > 500:
                    text = text[:remaining] + "\n...[截断]\n"
                else:
                    break

            if r['source'] == 'learned':
                header = f"[记忆 score:{r['metadata'].get('quality_score', '?')} dist:{r['distance']:.3f}]"
            else:
                meta = r['metadata']
                fname = meta.get('fname', '')
                header = f"[{meta.get('article_id', '?')} @{meta.get('start', '?')}-{meta.get('end', '?')} dist:{r['distance']:.3f}]"

            contents.append(header + text)
            total_chars += len(header) + len(text)
            loaded_chunks.append(r['label'])

        return "\n".join(contents), loaded_chunks

    # ---- 引用图骨架增强（推导类任务） ----
    _CITATION_GRAPH_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'citation_graph.json')

    def _load_citation_graph(self) -> dict:
        """懒加载引用图（tools/citation_graph.json）。失败返回空 dict。"""
        if not hasattr(self, '_graph_cache'):
            self._graph_cache = None
        if self._graph_cache is None:
            try:
                with open(self._CITATION_GRAPH_PATH, encoding='utf-8') as f:
                    self._graph_cache = json.load(f)
                logger.info(
                    f"[GRAPH] 引用图加载: "
                    f"{self._graph_cache.get('meta', {}).get('edges', 0)} 条边")
            except Exception as e:
                logger.debug(f"[GRAPH] 引用图加载失败: {e}")
                self._graph_cache = {}
        return self._graph_cache

    def enrich_with_graph(self, results: List[Dict[str, Any]], query: str,
                          max_skeleton: int = 3,
                          chunks_per_article: int = 1) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        引用图骨架增强：推导类任务专用。
        1. 从检索结果提取入口文章编号（fname 前缀）
        2. 沿引用图 out+in 扩展骨架文章（按引用次数降序，排除入口）
        3. 从 ChromaDB 按 fname 过滤拉取骨架文章与该查询最相关的 chunk
        4. 骨架 chunk 标记 _skeleton=True 插到结果最前
        返回 (增强后结果, 骨架标签列表)
        """
        # Workspace 模式：动态引用图（内存）+ 内存拉取骨架 chunk
        if self._use_workspace and self._ws is not None and (self._ws.get('graph') or {}):
            try:
                return self._enrich_with_workspace(results, query, max_skeleton, chunks_per_article)
            except Exception as _wse:
                logger.warning(f"[WS] 动态骨架异常（回退静态图）: {_wse}")
                self._use_workspace = False
        try:
            graph = self._load_citation_graph()
            if not graph or not results:
                return results, []

            # 1. 入口编号（fname 前缀，如 "1.5_代数作用量S(σ)_CN_260808.md" -> "1.5"）
            entry_ids = set()
            for r in results:
                fname = r.get('metadata', {}).get('fname', '') or ''
                _m = re.match(r'^(\d{1,2}\.\d{1,2})', fname)
                if _m:
                    entry_ids.add(_m.group(1))
            if not entry_ids:
                return results, []

            # 2. 骨架扩展：多跳 BFS（out + in），按引用次数聚合排序，权重沿跳数衰减
            def _multi_hop_skeleton(out_map, in_map, entry_ids, hops):
                # in_map 是 {to: {from: count}}，先转成 src->[(tgt,cnt)] 便于BFS
                in_out = {}
                for tgt, srcs in in_map.items():
                    for src, cnt in srcs.items():
                        in_out.setdefault(src, []).append((tgt, cnt))
                neigh: Dict[str, float] = {}
                frontier = set(entry_ids)
                visited = set(entry_ids)
                cur_w = 2.0
                for _h in range(hops):
                    if not frontier:
                        break
                    nxt = set()
                    for eid in frontier:
                        for nid, info in out_map.get(eid, {}).items():
                            if nid in visited:
                                continue
                            cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
                            neigh[nid] = neigh.get(nid, 0) + cur_w * cnt
                            nxt.add(nid)
                        for nid, cnt in in_out.get(eid, []):
                            if nid in visited:
                                continue
                            neigh[nid] = neigh.get(nid, 0) + cur_w * 0.5 * cnt
                            nxt.add(nid)
                    visited |= nxt
                    frontier = nxt
                    cur_w *= 0.7  # 每跳衰减
                return sorted(
                    ((nid, c) for nid, c in neigh.items() if nid not in entry_ids),
                    key=lambda x: -x[1])

            _hops = getattr(self, '_graph_max_hops', 2)
            _all_skeleton = _multi_hop_skeleton(out_map, in_map, entry_ids, _hops)
            skeleton = _all_skeleton[:max_skeleton]
            if not skeleton:
                return results, []

            # 3. 编号 -> 文件名映射（从文章目录扫描；目录为空时回退 ChromaDB metadata）
            id_to_fname = {}
            if self._articles_dir:
                try:
                    for fname in os.listdir(self._articles_dir):
                        _m = re.match(r'^(\d{1,2}\.\d{1,2})', fname)
                        if _m:
                            id_to_fname.setdefault(_m.group(1), fname)
                except Exception:
                    pass
            if not id_to_fname:
                if not hasattr(self, '_id_fname_cache') or not self._id_fname_cache:
                    _cache = {}
                    try:
                        _got = self._safe_collection_call(
                            'articles_collection', 'get', include=['metadatas'])
                        for _m in (_got.get('metadatas') or []):
                            _fn = (_m or {}).get('fname', '')
                            _mm = re.match(r'^(\d{1,2}\.\d{1,2})', _fn)
                            if _mm:
                                _cache.setdefault(_mm.group(1), _fn)
                    except Exception as _e:
                        logger.debug(f"[GRAPH] 编号映射回退失败: {_e}")
                    self._id_fname_cache = _cache
                id_to_fname = self._id_fname_cache

            _qvec = self._get_query_embedding(query)
            new_chunks = []
            for nid, cnt in skeleton:
                fname = id_to_fname.get(nid)
                if not fname:
                    continue
                try:
                    if _qvec:
                        sub = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_embeddings=[_qvec],
                            n_results=chunks_per_article,
                            where={"fname": fname}
                        )
                    else:
                        sub = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_texts=[query],
                            n_results=chunks_per_article,
                            where={"fname": fname}
                        )
                    if sub and sub['documents']:
                        for i, doc in enumerate(sub['documents'][0]):
                            meta = sub['metadatas'][0][i] if sub['metadatas'] else {}
                            dist = sub['distances'][0][i] if sub['distances'] else 0.0
                            new_chunks.append({
                                'id': meta.get('chunk_id', ''),
                                'text': doc,
                                'source': 'articles',
                                'metadata': meta,
                                'distance': dist,
                                '_skeleton': True,
                                'label': f"[引用图骨架:{nid}({cnt}次)] 文章库: {fname}"
                            })
                except Exception as e:
                    logger.debug(f"[GRAPH] 骨架文章 {nid} 拉取失败: {e}")

            if not new_chunks:
                return results, []

            # 4. 合并：骨架优先，去重
            existing_ids = set()
            for r in results:
                cid = r.get('id') or r.get('metadata', {}).get('chunk_id', '')
                if cid:
                    existing_ids.add(cid)
            skeleton_chunks = [c for c in new_chunks if (c.get('id') or '') not in existing_ids]
            merged = skeleton_chunks + results
            return merged, [c['label'] for c in skeleton_chunks]
        except Exception as e:
            logger.error(f"[GRAPH] 引用图增强失败: {e}")
            return results, []

    def learn(self, q: str, a: str, score: float) -> bool:
        """
        高质量对话后，将 Q&A 存入 learned 集合。
        metadata 包含 quality_score。
        """
        if not self._initialized:
            return False
        if not q or not a:
            return False

        # 组合 Q&A 为一个文档
        doc = f"问题: {q}\n回答: {a}"
        doc_id = f"learned_{hashlib.md5(doc.encode()).hexdigest()[:16]}_{int(time.time())}"

        try:
            self._safe_collection_call(
                'learned_collection', 'add',
                ids=[doc_id],
                documents=[doc],
                metadatas=[{
                    "question": q[:500],
                    "quality_score": round(score, 4),
                    "source": "learned",
                    "created_at": datetime.now().isoformat(),
                    "answer_length": len(a),
                    "fname": "learned_qa",
                    "article_id": "learned",
                    "start": 0,
                    "end": len(doc)
                }]
            )
            self._learned_count = self._safe_collection_call('learned_collection', 'count')
            logger.info(
                f"[VECTOR-LEARN] 存入学习库 | score={score:.3f} | "
                f"learned总数={self._learned_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[VECTOR-LEARN] 存入学习库失败: {e}")
            return False

    def learn_proposition(self, proposition: str, score: float) -> bool:
        """
        将关键论断存入 learned 集合（metadata 标记 type=proposition）。
        """
        if not self._initialized:
            return False
        if not proposition or len(proposition.strip()) < 10:
            return False

        doc_id = f"prop_{hashlib.md5(proposition.encode()).hexdigest()[:16]}_{int(time.time())}"

        try:
            self._safe_collection_call(
                'learned_collection', 'add',
                ids=[doc_id],
                documents=[proposition],
                metadatas=[{
                    "type": "proposition",
                    "quality_score": round(score, 4),
                    "source": "learned",
                    "created_at": datetime.now().isoformat(),
                    "answer_length": len(proposition),
                    "fname": "learned_proposition",
                    "article_id": "learned",
                    "start": 0,
                    "end": len(proposition)
                }]
            )
            self._learned_count = self._safe_collection_call('learned_collection', 'count')
            logger.info(
                f"[VECTOR-LEARN] 存入论断 | score={score:.3f} | "
                f"learned总数={self._learned_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[VECTOR-LEARN] 存入论断失败: {e}")
            return False

    def learn_propositions_batch(self, propositions: list, score: float) -> int:
        """
        批量存入论断到 learned 集合（一次性 embedding + 写入，避免逐条卡顿）。
        返回成功存入的数量。
        """
        if not self._initialized or not propositions:
            return 0

        valid_props = [p for p in propositions if p and len(p.strip()) >= 10]
        if not valid_props:
            return 0

        now = datetime.now().isoformat()
        ids = []
        docs = []
        metas = []
        for i, prop in enumerate(valid_props):
            doc_id = f"prop_{hashlib.md5(prop.encode()).hexdigest()[:16]}_{int(time.time())}_{i}"
            ids.append(doc_id)
            docs.append(prop)
            metas.append({
                "type": "proposition",
                "quality_score": round(score, 4),
                "source": "learned",
                "created_at": now,
                "answer_length": len(prop),
                "fname": "learned_proposition",
                "article_id": "learned",
                "start": 0,
                "end": len(prop)
            })

        try:
            self._safe_collection_call('learned_collection', 'add', ids=ids, documents=docs, metadatas=metas)
            self._learned_count = self._safe_collection_call('learned_collection', 'count')
            logger.info(
                f"[VECTOR-LEARN] 批量存入 {len(valid_props)} 个论断 | "
                f"score={score:.3f} | learned总数={self._learned_count}"
            )
            return len(valid_props)
        except Exception as e:
            logger.error(f"[VECTOR-LEARN] 批量存入论断失败: {e}")
            return 0

    def clear_learned(self) -> Dict[str, Any]:
        """清空学习库"""
        result = {"success": False, "cleared": 0}
        if not self._initialized:
            result["error"] = "ChromaDB 未初始化"
            return result
        try:
            count_before = self._learned_count
            # 删除 learned 集合再重建
            self.client.delete_collection("learned")
            self.learned_collection = self.client.get_or_create_collection(
                name="learned",
                metadata={"description": "动态学习的QA对"},
                embedding_function=self.embedding_fn
            )
            self._learned_count = 0
            result["success"] = True
            result["cleared"] = count_before
            logger.info(f"[VECTOR] 学习库已清空，共删除 {count_before} 条")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"[VECTOR] 清空学习库失败: {e}")
        return result

    # ==================== v10 新增：教学集合操作 ====================

    def add_correction(self, wrong: str, correct: str, reason: str = "",
                       context: str = "", session_id: str = "",
                       article_id: str = "", trust: float = 0.5) -> Dict[str, Any]:
        """
        v10 新增：添加一条纠正记录到 corrections 集合。
        如果提供了 article_id 且 trust >= 0.5，自动回写到 articles 集合。
        """
        result = {"success": False, "article_rewrite": None, "correction_id": None}

        if not self._initialized:
            result["error"] = "向量库未初始化"
            return result
        if not wrong or not correct:
            result["error"] = "wrong 和 correct 不能为空"
            return result

        doc = f"错误: {wrong}\n正确: {correct}\n原因: {reason or '未提供'}"
        doc_id = f"corr_{hashlib.md5(doc.encode()).hexdigest()[:16]}_{int(time.time())}"
        now = datetime.now().isoformat()

        try:
            self._safe_collection_call(
                'corrections_collection', 'add',
                ids=[doc_id],
                documents=[doc],
                metadatas=[{
                    "type": "correction",
                    "wrong": wrong[:1000],
                    "correct": correct[:2000],
                    "reason": reason[:1000],
                    "trust_level": round(min(max(trust, 0.0), 1.0), 2),
                    "applied_count": 0,
                    "created_at": now,
                    "session_id": session_id[:64] if session_id else "",
                    "article_id": article_id[:100] if article_id else "",
                }]
            )
            self._corrections_count = self._safe_collection_call('corrections_collection', 'count')
            logger.info(
                f"[TEACH-CORRECT] 纠正已存入 | corrections总数={self._corrections_count}"
            )
            result["success"] = True
            result["correction_id"] = doc_id

            # 自动回写到 articles 集合
            if article_id and trust >= 0.5:
                rewrite = self._apply_correction_to_articles(
                    wrong, correct, reason, article_id, trust, doc_id
                )
                result["article_rewrite"] = rewrite
                if rewrite.get("applied"):
                    logger.info(
                        f"[TEACH-CORRECT] 自动回写成功 | article_id={article_id} | "
                        f"updated={rewrite.get('chunks_updated', 0)}"
                    )

            return result
        except Exception as e:
            logger.error(f"[TEACH-CORRECT] 存入纠正失败: {e}")
            result["error"] = str(e)
            return result

    def _apply_correction_to_articles(self, wrong: str, correct: str, reason: str,
                                        article_id: str, trust: float,
                                        correction_id: str) -> Dict[str, Any]:
        """
        将纠正回写到 articles 集合中匹配的 chunk。
        只在 chunk 文本中找到 wrong 子串时才替换，避免误操作。
        替换前自动保存回滚快照到 patches 集合。
        """
        result = {"applied": False, "article_id": article_id, "chunks_updated": 0}

        if not self._initialized or not self.articles_collection:
            result["reason"] = "articles 集合不可用"
            return result
        if not article_id:
            result["reason"] = "未指定 article_id"
            return result
        if trust < 0.5:
            result["reason"] = f"trust_level {trust:.2f} 不足 0.5"
            return result

        try:
            # 查找该 article_id 下的所有 chunk
            existing = self._safe_collection_call(
                'articles_collection', 'get',
                where={"article_id": article_id},
                include=["documents", "metadatas"]
            )

            if not existing or not existing['ids']:
                result["reason"] = f"articles 中未找到 article_id={article_id}"
                return result

            update_ids = []
            update_docs = []
            update_metas = []
            # 回滚快照：记录修改前的 chunk id、原文、原 metadata
            rollback_chunks = []

            for idx, chunk_id in enumerate(existing['ids']):
                chunk_text = existing['documents'][idx] if idx < len(existing['documents']) else ""
                chunk_meta = existing['metadatas'][idx] if idx < len(existing['metadatas']) else {}

                if wrong not in chunk_text:
                    continue

                # 保存回滚快照（修改前的原始数据）
                rollback_chunks.append({
                    "id": chunk_id,
                    "document": chunk_text,
                    "metadata": dict(chunk_meta),
                })

                # 执行替换（只替换第一次出现）
                new_text = chunk_text.replace(wrong, correct, 1)
                update_ids.append(chunk_id)
                update_docs.append(new_text)

                # 记录纠正历史到 metadata
                corr_ids = chunk_meta.get("correction_ids", "")
                if corr_ids:
                    corr_ids = f"{corr_ids},{correction_id}"
                else:
                    corr_ids = correction_id
                chunk_meta["correction_ids"] = corr_ids
                chunk_meta["_corrected_at"] = datetime.now().isoformat()
                update_metas.append(chunk_meta)

            if not update_ids:
                result["reason"] = f"article_id={article_id} 下没有 chunk 包含错误文本"
                return result

            # 保存回滚快照到 patches 集合
            self._save_rollback_snapshot(correction_id, article_id, wrong, correct,
                                         reason, rollback_chunks)

            # 批量更新（ChromaDB update 会自动重新计算 embedding）
            for batch_start in range(0, len(update_ids), 500):
                batch_ids = update_ids[batch_start:batch_start + 500]
                batch_docs = update_docs[batch_start:batch_start + 500]
                batch_metas = update_metas[batch_start:batch_start + 500]
                self._safe_collection_call(
                    'articles_collection', 'update',
                    ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                )

            self._articles_count = self._safe_collection_call('articles_collection', 'count')

            # 记录 patch 日志
            self.add_patch(
                topic=f"[自动回写] article_id={article_id} 纠正: {wrong[:50]}",
                content=f"将 '{wrong[:200]}' 替换为 '{correct[:200]}'。"
                       f"原因: {reason[:200]}。"
                       f"涉及 chunk 数: {len(update_ids)}。"
                       f"correction_id: {correction_id}",
                source="auto_correction_rewrite"
            )

            result["applied"] = True
            result["chunks_updated"] = len(update_ids)
            result["correction_id"] = correction_id
            logger.info(
                f"[CORRECTION-REWRITE] 回写完成 | article_id={article_id} | "
                f"updated={len(update_ids)} chunks | snapshot saved"
            )
            return result

        except Exception as e:
            logger.error(f"[CORRECTION-REWRITE] 回写失败: {e}")
            result["reason"] = str(e)
            return result

    def _save_rollback_snapshot(self, correction_id: str, article_id: str,
                                  wrong: str, correct: str, reason: str,
                                  chunks: List[Dict]) -> None:
        """保存回滚快照到 patches 集合，用于后续撤销纠正。"""
        if not self._initialized or not self.patches_collection or not chunks:
            return

        snapshot_id = f"rollback_{correction_id}"
        now = datetime.now().isoformat()

        # ChromaDB metadata 只支持简单类型，将 chunks 序列化为 JSON 字符串
        import json as _json
        chunks_json = _json.dumps(chunks, ensure_ascii=False)

        snapshot_doc = (
            f"回滚快照 | correction_id={correction_id} | article_id={article_id}\n"
            f"原文: {wrong[:300]}\n"
            f"改为: {correct[:300]}\n"
            f"原因: {reason[:300]}\n"
            f"涉及 chunk 数: {len(chunks)}"
        )

        try:
            # 如果已有同 correction_id 的快照，先删除
            try:
                self._safe_collection_call('patches_collection', 'delete', ids=[snapshot_id])
            except Exception:
                pass

            self._safe_collection_call(
                'patches_collection', 'add',
                ids=[snapshot_id],
                documents=[snapshot_doc],
                metadatas=[{
                    "type": "rollback_snapshot",
                    "correction_id": correction_id,
                    "article_id": article_id,
                    "wrong_preview": wrong[:200],
                    "correct_preview": correct[:200],
                    "chunk_count": len(chunks),
                    "chunks_json": chunks_json[:50000],  # ChromaDB metadata 值长度限制
                    "created_at": now,
                }]
            )
            self._patches_count = self._safe_collection_call('patches_collection', 'count')
            logger.info(
                f"[ROLLBACK-SNAPSHOT] 快照已保存 | correction_id={correction_id} | "
                f"chunks={len(chunks)}"
            )
        except Exception as e:
            logger.error(f"[ROLLBACK-SNAPSHOT] 保存快照失败: {e}")

    def rollback_correction(self, correction_id: str) -> Dict[str, Any]:
        """
        回滚一个纠正：从 patches 集合取出快照，还原 articles chunk 到修改前的状态。
        """
        result = {"success": False, "correction_id": correction_id, "chunks_restored": 0}

        if not self._initialized or not self.patches_collection or not self.articles_collection:
            result["error"] = "向量库未初始化"
            return result

        try:
            # 从 patches 取出快照
            snapshot_id = f"rollback_{correction_id}"
            snapshot = self._safe_collection_call(
                'patches_collection', 'get',
                ids=[snapshot_id],
                include=["documents", "metadatas"]
            )

            if not snapshot or not snapshot['ids']:
                result["error"] = f"未找到 correction_id={correction_id} 的回滚快照"
                return result

            meta = snapshot['metadatas'][0]
            chunks_json = meta.get("chunks_json", "")
            article_id = meta.get("article_id", "")

            if not chunks_json:
                result["error"] = "快照数据为空"
                return result

            import json as _json
            chunks = _json.loads(chunks_json)

            if not chunks:
                result["error"] = "快照中无 chunk 数据"
                return result

            # 还原每个 chunk
            restore_ids = []
            restore_docs = []
            restore_metas = []

            for chunk in chunks:
                chunk_id = chunk["id"]
                original_text = chunk["document"]
                original_meta = chunk["metadata"]

                # 从 correction_ids 中移除当前 correction_id
                corr_ids_str = original_meta.get("correction_ids", "")
                if corr_ids_str:
                    corr_id_list = [cid.strip() for cid in corr_ids_str.split(",") if cid.strip()]
                    corr_id_list = [cid for cid in corr_id_list if cid != correction_id]
                    original_meta["correction_ids"] = ",".join(corr_id_list) if corr_id_list else ""
                else:
                    original_meta["correction_ids"] = ""

                # 清除 corrected_at 如果没有其他纠正
                if not original_meta.get("correction_ids"):
                    original_meta.pop("_corrected_at", None)

                restore_ids.append(chunk_id)
                restore_docs.append(original_text)
                restore_metas.append(original_meta)

            # 批量还原
            for batch_start in range(0, len(restore_ids), 500):
                batch_ids = restore_ids[batch_start:batch_start + 500]
                batch_docs = restore_docs[batch_start:batch_start + 500]
                batch_metas = restore_metas[batch_start:batch_start + 500]
                self._safe_collection_call(
                    'articles_collection', 'update',
                    ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                )

            self._articles_count = self._safe_collection_call('articles_collection', 'count')

            # 删除快照（已消费）
            self._safe_collection_call('patches_collection', 'delete', ids=[snapshot_id])
            self._patches_count = self._safe_collection_call('patches_collection', 'count')

            # 从 corrections 集合中标记为已回滚
            try:
                corr_record = self._safe_collection_call(
                    'corrections_collection', 'get',
                    ids=[correction_id],
                    include=["documents", "metadatas"]
                )
                if corr_record and corr_record['ids']:
                    corr_meta = corr_record['metadatas'][0]
                    corr_meta["rolled_back"] = "true"
                    corr_meta["rolled_back_at"] = datetime.now().isoformat()
                    self._safe_collection_call(
                        'corrections_collection', 'update',
                        ids=[correction_id],
                        metadatas=[corr_meta]
                    )
            except Exception as e:
                logger.warning(f"[ROLLBACK] 标记 correction 回滚状态失败: {e}")

            # 记录 patch 日志
            self.add_patch(
                topic=f"[回滚] article_id={article_id} correction_id={correction_id}",
                content=f"已回滚纠正，还原了 {len(restore_ids)} 个 chunk 到修改前状态。",
                source="correction_rollback"
            )

            result["success"] = True
            result["chunks_restored"] = len(restore_ids)
            result["article_id"] = article_id
            logger.info(
                f"[ROLLBACK] 回滚完成 | correction_id={correction_id} | "
                f"article_id={article_id} | restored={len(restore_ids)} chunks"
            )
            return result

        except Exception as e:
            logger.error(f"[ROLLBACK] 回滚失败: {e}")
            result["error"] = str(e)
            return result

    def _replay_all_corrections(self) -> Dict[str, Any]:
        """
        重放所有 trust >= 0.5 且有 article_id 的纠正记录到 articles 集合。
        在 build_index 重建索引后调用，确保纠正不丢失。
        """
        result = {"replayed": 0, "skipped": 0, "failed": 0}

        if not self._initialized or not self.corrections_collection:
            return result

        try:
            all_corrections = self._safe_collection_call('corrections_collection', 'get', include=["documents", "metadatas"])
            if not all_corrections or not all_corrections['ids']:
                return result

            for idx, corr_id in enumerate(all_corrections['ids']):
                meta = all_corrections['metadatas'][idx] if idx < len(all_corrections['metadatas']) else {}
                doc = all_corrections['documents'][idx] if idx < len(all_corrections['documents']) else ""

                article_id = meta.get("article_id", "")
                trust = float(meta.get("trust_level", 0.5))

                if not article_id or trust < 0.5:
                    result["skipped"] += 1
                    continue

                wrong = meta.get("wrong", "")
                correct = meta.get("correct", "")
                reason = meta.get("reason", "")

                if not wrong or not correct:
                    result["skipped"] += 1
                    continue

                rewrite = self._apply_correction_to_articles(
                    wrong, correct, reason, article_id, trust, corr_id
                )
                if rewrite.get("applied"):
                    result["replayed"] += 1
                else:
                    result["skipped"] += 1

            logger.info(
                f"[CORRECTION-REPLAY] 重放完成 | replayed={result['replayed']} | "
                f"skipped={result['skipped']} | failed={result['failed']}"
            )
        except Exception as e:
            logger.error(f"[CORRECTION-REPLAY] 重放失败: {e}")
            result["failed"] = 1

        return result

    def add_antipattern(self, pattern: str, description: str = "",
                        severity: str = "medium") -> bool:
        """
        v10 新增：添加一条反模式到 antipatterns 集合。
        """
        if not self._initialized:
            return False
        if not pattern:
            return False

        doc = f"反模式: {pattern}\n描述: {description or '未提供'}"
        doc_id = f"anti_{hashlib.md5(doc.encode()).hexdigest()[:16]}_{int(time.time())}"
        now = datetime.now().isoformat()

        try:
            self._safe_collection_call(
                'antipatterns_collection', 'add',
                ids=[doc_id],
                documents=[pattern],
                metadatas=[{
                    "type": "antipattern",
                    "pattern": pattern[:1000],
                    "description": description[:1000],
                    "severity": severity.lower(),
                    "created_at": now,
                }]
            )
            self._antipatterns_count = self._safe_collection_call('antipatterns_collection', 'count')
            logger.info(
                f"[TEACH-ANTIPATTERN] 反模式已存入 | severity={severity} | "
                f"antipatterns总数={self._antipatterns_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[TEACH-ANTIPATTERN] 存入反模式失败: {e}")
            return False

    def add_patch(self, topic: str, content: str, source: str = "") -> bool:
        """
        v10 新增：添加一条知识补丁到 patches 集合。
        """
        if not self._initialized:
            return False
        if not topic or not content:
            return False

        doc = f"主题: {topic}\n内容: {content}"
        doc_id = f"patch_{hashlib.md5(doc.encode()).hexdigest()[:16]}_{int(time.time())}"
        now = datetime.now().isoformat()

        try:
            self._safe_collection_call(
                'patches_collection', 'add',
                ids=[doc_id],
                documents=[doc],
                metadatas=[{
                    "type": "patch",
                    "topic": topic[:500],
                    "content": content[:5000],
                    "source": source[:500],
                    "trust_level": 0.5,
                    "created_at": now,
                }]
            )
            self._patches_count = self._safe_collection_call('patches_collection', 'count')
            logger.info(
                f"[TEACH-PATCH] 知识补丁已存入 | topic={topic[:50]} | "
                f"patches总数={self._patches_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[TEACH-PATCH] 存入知识补丁失败: {e}")
            return False

    def get_recent_corrections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        v10 新增：获取最近的纠正记录，按 trust_level 降序排列。
        ChromaDB 不支持按 metadata 排序，所以获取全部后在内存中排序。
        """
        if not self._initialized or not self.corrections_collection:
            return []
        try:
            count = self.corrections_count
            if count == 0:
                return []
            n = min(count, 100)  # 最多获取100条，然后排序取 top N
            results = self._safe_collection_call(
                'corrections_collection', 'get',
                include=["documents", "metadatas"]
            )
            corrections = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    meta = results['metadatas'][i] if results['metadatas'] else {}
                    corrections.append({
                        'id': results['ids'][i] if results['ids'] else f"corr_{i}",
                        'document': doc,
                        'metadata': meta,
                    })
            # 按 trust_level 降序，再按 created_at 降序
            corrections.sort(
                key=lambda x: (
                    x['metadata'].get('trust_level', 0.5),
                    x['metadata'].get('created_at', '')
                ),
                reverse=True
            )
            return corrections[:limit]
        except Exception as e:
            logger.error(f"[TEACH] 获取纠正记录失败: {e}")
            return []

    def get_all_antipatterns(self) -> List[Dict[str, Any]]:
        """
        v10 新增：获取所有反模式。
        """
        if not self._initialized or not self.antipatterns_collection:
            return []
        try:
            count = self.antipatterns_count
            if count == 0:
                return []
            results = self._safe_collection_call(
                'antipatterns_collection', 'get',
                include=["documents", "metadatas"]
            )
            patterns = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    meta = results['metadatas'][i] if results['metadatas'] else {}
                    patterns.append({
                        'document': doc,
                        'metadata': meta,
                    })
            return patterns
        except Exception as e:
            logger.error(f"[TEACH] 获取反模式失败: {e}")
            return []

    def get_all_patches(self) -> List[Dict[str, Any]]:
        """
        v10 新增：获取所有知识补丁。
        """
        if not self._initialized or not self.patches_collection:
            return []
        try:
            count = self.patches_count
            if count == 0:
                return []
            results = self._safe_collection_call(
                'patches_collection', 'get',
                include=["documents", "metadatas"]
            )
            patches_list = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    meta = results['metadatas'][i] if results['metadatas'] else {}
                    patches_list.append({
                        'document': doc,
                        'metadata': meta,
                    })
            return patches_list
        except Exception as e:
            logger.error(f"[TEACH] 获取知识补丁失败: {e}")
            return []

    def update_correction_trust(self, doc_id: str, new_trust: float,
                                  new_applied_count: int) -> bool:
        """
        v10 新增：更新纠正记录的信任等级和应用次数。
        ChromaDB 不支持原地更新 metadata，需要删除再插入。
        """
        if not self._initialized or not self.corrections_collection:
            return False
        try:
            # 获取原记录
            old = self._safe_collection_call(
                'corrections_collection', 'get',
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            if not old or not old['documents']:
                return False
            old_meta = old['metadatas'][0] if old['metadatas'] else {}
            # 更新 metadata
            new_meta = dict(old_meta)
            new_meta['trust_level'] = round(min(new_trust, 1.0), 2)
            new_meta['applied_count'] = new_applied_count
            # 仅更新 metadata（ChromaDB update 不传 documents 时不重新嵌入，省 API 调用）
            self._safe_collection_call(
                'corrections_collection', 'update',
                ids=[doc_id],
                metadatas=[new_meta]
            )
            logger.info(
                f"[TEACH-CORRECT] 更新信任等级 | id={doc_id[:12]} | "
                f"trust={new_meta['trust_level']} | applied={new_applied_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[TEACH-CORRECT] 更新信任等级失败: {e}")
            return False

    def get_teaching_history(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        v10 新增：获取所有教学记录（纠正、反模式、补丁），支持分页。
        """
        history = []

        # 获取纠正记录
        try:
            if self._initialized and self.corrections_collection and self.corrections_count > 0:
                corr_results = self._safe_collection_call(
                    'corrections_collection', 'get',
                    include=["documents", "metadatas"]
                )
                if corr_results and corr_results['documents']:
                    for i, doc in enumerate(corr_results['documents']):
                        meta = corr_results['metadatas'][i] if corr_results['metadatas'] else {}
                        history.append({
                            "type": "correction",
                            "document": doc,
                            "metadata": meta,
                            "created_at": meta.get('created_at', ''),
                        })
        except Exception as e:
            logger.error(f"[TEACH] 获取纠正历史失败: {e}")

        # 获取反模式记录
        try:
            if self._initialized and self.antipatterns_collection and self.antipatterns_count > 0:
                anti_results = self._safe_collection_call(
                    'antipatterns_collection', 'get',
                    include=["documents", "metadatas"]
                )
                if anti_results and anti_results['documents']:
                    for i, doc in enumerate(anti_results['documents']):
                        meta = anti_results['metadatas'][i] if anti_results['metadatas'] else {}
                        history.append({
                            "type": "antipattern",
                            "document": doc,
                            "metadata": meta,
                            "created_at": meta.get('created_at', ''),
                        })
        except Exception as e:
            logger.error(f"[TEACH] 获取反模式历史失败: {e}")

        # 获取知识补丁记录
        try:
            if self._initialized and self.patches_collection and self.patches_count > 0:
                patch_results = self._safe_collection_call(
                    'patches_collection', 'get',
                    include=["documents", "metadatas"]
                )
                if patch_results and patch_results['documents']:
                    for i, doc in enumerate(patch_results['documents']):
                        meta = patch_results['metadatas'][i] if patch_results['metadatas'] else {}
                        history.append({
                            "type": "patch",
                            "document": doc,
                            "metadata": meta,
                            "created_at": meta.get('created_at', ''),
                        })
        except Exception as e:
            logger.error(f"[TEACH] 获取补丁历史失败: {e}")

        # 按时间倒序排列
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # 分页
        total = len(history)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = history[start:end]

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
            "items": page_items,
        }

    def get_teaching_stats(self) -> Dict[str, Any]:
        """
        v10 新增：返回教学统计数据。
        """
        stats = {
            "corrections_count": self.corrections_count,
            "antipatterns_count": self.antipatterns_count,
            "patches_count": self.patches_count,
            "trust_distribution": {"0.5": 0, "0.6": 0, "0.7": 0, "0.8": 0, "0.9": 0, "1.0": 0},
            "severity_distribution": {"high": 0, "medium": 0, "low": 0},
        }

        # 统计纠正的信任等级分布
        try:
            if self._initialized and self.corrections_collection and self.corrections_count > 0:
                corr_results = self._safe_collection_call(
                    'corrections_collection', 'get',
                    include=["metadatas"]
                )
                if corr_results and corr_results['metadatas']:
                    for meta in corr_results['metadatas']:
                        tl = meta.get('trust_level', 0.5)
                        tl_key = str(round(tl, 1))
                        if tl_key in stats["trust_distribution"]:
                            stats["trust_distribution"][tl_key] += 1
        except Exception as e:
            logger.error(f"[TEACH] 统计信任等级分布失败: {e}")

        # 统计反模式严重度分布
        try:
            if self._initialized and self.antipatterns_collection and self.antipatterns_count > 0:
                anti_results = self._safe_collection_call(
                    'antipatterns_collection', 'get',
                    include=["metadatas"]
                )
                if anti_results and anti_results['metadatas']:
                    for meta in anti_results['metadatas']:
                        sev = meta.get('severity', 'medium')
                        if sev in stats["severity_distribution"]:
                            stats["severity_distribution"][sev] += 1
        except Exception as e:
            logger.error(f"[TEACH] 统计严重度分布失败: {e}")

        return stats

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本的 embedding 向量（强制 SiliconFlow 1024 维）"""
        if not texts:
            return []
        if self.embedding_fn is not None:
            return self.embedding_fn(texts)
        # 不应到达此处（__init__ 已强制 embedding_fn 非 None）
        raise RuntimeError("[VECTOR] embedding_fn 为 None，无法生成向量")

    def novelty_score(self, query: str, history_queries: List[str]) -> float:
        """
        用轻量文本匹配检测新颖度（避免 embedding 调用）。
        返回 0~1，越高表示越新颖（与历史差异越大）。
        """
        if not history_queries:
            return 1.0

        try:
            query_lower = query.lower()
            history_texts = history_queries[-20:]
            max_overlap = 0.0
            for h in history_texts:
                h_lower = h.lower()
                # 用字符级 n-gram 重叠率代替 embedding 余弦相似度
                q_chars = set(query_lower)
                h_chars = set(h_lower)
                if not q_chars or not h_chars:
                    continue
                overlap = len(q_chars & h_chars) / len(q_chars | h_chars)
                if overlap > max_overlap:
                    max_overlap = overlap
            return max(0.0, 1.0 - max_overlap)
        except Exception as e:
            logger.error(f"[VECTOR] novelty_score 计算失败: {e}")
            return 0.5

    def coherence_score(self, response: str, query: str) -> float:
        """
        用轻量文本匹配检测一致性（避免 embedding 调用）。
        返回 0~1，越高表示回复与问题越一致。
        """
        if not response or not query:
            return 0.0

        try:
            # 用字符级重叠率代替 embedding 余弦相似度
            r_chars = set(response.lower())
            q_chars = set(query.lower())
            if not r_chars or not q_chars:
                return 0.0
            overlap = len(r_chars & q_chars) / len(r_chars | q_chars)

            # 保留符号层面的一致性代理
            symbolic = estimate_coherence(response)

            return 0.7 * overlap + 0.3 * symbolic
        except Exception as e:
            logger.error(f"[VECTOR] coherence_score 计算失败: {e}")
            return 0.0

    def _cosine_similarity_texts(self, text_a: str, text_b: str) -> float:
        """
        v10 新增：直接计算两段文本的余弦相似度。
        """
        if not text_a or not text_b:
            return 0.0
        try:
            embeddings = self._get_embeddings([text_a, text_b])
            if not embeddings or len(embeddings) < 2:
                return 0.0
            return self._cosine_similarity(embeddings[0], embeddings[1])
        except Exception as e:
            logger.error(f"[VECTOR] _cosine_similarity_texts 计算失败: {e}")
            return 0.0

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_status(self) -> Dict[str, Any]:
        """返回向量库状态"""
        return {
            "initialized": self._initialized,
            "persist_dir": self.persist_dir,
            "articles_count": self.articles_count,
            "learned_count": self.learned_count,
            "corrections_count": self.corrections_count,
            "antipatterns_count": self.antipatterns_count,
            "patches_count": self.patches_count,
            "total_docs": self.total_docs,
            "embedding_model": GAI_EMBEDDING_MODEL,
            "dim_stale_collections": list(self._dim_stale_collections) if self._dim_stale_collections else [],
        }


# ==================== estimate_coherence（一致性评估） ====================

def estimate_coherence(response_text: str) -> float:
    """
    评估回复的共扼谱几何一致性得分。
    依赖 GEOMETRY_CONSTANTS、TERM_SYNONYMS、SYNONYM_EXPAND（从 config 导入）。
    """
    if not response_text:
        return 0.0
    scores = []
    formula_count = len(re.findall(
        r'[\u03bb\u03b8\u03b1\u03b2\u03b3\u03b4\u03b5\u03b6\u03b7\u03ba\u03bc\u03bd\u03be\u03c0\u03c1\u03c3\u03c4\u03c6\u03c7\u03c8\u03c9\u210f\u2202\u2207=+\-*/^_{}]',
        response_text
    ))
    formula_density = min(formula_count / max(len(response_text) / 500, 1), 1.0)
    scores.append(0.3 * formula_density)
    theorem_refs = len(re.findall(r'定理|公理|命题|引理|推论|证明', response_text))
    ref_score = min(theorem_refs / 3, 1.0)
    scores.append(0.3 * ref_score)
    structure_score = 0.0
    if re.search(r'[#\-\u2022]\s', response_text):
        structure_score += 0.2
    if re.search(r'总结|结论|综上|因此', response_text):
        structure_score += 0.2
    scores.append(0.2 * min(structure_score, 1.0))
    length = len(response_text)
    if 200 <= length <= 3000:
        length_score = 1.0
    elif length < 200:
        length_score = length / 200
    else:
        length_score = max(1.0 - (length - 3000) / 5000, 0.0)
    scores.append(0.2 * length_score)
    return min(sum(scores), 1.0)
