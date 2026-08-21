#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推导会话（中间层程序）：推导过程数据全内存自动暂存。

推导工作流（derive.DerivationFlow）在每个关键步骤自动调用本模块：
- 建台、验证器结果（含死胡同/失败）、横向比较快照、收敛判据、反向审计
  自动写入会话 rounds（可关联线）；收敛结论自动归档为 artifacts（定理草稿）。
- 全部数据在内存对象里；finalize() 才写盘快照（重启可恢复）。
- 推导者无需手动调用：推导即自动记录（多轮对话多次推导自动累积到同一会话，
  会话 id = 工作台 id）。
"""
from __future__ import annotations

import datetime
import glob
import json
import os
from typing import Dict, List, Optional

_STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DerivationSession:
    """推导会话：多轮推导的过程数据全内存暂存。

    一次推导（可能跨二三十轮对话）产生的中间文字、定理草稿、数值、
    5 线推进记录，全部保留在内存对象里；finalize() 之前不碰磁盘。
    """

    def __init__(self, sid: str, title: str, target: str = "",
                 anchors: Optional[List[str]] = None):
        self.id = sid
        self.title = title
        self.target = target
        self.anchors = anchors or []
        self.rounds: List[dict] = []        # 每轮产出：{round,ts,line_id,kind,content}
        self.artifacts: List[dict] = []     # 定理/公式/表格草稿：{name,ts,content}
        self.workbench_id: Optional[str] = None  # 关联的 5 线工作台
        self.finalized = False

    def add_round(self, content: str, line_id: str = "", kind: str = "推导") -> dict:
        r = {"round": len(self.rounds) + 1, "ts": _now(), "line_id": line_id,
             "kind": kind, "content": content}
        self.rounds.append(r)
        return r

    def add_artifact(self, name: str, content: str) -> dict:
        a = {"name": name, "ts": _now(), "content": content}
        self.artifacts.append(a)
        return a

    def link(self, workbench_id: str) -> None:
        self.workbench_id = workbench_id

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "target": self.target,
                "anchors": self.anchors, "rounds": self.rounds,
                "artifacts": self.artifacts, "workbench_id": self.workbench_id,
                "finalized": self.finalized}

    def summary(self) -> dict:
        return {"id": self.id, "title": self.title,
                "rounds": len(self.rounds), "artifacts": len(self.artifacts),
                "workbench_id": self.workbench_id, "finalized": self.finalized}


class SessionStore:
    """推导会话注册表（进程级单例，全内存）。

    启动时从 state/sessions/ 载入已 finalize 的会话快照；
    之后所有推导过程数据全内存，finalize() 才写盘。
    """

    _instance: Optional["SessionStore"] = None

    def __init__(self, state_dir: str = _STATE_DIR):
        self._state_dir = state_dir
        self._sessions: Dict[str, DerivationSession] = {}

    @classmethod
    def instance(cls) -> "SessionStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_all(self) -> int:
        """启动预热：载入已落盘的会话快照。返回数量。"""
        n = 0
        d = os.path.join(self._state_dir, "sessions")
        os.makedirs(d, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            sid = os.path.splitext(os.path.basename(f))[0]
            try:
                data = json.load(open(f, encoding="utf-8"))
                s = DerivationSession(data["id"], data.get("title", sid),
                                      data.get("target", ""), data.get("anchors", []))
                s.rounds = data.get("rounds", [])
                s.artifacts = data.get("artifacts", [])
                s.workbench_id = data.get("workbench_id")
                s.finalized = data.get("finalized", True)
                self._sessions[sid] = s
                n += 1
            except Exception:
                pass
        return n

    def create(self, sid: str, title: str, target: str = "",
               anchors: Optional[List[str]] = None) -> DerivationSession:
        s = DerivationSession(sid, title, target, anchors)
        self._sessions[sid] = s
        return s

    def get(self, sid: str) -> Optional[DerivationSession]:
        return self._sessions.get(sid)

    def list(self) -> List[dict]:
        return sorted((s.summary() for s in self._sessions.values()),
                      key=lambda d: d["id"])

    def finalize(self, sid: str) -> str:
        """收敛完成：一次性写盘快照（内存仍为权威）。"""
        s = self._sessions.get(sid)
        if s is None:
            raise KeyError(sid)
        d = os.path.join(self._state_dir, "sessions")
        os.makedirs(d, exist_ok=True)
        s.finalized = True
        p = os.path.join(d, f"{sid}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(s.to_dict(), f, ensure_ascii=False, indent=1)
        return p

    def memory_stats(self) -> dict:
        mb = 0.0
        for s in self._sessions.values():
            try:
                mb += len(json.dumps(s.to_dict(), ensure_ascii=False)) * 2 / 1e6
            except Exception:
                pass
        return {"sessions": len(self._sessions), "sessions_mb": round(mb, 3)}
