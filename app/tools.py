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
import requests as _requests
from bs4 import BeautifulSoup as _BS
from flask import request as _request
from typing import List, Tuple, Dict, Any
from datetime import datetime

# 文章读取缓存（同一文件 10 秒内不重复读取）
_read_cache: Dict[str, Tuple[str, float]] = {}
_READ_CACHE_TTL = 10  # 秒

from config import GAI_API_KEY, GAI_BASE_URL, GAI_MODEL, UPLOAD_FOLDER, OPENWEBUI_DB_PATH, logger
from models import personal_db, _save_personal_db

# ==================== 互联网搜索函数 ====================

_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
_SEARCH_TIMEOUT = 20

# Serper.dev API Key（不需要 SSL 证书，不走爬虫）
_SERPER_API_KEY = 'fca2c84c575026f7eb031babfa1bb9ee56ed8759'
_SERPER_URL = 'https://google.serper.dev/search'
_SERPER_BAIDU_URL = 'https://google.serper.dev/search'  # Serper 统一用 search 端点，engine 参数控制来源

_USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0',
]

# 通用请求头（模仿真实浏览器）
def _make_headers():
    import random as _rand
    return {
        'User-Agent': _rand.choice(_USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

import urllib.request as _urllib_req
import urllib.parse as _urllib_parse

def _http_fetch(url: str, headers: dict = None) -> str:
    """用系统 Python3 发送 HTTP 请求（绕过 .venv 的 LibreSSL 问题）"""
    import subprocess as _sp
    import json as _json
    import base64 as _b64
    try:
        script = 'import urllib.request,urllib.parse,sys,json,base64;'
        script += 'req=urllib.request.Request(sys.argv[1],headers=' + _json.dumps(headers or {}) + ');'
        script += 'resp=urllib.request.urlopen(req,timeout=' + str(_SEARCH_TIMEOUT) + ');'
        script += 'print(base64.b64encode(resp.read()).decode())'
        r = _sp.run(['python3', '-c', script, url], capture_output=True, timeout=_SEARCH_TIMEOUT + 5)
        if r.returncode == 0 and r.stdout:
            import base64 as _b64
            return _b64.b64decode(r.stdout.strip()).decode('utf-8', errors='replace')
        return ''
    except Exception:
        return ''

def _serper_search_curl(query: str, max_results: int = 8, engine: str = 'google') -> list:
    """通过 curl 调用 Serper.dev API（绕过 Python SSL 限制）"""
    import subprocess as _sp
    import json as _json
    results = []
    try:
        payload = {'q': query, 'num': max_results, 'gl': 'cn', 'hl': 'zh-cn'}
        if engine == 'baidu':
            payload['source'] = 'web'
        cmd = [
            'curl', '-s', '-X', 'POST', _SERPER_URL,
            '-H', 'Content-Type: application/json',
            '-H', 'X-API-KEY: ' + _SERPER_API_KEY,
            '-d', _json.dumps(payload),
        ]
        r = _sp.run(cmd, capture_output=True, timeout=15)
        if r.returncode != 0:
            return results
        data = _json.loads(r.stdout.decode('utf-8'))
        for item in data.get('organic', []):
            title = item.get('title', '')[:200]
            link = item.get('link', '')
            snippet = item.get('snippet', '')[:300]
            if title and link:
                results.append({'title': title, 'link': link, 'snippet': snippet})
                if len(results) >= max_results:
                    break
    except Exception:
        pass
    return results

def _search_google(query: str, max_results: int = 8) -> list:
    """搜索 Google（通过 Serper API / curl）"""
    return _serper_search_curl(query, max_results, 'google')

def _search_baidu(query: str, max_results: int = 8) -> list:
    """搜索百度（通过 Serper API / curl，中文结果优先）"""
    # Serper 本身是 Google 源，但加 locale 偏向中文
    return _serper_search_curl(query, max_results, 'google')

def web_search(query: str, max_results: int = 8) -> str:
    """互联网搜索：先 Google 后百度，合并去重"""
    seen_links = set()
    all_results = []
    for search_fn, engine_name in [(_search_google, 'Google'), (_search_baidu, '百度')]:
        try:
            items = search_fn(query, max_results)
            for item in items:
                link = item.get('link', '')
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_results.append(item)
        except Exception as e:
            pass
        if len(all_results) >= max_results:
            break
    if not all_results:
        return '互联网搜索失败：无法获取搜索结果（查询: ' + query + '）'
    output = ['互联网搜索 "' + query + '" 返回 ' + str(len(all_results)) + ' 条结果：']
    for i, item in enumerate(all_results[:max_results], 1):
        title = item.get('title', '无标题')
        link = item.get('link', '')
        snippet = item.get('snippet', '')
        output.append(str(i) + '. ' + title)
        if link:
            output.append('   来源: ' + link)
        if snippet:
            output.append('   摘要: ' + snippet)
        output.append('')
    return '\n'.join(output)

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
        if tool_name == "write_article":
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
            "name": "view_article",
            "description": "查看文章内容。每次默认读取前3000字符。如果用户要求阅读大文章全文，请分多次调用：先读前3000字符（offset=0,limit=3000），再读下一段（offset=3000,limit=3000），依此类推，直到读完。大多数情况下向量检索已自动注入相关片段到【参考资料】区域，无需调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名，如 '10_中微子集群效应_CN_260626.6.md'。从向量检索结果的文章标签中获取。"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "每次读取的字符数，默认5000。大文章请分批读取，每批5000字符。",
                        "default": 5000
                    },
                    "offset": {
                        "type": "integer",
                        "description": "从第N个字符开始读取（默认0=从头开始）。例如：第一批offset=0，第二批offset=3000，第三批offset=6000。",
                        "default": 0
                    },
                    "section": {
                        "type": "string",
                        "description": "按章节名跳转（推荐方式）。传入章节关键词，如 section='公理3' 会自动定位到包含'公理3'的 ## 或 ### 标题处读取。比用 offset 更精确，不需要知道字符位置。首次读取时会自动显示章节目录和各章节的 offset。"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_articles",
            "description": "列出所有文章的编号、标题和摘要。当你需要了解文章全貌（如查找特定主题的文章、确认文章编号、浏览文章结构）时，优先用此工具而不是逐篇 view_article。返回内容轻量（每篇约1行），不会消耗大量token。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "可选，筛选关键词。如 '应用' 只显示应用篇（编号>=1），'0.8' 只显示 0.8.x 系列，'量子' 只显示标题含量子的文章。留空返回全部。"
                    },
                    "lang": {
                        "type": "string",
                        "description": "可选，语言筛选：'CN' 只显示中文，'EN' 只显示英文，留空显示全部。",
                        "default": "",
                        "enum": ["CN", "EN", ""]
                    }
                },
                "required": []
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
            "name": "edit_article",
            "description": "局部修改文章：指定旧文本和新文本，服务端自动替换。先归档完整原文件，再执行替换。适用于修改已有文章中的若干处措辞、公式、段落，不需要输出整篇文章。支持多次替换（传入数组）。替换完成后自动更新向量索引和 git。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "要修改的文件名，如 '0.3.1_量纲桥_CN_260701.1.md'"
                    },
                    "replacements": {
                        "type": "array",
                        "description": "替换规则列表，每项包含 old_text（要被替换的原始文本，必须精确匹配）和 new_text（替换后的新文本）。原文件中所有出现的位置都会被替换。如果 old_text 在文件中出现多次但你只想替换其中一部分，请在 old_text 中包含足够的上下文以唯一确定位置。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {
                                    "type": "string",
                                    "description": "文件中的原始文本（必须精确匹配，包括空格和换行）"
                                },
                                "new_text": {
                                    "type": "string",
                                    "description": "替换后的新文本"
                                }
                            },
                            "required": ["old_text", "new_text"]
                        }
                    }
                },
                "required": ["filename", "replacements"]
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
            "description": "管理文章的文件操作：归档旧版文章到 archive/ 子目录、查看归档、创建子目录、移动/重命名/删除文件。注意：只在用户明确要求归档/管理文章时才使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["archive", "list_archive", "create_dir", "move", "rename", "delete"],
                        "description": "操作类型：archive(归档到archive/)、list_archive(查看归档)、create_dir(创建子目录)、move(移动到子目录)、rename(重命名文件)、delete(删除文件)"
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
    # ====== 互联网搜索工具 ======
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网上的最新信息。当你需要查找实时新闻、最新研究、网络资料、维基百科内容等，或用户明确要求你搜索互联网时调用此工具。自动搜索 Google 和百度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词，如 '量子计算 2025年最新进展'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回结果数量，默认8条"
                    }
                },
                "required": ["query"]
            }
        }
    },
    # ====== 教学反馈工具 ======
    {
        "type": "function",
        "function": {
            "name": "teach_correction",
            "description": "当你发现之前的回答中有错误或需要纠正时调用。将错误内容和正确内容记录下来，帮助改进后续回答。",
            "parameters": {
                "type": "object",
                "properties": {
                    "wrong": {"type": "string", "description": "之前回答中的错误内容"},
                    "correct": {"type": "string", "description": "纠正后的正确内容"},
                    "reason": {"type": "string", "description": "纠正原因（可选）"},
                    "context": {"type": "string", "description": "对话上下文（可选）"}
                },
                "required": ["wrong", "correct"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "teach_antipattern",
            "description": "标记不应出现的回复模式。例如：AI不应该编造数据、不应该在缺少依据时给出确定结论、不应该忽略文章中的限定条件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "错误模式描述"},
                    "description": {"type": "string", "description": "详细说明为什么这是不好的模式"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"], "description": "严重程度（默认 medium）"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "teach_patch",
            "description": "补充知识补丁。当发现文章库或回答中缺少某个重要知识时调用，记录后后续回答会参考此补丁。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "知识主题"},
                    "content": {"type": "string", "description": "补充的知识内容"},
                    "source": {"type": "string", "description": "知识来源（可选，如文章编号、URL等）"}
                },
                "required": ["topic", "content"]
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


def _cleanup_stale_article(vector_kb, new_filename: str) -> None:
    """
    写入新文章后，清理向量库中同编号前缀（如 '27_'、'0.6.8_'）但不同 fname 的旧版本 chunk。
    例如：写入 27_重子光子比_CN_260626.6.md 时，清理旧的 27_夸克质量谱的几何框架_CN.md 的 chunk。
    """
    if not vector_kb or not vector_kb.is_initialized or not vector_kb.articles_collection:
        return
    import re
    _log = logging.getLogger(__name__)
    try:
        # 从新文件名提取编号前缀（如 '27'、'0.6.8'、'目录'）
        m = re.match(r'^((?:\d+(?:\.\d+)*|[^\d_]{2,}))_', new_filename)
        if not m:
            return
        prefix = m.group(1)

        # 查找向量库中同前缀但不同 fname 的 chunk
        col = vector_kb.articles_collection
        all_meta = col.get(include=['metadatas'])
        stale_fnames = set()
        for meta in all_meta['metadatas']:
            fn = meta.get('fname', '')
            if fn != new_filename:
                m2 = re.match(r'^((?:\d+(?:\.\d+)*|[^\d_]{2,}))_', fn)
                if m2 and m2.group(1) == prefix:
                    stale_fnames.add(fn)

        # 删除旧 fname 的 chunk
        for stale_fn in stale_fnames:
            try:
                col.delete(where={"fname": stale_fn})
                _log.info(f"[VECTOR] 清理旧版本 chunk: {stale_fn} (被 {new_filename} 替代)")
            except Exception as e:
                _log.debug(f"[VECTOR] 清理旧版本失败 {stale_fn}: {e}")
    except Exception as e:
        _log.debug(f"[VECTOR] 清理旧版本检查失败: {e}")


def _article_sort_key(filename: str):
    """按文章编号排序：0.0.1 < 0.1 < 1 < 10 < 目录"""
    import re
    m = re.match(r'^(\d+(?:\.\d+)*)', filename)
    if m:
        parts = [int(x) for x in m.group(1).split('.')]
        return (0, parts, filename)
    return (1, [], filename)


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


def _extract_toc(content: str, filename: str, total: int) -> str:
    """从文章内容中提取章节目录（## 和 ### 标题），附带字符偏移。"""
    import re as _re_toc
    lines = content.split('\n')
    entries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('## ') or stripped.startswith('### '):
            # 计算此行在原文中的字符偏移
            char_offset = sum(len(lines[j]) + 1 for j in range(i))
            entries.append((char_offset, stripped))
    if not entries:
        return ""
    toc_lines = ["【章节目录】（可用 section 参数按章节名跳转，如 section=\"公理\"）"]
    for offset, title in entries[:30]:  # 最多显示 30 个章节
        prefix = "  " if title.startswith("###") else ""
        toc_lines.append(f"{prefix}- {title} (offset={offset})")
    if len(entries) > 30:
        toc_lines.append(f"  ...共 {len(entries)} 个章节")
    return "\n".join(toc_lines)


def _list_articles(arguments: Dict[str, Any]) -> str:
    """
    轻量列出文章编号+标题+摘要。每篇约1行，总消耗约50行。
    filter: 关键词筛选
    lang: CN/EN/空
    """
    import re as _re_la
    articles_dir = os.path.join(UPLOAD_FOLDER) if not os.path.isdir(UPLOAD_FOLDER) else UPLOAD_FOLDER
    if not os.path.isdir(articles_dir):
        return "文章目录不存在"

    filter_kw = arguments.get("filter", "").strip().lower()
    lang_filter = arguments.get("lang", "").strip().upper()

    entries = []
    seen_nums = set()  # 同一编号只取 CN 优先

    for f in sorted(os.listdir(articles_dir)):
        if not f.endswith('.md') or f.startswith('目录_总览') or f.startswith('.') or f.startswith('search_') or f.startswith('hidden_') or f.startswith('Mathematical_') or f.startswith('十方') or f.startswith('README'):
            continue
        m = _re_la.match(r'^([\d.]+)_(.+)_(CN|EN)_[\d.]+\.md$', f)
        if not m:
            continue
        num = m.group(1)
        title_part = m.group(2).replace('_', ' ')
        lang = m.group(3)

        # 语言筛选
        if lang_filter and lang != lang_filter:
            continue

        # 去重：同一编号优先 CN
        if num in seen_nums:
            continue
        if lang_filter != "EN":
            seen_nums.add(num)

        # 关键词筛选
        if filter_kw:
            if filter_kw not in num.lower() and filter_kw not in title_part.lower():
                continue

        # 读取标题（首行）和摘要（第二行或前100字符）
        filepath = os.path.join(articles_dir, f)
        title = title_part
        summary = ""
        try:
            with open(filepath, 'r', encoding='utf-8') as fh:
                first_line = fh.readline().strip()
                if first_line.startswith('# '):
                    title = first_line[2:].strip()
                # 摘要：取第二行到第五行中非空的内容
                for _ in range(4):
                    line = fh.readline().strip()
                    if line and not line.startswith('#') and not line.startswith('|') and not line.startswith('---'):
                        summary = line[:120]
                        break
        except:
            pass

        lang_tag = f"[{lang}] " if lang == "EN" else ""
        entries.append(f"| {num} | {lang_tag}{title} | {summary} |")

    if not entries:
        hint = f"未找到匹配文章 (filter='{filter_kw}', lang='{lang_filter}')。共 {len(os.listdir(articles_dir))} 个文件。"
        return hint

    header = "| 编号 | 标题 | 摘要 |\n|------|------|------|"
    result = header + "\n" + "\n".join(entries)
    result += f"\n\n共 {len(entries)} 篇文章。如需查看具体内容，请用 view_article（默认3000字符/次）。"
    return result


def execute_tool_call(name: str, arguments: Dict[str, Any], vector_kb=None) -> str:
    """执行工具调用并返回结果文本。"""
    try:
        if name == "list_articles":
            return _list_articles(arguments)
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
            limit = int(arguments.get("limit", 5000) or 5000)
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
                    # 提取纯数字编号再匹配（如"3号文章"→"3"，"3(260626.6)"→"3"）
                    if not matches:
                        import re as _re
                        num_match = _re.match(r'^(\d+(?:\.\d+)*)', filename)
                        if num_match:
                            prefix = num_match.group(1)
                            for f in os.listdir(UPLOAD_FOLDER):
                                if f.startswith(prefix + "_"):
                                    matches.append(f)
                    if len(matches) == 1:
                        fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                    elif len(matches) > 1:
                        # 多个匹配，优先选最新版本
                        matches.sort(reverse=True)
                        fpath = os.path.join(UPLOAD_FOLDER, matches[0])
                    else:
                        # 列出所有文件帮助AI选择（按编号智能排序）
                        all_files = sorted(os.listdir(UPLOAD_FOLDER), key=_article_sort_key)
                        # 如果是数字编号搜索，高亮匹配项
                        hint = f"文件 '{filename}' 不存在。共 {len(all_files)} 个文件，按编号排序：\n"
                        return hint + "\n".join(all_files[:50]) + (f"\n...还有 {len(all_files)-50} 个文件" if len(all_files) > 50 else "")
                else:
                    return "文章目录不存在"
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            total = len(content)

            # 新增参数 section：按章节名跳转（自动扫描 ## 标题）
            section_name = arguments.get("section", "").strip()
            if section_name:
                import re as _re_sec
                # 找包含 section_name 的 ## 或 ### 标题行
                for i, line in enumerate(content.split('\n')):
                    if (line.startswith('## ') or line.startswith('### ')) and section_name in line:
                        # 计算该标题的字符偏移
                        offset = content.index(line)
                        # 从该位置开始读 limit 字符
                        section_content = content[offset:offset + (limit or 5000)]
                        if limit and len(section_content) > limit:
                            section_content = section_content[:limit] + "\n...[截断]"
                        # 找下一章节标题位置，提示剩余内容
                        next_section_pos = content.find('\n## ', offset + 10)
                        return f"文件: {filename} (共{total}字符) | 章节: {line.strip()}\n位置: {offset}-{offset+len(section_content)}\n{section_content}"
                return f"未找到包含 '{section_name}' 的章节。\n可用章节：\n" + _extract_toc(content, filename, total)

            # 当 limit=0 且 offset=0 时（首次打开），自动附加章节目录
            # 如果 limit > 0 且 offset == 0，说明是默认 3000 字符读取，也附加目录
            toc = ""
            if (not limit and not offset) or (limit and not offset):
                toc = "\n" + _extract_toc(content, filename, total)

            # 应用offset和limit
            if offset and offset > 0:
                content = content[offset:]
            if limit and limit > 0 and len(content) > limit:
                content = content[:limit] + f"\n...[截断]"
            pos_info = f"位置: {offset}-{min(offset + (limit or total), total)}"
            return f"文件: {filename} (共{total}字符, {pos_info})\n{toc}\n{content}"

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
                # 截断检测：如果原文件 > 100KB，新内容不到原文件的 50%，警告并拒绝
                if os.path.exists(fpath):
                    _old_size = os.path.getsize(fpath)
                    _new_size = len(content.encode('utf-8'))
                    if _old_size > 100000 and _new_size < _old_size * 0.5:
                        return (f"错误：截断保护触发。原文件 {_old_size//1024}KB，"
                                f"新内容仅 {_new_size//1024}KB（不足原文件的 50%）。\n"
                                f"请检查是否需要分段写入（mode=append）。\n"
                                f"如果是小修改，请确认 content 包含完整的文章内容。\n"
                                f"写入已取消，原文件未受影响。")

                # 自动归档旧版（如果同名文件已存在）
                archive_msg = ""
                if os.path.exists(fpath):
                    import shutil as _shutil
                    import time as _time2
                    archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
                    os.makedirs(archive_dir, exist_ok=True)
                    # 始终加时间戳后缀，避免任何覆盖或目录化问题
                    ts = _time2.strftime("%Y%m%d_%H%M%S")
                    stem, ext = os.path.splitext(filename)
                    archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
                    # 用 copy2 + remove 替代 shutil.move（move 在目标已存在时会变成目录）
                    try:
                        _shutil.copy2(fpath, archive_path)
                        os.remove(fpath)
                        archive_msg = f"（旧版已归档到 archive/{stem}_{ts}{ext}）"
                    except Exception as _arch_e:
                        archive_msg = f"（归档失败: {_arch_e}，旧文件仍保留）"
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                # 只索引新写入的文件（增量索引，不重建全部）
                if vector_kb and vector_kb.is_initialized:
                    vector_kb.index_single_file(fpath)
                    # 清理向量库中同 article_id 的旧版本文件 chunk
                    # （当新文件名和旧文件名不同时，index_single_file 不会清理旧的）
                    _cleanup_stale_article(vector_kb, filename)
                # 自动 git commit（版本管理）
                _git_result = _auto_git_commit(filename, content)
                try:
                    preview_host = _request.host
                except RuntimeError:
                    preview_host = "localhost:5000"
                preview_url = f"http://{preview_host}/preview/{filename}"
                return f"已写入 {filename} ({len(content)} 字符)，向量索引已更新。{archive_msg}{_git_result}\n\n【重要】请务必在回复中告诉用户文章已保存，并将以下预览链接以Markdown格式提供给用户：[点击预览文章]({preview_url})"

        elif name == "edit_article":
            # 局部修改文章：先归档完整原文件，再执行替换
            filename = arguments.get("filename", "")
            replacements = arguments.get("replacements", [])
            if not filename:
                return "错误：缺少文件名"
            if not replacements or not isinstance(replacements, list):
                return "错误：缺少 replacements 参数，或格式不正确（需要数组）"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            try:
                fpath = _safe_path(filename)
            except ValueError as e:
                return f"错误：{e}"

            if not os.path.exists(fpath):
                return f"错误：文件 {filename} 不存在，请先用 write_article 创建"

            # 第一步：归档完整原文件
            import shutil as _shutil
            import time as _time2
            archive_dir = os.path.join(UPLOAD_FOLDER, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            ts = _time2.strftime("%Y%m%d_%H%M%S")
            stem, ext = os.path.splitext(filename)
            archive_path = os.path.join(archive_dir, f"{stem}_{ts}{ext}")
            try:
                _shutil.copy2(fpath, archive_path)
                archive_msg = f"（完整原文件已归档到 archive/{stem}_{ts}{ext}）"
            except Exception as _arch_e:
                archive_msg = f"（归档失败: {_arch_e}）"

            # 第二步：读取文件并执行替换
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            except Exception as e:
                return f"错误：读取文件失败: {e}"

            original_size = len(file_content)
            replacement_details = []
            total_chars_added = 0
            total_chars_removed = 0

            for i, rep in enumerate(replacements):
                old_text = rep.get("old_text", "")
                new_text = rep.get("new_text", "")
                if not old_text:
                    replacement_details.append(f"  #{i+1}: 跳过（old_text 为空）")
                    continue
                count = file_content.count(old_text)
                if count == 0:
                    replacement_details.append(f"  #{i+1}: 未找到匹配文本（前50字符: ...{old_text[:50]}...）")
                else:
                    file_content = file_content.replace(old_text, new_text)
                    total_chars_added += len(new_text)
                    total_chars_removed += len(old_text) * count
                    replacement_details.append(f"  #{i+1}: 替换 {count} 处（-{len(old_text)*count}字符 +{len(new_text)*count}字符）")

            # 第三步：写回文件
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(file_content)
            except Exception as e:
                return f"错误：写入文件失败: {e}"

            new_size = len(file_content)

            # 第四步：更新向量索引
            if vector_kb and vector_kb.is_initialized:
                vector_kb.index_single_file(fpath)

            # 第五步：git commit
            _git_result = _auto_git_commit(filename, file_content)

            try:
                preview_host = _request.host
            except RuntimeError:
                preview_host = "localhost:5000"
            preview_url = f"http://{preview_host}/preview/{filename}"

            detail_str = "\n".join(replacement_details)
            size_change = new_size - original_size
            size_str = f"+{size_change}" if size_change >= 0 else str(size_change)
            return (
                f"已修改 {filename}（{original_size} -> {new_size} 字符，{size_str}）。{archive_msg}\n"
                f"替换详情:\n{detail_str}\n"
                f"向量索引已更新。{_git_result}\n\n"
                f"【重要】请务必在回复中告诉用户文章已修改，并将以下预览链接以Markdown格式提供给用户：[点击预览文章]({preview_url})"
            )

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
                            "source": "personal_write",
                            "fname": f"personal_{cat_key}",
                            "article_id": "personal",
                            "start": 0,
                            "end": len(content)
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
                files = sorted(os.listdir(archive_dir), key=_article_sort_key)
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
                # 智能判断：target 以 .md 结尾则为重命名+移动，否则为移动到子目录
                if target.endswith('.md'):
                    # 目标是文件名：重命名（保持在当前目录）
                    target_path = os.path.join(UPLOAD_FOLDER, target)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    _shutil2.move(fpath, target_path)
                    # 更新向量索引中的文件名引用
                    try:
                        vector_kb = getattr(sys.modules.get('knowledge'), 'vector_kb', None)
                        if vector_kb:
                            vector_kb.update_filename_in_metadata(filename, target)
                    except Exception:
                        pass
                    return f"已重命名: {filename} -> {target}"
                else:
                    # 目标是目录名：移动到子目录
                    target_dir = os.path.join(UPLOAD_FOLDER, target)
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, os.path.basename(filename))
                    _shutil2.move(fpath, target_path)
                    return f"已移动: {filename} -> {target}/"

            elif action == "rename":
                if not filename or not target:
                    return "错误：缺少文件名和新名称"
                try:
                    fpath = _safe_path(filename)
                    new_path = _safe_path(target)
                except ValueError as e:
                    return f"错误：{e}"
                if not os.path.exists(fpath):
                    return f"文件 '{filename}' 不存在"
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                _shutil2.move(fpath, new_path)
                # 更新向量索引：删除旧文件名的 chunk，重建新文件名的 chunk
                index_msg = ""
                if vector_kb and vector_kb.is_initialized:
                    try:
                        # 先删除旧 fname 的所有 chunk
                        vector_kb.articles_collection.delete(where={"fname": filename})
                        # 再对新文件做增量索引
                        vector_kb.index_single_file(new_path)
                        index_msg = "，向量索引已更新"
                    except Exception as _idx_e:
                        index_msg = f"，向量索引更新失败: {_idx_e}"
                return f"已重命名: {filename} -> {target}{index_msg}"

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
                # 同步删除向量索引
                if vector_kb and vector_kb.is_initialized:
                    try:
                        vector_kb.articles_collection.delete(where={"fname": filename})
                        vector_kb._articles_count = vector_kb.articles_collection.count()
                    except Exception:
                        pass
                return f"已删除: {filename}，向量索引已同步"

            else:
                return f"未知操作: {action}，支持: archive/list_archive/create_dir/move/rename/delete"

        # ====== 互联网搜索 ======
        elif name == "web_search":
            query = arguments.get("query", "")
            max_results = int(arguments.get("max_results", 8))
            if not query:
                return "错误：缺少搜索查询词"
            result = web_search(query, max_results)
            return result

        # ====== 教学反馈工具 ======
        elif name == "teach_correction":
            if not teaching_system:
                return "教学系统未初始化"
            wrong = arguments.get("wrong", "")
            correct = arguments.get("correct", "")
            reason = arguments.get("reason", "")
            context = arguments.get("context", "")
            result = teaching_system.add_correction(
                wrong=wrong, correct=correct, reason=reason, context=context
            )
            if result["success"]:
                return f"已记录纠正：将\"{wrong[:50]}\"纠正为\"{correct[:50]}\""
            return f"纠正记录失败: {result.get('error', '未知错误')}"

        elif name == "teach_antipattern":
            if not teaching_system:
                return "教学系统未初始化"
            pattern = arguments.get("pattern", "")
            description = arguments.get("description", "")
            severity = arguments.get("severity", "medium")
            result = teaching_system.add_antipattern(
                pattern=pattern, description=description, severity=severity
            )
            if result["success"]:
                return f"已记录反模式（{severity}）：{pattern[:80]}"
            return f"反模式记录失败: {result.get('error', '未知错误')}"

        elif name == "teach_patch":
            if not teaching_system:
                return "教学系统未初始化"
            topic = arguments.get("topic", "")
            content = arguments.get("content", "")
            source = arguments.get("source", "")
            result = teaching_system.add_patch(
                topic=topic, content=content, source=source
            )
            if result["success"]:
                return f"已记录知识补丁：{topic[:60]}"
            return f"知识补丁记录失败: {result.get('error', '未知错误')}"

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
        }
    }
}
