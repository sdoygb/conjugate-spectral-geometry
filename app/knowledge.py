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


class SiliconFlowEmbeddingFunction:
    """使用 SiliconFlow 免费 API 的中文 Embedding（BAAI/bge-large-zh-v1.5, 1024维）"""

    def __init__(self, api_key: str = "", model: str = "BAAI/bge-large-zh-v1.5"):
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
            if len(t) > 500:
                t = t[:500]
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
        if len(text) > 500:
            text = text[:500]
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
        
        策略：
        - articles 集合：维度不匹配时重建（因为有源文件可以重新索引）
        - learned/corrections/antipatterns/patches/personal：维度不匹配时保留数据，
          但标记为「维度过期」不参与搜索。这些集合没有可靠的重建源。
        """
        import chromadb
        try:
            existing = self.client.get_collection(collection_name)
            count = existing.count()
            if count == 0:
                return existing
            # 尝试用当前 embedding function 生成一个测试向量来检测维度
            test_emb = self.embedding_fn(["维度检测测试"])
            current_dim = len(test_emb[0]) if test_emb else 0
            # 从集合中获取一条记录的维度（peek 不支持 include，用 get 代替）
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
                # articles 集合可以安全重建（有源文件）
                if collection_name == "articles":
                    logger.warning(
                        f"[VECTOR] 集合 '{collection_name}' 维度不匹配 "
                        f"(存储={stored_dim}, 当前={current_dim})，将删除旧数据重建"
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
                else:
                    # 非源文件集合：保留数据，标记维度过期，不删除
                    self._dim_stale_collections.add(collection_name)
                    logger.error(
                        f"[VECTOR] 集合 '{collection_name}' 维度不匹配 "
                        f"(存储={stored_dim}, 当前={current_dim})，"
                        f"保留 {count} 条旧数据。这些数据将不参与向量搜索。"
                        f"如需重建，请手动调用 clear 方法。"
                    )
                    # 返回 None 表示「不要覆盖」，让正常路径的 get_or_create 处理
                    return None
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

            match = re.match(r'([\d\.]+|AI-\d+)', fname)
            article_id = match.group(1) if match else fname
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
                "source": "articles"
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

        match = re.match(r'([\d\.]+|AI-\d+)', fname)
        article_id = match.group(1) if match else fname

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

        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{fname}_{i}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append({
                "article_id": chunk.get('article_id', article_id),
                "fname": chunk.get('fname', fname),
                "start": chunk.get('start', 0),
                "end": chunk.get('end', 0)
            })

        try:
            self.articles_collection.add(
                ids=ids, documents=documents, metadatas=metadatas
            )
            self._articles_count = self.articles_collection.count()
            logger.info(f"[VECTOR] 增量索引: {fname} ({len(chunks)} 块), 总计 {self._articles_count} 块")
        except Exception as e:
            logger.error(f"[VECTOR] 增量索引失败 {fname}: {e}")

    def search(self, query: str, top_k: int = 15, include_personal: bool = False) -> List[Dict[str, Any]]:
        """
        从 articles 集合检索，返回相关文本。
        learned 集合始终参与搜索，可通过 include_personal 附加个人记忆。
        每个结果包含 text, source, metadata 等信息。
        排序规则：articles 优先（按距离），然后 learned（按距离），最后 personal（按距离）。
        """
        if not self._initialized:
            return []

        results = []

        # 从 articles 集合检索
        try:
            n_articles = min(top_k * 2 // 3, self.articles_count) if self.articles_count > 0 else 0
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
        except Exception as e:
            logger.error(f"[VECTOR] articles 检索失败: {e}")

        # 从 learned 集合检索（始终参与搜索，但数量限制为 top_k//3）
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

        # 分组排序：articles 优先（按距离），然后 learned（按距离），最后 personal（按距离）
        def _sort_key(r):
            source_order = {'articles': 0, 'learned': 1, 'personal': 2}
            return (source_order.get(r.get('source', ''), 99), r.get('distance', 999.0))
        results.sort(key=_sort_key)

        # personal 集合单独追加（不抢占文章排名）
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

        return results[:top_k]

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
                header = (
                    f"\n{'='*50}\n"
                    f"[学习记忆] 质量分:{r['metadata'].get('quality_score', '?')} "
                    f"距离:{r['distance']:.4f}\n"
                    f"{'='*50}\n"
                )
            else:
                meta = r['metadata']
                fname = meta.get('fname', '')
                header = (
                    f"\n{'='*50}\n"
                    f"文章: {meta.get('article_id', '?')} ({fname}) "
                    f"位置:{meta.get('start', '?')}-{meta.get('end', '?')} "
                    f"距离:{r['distance']:.4f}"
                )
                if fname:
                    header += f"\n完整文章: [点击预览](http://localhost:5000/preview/{fname})"

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
                       context: str = "", session_id: str = "") -> bool:
        """
        v10 新增：添加一条纠正记录到 corrections 集合。
        """
        if not self._initialized:
            return False
        if not wrong or not correct:
            return False

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
                    "trust_level": 0.5,
                    "applied_count": 0,
                    "created_at": now,
                    "session_id": session_id[:64] if session_id else "",
                }]
            )
            self._corrections_count = self.corrections_collection.count()
            logger.info(
                f"[TEACH-CORRECT] 纠正已存入 | corrections总数={self._corrections_count}"
            )
            return True
        except Exception as e:
            logger.error(f"[TEACH-CORRECT] 存入纠正失败: {e}")
            return False

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
