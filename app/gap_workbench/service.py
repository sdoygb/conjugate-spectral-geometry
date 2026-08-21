"""工作台常驻服务：全内存注册表 + Flask 蓝图（中间层程序）。

全内存运作模式：
- 启动时（server.py main）调用 WorkbenchRegistry.get().load_all()：
  把 state/ 目录下全部工作台载入内存，之后推导/比较/审计/报告全部在内存完成。
- save 仅用于持久化写回（磁盘不是读取来源）。
- 重启电脑 → 启动服务 → 自动全量载入 → 打开即用。

API（挂载于 /api/workbench）：
  POST /api/workbench/derive   一键推导：建台→5线→验证器→比较→收敛→审计→报告（全内存）
  GET  /api/workbench          内存中全部工作台列表
  GET  /api/workbench/<id>     单台状态 + 横向比较
  POST /api/workbench/<id>/converge  收敛判据
  POST /api/workbench/<id>/audit     反向审计
  GET  /api/workbench/<id>/report    Markdown 报告
  POST /api/workbench/<id>/save     持久化写回磁盘

推导会话（过程数据全内存暂存，finalize 才写盘）：
  POST /api/workbench/session                 开新推导会话（内存）
  POST /api/workbench/session/<sid>/round     记录一轮推导产出（文字/数值，可关联线）
  POST /api/workbench/session/<sid>/artifact  记录定理/公式/表格草稿
  POST /api/workbench/session/<sid>/link      关联 5 线工作台
  GET  /api/workbench/session/<sid>           查看完整推导过程（内存）
  GET  /api/workbench/session                 会话列表
  POST /api/workbench/session/<sid>/finalize  收敛完成，一次性写盘快照
"""
from __future__ import annotations

import glob
import json
import os
from typing import Dict, List, Optional

from .workbench import Workbench
from .derive import DerivationFlow
from .session import DerivationSession, SessionStore, _now

_STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


class WorkbenchRegistry:
    """全内存工作台注册表（进程级单例）。

    所有工作台状态常驻内存；磁盘 state/*.json 只用于启动载入与写回持久化。
    """

    _instance: Optional["WorkbenchRegistry"] = None

    def __init__(self, state_dir: str = _STATE_DIR):
        self._state_dir = state_dir
        self._workspaces: Dict[str, Workbench] = {}

    @classmethod
    def instance(cls) -> "WorkbenchRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ---------- 生命周期 ----------
    def load_all(self) -> int:
        """启动预热：把 state/ 下全部工作台载入内存。返回载入数量。"""
        n = 0
        os.makedirs(self._state_dir, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(self._state_dir, "*.json"))):
            gid = os.path.splitext(os.path.basename(f))[0]
            try:
                self._workspaces[gid] = Workbench.load(f)
                n += 1
            except Exception:
                pass
        return n

    def save(self, gap_id: str) -> str:
        """持久化写回磁盘（内存是权威，磁盘是快照）。"""
        wb = self._workspaces.get(gap_id)
        if wb is None:
            raise KeyError(gap_id)
        p = os.path.join(self._state_dir, f"{gap_id}.json")
        wb.save(p)
        return p

    def save_all(self) -> int:
        n = 0
        for gid in list(self._workspaces):
            try:
                self.save(gid)
                n += 1
            except Exception:
                pass
        return n

    # ---------- 操作（全内存） ----------
    def create(self, gap_id: str, title: str, anchors: List[str], target: str,
               gap_type: str = "DERIVATION", use_template: bool = True) -> Workbench:
        flow = DerivationFlow.create_task(gap_id, title, anchors, target, gap_type, use_template)
        self._workspaces[gap_id] = flow.wb
        return flow.wb

    def get(self, gap_id: str) -> Optional[Workbench]:
        return self._workspaces.get(gap_id)

    def list(self) -> List[dict]:
        out = []
        for gid, wb in self._workspaces.items():
            g = wb.gap
            out.append({
                "id": gid,
                "title": g.title,
                "converged": g.converged,
                "lines": len(g.lines),
                "closed": sum(1 for l in g.lines if l.status == "CLOSED"),
                "dead": sum(1 for l in g.lines if l.status == "DEAD"),
            })
        return sorted(out, key=lambda d: d["id"])

    def memory_stats(self) -> dict:
        """全内存占用统计（估算，MB）。"""
        mb = 0.0
        for wb in self._workspaces.values():
            try:
                mb += len(json.dumps(wb.to_dict(), ensure_ascii=False)) * 2 / 1e6
            except Exception:
                pass
        return {"workspaces": len(self._workspaces), "state_mb": round(mb, 3)}

    def run_derivation(self, gap_id: str, title: str, anchors: List[str], target: str,
                       verifiers: Optional[Dict] = None, conclude: str = "",
                       chain: Optional[List[str]] = None, support: Optional[List[str]] = None,
                       audit_now: bool = True) -> dict:
        """一键推导（全内存）：建台 → 5线 → 验证器自动执行 → 横向比较 → 收敛 → 审计 → 报告。"""
        wb = self.create(gap_id, title, anchors, target)
        flow = DerivationFlow(wb)
        vout = flow.run_verifiers(verifiers or {})
        cmp = flow.compare()
        check = None
        if conclude:
            check = flow.converge(conclude, chain or [], support)
        items, stats = ([], {}) if not audit_now else flow.audit()
        md = flow._build_report_md()
        self.save(gap_id)  # 持久化快照（内存仍为权威）
        # 自动会话：全流程过程数据已在内存（derive 内嵌记录）；收敛成功才归档写盘
        session = SessionStore.instance().get(gap_id)
        if check and check.get("ok"):
            try:
                flow.finalize_session()
            except Exception:
                pass
        return {
            "id": gap_id,
            "verifiers": vout,
            "compare": cmp,
            "converge": check,
            "audit_stats": stats,
            "report_md": md,
            "session": session.summary() if session else None,
            "state_path": os.path.join(self._state_dir, f"{gap_id}.json"),
        }




def _make_blueprint():
    from flask import Blueprint, jsonify, request

    bp = Blueprint("workbench", __name__, url_prefix="/api/workbench")
    reg = WorkbenchRegistry.instance()

    @bp.post("/derive")
    def api_derive():
        data = request.get_json(force=True, silent=True) or {}
        gid = data.get("id", "")
        if not gid:
            return jsonify({"error": "缺少 id"}), 400
        try:
            result = reg.run_derivation(
                gid,
                data.get("title", gid),
                data.get("anchors", []),
                data.get("target", ""),
                data.get("verifiers"),
                data.get("conclude", ""),
                data.get("chain"),
                data.get("support"),
                audit_now=data.get("audit", True),
            )
            return jsonify({"ok": True, **result})
        except Exception as ex:
            return jsonify({"ok": False, "error": str(ex)}), 500

    @bp.get("")
    def api_list():
        return jsonify({"ok": True, "workspaces": reg.list(),
                        "memory": reg.memory_stats()})

    @bp.get("/<gid>")
    def api_get(gid):
        wb = reg.get(gid)
        if wb is None:
            return jsonify({"error": f"工作台 {gid} 不在内存（未载入）"}), 404
        flow = DerivationFlow(wb)
        return jsonify({"ok": True, "id": gid, "title": wb.gap.title,
                        "converged": wb.gap.converged,
                        "compare": flow.compare()})

    @bp.post("/<gid>/converge")
    def api_converge(gid):
        wb = reg.get(gid)
        if wb is None:
            return jsonify({"error": "不在内存"}), 404
        data = request.get_json(force=True, silent=True) or {}
        flow = DerivationFlow(wb)
        check = flow.converge(data.get("conclusion", ""),
                              data.get("chain", []),
                              data.get("support"))
        reg.save(gid)
        if check.get("ok"):
            try:
                flow.finalize_session()
            except Exception:
                pass
        return jsonify({"ok": True, "converge": check})

    @bp.post("/<gid>/audit")
    def api_audit(gid):
        wb = reg.get(gid)
        if wb is None:
            return jsonify({"error": "不在内存"}), 404
        items, stats = DerivationFlow(wb).audit()
        reg.save(gid)
        return jsonify({"ok": True,
                        "items": [{"link": i.link, "status": i.status,
                                   "evidence": i.evidence} for i in items],
                        "stats": stats})

    @bp.get("/<gid>/report")
    def api_report(gid):
        wb = reg.get(gid)
        if wb is None:
            return jsonify({"error": "不在内存"}), 404
        return jsonify({"ok": True, "report_md": DerivationFlow(wb)._build_report_md()})

    @bp.post("/<gid>/save")
    def api_save(gid):
        try:
            p = reg.save(gid)
            return jsonify({"ok": True, "path": p})
        except KeyError:
            return jsonify({"error": "不在内存"}), 404


    # ---------- 推导会话（过程数据全内存暂存） ----------
    store = SessionStore.instance()

    @bp.post("/session")
    def api_session_create():
        data = request.get_json(force=True, silent=True) or {}
        sid = data.get("id", "")
        if not sid:
            return jsonify({"error": "缺少 id"}), 400
        if store.get(sid) is not None:
            return jsonify({"ok": True, "session": store.get(sid).summary()})
        s = store.create(sid, data.get("title", sid), data.get("target", ""),
                         data.get("anchors"))
        return jsonify({"ok": True, "session": s.summary()})

    @bp.get("/session")
    def api_session_list():
        return jsonify({"ok": True, "sessions": store.list(),
                        "memory": store.memory_stats()})

    @bp.post("/session/<sid>/round")
    def api_session_round(sid):
        s = store.get(sid)
        if s is None:
            return jsonify({"error": f"会话 {sid} 不在内存"}), 404
        data = request.get_json(force=True, silent=True) or {}
        if not data.get("content"):
            return jsonify({"error": "缺少 content"}), 400
        r = s.add_round(data["content"], data.get("line_id", ""), data.get("kind", "推导"))
        return jsonify({"ok": True, "round": r})

    @bp.post("/session/<sid>/artifact")
    def api_session_artifact(sid):
        s = store.get(sid)
        if s is None:
            return jsonify({"error": f"会话 {sid} 不在内存"}), 404
        data = request.get_json(force=True, silent=True) or {}
        if not data.get("name") or not data.get("content"):
            return jsonify({"error": "缺少 name/content"}), 400
        a = s.add_artifact(data["name"], data["content"])
        return jsonify({"ok": True, "artifact": a})

    @bp.post("/session/<sid>/link")
    def api_session_link(sid):
        s = store.get(sid)
        if s is None:
            return jsonify({"error": f"会话 {sid} 不在内存"}), 404
        data = request.get_json(force=True, silent=True) or {}
        wid = data.get("workbench_id", "")
        if wid and reg.get(wid) is None:
            return jsonify({"error": f"工作台 {wid} 不在内存"}), 404
        s.link(wid)
        return jsonify({"ok": True, "session": s.summary()})

    @bp.get("/session/<sid>")
    def api_session_get(sid):
        s = store.get(sid)
        if s is None:
            return jsonify({"error": f"会话 {sid} 不在内存"}), 404
        return jsonify({"ok": True, "session": s.to_dict()})

    @bp.post("/session/<sid>/finalize")
    def api_session_finalize(sid):
        try:
            p = store.finalize(sid)
            return jsonify({"ok": True, "path": p})
        except KeyError:
            return jsonify({"error": f"会话 {sid} 不在内存"}), 404

    return bp


workbench_bp = _make_blueprint()
