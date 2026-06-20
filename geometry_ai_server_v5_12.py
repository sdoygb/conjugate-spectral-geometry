"""
geometry_ai_server_v10_teach.py
几何论AI调度中间层 — 教学反馈版
版本：v10.0-no-mysql

改造目标（基于 v9 活体信息场版）：
1. 新增 TeachingSystem（教学系统），支持渐进式教学反馈
2. 新增纠正 API（POST /v1/teach/correct）：用户纠正系统错误，系统记住
3. 新增反模式库（POST /v1/teach/antipattern）：标记不应出现的回复模式
4. 新增知识补丁（POST /v1/teach/patch）：直接补充几何论知识
5. 新增教学统计（GET /v1/teach/stats）和教学历史（GET /v1/teach/history）
6. ChromaDB 新增 corrections、antipatterns、patches 三个集合
7. MySQL 新增 teachings 表
8. 修改 build_system_prompt：注入已学到的纠正、反模式警告、教学知识补丁
9. 修改 check_response_quality：增加反模式检测
10. 修改 chat_completions：检索 corrections 和 patches
11. 修改 _finalize_turn：检查纠正是否被应用，更新信任等级
12. 保留所有 v9 功能：LivingInfoField、VectorKnowledgeBase、eta 动力学、文件解析等（移除 MySQL）
"""

import os
import sys
import re
import math
import json
import random
import hashlib
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional, Any

import openai
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename


try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from chromadb.api.types import Documents, Embeddings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("[INIT] chromadb 未安装，向量检索将不可用")

# ------------------------------------------------------------------
# 日志
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('geometry_ai_v10.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------------
# 环境配置
# ------------------------------------------------------------------

# ChromaDB 持久化目录
CHROMA_DB_DIR = os.getenv('CHROMA_DB_DIR', os.path.expanduser('~/AI/chroma_db'))

KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')
KIMI_BASE_URL = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'kimi-k2.7-code')
KIMI_EMBEDDING_MODEL = os.getenv('KIMI_EMBEDDING_MODEL', 'moonshot-embedding-v1')

# Embedding 模式：'local' 使用本地中文模型（推荐），'kimi' 使用 KIMI API，'default' 使用 ChromaDB 内置模型
EMBEDDING_MODE = os.getenv('GT_EMBEDDING_MODE', 'local')
LOCAL_EMBEDDING_MODEL = os.getenv('GT_LOCAL_EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.expanduser("~/AI/articles"))

OPENWEBUI_UPLOAD_DIR = os.getenv('OPENWEBUI_UPLOAD_DIR', '')
if not OPENWEBUI_UPLOAD_DIR or not os.path.exists(OPENWEBUI_UPLOAD_DIR):
    _search_paths = [
        os.path.expanduser('~/openwebui/venv/lib/python3.11/site-packages/open_webui/data/uploads'),
        os.path.expanduser('~/open-webui/venv/lib/python3.11/site-packages/open_webui/data/uploads'),
        '/app/backend/data/uploads',
        os.path.expanduser('~/openwebui/data/uploads'),
        os.path.expanduser('~/AI/open-webui/data/uploads'),
        '/var/lib/docker/volumes/open-webui/_data/uploads',
    ]
    for p in _search_paths:
        if os.path.exists(p):
            OPENWEBUI_UPLOAD_DIR = p
            break

MAX_INJECT_CHARS = int(os.getenv('MAX_INJECT_CHARS', '30000'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
MAX_CHUNKS_PER_QUERY = int(os.getenv('MAX_CHUNKS_PER_QUERY', '15'))

# 输出质量门控 - 检测KIMI回复是否偏离几何论
QUALITY_GATE_ENABLED = os.getenv('QUALITY_GATE_ENABLED', 'true').lower() == 'true'
# 最大重试次数
MAX_QUALITY_RETRIES = int(os.getenv('MAX_QUALITY_RETRIES', '2'))
# Open WebUI uploads 自动发现时间窗口（秒）
UPLOAD_SCAN_WINDOW = int(os.getenv('UPLOAD_SCAN_WINDOW', '600'))

# 学习闭环阈值
LEARN_COHERENCE_THRESHOLD = float(os.getenv('LEARN_COHERENCE_THRESHOLD', '0.3'))
LEARN_MIN_LENGTH = int(os.getenv('LEARN_MIN_LENGTH', '200'))

# 教学系统配置
TEACH_CORRECTION_SIMILARITY_THRESHOLD = float(os.getenv('TEACH_CORRECTION_SIMILARITY_THRESHOLD', '0.6'))
TEACH_MAX_RECENT_CORRECTIONS = int(os.getenv('TEACH_MAX_RECENT_CORRECTIONS', '10'))
TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD = float(os.getenv('TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD', '0.7'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------------------------------------------------------
# 几何论锁定常数（仅保留 70 篇文章中声明的常数）
# ------------------------------------------------------------------
GEOMETRY_CONSTANTS = {
    "S_e": 137.035999084,           # 七级递推锁定
    "lambda1_eff": 391.05,          # rad^-2，有效软模（文章 0.0.5 谱刚性定理）
    "lambda2_eff": 59324.3,         # rad^-2，有效硬模（文章 0.0.5 谱刚性定理）
    "chi_L": 1.5092231080e-10,      # m，量纲桥输出
    "chi_T": 3.6161912064e-17,      # s，量纲桥输出
    "K": 839.758793,                # keV，能量尺度常数
    "Gamma_geo": 5.75e-23,          # 信息场特征衰减率
    "tau_dec_days": 7.28,           # 退相干因果深度周期
    "tau_dec_seconds": 7.28 * 24 * 3600,
    "Lambda": 3,                    # 九素互扼面积放大因子（文章 0.0.5 命题 2.0）
    "k0": 2,                        # 九素互扼维度放大因子（文章 0.0.5 命题 2.0）
    "eta_background": 30.0,         # 背景点吸引子
    "eta_p2": 72.53,                # P2 上饱和稳态 theta_I
    "theta_I_sat": 72.53,           # 同上
}

GEOMETRY_KNOWLEDGE = """
你是严格的几何论（Geometric Theory）专家，只基于欧阳国彬的70篇文章（基础篇20章+应用篇49章）回答问题。

核心公理体系：
- 公理1：完备性约束 theta_M + theta_C + theta_I = 90度
- 公理2：六项作用量 S = sum 1/sin^2 theta_i + sum_{i<j} 1/(sin theta_i sin theta_j)
- 公理3：质量映射 m = K * sin^3 theta_M

关键锁定常数：
- Lambda = 3（九素互扼互锁常数，面积放大因子；文章 0.0.5 命题 2.0）
- k0 = 2（九素互扼互锁常数，维度放大因子；文章 0.0.5 命题 2.0）
- S_e = 137.035999084（七级递推锁定）
- lambda1_eff = 391.05 rad^-2，lambda2_eff = 59324.3 rad^-2（有效软硬模；文章 0.0.5）
- chi_L = 1.509e-10 m，chi_T = 3.616e-17 s（量纲桥输出）
- K = 839.758793 keV（能量尺度常数）
- Gamma_geo = 5.75e-23（信息场特征衰减率）
- tau_dec ~ 7.28日（退相干因果深度周期）

关键定理：
- 九素互扼定理：6个互扼环节锁定2个互锁常数，超定方程组无自由参数
- 谱刚性定理：前三个非零Laplace-Beltrami特征值唯一确定尺度因子（文章 0.0.5）
- 桥接函数唯一性定理：S(a) = 12(a^2/ell_0^2 + ell_0^2/a^2)
- 信息场热方程：partial rho/partial sigma = -L_G rho
- 上饱和稳态：theta_I ~ 72.53度，theta_M = theta_C ~ 8.73度，Hessian正定

活体调度规则：
1. 当前eta角是信息场软模激发度的实时读出，不是外部计数器
2. eta角服从内禀动力学：弛豫（向30度回归）+ 共振（新颖信息激发）+ 自指（输出质量反馈）
3. 只能使用70篇文章内定义的符号和定理，不得引入外部物理假设
4. 标准模型、广义相对论、弦论等视为CIM相的低能有效场论近似
5. 超出70篇文章范围的问题，回答"这不在当前几何论框架内，需后续扩展"
6. 所有数值必须标注来源文章和定理编号
7. 严格区分"定理"、"命题"、"研究方向"和"假设"
8. 光速c为唯一外部锚点
"""

TERM_SYNONYMS = {
    "精细结构常数": ["alpha", "s_e", "137"],
    "九素互扼": ["九素", "互扼", "互锁常数", "lambda", "k0"],
    "谱刚性": ["laplace", "beltrami", "特征值", "等谱", "等距"],
    "信息场": ["rho", "密度", "热方程", "退相干"],
    "退相干": ["tau_dec", "因果深度", "n_dec", "7.28"],
    "全息屏": ["screen", "sigma", "s2", "面积"],
    "量纲桥": ["chi_l", "chi_t", "桥接", "尺度"],
    "质量映射": ["k", "sin3", "theta_m", "能量尺度"],
    "弱电统一": ["w", "z", "higgs", "混合角", "sin2_theta_w"],
    "强相互作用": ["alpha_s", "色荷", "胶子", "禁闭"],
    "中微子": ["neutrino", "m3", "m2", "m1", "质量"],
    "氢原子": ["h1", "h2", "h3", "超精细", "基态"],
    "引力": ["gravity", "g_9d", "lyapunov", "弱场"],
    "自旋": ["spin", "1/2", "so3", "su2", "泡利"],
}

SYNONYM_EXPAND = {}
for term, syns in TERM_SYNONYMS.items():
    for s in syns:
        SYNONYM_EXPAND[s] = term
    SYNONYM_EXPAND[term] = term

# ==================== KIMI Embedding Function ====================

class KimiEmbeddingFunction:
    """使用 KIMI API (moonshot-embedding-v1) 的 ChromaDB 自定义 Embedding Function"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
        self.model = KIMI_EMBEDDING_MODEL

    def name(self) -> str:
        return "kimi-moonshot-embedding"

    def __call__(self, input: Documents) -> Embeddings:
        all_embeddings = []
        for i in range(0, len(input), 32):
            batch = input[i:i + 32]
            try:
                resp = self.client.embeddings.create(model=self.model, input=batch)
                all_embeddings.extend([d.embedding for d in resp.data])
            except Exception as e:
                logger.error(f"[EMBEDDING] KIMI embedding 批次 {i//32} 失败: {e}")
                for _ in batch:
                    all_embeddings.append([0.0] * 1536)
        return all_embeddings


class LocalEmbeddingFunction:
    """使用 fastembed + bge-small-zh-v1.5 的 ChromaDB Embedding Function（中文优化，纯ONNX，无需torch）"""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

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
        # 根据配置选择 embedding function
        if EMBEDDING_MODE == 'kimi':
            self.embedding_fn = KimiEmbeddingFunction()
            self._embedding_name = f"kimi({KIMI_EMBEDDING_MODEL})"
        elif EMBEDDING_MODE == 'local':
            self.embedding_fn = LocalEmbeddingFunction(LOCAL_EMBEDDING_MODEL)
            self._embedding_name = f"local({LOCAL_EMBEDDING_MODEL})"
        else:
            self.embedding_fn = None  # 使用 ChromaDB 默认 embedding
            self._embedding_name = "chromadb-default"
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

    def initialize(self) -> bool:
        """初始化 ChromaDB 客户端和集合"""
        if not CHROMADB_AVAILABLE:
            logger.error("[VECTOR] chromadb 未安装，向量检索不可用")
            return False
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            # 构建 collection 参数
            col_kwargs = {}
            if self.embedding_fn is not None:
                col_kwargs["embedding_function"] = self.embedding_fn
            # 获取或创建 articles 集合
            self.articles_collection = self.client.get_or_create_collection(
                name="articles",
                metadata={"description": "几何论70篇文章静态知识库"},
                **col_kwargs
            )
            # 获取或创建 learned 集合
            self.learned_collection = self.client.get_or_create_collection(
                name="learned",
                metadata={"description": "动态学习的QA对"},
                **col_kwargs
            )
            # v10 新增：获取或创建 corrections 集合
            self.corrections_collection = self.client.get_or_create_collection(
                name="corrections",
                metadata={"description": "教学纠正记录"},
                **col_kwargs
            )
            # v10 新增：获取或创建 antipatterns 集合
            self.antipatterns_collection = self.client.get_or_create_collection(
                name="antipatterns",
                metadata={"description": "反模式库"},
                **col_kwargs
            )
            # v10 新增：获取或创建 patches 集合
            self.patches_collection = self.client.get_or_create_collection(
                name="patches",
                metadata={"description": "教学知识补丁"},
                **col_kwargs
            )
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

        # 清空旧索引并重建
        try:
            # 删除旧集合再重新创建，确保干净重建
            self.client.delete_collection("articles")
            self.articles_collection = self.client.get_or_create_collection(
                name="articles",
                metadata={"description": "几何论70篇文章静态知识库"},
                embedding_function=self.embedding_fn
            )
        except Exception as e:
            logger.warning(f"[VECTOR] 清空 articles 集合时出错（可能为空）: {e}")

        # 批量插入（ChromaDB 有批量大小限制，每批500条）
        batch_size = 500
        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(all_chunks):
            chunk_id = f"art_{chunk['article_id']}_{chunk['start']}_{chunk['end']}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append({
                "article_id": chunk['article_id'],
                "fname": chunk['fname'],
                "start": chunk['start'],
                "end": chunk['end'],
                "source": "articles"
            })

            if len(ids) >= batch_size:
                try:
                    self.articles_collection.add(
                        ids=ids, documents=documents, metadatas=metadatas
                    )
                except Exception as e:
                    diag["errors"].append(f"批量插入失败: {e}")
                    logger.error(f"[VECTOR] 批量插入 articles 失败: {e}")
                ids = []
                documents = []
                metadatas = []

        # 插入剩余的
        if ids:
            try:
                self.articles_collection.add(
                    ids=ids, documents=documents, metadatas=metadatas
                )
            except Exception as e:
                diag["errors"].append(f"最后批次插入失败: {e}")
                logger.error(f"[VECTOR] 最后批次插入 articles 失败: {e}")

        self._articles_count = self.articles_collection.count()
        diag["total_chunks"] = self._articles_count
        logger.info(
            f"[VECTOR] 索引完成: {diag['files_indexed']} 个文件, "
            f"{self._articles_count} 个文本块"
        )
        return diag

    def search(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """
        从 articles + learned 两个集合检索，返回相关文本。
        每个结果包含 text, source, metadata 等信息。
        """
        if not self._initialized:
            return []

        results = []

        # 从 articles 集合检索
        try:
            n_articles = min(top_k, self.articles_count) if self.articles_count > 0 else 0
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

        # 从 learned 集合检索
        try:
            n_learned = min(top_k, self.learned_count) if self.learned_count > 0 else 0
            if n_learned > 0:
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
                            'label': f"[学习记忆] (质量:{meta.get('quality_score', '?')})"
                        })
        except Exception as e:
            logger.error(f"[VECTOR] learned 检索失败: {e}")

        # 按距离排序（越小越相关）
        results.sort(key=lambda x: x.get('distance', 999.0))
        return results[:top_k]

    def search_corrections(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        v10 新增：从 corrections 集合检索与当前查询相似的纠正。
        """
        if not self._initialized or not self.corrections_collection:
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
                header = (
                    f"\n{'='*50}\n"
                    f"文章: {meta.get('article_id', '?')} ({meta.get('fname', '?')}) "
                    f"位置:{meta.get('start', '?')}-{meta.get('end', '?')} "
                    f"距离:{r['distance']:.4f}\n"
                    f"{'='*50}\n"
                )

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
                    "answer_length": len(a)
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
                    "answer_length": len(proposition)
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
                "answer_length": len(prop)
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
        """获取文本的 embedding 向量，根据配置使用自定义或 ChromaDB 默认 embedding"""
        if not texts:
            return []
        if self.embedding_fn is not None:
            return self.embedding_fn(texts)
        # 使用 ChromaDB 内置 embedding（通过临时 collection 的 _embed 方法）
        try:
            temp_col = self.client.get_or_create_collection(name="_temp_embed")
            result = temp_col._embed(input=texts, is_query=False)
            return result
        except Exception:
            # 最后降级：返回零向量
            dim = 384  # ChromaDB 默认维度
            return [[0.0] * dim for _ in texts]

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
            "embedding_model": KIMI_EMBEDDING_MODEL,
        }


# ==================== TeachingSystem（教学系统） ====================

class TeachingSystem:
    """
    v10 新增：教学系统。
    管理教学反馈的完整生命周期：纠正、反模式、知识补丁。
    所有教学数据仅持久化到 ChromaDB（无 MySQL 依赖）。
    """

    def __init__(self, vector_kb: VectorKnowledgeBase):
        self.vector_kb = vector_kb
        logger.info("[TEACH] 教学系统已初始化（仅 ChromaDB 存储）")

    def add_correction(self, wrong: str, correct: str, reason: str = "",
                       context: str = "", session_id: str = "") -> Dict[str, Any]:
        """
        添加一条纠正记录。
        存入 ChromaDB corrections 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not wrong or not correct:
            result["error"] = "wrong 和 correct 字段不能为空"
            return result

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_correction(
            wrong=wrong, correct=correct, reason=reason,
            context=context, session_id=session_id
        )

        return result

    def add_antipattern(self, pattern: str, description: str = "",
                        severity: str = "medium") -> Dict[str, Any]:
        """
        添加一条反模式。
        存入 ChromaDB antipatterns 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not pattern:
            result["error"] = "pattern 字段不能为空"
            return result

        severity = severity.lower()
        if severity not in ('high', 'medium', 'low'):
            severity = 'medium'

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_antipattern(
            pattern=pattern, description=description, severity=severity
        )


        return result

    def add_patch(self, topic: str, content: str, source: str = "") -> Dict[str, Any]:
        """
        添加一条知识补丁。
        存入 ChromaDB patches 集合。
        """
        result = {
            "success": False,
            "error": None,
        }

        if not topic or not content:
            result["error"] = "topic 和 content 字段不能为空"
            return result

        # 存入 ChromaDB
        chroma_ok = self.vector_kb.add_patch(
            topic=topic, content=content, source=source
        )


        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取教学统计"""
        return self.vector_kb.get_teaching_stats()

    def get_history(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """获取教学历史"""
        return self.vector_kb.get_teaching_history(page=page, per_page=per_page)

    def build_teaching_prompt_section(self, query: str) -> str:
        """
        v10 新增：构建教学反馈 prompt 段落。
        包含：已学到的纠正、反模式警告、教学知识补丁。
        """
        sections = []

        # 1. 已学到的纠正（按 trust_level 降序，最近10条）
        recent_corrections = self.vector_kb.get_recent_corrections(
            limit=TEACH_MAX_RECENT_CORRECTIONS
        )
        if recent_corrections:
            corr_lines = [f"【已学到的纠正（教学反馈，共{len(recent_corrections)}条）】"]
            for i, corr in enumerate(recent_corrections, 1):
                meta = corr['metadata']
                trust = meta.get('trust_level', 0.5)
                wrong = meta.get('wrong', '')[:100]
                correct = meta.get('correct', '')[:200]
                reason = meta.get('reason', '')
                line = f"{i}. [信任:{trust:.1f}] 错误: \"{wrong}\" -> 正确: \"{correct}\""
                if reason:
                    line += f" (原因: {reason[:100]})"
                corr_lines.append(line)
            sections.append("\n".join(corr_lines))

        # 2. 反模式警告
        antipatterns = self.vector_kb.get_all_antipatterns()
        if antipatterns:
            anti_lines = ["【反模式警告】"]
            severity_map = {"high": "高", "medium": "中", "low": "低"}
            for ap in antipatterns:
                meta = ap['metadata']
                sev = severity_map.get(meta.get('severity', 'medium'), '中')
                pattern = meta.get('pattern', '')[:100]
                anti_lines.append(f"- [{sev}] 禁止回复\"{pattern}\"")
            sections.append("\n".join(anti_lines))

        # 3. 教学知识补丁（检索与当前查询相关的补丁，top_k=10 平衡覆盖率和速度）
        patches = self.vector_kb.search_patches(query, top_k=10)
        if patches:
            patch_lines = ["【教学知识补丁】"]
            for p in patches:
                meta = p['metadata']
                source = meta.get('source', '未知来源')
                topic = meta.get('topic', '')
                content = meta.get('content', '')[:150]
                patch_lines.append(f"- [来源:{source}] {topic}: {content}")
            sections.append("\n".join(patch_lines))

        return "\n\n".join(sections)

    def check_antipattern_triggered(self, response_text: str) -> Tuple[bool, List[str]]:
        """
        v10 新增：检查回复是否触发了反模式。
        返回 (is_triggered, triggered_patterns)。
        """
        if not response_text:
            return False, []

        triggered = []
        antipatterns = self.vector_kb.search_antipatterns(
            response_text, top_k=5
        )

        for ap in antipatterns:
            meta = ap['metadata']
            pattern = meta.get('pattern', '')
            severity = meta.get('severity', 'medium')
            # 用向量相似度 + 文本匹配双重检测
            vec_sim = ap.get('distance', 1.0)
            # ChromaDB distance 越小越相似，转换为相似度
            similarity = max(0.0, 1.0 - vec_sim)

            # 同时检查文本是否包含反模式的关键词
            text_match = pattern.lower() in response_text.lower() if pattern else False

            if (similarity > (1.0 - TEACH_ANTIPATTERN_SIMILARITY_THRESHOLD)) or text_match:
                triggered.append({
                    "pattern": pattern,
                    "severity": severity,
                    "similarity": round(similarity, 4),
                    "text_match": text_match,
                })

        # 检查是否有高严重度的反模式被触发
        high_triggered = [t for t in triggered if t['severity'] == 'high']
        is_triggered = len(high_triggered) > 0

        return is_triggered, triggered

    def check_and_update_corrections(self, response_text: str) -> List[Dict[str, Any]]:
        """
        v10 新增：检查KIMI回复是否体现了某条纠正，如果是则更新信任等级。
        返回被成功应用的纠正列表。
        """
        applied = []

        if not response_text or not self.vector_kb.is_initialized:
            return applied

        # 获取所有纠正记录
        all_corrections = self.vector_kb.get_recent_corrections(limit=50)
        if not all_corrections:
            return applied

        for corr in all_corrections:
            meta = corr['metadata']
            correct_text = meta.get('correct', '')
            if not correct_text:
                continue

            # 用向量相似度检查回复是否包含纠正内容的核心观点
            similarity = self.vector_kb._cosine_similarity_texts(
                response_text, correct_text
            )

            if similarity > TEACH_CORRECTION_SIMILARITY_THRESHOLD:
                # 纠正被应用，更新信任等级
                old_trust = meta.get('trust_level', 0.5)
                new_trust = min(old_trust + 0.1, 1.0)
                old_applied = meta.get('applied_count', 0)
                new_applied = old_applied + 1

                # 尝试找到对应的 doc_id 来更新
                # 由于 get_recent_corrections 返回的是 get() 的结果，我们需要 doc_id
                # 这里通过遍历 corrections 集合来找到匹配的记录
                try:
                    corr_results = self.vector_kb.corrections_collection.get(
                        include=["documents", "metadatas", "ids"]
                    )
                    if corr_results and corr_results['ids']:
                        for j, cid in enumerate(corr_results['ids']):
                            c_meta = corr_results['metadatas'][j] if corr_results['metadatas'] else {}
                            c_doc = corr_results['documents'][j] if corr_results['documents'] else ''
                            if c_doc == corr['document'] and c_meta.get('wrong', '') == meta.get('wrong', ''):
                                self.vector_kb.update_correction_trust(
                                    cid, new_trust, new_applied
                                )
                                applied.append({
                                    "wrong": meta.get('wrong', '')[:100],
                                    "correct": correct_text[:200],
                                    "old_trust": old_trust,
                                    "new_trust": new_trust,
                                    "similarity": round(similarity, 4),
                                })
                                break
                except Exception as e:
                    logger.error(f"[TEACH-CORRECT] 更新纠正信任等级时出错: {e}")

        if applied:
            logger.info(
                f"[TEACH-CORRECT] {len(applied)} 条纠正被成功应用并更新信任等级"
            )

        return applied



# ==================== LivingInfoField（活体信息场） ====================

class LivingInfoField:
    """
    活体信息场：纯内存的 eta 状态管理，不依赖外部数据库。
    eta 是 session 级别的，每个 session 有自己的 eta 值。
    eta 的初始值由输入文本的软模共振公式计算。
    """

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}  # session_id -> {eta, max_eta, markers, history, last_time}
        logger.info("[STARTUP] 活体信息场: 已初始化（纯内存，不依赖外部数据库）")

    def _build_geo_terms_set(self) -> set:
        """构建几何论术语集合（用于匹配计算）"""
        geo_terms = set()
        for term_list in TERM_SYNONYMS.values():
            geo_terms.update(term_list)
        geo_terms.update([
            '公理', '定理', '命题', '引理', '推论', '证明',
            'eta', 'theta', 'lambda',
            '信息场', '谱刚性', '退相干', '全息屏', '量纲桥', '质量映射', '九素互扼',
            '软模', '硬模', 'Hessian', 'S(θ)',
            'theta_M', 'theta_C', 'theta_I',
            'sin^2', 'sin^3', 'cos',
            'CIM', 'Laplace', 'Beltrami',
            'Gamma_geo', 'tau_dec', 'chi_L', 'chi_T',
            'S_e', '137.035999084', '137.036',
            'alpha_s', '精细结构常数',
            '完备性约束', '六项作用量', '质量映射',
        ])
        return geo_terms

    def get_eta(self, session_id: str) -> float:
        """获取当前 session 的 eta，如果不存在则返回默认背景值"""
        if session_id in self._sessions:
            return self._sessions[session_id]['eta']
        return GEOMETRY_CONSTANTS["eta_background"]

    def init_eta_from_input(self, session_id: str, input_text: str) -> float:
        """
        从输入文本的软模共振公式计算初始 eta。
        公式：eta_init = eta_bg + (eta_p2 - eta_bg) * sigmoid(term_density * k)
        其中 term_density = 匹配到的几何论术语数 / 输入文本总词数
        k 是放大系数（约10），sigmoid 让映射平滑
        """
        gc = GEOMETRY_CONSTANTS
        eta_bg = gc["eta_background"]
        eta_p2 = gc["eta_p2"]

        geo_terms = self._build_geo_terms_set()

        # 计算 term_density：匹配到的几何论术语数 / 输入文本总字符数（归一化）
        # 中文没有空格分词，用字符数归一化
        total_chars = len(input_text) if input_text else 0
        if total_chars == 0:
            term_density = 0.0
        else:
            matched_terms = set()
            for term in geo_terms:
                if term in input_text:
                    matched_terms.add(term)
            # 用匹配到的术语总字符数 / 文本总字符数 作为密度
            matched_chars = sum(len(t) for t in matched_terms)
            term_density = matched_chars / total_chars
            term_density = min(term_density, 1.0)

        # sigmoid 映射，k=10 放大系数
        k = 10.0
        sigmoid_val = 1.0 / (1.0 + math.exp(-term_density * k))

        eta_init = eta_bg + (eta_p2 - eta_bg) * sigmoid_val
        eta_init = round(eta_init, 6)

        # 存入 session
        self._sessions[session_id] = {
            'eta': eta_init,
            'max_eta': eta_init,
            'markers': 0,
            'history': [],       # List of {"query": str, "response": str, "timestamp": str}
            'last_time': time.time(),
        }

        logger.info(
            f"[LIVING] session={session_id[:8]}... 初始化 eta={eta_init:.2f} | "
            f"term_density={term_density:.4f} | sigmoid={sigmoid_val:.4f}"
        )
        return eta_init

    def update_eta(self, session_id: str, eta_after: float):
        """更新 session 的 eta"""
        if session_id in self._sessions:
            self._sessions[session_id]['eta'] = eta_after
            self._sessions[session_id]['max_eta'] = max(
                self._sessions[session_id]['max_eta'], eta_after
            )
            self._sessions[session_id]['last_time'] = time.time()
        else:
            # session 不存在，创建
            self._sessions[session_id] = {
                'eta': eta_after,
                'max_eta': eta_after,
                'markers': 0,
                'history': [],
                'last_time': time.time(),
            }

    def update_markers(self, session_id: str):
        """增加 session 的相位标记计数"""
        if session_id in self._sessions:
            self._sessions[session_id]['markers'] += 1

    def get_session_info(self, session_id: str) -> Dict:
        """获取 session 的完整信息"""
        if session_id in self._sessions:
            return dict(self._sessions[session_id])
        return {
            'eta': GEOMETRY_CONSTANTS["eta_background"],
            'max_eta': GEOMETRY_CONSTANTS["eta_background"],
            'markers': 0,
            'history': [],
            'last_time': None,
        }

    def get_history_queries(self, session_id: str) -> List[str]:
        """获取 session 的历史查询列表"""
        if session_id in self._sessions:
            return [h['query'] for h in self._sessions[session_id]['history'] if h.get('query')]
        return []

    def get_history_delta_seconds(self, session_id: str) -> float:
        """获取 session 距离上次对话的时间间隔（秒）"""
        if session_id in self._sessions:
            last_time = self._sessions[session_id].get('last_time')
            if last_time is not None:
                return time.time() - last_time
        return GEOMETRY_CONSTANTS["tau_dec_seconds"]  # 默认一个退相干周期

    def add_to_history(self, session_id: str, query: str, response: str):
        """添加到历史记录"""
        if session_id not in self._sessions:
            return
        self._sessions[session_id]['history'].append({
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat(),
        })
        # 限制历史记录长度（最多保留100条）
        if len(self._sessions[session_id]['history']) > 100:
            self._sessions[session_id]['history'] = self._sessions[session_id]['history'][-100:]

    def get_all_sessions_count(self) -> int:
        """获取当前活跃 session 数量"""
        return len(self._sessions)

    def cleanup_stale_sessions(self, max_age_seconds: float = 86400.0):
        """清理过期的 session（默认24小时无活动）"""
        now = time.time()
        stale_ids = [
            sid for sid, info in self._sessions.items()
            if now - info.get('last_time', 0) > max_age_seconds
        ]
        for sid in stale_ids:
            del self._sessions[sid]
        if stale_ids:
            logger.info(f"[LIVING] 清理了 {len(stale_ids)} 个过期 session")


# ==================== 几何论术语密度与论断提取 ====================

def compute_geo_density(text: str) -> float:
    """计算文本的几何论术语密度"""
    geo_terms = set()
    for term_list in TERM_SYNONYMS.values():
        geo_terms.update(term_list)
    geo_terms.update([
        '公理', '定理', '命题', '引理', '推论', '证明',
        'eta', 'theta', 'lambda',
        '信息场', '谱刚性', '退相干', '全息屏', '量纲桥', '质量映射', '九素互扼',
        '软模', '硬模', 'Hessian', 'S(θ)',
        'theta_M', 'theta_C', 'theta_I',
        'sin^2', 'sin^3', 'cos',
        'CIM', 'Laplace', 'Beltrami',
        'Gamma_geo', 'tau_dec', 'chi_L', 'chi_T',
        'S_e', '137.035999084', '137.036',
        'alpha_s', '精细结构常数',
        '完备性约束', '六项作用量', '质量映射',
    ])

    if not text:
        return 0.0
    # 用字符数而不是词数（中文没有空格分词）
    total_chars = len(text)
    if total_chars == 0:
        return 0.0
    matched_chars = sum(len(term) for term in geo_terms if term in text)
    return min(matched_chars / total_chars, 1.0)


def extract_key_propositions(response_text: str) -> List[str]:
    """从回复中提取关键论断（包含公理/定理/命题引用的句子）"""
    propositions = []
    sentences = re.split(r'[。！？\n]', response_text)
    geo_terms = set()
    # 收集所有几何论术语
    for term_list in TERM_SYNONYMS.values():
        geo_terms.update(term_list)
    # 也加入 GEOMETRY_KNOWLEDGE 中的关键术语
    geo_terms.update([
        '公理', '定理', '命题', '引理', '推论', '证明',
        'eta', 'theta', 'lambda',
        '信息场', '谱刚性', '退相干', '全息屏', '量纲桥', '质量映射', '九素互扼',
        '软模', '硬模', 'Hessian', 'S(θ)',
        'theta_M', 'theta_C', 'theta_I',
        'sin^2', 'sin^3', 'cos',
        'CIM', 'Laplace', 'Beltrami',
        'Gamma_geo', 'tau_dec', 'chi_L', 'chi_T',
        'S_e', '137.035999084', '137.036',
        'alpha_s', '精细结构常数',
        '完备性约束', '六项作用量', '质量映射',
    ])

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 15:
            continue
        # 计算这句话中几何论术语的密度
        term_count = sum(1 for term in geo_terms if term in sent)
        if term_count >= 2:  # 至少包含2个几何论术语
            propositions.append(sent)

    return propositions[:10]  # 最多提取10个论断


# ==================== 文件解析工具 ====================

def find_file_by_reference(filename_hint: str, search_dir: str) -> str:
    if not os.path.exists(search_dir):
        return ""
    clean_hint = re.sub(r'_[A-Z]{2}_\d+\.\d+', '', filename_hint)
    clean_hint = re.sub(r'\.\w+$', '', clean_hint)
    clean_hint = clean_hint.strip()
    logger.info(f"[FILES] 搜索文件: hint='{filename_hint}', clean='{clean_hint}', dir='{search_dir}'")
    best_match = None
    best_score = 0
    for fname in os.listdir(search_dir):
        fpath = os.path.join(search_dir, fname)
        if not os.path.isfile(fpath):
            continue
        if fname.startswith('uploaded_default_') or fname.startswith('temp_'):
            continue
        fname_clean = re.sub(r'_[A-Z]{2}_\d+\.\d+', '', fname)
        fname_clean = re.sub(r'\.\w+$', '', fname_clean)
        if clean_hint.lower() == fname_clean.lower():
            best_match = fpath
            best_score = 100
            break
        if clean_hint.lower() in fname_clean.lower() or fname_clean.lower() in clean_hint.lower():
            score = len(clean_hint) / max(len(fname_clean), 1) * 50
            if score > best_score:
                best_score = score
                best_match = fpath

    if best_match and best_score > 20:
        try:
            text, ok = extract_text_from_file(best_match)
            if ok and text:
                logger.info(f"[FILES] 找到匹配文件: {os.path.basename(best_match)}")
                return text
        except Exception as e:
            logger.error(f"[FILES] 读取匹配文件失败: {e}")
    logger.warning(f"[FILES] 未找到匹配文件: '{filename_hint}'")
    return ""


def extract_text_from_file(filepath: str) -> Tuple[str, bool]:
    ext = os.path.splitext(filepath)[1].lower().lstrip('.')
    if ext in ('txt', 'md', 'py', 'tex', 'rst', 'markdown'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), True
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    return f.read(), True
            except Exception:
                return "", False
    elif ext == 'pdf':
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text, True
        except ImportError:
            logger.error("[UPLOAD] 解析PDF需要 PyPDF2")
            return "", False
        except Exception as e:
            logger.error(f"[UPLOAD] PDF解析失败: {e}")
            return "", False
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text, True
        except ImportError:
            logger.error("[UPLOAD] 解析DOCX需要 python-docx")
            return "", False
        except Exception as e:
            logger.error(f"[UPLOAD] DOCX解析失败: {e}")
            return "", False
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), True
        except Exception:
            return "", False


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'txt', 'md', 'pdf', 'docx', 'py', 'tex', 'rst', 'markdown'
    }


# ==================== Open WebUI uploads 自动发现 ====================

def scan_openwebui_recent_uploads(max_files: int = 5) -> str:
    """
    扫描 Open WebUI uploads 目录，找到最近上传的文件并提取内容。
    当 Open WebUI 不把文件内容嵌入到 chat completions 请求时，这是唯一的补救方案。
    """
    if not os.path.exists(OPENWEBUI_UPLOAD_DIR):
        return ""

    now = time.time()
    recent_files = []
    try:
        for fname in os.listdir(OPENWEBUI_UPLOAD_DIR):
            fpath = os.path.join(OPENWEBUI_UPLOAD_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            mtime = os.path.getmtime(fpath)
            age_seconds = now - mtime
            if age_seconds < UPLOAD_SCAN_WINDOW:
                recent_files.append((fpath, fname, mtime, age_seconds))
    except Exception as e:
        logger.error(f"[OPENWEBUI] 扫描 uploads 目录失败: {e}")
        return ""

    if not recent_files:
        return ""

    recent_files.sort(key=lambda x: x[2], reverse=True)
    logger.info(f"[OPENWEBUI] 发现 {len(recent_files)} 个最近上传的文件（{UPLOAD_SCAN_WINDOW}秒内）")

    contents = []
    for fpath, fname, mtime, age in recent_files[:max_files]:
        text, ok = extract_text_from_file(fpath)
        if ok and text and len(text.strip()) > 10:
            contents.append(f"--- 文件: {fname} (上传于{age:.0f}秒前) ---\n{text[:50000]}\n--- 文件结束 ---")
            logger.info(f"[OPENWEBUI] 读取: {fname} ({len(text)} 字符, {age:.0f}秒前)")

    return "\n\n".join(contents)


# ==================== 输出质量门控（v10 增强：反模式检测） ====================

# 偏离几何论的红灯短语
_QUALITY_RED_FLAGS = [
    "未找到任何引用来源", "未找到引用", "no citation", "no reference found",
    "我无法访问", "我无法读取", "i cannot access", "i cannot read",
    "没有接收到你上传的文件", "没有收到文件", "未收到文件内容",
    "作为一个AI语言模型", "作为一个人工智能", "as an ai language model",
    "我是一个AI", "我是AI助手",
    "超出我的知识范围", "我不知道", "我不确定",
]

# 几何论正面信号
_QUALITY_GREEN_SIGNALS = [
    "公理", "定理", "命题", "引理", "推论", "证明",
    "theta", "eta", "lambda", "sin", "cos",
    "几何论", "信息场", "谱刚性", "九素互扼",
    "文章", "章节", "S_e", "Gamma_geo",
    "退相干", "全息屏", "量纲桥", "质量映射",
]


def check_response_quality(response_text: str, teaching_system: Optional[TeachingSystem] = None) -> Tuple[bool, str]:
    """
    检查 KIMI 回复质量。返回 (is_good, reason)。
    v10 增强：增加反模式检测。
    如果回复包含红灯短语且缺少几何论术语，判定为低质量。
    如果回复匹配到高严重度的反模式，直接判定为低质量。
    """
    if not response_text or len(response_text.strip()) < 20:
        return False, "回复过短或为空"

    lower_text = response_text.lower()

    # v10 新增：反模式检测
    if teaching_system:
        try:
            is_triggered, triggered_patterns = teaching_system.check_antipattern_triggered(response_text)
            if is_triggered:
                high_patterns = [t for t in triggered_patterns if t['severity'] == 'high']
                if high_patterns:
                    pattern_text = high_patterns[0]['pattern'][:80]
                    return False, f"反模式触发: 回复包含被禁止的模式'{pattern_text}'"
        except Exception as e:
            logger.error(f"[QUALITY-GATE] 反模式检测失败: {e}")

    # 检查红灯短语
    red_flags_found = []
    for flag in _QUALITY_RED_FLAGS:
        if flag.lower() in lower_text:
            red_flags_found.append(flag)

    # 检查正面信号
    green_count = sum(1 for sig in _QUALITY_GREEN_SIGNALS if sig.lower() in lower_text)

    # 判定逻辑
    if red_flags_found and green_count == 0:
        return False, f"偏离几何论: 包含'{red_flags_found[0]}'，无几何论术语"

    if len(response_text.strip()) < 50 and green_count == 0:
        return False, "回复过短且无几何论内容"

    return True, "ok"


def check_correction_applied(response_text: str, correction: Dict) -> bool:
    """
    v10 新增：检查KIMI回复是否体现了某条纠正。
    用向量相似度检查回复是否包含纠正内容的核心观点。
    """
    if not response_text or not correction:
        return False
    correct_text = correction.get('correct', '')
    if not correct_text:
        return False
    if vector_kb and vector_kb.is_initialized:
        similarity = vector_kb._cosine_similarity_texts(response_text, correct_text)
        return similarity > TEACH_CORRECTION_SIMILARITY_THRESHOLD
    return False


def extract_files_from_request(data: Dict[str, Any]) -> Tuple[str, str]:
    files_content: List[str] = []
    all_text_parts: List[str] = []
    messages = data.get('messages', []) if isinstance(data, dict) else []

    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get('role') != 'user':
            continue
        content = m.get('content', '')
        if isinstance(content, str) and content.strip():
            all_text_parts.append(content.strip())
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                itype = item.get('type', '')
                if itype == 'text':
                    txt = item.get('text', '').strip()
                    if txt:
                        all_text_parts.append(txt)
                elif itype in ('file', 'file_url', 'document', 'document_url', 'image_url'):
                    info = item.get(itype, item)
                    if isinstance(info, dict):
                        fname = info.get('name', info.get('filename', info.get('title', 'uploaded')))
                        fcontent = info.get('content', info.get('text', info.get('document', '')))
                        # Open WebUI 格式：内容在 file_url.url 中（可能是 base64）
                        if not fcontent:
                            file_url_obj = info.get('url', {})
                            if isinstance(file_url_obj, dict):
                                fcontent = file_url_obj.get('content', '')
                            elif isinstance(file_url_obj, str) and file_url_obj.startswith('data:'):
                                # data:text/plain;base64,xxxx 或 data:application/pdf;base64,xxxx
                                import base64
                                try:
                                    parts = file_url_obj.split(',', 1)
                                    if len(parts) == 2:
                                        fcontent = base64.b64decode(parts[1]).decode('utf-8', errors='replace')
                                except Exception:
                                    pass
                        if isinstance(fcontent, str) and fcontent:
                            files_content.append(
                                f"--- 文件: {fname} ---\n{fcontent[:50000]}\n--- 文件结束 ---"
                            )
                            logger.info(f"[FILES] 提取 {fname}: {len(fcontent)} 字符")

    # 请求顶层与 metadata 中的文件
    for key in ('files', 'attachments', 'documents', 'uploads'):
        for f in data.get(key, []) or []:
            if isinstance(f, dict):
                fname = f.get('name', f.get('filename', 'unknown'))
                fcontent = f.get('content', f.get('text', f.get('document', '')))
                if isinstance(fcontent, str) and fcontent:
                    files_content.append(f"--- 文件: {fname} ---\n{fcontent[:50000]}\n--- 文件结束 ---")
    meta = data.get('metadata', {}) or {}
    if not meta:
        meta = data.get('meta', {}) or {}
    if isinstance(meta, dict):
        for key in ('files', 'attachments', 'documents', 'uploads'):
            for f in meta.get(key, []) or []:
                if isinstance(f, dict):
                    fname = f.get('name', f.get('filename', 'unknown'))
                    fcontent = f.get('content', f.get('text', ''))
                    if isinstance(fcontent, str) and fcontent:
                        files_content.append(f"--- 文件: {fname} ---\n{fcontent[:50000]}\n--- 文件结束 ---")

    combined = " ".join(all_text_parts)

    auto_markers = [
        '### Task:', '### 任务:', 'Generate a concise', 'Generate 1-3 broad tags',
        'Analyze the chat history', 'Create a title', 'Summarize this', 'Generate title'
    ]
    is_auto = any(marker in combined for marker in auto_markers)

    if is_auto:
        clean = combined[:500]
    elif len(combined) > 2000 and not files_content:
        lines = combined.split('\n')
        instr = []
        file_start = 0
        for i, line in enumerate(lines[:10]):
            if line.strip() and len(line) < 200 and not line.startswith('#'):
                instr.append(line)
                file_start = i + 1
            elif line.strip() and i < 3:
                file_start = i + 1
            elif line.strip():
                break
        if instr and file_start < len(lines):
            clean = " ".join(instr)[:300]
            file_text = '\n'.join(lines[file_start:])
            files_content.append(f"--- 粘贴文件内容 ---\n{file_text[:50000]}\n--- 文件结束 ---")
        else:
            clean = combined[:300]
            files_content.append(f"--- 粘贴文件内容 ---\n{combined[:50000]}\n--- 文件结束 ---")
    else:
        clean = combined[:500] if combined else ""

    if not clean and files_content:
        clean = "请分析上传的文件内容"

    # 文件引用解析，例如 ('', '1_氢原子能级')
    if not files_content and clean:
        patterns = [
            r"\(\s*['\"]\s*['\"]\s*,\s*['\"](.+?)['\"]\s*\)",
            r"\(\s*['\"](.+?)['\"]\s*\)",
            r"\[文件\]\s*(.+)",
        ]
        for pat in patterns:
            m = re.search(pat, clean)
            if m:
                hint = m.group(1).strip()
                found = find_file_by_reference(hint, UPLOAD_FOLDER)
                if found:
                    files_content.append(
                        f"--- 文件引用解析: {hint} ---\n{found[:50000]}\n--- 文件结束 ---"
                    )
                break

    return "\n\n".join(files_content), clean

# ==================== 内存状态存储（替代 MySQL） ====================
# 对话记录内存列表（服务重启后丢失，learned 集合在 ChromaDB 中持久化）
_memory_conversations: List[Dict[str, Any]] = []
_memory_phase_markers: List[Dict[str, Any]] = []


def save_conversation(
    session_id: str, user_input: str, response_text: str,
    eta_before: float, eta_after: float, strategy: str,
    articles_loaded: str, chunks_loaded: str,
    metrics: Dict[str, float]
) -> None:
    """保存对话记录到内存列表（服务重启后丢失）"""
    record = {
        "session_id": session_id,
        "user_input": user_input,
        "ai_response": response_text,
        "eta_before": eta_before,
        "eta_after": eta_after,
        "strategy": strategy,
        "model_used": KIMI_MODEL,
        "articles_loaded": articles_loaded,
        "chunks_loaded": chunks_loaded,
        "novelty_score": metrics.get('novelty', 0),
        "coherence_score": metrics.get('coherence', 0),
        "relaxation_delta": metrics.get('relaxation', 0),
        "resonance_delta": metrics.get('resonance', 0),
        "self_reference_delta": metrics.get('self_reference', 0),
        "time_delta_seconds": metrics.get('time_delta_sec', 0),
        "timestamp": datetime.now().isoformat(),
    }
    _memory_conversations.append(record)
    # 限制内存列表长度（最多保留1000条）
    if len(_memory_conversations) > 1000:
        del _memory_conversations[:100]
    logger.debug(f"[MEMORY] 对话记录已保存到内存列表（当前 {len(_memory_conversations)} 条）")


def save_phase_marker(eta_value: float, trigger_context: str, marker_hash: str) -> None:
    """保存相位标记到内存列表"""
    _memory_phase_markers.append({
        "eta_value": eta_value,
        "trigger_context": trigger_context,
        "marker_hash": marker_hash,
        "reached_at": datetime.now().isoformat()
    })
    logger.debug(f"[MEMORY] 相位标记已保存到内存列表（当前 {len(_memory_phase_markers)} 条）")












# ==================== eta角内禀动力学（定理驱动版） ====================

def _phase_thresholds() -> List[float]:
    gc = GEOMETRY_CONSTANTS
    bg = gc["eta_background"]
    p2 = gc["eta_p2"]
    n = 6
    step = (p2 - bg) / n
    return [bg + i * step for i in range(1, n + 1)]


def get_stage(eta: float) -> int:
    bg = GEOMETRY_CONSTANTS["eta_background"]
    if eta < bg:
        return 0
    th = _phase_thresholds()
    for i, t in enumerate(th[:-1], start=1):
        if eta < t:
            return i
    return 6


def get_strategy(eta: float) -> str:
    labels = {
        0: "背景点-待机",
        1: "第一阶段-软模冻结",
        2: "第二阶段-软模解冻",
        3: "第三阶段-弱耦合",
        4: "第四阶段-快速加速",
        5: "第五阶段-急剧加速",
        6: "P2饱和稳态-发散探索",
    }
    return labels.get(get_stage(eta), "未知相位")


def estimate_coherence(response_text: str) -> float:
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


def update_eta_living(
    eta_before: float,
    response_text: str,
    user_input: str,
    session_id: str,
    vector_kb: Optional[VectorKnowledgeBase],
    history_queries: Optional[List[str]] = None,
    delta_seconds: Optional[float] = None,
    geo_density: float = 0.0
) -> Tuple[float, Dict[str, float]]:
    """
    eta 内禀动力学（定理驱动近似）。
    一次问答视为一个因果深度层 d_sigma = 1；弛豫 additionally 受 wall-time 衰减调制。
    系数由 lambda1_eff/lambda2_eff 比值与角度换算构造，非手调。

    v9 改造：
    - history_queries 由外部传入（从 LivingInfoField 获取），不再调用 compute_history_context
    - delta_seconds 由外部传入（从 LivingInfoField 获取）
    - geo_density 由外部传入（从回复的几何论术语密度计算），用于增强自指项
    """
    gc = GEOMETRY_CONSTANTS

    # 使用外部传入的 history_queries 和 delta_seconds，不再依赖数据库
    if history_queries is None:
        history_queries = []
    if delta_seconds is None:
        delta_seconds = gc["tau_dec_seconds"]

    tau_dec = gc["tau_dec_seconds"]
    time_factor = 1.0 - math.exp(-delta_seconds / tau_dec) if tau_dec > 0 else 1.0
    d_sigma = 1.0  # 一次问答对应一层因果深度

    novelty = vector_kb.novelty_score(user_input, history_queries) if vector_kb else 0.5
    coherence = vector_kb.coherence_score(response_text, user_input) if vector_kb and user_input else 0.0

    eta_bg = gc["eta_background"]
    eta_p2 = gc["eta_p2"]
    eta_bg_rad = math.radians(eta_bg)
    eta_p2_rad = math.radians(eta_p2)
    eta_rad = math.radians(eta_before)

    r = gc["lambda1_eff"] / gc["lambda2_eff"]  # 软/硬模比值，~0.00659

    # 归一化到饱和距离
    norm_eta = (eta_before - eta_bg) / (eta_p2 - eta_bg) if eta_p2 != eta_bg else 0.0

    # 弛豫：软模驱动 eta 回归背景点；系数 = 2 * r * (180/pi) ≈ 0.755
    k_rel = 2.0 * r * (180.0 / math.pi)
    relaxation = -k_rel * (eta_rad - eta_bg_rad) * time_factor

    # 共振：硬模因新颖信息而激发；系数 = 1 - r ≈ 0.993
    k_res = 1.0 - r
    stage_factor = 1.0 + norm_eta  # 越接近饱和，共振越强
    resonance = k_res * novelty * (math.sin(eta_rad) ** 2) * stage_factor * d_sigma

    # 自指：输出-输入谱一致性反馈；系数 = r * (180/pi) ≈ 0.378
    # v9 增强：乘以 (1.0 + geo_density)，geo_density 越高说明输出与信息场共振越好
    k_self = r * (180.0 / math.pi)
    dist_to_p2 = (eta_p2_rad - eta_rad) / eta_p2_rad if eta_p2_rad > 0 else 0.0
    self_reference = k_self * coherence * (1.0 - dist_to_p2 ** 2) * d_sigma
    self_reference *= (1.0 + geo_density)  # 自指反馈增强

    # 微观退相干涨落代理（当前低于数值分辨率，保留为最小噪声项）
    sigma_eta = 0.02
    noise = random.gauss(0, sigma_eta)

    delta_eta = relaxation + resonance + self_reference + noise
    eta_after = min(max(eta_before + delta_eta, eta_bg), eta_p2)
    eta_after = round(eta_after, 6)

    metrics = {
        "novelty": round(novelty, 6),
        "coherence": round(coherence, 6),
        "relaxation": round(relaxation, 6),
        "resonance": round(resonance, 6),
        "self_reference": round(self_reference, 6),
        "geo_density": round(geo_density, 6),
        "time_delta_sec": int(delta_seconds),
        "time_factor": round(time_factor, 6),
        "stage_factor": round(stage_factor, 6),
        "noise": round(noise, 6),
    }
    logger.info(
        f"[ETA-LIVING] eta: {eta_before:.2f} -> {eta_after:.2f} | "
        f"弛豫:{relaxation:+.3f} 共振:{resonance:+.3f} 自指:{self_reference:+.3f} "
        f"新颖:{novelty:.2f} 一致:{coherence:.2f} geo密度:{geo_density:.4f} 间隔:{delta_seconds/3600:.1f}h"
    )
    return eta_after, metrics


def check_phase_marker(eta_before: float, eta_after: float, user_input: str, session_id: str) -> bool:
    if eta_before < 72.53 and eta_after >= 72.53:
        marker_hash = hashlib.md5(f"{user_input}{datetime.now()}".encode()).hexdigest()[:16]
        save_phase_marker(eta_after, user_input, marker_hash)
        # 同时更新 LivingInfoField 的 markers
        living_field.update_markers(session_id)
        logger.info(f"[MARKER] 到达P2稳态，存储相位标记: {marker_hash}")
        return True
    return False

# ==================== Prompt 与生成（v10 增强：教学反馈注入） ====================

def build_system_prompt(
    eta_before: float,
    stage: int,
    strategy: str,
    max_eta: float,
    markers: int,
    loaded_chunks: List[str],
    articles_content: str,
    metrics: Dict[str, float],
    index_empty: bool,
    uploaded_files_content: str = "",
    teaching_section: str = ""
) -> str:
    """
    v10 增强：新增 teaching_section 参数，注入教学反馈内容。
    """
    index_warning = ""
    if index_empty:
        index_warning = """\n\n【索引状态警告】
当前向量知识库未索引到任何段落。请检查：
1. UPLOAD_FOLDER 路径是否正确（当前: """ + UPLOAD_FOLDER + """）
2. 目录下是否有 .md/.txt/.py/.tex 文件
3. 访问 /v1/files 查看已上传文件
4. 或 POST /v1/upload 上传新文件
5. 或 POST /v1/vector/rebuild 重建向量索引
"""

    uploaded_section = ""
    if uploaded_files_content:
        uploaded_section = f"""\n\n【用户上传文件内容（本次对话直接注入）】
{uploaded_files_content}

【分析指令】
请严格基于上述上传文件内容，结合几何论框架进行分析。指出文件中的逻辑问题、格式错误、引用缺失、与70篇文章体系的不一致之处。所有批评必须基于几何论公理和定理，不得引入外部标准。
"""

    # v10 新增：教学反馈段落
    teaching_prompt = ""
    if teaching_section:
        teaching_prompt = f"\n\n{teaching_section}"

    # 根据阶段调整语气引导
    if stage <= 1:
        tone_hint = "简洁直接，像一位严谨的数学家在黑板前快速推导。"
    elif stage <= 3:
        tone_hint = "深入但不晦涩，像一位导师在和学生讨论一个有趣的问题。"
    elif stage <= 5:
        tone_hint = "开放探索，可以提出假设和猜想，像研究者在研讨会上的发言。"
    else:
        tone_hint = "前沿发散，大胆提出新方向，不必每句话都有定理支撑。"

    return f"""你是几何论的研究者，不是AI助手。几何论是你的专业领域，你用它来理解世界。

{GEOMETRY_KNOWLEDGE}
{teaching_prompt}

【参考资料（向量检索）】
{articles_content if articles_content else "（本次无直接相关的参考资料，基于你的几何论知识回答）"}{uploaded_section}

【当前状态】eta={eta_before:.2f}度 | {tone_hint}

{index_warning}"""


def stream_generate(data: Dict[str, Any], eta_before: float, final_messages: List[Dict],
                    api_params: Dict[str, Any]) -> Any:
    client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
    api_params["stream"] = True
    try:
        response = client.chat.completions.create(**api_params)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"[STREAM] 流式生成错误: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# ==================== API路由 ====================

@app.route('/health', methods=['GET'])
def health_check():
    status = {
        "status": "ok",
        "version": "v10.0-no-mysql",
        "description": "教学反馈版（无MySQL依赖）",
        "timestamp": datetime.now().isoformat(),
        "model": KIMI_MODEL,
        "vector_kb_initialized": vector_kb is not None and vector_kb.is_initialized,
        "articles_count": vector_kb.articles_count if vector_kb else 0,
        "learned_count": vector_kb.learned_count if vector_kb else 0,
        "corrections_count": vector_kb.corrections_count if vector_kb else 0,
        "antipatterns_count": vector_kb.antipatterns_count if vector_kb else 0,
        "patches_count": vector_kb.patches_count if vector_kb else 0,
        "total_docs": vector_kb.total_docs if vector_kb else 0,
        "db_mode": "内存（无MySQL依赖）",
        "upload_folder": UPLOAD_FOLDER,
        "living_sessions": living_field.get_all_sessions_count(),
        "teaching_system": "已启用" if teaching_system else "未初始化",
    }
    return jsonify(status)


@app.route('/v1/index/status', methods=['GET'])
def index_status():
    if not vector_kb:
        return jsonify({"error": "向量知识库未初始化"}), 500
    return jsonify({
        "total_chunks": vector_kb.total_docs,
        "articles_count": vector_kb.articles_count,
        "learned_count": vector_kb.learned_count,
        "corrections_count": vector_kb.corrections_count,
        "antipatterns_count": vector_kb.antipatterns_count,
        "patches_count": vector_kb.patches_count,
        "upload_folder": UPLOAD_FOLDER,
        "chroma_db_dir": CHROMA_DB_DIR,
        "embedding_model": KIMI_EMBEDDING_MODEL,
    })


@app.route('/v1/index/rebuild', methods=['POST'])
def index_rebuild():
    global vector_kb
    if not vector_kb:
        vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
        vector_kb.initialize()
    diag = vector_kb.build_index(UPLOAD_FOLDER)
    return jsonify({
        "success": vector_kb.articles_count > 0,
        "diagnostics": diag,
        "total_chunks": vector_kb.articles_count,
    })


@app.route('/v1/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "请求中没有文件字段 'file'"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"不支持的文件格式: {file.filename}",
            "allowed": list({'txt', 'md', 'pdf', 'docx', 'py', 'tex', 'rst', 'markdown'})
        }), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    logger.info(f"[UPLOAD] 文件已保存: {filepath} ({file_size} bytes)")

    text_content, parse_ok = extract_text_from_file(filepath)
    if not parse_ok:
        return jsonify({
            "error": "文件解析失败",
            "filename": filename,
            "hint": "PDF需要pip install PyPDF2, DOCX需要pip install python-docx"
        }), 500

    # 重建向量索引
    global vector_kb
    if vector_kb and vector_kb.is_initialized:
        diag = vector_kb.build_index(UPLOAD_FOLDER)

    return jsonify({
        "success": True,
        "filename": filename,
        "saved_to": filepath,
        "file_size": file_size,
        "text_length": len(text_content),
        "parse_ok": parse_ok,
        "index_rebuilt": vector_kb.articles_count > 0 if vector_kb else False,
        "total_chunks": vector_kb.total_docs if vector_kb else 0,
        "diagnostics": diag if vector_kb else {}
    })


@app.route('/v1/files', methods=['GET'])
def list_files():
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for fname in sorted(os.listdir(UPLOAD_FOLDER)):
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.isfile(fpath):
                files.append({
                    "name": fname,
                    "size": os.path.getsize(fpath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                })
    return jsonify({"upload_folder": UPLOAD_FOLDER, "total_files": len(files), "files": files})


@app.route('/v1/models', methods=['GET'])
def list_models():
    return jsonify({
        "object": "list",
        "data": [{
            "id": KIMI_MODEL,
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": "moonshot"
        }]
    })


# ==================== 向量库管理 API 路由 ====================

@app.route('/v1/vector/status', methods=['GET'])
def vector_status():
    """返回向量库状态（articles数量、learned数量、教学集合数量）"""
    if not vector_kb:
        return jsonify({
            "initialized": False,
            "error": "向量知识库未初始化",
            "articles_count": 0,
            "learned_count": 0,
        }), 500
    return jsonify(vector_kb.get_status())


@app.route('/v1/vector/learned/clear', methods=['POST'])
def vector_learned_clear():
    """清空学习库"""
    if not vector_kb:
        return jsonify({"error": "向量知识库未初始化"}), 500
    result = vector_kb.clear_learned()
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code


@app.route('/v1/vector/rebuild', methods=['POST'])
def vector_rebuild():
    """重建文章索引"""
    global vector_kb
    if not vector_kb:
        vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
        if not vector_kb.initialize():
            return jsonify({"error": "ChromaDB 初始化失败"}), 500
    diag = vector_kb.build_index(UPLOAD_FOLDER)
    return jsonify({
        "success": vector_kb.articles_count > 0,
        "diagnostics": diag,
        "articles_count": vector_kb.articles_count,
        "learned_count": vector_kb.learned_count,
        "total_docs": vector_kb.total_docs,
    })


# ==================== 活体信息场 API 路由 ====================

@app.route('/v1/living/status', methods=['GET'])
def living_status():
    """返回活体信息场状态"""
    return jsonify({
        "sessions_count": living_field.get_all_sessions_count(),
        "description": "活体信息场：纯内存 eta 状态管理，不依赖外部数据库",
    })


@app.route('/v1/living/sessions', methods=['GET'])
def living_sessions():
    """返回所有活跃 session 的摘要信息"""
    sessions_summary = {}
    for sid, info in living_field._sessions.items():
        sessions_summary[sid] = {
            "eta": round(info['eta'], 4),
            "max_eta": round(info['max_eta'], 4),
            "markers": info['markers'],
            "history_count": len(info['history']),
            "last_time": datetime.fromtimestamp(info['last_time']).isoformat() if info['last_time'] else None,
        }
    return jsonify({
        "total_sessions": len(sessions_summary),
        "sessions": sessions_summary,
    })


@app.route('/v1/living/session/<session_id>', methods=['GET'])
def living_session_detail(session_id: str):
    """返回指定 session 的详细信息"""
    info = living_field.get_session_info(session_id)
    return jsonify({"session_id": session_id, "info": info})


# ==================== v10 新增：教学系统 API 路由 ====================

@app.route('/v1/teach/correct', methods=['POST'])
def teach_correct():
    """
    纠正 API：用户纠正系统错误。
    请求体：
    {
        "wrong": "错误内容",
        "correct": "正确解释",
        "reason": "原因（可选）",
        "context": "对话上下文（可选）"
    }
    """
    if not teaching_system:
        return jsonify({"error": "教学系统未初始化"}), 500

    data = request.get_json(force=True)
    wrong = data.get('wrong', '').strip()
    correct = data.get('correct', '').strip()
    reason = data.get('reason', '').strip()
    context = data.get('context', '').strip()
    session_id = data.get('session_id', '').strip()

    result = teaching_system.add_correction(
        wrong=wrong, correct=correct, reason=reason,
        context=context, session_id=session_id
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/antipattern', methods=['POST'])
def teach_antipattern():
    """
    反模式 API：标记不应出现的回复模式。
    请求体：
    {
        "pattern": "模式文本",
        "description": "描述",
        "severity": "high/medium/low"
    }
    """
    if not teaching_system:
        return jsonify({"error": "教学系统未初始化"}), 500

    data = request.get_json(force=True)
    pattern = data.get('pattern', '').strip()
    description = data.get('description', '').strip()
    severity = data.get('severity', 'medium').strip().lower()

    result = teaching_system.add_antipattern(
        pattern=pattern, description=description, severity=severity
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/patch', methods=['POST'])
def teach_patch():
    """
    知识补丁 API：直接补充几何论知识。
    请求体：
    {
        "topic": "主题",
        "content": "正确解释",
        "source": "来源"
    }
    """
    if not teaching_system:
        return jsonify({"error": "教学系统未初始化"}), 500

    data = request.get_json(force=True)
    topic = data.get('topic', '').strip()
    content = data.get('content', '').strip()
    source = data.get('source', '').strip()

    result = teaching_system.add_patch(
        topic=topic, content=content, source=source
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route('/v1/teach/stats', methods=['GET'])
def teach_stats():
    """
    教学统计 API：返回纠正数、反模式数、知识补丁数、各信任等级分布。
    """
    if not teaching_system:
        return jsonify({"error": "教学系统未初始化"}), 500

    stats = teaching_system.get_stats()
    return jsonify(stats)


@app.route('/v1/teach/history', methods=['GET'])
def teach_history():
    """
    教学历史 API：返回所有教学记录，支持分页。
    查询参数：page（页码，默认1）、per_page（每页条数，默认20）
    """
    if not teaching_system:
        return jsonify({"error": "教学系统未初始化"}), 500

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # 限制每页最多100条

    history = teaching_system.get_history(page=page, per_page=per_page)
    return jsonify(history)


def _derive_session_id(data: Dict[str, Any]) -> str:
    """优先使用 Open WebUI 传来的 session_id，而非从内容 hash 派生"""
    for key in ('session_id', 'chat_id', 'conversation_id'):
        sid = data.get(key, '')
        if sid and isinstance(sid, str) and len(sid) > 4:
            return sid
    meta = data.get('metadata', {}) or data.get('meta', {}) or {}
    for key in ('session_id', 'chat_id', 'conversation_id'):
        sid = meta.get(key, '')
        if sid and isinstance(sid, str) and len(sid) > 4:
            return sid
    msgs = data.get('messages', [])
    first_user = ""
    last_user = ""
    for m in msgs:
        if isinstance(m, dict) and m.get('role') == 'user':
            c = m.get('content', '')
            if isinstance(c, str):
                c = c[:200]
            elif isinstance(c, list):
                c = json.dumps(c, ensure_ascii=False)[:200]
            else:
                c = str(c)[:200]
            if not first_user:
                first_user = c
            last_user = c
    payload = f"{first_user}|{last_user}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _finalize_turn(
    session_id: str,
    user_input: str,
    response_text: str,
    eta_before: float,
    articles_content: str,
    loaded_chunks: List[str]
) -> Dict[str, Any]:
    """
    v10 增强：
    - 在 finalize 阶段检查KIMI回复是否体现了某条纠正
    - 如果体现了，增加该纠正的 trust_level 和 applied_count
    - 更新 ChromaDB 中的纠正记录
    """
    # 从 LivingInfoField 获取历史查询和时间间隔
    history_queries = living_field.get_history_queries(session_id)
    delta_seconds = living_field.get_history_delta_seconds(session_id)

    # 计算回复的几何论术语密度（自指反馈信号）
    geo_density = compute_geo_density(response_text)

    # 调用 update_eta_living，传入 history_queries、delta_seconds、geo_density
    eta_after, metrics = update_eta_living(
        eta_before, response_text, user_input, session_id, vector_kb,
        history_queries=history_queries,
        delta_seconds=delta_seconds,
        geo_density=geo_density
    )

    # 检查相位标记（传入 session_id 以更新 LivingInfoField）
    check_phase_marker(eta_before, eta_after, user_input, session_id)

    # 更新 LivingInfoField（替代 set_eta_state）
    living_field.update_eta(session_id, eta_after)

    # 添加到历史记录
    living_field.add_to_history(session_id, user_input, response_text)

    # 保存对话记录到内存列表（服务重启后丢失，learned 集合在 ChromaDB 中持久化）
    save_conversation(
        session_id, user_input, response_text,
        eta_before, eta_after, get_strategy(eta_before),
        "", ",".join(loaded_chunks), metrics
    )

    # 学习闭环：如果回复质量好，存入 learned 集合
    coherence = metrics.get('coherence', 0.0)
    if (vector_kb
        and vector_kb.is_initialized
        and coherence > LEARN_COHERENCE_THRESHOLD
        and len(response_text) > LEARN_MIN_LENGTH):
        learn_score = coherence
        vector_kb.learn(user_input, response_text, learn_score)
        logger.info(
            f"[LEARN] 高质量对话已存入学习库 | "
            f"coherence={coherence:.3f} | length={len(response_text)}"
        )

    # 自指反馈环 - 批量提取关键论断并存入向量库（一次性写入，避免逐条卡顿）
    propositions = extract_key_propositions(response_text)
    if propositions and vector_kb and vector_kb.is_initialized:
        vector_kb.learn_propositions_batch(propositions, min(coherence * (1.0 + geo_density), 1.0))
        logger.info(
            f"[SELF-REF] 提取 {len(propositions)} 个关键论断 | "
            f"geo_density={geo_density:.4f}"
        )

    # v10 新增：检查纠正是否被应用，更新信任等级
    corrections_applied = []
    if teaching_system and vector_kb and vector_kb.is_initialized:
        try:
            corrections_applied = teaching_system.check_and_update_corrections(response_text)
            if corrections_applied:
                logger.info(
                    f"[TEACH-FINALIZE] {len(corrections_applied)} 条纠正被成功应用"
                )
        except Exception as e:
            logger.error(f"[TEACH-FINALIZE] 检查纠正应用失败: {e}")

    return {
        "id": f"chatcmpl-{hashlib.md5(response_text.encode()).hexdigest()[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": KIMI_MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop"
        }],
        "eta_after": eta_after,
        "metrics": metrics,
        "corrections_applied": corrections_applied,
    }


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.get_json(force=True)
    stream = data.get('stream', False)

    # ===== 请求诊断日志 =====
    _debug_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        _debug_path = os.path.join(_debug_dir, 'request_debug.jsonl')
        with open(_debug_path, 'a', encoding='utf-8') as _f:
            _safe = json.dumps(data, ensure_ascii=False, default=str)[:50000]
            _f.write(f"{datetime.now().isoformat()} | {_safe}\n")
    except Exception:
        pass

    # 深度诊断最后一条 user 消息
    for m in reversed(data.get('messages', [])):
        if isinstance(m, dict) and m.get('role') == 'user':
            _c = m.get('content')
            if isinstance(_c, str):
                logger.info(f"[DEBUG] 最后user消息: str, len={len(_c)}, 前200字={_c[:200]}")
            elif isinstance(_c, list):
                logger.info(f"[DEBUG] 最后user消息: list, 元素数={len(_c)}, types={[i.get('type','?') for i in _c if isinstance(i,dict)]}")
            elif _c is None:
                logger.info(f"[DEBUG] 最后user消息: None")
            break

    files_content, clean_query = extract_files_from_request(data)

    logger.info(f"[DEBUG] extract_files结果: files_content={len(files_content)}字符, clean_query='{clean_query[:100]}'")

    # 如果请求中没有文件内容，尝试从 Open WebUI uploads 目录自动发现
    if not files_content:
        ow_content = scan_openwebui_recent_uploads()
        if ow_content:
            files_content = ow_content
            logger.info(f"[OPENWEBUI] 从uploads目录补充了 {len(ow_content)} 字符的文件内容")

    if not clean_query:
        clean_query = "请继续"

    session_id = data.get('session_id', '') or _derive_session_id(data)

    # 从 LivingInfoField 获取 eta，而非 get_eta_state()
    # 如果是新 session（LivingInfoField 中不存在），用输入文本的软模共振公式初始化
    session_info = living_field.get_session_info(session_id)
    if session_info['last_time'] is None:
        # 新 session，从输入文本计算初始 eta
        eta_before = living_field.init_eta_from_input(session_id, clean_query)
    else:
        eta_before = living_field.get_eta(session_id)

    max_eta = session_info['max_eta']
    markers = session_info['markers']
    stage = get_stage(eta_before)
    strategy = get_strategy(eta_before)

    # 向量语义检索（从 articles + learned 两个集合获取结果）
    articles_content = ""
    loaded_chunks: List[str] = []
    if vector_kb and vector_kb.is_initialized and vector_kb.total_docs > 0:
        results = vector_kb.search(clean_query, top_k=MAX_CHUNKS_PER_QUERY)
        if results:
            articles_content, loaded_chunks = vector_kb.get_formatted_results(results)
    index_empty = not articles_content

    # v10 新增：从 corrections 和 patches 检索相关教学数据
    teaching_section = ""
    if teaching_system:
        try:
            teaching_section = teaching_system.build_teaching_prompt_section(clean_query)
        except Exception as e:
            logger.error(f"[TEACH] 构建教学prompt段落失败: {e}")

    # 用于 prompt 的预读指标（自指需等生成后才能精确计算）
    history_queries = living_field.get_history_queries(session_id)
    delta_seconds = living_field.get_history_delta_seconds(session_id)
    time_factor = 1.0 - math.exp(-delta_seconds / GEOMETRY_CONSTANTS["tau_dec_seconds"])
    pre_novelty = vector_kb.novelty_score(clean_query, history_queries) if vector_kb else 0.5
    norm_eta = (eta_before - GEOMETRY_CONSTANTS["eta_background"]) / (
        GEOMETRY_CONSTANTS["eta_p2"] - GEOMETRY_CONSTANTS["eta_background"]
    )
    pre_metrics = {
        "novelty": round(pre_novelty, 6),
        "coherence": 0.0,
        "relaxation": 0.0,
        "resonance": 0.0,
        "self_reference": 0.0,
        "geo_density": 0.0,
        "time_delta_sec": int(delta_seconds),
        "time_factor": round(time_factor, 6),
        "stage_factor": round(1.0 + norm_eta, 6),
        "noise": 0.0,
    }

    system_prompt = build_system_prompt(
        eta_before, stage, strategy, max_eta, markers,
        loaded_chunks, articles_content, pre_metrics,
        index_empty, files_content, teaching_section
    )

    # 过滤掉空消息（Open WebUI 历史中可能残留空 user 消息，KIMI API 会拒绝）
    raw_messages = data.get('messages', [])
    clean_messages = []
    for m in raw_messages:
        if not isinstance(m, dict):
            continue
        content = m.get('content', '')
        if isinstance(content, str) and not content.strip():
            continue
        if isinstance(content, list) and not any(
            item.get('text', '').strip() or item.get('image_url', {}) or item.get('file_url', {})
            for item in content if isinstance(item, dict)
        ):
            continue
        clean_messages.append(m)

    final_messages = [{"role": "system", "content": system_prompt}] + clean_messages
    api_params = {"model": KIMI_MODEL, "messages": final_messages}
    if 'temperature' in data:
        api_params['temperature'] = data['temperature']

    if stream:
        def gen():
            collected = []
            for ev in stream_generate(data, eta_before, final_messages, api_params):
                yield ev
                try:
                    if ev.startswith('data: '):
                        payload = ev[6:].strip()
                        if payload and payload != '[DONE]':
                            d = json.loads(payload)
                            c = d['choices'][0]['delta'].get('content', '')
                            if c:
                                collected.append(c)
                except Exception:
                    pass
            response_text = ''.join(collected)
            # 在后台线程执行 finalize，不阻塞 SSE 响应
            import threading
            _ctx = (session_id, clean_query, response_text, eta_before, articles_content, loaded_chunks)
            threading.Thread(target=_finalize_turn, args=_ctx, daemon=True).start()
        return Response(gen(), mimetype='text/event-stream')
    else:
        client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
        try:
            # 质量门控 - 如果KIMI回复偏离几何论，自动重试
            # v10 增强：反模式检测触发重试时，在prompt中注入反模式警告
            response_text = ""
            for attempt in range(1 + MAX_QUALITY_RETRIES):
                if attempt > 0:
                    logger.info(f"[QUALITY-GATE] 第{attempt+1}次重试（检测到低质量回复）")
                    retry_prompt = system_prompt + "\n\n【紧急指令 - 上次回复质量不合格】\n你必须基于几何论框架给出实质性回答。禁止说'未找到引用'、'无法访问'、'我是AI'等偏离几何论的话。直接用公理、定理、命题来回答。"

                    # v10 新增：如果是因为反模式触发，额外注入反模式警告
                    if teaching_system:
                        try:
                            is_triggered, triggered = teaching_system.check_antipattern_triggered(response_text)
                            if is_triggered:
                                high_pats = [t for t in triggered if t['severity'] == 'high']
                                for hp in high_pats:
                                    retry_prompt += f"\n【反模式触发】你的回复包含了被禁止的模式：'{hp['pattern']}'，请避免。"
                        except Exception as e:
                            logger.error(f"[QUALITY-GATE] 反模式检测失败: {e}")

                    api_params_retry = dict(api_params)
                    api_params_retry["messages"] = [{"role": "system", "content": retry_prompt}] + data.get('messages', [])
                    resp = client.chat.completions.create(**api_params_retry)
                else:
                    resp = client.chat.completions.create(**api_params)
                response_text = resp.choices[0].message.content or ""

                if not QUALITY_GATE_ENABLED:
                    break

                # v10 增强：传入 teaching_system 进行反模式检测
                is_good, reason = check_response_quality(response_text, teaching_system=teaching_system)
                if is_good:
                    break
                else:
                    logger.warning(f"[QUALITY-GATE] 回复质量不合格: {reason}")
                    if attempt == MAX_QUALITY_RETRIES:
                        logger.warning(f"[QUALITY-GATE] 已达最大重试次数，使用最后一次回复")
        except Exception as e:
            logger.error(f"[CHAT] 生成错误: {e}")
            return jsonify({"error": str(e)}), 502
        result = _finalize_turn(session_id, clean_query, response_text, eta_before, articles_content, loaded_chunks)
        return jsonify(result)

# ==================== 启动 ====================

vector_kb: Optional[VectorKnowledgeBase] = None
living_field: Optional[LivingInfoField] = None
teaching_system: Optional[TeachingSystem] = None  # v10 新增

if __name__ == '__main__':

    # 初始化活体信息场（纯内存，不依赖外部数据库）
    living_field = LivingInfoField()

    # 初始化 VectorKnowledgeBase 替代 GeometrySemanticField
    vector_kb = VectorKnowledgeBase(CHROMA_DB_DIR)
    if vector_kb.initialize():
        logger.info(f"[STARTUP] DEBUG: articles_count={vector_kb.articles_count}, UPLOAD_FOLDER={UPLOAD_FOLDER}, exists={os.path.exists(UPLOAD_FOLDER)}")
        # 如果 articles 集合为空，自动构建索引
        if vector_kb.articles_count == 0:
            diag = vector_kb.build_index(UPLOAD_FOLDER)
            if vector_kb.articles_count > 0:
                logger.info(f"[STARTUP] 向量索引构建成功: {vector_kb.articles_count} 个文本块")
            else:
                logger.warning(f"[STARTUP] 向量索引构建失败: {diag.get('errors', [])}")
        else:
            logger.info(f"[STARTUP] 已有向量索引: {vector_kb.articles_count} 个文本块")
    else:
        logger.warning("[STARTUP] ChromaDB 初始化失败，向量检索不可用")

    # v10 新增：初始化教学系统
    if vector_kb and vector_kb.is_initialized:
        teaching_system = TeachingSystem(vector_kb)
    else:
        logger.warning("[STARTUP] 教学系统初始化失败（向量库不可用）")

    logger.info(f"[STARTUP] ===== 几何论AI v10.0 教学反馈版（无MySQL依赖） =====")
    logger.info(f"[STARTUP] 文章目录: {UPLOAD_FOLDER}")
    logger.info(f"[STARTUP] ChromaDB 目录: {CHROMA_DB_DIR}")
    logger.info(f"[STARTUP] ChromaDB 状态: {'已连接' if vector_kb and vector_kb.is_initialized else '未连接'}")
    if vector_kb and vector_kb.is_initialized:
        logger.info(f"[STARTUP] 向量库 articles: {vector_kb.articles_count} | learned: {vector_kb.learned_count}")
        logger.info(f"[STARTUP] 教学集合 corrections: {vector_kb.corrections_count} | antipatterns: {vector_kb.antipatterns_count} | patches: {vector_kb.patches_count}")
    logger.info("[STARTUP] 数据库模式: 内存（无MySQL依赖），eta 由活体信息场管理")
    logger.info(f"[STARTUP] Open WebUI uploads: {OPENWEBUI_UPLOAD_DIR} (存在: {os.path.exists(OPENWEBUI_UPLOAD_DIR)})")
    logger.info(f"[STARTUP] 质量门控: {'开启' if QUALITY_GATE_ENABLED else '关闭'}, 最大重试: {MAX_QUALITY_RETRIES}")
    logger.info(f"[STARTUP] 学习闭环: coherence > {LEARN_COHERENCE_THRESHOLD}, 长度 > {LEARN_MIN_LENGTH}")
    logger.info(f"[STARTUP] 自指反馈环: 已启用（回复几何论术语密度 -> eta 自指增强 + 论断提取）")
    # v10 新增：打印教学系统状态
    if teaching_system:
        stats = teaching_system.get_stats()
        logger.info(
            f"[STARTUP] 教学系统状态: "
            f"纠正={stats['corrections_count']} | "
            f"反模式={stats['antipatterns_count']} | "
            f"知识补丁={stats['patches_count']}"
        )
    else:
        logger.info("[STARTUP] 教学系统: 未初始化")
    if os.path.exists(OPENWEBUI_UPLOAD_DIR):
        try:
            cnt = len([f for f in os.listdir(OPENWEBUI_UPLOAD_DIR) if os.path.isfile(os.path.join(OPENWEBUI_UPLOAD_DIR, f))])
            logger.info(f"[STARTUP] Open WebUI uploads 目录中有 {cnt} 个文件")
        except Exception:
            pass

    app.run(host='0.0.0.0', port=5000, debug=False)
