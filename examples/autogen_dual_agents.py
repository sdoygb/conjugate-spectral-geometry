"""
AutoGen 双智能体 — Writer / Reviewer 循环（双接口，对话可见 + 自动成文）

研究者（Writer）  → 本地中间层 http://127.0.0.1:5000/v1（deepseek-v4-pro）
                     走共扼谱几何调度中间层：知识库注入、质量门控、工具调度
审核者（Reviewer）→ DeepSeek 官方直连 https://api.deepseek.com/v1（deepseek-v4-flash）
                     轻量模型，快速审阅

特性：
- 对话实时打印到终端，同时完整保存到 logs/autogen_dual_conversation_<时间戳>.md
- 对话结束后自动把成果文章写入 app/articles/ 根目录（自动编号，遵循库命名规范）

用法:
    app/.venv/bin/python examples/autogen_dual_agents.py
    app/.venv/bin/python examples/autogen_dual_agents.py --turns 4
    app/.venv/bin/python examples/autogen_dual_agents.py --prefix 0.
"""
import argparse
import asyncio
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dotenv import load_dotenv

_ENV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "app", ".env"
)
load_dotenv(_ENV_PATH, override=True)

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

API_KEY = os.getenv("GAI_API_KEY", "")
OFFICIAL_BASE_URL = os.getenv("GAI_BASE_URL", "https://api.deepseek.com/v1")
MIDDLE_BASE_URL = os.getenv("GAI_MIDDLE_BASE_URL", "http://127.0.0.1:5000/v1")
MODEL_FULL = os.getenv("GAI_MODEL", "deepseek-v4-pro")
MODEL_LITE = os.getenv("GAI_MODEL_LITE", "deepseek-v4-flash")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "app", "articles")
LOGS_DIR = os.path.join(ARTICLES_DIR, "logs")

if not API_KEY:
    sys.exit("未找到 GAI_API_KEY，请先在 app/.env 中配置")


def build_model_client(base_url: str, model: str, subagent: bool = False):
    """构造 OpenAI 兼容客户端；中间层不需要真实 key，但传上无妨"""
    kwargs = dict(
        model=model,
        api_key=API_KEY,
        base_url=base_url,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "structured_output": False,
            "family": "deepseek",
        },
    )
    # 子代理标记：让中间层跳过工具注入（识别 X-GAI-MODE header）
    if subagent:
        kwargs["default_headers"] = {"X-GAI-MODE": "subagent"}
    return OpenAIChatCompletionClient(**kwargs)


def next_article_number(prefix: str) -> str:
    """扫描 app/articles/ 根目录，返回下一个可用编号，如 10.30"""
    max_n = 0
    if os.path.isdir(ARTICLES_DIR):
        for name in os.listdir(ARTICLES_DIR):
            m = re.match(rf"^{re.escape(prefix)}(\d+)_", name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1}"


def save_article(title: str, writer_final: str, transcript: list, prefix: str, number: int = None):
    """把成果文章写入 app/articles/ 根目录，返回 (完整路径, 文件名)"""
    number = next_article_number(prefix) if number is None else f"{prefix}{number}"
    date = datetime.datetime.now().strftime("%y%m%d")
    filename = f"{number}_{title}_CN_{date}.md"
    path = os.path.join(ARTICLES_DIR, filename)

    header = (
        f"# {title}\n\n"
        f"> 本文由 AutoGen 双智能体协作产出："
        f"Writer（研究者，中间层 {MODEL_FULL}）与 Reviewer（审核者，{MODEL_LITE} 直连）"
        f"经 {len(transcript)} 轮对话后定稿。\n\n"
        f"---\n\n"
    )
    body = writer_final.strip() + "\n"
    # 归一化 LaTeX 定界符：库内规范为 $$...$$（行间）与 $...$（行内），
    # 预览页 KaTeX 只渲染这两种；模型输出的 \[...\] / \(...\) 需转换。
    body = (body.replace("\\[", "$$")
                .replace("\\]", "$$")
                .replace("\\(", "$")
                .replace("\\)", "$"))
    # 预览页渲染器不支持 blockquote，去掉行首 "> "（引用块转普通段落）
    body = "\n".join(l[2:] if l.startswith("> ") else l for l in body.split("\n"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + body)
    return path, filename


async def main() -> None:
    parser = argparse.ArgumentParser(description="AutoGen 双智能体协作")
    parser.add_argument("--turns", type=int, default=6, help="总发言次数（默认6）")
    parser.add_argument("--prefix", default="10.", help="文章编号前缀（默认10.应用篇）")
    parser.add_argument("--number", type=int, default=None, help="显式文章编号（跳过自动分配，用于并发任务）")
    parser.add_argument("--topic", default=None, help="研究任务文本；以@开头时从文件读取")
    parser.add_argument("--title", default=None, help="成果文章标题（默认SE锁定的谱刚性本质）")
    args = parser.parse_args()
    if args.topic and args.topic.startswith("@"):
        with open(args.topic[1:], encoding="utf-8") as _f:
            args.topic = _f.read()

    # 研究者走中间层（知识库注入 + 质量门控），审核者直连官方轻量模型
    writer_client = build_model_client(MIDDLE_BASE_URL, MODEL_FULL, subagent=True)
    reviewer_client = build_model_client(OFFICIAL_BASE_URL, MODEL_LITE)

    # ---- 智能体 1：撰稿者（研究者，走中间层） ----
    writer = AssistantAgent(
        name="Writer",
        model_client=writer_client,
        system_message=(
            "你是共扼谱几何理论的研究者，写作风格严谨简洁。"
            "收到任务后直接给出你的分析，不要客套。"
            "你的最终回复将成为正式文章正文，请以完整、自洽的论述收尾。"
        ),
    )

    # ---- 智能体 2：审阅者（严格把关，官方轻量模型） ----
    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=reviewer_client,
        system_message=(
            "你是共扼谱几何理论的严格审阅者。"
            "审阅 Writer 的产出时：指出推导漏洞、未说明的假设、术语不严谨之处；"
            "如果发现实质问题，明确列出需要修改的点；"
            "如果认为产出合格，直接回复『通过』并给出简短结论。"
        ),
    )

    team = RoundRobinGroupChat([writer, reviewer], max_turns=args.turns)

    task = args.topic or (
        "用几何直觉解释：为什么 S_e 锁定的本质是谱的刚性约束，"
        "而不是单纯的参数拟合？请给出你的论证。"
    )
    title = args.title or "SE锁定的谱刚性本质"

    print(f"=== 任务：{task} ===", flush=True)
    print(f"Writer    → 中间层 {MIDDLE_BASE_URL} ({MODEL_FULL})", flush=True)
    print(f"Reviewer  → 官方直连 {OFFICIAL_BASE_URL} ({MODEL_LITE})", flush=True)
    print(f"总发言次数 → {args.turns}（实时打印中…）\n", flush=True)

    # ---- 实时对话：打印 + 收集 ----
    transcript = []  # [(speaker, content)]
    async for event in team.run_stream(task=task):
        if isinstance(event, TextMessage) and event.source != "user":
            speaker, content = event.source, event.content
            print(f"\n{'=' * 72}\n【{speaker}】\n{'=' * 72}\n{content}\n", flush=True)
            transcript.append((speaker, content))
        elif isinstance(event, TaskResult):
            print("\n=== 对话结束 ===", flush=True)

    # ---- 1. 保存完整对话记录（logs/） ----
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs(LOGS_DIR, exist_ok=True)
    conv_path = os.path.join(LOGS_DIR, f"autogen_dual_conversation_{ts}.md")
    with open(conv_path, "w", encoding="utf-8") as f:
        f.write(f"# AutoGen 双智能体对话记录（{ts}）\n\n")
        f.write(f"- 任务：{task}\n")
        f.write(f"- Writer → 中间层 {MIDDLE_BASE_URL} ({MODEL_FULL})\n")
        f.write(f"- Reviewer → 官方直连 {OFFICIAL_BASE_URL} ({MODEL_LITE})\n\n")
        for speaker, content in transcript:
            f.write(f"## {speaker}\n\n{content}\n\n")
    print(f"\n✅ 对话记录已保存：{conv_path}", flush=True)

    # ---- 2. 生成文章，写入 articles 根目录 ----
    writer_msgs = [c for s, c in transcript if s == "Writer" and c and c.strip()]
    if writer_msgs:
        path, filename = save_article(title, writer_msgs[-1], transcript, args.prefix, args.number)
        print(f"✅ 文章已生成：{path}", flush=True)
        print(f"   文件名：{filename}（编号自动分配）", flush=True)
    else:
        print("⚠️ 未捕获到 Writer 的回复，跳过文章生成", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
