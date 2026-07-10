"""
server.py — 主库AI API服务

提供以下端点：
  POST /v1/master/submit    — 本地 Agent 提交候选公式
  POST /v1/master/verify    — 触发验证（可指定 submission_id）
  GET  /v1/master/status    — 查看主库状态
  GET  /v1/master/truth     — 获取真理层快照（反哺）
  GET  /v1/master/pending   — 列出待验证公式
  GET  /v1/master/formula/:id — 查看已验证公式详情

内置自动验证调度器：
  后台线程定期检查 pending 队列，按提交顺序自动验证。
  提交后无需手动触发，主库自动有序处理。

启动方式：
  cd master_ai
  python server.py
"""
import os
import sys
import json
import time
import threading
from typing import Dict, Any, List

# 确保自身目录在 path 中
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from config import (
    logger,
    MASTER_AI_PORT,
    MASTER_AI_TOKEN,
)
from master_db import MasterDatabase
from verifier import MasterVerifier

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.error("[SERVER] Flask 未安装，API服务不可用。请运行: pip install flask")
    sys.exit(1)


app = Flask(__name__)

# 全局实例（启动时初始化）
master_db: MasterDatabase = None
verifier: MasterVerifier = None


def init_services():
    """初始化主库数据库和验证引擎"""
    global master_db, verifier
    logger.info("[SERVER] 初始化主库AI服务...")
    master_db = MasterDatabase()
    verifier = MasterVerifier(master_db=master_db)

    # 与真理库同步：确保所有已入库真理都注册到依赖图
    synced = verifier.dep_graph.sync_with_master_db(master_db.master_collection)
    if synced > 0:
        logger.info(f"[SERVER] 依赖图与真理库同步: 新增 {synced} 个映射")

    logger.info("[SERVER] 主库AI服务初始化完成")


# ==================== 自动验证调度器 ====================

# 调度器配置
AUTO_VERIFY_ENABLED = os.getenv('AUTO_VERIFY_ENABLED', 'true').lower() == 'true'
AUTO_VERIFY_INTERVAL = int(os.getenv('AUTO_VERIFY_INTERVAL', '10'))  # 检查间隔（秒）
AUTO_VERIFY_MAX_RETRIES = int(os.getenv('AUTO_VERIFY_MAX_RETRIES', '1'))  # 依赖不足的最大重试次数

# 调度器状态
_scheduler_thread = None
_scheduler_running = False
_verify_lock = threading.Lock()  # 确保同一时间只验证一个公式
_retry_counts: Dict[str, int] = {}  # submission_id → 重试次数

# 并行worker配置
NUM_WORKERS = int(os.getenv('MASTER_VERIFY_WORKERS', '10'))  # 并行验证worker数
_worker_locks = [threading.Lock() for _ in range(NUM_WORKERS)]  # 每个worker一个锁
_worker_threads: List[threading.Thread] = []
_last_promote_time = time.time()  # 上次有公式入库的时间
_cycle_check_cooldown = 600  # 环路检测冷却时间（秒）
_last_cycle_check_time = 0.0  # 上次环路检测时间
_dispatch_lock = threading.Lock()  # 取公式时的原子锁，防止多worker取到同一个
_self_audit_cooldown = 1800  # 自查冷却时间（秒）——30分钟
_last_self_audit_time = 0.0  # 上次自查时间


def _verify_one(sub_id: str, formula_name: str) -> str:
    """
    验证单个公式，返回action。
    被worker调用，不直接加锁（worker自己管理锁）。
    """
    result = verifier.verify_submission(sub_id)
    action = result.get("action", "unknown")

    if action == "promoted":
        logger.info(f"[SCHEDULER] ✓ 验证通过，已入库: {formula_name}")
        _retry_counts.pop(sub_id, None)
        global _last_promote_time
        _last_promote_time = time.time()
        # 新定理入库 → 触发waiting_dependencies重试
        _trigger_cascade_retry()

    elif action == "rejected":
        logger.warning(f"[SCHEDULER] ✗ 验证驳回: {formula_name} | {result.get('rejection_reason', '')[:80]}")
        _retry_counts.pop(sub_id, None)

    elif action == "dependency_gap":
        retries = _retry_counts.get(sub_id, 0) + 1
        _retry_counts[sub_id] = retries
        if retries >= AUTO_VERIFY_MAX_RETRIES:
            logger.info(
                f"[SCHEDULER] ⏸ 依赖不足，已达最大重试({retries})，暂停: {formula_name} | "
                f"等待更多底层定理入库"
            )
            master_db._update_pending_status(sub_id, "waiting_dependencies")
            _retry_counts.pop(sub_id, None)
        else:
            gap = result.get("dependency_gap", {})
            missing = gap.get("missing_dependencies", [])
            logger.info(
                f"[SCHEDULER] ⚠ 依赖不足({retries}/{AUTO_VERIFY_MAX_RETRIES}): {formula_name} | "
                f"缺少: {missing[:3]}"
            )
            master_db._update_pending_status(sub_id, "pending")

    return action


def _trigger_cascade_retry():
    """
    新定理入库后，自动重试waiting_dependencies中的公式。
    把waiting_dependencies重置为pending，让调度器重新验证。
    """
    try:
        pending_list = master_db.list_pending(limit=500)
        waiting = [p for p in pending_list if p.get("status") == "waiting_dependencies"]
        if not waiting:
            return

        # 检查这些公式的依赖是否已被满足
        retry_count = 0
        for item in waiting:
            sub_id = item["submission_id"]
            name = item.get("formula_name", "")
            # 重置为pending，让调度器重新验证
            master_db._update_pending_status(sub_id, "pending")
            _retry_counts.pop(sub_id, None)
            retry_count += 1

        if retry_count > 0:
            logger.info(f"[SCHEDULER] 🔄 级联重试: {retry_count}个waiting公式重置为pending")
    except Exception as e:
        logger.error(f"[SCHEDULER] 级联重试异常: {e}")


def _try_cycle_verification():
    """
    当waiting_dependencies积压时，自动触发环路检测和批量验证。
    同时检测互锁组——比环路更精确的关系判断。
    """
    global _last_cycle_check_time

    now = time.time()
    if now - _last_cycle_check_time < _cycle_check_cooldown:
        return

    _last_cycle_check_time = now

    try:
        pending_list = master_db.list_pending(limit=500)
        waiting = [p for p in pending_list if p.get("status") == "waiting_dependencies"]

        if len(waiting) < 3:
            return  # 积压不够多，不值得检测环路

        logger.info(f"[SCHEDULER] 🔍 waiting积压({len(waiting)}个)，触发互锁+环路检测")

        # 先检测互锁（比环路更精确的分类）
        interlocks = verifier.dep_graph.detect_interlocks()
        if interlocks:
            for il in interlocks:
                il_type = "强互锁" if il["type"] == "strong" else "弱互锁"
                names = [f["formula_name"][:30] for f in il["formulas"]]
                batch_ready = il["batch_verification_ready"]
                mutual = il.get("mutual_pairs", [])
                logger.info(
                    f"[SCHEDULER] 🔒 {il_type}组 {il['interlock_id']} "
                    f"({il['size']}个公式): {names[:3]}"
                    f"{' | 批量验证就绪' if batch_ready else ' | 阻塞: ' + il['blocking_reason'][:60]}"
                )
                if mutual:
                    for m in mutual[:2]:
                        logger.info(
                            f"[SCHEDULER]   互锁对: {m['a'][:25]} ↔ {m['b'][:25]}"
                        )

        # 检测环路
        cycles = verifier.dep_graph.detect_cycles()

        if not cycles:
            logger.info(f"[SCHEDULER] 环路检测: 无环路。{len(waiting)}个公式确实缺外部依赖。")
            return

        # 对自包含环路执行批量验证
        for cycle in cycles:
            if cycle.get("is_self_contained"):
                cycle_id = cycle.get("cycle_id", "")
                formulas = [f["formula_name"] for f in cycle.get("formulas", [])]
                logger.info(
                    f"[SCHEDULER] 🔄 发现自包含环路 {cycle_id} "
                    f"({len(formulas)}个公式): {formulas[:3]}..."
                )
                result = verifier.verify_cycle(cycle)
                action = result.get("action", "unknown")
                if action == "batch_promoted":
                    logger.info(
                        f"[SCHEDULER] ✓ 环路验证通过: {cycle_id}, "
                        f"入库{result.get('promoted_count', 0)}个"
                    )
                    _last_promote_time = time.time()
                elif action == "batch_rejected":
                    logger.info(f"[SCHEDULER] ✗ 环路验证未通过: {cycle_id}")
                else:
                    logger.info(f"[SCHEDULER] ⏸ 环路仍被阻塞: {cycle_id}")

    except Exception as e:
        logger.error(f"[SCHEDULER] 环路检测异常: {e}")


def _try_self_audit():
    """
    定期自查已入库定理，发现重复/近似/多证。
    自动合并精确重复，标记疑似重复供人工/LLM审查。
    """
    global _last_self_audit_time

    now = time.time()
    if now - _last_self_audit_time < _self_audit_cooldown:
        return

    _last_self_audit_time = now

    try:
        logger.info("[SCHEDULER] 🔍 触发定期自查")
        audit_result = master_db.self_audit()

        exact_dups = audit_result.get("exact_duplicates", [])
        if exact_dups:
            logger.info(f"[SCHEDULER] 自查发现 {len(exact_dups)} 对精确重复，自动合并")
            for dup in exact_dups:
                from_id = dup["theorem_b"]["id"]
                into_id = dup["theorem_a"]["id"]
                if master_db.merge_theorems(from_id, into_id):
                    logger.info(
                        f"[SCHEDULER] ✓ 自动合并: {dup['theorem_b']['name']} → "
                        f"{dup['theorem_a']['name']} (sim={dup['similarity']})"
                    )

        suspected = audit_result.get("suspected_duplicates", [])
        if suspected:
            logger.info(
                f"[SCHEDULER] 自查发现 {len(suspected)} 对疑似重复，"
                f"需LLM判断等价性（等待后续处理）"
            )

        multi_proofs = audit_result.get("multi_proof_theorems", [])
        if multi_proofs:
            logger.info(
                f"[SCHEDULER] 自查发现 {len(multi_proofs)} 个多证定理"
            )

    except Exception as e:
        logger.error(f"[SCHEDULER] 自查异常: {e}")


def _worker_loop(worker_id: int):
    """
    并行验证worker。每个worker独立取pending公式验证。
    """
    logger.info(f"[WORKER-{worker_id}] 启动")
    global _scheduler_running

    while _scheduler_running:
        try:
            # 每个worker用自己的锁控制并发
            lock = _worker_locks[worker_id]
            if not lock.acquire(blocking=False):
                time.sleep(AUTO_VERIFY_INTERVAL)
                continue

            try:
                # 原子地取一个pending公式（按优先级排序）
                with _dispatch_lock:
                    # 使用优先级排序的列表
                    pending_items = master_db.list_pending_by_priority(limit=500)

                    if not pending_items:
                        # 没有pending了——触发优先级验证、环路验证和自查
                        if worker_id == 0:
                            master_db.verify_priority_claims()
                            _try_cycle_verification()
                            _try_self_audit()
                        time.sleep(AUTO_VERIFY_INTERVAL)
                        continue

                    # 取第一个（优先级最高的）
                    next_item = pending_items[0]
                    sub_id = next_item["submission_id"]
                    formula_name = next_item.get("formula_name", "未知")
                    priority = next_item.get("verified_priority", "false") == "true"
                    deps = next_item.get("dependents_count", "0")

                    # 立即标记为processing，防止其他worker重复取
                    master_db._update_pending_status(sub_id, "processing")

                if priority:
                    logger.info(
                        f"[WORKER-{worker_id}] ⭐ 优先验证: {formula_name} "
                        f"(id={sub_id}, 被{deps}个公式依赖)"
                    )
                else:
                    logger.info(f"[WORKER-{worker_id}] 开始验证: {formula_name} (id={sub_id})")

                # 执行验证（不持有_dispatch_lock，允许其他worker并行取公式）
                _verify_one(sub_id, formula_name)

            finally:
                lock.release()

        except Exception as e:
            logger.error(f"[WORKER-{worker_id}] 异常: {e}")
            try:
                _worker_locks[worker_id].release()
            except:
                pass

        time.sleep(1)  # worker间隔短一些，提高吞吐


def start_scheduler():
    """启动自动验证调度器（多worker并行）"""
    global _scheduler_thread, _scheduler_running, _worker_threads
    if not AUTO_VERIFY_ENABLED:
        logger.info("[SCHEDULER] 自动验证已禁用 (AUTO_VERIFY_ENABLED=false)")
        return
    _scheduler_running = True

    # 启动多个worker
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=_worker_loop, args=(i,), daemon=True)
        _worker_threads.append(t)
        t.start()

    logger.info(
        f"[SCHEDULER] 调度器启动 | {NUM_WORKERS}个worker | "
        f"间隔={AUTO_VERIFY_INTERVAL}s | 最大重试={AUTO_VERIFY_MAX_RETRIES} | "
        f"环路检测冷却={_cycle_check_cooldown}s"
    )


def stop_scheduler():
    """停止自动验证调度器"""
    global _scheduler_running
    _scheduler_running = False
    logger.info("[SCHEDULER] 自动验证调度器已停止")


def _check_auth() -> bool:
    """检查请求认证"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    else:
        token = request.args.get("token", "")
    return token == MASTER_AI_TOKEN


# ==================== API 端点 ====================

@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "master-ai",
        "master_db_ready": master_db is not None and master_db.is_initialized,
        "verifier_ready": verifier is not None,
    })


@app.route("/v1/master/status", methods=["GET"])
def status():
    """主库状态"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    s = verifier.get_status()
    s["scheduler_running"] = _scheduler_running
    s["auto_verify_enabled"] = AUTO_VERIFY_ENABLED
    s["retry_counts"] = dict(_retry_counts)
    # 展开关键字段到顶层，方便客户端读取
    db_status = s.get("master_db", {})
    s["master_count"] = db_status.get("master_formulas_count", 0)
    s["pending_count"] = db_status.get("pending_count", 0)
    return jsonify(s)


@app.route("/v1/master/submit", methods=["POST"])
def submit():
    """
    本地 Agent 提交候选公式。

    请求体:
    {
        "formula_name": "公式名称",
        "formula_content": "公式表达式和说明",
        "derivation_chain": "推导链（引用公理/定理的步骤）",
        "source_agent": "agent标识",
        "local_verification": {  // 本地自检结果（可选）
            "berry_phase": 6.283,
            "n_value": 1,
            "is_consummated": true,
            "level": "初圆满"
        }
    }

    返回:
    {
        "submission_id": "xxx",
        "status": "pending"
    }
    """
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "缺少请求体"}), 400

    formula_name = data.get("formula_name", "")
    formula_content = data.get("formula_content", "")
    derivation_chain = data.get("derivation_chain", "")
    source_agent = data.get("source_agent", "unknown")
    local_verification = data.get("local_verification")
    external_anchors = data.get("external_anchors", [])
    topology_class = data.get("topology_class", "")  # A0 或 A1
    priority_hint = data.get("priority_hint", False)  # 优先验证提示
    interlock_hint = data.get("interlock_hint", [])  # 子AI互锁提示
    interlock_reasoning = data.get("interlock_reasoning", "")  # 子AI互锁推导说明

    if not formula_name or not formula_content:
        return jsonify({"error": "缺少 formula_name 或 formula_content"}), 400

    if topology_class not in ("A0", "A1"):
        return jsonify({
            "error": "必须声明 topology_class: A0（局部代数，Berry相位=0）或 A1（整体拓扑，Berry相位=2π）"
        }), 400

    submission_id = master_db.submit_candidate(
        formula_name=formula_name,
        formula_content=formula_content,
        derivation_chain=derivation_chain,
        source_agent=source_agent,
        local_verification=local_verification,
        external_anchors=external_anchors,
        topology_class=topology_class,
        priority_hint=priority_hint,
        interlock_hint=interlock_hint,
        interlock_reasoning=interlock_reasoning,
    )

    # 检查提交后的实际状态（可能是duplicate）
    pending = master_db.get_pending(submission_id)
    actual_status = pending["metadata"].get("status", "pending") if pending else "pending"

    if actual_status == "duplicate":
        duplicate_of = pending["metadata"].get("duplicate_of", "")
        duplicate_sim = pending["metadata"].get("duplicate_similarity", "")
        # 查找已有定理的名称
        existing = master_db.master_collection.get(ids=[duplicate_of], include=["metadatas"])
        existing_name = existing["metadatas"][0].get("formula_name", "") if existing["ids"] else ""
        return jsonify({
            "submission_id": submission_id,
            "status": "duplicate",
            "message": f"精确重复，已拒收。与已入库定理「{existing_name}」相似度={duplicate_sim}（master_id={duplicate_of}）。",
            "duplicate_of": duplicate_of,
            "duplicate_of_name": existing_name,
            "duplicate_similarity": duplicate_sim,
        })

    return jsonify({
        "submission_id": submission_id,
        "status": "pending",
        "message": f"候选公式已提交（{topology_class}类），等待验证。使用 POST /v1/master/verify 触发验证。",
        "external_anchors": external_anchors,
    })


@app.route("/v1/master/withdraw", methods=["POST"])
def withdraw():
    """
    撤回已提交的候选公式。

    每个子AI只能撤回自己提交的公式，不能撤回其他AI的提交。
    只能撤回未入库的公式（pending/waiting/processing状态）。
    已入库(promoted)的公式不可撤回。

    请求体:
    {
        "submission_id": "xxx",
        "source_agent": "agent标识"
    }

    返回:
    {
        "status": "withdrawn" / "error",
        "message": "..."
    }
    """
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "缺少请求体"}), 400

    submission_id = data.get("submission_id", "")
    source_agent = data.get("source_agent", "")

    if not submission_id or not source_agent:
        return jsonify({"error": "缺少 submission_id 或 source_agent"}), 400

    # 获取pending记录
    pending = master_db.get_pending(submission_id)
    if not pending:
        return jsonify({
            "status": "error",
            "message": f"提交不存在或已不在pending队列中: {submission_id}"
        }), 404

    # 校验身份：只有提交者本人才能撤回
    original_agent = pending["metadata"].get("source_agent", "")
    if original_agent != source_agent:
        return jsonify({
            "status": "error",
            "message": (
                f"无权撤回：此提交由 '{original_agent}' 提交，"
                f"你是 '{source_agent}'。每个子AI只能撤回自己的提交。"
            )
        }), 403

    # 检查状态：已入库的不可撤回
    current_status = pending["metadata"].get("status", "")
    if current_status == "promoted":
        # 已入库的公式在master_collection中，不在pending里
        # 但以防万一
        return jsonify({
            "status": "error",
            "message": "此公式已通过验证并入库为绝对真理，不可撤回。"
        }), 409

    # 检查是否正在验证中
    if current_status == "processing":
        logger.warning(
            f"[WITHDRAW] {source_agent} 撤回正在验证中的公式: "
            f"{pending['metadata'].get('formula_name', '')} (id={submission_id})"
        )

    # 执行撤回：从pending_collection删除
    formula_name = pending["metadata"].get("formula_name", "")
    master_db.pending_collection.delete(ids=[submission_id])

    logger.info(
        f"[WITHDRAW] {source_agent} 撤回提交: {formula_name} "
        f"(id={submission_id}, 原状态={current_status})"
    )

    return jsonify({
        "status": "withdrawn",
        "submission_id": submission_id,
        "formula_name": formula_name,
        "previous_status": current_status,
        "message": f"已撤回提交: {formula_name}"
    })


@app.route("/v1/master/verify", methods=["POST"])
def verify():
    """
    触发验证。

    请求体:
    {
        "submission_id": "xxx"  // 可选，不填则验证最早的待验证公式
    }

    返回完整验证结果。
    """
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    submission_id = data.get("submission_id", "")

    if not submission_id:
        # 自动取最早的待验证公式
        pending_list = master_db.list_pending(limit=1)
        if not pending_list:
            return jsonify({"error": "没有待验证的公式"}), 404
        submission_id = pending_list[0]["submission_id"]

    result = verifier.verify_submission(submission_id)
    return jsonify(result)


@app.route("/v1/master/pending", methods=["GET"])
def pending():
    """列出待验证公式"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    limit = int(request.args.get("limit", "500"))
    return jsonify({
        "pending": master_db.list_pending(limit=limit),
        "count": master_db.pending_collection.count() if master_db.pending_collection else 0,
    })


@app.route("/v1/master/truth", methods=["GET"])
def truth():
    """
    获取真理层快照（供本地 Agent 反哺）。

    返回已通过上圆满验证的公式列表。
    """
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    limit = int(request.args.get("limit", "100"))
    formulas = verifier.get_truth_layer(limit=limit)
    return jsonify({
        "formulas": formulas,
        "count": len(formulas),
        "master_total": master_db.master_count,
    })


@app.route("/v1/master/formula/<formula_id>", methods=["GET"])
def formula_detail(formula_id: str):
    """查看已验证公式详情"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    result = master_db.master_collection.get(
        ids=[formula_id],
        include=["documents", "metadatas"]
    )
    if not result["ids"]:
        return jsonify({"error": "公式不存在"}), 404

    meta = result["metadatas"][0]
    verification = {}
    if "verification_result" in meta:
        try:
            verification = json.loads(meta["verification_result"])
        except:
            verification = {"raw": meta["verification_result"][:500]}

    return jsonify({
        "master_id": formula_id,
        "permanent_number": meta.get("permanent_number", ""),
        "formula_name": meta.get("formula_name", ""),
        "document": result["documents"][0],
        "status": meta.get("status", ""),
        "verified_at": meta.get("verified_at", ""),
        "source_agent": meta.get("source_agent", ""),
        "verification": verification,
    })


@app.route("/v1/master/berry_accumulation", methods=["GET"])
def berry_accumulation():
    """查看Berry角度数据积累情况"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    formulas = master_db.get_truth_layer(limit=200)

    # 统计
    total = len(formulas)
    has_angle = [f for f in formulas if f.get("berry_path_points")]
    no_angle = [f for f in formulas if not f.get("berry_path_points")]
    has_phase = [f for f in formulas if f.get("berry_phase", 0) > 0]

    # 收集所有角度点
    all_points = []
    for f in has_angle:
        for pt in f.get("berry_path_points", []):
            all_points.append({
                "formula": f.get("formula_name", "")[:40],
                "theta_M": pt[0] if len(pt) > 0 else None,
                "theta_C": pt[1] if len(pt) > 1 else None,
                "theta_I": pt[2] if len(pt) > 2 else None,
            })

    # 统计Berry相位分布
    phase_distribution = {}
    for f in has_phase:
        n = f.get("berry_n_value", 0)
        phase_distribution[n] = phase_distribution.get(n, 0) + 1

    # 所有角度点的θ_I分布（关键维度）
    theta_i_values = [p["theta_I"] for p in all_points if p.get("theta_I") is not None]

    return jsonify({
        "summary": {
            "total_formulas": total,
            "with_angle_data": len(has_angle),
            "without_angle_data": len(no_angle),
            "with_berry_phase": len(has_phase),
            "total_angle_points": len(all_points),
        },
        "phase_distribution": phase_distribution,
        "theta_i_range": {
            "min": min(theta_i_values) if theta_i_values else None,
            "max": max(theta_i_values) if theta_i_values else None,
            "values": theta_i_values,
        },
        "formulas_with_angles": [
            {
                "formula_name": f.get("formula_name", "")[:50],
                "berry_status": f.get("berry_status", ""),
                "berry_phase": f.get("berry_phase", 0),
                "berry_n": f.get("berry_n_value", 0),
                "point_count": len(f.get("berry_path_points", [])),
            }
            for f in has_angle
        ],
        "all_angle_points": all_points,
    })


@app.route("/v1/master/dependency_graph", methods=["GET"])
def dependency_graph():
    """查看全局依赖图"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    summary = verifier.dep_graph.get_graph_summary()
    blocked = verifier.dep_graph.get_blocked_formulas()
    check_result = verifier.dep_graph.check_all_blocked()

    return jsonify({
        "summary": summary,
        "blocked_formulas": blocked,
        "fully_unblocked": check_result["fully_unblocked"],
        "partially_unblocked": check_result["partially_unblocked"],
        "still_blocked": check_result["still_blocked"],
    })


@app.route("/v1/master/verification_order", methods=["GET"])
def verification_order():
    """获取最优验证顺序（拓扑排序）"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    order = verifier.dep_graph.topological_order()

    return jsonify({
        "order": order,
        "total": len(order),
    })


@app.route("/v1/master/cycles", methods=["GET"])
def detect_cycles():
    """检测依赖图中的环路（相互依赖的公式集）"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    summary = verifier.dep_graph.get_cycle_summary()
    return jsonify(summary)


@app.route("/v1/master/verify_cycle/<cycle_id>", methods=["POST"])
def verify_cycle(cycle_id):
    """对指定环路进行批量闭环验证"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    # 找到对应的环路
    cycles = verifier.dep_graph.detect_cycles()
    target = None
    for c in cycles:
        if c.get("cycle_id") == cycle_id:
            target = c
            break

    if not target:
        return jsonify({"error": f"环路 {cycle_id} 不存在"}), 404

    # 执行批量闭环验证
    result = verifier.verify_cycle(target)
    return jsonify(result)


@app.route("/v1/master/verify_all_cycles", methods=["POST"])
def verify_all_cycles():
    """对所有自包含环路执行批量闭环验证"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    cycles = verifier.dep_graph.detect_cycles()
    results = []

    for c in cycles:
        if c.get("is_self_contained"):
            result = verifier.verify_cycle(c)
            results.append({
                "cycle_id": c["cycle_id"],
                "formulas": [f["formula_name"] for f in c["formulas"]],
                "action": result.get("action"),
                "duration": result.get("duration_seconds", 0),
            })
        else:
            results.append({
                "cycle_id": c["cycle_id"],
                "formulas": [f["formula_name"] for f in c["formulas"]],
                "action": "still_blocked",
                "unsatisfied_deps": c.get("unsatisfied_external_deps", [])[:3],
            })

    return jsonify({
        "total_cycles": len(cycles),
        "verified": sum(1 for r in results if r["action"] == "batch_promoted"),
        "rejected": sum(1 for r in results if r["action"] == "batch_rejected"),
        "still_blocked": sum(1 for r in results if r["action"] == "still_blocked"),
        "results": results,
    })


@app.route("/v1/master/source_audit", methods=["GET"])
def source_audit():
    """查看全部公式的来源溯源审计摘要"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(master_db.get_source_audit())


@app.route("/v1/master/self_audit", methods=["GET"])
def self_audit():
    """手动触发真理库自查（重复/近似/多证检测）"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    result = master_db.self_audit()
    return jsonify(result)


@app.route("/v1/master/verify_priority", methods=["POST"])
def verify_priority():
    """手动触发优先级声明验证"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    result = master_db.verify_priority_claims()
    return jsonify(result)


@app.route("/v1/master/interlocks", methods=["GET"])
def interlocks():
    """查看互锁组检测摘要"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(verifier.dep_graph.get_interlock_summary())


@app.route("/v1/master/force_promote_pia", methods=["POST"])
def force_promote_pia():
    """
    [已禁用] PIA强制入库已关闭。
    主库现在只接受纯几何数学公式，不接受任何物理映射。
    物理推导请在子AI本地完成。
    """
    return jsonify({
        "error": "PIA强制入库已禁用。主库只接受纯几何数学公式，物理映射不再入库。"
    }), 403


@app.route("/v1/master/merge", methods=["POST"])
def merge_theorems():
    """手动合并两个重复定理"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    from_id = data.get("from_id", "")
    into_id = data.get("into_id", "")

    if not from_id or not into_id:
        return jsonify({"error": "缺少 from_id 或 into_id"}), 400

    success = master_db.merge_theorems(from_id, into_id)
    if success:
        return jsonify({"status": "ok", "message": f"已合并 {from_id} → {into_id}"})
    else:
        return jsonify({"error": "合并失败"}), 400


@app.route("/v1/master/similar", methods=["GET"])
def find_similar():
    """查找与指定文本相似的已入库定理"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    text = request.args.get("text", "")
    threshold = float(request.args.get("threshold", "0.85"))

    if not text:
        return jsonify({"error": "缺少 text 参数"}), 400

    results = master_db.find_similar_in_master(text, threshold=threshold)
    return jsonify({"results": results, "count": len(results)})


@app.route("/v1/master/pia", methods=["GET"])
def get_pia():
    """查看已注册的物理识别锚点（PIA）"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401
    pia = master_db.get_pia()
    if pia:
        return jsonify(pia)
    else:
        return jsonify({
            "registered": False,
            "message": "PIA未注册。框架允许注册唯一的物理识别锚点（ℰ）。"
                       "注册后锁死，不再接受新的物理映射。"
        })


@app.route("/v1/master/register_pia", methods=["POST"])
def register_pia():
    """
    [已禁用] PIA注册已关闭。
    主库现在只接受纯几何数学公式，不接受任何物理映射。
    """
    return jsonify({
        "error": "PIA注册已禁用。主库只接受纯几何数学公式，物理映射不再入库。"
                 "物理推导请在子AI本地完成。"
    }), 403


@app.route("/v1/master/annotate_source", methods=["POST"])
def annotate_source():
    """为指定公式标注来源溯源信息"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    master_id = data.get("master_id", "")
    source_trace = data.get("source_trace", [])
    risk_level = data.get("risk_level", "unaudited")
    berry_closure = data.get("berry_closure", "pending")

    if not master_id:
        return jsonify({"error": "master_id required"}), 400

    success = master_db.annotate_source(master_id, source_trace, risk_level, berry_closure)
    if success:
        return jsonify({"status": "ok", "master_id": master_id})
    else:
        return jsonify({"error": "formula not found"}), 404


@app.route("/v1/master/cascade_check", methods=["POST"])
def cascade_check():
    """手动触发级联检查：检查哪些blocked公式现在可以重试验证"""
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    check_result = verifier.dep_graph.check_all_blocked()
    fully = check_result["fully_unblocked"]

    # 对已解锁的公式自动触发重试验证
    triggered = []
    for item in fully:
        fid = item["formula_id"]
        result = verifier.verify_submission(fid)
        triggered.append({
            "formula_id": fid,
            "formula_name": item["formula_name"],
            "action": result.get("action", "unknown"),
            "duration": result.get("duration_seconds", 0),
        })
        verifier.dep_graph.record_retry(
            fid, item["formula_name"], "cascade_check"
        )

    return jsonify({
        "checked": len(fully) + len(check_result["partially_unblocked"]),
        "fully_unblocked": len(fully),
        "triggered_retries": triggered,
    })


@app.route("/v1/master/suspend", methods=["POST"])
def suspend():
    """
    标记已验证公式为存疑（不删除）。

    请求体:
    {
        "formula_id": "master_xxx",
        "reason": "存疑原因"
    }
    """
    if not _check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    formula_id = data.get("formula_id", "")
    reason = data.get("reason", "")

    if not formula_id:
        return jsonify({"error": "缺少 formula_id"}), 400

    success = master_db.suspend_formula(formula_id, reason)
    if success:
        return jsonify({"status": "suspended", "formula_id": formula_id})
    else:
        return jsonify({"error": "公式不存在"}), 404


# ==================== 启动 ====================

def main():
    """启动主库AI服务"""
    logger.info("=" * 60)
    logger.info("几何论 主库AI 验证引擎")
    logger.info(f"端口: {MASTER_AI_PORT}")
    logger.info(f"验证模型: {os.getenv('MASTER_VERIFY_MODEL', 'deepseek-v4-pro')}")
    logger.info(f"推导模型: {os.getenv('MASTER_DERIVE_MODEL', 'deepseek-v4-pro')}")
    logger.info(f"主库目录: {os.getenv('MASTER_DB_DIR', os.path.join(_THIS_DIR, 'master_chroma_db'))}")
    logger.info("=" * 60)

    init_services()
    start_scheduler()  # 启动自动验证调度器

    app.run(
        host="0.0.0.0",
        port=MASTER_AI_PORT,
        debug=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
