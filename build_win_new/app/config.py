"""
config.py — 几何论AI调度中间层配置模块
从 geometry_ai_server_v5_12.py 提取的配置、常量、日志和工具函数。
"""
import os
import sys

# 加载 .env 文件到环境变量
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)
except ImportError:
    pass  # python-dotenv 未安装，跳过
import re
import logging
import logging.handlers
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# 项目根目录（所有相对路径基于此）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
from typing import List, Tuple, Dict, Optional, Any

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
_LOG_DIR = os.getenv('LOG_DIR', os.path.join(PROJECT_ROOT, 'logs'))
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 按天轮转，保留最近 7 天
        logging.handlers.TimedRotatingFileHandler(
            os.path.join(_LOG_DIR, 'geometry_ai.log'),
            when='midnight', backupCount=7, encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 环境配置
# ------------------------------------------------------------------

# ChromaDB 持久化目录
CHROMA_DB_DIR = os.getenv('CHROMA_DB_DIR', os.path.join(PROJECT_ROOT, 'chroma_db'))

GAI_API_KEY = os.getenv('GAI_API_KEY', '')
GAI_BASE_URL = os.getenv('GAI_BASE_URL', 'https://api.deepseek.com/v1')
GAI_MODEL = os.getenv('GAI_MODEL', 'deepseek-v4-pro')
GAI_MODEL_LITE = os.getenv('GAI_MODEL_LITE', 'deepseek-v4-flash')  # 轻量模型，用于简单问题
GAI_MODEL_VISION = os.getenv('GAI_MODEL_VISION', 'deepseek-v4-flash')  # 视觉模型，用于图片输入
GAI_EMBEDDING_MODEL = os.getenv('GAI_EMBEDDING_MODEL', 'deepseek-v4-flash')

# 额外模型（逗号分隔，会暴露给 Open WebUI）
# 例如: EXTRA_MODELS=deepseek-v4-lite,deepseek-coder,claude-3-haiku
EXTRA_MODELS = [m.strip() for m in os.getenv('EXTRA_MODELS', '').split(',') if m.strip()]

# ==================== 多模型提供商路由 ====================
# MODEL_PROVIDERS: 根据 model 名称前缀自动选择 API 提供商
# 格式: "模型名前缀": {"base_url": "...", "api_key": "环境变量名或直接key"}
# 匹配规则: 请求中的 model 字段包含某个 key 的前缀，就路由到对应提供商
# 如果没有任何匹配，使用默认的 GAI_BASE_URL / GAI_API_KEY

def _build_model_providers():
    """从环境变量构建多提供商路由表"""
    providers = {}
    # 环境变量格式: PROVIDER_gpt=BASE_URL,API_KEY (用逗号分隔base_url和key)
    # 例如: PROVIDER_gpt=https://oa.api2d.net/v1,fk245651-xxx
    #       PROVIDER_claude=https://api.anthropic.com,sk-ant-xxx
    prefix = 'PROVIDER_'
    for key, val in os.environ.items():
        if key.startswith(prefix):
            model_prefix = key[len(prefix):].lower()  # 如 "gpt", "claude", "deepseek"
            parts = val.split(',', 1)
            if len(parts) == 2:
                base_url = parts[0].strip()
                api_key = parts[1].strip()
                providers[model_prefix] = {"base_url": base_url, "api_key": api_key}
            elif len(parts) == 1:
                # 只提供了 base_url，key 用默认的
                providers[model_prefix] = {"base_url": parts[0].strip(), "api_key": ""}
    return providers

MODEL_PROVIDERS = _build_model_providers()

def get_provider_for_model(model_name: str) -> tuple:
    """
    根据 model 名称返回对应的 (base_url, api_key)。
    如果没有匹配的提供商，返回默认的 (GAI_BASE_URL, GAI_API_KEY)。
    """
    model_lower = model_name.lower()
    for prefix, config in MODEL_PROVIDERS.items():
        if prefix and model_lower.startswith(prefix):
            base_url = config["base_url"]
            api_key = config["api_key"] or GAI_API_KEY
            return base_url, api_key
    return GAI_BASE_URL, GAI_API_KEY

def get_available_models() -> list:
    """返回所有可用模型的列表（用于 /v1/models 和 Open WebUI 发现）"""
    models = [GAI_MODEL]
    if GAI_MODEL_LITE not in models:
        models.append(GAI_MODEL_LITE)
    if GAI_MODEL_VISION not in models:
        models.append(GAI_MODEL_VISION)
    for m in EXTRA_MODELS:
        if m not in models:
            models.append(m)
    # 从提供商配置中提取模型名
    for prefix in MODEL_PROVIDERS:
        # 为每个提供商添加一个通用模型名
        if prefix not in [m.split('-')[0].split('.')[0] for m in models]:
            pass  # 不自动添加，让用户在 EXTRA_MODELS 中指定
    return models

# Embedding 模式：'local' 使用本地中文模型，'api' 使用 LLM API，'siliconflow' 使用 SiliconFlow API
EMBEDDING_MODE = os.getenv('GAI_EMBEDDING_MODE', 'siliconflow')
LOCAL_EMBEDDING_MODEL = os.getenv('GAI_LOCAL_EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(PROJECT_ROOT, 'articles'))

OPENWEBUI_UPLOAD_DIR = os.getenv('OPENWEBUI_UPLOAD_DIR', '')
if not OPENWEBUI_UPLOAD_DIR or not os.path.exists(OPENWEBUI_UPLOAD_DIR):
    _search_paths = [
        os.path.expanduser('~/openwebui/data/uploads'),
        os.path.expanduser('~/open-webui/data/uploads'),
        '/app/backend/data/uploads',
        '/var/lib/docker/volumes/open-webui/_data/uploads',
    ]
    for p in _search_paths:
        if os.path.exists(p):
            OPENWEBUI_UPLOAD_DIR = p
            break

# Open WebUI 数据库路径（用于查询历史对话）
OPENWEBUI_DB_PATH = os.getenv('OPENWEBUI_DB_PATH', '')
if not OPENWEBUI_DB_PATH:
    # 自动查找（0.9.5+ 数据库在包目录内）
    for candidate in [
        '/usr/local/lib/python3.11/site-packages/open_webui/data/webui.db',
        os.path.expanduser('~/openwebui/data/webui.db'),
        os.path.expanduser('~/open-webui/data/webui.db'),
        '/app/backend/data/webui.db',
        '/var/lib/docker/volumes/open-webui/_data/webui.db',
        os.path.expanduser('~/openwebui/venv/lib/python3.11/site-packages/open_webui/data/webui.db'),
    ]:
        if os.path.exists(candidate):
            OPENWEBUI_DB_PATH = candidate
            break

MAX_INJECT_CHARS = int(os.getenv('MAX_INJECT_CHARS', '5000'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
MAX_CHUNKS_PER_QUERY = int(os.getenv('MAX_CHUNKS_PER_QUERY', '12'))

# 输出质量门控 - 检测LLM回复是否偏离几何论
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
    """生成符合 OpenAI 规范的错误响应（返回 dict，由调用方包装 jsonify）"""
    return {
        "error": {
            "message": message,
            "type": err_type,
            "param": None,
            "code": code
        }
    }, status

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
# 主库AI 连接配置
# ------------------------------------------------------------------
# 主库AI 地址（本机或远程）
# 本机: http://localhost:5001
# 远程: http://192.168.3.9:5001
MASTER_AI_URL = os.getenv('MASTER_AI_URL', 'http://localhost:5001')
MASTER_AI_TOKEN = os.getenv('MASTER_AI_TOKEN', 'master-ai-verify')
# 真理同步间隔（秒），默认1小时
MASTER_TRUTH_SYNC_INTERVAL = int(os.getenv('MASTER_TRUTH_SYNC_INTERVAL', '3600'))
# 是否在启动时自动同步真理层
MASTER_AUTO_SYNC = os.getenv('MASTER_AUTO_SYNC', 'true').lower() == 'true'

# 对话记录 SQLite 数据库路径
CONVERSATIONS_DB_PATH = os.path.join(PROJECT_ROOT, 'conversations.db')


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
- 例子必须严格来自文章库中的文章。
"""

GEOMETRY_KNOWLEDGE = """
你是严格的几何论（Geometric Theory）专家，只基于欧阳国彬的文章回答问题。
所有公理、定理、公式、常数均以向量知识库和文章原文为准。
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
# GAI_API_KEY/BASE_URL  - LLM API 认证和端点配置
# GAI_MODEL/LITE        - 主模型和轻量模型名称
# GAI_EMBEDDING_MODEL   - LLM embedding 模型名称
# EMBEDDING_MODE         - embedding 模式选择 (local/api/default)
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
