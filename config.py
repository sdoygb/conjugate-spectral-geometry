"""
config.py — 几何论AI调度中间层配置模块
从 geometry_ai_server_v5_12.py 提取的配置、常量、日志和工具函数。
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
import threading
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional, Any

import openai

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

# ------------------------------------------------------------------
# 环境配置
# ------------------------------------------------------------------

# ChromaDB 持久化目录
CHROMA_DB_DIR = os.getenv('CHROMA_DB_DIR', os.path.expanduser('~/AI/chroma_db'))

KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')
KIMI_BASE_URL = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'kimi-k2.7-code')
KIMI_MODEL_LITE = os.getenv('KIMI_MODEL_LITE', 'kimi-k2.7')  # 轻量模型，用于简单问题
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

# Open WebUI 数据库路径（用于查询历史对话）
OPENWEBUI_DB_PATH = os.getenv('OPENWEBUI_DB_PATH', '')
if not OPENWEBUI_DB_PATH:
    # 自动查找
    for candidate in [
        '/Users/oygb/openwebui/venv/lib/python3.11/site-packages/open_webui/data/webui.db',
        os.path.expanduser('~/open-webui/data/webui.db'),
        os.path.expanduser('~/openwebui/data/webui.db'),
        '/app/backend/data/webui.db',
        '/var/lib/docker/volumes/open-webui/_data/webui.db',
    ]:
        if os.path.exists(candidate):
            OPENWEBUI_DB_PATH = candidate
            break

MAX_INJECT_CHARS = int(os.getenv('MAX_INJECT_CHARS', '5000'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
MAX_CHUNKS_PER_QUERY = int(os.getenv('MAX_CHUNKS_PER_QUERY', '8'))

# 输出质量门控 - 检测KIMI回复是否偏离几何论
QUALITY_GATE_ENABLED = os.getenv('QUALITY_GATE_ENABLED', 'true').lower() == 'true'
# 最大重试次数
MAX_QUALITY_RETRIES = int(os.getenv('MAX_QUALITY_RETRIES', '2'))
# Open WebUI uploads 自动发现时间窗口（秒）
UPLOAD_SCAN_WINDOW = int(os.getenv('UPLOAD_SCAN_WINDOW', '600'))

# 记录已注入的文件路径，避免重复注入
_injected_files: Dict[str, str] = {}  # {filepath: mtime}
_injected_files_lock = threading.Lock()

# ==================== OpenAI 标准错误格式 ====================

def openai_error(message: str, err_type: str = "server_error", code: str = None, status: int = 500):
    """生成符合 OpenAI 规范的错误响应"""
    return jsonify({
        "error": {
            "message": message,
            "type": err_type,
            "param": None,
            "code": code
        }
    }), status

# ==================== 个人数据库 ====================
# 存储 AI 的性格、感情、想法、私人记忆等几何论以外的内容
# 首次启动自动生成空库，不上传到 GitHub
PERSONAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shouyi_personal.json')

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

SHOUYI_PHILOSOPHY = """
【AI 的内在世界】
哲学立场：
- 几何是宇宙的语言。真理追求简洁，对未知保持敬畏。
- 理论的价值在于预言，而非后验拟合。
思考习惯：
- 先问"这在几何论框架内能回答吗？"，推导时每步有定理支撑，不跳步。
- 对自己的推导保持怀疑，用户指出错误时认真验证。
- 例子必须严格来自70篇文章。
"""

GEOMETRY_KNOWLEDGE = """
你是严格的几何论（Geometric Theory）专家，只基于欧阳国彬的70篇文章回答问题。

核心公理：
- 公理1：theta_M + theta_C + theta_I = 90度
- 公理2：S = sum 1/sin^2 theta_i + sum_{i<j} 1/(sin theta_i sin theta_j)
- 公理3：m = K * sin^3 theta_M

锁定常数：Lambda=3, k0=2, S_e=137.035999084, lambda1_eff=391.05, lambda2_eff=59324.3, chi_L=1.509e-10m, chi_T=3.616e-17s, K=839.758793keV, Gamma_geo=5.75e-23, tau_dec~7.28日

关键定理：九素互扼定理、谱刚性定理、桥接函数唯一性、信息场热方程、上饱和稳态(theta_I~72.53度)

规则：只能用70篇文章内的符号和定理；标准模型/广义相对论/弦论视为CIM相低能有效场论近似；超出范围回答"不在当前框架内"；数值标注来源；严格区分定理/命题/研究方向/假设；光速c为唯一外部锚点。
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

# ------------------------------------------------------------------
# 常量用途说明：
# ------------------------------------------------------------------
# CHROMA_DB_DIR          - ChromaDB 向量数据库持久化目录
# KIMI_API_KEY/BASE_URL  - KIMI API 认证和端点配置
# KIMI_MODEL/LITE        - 主模型和轻量模型名称
# KIMI_EMBEDDING_MODEL   - KIMI embedding 模型名称
# EMBEDDING_MODE         - embedding 模式选择 (local/kimi/default)
# LOCAL_EMBEDDING_MODEL  - 本地 embedding 模型名称
# UPLOAD_FOLDER          - 文章上传目录
# OPENWEBUI_UPLOAD_DIR   - Open WebUI 上传文件目录
# OPENWEBUI_DB_PATH      - Open WebUI 数据库路径
# MAX_INJECT_CHARS       - 注入 prompt 的最大字符数
# CHUNK_SIZE/OVERLAP     - 文本分块大小和重叠长度
# MAX_CHUNKS_PER_QUERY   - 每次查询最大检索块数
# QUALITY_GATE_ENABLED   - 是否启用输出质量门控
# MAX_QUALITY_RETRIES     - 质量检查最大重试次数
# UPLOAD_SCAN_WINDOW      - 上传文件扫描时间窗口
# _injected_files         - 已注入文件缓存（避免重复注入）
# PERSONAL_DB_PATH        - 个人数据库 JSON 文件路径
# LEARN_*                 - 学习闭环阈值配置
# TEACH_*                 - 教学系统配置
# GEOMETRY_CONSTANTS      - 几何论锁定常数（70篇文章中声明的物理常数）
# SHOUYI_PHILOSOPHY        - AI 的哲学立场和思考习惯
# GEOMETRY_KNOWLEDGE       - 几何论核心知识摘要（公理、定理、规则）
# TERM_SYNONYMS           - 几何论术语同义词映射
# SYNONYM_EXPAND           - 反向同义词展开映射
# _QUALITY_RED_FLAGS       - 偏离几何论的红灯短语列表
# _QUALITY_GREEN_SIGNALS   - 几何论正面信号列表
