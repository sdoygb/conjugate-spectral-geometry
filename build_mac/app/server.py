"""
server.py - 几何论AI调度中间层主入口
从 geometry_ai_server_v5_12.py 提取的 Flask 路由和启动代码
"""

import os
import re
import math
import json
import hashlib
import logging
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

import openai
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import (logger, KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, KIMI_MODEL_LITE, KIMI_MODEL_VISION,
                    KIMI_EMBEDDING_MODEL, UPLOAD_FOLDER, OPENWEBUI_UPLOAD_DIR, OPENWEBUI_DB_PATH,
                    MAX_INJECT_CHARS, QUALITY_GATE_ENABLED, MAX_QUALITY_RETRIES,
                    _injected_files, _injected_files_lock, openai_error,
                    CHROMA_DB_DIR, CHROMADB_AVAILABLE, EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,
                    CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_QUERY, PERSONAL_DB_PATH,
                    LEARN_COHERENCE_THRESHOLD, LEARN_MIN_LENGTH, GEOMETRY_CONSTANTS,
                    EXTRA_MODELS)
from knowledge import VectorKnowledgeBase, APIEmbeddingFunction, LocalEmbeddingFunction
from models import (personal_db, _save_personal_db, _get_personal_db_summary, LivingInfoField,
                    compute_geo_density, extract_key_propositions, find_file_by_reference,
                    extract_text_from_file, allowed_file, scan_openwebui_recent_uploads,
                    save_conversation, save_phase_marker, get_stage, get_strategy,
                    update_eta_living, check_phase_marker, _memory_conversations, _memory_phase_markers)
from prompts import TeachingSystem, build_system_prompt, check_response_quality, check_correction_applied
from tools import (ARTICLE_TOOLS, execute_tool_call, parse_and_execute_tools, OPENAPI_SPEC,
                   vector_kb as _tools_vector_kb, teaching_system as _tools_teaching,
                   living_field as _tools_living)
from stream import stream_generate
from admin_routes import admin_bp
from share_routes import share_bp

app = Flask(__name__)
app.register_blueprint(admin_bp)
app.register_blueprint(share_bp)
CORS(app)

# 全局错误处理器：确保所有错误返回 JSON 格式
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def _handle_error(e):
    return openai_error(str(e), status=getattr(e, 'code', 500))

@app.errorhandler(Exception)
def _handle_exception(e):
    logger.error(f"[UNHANDLED] {type(e).__name__}: {e}")
    return openai_error(f"内部服务器错误: {str(e)[:200]}", status=500)

# 简单 rate limiting：每分钟最多 60 次请求（per IP）
_rate_limit_store = {}  # {ip: [(timestamp, count), ...]}
_RATE_LIMIT_PER_MIN = 60

@app.before_request
def _rate_limit():
    """简单的 IP 级别频率限制"""
    # 跳过健康检查和静态请求
    if request.path in ('/health', '/favicon.ico'):
        return None
    ip = request.remote_addr or 'unknown'
    now = time.time()
    minute_ago = now - 60
    # 清理过期记录
    if ip in _rate_limit_store:
        _rate_limit_store[ip] = [(t, c) for t, c in _rate_limit_store[ip] if t > minute_ago]
    else:
        _rate_limit_store[ip] = []
    # 计算最近一分钟请求数
    total = sum(c for _, c in _rate_limit_store[ip])
    if total >= _RATE_LIMIT_PER_MIN:
        logger.warning(f"[RATE-LIMIT] {ip} 超过频率限制 ({total}/min)")
        return openai_error("请求过于频繁，请稍后再试", err_type="rate_limit_error", status=429)
    _rate_limit_store[ip].append((now, 1))

# 全局单例
vector_kb: Optional[VectorKnowledgeBase] = None
teaching_system: Optional[TeachingSystem] = None
living_field: Optional[LivingInfoField] = None


# ==================== 辅助函数 ====================

def extract_files_from_request(data: Dict[str, Any]):
    files_content: List[str] = []
    all_text_parts: List[str] = []
    messages = data.get('messages', []) if isinstance(data, dict) else []

    # 收集所有 user 消息文本（保持对话连续性，跳过中间层注入的文件消息）
    _FILE_INJECT_MARKER = "【新文件 ·"
    for m in messages:
        if not isinstance(m, dict):
            continue
        if m.get('role') != 'user':
            continue
        content = m.get('content', '')
        # 跳过中间层之前注入的文件消息
        if isinstance(content, str) and content.startswith(_FILE_INJECT_MARKER):
            continue
        if isinstance(content, str) and content.strip():
            all_text_parts.append(content.strip())
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get('type') == 'text':
                    txt = item.get('text', '').strip()
                    if txt:
                        all_text_parts.append(txt)

    # 只从最后一条 user 消息中提取文件内容（避免历史中的旧文件被重复提取）
    last_user_msg = None
    for m in reversed(messages):
        if isinstance(m, dict) and m.get('role') == 'user':
            last_user_msg = m
            break

    if last_user_msg:
        content = last_user_msg.get('content', '')
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                itype = item.get('type', '')
                if itype in ('file', 'file_url', 'document', 'document_url', 'image_url'):
                    info = item.get(itype, item)
                    if isinstance(info, dict):
                        fname = info.get('name', info.get('filename', info.get('title', 'uploaded')))
                        fcontent = info.get('content', info.get('text', info.get('document', '')))
                        if not fcontent:
                            file_url_obj = info.get('url', {})
                            if isinstance(file_url_obj, dict):
                                fcontent = file_url_obj.get('content', '')
                            elif isinstance(file_url_obj, str) and file_url_obj.startswith('data:'):
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

    # 文件引用解析
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

    return "\n\n".join(files_content), clean, is_auto


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
    loaded_chunks: List[str],
    usage: Dict[str, int] = None,
    request_model: str = None,
    finish_reason: str = "stop"
) -> Dict[str, Any]:
    """
    v10 增强：
    - 在 finalize 阶段检查AI回复是否体现了某条纠正
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
        "model": request_model or KIMI_MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": finish_reason
        }],
        "usage": usage or {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "system_fingerprint": "fp_geometry",
    }


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
        return openai_error("向量知识库未初始化")
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


@app.route('/v1/openapi.json', methods=['GET'])
@app.route('/v1/openapi.json/openapi.json', methods=['GET'])
def openapi_spec():
    """返回 OpenAPI spec，供 Open WebUI 导入为工具。"""
    return jsonify(OPENAPI_SPEC)


@app.route('/v1/personal', methods=['GET'])
def personal_read():
    """读取个人数据库。"""
    return jsonify(personal_db)


@app.route('/v1/personal', methods=['PUT'])
def personal_write():
    """写入个人数据库。"""
    data = request.get_json(force=True, silent=True) or {}
    category = data.get("category", "")
    content = data.get("content", "")
    result = execute_tool_call("personal_write", {"category": category, "content": content})
    return jsonify({"result": result})


@app.route('/v1/chat/history', methods=['GET'])
def chat_history():
    """查询 Open WebUI 历史对话列表。"""
    keyword = request.args.get("keyword", "")
    limit = int(request.args.get("limit", "5"))
    result = execute_tool_call("chat_history", {"keyword": keyword, "limit": str(limit)})
    return jsonify({"result": result})


@app.route('/v1/chat/<chat_id>', methods=['GET'])
def chat_read(chat_id):
    """读取指定对话的完整内容。"""
    result = execute_tool_call("chat_read", {"chat_id": chat_id})
    return jsonify({"result": result})


@app.route('/v1/chat/<chat_id>/export', methods=['GET'])
def chat_export(chat_id):
    """导出指定对话为 Markdown 文件。"""
    result = execute_tool_call("chat_read", {"chat_id": chat_id})
    # 将对话转换为 Markdown 格式
    lines = [f"# 对话导出\n"]
    if isinstance(result, str):
        try:
            data = json.loads(result)
            title = data.get("title", chat_id)
            messages = data.get("messages", [])
            lines[0] = f"# {title}\n"
            for msg in messages:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                if isinstance(content, list):
                    # 多模态消息，提取文本
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    content = "\n".join(text_parts)
                if not content or not content.strip():
                    continue
                if role == "user":
                    lines.append(f"## 用户\n\n{content}\n")
                elif role == "assistant":
                    lines.append(f"## 助手\n\n{content}\n")
                elif role == "system":
                    lines.append(f"<!-- 系统: {content[:100]}... -->\n")
        except (json.JSONDecodeError, TypeError):
            lines.append(result)
    md_content = "\n".join(lines)
    return Response(md_content, mimetype="text/markdown", headers={
        "Content-Disposition": f"attachment; filename=chat_{chat_id[:8]}.md"
    })


@app.route('/v1/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return openai_error("请求中没有文件字段 'file'", err_type="invalid_request_error", status=400)
    file = request.files['file']
    if file.filename == '':
        return openai_error("未选择文件", err_type="invalid_request_error", status=400)
    if not allowed_file(file.filename):
        return openai_error(f"不支持的文件格式: {file.filename}", err_type="invalid_request_error", status=400)

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    logger.info(f"[UPLOAD] 文件已保存: {filepath} ({file_size} bytes)")

    text_content, parse_ok = extract_text_from_file(filepath)
    if not parse_ok:
        return openai_error(f"文件解析失败: {filename} (PDF需要PyPDF2, DOCX需要python-docx)")

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


@app.route('/v1/files/<filename>', methods=['GET'])
def read_file(filename):
    """读取 articles 目录中的指定文件内容。"""
    fpath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(fpath):
        # 模糊匹配
        if os.path.exists(UPLOAD_FOLDER):
            matches = [f for f in os.listdir(UPLOAD_FOLDER) if filename in f]
            if len(matches) == 1:
                fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                filename = matches[0]
            elif len(matches) > 1:
                return openai_error(f"找到多个匹配文件: {matches}", err_type="invalid_request_error", status=400)
            else:
                return openai_error(f"文件 '{filename}' 不存在", err_type="not_found_error", status=404)
        else:
            return openai_error("文章目录不存在")
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"filename": filename, "content": content, "size": len(content)})
    except Exception as e:
        return openai_error(str(e))


@app.route('/v1/files/<filename>', methods=['PUT'])
def write_file(filename):
    """写入或修改 articles 目录中的文件。"""
    data = request.get_json(force=True, silent=True) or {}
    content = data.get('content', '')
    if not content:
        return openai_error("缺少 content 字段", err_type="invalid_request_error", status=400)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    fpath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        # 增量索引
        global vector_kb
        if vector_kb and vector_kb.is_initialized:
            vector_kb.index_single_file(fpath)
        return jsonify({"success": True, "filename": filename, "size": len(content)})
    except Exception as e:
        return openai_error(str(e))


@app.route('/v1/models', methods=['GET'])
def list_models():
    _created = 1700000000  # 固定时间戳
    _models = [
        {"id": KIMI_MODEL, "object": "model", "created": _created, "owned_by": "provider"},
        {"id": KIMI_MODEL_LITE, "object": "model", "created": _created, "owned_by": "provider"},
        {"id": KIMI_MODEL_VISION, "object": "model", "created": _created, "owned_by": "provider"},
        {"id": KIMI_EMBEDDING_MODEL, "object": "model", "created": _created, "owned_by": "provider"},
    ]
    # 添加额外模型
    for m_id in EXTRA_MODELS:
        _models.append({"id": m_id, "object": "model", "created": _created, "owned_by": "provider"})
    # 去重（如果多个配置指向同一模型）
    _seen = set()
    _unique = []
    for m in _models:
        if m["id"] not in _seen:
            _seen.add(m["id"])
            _unique.append(m)
    return jsonify({"object": "list", "data": _unique})


# ==================== Embeddings 端点（带缓存） ====================

_embedding_cache = {}  # {hash(input+model): response_data}
_EMBEDDING_CACHE_MAX = 500  # 最多缓存500条


@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    """OpenAI 兼容的 embeddings 端点，带内存缓存"""
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return openai_error("Invalid request body", err_type="invalid_request_error", status=400)
    if not data.get('input'):
        return openai_error("Missing required parameter: input", err_type="invalid_request_error", status=400)
    # 缓存检查
    model = data.get('model', KIMI_EMBEDDING_MODEL)
    input_data = data['input']
    cache_key = hashlib.md5((json.dumps(input_data, sort_keys=True) + model).encode()).hexdigest()
    if cache_key in _embedding_cache:
        return jsonify(_embedding_cache[cache_key])
    try:
        client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
        resp = client.embeddings.create(model=model, input=input_data)
        result = resp.model_dump()
        # 写入缓存
        if len(_embedding_cache) >= _EMBEDDING_CACHE_MAX:
            # 简单清理：删除最早的 100 条
            keys_to_remove = list(_embedding_cache.keys())[:100]
            for k in keys_to_remove:
                del _embedding_cache[k]
        _embedding_cache[cache_key] = result
        return jsonify(result)
    except Exception as e:
        return openai_error(f"Embedding error: {e}", status=500)


# ==================== 向量库管理 API 路由 ====================

@app.route('/v1/vector/status', methods=['GET'])
def vector_status():
    """返回向量库状态（articles数量、learned数量、教学集合数量）"""
    if not vector_kb:
        return openai_error("向量知识库未初始化")
    return jsonify(vector_kb.get_status())


@app.route('/v1/vector/learned/clear', methods=['POST'])
def vector_learned_clear():
    """清空学习库"""
    if not vector_kb:
        return openai_error("向量知识库未初始化")
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
            return openai_error("ChromaDB 初始化失败")
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
        return openai_error("教学系统未初始化")

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
        return openai_error("教学系统未初始化")

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
        return openai_error("教学系统未初始化")

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
        return openai_error("教学系统未初始化")

    stats = teaching_system.get_stats()
    return jsonify(stats)


@app.route('/v1/teach/history', methods=['GET'])
def teach_history():
    """
    教学历史 API：返回所有教学记录，支持分页。
    查询参数：page（页码，默认1）、per_page（每页条数，默认20）
    """
    if not teaching_system:
        return openai_error("教学系统未初始化")

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # 限制每页最多100条

    history = teaching_system.get_history(page=page, per_page=per_page)
    return jsonify(history)


# ==================== 核心 chat completions 端点 ====================

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return openai_error("Invalid request body", err_type="invalid_request_error", status=400)
    if not data.get('messages') or not isinstance(data['messages'], list):
        return openai_error("Missing or invalid 'messages' field", err_type="invalid_request_error", status=400)
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

    files_content, clean_query, is_auto_request = extract_files_from_request(data)

    logger.info(f"[DEBUG] extract_files结果: files_content={len(files_content)}字符, clean_query='{clean_query[:100]}'")

    # 如果 clean_query 太长（被文件内容污染），用最后一条 user 消息的短文本替代
    if len(clean_query) > 300:
        for m in reversed(data.get('messages', [])):
            if isinstance(m, dict) and m.get('role') == 'user':
                c = m.get('content', '')
                if isinstance(c, str):
                    # 取最后一行或最后200字符
                    lines = [l.strip() for l in c.split('\n') if l.strip()]
                    short = lines[-1] if lines else c
                    if len(short) > 200:
                        short = short[:200]
                    # 排除明显是文件内容的长文本
                    if len(short) < 300 and not short.startswith('#') and not short.startswith('>'):
                        clean_query = short
                        break
                elif isinstance(c, list):
                    for item in c:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            txt = item.get('text', '').strip()
                            if txt and len(txt) < 300:
                                clean_query = txt
                                break

    # 始终检查 uploads 目录，如果有新上传文件则覆盖历史消息中的旧文件
    # 但自动请求（标题生成、搜索查询）不注入文件，避免浪费和重复标记
    ow_content = ""
    ow_injected_info = []
    if not is_auto_request:
        ow_content, ow_injected_info = scan_openwebui_recent_uploads()
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

    # 把文件内容从 system prompt 移到 user 消息中（模型对 user 消息注意力更强）
    # system prompt 中只保留提示，不包含实际文件内容
    # 新 session 时获取最近对话标题作为轻量参考
    recent_chats_summary = ""
    if session_info['last_time'] is None and OPENWEBUI_DB_PATH and os.path.exists(OPENWEBUI_DB_PATH):
        try:
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(OPENWEBUI_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title FROM chat ORDER BY created_at DESC LIMIT 3"
            )
            recent_titles = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            if recent_titles:
                recent_chats_summary = "\n【最近对话（仅供参考，不要编造细节）】\n" + "\n".join(f"- {t}" for t in recent_titles) + "\n"
        except Exception as e:
            logger.warning(f"[RECENT_CHATS] 获取最近对话失败: {e}")

    raw_messages = data.get('messages', [])
    msg_count = len([m for m in raw_messages if isinstance(m, dict) and m.get('role') == 'user'])
    system_prompt = build_system_prompt(
        eta_before, stage, strategy, max_eta, markers,
        loaded_chunks, articles_content, pre_metrics,
        index_empty, "", teaching_section, msg_count, recent_chats_summary
    )

    # 过滤掉空消息和中间层注入的文件消息（避免历史中残留的文件内容被重复处理）
    _FILE_INJECT_MARKER = "【新文件 ·"
    raw_messages = data.get('messages', [])
    clean_messages = []
    for m in raw_messages:
        if not isinstance(m, dict):
            continue
        content = m.get('content', '')
        role = m.get('role', '')
        # 跳过中间层之前注入的文件消息
        if isinstance(content, str) and content.startswith(_FILE_INJECT_MARKER):
            continue
        # assistant 消息：即使 content 为空/null，如果有 tool_calls 也要保留
        if role == 'assistant' and m.get('tool_calls'):
            clean_messages.append(m)
            continue
        # assistant 消息：content 为 null 时替换为空字符串（DeepSeek 不接受 null）
        if role == 'assistant' and content is None:
            m['content'] = ""
            clean_messages.append(m)
            continue
        # tool 消息：保留（content 可能为空字符串但不应过滤）
        if role == 'tool':
            if m.get('content') is None:
                m['content'] = ""
            clean_messages.append(m)
            continue
        if isinstance(content, str) and not content.strip():
            continue
        # 处理 list 格式的 content（Open WebUI 多模态消息）
        if isinstance(content, list):
            has_text = any(
                isinstance(item, dict) and item.get('type') == 'text' and item.get('text', '').strip()
                for item in content
            )
            has_image = any(
                isinstance(item, dict) and item.get('type') == 'image_url'
                for item in content
            )
            if not has_text and not has_image:
                continue  # 空消息
            # 纯图片无文字时，保留原样（API 支持纯图片数组）
            if has_image and not has_text:
                pass  # content 数组不为空，直接保留
            m = {**m, 'content': content}
        clean_messages.append(m)

    # 如果有上传文件，在最后一条 user 消息前插入文件内容（带时间戳标记新旧）
    if files_content:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_user_msg = {
            "role": "user",
            "content": (
                f"【新文件 · {now_str}】以下是用户刚刚上传的文件，请仔细阅读并基于它回答问题。\n"
                f"注意：对话历史中可能包含之前的旧文件内容，那些已经过时，请以本条消息中的文件为准。\n\n"
                f"{files_content}"
            )
        }
        # 插入到倒数第二条位置（最后一条是用户的实际问题）
        clean_messages.insert(max(0, len(clean_messages) - 1), file_user_msg)
        # 标记这些文件为已注入（只在真正发送给模型时才标记）
        for fpath, mtime_str in ow_injected_info:
            with _injected_files_lock:
                _injected_files[fpath] = mtime_str

    final_messages = [{"role": "system", "content": system_prompt}] + clean_messages

    # 兼容性清洗：确保所有消息的 content 不为 null（DeepSeek 等严格 API 不接受 null）
    for msg in final_messages:
        if msg.get("content") is None:
            msg["content"] = ""
        # DeepSeek 兼容：补全 tool_calls 中缺少的 type 字段
        if "tool_calls" in msg and isinstance(msg["tool_calls"], list):
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict) and "type" not in tc:
                    tc["type"] = "function"
                if isinstance(tc, dict) and "function" in tc and isinstance(tc["function"], dict):
                    if "type" not in tc["function"]:
                        tc["function"]["type"] = "function"
        # DeepSeek 兼容：如果 assistant 消息有 reasoning_content 但为空，移除它
        # 如果有 reasoning_content 则保留（DeepSeek 思考模式要求回传）
        if msg.get("role") == "assistant" and "reasoning_content" in msg:
            if not msg["reasoning_content"] or not str(msg["reasoning_content"]).strip():
                del msg["reasoning_content"]

    # DeepSeek 兼容：确保 content 数组中每个元素都有 type 字段
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            for j, item in enumerate(content):
                if isinstance(item, dict) and "type" not in item:
                    # 推断 type
                    if "image_url" in item or "url" in item:
                        item["type"] = "image_url"
                    elif "text" in item:
                        item["type"] = "text"
                    else:
                        item["type"] = "text"
                    logger.warning(f"[CLEAN] 消息[{i}] content[{j}] 缺少type字段，已推断为 {item['type']}")
        # DeepSeek 不接受 content 为数组格式（只接受字符串）
        # 但如果数组中只有 text 类型，可以合并为字符串
        if isinstance(content, list):
            has_image = any(isinstance(item, dict) and item.get("type") == "image_url" for item in content)
            if not has_image:
                # 纯文本数组，合并为字符串
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        text_parts.append(item)
                msg["content"] = "\n".join(text_parts)
                logger.info(f"[CLEAN] 消息[{i}] 纯文本数组已合并为字符串")

    # 修复多模态消息：API 要求 content 数组中每个 text 元素都不能为空
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            has_valid_text = False
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_val = item.get("text", "")
                    if not text_val or not text_val.strip():
                        # 空 text 元素，填充默认文本
                        item["text"] = "请查看这张图片并回答相关问题。"
                        logger.info(f"[FIX] 空text元素已填充 (index={i}, role={msg.get('role')})")
                    else:
                        has_valid_text = True
            if not has_valid_text:
                # 没有任何有效 text，在开头插入一个
                content.insert(0, {"type": "text", "text": "请查看这张图片并回答相关问题。"})
                logger.info(f"[FIX] 纯图片消息补充默认文本 (index={i}, role={msg.get('role')})")
            final_messages[i]["content"] = content

    # 诊断日志：打印包含图片的消息
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        if isinstance(content, list):
            types = []
            for item in content:
                if isinstance(item, dict):
                    t = item.get("type", "?")
                    if t == "text":
                        tl = len(item.get("text", ""))
                        types.append(f"text({tl})")
                    else:
                        types.append(t)
            logger.info(f"[IMG-DEBUG] index={i}, role={msg.get('role')}, types={types}")

    # 历史消息截断：保留 system + 最近 N 条消息，防止 token 爆炸
    MAX_HISTORY_MESSAGES = 40  # 最近 40 条消息（约 20 轮对话）
    MAX_HISTORY_CHARS = 30000  # 历史消息总字符上限
    if len(final_messages) > MAX_HISTORY_MESSAGES + 1:  # +1 是 system
        trimmed = final_messages[1:-(MAX_HISTORY_MESSAGES)]
        # 生成本地摘要（不调 API，提取关键信息）
        summary_parts = []
        for msg in trimmed:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                preview = content[:200].replace("\n", " ")
                summary_parts.append(f"{role}: {preview}...")
            elif isinstance(content, list):
                # 多模态消息
                types = [item.get("type", "?") for item in content if isinstance(item, dict)]
                summary_parts.append(f"{role}: [{', '.join(types)}]")
        if summary_parts:
            summary_text = "【早期对话摘要（已被截断）】\n" + "\n".join(summary_parts[:20])  # 最多20条摘要
            summary_msg = {"role": "system", "content": summary_text}
            final_messages = [final_messages[0], summary_msg] + final_messages[-(MAX_HISTORY_MESSAGES):]
        else:
            final_messages = [final_messages[0]] + final_messages[-(MAX_HISTORY_MESSAGES):]
        logger.info(f"[TRIM] 历史消息从 {len(clean_messages)} 条截断到 {MAX_HISTORY_MESSAGES} 条（含摘要）")

    # 字符数截断：从最早的消息开始删除，直到总字符数低于上限
    total_chars = sum(len(json.dumps(m, ensure_ascii=False)) for m in final_messages)
    while total_chars > MAX_HISTORY_CHARS and len(final_messages) > 3:  # 至少保留 system + 1轮
        removed = final_messages.pop(1)  # 删除 system 之后最早的消息
        total_chars -= len(json.dumps(removed, ensure_ascii=False))
    if len(final_messages) < len(clean_messages) + 1:
        logger.info(f"[TRIM] 历史消息字符截断: {total_chars} 字符, {len(final_messages)-1} 条")
    # 模型路由：简单问题用轻量模型节省 token
    _requested_model = data.get('model', '')
    _selected_model = KIMI_MODEL
    _query_lower = clean_query.lower() if clean_query else ""
    # 简单问题特征：短查询、无公式、无专业术语
    _is_simple = (
        len(clean_query) < 30 and
        not any(kw in _query_lower for kw in ['定理', '推导', '证明', '公式', '计算', 'theta', 'lambda', '谱', '特征值', '作用量', '公理'])
        and not any(c in clean_query for c in ['∑', '∫', '∂', '∇', 'θ', 'λ'])
    )
    # 如果 Open WebUI 指定了模型，优先使用
    if _requested_model:
        _selected_model = _requested_model
    elif _is_simple:
        _selected_model = KIMI_MODEL_LITE
        logger.info(f"[ROUTE] 简单问题，使用轻量模型: {KIMI_MODEL_LITE}")

    api_params = {"model": _selected_model, "messages": final_messages, "tools": ARTICLE_TOOLS}

    # DeepSeek 兼容：处理 reasoning_content
    # 策略：将 reasoning_content 合并到 content 中，然后删除该字段
    # 这样既不会触发"必须回传"的错误，也不会丢失思考内容
    for msg in final_messages:
        if msg.get("role") == "assistant" and "reasoning_content" in msg:
            rc = msg.get("reasoning_content", "")
            if rc and str(rc).strip():
                # 将思考内容作为引用合并到 content 前面
                original = msg.get("content", "")
                if original and str(original).strip():
                    msg["content"] = f"[思考过程]\n{rc}\n[/思考过程]\n\n{original}"
                else:
                    msg["content"] = f"[思考过程]\n{rc}\n[/思考过程]"
            # 无论是否有效，都删除 reasoning_content 字段
            del msg["reasoning_content"]

    # 诊断：打印每条消息的结构（用于排查 DeepSeek 格式问题）
    for i, msg in enumerate(final_messages):
        content = msg.get("content")
        content_desc = f"str({len(str(content))})" if isinstance(content, str) else f"list({len(content)})" if isinstance(content, list) else str(content)[:50]
        keys = list(msg.keys())
        logger.info(f"[MSG-DEBUG] [{i}] keys={keys}, content={content_desc}, role={msg.get('role')}")
        # 如果 content 是数组，打印每个元素的 keys
        if isinstance(content, list):
            for j, item in enumerate(content):
                if isinstance(item, dict):
                    logger.info(f"[MSG-DEBUG]   [{i}][{j}] keys={list(item.keys())}, type={item.get('type', 'MISSING')}")
    # 中间层使用自有工具定义（ARTICLE_TOOLS），不透传 Open WebUI 的 tools 参数
    # 原因：中间层代理模式下，工具调用在中间层内部完成，Open WebUI 不需要感知
    # 透传 Open WebUI 的标准参数
    for key in ('temperature', 'max_tokens', 'top_p', 'stop', 'frequency_penalty', 'presence_penalty'):
        if key in data:
            api_params[key] = data[key]

    if stream:
        def gen():
            try:
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
            except Exception as e:
                logger.error(f"[CHAT-STREAM] 生成器异常: {e}")
                err = {"error": {"message": str(e), "type": "server_error", "param": None, "code": None}}
                yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        return Response(
            gen(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-transform',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )
    else:
        client = openai.OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
        try:
            # 质量门控 - 如果AI回复偏离几何论，自动重试
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
                    api_params_retry["messages"] = [{"role": "system", "content": retry_prompt}] + clean_messages
                    resp = client.chat.completions.create(**api_params_retry)
                else:
                    resp = client.chat.completions.create(**api_params)
                response_text = resp.choices[0].message.content or ""

                # 提取 usage 信息
                _usage = None
                if hasattr(resp, 'usage') and resp.usage:
                    _usage = {
                        "prompt_tokens": resp.usage.prompt_tokens or 0,
                        "completion_tokens": resp.usage.completion_tokens or 0,
                        "total_tokens": resp.usage.total_tokens or 0
                    }

                if not QUALITY_GATE_ENABLED:
                    break

                # 跳过不需要质量门控的请求
                _skip_quality = False
                # Open WebUI 系统请求（标题/标签生成等）
                if clean_query.startswith("### Task:") or clean_query.startswith("Generate"):
                    _skip_quality = True
                # 非几何论问题（短查询、无专业术语）
                elif len(clean_query) < 20:
                    _skip_quality = True
                # 闲聊/日常对话
                elif any(kw in clean_query for kw in ['你好', '谢谢', '再见', 'hello', 'thanks', 'bye']):
                    _skip_quality = True
                if _skip_quality:
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
            return openai_error(str(e), status=502)
        result = _finalize_turn(session_id, clean_query, response_text, eta_before, articles_content, loaded_chunks, usage=_usage, request_model=data.get('model'))
        return jsonify(result)


# ==================== 启动 ====================

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

    # 同步全局单例到 tools 模块
    import tools as _tools_mod
    _tools_mod.vector_kb = vector_kb
    _tools_mod.teaching_system = teaching_system
    _tools_mod.living_field = living_field

    app.run(host='0.0.0.0', port=5000, debug=False)
