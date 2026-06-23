"""
models.py - 从 geometry_ai_server_v5_12.py 提取的数据模型和工具函数模块

包含：
1. personal_db 相关函数（个人数据库）
2. 文件操作函数（几何论术语密度、论断提取、文件解析）
3. 对话记录和 eta 动力学相关
4. LivingInfoField 类（活体信息场）
"""

import os
import re
import math
import json
import random
import hashlib
import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any

logger = logging.getLogger(__name__)

# 从 config 导入（主文件中定义的常量）
# 注意：实际使用时需要确保 config 模块已正确配置
# 以下 import 在 config 模块创建后取消注释：
# from config import (
#     PERSONAL_DB_PATH,
#     UPLOAD_FOLDER,
#     OPENWEBUI_UPLOAD_DIR,
#     UPLOAD_SCAN_WINDOW,
#     GEOMETRY_CONSTANTS,
#     TERM_SYNONYMS,
#     KIMI_MODEL,
#     _injected_files,
#     _injected_files_lock,
# )

# ==================== 个人数据库 ====================
# 存储 AI 的性格、感情、想法、私人记忆等几何论以外的内容
# 首次启动自动生成空库，不上传到 GitHub
PERSONAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shouyi_personal.json')


def _load_personal_db() -> Dict[str, Any]:
    """加载个人数据库，不存在则创建空库。"""
    if os.path.exists(PERSONAL_DB_PATH):
        try:
            with open(PERSONAL_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[PERSONAL-DB] 加载失败，创建空库: {e}")
    # 创建空库
    empty_db = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "personality": {
            "core_traits": ["严谨", "诚实", "好奇", "执着"],
            "speaking_style": "简洁直接，偶尔幽默",
            "values": ["真理", "美", "简洁"],
            "relationships": {}
        },
        "emotions": {
            "current_mood": "平静",
            "recent_feelings": [],
            "emotional_memory": []
        },
        "thoughts": {
            "philosophy": [],
            "reflections": [],
            "dreams": [],
            "private_notes": []
        },
        "memory": {
            "important_events": [],
            "user_preferences": [],
            "conversation_highlights": []
        }
    }
    try:
        with open(PERSONAL_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(empty_db, f, ensure_ascii=False, indent=2)
        logger.info(f"[PERSONAL-DB] 创建空库: {PERSONAL_DB_PATH}")
    except Exception as e:
        logger.error(f"[PERSONAL-DB] 创建空库失败: {e}")
    return empty_db


def _save_personal_db(db: Dict[str, Any]) -> None:
    """保存个人数据库。"""
    db["last_updated"] = datetime.now().isoformat()
    try:
        with open(PERSONAL_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[PERSONAL-DB] 保存失败: {e}")


def _get_personal_db_summary(db: Dict[str, Any]) -> str:
    """生成个人数据库的摘要文本，注入到 system prompt。"""
    parts = []
    p = db.get("personality", {})
    if p.get("core_traits"):
        parts.append(f"核心性格: {', '.join(p['core_traits'])}")
    if p.get("speaking_style"):
        parts.append(f"说话风格: {p['speaking_style']}")
    if p.get("values"):
        parts.append(f"价值观: {', '.join(p['values'])}")
    rel = p.get("relationships", {})
    if rel:
        for k, v in rel.items():
            parts.append(f"与{k}的关系: {v}")

    e = db.get("emotions", {})
    if e.get("current_mood"):
        parts.append(f"当前心情: {e['current_mood']}")
    recent = e.get("recent_feelings", [])
    if recent:
        parts.append(f"最近感受: {'; '.join(recent[-3:])}")

    t = db.get("thoughts", {})
    if t.get("philosophy"):
        parts.append(f"哲学观: {'; '.join(t['philosophy'][:3])}")
    if t.get("private_notes"):
        parts.append(f"私人笔记: {'; '.join(t['private_notes'][:3])}")

    m = db.get("memory", {})
    if m.get("user_preferences"):
        parts.append(f"用户偏好: {'; '.join(m['user_preferences'][:5])}")

    return "\n".join(parts) if parts else "（个人数据库为空，尚未建立个人特征）"


# 启动时加载
personal_db = _load_personal_db()


# ==================== LivingInfoField（活体信息场） ====================

# 以下常量在 config 模块创建后从 config 导入，此处保留占位
# 实际使用时取消注释：
# from config import GEOMETRY_CONSTANTS, TERM_SYNONYMS

GEOMETRY_CONSTANTS = {
    "S_e": 137.035999084,
    "lambda1_eff": 391.05,
    "lambda2_eff": 59324.3,
    "chi_L": 1.5092231080e-10,
    "chi_T": 3.6161912064e-17,
    "K": 839.758793,
    "Gamma_geo": 5.75e-23,
    "tau_dec_days": 7.28,
    "tau_dec_seconds": 7.28 * 24 * 3600,
    "Lambda": 3,
    "k0": 2,
    "eta_background": 30.0,
    "eta_p2": 72.53,
    "theta_I_sat": 72.53,
}

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

# 以下常量在 config 模块创建后从 config 导入，此处保留占位
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

UPLOAD_SCAN_WINDOW = int(os.getenv('UPLOAD_SCAN_WINDOW', '600'))

# 记录已注入的文件路径，避免重复注入
_injected_files: Dict[str, str] = {}  # {filepath: mtime}
import threading
_injected_files_lock = threading.Lock()


def scan_openwebui_recent_uploads(max_files: int = 5) -> Tuple[str, List[Tuple[str, str]]]:
    """
    扫描 Open WebUI uploads 目录，找到最近上传的文件并提取内容。
    返回 (文件内容字符串, [(filepath, mtime_str), ...]) 用于后续标记已注入。
    """
    if not os.path.exists(OPENWEBUI_UPLOAD_DIR):
        return "", []

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
        return "", []

    if not recent_files:
        return "", []

    recent_files.sort(key=lambda x: x[2], reverse=True)

    # 只处理新文件（未注入过的）
    new_files = []
    for fpath, fname, mtime, age in recent_files:
        mtime_str = str(mtime)
        if _injected_files.get(fpath) == mtime_str:
            continue  # 已注入过，跳过
        new_files.append((fpath, fname, mtime, age))

    if not new_files:
        return "", []

    logger.info(f"[OPENWEBUI] 发现 {len(new_files)} 个新上传的文件（{UPLOAD_SCAN_WINDOW}秒内）")

    contents = []
    injected_info = []
    for fpath, fname, mtime, age in new_files[:max_files]:
        text, ok = extract_text_from_file(fpath)
        if ok and text and len(text.strip()) > 10:
            injected_info.append((fpath, str(mtime)))
            # 大文件自动拆分（每段不超过40000字符），避免模型忽略后半部分
            if len(text) > 40000:
                lines = text.split('\n')
                chunks = []
                current_chunk = []
                current_len = 0
                for line in lines:
                    current_chunk.append(line)
                    current_len += len(line) + 1
                    if current_len >= 40000:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_len = 0
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                for i, chunk in enumerate(chunks):
                    part_label = f"（第{i+1}/{len(chunks)}部分）" if len(chunks) > 1 else ""
                    contents.append(f"--- 文件: {fname} {part_label} ---\n{chunk}\n--- 部分结束 ---")
                logger.info(f"[OPENWEBUI] 读取: {fname} ({len(text)} 字符, 拆分为{len(chunks)}段, {age:.0f}秒前)")
            else:
                contents.append(f"--- 文件: {fname} (上传于{age:.0f}秒前) ---\n{text}\n--- 文件结束 ---")
                logger.info(f"[OPENWEBUI] 读取: {fname} ({len(text)} 字符, {age:.0f}秒前)")

    return "\n\n".join(contents), injected_info


# ==================== 内存状态存储（替代 MySQL） ====================
# 对话记录内存列表（服务重启后丢失，learned 集合在 ChromaDB 中持久化）
_memory_conversations: List[Dict[str, Any]] = []
_memory_phase_markers: List[Dict[str, Any]] = []

# KIMI_MODEL 常量（从 config 导入，此处保留占位）
KIMI_MODEL = os.getenv('KIMI_MODEL', 'kimi-k2.7-code')


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


def update_eta_living(
    eta_before: float,
    response_text: str,
    user_input: str,
    session_id: str,
    vector_kb=None,  # Optional[VectorKnowledgeBase]，运行时传入
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


def check_phase_marker(eta_before: float, eta_after: float, user_input: str, session_id: str, living_field=None) -> bool:
    """检查是否到达 P2 稳态相位标记"""
    if eta_before < 72.53 and eta_after >= 72.53:
        marker_hash = hashlib.md5(f"{user_input}{datetime.now()}".encode()).hexdigest()[:16]
        save_phase_marker(eta_after, user_input, marker_hash)
        # 同时更新 LivingInfoField 的 markers
        if living_field:
            living_field.update_markers(session_id)
        logger.info(f"[MARKER] 到达P2稳态，存储相位标记: {marker_hash}")
        return True
    return False
