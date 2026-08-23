#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""子AI 自动圆满判定 Worker（接入对话主流程，进程级后台轮询）。

背景：主库 LLM 于 2026-08-05 退役后，入库判据移交子AI执行。凡进入
`awaiting_child_judge` 的候选公式，主库只等子AI回传圆满判定，若不判就永久挂起。

本模块周期性做三件事：
  1) list   —— 轮询主库 awaiting_child_judge 的候选公式
  2) show   —— 拉取完整判定材料（公式内容 + 机械检查 + 依赖核对）
  3) judge  —— 交子AI LLM（带工具）做出圆满意语义判定，回写主库

全部通过子进程调用 master_ai/child_judge.py，把主库数据库操作留在主库自己的
进程/解释器里执行，避免子AI进程直接双开主库 Chroma 造成锁冲突或配置污染。

默认 dry_run=True：只计算判定并打印"将要写入的内容"，不真库；设置环境变量
CHILD_AUTO_JUDGE_REAL=1 才真正回写。CHILD_AUTO_JUDGE=0 完全关闭本 worker。
"""
from __future__ import annotations
import os
import re
import sys
import json
import time
import logging
import subprocess
import threading
from datetime import datetime  # noqa: F401
from typing import Callable, Dict, List, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJ_DIR = os.path.dirname(_THIS_DIR)
MASTER_CLI = os.path.join(_PROJ_DIR, "master_ai", "child_judge.py")
# 默认用子AI自身解释器；主库运行时同是 python3.11，可正常 import master_ai 依赖
PYTHON = os.environ.get("MASTER_PYTHON") or sys.executable

# verdict 白名单（可安全回写主库）
V_VERDICTS = {"promote", "reject", "dependency_gap"}
V_LEVELS = {"初圆满", "中圆满", "上圆满", ""}


_logger = logging.getLogger("child_judge_worker")


def _log(msg: str) -> None:
    _logger.info(f"[CHILD-JUDGE] {msg}")


def _run_cli(args: List[str], timeout: int = 300) -> str:
    """子进程执行 child_judge.py，返回 stdout。

    关键：清掉 PYTHONHOME/PYTHONPATH 污染（与 start-middleware.sh 同理），
    否则 python3.11 会 init_fs_encoding 失败（No module named 'encodings'）。
    """
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    full = [PYTHON, MASTER_CLI] + args
    _log("shell: " + " ".join(full))
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout,
                       env=env, cwd=_PROJ_DIR)
    if r.returncode != 0:
        raise RuntimeError(f"child_judge.py 失败 rc={r.returncode}: {r.stderr.strip()[:500]}")
    return r.stdout


def list_awaiting() -> List[Dict[str, str]]:
    """返回所有 awaiting_child_judge 的候选公式。

    直接按"16位十六进制提交ID 行"匹配，忽略日志前缀/分隔线等噪音。
    """
    out = _run_cli(["list"], timeout=120)
    items: List[Dict[str, str]] = []
    for line in out.splitlines():
        m = re.match(r"^\s*([0-9a-f]{12,})\s*\|\s*(.+?)\s*\|\s*berry=", line)
        if m:
            items.append({"submission_id": m.group(1), "formula_name": m.group(2).strip()})
    return items


def show_material(sid: str) -> str:
    """拉取单条候选的完整判定材料。"""
    return _run_cli(["show", sid], timeout=180)


def commit(sid: str, verdict: str, level: str, reason: str, judge: str) -> Dict:
    """回写判定到主库，返回结构化结果。"""
    args = ["judge", sid, "--verdict", verdict, "--reason", reason, "--judge", judge]
    if level:
        args += ["--level", level]
    out = _run_cli(args, timeout=300)
    return {"sid": sid, "verdict": verdict, "level": level, "reason": reason,
            "output": out.strip(), "ok": bool(out.strip())}


def judge_one(sid: str, run_llm: Callable[[str], Dict], dry_run: bool,
              judge: str = "sub_ai_auto") -> Dict:
    """对单条候选执行"拉材料 → LLM 判定 → 回写"。"""
    material = show_material(sid)
    decision = run_llm(material or sid)  # 子AI LLM 带工具做出圆满语义判定
    verdict = str(decision.get("verdict", "keep_pending"))
    level = str(decision.get("level", ""))
    reason = str(decision.get("reason", "")).strip()[:600]

    if verdict not in V_VERDICTS:
        _log(f"{sid}: LLM 产出 {verdict}，跳过（保持待判定）")
        return {"sid": sid, "verdict": verdict, "skipped": True}
    if not reason:
        _log(f"{sid}: LLM 判定 {verdict} 但无理由，跳过（保持待判定）")
        return {"sid": sid, "verdict": verdict, "skipped": True}
    if verdict == "promote" and level not in V_LEVELS:
        _log(f"{sid}: promote 需合法圆满级别，当前 level={level!r}，跳过")
        return {"sid": sid, "verdict": verdict, "skipped": True}

    _log(f"{sid}: 拟判定 verdict={verdict} level={level!r} reason={reason[:80]} ...")
    if dry_run:
        return {"sid": sid, "verdict": verdict, "level": level, "reason": reason,
                "dry_run": True}
    return commit(sid, verdict, level, reason, judge)


def _worker_loop(run_llm: Callable[[str], Dict], interval: float, dry_run: bool,
                 stop_flag: threading.Event):
    handled: set = set()
    _log(f"worker 启动 interval={interval}s dry_run={dry_run}")
    while not stop_flag.is_set():
        try:
            awaiting = list_awaiting()
        except Exception as e:
            _log(f"轮询主库失败：{e}，{interval*2}s 后重试")
            time.sleep(interval * 2)
            continue
        if not awaiting:
            _log("没有 awaiting_child_judge，空闲")
        else:
            _log(f"发现 {len(awaiting)} 条待判定")
        for item in awaiting:
            if stop_flag.is_set():
                break
            sid = item["submission_id"]
            if sid in handled:
                continue
            try:
                res = judge_one(sid, run_llm, dry_run)
                if res.get("dry_run"):
                    _log(f"[DRY] {sid} 将写入 → {res['verdict']} ({res.get('level')}) {res['reason'][:60]}")
                elif res.get("verdict") != "keep_pending":
                    _log(f"[COMMIT] {sid} 已完成：{res.get('output', '')[:120]}")
            except Exception as e:
                _log(f"{sid} 判定异常：{e}")
            finally:
                handled.add(sid)
        time.sleep(interval)


_STOP = threading.Event()


def start_worker(run_llm: Callable[[str], Dict], interval: float = 240.0,
                 dry_run: Optional[bool] = None) -> Optional[threading.Thread]:
    """启动后台判定 worker（幂等）。返回线程；被禁用时返回 None。"""
    env_on = os.environ.get("CHILD_AUTO_JUDGE", "1")
    if env_on == "0":
        _log("CHILD_AUTO_JUDGE=0，worker 关闭")
        return None
    if dry_run is None:
        # 默认 dry_run=True（安全）；仅当 CHILD_AUTO_JUDGE_REAL=1 才真正写库
        real = os.environ.get("CHILD_AUTO_JUDGE_REAL", "0") == "1"
        dry_run = not real
    if not dry_run:
        _log("⚠ 真实模式已开启（CHILD_AUTO_JUDGE_REAL=1），判定将实际写入主库")
    t = threading.Thread(
        target=_worker_loop, args=(run_llm, interval, dry_run, _STOP), daemon=True,
        name="child-judge-worker",
    )
    t.start()
    return t