import logging
import os
import re as _re
import json
import time
from flask import request as _request
from typing import List, Tuple, Dict, Any
from datetime import datetime
# 文章读取缓存（同一文件 10 秒内不重复读取）
_read_cache: Dict[str, Tuple[str, float]] = {}
_READ_CACHE_TTL = 10  # 秒
from config import GAI_API_KEY, GAI_BASE_URL, GAI_MODEL, UPLOAD_FOLDER, OPENWEBUI_DB_PATH, logger
from models import personal_db, _save_personal_db

# ==================== 新增：代码文件读写工具 ====================
# 自动检测 daima/app 目录（此文件本身就在 daima/app 中）
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))

def _safe_code_path(filename: str) -> str:
    """安全路径检查：限制在 _CODE_DIR 内，仅允许 .py 文件"""
    fpath = os.path.abspath(os.path.join(_CODE_DIR, filename))
    if not fpath.startswith(os.path.abspath(_CODE_DIR)):
        raise ValueError(f"非法文件路径（超出代码目录）: {filename}")
    if not fpath.endswith('.py'):
        raise ValueError(f"仅允许 .py 文件: {filename}")
    return fpath
# ==================== 新增结束 ====================

# ==================== 文本标记工具调用 ====================
_TOOL_PATTERN = _re.compile(r'\[TOOL:(\w+?)(?::([^\]]*))?\](.*?)(?:\[/TOOL\])?', _re.DOTALL)

def parse_and_execute_tools(text: str) -> Tuple[str, bool]:
    """
    解析文本中的 [TOOL:...] 标记，执行工具调用，返回 (处理后的文本, 是否有工具被调用)。
    """
    tools_found = False
    results = []
    # 先处理需要多行内容的工具（write_article, personal_write, write_py_file）
    multiline_pattern = _re.compile(
        r'\[TOOL:(write_article|personal_write|write_py_file):([^\]]+)\](.*?)\[/TOOL\]',
        _re.DOTALL
    )
    def _exec_multiline(m):
        nonlocal tools_found
        tools_found = True
        tool_name = m.group(1)
        tool_arg = m.group(2).strip()
        content = m.group(3).strip()
        if tool_name == "personal_write":
            result = execute_tool_call(tool_name, {"content": content, "category": tool_arg})
        elif tool_name == "write_py_file":
            result = execute_tool_call(tool_name, {"filename": tool_arg, "content": content})
        else:
            result = execute_tool_call(tool_name, {"filename": tool_arg, "content": content})
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
        if tool_name in ("write_article", "personal_write", "write_py_file"):
            # 已在上面 multiline 处理，这里跳过
            return m.group(0)
        elif tool_name == "personal_read":
            pass  # 无参数
        elif tool_name == "read_py_file":
            if tool_arg:
                args["filename"] = tool_arg
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
            "name": "view_article",
            "description": "查看文章完整内容。仅在向量检索提供的片段不够、需要阅读完整文章时使用。向量检索已自动注入相关片段到【参考资料】区域，大多数情况下无需调用此工具。文件名可从参考资料中的文章标签获取。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 '10_中微子集群效应_CN_260626.6.md'。从向量检索结果的文章标签中获取。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "可选，读取的字符数（默认0=全部）。大文章建议设5000避免token浪费。",
                        "default": 0
                    },
                    "offset": {
                        "type": "integer",
                        "description": "可选，从第N个字符开始读取（默认0=从头开始）。用于查看文章末尾部分，如offset=20000表示从第2万字开始读。",
                        "default": 0
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "主动向量语义搜索。用自然语言描述你要找的内容，返回最相关的文章片段（含文件名和位置）。适用于：查找特定概念/定理/公式在哪些文章中出现、跨文章主题汇总、审核时查找相关引用。与被动自动注入不同，你可以用不同查询词多次搜索以覆盖不同角度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，自然语言描述要查找的内容。如 'S_e锁定的证明过程'、'中微子振荡的几何解释'、'因果场动力学与信息场的关系'。"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量（默认8，最大20）",
                        "default": 8
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_article",
            "description": "将内容写入 articles 目录中的文件，用于创建或修改几何论文章。支持分段写入大文章：第一次用 mode=write，后续用 mode=append 追加。写入时旧版自动归档到 archive/。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 '50_新文章_CN_260622.6.md'"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文件内容（Markdown格式）。对于超过30000字符的长文章，请分段调用：第一次 mode=write 写入前半部分，后续 mode=append 追加剩余部分。"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "写入模式：write=覆盖写入（默认，首次使用），append=追加写入（续写大文章的后续部分）"
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
    },
    # ==================== 新增：代码文件读写工具 ====================
    {
        "type": "function",
        "function": {
            "name": "read_py_file",
            "description": "读取 daima/app 目录中的 Python 源文件。用于审查代码、理解项目结构、定位函数/类定义。仅限 .py 文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Python 文件名，如 'tools.py'、'server.py'。仅限 daima/app 目录下的 .py 文件。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "可选，读取的字符数（默认0=全部）。大文件建议设5000避免token浪费。",
                        "default": 0
                    },
                    "offset": {
                        "type": "integer",
                        "description": "可选，从第N个字符开始读取（默认0=从头开始）。",
                        "default": 0
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_py_file",
            "description": "写入/修改 daima/app 目录中的 Python 源文件。支持分段写入：第一次 mode=write，后续 mode=append。写入时旧版自动归档，自动 git commit。仅限 .py 文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Python 文件名，如 'tools.py'。仅限 daima/app 目录下的 .py 文件。"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的完整 Python 代码内容。"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "写入模式：write=覆盖写入（默认），append=追加写入。"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    }
    # ==================== 新增结束 ====================
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

def _find_code_git_repo():
    """查找 daima/app（代码目录）所在的 git 仓库根目录"""
    d = os.path.abspath(_CODE_DIR)
    for _ in range(10):
        if os.path.exists(os.path.join(d, '.git')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
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

def _auto_code_git_commit(filename: str, content: str) -> str:
    """write_py_file 后自动 git add + commit（代码仓库）"""
    repo = _find_code_git_repo()
    if not repo:
        return ""
    try:
        import subprocess as _sp
        rel = os.path.relpath(os.path.join(_CODE_DIR, filename), repo)
        _sp.run(["git", "-C", repo, "add", rel], capture_output=True, timeout=10)
        line_count = content.count('\n') + 1
        msg = f"AI修改代码: {filename} ({line_count}行)"
        r = _sp.run(["git", "-C", repo, "commit", "-m", msg], capture_output=True, timeout=10)
        if r.returncode == 0:
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

def execute_tool_call(name: str, arguments: Dict[str, Any], vector_kb=None) -> str:
    """执行工具调用并返回结果文本。"""
    try:
        if name == "vector_search":
            query = arguments.get("query", "")
            top_k = min(arguments.get("top_k", 8), 20)
            if not vector_kb or not vector_kb.is_initialized:
                return "向量知识库未初始化，无法搜索"
            results = vector_kb.search(query, top_k=top_k)
            if not results:
                return f"未找到与 '{query}' 相关的内容"
            # 格式化结果
            output_parts = [f"向量搜索 '{query}' 返回 {len(results)} 条结果:\n"]
            for r in results:
                meta = r.get('metadata', {})
                fname = meta.get('fname', '?')
                aid = meta.get('article_id', '?')
                start = meta.get('start', '?')
                end = meta.get('end', '?')
                dist = r.get('distance', 0)
                content = r.get('document', '')[:500]
                output_parts.append(f"[{aid}] {fname} 位置:{start}-{end} 距离:{dist:.4f}\n{content}\n")
            return "\n".join(output_parts)
        elif name == "view_article":
            filename = arguments.get("filename", "")
            limit = int(arguments.get("limit", 0) or 0)
            offset = int(arguments.get("offset", 0) or 0)
            try:
                fpath = _safe_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            if not os.path.exists(fpath):
                # 智能模糊匹配：支持编号匹配（如"0.1"匹配"0.1_几何动力学_CN_260626.6.md"）
                if os.path.exists(UPLOAD_FOLDER):
                    matches = [f for f in os.listdir(UPLOAD_FOLDER) if filename in f]
                    # 如果没命中，尝试按编号前缀匹配（如"0.1"开头的文件）
                    if not matches:
                        for f in os.listdir(UPLOAD_FOLDER):
                            if f.startswith(filename + "_"):
                                matches.append(f)
                    if len(matches) == 1:
                        fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                    elif len(matches) > 1:
                        # 多个匹配，优先选最新版本
                        matches.sort(reverse=True)
                        fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                    else:
                        # 列出所有文件帮助AI选择
                        all_files = sorted(os.listdir(UPLOAD_FOLDER))
                        return f"文件 '{filename}' 不存在。可用文件：\n" + "\n".join(all_files[:30])
                else:
                    return "文章目录不存在"
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            total = len(content)
            # 应用offset和limit
            if offset and offset > 0:
                content = content[offset:]
            if limit and limit > 0 and len(content) > limit:
                content = content[:limit] + f"\n...[截断]"
            pos_info = f"位置: {offset}-{min(offset + (limit or total), total)}"
            return f"文件: {filename} (共{total}字符, {pos_info})\n{content}"
        # ==================== 新增：read_py_file ====================
        elif name == "read_py_file":
            filename = arguments.get("filename", "")
            limit = int(arguments.get("limit", 0) or 0)
            offset = int(arguments.get("offset", 0) or 0)
            if not filename:
                return "错误：缺少文件名"
            try:
                fpath = _safe_code_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            if not os.path.exists(fpath):
                # 列出 daima/app 中的 .py 文件帮助 AI 选择
                all_py = sorted([f for f in os.listdir(_CODE_DIR) if f.endswith('.py')])
                # 尝试模糊匹配
                matches = [f for f in all_py if filename in f]
                if len(matches) == 1:
                    fpath = os.path.join(_CODE_DIR, matches[0])
                elif len(matches) > 1:
                    matches.sort()
                    fpath = os.path.join(_CODE_DIR, matches[0])
                else:
                    return f"文件 '{filename}' 不存在。daima/app 中的 .py 文件：\n" + "\n".join(all_py)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            total = len(content)
            if offset and offset > 0:
                content = content[offset:]
            if limit and limit > 0 and len(content) > limit:
                content = content[:limit] + f"\n...[截断]"
            pos_info = f"位置: {offset}-{min(offset + (limit or total), total)}"
            return f"文件: {filename} (共{total}字符, {pos_info})\n{content}"
        # ==================== 新增：write_py_file ====================
        elif name == "write_py_file":
            filename = arguments.get("filename", "")
            content = arguments.get("content", "")
            mode = arguments.get("mode", "write")
            if not filename:
                return "错误：缺少文件名"
            try:
                fpath = _safe_code_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            os.makedirs(_CODE_DIR, exist_ok=True)
            if mode == "append":
                with open(fpath, 'a', encoding='utf-8') as f:
                    f.write(content)
                total_chars = os.path.getsize(fpath)
                git_result = _auto_code_git_commit(filename, content)
                return f"已追加到 {filename}（当前共 {total_chars} 字符）。如还有剩余内容，请继续用 mode=append 调用。{git_result}"
            else:
                # 覆盖写入模式：自动归档旧版
                archive_msg = ""
                if os.path.exists(fpath):
                    archive_dir = os.path.join(_CODE_DIR, "archive")
                    os.makedirs(archive_dir, exist_ok=True)
                    archive_path = os.path.join(archive_dir, filename)
                    if os.path.exists(archive_path):
                        ts = time.strftime("%Y%m%d_%H%M%S")
                        stem, ext = os.path.splitext(filename)
                        archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                    import shutil as _shutil
                    _shutil.move(fpath, archive_path)
                    archive_msg = f"（旧版已归档到 archive/）"
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                git_result = _auto_code_git_commit(filename, content)
                return f"已写入 {filename} ({len(content)} 字符)。{archive_msg}{git_result}"
        elif name == "write_article":
            filename = arguments.get("filename", "")
            content = arguments.get("content", "")
            mode = arguments.get("mode", "write")
            if not filename:
                return "错误：缺少文件名"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            try:
                fpath = _safe_path(filename)
            except ValueError as e:
                return f"错误：{e}"
            if mode == "append":
                # 追加模式：不归档，直接追加
                with open(fpath, 'a', encoding='utf-8') as f:
                    f.write(content)
                total_chars = os.path.getsize(fpath)
                return f"已追加到 {filename}（当前共 {total_chars} 字符）。如还有剩余内容，请继续用 mode=append 调用。全部写完后，向量索引和 git 提交将自动完成。"
            else:
                # 覆盖写入模式（默认）
                # 自动归档旧版（如果同名文件已存在）
                archive_msg = ""
                if os.path.exists(fpath):
                    archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
                    os.makedirs(archive_dir, exist_ok=True)
                    archive_path = os.path.join(archive_dir, filename)
                    if os.path.exists(archive_path):
                        import time as _time2
                        ts = _time2.strftime("%Y%m%d_%H%M%S")
                        stem, ext = os.path.splitext(filename)
                        archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                    import shutil as _shutil2
                    _shutil2.move(fpath, archive_path)
                    archive_msg = f"（旧版已归档到 archive/）"
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                # 只索引新写入的文件（增量索引，不重建全部）
                if vector_kb and vector_kb.is_initialized:
                    vector_kb.index_single_file(fpath)
                # 自动 git commit（版本管理）
                _git_result = _auto_git_commit(filename, content)
                try:
                    preview_host = _request.host
                except RuntimeError:
                    preview_host = "localhost:5000"
                preview_url = f"http://{preview_host}/preview/{filename}"
                return f"已写入 {filename} ({len(content)} 字符)，向量索引已更新。{archive_msg}{_git_result}\n\n【重要】请务必在回复中告诉用户文章已保存，并将以下预览链接以Markdown格式提供给用户：[点击预览文章]({preview_url})"
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
            import shutil as _shutil3
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
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    stem, ext = os.path.splitext(filename)
                    archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                _shutil3.move(fpath, archive_path)
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
                _shutil3.move(fpath, target_path)
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
        "description": "几何论 AI 可用的文件读写、个人数据库、对话记录查询、代码文件读写工具",
        "version": "1.1.0"
    },
    "servers": [{"url": "http://localhost:5000"}],
    "paths": {
        "/v1/files/{filename}": {
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
        },
        # ==================== 新增：代码文件 API ====================
        "/v1/code/{filename}": {
            "get": {
                "summary": "读取 daima/app 中的 Python 源文件",
                "description": "读取 daima/app 目录中的 .py 文件，支持 offset/limit 分段读取",
                "operationId": "read_py_file",
                "parameters": [
                    {"name": "filename", "in": "path", "description": "Python 文件名", "required": True, "schema": {"type": "string"}},
                    {"name": "offset", "in": "query", "description": "起始字符位置", "required": False, "schema": {"type": "integer", "default": 0}},
                    {"name": "limit", "in": "query", "description": "读取字符数（默认全部）", "required": False, "schema": {"type": "integer", "default": 0}}
                ],
                "responses": {"200": {"description": "文件内容"}}
            },
            "put": {
                "summary": "写入/修改 daima/app 中的 Python 源文件",
                "description": "写入 daima/app 目录中的 .py 文件，自动归档旧版并 git commit",
                "operationId": "write_py_file",
                "parameters": [
                    {"name": "filename", "in": "path", "description": "Python 文件名", "required": True, "schema": {"type": "string"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object", "properties": {
                        "content": {"type": "string", "description": "完整的 Python 代码内容"},
                        "mode": {"type": "string", "enum": ["write", "append"], "description": "写入模式", "default": "write"}
                    }, "required": ["content"]}}}
                },
                "responses": {"200": {"description": "写入成功"}}
            }
        }
        # ==================== 新增结束 ====================
    }
}
