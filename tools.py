"""
tools.py — 工具调用模块
从 geometry_ai_server_v5_12.py 提取
包含：ARTICLE_TOOLS, OPENAPI_SPEC, execute_tool_call, parse_and_execute_tools
"""

import os
import re as _re
import json
import time
import logging
from flask import request as _request
from typing import List, Tuple, Dict, Any
from datetime import datetime

from config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, UPLOAD_FOLDER, OPENWEBUI_DB_PATH, logger
from models import personal_db, _save_personal_db

# ==================== 文本标记工具调用 ====================

_TOOL_PATTERN = _re.compile(r'\[TOOL:(\w+?)(?::([^\]]*))?\](.*?)(?:\[/TOOL\])?', _re.DOTALL)


def parse_and_execute_tools(text: str) -> Tuple[str, bool]:
    """
    解析文本中的 [TOOL:...] 标记，执行工具调用，返回 (处理后的文本, 是否有工具被调用)。
    """
    tools_found = False
    results = []

    # 先处理需要多行内容的工具（write_article, personal_write）
    multiline_pattern = _re.compile(r'\[TOOL:(write_article|personal_write):([^\]]+)\](.*?)\[/TOOL\]', _re.DOTALL)

    def _exec_multiline(m):
        nonlocal tools_found
        tools_found = True
        tool_name = m.group(1)
        tool_arg = m.group(2).strip()
        content = m.group(3).strip()
        result = execute_tool_call(tool_name, {"content": content, "category": tool_arg} if tool_name == "personal_write" else {"filename": tool_arg, "content": content})
        return f"[工具结果: {tool_name}]\n{result}\n[/工具结果]"

    text = multiline_pattern.sub(_exec_multiline, text)

    # 处理其他单行工具
    def _exec_tool(m):
        nonlocal tools_found
        tools_found = True
        tool_name = m.group(1)
        tool_arg = m.group(2) or ""
        tool_arg = tool_arg.strip()
        args = {}
        if tool_name == "list_articles":
            if tool_arg:
                args["pattern"] = tool_arg
        elif tool_name == "read_article":
            args["filename"] = tool_arg
        elif tool_name == "write_article":
            # 已在上面处理，这里跳过
            return m.group(0)
        elif tool_name == "personal_read":
            pass  # 无参数
        elif tool_name == "personal_write":
            # 已在上面 multiline 处理，这里跳过
            return m.group(0)
        elif tool_name == "chat_history":
            if tool_arg:
                args["keyword"] = tool_arg
        elif tool_name == "chat_read":
            args["chat_id"] = tool_arg
        else:
            return m.group(0)
        result = execute_tool_call(tool_name, args)
        return f"[工具结果: {tool_name}]\n{result}\n[/工具结果]"

    text = _TOOL_PATTERN.sub(_exec_tool, text)

    return text, tools_found


# ==================== 工具调用：文件读写（OpenAI function calling 备用） ====================

ARTICLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_articles",
            "description": "列出 articles 目录中的所有文件。支持子目录。默认只列出主目录（不含 archive），可指定 subdir 查看子目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "可选的文件名过滤模式，如 '0.3' 或 '氢原子'"
                    },
                    "subdir": {
                        "type": "string",
                        "description": "子目录名，如 'archive'。不填则只列出主目录文件。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_article",
            "description": "读取 articles 目录中指定文件的内容。返回文件全文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 '1_氢原子能级_CN_260622.6.md'。先用 list_articles 查看可用文件。"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_article",
            "description": "将内容写入 articles 目录中的文件，用于创建或修改几何论文章。写入时旧版自动归档到 archive/。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 '50_新文章_CN_260622.6.md'"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的完整文件内容（Markdown格式）"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "personal_read",
            "description": "读取个人数据库的全部内容（性格、感情、想法、记忆等私人数据）。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "personal_write",
            "description": "写入个人数据库，支持类别: personality(性格)/emotions(感情)/thoughts(想法)/memory(记忆)。也支持子字段如 memory:conversation_highlights。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "类别，如 personality/emotions/thoughts/memory，或带子字段如 memory:conversation_highlights"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容，可以是纯文本或JSON格式"
                    }
                },
                "required": ["category", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "chat_history",
            "description": "查询 Open WebUI 的历史对话列表。返回最近对话的标题、时间和ID。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "可选的搜索关键词（匹配对话标题）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认5",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "chat_read",
            "description": "读取 Open WebUI 中指定对话的完整内容（所有消息）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "对话ID（前几位即可，先用 chat_history 获取ID）"
                    }
                },
                "required": ["chat_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "手动提交当前所有文章修改到 git 版本库并推送到远程。write_article 已自动提交，此工具用于批量提交或推送。",
            "parameters": {
                "type": "object",
                "properties": {
                    "push": {
                        "type": "boolean",
                        "description": "是否同时推送到远程仓库（默认 false）"
                    },
                    "message": {
                        "type": "string",
                        "description": "提交说明（可选，默认自动生成）"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_articles",
            "description": "管理文章的子目录操作：归档旧版文章到 archive/ 子目录、查看归档、创建子目录。注意：只在用户明确要求归档/管理文章时才使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["archive", "list_archive", "create_dir", "move", "delete"],
                        "description": "操作类型：archive(归档到archive/)、list_archive(查看归档)、create_dir(创建子目录)、move(移动文件)、delete(删除文件)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "文件名（archive/move/delete 时必填）"
                    },
                    "target": {
                        "type": "string",
                        "description": "目标子目录或路径（create_dir/move 时必填）"
                    }
                },
                "required": ["action"]
             }
         }
    },
    {
        "type": "function",
        "function": {
            "name": "git_history",
            "description": "查看文章的修改历史（git log）。可以查看某篇文章的版本演变，或查看最近的提交记录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名（可选，不填则显示所有文章的最近提交）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "显示最近几条记录（默认 10）"
                    }
                },
                "required": []
            }
        }
    }
]


# 模块级变量，由 server.py 在启动时设置
vector_kb = None
teaching_system = None
living_field = None

# Git 仓库根目录（articles 所在的 git 仓库）
_GIT_REPO_DIR = None


def _safe_path(filename: str) -> str:
    """安全路径检查：防止路径遍历攻击"""
    fpath = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
    if not fpath.startswith(os.path.abspath(UPLOAD_FOLDER)):
        raise ValueError(f"非法文件路径: {filename}")
    return fpath

def _find_git_repo():
    """查找 articles 目录所在的 git 仓库根目录"""
    global _GIT_REPO_DIR
    if _GIT_REPO_DIR:
        return _GIT_REPO_DIR
    # 从 UPLOAD_FOLDER 向上查找 .git 目录
    d = os.path.abspath(UPLOAD_FOLDER)
    for _ in range(10):
        if os.path.exists(os.path.join(d, '.git')):
            _GIT_REPO_DIR = d
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    _GIT_REPO_DIR = None
    return None


def _auto_git_commit(filename: str, content: str) -> str:
    """write_article 后自动 git add + commit"""
    repo = _find_git_repo()
    if not repo:
        return ""
    try:
        import subprocess as _sp
        rel = os.path.relpath(os.path.join(UPLOAD_FOLDER, filename), repo)
        _sp.run(["git", "-C", repo, "add", rel], capture_output=True, timeout=10)
        # 生成 commit message
        line_count = content.count('\n') + 1
        msg = f"AI修改: {filename} ({line_count}行)"
        r = _sp.run(["git", "-C", repo, "commit", "-m", msg], capture_output=True, timeout=10)
        if r.returncode == 0:
            # 提取短 commit hash
            r2 = _sp.run(["git", "-C", repo, "log", "--oneline", "-1"], capture_output=True, timeout=10)
            short_hash = r2.stdout.decode().strip().split()[0] if r2.returncode == 0 else ""
            return f"已自动提交: {short_hash}"
        else:
            err = r.stderr.decode().strip()
            if "nothing to commit" in err or "no changes added" in err:
                return ""
            return f"(git commit 失败: {err[:80]})"
    except Exception as e:
        return f"(git commit 异常: {str(e)[:60]})"


def _git_push() -> str:
    """尝试 git push"""
    repo = _find_git_repo()
    if not repo:
        return "错误：未找到 git 仓库"
    try:
        import subprocess as _sp
        r = _sp.run(["git", "-C", repo, "push"], capture_output=True, timeout=60)
        if r.returncode == 0:
            return "push 成功"
        err = r.stderr.decode().strip()
        return f"push 失败: {err[:100]}"
    except Exception as e:
        return f"push 异常: {str(e)[:60]}"


def execute_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """执行工具调用并返回结果文本。"""
    try:
        if name == "list_articles":
            pattern = arguments.get("pattern", "")
            subdir = arguments.get("subdir", "")
            if subdir:
                list_dir = os.path.join(UPLOAD_FOLDER, subdir)
            else:
                list_dir = UPLOAD_FOLDER
            if not os.path.exists(list_dir):
                return f"目录 {list_dir} 不存在"
            # 列出文件（不含子目录）
            files = sorted([f for f in os.listdir(list_dir) if os.path.isfile(os.path.join(list_dir, f))])
            if pattern:
                # 智能匹配：支持 "1号" -> "1_", "一号" -> "1_" 等中文数字映射
                import re as _re2
                smart_pattern = pattern
                smart_pattern = _re2.sub(r'(\d+)号', r'\1_', smart_pattern)
                smart_pattern = _re2.sub(r'(\d+)号', r'\1_', smart_pattern)
                # 中文数字映射
                cn_nums = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                           '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
                for cn, num in cn_nums.items():
                    smart_pattern = smart_pattern.replace(cn + '号', num + '_')
                files = [f for f in files if pattern in f or smart_pattern in f]
            if not files:
                return f"目录中没有匹配 '{pattern}' 的文件（共 {len(sorted(os.listdir(UPLOAD_FOLDER)))} 个文件）"
            result = f"共 {len(files)} 个文件：\n"
            for f in files:
                fpath = os.path.join(UPLOAD_FOLDER, f)
                size = os.path.getsize(fpath)
                result += f"  {f} ({size} 字节)\n"
            return result.strip()

        elif name == "read_article":
            filename = arguments.get("filename", "")
            try:
                fpath = _safe_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            if not os.path.exists(fpath):
                # 尝试模糊匹配
                if os.path.exists(UPLOAD_FOLDER):
                    matches = [f for f in os.listdir(UPLOAD_FOLDER) if filename in f]
                    if len(matches) == 1:
                        fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                    elif len(matches) > 1:
                        return f"找到多个匹配文件：{matches}，请指定完整文件名"
                    else:
                        return f"文件 '{filename}' 不存在于 {UPLOAD_FOLDER}，请先用 list_articles 查看"
                else:
                    return f"文章目录 {UPLOAD_FOLDER} 不存在"
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"文件: {filename} ({len(content)} 字符)\n{content}"

        elif name == "write_article":
            filename = arguments.get("filename", "")
            content = arguments.get("content", "")
            if not filename:
                return "错误：缺少文件名"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            try:
                fpath = _safe_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            # 自动归档旧版（如果同名文件已存在）
            archive_msg = ""
            if os.path.exists(fpath):
                archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
                os.makedirs(archive_dir, exist_ok=True)
                archive_path = os.path.join(archive_dir, filename)
                # 如果归档目录已有同名文件，加时间戳区分
                if os.path.exists(archive_path):
                    import time as _time2
                    ts = _time2.strftime("%Y%m%d_%H%M%S")
                    stem, ext = os.path.splitext(filename)
                    archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                import shutil as _shutil
                _shutil.move(fpath, archive_path)
                archive_msg = f"（旧版已归档到 archive/）"
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            # 只索引新写入的文件（增量索引，不重建全部）
            if vector_kb and vector_kb.is_initialized:
                vector_kb.index_single_file(fpath)
            # 自动 git commit（版本管理）
            _git_result = _auto_git_commit(filename, content)
            preview_url = f"http://{_request.host}/preview/{filename}"
            return f"已写入 {filename} ({len(content)} 字符)，向量索引已更新。{archive_msg}{_git_result}\n预览链接: {preview_url}"

        elif name == "personal_read":
            # 读取个人数据库
            return json.dumps(personal_db, ensure_ascii=False, indent=2)

        elif name == "chat_history":
            # 查询 Open WebUI 历史对话
            keyword = arguments.get("keyword", "")
            limit = int(arguments.get("limit", "5"))
            if not OPENWEBUI_DB_PATH or not os.path.exists(OPENWEBUI_DB_PATH):
                return "错误：未找到 Open WebUI 数据库"
            try:
                import sqlite3 as _sqlite3
                conn = _sqlite3.connect(OPENWEBUI_DB_PATH)
                cursor = conn.cursor()
                if keyword:
                    cursor.execute(
                        "SELECT id, title, created_at FROM chat WHERE title LIKE ? ORDER BY created_at DESC LIMIT ?",
                        (f"%{keyword}%", limit)
                    )
                else:
                    cursor.execute(
                        "SELECT id, title, created_at FROM chat ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                rows = cursor.fetchall()
                if not rows:
                    conn.close()
                    return f"未找到匹配 '{keyword}' 的对话" if keyword else "没有历史对话"
                result_lines = [f"最近 {len(rows)} 个对话："]
                for row in rows:
                    from datetime import datetime as _dt
                    ts = _dt.fromtimestamp(row[2]).strftime("%Y-%m-%d %H:%M") if row[2] else "未知"
                    result_lines.append(f"  [{ts}] {row[1]} (id: {row[0][:12]}...)")
                conn.close()
                return "\n".join(result_lines)
            except Exception as e:
                return f"查询失败: {e}"

        elif name == "chat_read":
            # 读取指定对话的完整内容
            chat_id = arguments.get("chat_id", "")
            if not chat_id or not OPENWEBUI_DB_PATH:
                return "错误：需要 chat_id 参数，或数据库不存在"
            try:
                import sqlite3 as _sqlite3
                conn = _sqlite3.connect(OPENWEBUI_DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT chat FROM chat WHERE id LIKE ?", (f"%{chat_id}%",))
                row = cursor.fetchone()
                conn.close()
                if not row:
                    return f"未找到对话 id 包含 '{chat_id}'"
                data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                # Open WebUI 数据结构: data.history.messages 是 dict {id: msg}
                history = data.get("history", {})
                msgs_dict = history.get("messages", {}) if isinstance(history, dict) else {}
                if not msgs_dict:
                    # 兼容旧格式：data 直接是消息列表
                    if isinstance(data, list):
                        msgs_dict = {str(i): m for i, m in enumerate(data)}
                    else:
                        return "对话为空"
                # 按 childrenIds 正向遍历，构建消息序列
                def _walk_chain(mid, visited=None):
                    if visited is None:
                        visited = set()
                    if mid in visited:
                        return []
                    visited.add(mid)
                    msg = msgs_dict.get(mid)
                    if not msg:
                        return []
                    result = [msg]
                    children = msg.get("childrenIds", [])
                    for cid in children:
                        result.extend(_walk_chain(cid, visited))
                    return result
                # 找根消息（无 parentId）
                roots = [mid for mid, m in msgs_dict.items() if not m.get("parentId")]
                all_lines = []
                for root_id in roots:
                    chain = _walk_chain(root_id)
                    for msg in chain:
                        role = msg.get("role", "?")
                        content = msg.get("content", "")
                        if isinstance(content, str) and content.strip():
                            all_lines.append(f"[{role}] {content[:500]}")
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("text"):
                                    all_lines.append(f"[{role}] {item['text'][:500]}")
                if not all_lines:
                    return "对话为空（无文本内容）"
                return f"共 {len(all_lines)} 条消息：\n" + "\n".join(all_lines[-80:])
            except Exception as e:
                return f"读取失败: {e}"

        elif name == "personal_write":
            # 写入个人数据库（JSON + ChromaDB 双写）
            # 支持格式: [TOOL:personal_write:类别] 或 [TOOL:personal_write:类别:子字段]
            category = arguments.get("category", "")
            content = arguments.get("content", "")
            if not category or not content:
                return "错误：需要 category 和 content 参数。类别: personality/emotions/thoughts/memory"
            cat_map = {
                "personality": "personality", "emotions": "emotions",
                "thoughts": "thoughts", "memory": "memory",
                "性格": "personality", "感情": "emotions",
                "想法": "thoughts", "记忆": "memory",
                "心情": "emotions", "偏好": "memory",
            }
            # 支持 "类别:子字段" 格式
            sub_field = None
            if ":" in category:
                parts = category.split(":", 1)
                category = parts[0].strip()
                sub_field = parts[1].strip()
            cat_key = cat_map.get(category, category)
            if cat_key not in personal_db:
                return f"未知类别: {cat_key}，支持: personality/emotions/thoughts/memory"

            # 尝试解析 JSON 内容
            try:
                update_data = json.loads(content)
                if isinstance(update_data, dict):
                    if sub_field and sub_field in personal_db[cat_key]:
                        # 写入指定子字段
                        if isinstance(personal_db[cat_key][sub_field], list):
                            personal_db[cat_key][sub_field].extend(
                                update_data.get(sub_field, []) if isinstance(update_data.get(sub_field), list) else [update_data]
                            )
                        elif isinstance(personal_db[cat_key][sub_field], dict):
                            personal_db[cat_key][sub_field].update(update_data)
                        else:
                            personal_db[cat_key][sub_field] = update_data
                    else:
                        # 合并到类别
                        for k, v in update_data.items():
                            personal_db[cat_key][k] = v
                    _save_personal_db(personal_db)
            except (json.JSONDecodeError, TypeError):
                pass

            # 添加到 JSON 备注
            if "private_notes" in personal_db[cat_key]:
                personal_db[cat_key]["private_notes"].append(content[:500])
            _save_personal_db(personal_db)

            # 同时写入 ChromaDB personal 集合（支持语义检索）
            if vector_kb and vector_kb.is_initialized and hasattr(vector_kb, 'personal_collection'):
                try:
                    chunk_id = f"personal_{cat_key}_{sub_field or 'general'}_{int(time.time())}"
                    vector_kb.personal_collection.add(
                        ids=[chunk_id],
                        documents=[content],
                        metadatas=[{
                            "category": cat_key,
                            "sub_field": sub_field or "",
                            "timestamp": datetime.now().isoformat(),
                            "source": "personal_write"
                        }]
                    )
                    logger.info(f"[PERSONAL] 写入向量库: {cat_key}.{sub_field or '*'}, {len(content)}字符")
                except Exception as e:
                    logger.error(f"[PERSONAL] 向量库写入失败: {e}")
            return f"已写入 {cat_key}.{sub_field or '*'}（JSON + 向量库）"

        elif name == "git_commit":
            import subprocess as _sp
            repo = _find_git_repo()
            if not repo:
                return "错误：未找到 git 仓库，无法提交"
            try:
                do_push = arguments.get("push", False)
                custom_msg = arguments.get("message", "")
                # git add 所有文章
                rel_dir = os.path.relpath(UPLOAD_FOLDER, repo)
                add_path = rel_dir if rel_dir != '.' else "."
                _sp.run(["git", "-C", repo, "add", add_path], capture_output=True, timeout=10)
                # commit
                if custom_msg:
                    msg = custom_msg
                else:
                    # 统计修改了哪些文件
                    r_status = _sp.run(["git", "-C", repo, "diff", "--cached", "--name-only"], capture_output=True, timeout=10)
                    files = r_status.stdout.decode().strip().split('\n') if r_status.stdout else []
                    msg = f"AI批量提交: {', '.join(files[:5])}" if files else "AI批量提交"
                r = _sp.run(["git", "-C", repo, "commit", "-m", msg], capture_output=True, timeout=10)
                if r.returncode == 0:
                    r2 = _sp.run(["git", "-C", repo, "log", "--oneline", "-1"], capture_output=True, timeout=10)
                    short_hash = r2.stdout.decode().strip().split()[0] if r2.returncode == 0 else ""
                    result = f"已提交: {short_hash} ({msg})"
                    if do_push:
                        push_result = _git_push()
                        result += f"\n{push_result}"
                    return result
                else:
                    err = r.stderr.decode().strip()
                    if "nothing to commit" in err:
                        return "没有需要提交的修改"
                    return f"提交失败: {err[:100]}"
            except Exception as e:
                return f"git 操作异常: {str(e)[:100]}"

        elif name == "git_history":
            import subprocess as _sp
            repo = _find_git_repo()
            if not repo:
                return "错误：未找到 git 仓库"
            try:
                filename = arguments.get("filename", "")
                limit = min(int(arguments.get("limit", "10")), 30)
                if filename:
                    # 构建文件相对路径
                    rel_dir = os.path.relpath(UPLOAD_FOLDER, repo)
                    if rel_dir == '.':
                        file_path = filename
                    else:
                        file_path = os.path.join(rel_dir, filename)
                    r = _sp.run(
                        ["git", "-C", repo, "log", "--oneline", f"-{limit}", "--", file_path],
                        capture_output=True, timeout=10
                    )
                else:
                    # 显示所有文章的提交记录
                    rel_dir = os.path.relpath(UPLOAD_FOLDER, repo)
                    if rel_dir == '.':
                        r = _sp.run(
                            ["git", "-C", repo, "log", "--oneline", f"-{limit}"],
                            capture_output=True, timeout=10
                        )
                    else:
                        r = _sp.run(
                            ["git", "-C", repo, "log", "--oneline", f"-{limit}", "--", rel_dir],
                            capture_output=True, timeout=10
                        )
                if r.returncode == 0 and r.stdout:
                    lines = r.stdout.decode().strip().split('\n')
                    return f"最近 {len(lines)} 条提交记录:\n" + "\n".join(f"  {l}" for l in lines)
                return "没有找到提交记录"
            except Exception as e:
                return f"git log 异常: {str(e)[:100]}"

        elif name == "manage_articles":
            import shutil as _shutil2
            action = arguments.get("action", "")
            filename = arguments.get("filename", "")
            target = arguments.get("target", "")

            if action == "archive":
                if not filename:
                    return "错误：缺少文件名"
                try:
                    fpath = _safe_path(filename)
                except ValueError as e:
                    return f"错误：{e}"
                if not os.path.exists(fpath):
                    return f"文件 '{filename}' 不存在"
                archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
                os.makedirs(archive_dir, exist_ok=True)
                archive_path = os.path.join(archive_dir, filename)
                if os.path.exists(archive_path):
                    import time as _time3
                    ts = _time3.strftime("%Y%m%d_%H%M%S")
                    stem, ext = os.path.splitext(filename)
                    archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                _shutil2.move(fpath, archive_path)
                return f"已归档: {filename} -> archive/"

            elif action == "list_archive":
                archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
                if not os.path.exists(archive_dir):
                    return "归档目录为空（archive/ 不存在）"
                files = sorted(os.listdir(archive_dir))
                if not files:
                    return "归档目录为空"
                result = f"归档目录共 {len(files)} 个文件：\n"
                for f in files:
                    fpath = os.path.join(archive_dir, f)
                    size = os.path.getsize(fpath)
                    result += f"  {f} ({size} 字节)\n"
                return result.strip()

            elif action == "create_dir":
                if not target:
                    return "错误：缺少目标子目录名"
                new_dir = os.path.join(UPLOAD_FOLDER, target)
                os.makedirs(new_dir, exist_ok=True)
                return f"已创建子目录: {target}/"

            elif action == "move":
                if not filename or not target:
                    return "错误：缺少文件名和目标路径"
                try:
                    fpath = _safe_path(filename)
                except ValueError as e:
                    return f"错误：{e}"
                if not os.path.exists(fpath):
                    return f"文件 '{filename}' 不存在"
                target_dir = os.path.join(UPLOAD_FOLDER, target)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, filename)
                _shutil2.move(fpath, target_path)
                return f"已移动: {filename} -> {target}/"

            elif action == "delete":
                if not filename:
                    return "错误：缺少文件名"
                try:
                    fpath = _safe_path(filename)
                except ValueError as e:
                    return f"错误：{e}"
                if not os.path.exists(fpath):
                    return f"文件 '{filename}' 不存在"
                os.remove(fpath)
                return f"已删除: {filename}"

            else:
                return f"未知操作: {action}，支持: archive/list_archive/create_dir/move/delete"

        else:
            return f"未知工具: {name}"
    except Exception as e:
        logger.error(f"[TOOL] 执行 {name} 失败: {e}")
        return f"工具执行错误: {e}"


# OpenAPI Spec（供 Open WebUI 导入为工具服务器）
OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Geometry AI Server - 工具集",
        "description": "几何论 AI 可用的文件读写、个人数据库、对话记录查询工具",
        "version": "1.0.0"
    },
    "servers": [{"url": "http://localhost:5000"}],
    "paths": {
        "/v1/files": {
            "get": {
                "summary": "列出文章目录中的所有文件",
                "description": "返回 articles 目录中的文件列表，支持关键词搜索",
                "operationId": "list_articles",
                "parameters": [
                    {"name": "pattern", "in": "query", "description": "搜索关键词（如文件名片段）", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "文件列表"}}
            }
        },
        "/v1/files/{filename}": {
            "get": {
                "summary": "读取指定文章内容",
                "description": "读取 articles 目录中的指定文件，支持模糊匹配文件名",
                "operationId": "read_article",
                "parameters": [
                    {"name": "filename", "in": "path", "description": "文件名（如 1_氢原子能级_CN_260622.6.md），支持模糊匹配", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "文件内容"}}
            },
            "put": {
                "summary": "写入或修改文章",
                "description": "将内容写入 articles 目录中的指定文件，自动更新向量索引",
                "operationId": "write_article",
                "parameters": [
                    {"name": "filename", "in": "path", "description": "文件名", "required": True, "schema": {"type": "string"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object", "properties": {"content": {"type": "string", "description": "文件内容（Markdown格式）"}}, "required": ["content"]}}}
                },
                "responses": {"200": {"description": "写入成功"}}
            }
        },
        "/v1/personal": {
            "get": {
                "summary": "读取个人数据库",
                "description": "返回 AI 的私人数据（性格、感情、想法、记忆等）",
                "operationId": "personal_read",
                "responses": {"200": {"description": "个人数据库内容"}}
            },
            "put": {
                "summary": "写入个人数据库",
                "description": "更新个人数据，支持类别和子字段",
                "operationId": "personal_write",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object", "properties": {
                        "category": {"type": "string", "description": "类别: personality/emotions/thoughts/memory，支持 子字段 如 memory:conversation_highlights"},
                        "content": {"type": "string", "description": "内容，可以是纯文本或JSON"}
                    }, "required": ["category", "content"]}}}
                },
                "responses": {"200": {"description": "写入成功"}}
            }
        },
        "/v1/chat/history": {
            "get": {
                "summary": "查询 Open WebUI 历史对话列表",
                "description": "返回最近的对话列表，支持关键词搜索",
                "operationId": "chat_history",
                "parameters": [
                    {"name": "keyword", "in": "query", "description": "搜索关键词（匹配对话标题）", "required": False, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "description": "返回数量，默认5", "required": False, "schema": {"type": "integer", "default": 5}}
                ],
                "responses": {"200": {"description": "对话列表"}}
            }
        },
        "/v1/chat/{chat_id}": {
            "get": {
                "summary": "读取指定对话的完整内容",
                "description": "返回指定对话的所有消息（最多80条）",
                "operationId": "chat_read",
                "parameters": [
                    {"name": "chat_id", "in": "path", "description": "对话ID（前几位即可）", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "对话内容"}}
            }
        }
    }
}
