"""
config.py — 主库AI配置模块

复用上层 app/ 的几何论常数和 SiliconFlow embedding 配置，
主库AI只读公理层（0.0.*）和已验证定理（master_formulas collection）。
"""
import os
import sys
import logging
import logging.handlers
from typing import Dict, Any

# ------------------------------------------------------------------
# 路径
# ------------------------------------------------------------------
# master_ai/ 自身目录
MASTER_AI_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（GeometryAI-Mac-Build/）
PROJECT_ROOT = os.path.dirname(MASTER_AI_DIR)
# 上层 app/ 目录（复用其 .env 和几何论常数）
APP_DIR = os.path.join(PROJECT_ROOT, "app")

# 加载 .env（优先 master_ai/.env，回退 app/.env）
# 不依赖 python-dotenv，手动解析
def _load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # 不覆盖已有的环境变量（除非 .env 在 master_ai/ 下）
                if key and key not in os.environ:
                    os.environ[key] = value

# 先加载 master_ai/.env（最高优先级），再加载 app/.env（补充）
_load_env_file(os.path.join(MASTER_AI_DIR, '.env'))
_load_env_file(os.path.join(APP_DIR, '.env'))

# 如果安装了 dotenv，也用它加载一次（覆盖模式）
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(MASTER_AI_DIR, '.env'), override=True)
    load_dotenv(os.path.join(APP_DIR, '.env'), override=False)
except ImportError:
    pass

# 把 app/ 加入 sys.path，以便复用其模块
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# ------------------------------------------------------------------
# 日志
# ------------------------------------------------------------------
_LOG_DIR = os.getenv('LOG_DIR', os.path.join(MASTER_AI_DIR, 'logs'))
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MASTER-AI %(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.TimedRotatingFileHandler(
            os.path.join(_LOG_DIR, 'master_ai.log'),
            when='midnight', backupCount=7, encoding='utf-8'
        )
    ]
)
logger = logging.getLogger("master_ai")

# ------------------------------------------------------------------
# API 配置（复用上层 app/ 的环境变量）
# ------------------------------------------------------------------
GAI_API_KEY = os.getenv('GAI_API_KEY', '')
GAI_BASE_URL = os.getenv('GAI_BASE_URL', 'https://api.deepseek.com/v1')

# 主库AI使用的验证模型（可以与本地 Agent 不同，强调严格推理）
MASTER_VERIFY_MODEL = os.getenv('MASTER_VERIFY_MODEL', 'deepseek-v4-flash')
# 主库AI的推导模型（独立重推导时使用，可以更强）
MASTER_DERIVE_MODEL = os.getenv('MASTER_DERIVE_MODEL', 'deepseek-v4-flash')

# SiliconFlow embedding（与本地一致，1024维）
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# 主库 ChromaDB 持久化目录（独立于本地 chroma_db）
MASTER_DB_DIR = os.getenv('MASTER_DB_DIR', os.path.join(MASTER_AI_DIR, 'master_chroma_db'))

# 公理层文章目录（只读）
ARTICLES_DIR = os.getenv('UPLOAD_FOLDER', os.path.join(APP_DIR, 'articles'))

# 主库AI服务端口
MASTER_AI_PORT = int(os.getenv('MASTER_AI_PORT', '5001'))

# 主库AI认证 token（提交公式时需要）
MASTER_AI_TOKEN = os.getenv('MASTER_AI_TOKEN', 'master-ai-verify')

# ------------------------------------------------------------------
# 几何论锁定常数（与 app/config.py 完全一致）
# ------------------------------------------------------------------
GEOMETRY_CONSTANTS: Dict[str, Any] = {
    "S_e": 137.035999084,           # 七级递推锁定，精细结构常数倒数
    "lambda1_eff": 391.05,          # rad^-2，有效软模
    "lambda2_eff": 59324.3,         # rad^-2，有效硬模
    "Lambda_H": 150,                # 软硬模比 = lambda2/lambda1
    "chi_L": 1.5092231080e-10,      # m，空间量纲桥
    "chi_T": 3.6161912064e-17,      # s，时间量纲桥
    "K": 839.758793,                # keV，能量尺度常数
    "m_e": 510.99895,               # keV，电子质量
    "tau_dec_days": 7.28,           # 退相干因果深度周期（天）
    "tau_dec_seconds": 7.28 * 24 * 3600,
    "Lambda": 3,                    # 九素互扼面积放大因子
    "k0": 2,                        # 九素互扼维度放大因子
    "eta_background": 30.0,         # 背景点 P0
    "eta_p2": 72.53,                # 上圆满态 P2（theta_I 饱和值）
    "eta_initial": 32.07,           # 初圆满态（theta_I 初级圆满）
    "eta_middle": 55.0,             # 中圆满态（亚稳态）
    # 第七级极限（§9.3 特征尺度用）
    "epsilon_7": 1.928e-9,
    # §9.3 核心尺度预言值
    "r_core_predicted_fm": 8.4,     # fm，Berry相位缺陷核心半径
    # §9.4 外围衰减尺度
    "xi_decay_angstrom": 0.89,      # Å，Berry曲率衰减长度
}

# 基础文章编号前缀（主库AI参考这些 + 已验证主库公式）
AXIOM_PREFIXES = ("0.0.0", "0.0.1", "0.0.3", "0.0.5", "0.0.6", "0.0.7")

# ------------------------------------------------------------------
# 验证标准（§9.6 证伪条件 + 数值吻合容差）
# ------------------------------------------------------------------
VERIFICATION_TOLERANCE = {
    "S_e_relative_error": 1e-7,       # S_e 数值吻合相对误差容限
    "berry_phase_2pi_tolerance": 0.01, # Berry相位与2π整数倍的绝对容差（rad）
    "r_core_min_fm": 0.8,             # §9.6: r_core 下限
    "r_core_max_fm": 84.0,            # §9.6: r_core 上限（一个数量级）
    "derivation_chain_min_depth": 3,   # 推导链最少引用数（防止跳步）
}

logger.info(f"[CONFIG] 主库AI配置加载完成 | 模型={MASTER_VERIFY_MODEL} | DB={MASTER_DB_DIR}")
