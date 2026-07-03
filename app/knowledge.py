"""
knowledge.py — 几何论AI调度中间层知识库模块
从 geometry_ai_server_v5_12.py 提取的嵌入函数、向量知识库和一致性评估。
"""

import os
import re
import math
import hashlib
import time
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any

import openai

from config import (
    logger,
    GAI_API_KEY, GAI_BASE_URL, GAI_EMBEDDING_MODEL,
    EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,
    CHROMADB_AVAILABLE,
    MAX_INJECT_CHARS, CHUNK_SIZE, CHUNK_OVERLAP,
    GEOMETRY_CONSTANTS, TERM_SYNONYMS, SYNONYM_EXPAND,
)

try:
    from chromadb.api.types import Documents, Embeddings
except ImportError:
    Documents = list
    Embeddings = list


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
        text = input if isinstance(input, str) else str(input)
        try:
            resp = self.client.embeddings.create(model=self.model, input=[text])
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.error(f"[EMBEDDING] embed_query失败: {e}")
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
                # 添加几何论领域自定义词典
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
        # 逐条发送（最稳定，避免批次中某条有问题导致整批失败）
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

    def embed_query(self, input: str) -> Embeddings:
        """ChromaDB查询时调用（单条文本embedding）"""
        text = input if isinstance(input, str) else str(input)
        text = text.replace('\x00', '').replace('\r', '')
        import re as _re
        text = _re.sub(r'\s+', ' ', text).strip()
        if len(text) > 2000:
            text = text[:2000]
        try:
            resp = self.client.embeddings.create(model=self.model, input=[text])
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.error(f"[EMBEDDING-SF] embed_query失败: {e}")
            return [[0.0] * self._dim]

    def embed_documents(self, input: Documents) -> Embeddings:
        """ChromaDB插入文档时调用（批量embedding）"""
        return self(input)


class LocalEmbeddingFunction:
    """使用 fastembed + bge-small-zh-v1.5 的 ChromaDB Embedding Function（中文优化，纯ONNX，无需torch）"""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        # 启动时立即尝试加载，失败则抛异常让上层fallback
        self._get_model()

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                logger.info(f"[EMBEDDING] 加载本地中文模型: {self.model_name}（首次运行会自动下载，约100MB）")
                self._model = TextEmbedding(model_name=self.model_name)
                logger.info("[EMBEDDING] 中文 embedding 模型加载成功")
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
        """ChromaDB 查询时调用的方法"""
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        """ChromaDB 插入文档时调用的方法"""
        return self(input)


# ==================== VectorKnowledgeBase（含教学集合） ====================

class VectorKnowledgeBase:
    """
    使用 ChromaDB 向量数据库的几何论知识库。
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
        self._initialized = False
        self._articles_count = 0
        self._learned_count = 0
        self._corrections_count = 0
        self._antipatterns_count = 0
        self._patches_count = 0
        self._dim_stale_collections = set()  # 维度过期的集合名，不参与搜索
        self.bm25_searcher = BM25Searcher()  # BM25 关键词检索器
        self._last_index_mtime = 0.0  # 记录上次索引时最新的文件修改时间
        self._articles_dir = ""  # articles 目录路径

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
        """
        import chromadb
        try:
            existing = self.client.get_collection(collection_name)
            count = existing.count()
            if count == 0:
                return existing
            test_emb = self.embedding_fn(["维度检测测试"])
            current_dim = len(test_emb[0]) if test_emb else 0
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
                    f"(存储={stored_dim}, 当前={current_dim})，删除旧数据重建（统一1024维）"
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
                ("articles", "几何论70篇文章静态知识库"),
                ("learned", "动态学习的QA对"),
                ("corrections", "教学纠正记录"),
                ("antipatterns", "反模式库"),
                ("patches", "教学知识补丁"),
                ("personal", "个人数据：性格、感情、想法、记忆"),
            ]

            for col_name, col_desc in collections_config:
                # 检查维度不匹配并自动重建
                rebuilt = self._rebuild_collection_if_dim_mismatch(col_name, col_desc)
                if rebuilt is not None:
                    setattr(self, f"{col_name}_collection" if col_name != "personal" else "personal_collection", rebuilt)
                else:
                    # 正常获取或创建
                    col = self.client.get_or_create_collection(
                        name=col_name,
                        metadata={"description": col_desc},
                        **col_kwargs
                    )
                    attr_name = f"{col_name}_collection"
                    setattr(self, attr_name, col)

            self._articles_count = self.articles_collection.count()
            self._learned_count = self.learned_collection.count()
            self._corrections_count = self.corrections_collection.count()
            self._antipatterns_count = self.antipatterns_collection.count()
            self._patches_count = self.patches_collection.count()
            self._initialized = True
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

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def articles_count(self) -> int:
        if self.articles_collection:
            self._articles_count = self.articles_collection.count()
        return self._articles_count

    @property
    def learned_count(self) -> int:
        if self.learned_collection:
            self._learned_count = self.learned_collection.count()
        return self._learned_count

    @property
    def corrections_count(self) -> int:
        if self.corrections_collection:
            self._corrections_count = self.corrections_collection.count()
        return self._corrections_count

    @property
    def antipatterns_count(self) -> int:
        if self.antipatterns_collection:
            self._antipatterns_count = self.antipatterns_collection.count()
        return self._antipatterns_count

    @property
    def patches_count(self) -> int:
        if self.patches_collection:
            self._patches_count = self.patches_collection.count()
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
            self.embedding_fn(all_documents[:1])
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
            metadata={"description": "几何论70篇文章静态知识库"},
            embedding_function=self.embedding_fn
        )

        # 批量插入
        for batch_start in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[batch_start:batch_start + batch_size]
            batch_docs = all_documents[batch_start:batch_start + batch_size]
            batch_meta = all_metadatas[batch_start:batch_start + batch_size]
            try:
                self.articles_collection.add(
                    ids=batch_ids, documents=batch_docs, metadatas=batch_meta
                )
                success_chunks += len(batch_ids)
            except Exception as e:
                failed_batches += 1
                diag["errors"].append(f"批量插入失败 (批次{batch_start//batch_size+1}): {e}")
                logger.error(f"[VECTOR] 批量插入失败 (批次{batch_start//batch_size+1}): {e}")

        self._articles_count = self.articles_collection.count()
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
                self.articles_collection.delete(where={"fname": fname})
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
            self.articles_collection.delete(
                where={"fname": fname}
            )
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
            self.articles_collection.add(
                ids=ids, documents=documents, metadatas=metadatas
            )
            self._articles_count = self.articles_collection.count()
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
        if not self.bm25_searcher._jieba_loaded:
            return
        try:
            all_data = self.articles_collection.get(include=['documents'])
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

        # 检测是否在询问特定文章编号
        id_pattern = re.search(r'(\d+[\d\.]*)', query)
        target_id = id_pattern.group(1) if id_pattern else None

        # 从 articles 集合检索（扩大召回范围，避免只取 top_k*2//3=10 条）
        try:
            n_articles = min(top_k * 2, self.articles_count) if self.articles_count > 0 else 0
            if n_articles > 0:
                art_results = self.articles_collection.query(
                    query_texts=[query],
                    n_results=n_articles
                )
                if art_results and art_results['documents']:
                    for i, doc in enumerate(art_results['documents'][0]):
                        meta = art_results['metadatas'][0][i] if art_results['metadatas'] else {}
                        dist = art_results['distances'][0][i] if art_results['distances'] else 0.0
                        results.append({
                            'text': doc,
                            'source': 'articles',
                            'metadata': meta,
                            'distance': dist,
                            'label': f"文章库: {meta.get('fname', '未知')} ({meta.get('article_id', '?')})"
                        })

                # 同义词扩展查询：用 TERM_SYNONYMS 扩展 query，补充召回
                expanded_queries = self._expand_query_synonyms(query)
                for eq in expanded_queries:
                    if eq == query:
                        continue
                    try:
                        eq_results = self.articles_collection.query(
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

                    # BM25 分数归一化：将 BM25 分数映射到距离区间 [0.2, 0.6]
                    # 分数越高 → 距离越小（越相关）
                    bm25_scores_raw = [score for _, score in bm25_hits]
                    bm25_min = min(bm25_scores_raw) if bm25_scores_raw else 0
                    bm25_max = max(bm25_scores_raw) if bm25_scores_raw else 1
                    bm25_range = bm25_max - bm25_min if bm25_max > bm25_min else 1.0

                    # 从 ChromaDB 获取 BM25 命中的 chunk 文本和 metadata
                    bm25_ids = [cid for cid, _ in bm25_hits if cid not in existing_chunk_ids]
                    if bm25_ids:
                        chroma_data = self.articles_collection.get(ids=bm25_ids, include=['documents', 'metadatas'])
                        for i, cid in enumerate(chroma_data['ids']):
                            meta = chroma_data['metadatas'][i] if chroma_data['metadatas'] else {}
                            doc = chroma_data['documents'][i] if chroma_data['documents'] else ''
                            # 找到 BM25 分数并归一化为距离
                            bm25_score = 0.0
                            for hid, hscore in bm25_hits:
                                if hid == cid:
                                    bm25_score = hscore
                                    break
                            # 归一化：最高分 -> 0.2，最低分 -> 0.6
                            norm_score = (bm25_score - bm25_min) / bm25_range
                            bm25_distance = 0.6 - 0.4 * norm_score  # 范围 [0.2, 0.6]

                            results.append({
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
        if target_id and self.articles_collection and self.articles_count > 0:
            try:
                # 按 article_id 模糊匹配（ChromaDB $contains 操作符）
                match_results = self.articles_collection.get(
                    where={"article_id": {"$contains": target_id}}
                )
                if match_results and match_results['documents']:
                    existing_fnames = {r['metadata'].get('fname') for r in results}
                    for i, doc in enumerate(match_results['documents']):
                        meta = match_results['metadatas'][i] if match_results['metadatas'] else {}
                        fname = meta.get('fname', '')
                        if fname not in existing_fnames:
                            results.append({
                                'text': doc,
                                'source': 'articles',
                                'metadata': meta,
                                'distance': 0.0,
                                'label': f"[精确匹配] 文章库: {fname} ({meta.get('article_id', '?')})"
                            })
                            existing_fnames.add(fname)
            except Exception as e:
                logger.debug(f"[VECTOR] article_id 精确匹配失败: {e}")

        # 排序：精确匹配排前面，向量结果按距离排序
        def _sort_key(r):
            is_exact = 0 if r.get('label', '').startswith('[精确匹配]') else 1
            return (is_exact, r.get('distance', 999.0))
        results.sort(key=_sort_key)

        # 从 learned 集合检索
        try:
            n_learned = min(top_k // 3, self.learned_count) if self.learned_count > 0 else 0
            if n_learned > 0 and 'learned' not in self._dim_stale_collections:
                learned_results = self.learned_collection.query(
                    query_texts=[query],
                    n_results=n_learned
                )
                if learned_results and learned_results['documents']:
                    for i, doc in enumerate(learned_results['documents'][0]):
                        meta = learned_results['metadatas'][0][i] if learned_results['metadatas'] else {}
                        dist = learned_results['distances'][0][i] if learned_results['distances'] else 0.0
                        results.append({
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
                    n_personal = min(top_k // 2, self.personal_collection.count())
                    if n_personal > 0:
                        personal_results = self.personal_collection.query(
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

        return results[:top_k * 2]


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
            results = self.corrections_collection.query(
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
            results = self.antipatterns_collection.query(
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
        for coll_name, coll in [
            ('articles', self.collection),
        ]:
            if not coll or coll_name in self._dim_stale_collections:
                continue
            try:
                all_data = coll.get(include=['metadatas'])
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
                    coll.update(
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
            results = self.patches_collection.query(
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
            self.learned_collection.add(
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
            self._learned_count = self.learned_collection.count()
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
            self.learned_collection.add(
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
            self._learned_count = self.learned_collection.count()
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
            self.learned_collection.add(ids=ids, documents=docs, metadatas=metas)
            self._learned_count = self.learned_collection.count()
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
            self.corrections_collection.add(
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
            self._corrections_count = self.corrections_collection.count()
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
            existing = self.articles_collection.get(
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
                self.articles_collection.update(
                    ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                )

            self._articles_count = self.articles_collection.count()

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
                self.patches_collection.delete(ids=[snapshot_id])
            except Exception:
                pass

            self.patches_collection.add(
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
            self._patches_count = self.patches_collection.count()
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
            snapshot = self.patches_collection.get(
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
                self.articles_collection.update(
                    ids=batch_ids, documents=batch_docs, metadatas=batch_metas
                )

            self._articles_count = self.articles_collection.count()

            # 删除快照（已消费）
            self.patches_collection.delete(ids=[snapshot_id])
            self._patches_count = self.patches_collection.count()

            # 从 corrections 集合中标记为已回滚
            try:
                corr_record = self.corrections_collection.get(
                    ids=[correction_id],
                    include=["documents", "metadatas"]
                )
                if corr_record and corr_record['ids']:
                    corr_meta = corr_record['metadatas'][0]
                    corr_meta["rolled_back"] = "true"
                    corr_meta["rolled_back_at"] = datetime.now().isoformat()
                    self.corrections_collection.update(
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
            all_corrections = self.corrections_collection.get(include=["documents", "metadatas"])
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
            self.antipatterns_collection.add(
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
            self._antipatterns_count = self.antipatterns_collection.count()
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
            self.patches_collection.add(
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
            self._patches_count = self.patches_collection.count()
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
            results = self.corrections_collection.get(
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
            results = self.antipatterns_collection.get(
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
            results = self.patches_collection.get(
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
            old = self.corrections_collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            if not old or not old['documents']:
                return False
            old_doc = old['documents'][0]
            old_meta = old['metadatas'][0] if old['metadatas'] else {}
            # 更新 metadata
            new_meta = dict(old_meta)
            new_meta['trust_level'] = round(min(new_trust, 1.0), 2)
            new_meta['applied_count'] = new_applied_count
            # 删除旧记录
            self.corrections_collection.delete(ids=[doc_id])
            # 插入新记录
            self.corrections_collection.add(
                ids=[doc_id],
                documents=[old_doc],
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
                corr_results = self.corrections_collection.get(
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
                anti_results = self.antipatterns_collection.get(
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
                patch_results = self.patches_collection.get(
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
                corr_results = self.corrections_collection.get(
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
                anti_results = self.antipatterns_collection.get(
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
    评估回复的几何论一致性得分。
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
