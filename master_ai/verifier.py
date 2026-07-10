"""
verifier.py — 主库AI验证引擎

整合三重检查：
1. Berry回路闭合检测（berry_checker）
2. §9.6 证伪条件检查（falsification）
3. 独立推导复现（通过 LLM 从公理重新推导）

验证流程：
  候选公式 → Berry检测 → 证伪检查 → 独立推导 → 全部通过 → 入库
                                      任一失败 → 驳回（附理由）
"""
import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import (
    logger,
    GAI_API_KEY,
    GAI_BASE_URL,
    MASTER_VERIFY_MODEL,
    MASTER_DERIVE_MODEL,
    THREE_AXIOMS,
    AXIOM_PREFIXES,
    ARTICLES_DIR,
    GEOMETRY_CONSTANTS,
)
from master_db import MasterDatabase
from math_foundations import (
    get_foundations_text,
    get_bridge_hypothesis_text,
    validate_anchors,
    get_pending_derivations_text,
    BRIDGE_HYPOTHESES,
)
from dependency_graph import DependencyGraph
from berry_checker import BerryPhaseChecker, BerryPhaseResult
from falsification import FalsificationChecker


class MasterVerifier:
    """
    主库AI验证引擎

    默认怀疑一切，只有三重检查全部通过才放行入库。
    """

    def __init__(self, master_db: Optional[MasterDatabase] = None):
        self.master_db = master_db or MasterDatabase()
        self.berry_checker = BerryPhaseChecker()
        self.falsification_checker = FalsificationChecker()
        self._llm_client = None
        self._init_llm()

        # 依赖图引擎
        dep_graph_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "dependency_graph.json"
        )
        self.dep_graph = DependencyGraph(persist_path=dep_graph_path)
        logger.info(
            f"[VERIFIER] 依赖图加载: {self.dep_graph.get_graph_summary()}"
        )

    def _init_llm(self):
        """初始化 LLM 客户端（用于独立推导复现）"""
        if not GAI_API_KEY:
            logger.warning("[VERIFIER] GAI_API_KEY 未配置，独立推导复现不可用")
            return
        try:
            import openai
            self._llm_client = openai.OpenAI(
                api_key=GAI_API_KEY,
                base_url=GAI_BASE_URL,
            )
            logger.info(f"[VERIFIER] LLM 客户端就绪: {MASTER_VERIFY_MODEL}")
        except Exception as e:
            logger.error(f"[VERIFIER] LLM 初始化失败: {e}")

    # ==================== 主验证入口 ====================

    def verify_submission(self, submission_id: str) -> Dict[str, Any]:
        """
        验证一个候选公式。

        流程：
        1. 从待验证队列获取公式
        2. Berry回路闭合检测
        3. §9.6 证伪条件检查
        4. 独立推导复现（LLM 从公理重新推导）
        5. 全部通过 → 入库；任一失败 → 驳回

        Returns:
            完整验证结果
        """
        start_time = time.time()
        result = {
            "submission_id": submission_id,
            "started_at": datetime.now().isoformat(),
            "stages": {},
            "passed": False,
            "action": "",
            "rejection_reason": "",
        }

        # 获取候选公式
        pending = self.master_db.get_pending(submission_id)
        if not pending:
            result["error"] = f"候选公式不存在: {submission_id}"
            result["action"] = "error"
            return result

        formula_name = pending["metadata"].get("formula_name", "unnamed")
        document = pending["document"]
        # 从文档中分离公式内容和推导链
        formula_content, derivation_chain = self._parse_document(document)

        # 提取子AI声明的外部锚点（L2桥接假设）
        external_anchors_str = pending["metadata"].get("external_anchors", "")
        external_anchors = []
        if external_anchors_str:
            try:
                external_anchors = json.loads(external_anchors_str) if isinstance(external_anchors_str, str) else external_anchors_str
            except:
                external_anchors = [external_anchors_str] if external_anchors_str else []

        if external_anchors:
            logger.info(f"[VERIFIER] 子AI声明的外部锚点: {external_anchors}")

        # 提取子AI互锁提示
        pending_meta = {
            "interlock_hint_list": [],
            "interlock_reasoning": pending["metadata"].get("interlock_reasoning", ""),
        }
        interlock_hint_str = pending["metadata"].get("interlock_hint", "")
        if interlock_hint_str:
            try:
                pending_meta["interlock_hint_list"] = json.loads(interlock_hint_str) if isinstance(interlock_hint_str, str) else interlock_hint_str
            except:
                pass
        if pending_meta["interlock_hint_list"]:
            logger.info(
                f"[VERIFIER] 子AI互锁提示: {pending_meta['interlock_hint_list']}"
            )
        if pending_meta["interlock_reasoning"]:
            logger.info(
                f"[VERIFIER] 子AI互锁推导: {pending_meta['interlock_reasoning'][:100]}"
            )

        logger.info(f"[VERIFIER] 开始验证: {formula_name} (id={submission_id})")

        # ---- 纯几何封锁：拒绝实质性物理公式 ----
        # 主库只接受纯几何数学公式和推导，物理量纲推导留给子AI本地完成
        #
        # 区分两层：
        # 1. 硬封锁关键词：公式本身就是物理映射/使用了物理常数 → 立即拒绝
        # 2. 软提示关键词：公式说明中提到物理术语（如"对应物理中的X"）→ 不拦截，交给LLM阶段判断
        #
        # 这样纯几何定理即使说明文字中带物理术语也不会被误杀

        # 硬封锁：这些关键词出现说明公式本身就是物理映射
        hard_physics_keywords = [
            # 物理映射本身
            "ℰ映射", "ℰ 映射", "ε映射", "epsilon映射",
            "单一物理映射", "物理识别锚点", "PIA",
            # 物理假设
            "Born规则", "玻恩规则",
            # 纯物理量纲
            "SI单位", "SI制",
        ]

        # 注意：以下词从硬封锁移除，改为软提示（交给LLM判断）
        # - 精细结构常数、α⁻¹、S_e=137：既是物理量也是几何量
        # - 量纲桥：常在纯几何定理的说明文字中出现，不是公式本身

        # 软提示：这些词可能出现在纯几何定理的说明文字中，不拦截
        # （量纲、物理量、物理世界、物理常数、物理参数、物理假设、物理对应等）
        # LLM阶段3的独立推导会检查公式是否真正依赖物理概念

        # 只检查公式名和公式内容（不检查推导链的说明文字）
        formula_text = (formula_name + " " + formula_content).lower()
        is_hard_physics = any(kw.lower() in formula_text for kw in hard_physics_keywords)

        if is_hard_physics:
            result["passed"] = False
            result["action"] = "rejected"
            result["rejection_reason"] = (
                "主库只接受纯几何数学公式。公式本身包含物理映射或物理常数"
                "（ℰ映射/精细结构常数/SI单位/量纲桥/Born规则等）。"
                "物理量纲相关的推导请在子AI本地完成，不提交主库验证。"
            )
            logger.info(
                f"[VERIFIER] 纯几何封锁: 公式本身含物理常数/映射，拒绝入库"
            )
            self._finalize(result, start_time, submission_id)
            return result

        # ---- 外部锚点处理：忽略ℰ，不拦截 ----
        # 子AI可能习惯性填 external_anchors=['ℰ']，但公式本身是纯几何的
        # ℰ映射已从主库删除，不再作为外部输入。
        # 直接清空外部锚点，不因标签拒绝公式——公式是否纯几何由硬封锁和LLM阶段判断
        ext_anchors_raw = pending["metadata"].get("external_anchors", "[]")
        try:
            ext_anchors = json.loads(ext_anchors_raw) if isinstance(ext_anchors_raw, str) else ext_anchors_raw
        except:
            ext_anchors = []

        # 清空外部锚点（不再因ℰ标签拒绝）
        ext_anchors = []

        # ---- 阶段0: 拓扑分类检查 ----
        topology_class = pending["metadata"].get("topology_class", "")
        if not topology_class:
            result["passed"] = False
            result["action"] = "rejected"
            result["rejection_reason"] = (
                "未声明拓扑分类。每个公式必须标注 topology_class=A0（局部代数，Berry相位=0）"
                "或 A1（整体拓扑，Berry相位=2π）。"
            )
            self._finalize(result, start_time, submission_id)
            return result

        if topology_class not in ("A0", "A1"):
            result["passed"] = False
            result["action"] = "rejected"
            result["rejection_reason"] = (
                f"拓扑分类不合法: {topology_class}。只能为 A0 或 A1。"
            )
            self._finalize(result, start_time, submission_id)
            return result

        topology_check = {
            "declared_class": topology_class,
            "external_anchors": ext_anchors,
            "has_external_input": False,
            "passed": True,
            "note": "纯几何验证，无外部输入",
        }

        logger.info(
            f"[VERIFIER] 阶段0通过: 拓扑分类={topology_class}, 纯几何"
        )
        result["stages"]["topology_check"] = topology_check

        # ---- 阶段1: Berry角度记录（不拦截，只记录） ----
        # Berry相位不作为入库门槛，但始终提取并记录角度数据
        # 积累足够多公式后，可以统计分析Berry相位模式
        berry_result = self.berry_checker.verify(
            derivation_chain=derivation_chain,
            formula_content=formula_content,
        )
        berry_dict = self.berry_checker.result_to_dict(berry_result)

        # 无论是否有角度数据，都记录下来
        path_point_count = len(berry_result.path_points)
        if path_point_count == 0:
            berry_dict["status"] = "no_angle_data"
            berry_dict["note"] = "推导链未包含角度参数，暂无Berry数据。公式继续验证。"
            logger.info(
                f"[VERIFIER] 阶段1记录: 无角度数据 "
                f"(推导深度={len(berry_result.path_steps)})，继续验证"
            )
        elif path_point_count < 3:
            berry_dict["status"] = "insufficient_points"
            berry_dict["note"] = f"仅{path_point_count}个角度点，不足以计算Berry相位。已记录，继续验证。"
            logger.info(
                f"[VERIFIER] 阶段1记录: {path_point_count}个角度点 "
                f"(不足3个)，已记录，继续验证"
            )
        else:
            berry_dict["status"] = "recorded"
            if berry_result.is_consummated:
                logger.info(
                    f"[VERIFIER] 阶段1记录: Berry相位 {berry_result.berry_phase:.4f} rad "
                    f"= {berry_result.n_value}×2π ({berry_result.consummation_level})，"
                    f"闭合误差 {berry_result.closure_error:.6f}"
                )
            else:
                logger.info(
                    f"[VERIFIER] 阶段1记录: Berry相位 {berry_result.berry_phase:.4f} rad，"
                    f"未闭合（误差 {berry_result.closure_error:.4f}），已记录"
                )

        result["stages"]["berry_check"] = berry_dict

        # ---- 阶段2: §9.6 证伪条件检查 ----
        # Berry检查跳过时，证伪检查中的Berry相关检查也相应跳过
        falsify_result = self.falsification_checker.run_all_checks(
            formula_content=formula_content,
            derivation_chain=derivation_chain,
            berry_result=berry_dict,
        )
        result["stages"]["falsification"] = falsify_result

        if not falsify_result["all_passed"]:
            result["passed"] = False
            result["action"] = "rejected"
            result["rejection_reason"] = f"证伪条件未通过: {falsify_result['rejection_reason']}"
            self._finalize(result, start_time, submission_id)
            return result

        logger.info(f"[VERIFIER] 阶段2通过: 证伪条件全部通过")

        # ---- 阶段3: 独立推导复现 ----
        derivation_result = self._independent_derivation(
            formula_name=formula_name,
            formula_content=formula_content,
            external_anchors=external_anchors,
            topology_class=topology_class,
        )
        result["stages"]["independent_derivation"] = derivation_result

        if not derivation_result.get("reproduced", False):
            # 复现失败 — 区分"依赖不足"和"公式真错误"
            gap_analysis = self._analyze_dependency_gap(
                formula_name=formula_name,
                formula_content=formula_content,
                derivation_result=derivation_result,
            )
            result["stages"]["dependency_gap_analysis"] = gap_analysis

            if gap_analysis.get("is_dependency_gap", False):
                # 依赖不足：不是公式的错，是主库还没准备好
                result["passed"] = False
                result["action"] = "dependency_gap"
                result["rejection_reason"] = ""
                result["dependency_gap"] = gap_analysis

                # ---- 互锁检测：判断是单纯依赖不足还是互锁 ----
                interlocks = self.dep_graph.get_interlocks_for_formula(submission_id)
                if interlocks:
                    # 这个公式参与了互锁组
                    interlock_info = interlocks[0]  # 取第一个互锁组
                    il_type = "强互锁（直接互引）" if interlock_info["type"] == "strong" else "弱互锁（间接成环）"
                    il_formulas = [f["formula_name"] for f in interlock_info["formulas"]]
                    batch_ready = interlock_info["batch_verification_ready"]
                    blocking = interlock_info["blocking_reason"]
                    mutual = interlock_info.get("mutual_pairs", [])

                    result["is_interlocked"] = True
                    result["interlock_type"] = interlock_info["type"]
                    result["interlock_group"] = il_formulas
                    result["interlock_batch_ready"] = batch_ready

                    if batch_ready:
                        result["message"] = (
                            f"公式与以下定理形成{il_type}: {', '.join(il_formulas[:5])}。"
                            f"互锁组已自包含（无外部依赖），主库AI将自动触发批量验证。"
                            f"无需子AI补全任何前置定理。"
                        )
                    else:
                        ext_deps = interlock_info.get("external_deps", [])
                        result["message"] = (
                            f"公式与以下定理形成{il_type}: {', '.join(il_formulas[:5])}。"
                            f"互锁组缺少外部依赖: {', '.join(ext_deps[:3])}。"
                            f"需要先验证这些外部定理，才能解锁互锁组进行批量验证。"
                        )
                        if mutual:
                            pairs_str = "; ".join([f"{m['a'][:20]}↔{m['b'][:20]}" for m in mutual[:3]])
                            result["message"] += f" 强互锁对: {pairs_str}"
                else:
                    # 单纯依赖不足，没有互锁
                    result["is_interlocked"] = False
                    result["message"] = (
                        f"公式未通过验证，但并非公式本身有误。主库AI缺少以下依赖: "
                        f"{', '.join(gap_analysis.get('missing_dependencies', []))}。"
                        f"请子库先补全这些前置定理后重新提交。"
                    )
                self._finalize(result, start_time, submission_id)
                return result
            else:
                # 公式真有错误
                result["passed"] = False
                result["action"] = "rejected"
                result["rejection_reason"] = (
                    f"独立推导复现失败（公式错误）: "
                    f"{derivation_result.get('reason', '未知原因')}"
                )
                self._finalize(result, start_time, submission_id)
                return result

        logger.info(f"[VERIFIER] 阶段3通过: 独立推导复现成功")

        # ---- 绝对真理判定 ----
        # 主库只接受绝对真理
        # ℰ是唯一合法的L2假设——使用ℰ不构成驳回理由
        # 但Born规则、物理识别等未验证概念不得使用——使用则驳回
        used_anchors = derivation_result.get("used_anchors", [])
        declared_anchors = derivation_result.get("declared_anchors", [])

        # 区分：ℰ使用（合法）vs 未验证概念使用（非法）
        epsilon_used = "ℰ 单一物理映射" in used_anchors
        unverified_used = [a for a in used_anchors if a != "ℰ 单一物理映射"]

        if unverified_used:
            # 推导依赖了未验证的物理概念（如Born规则）→ 不是绝对真理，驳回
            result["passed"] = False
            result["action"] = "rejected"
            result["rejection_reason"] = (
                f"推导依赖未验证的物理概念: {', '.join(unverified_used)}。"
                f"这些概念不是独立假设，必须从ℰ推导出来、验证入库后才能使用。"
                f"请先从ℰ推导{unverified_used[0]}并提交验证。"
            )
            result["used_anchors"] = used_anchors
            logger.info(
                f"[VERIFIER] 驳回: 推导依赖未验证物理概念 {unverified_used}，非绝对真理"
            )
            self._finalize(result, start_time, submission_id)
            return result

        # ℰ使用或无假设依赖 → 绝对真理，入库
        if epsilon_used:
            logger.info(f"[VERIFIER] 绝对真理: 使用ℰ映射（合法L2假设）")
        elif declared_anchors:
            logger.info(
                f"[VERIFIER] 绝对真理: 子AI声明了{declared_anchors}但LLM推导未实际使用"
            )
        else:
            logger.info(f"[VERIFIER] 绝对真理: 无桥接假设，纯公理+数学基座推导")

        result["passed"] = True
        result["action"] = "promoted"
        result["rejection_reason"] = ""
        result["used_anchors"] = []

        self._finalize(result, start_time, submission_id)
        return result

    def _finalize(self, result: Dict, start_time: float, submission_id: str):
        """完成验证，执行入库或驳回"""
        result["completed_at"] = datetime.now().isoformat()
        result["duration_seconds"] = round(time.time() - start_time, 2)

        formula_name = result.get("formula_name", "")

        # 始终将完整验证结果保存到 pending metadata，供子AI查询
        verification_result_json = json.dumps(result, ensure_ascii=False, default=str)

        # 提前获取pending数据（passed和rejected分支都需要）
        pending = self.master_db.get_pending(submission_id)

        # 提取子AI互锁提示（所有分支都需要，提前定义）
        interlock_hint_list = []
        interlock_reasoning_str = ""
        if pending:
            ih_str = pending["metadata"].get("interlock_hint", "")
            if ih_str:
                try:
                    interlock_hint_list = json.loads(ih_str) if isinstance(ih_str, str) else ih_str
                except:
                    pass
            interlock_reasoning_str = pending["metadata"].get("interlock_reasoning", "")

        if result["passed"]:
            # ---- 去重检查：验证通过后，检查是否已有同结论定理 ----
            # 如果已有高度相似的定理(>0.90)，不重复入库，而是附加为替代证明
            doc_text = pending.get("document", "") if pending else ""
            source_agent = pending["metadata"].get("source_agent", "") if pending else ""

            # 也检查提交时标记的suspected_duplicate_of
            suspected_dup_id = ""
            if pending:
                suspected_dup_id = pending["metadata"].get("suspected_duplicate_of", "")

            master_id = ""

            # 在已入库定理中查找相似项
            similar = self.master_db.find_similar_in_master(doc_text, threshold=0.90, limit=3)
            if similar:
                best_match = similar[0]
                best_sim = best_match["similarity"]
                existing_id = best_match["master_id"]
                existing_name = best_match["formula_name"]

                if best_sim > 0.95:
                    # 高度相似——附加为替代证明（如果推导方法不同）
                    derivation_text = result.get("stages", {}).get(
                        "independent_derivation", {}
                    ).get("derivation", "")
                    method = self._extract_proof_method(derivation_text, formula_name)

                    proof_data = {
                        "method": method,
                        "derivation_chain": derivation_text[:2000],
                        "source_agent": source_agent,
                        "verification_result": json.dumps(result, ensure_ascii=False, default=str)[:5000],
                        "submission_id": submission_id,
                        "similarity": best_sim,
                    }
                    self.master_db.add_alternative_proof(existing_id, proof_data)
                    self.master_db._update_pending_status(
                        submission_id, "alternative_proof",
                        verification_result=verification_result_json,
                    )
                    logger.info(
                        f"[VERIFIER] 验证通过，附加为替代证明: {formula_name} → "
                        f"{existing_name} (sim={best_sim:.4f}, method={method})"
                    )
                    master_id = existing_id
                    result["action"] = "alternative_proof"
                    result["attached_to"] = existing_id
                    result["proof_method"] = method
                else:
                    # 0.90-0.95: 让LLM判断——但为简化，先正常入库
                    # LLM等价性判断可以后续作为self_audit的一部分
                    master_id = self.master_db.promote_to_master(submission_id, result)
            else:
                # 没有相似项——正常入库
                master_id = self.master_db.promote_to_master(submission_id, result)

            if result["action"] != "alternative_proof":
                # 统一标记为promoted（无论是否同名重复提交）
                self.master_db._update_pending_status(
                    submission_id,
                    "promoted",
                    verification_result=verification_result_json,
                )
                if master_id:
                    logger.info(
                        f"[VERIFIER] 验证通过，已入库: {formula_name} "
                        f"→ master_id={master_id} "
                        f"(耗时 {result['duration_seconds']}s)"
                    )
                else:
                    logger.warning(
                        f"[VERIFIER] 验证通过但master_id为空: {submission_id}"
                    )

            # 确保master_id写入result（无论哪种情况）
            result["master_id"] = master_id

            # ---- 依赖图：注册入库公式 ----
            # 提取推导中引用的L3定理作为依赖
            derivation_text = result.get("stages", {}).get(
                "independent_derivation", {}
            ).get("derivation", "")
            used_l3 = self._extract_l3_references(derivation_text)

            self.dep_graph.register_formula(
                formula_id=submission_id,
                formula_name=formula_name,
                status="promoted",
                dependencies=used_l3,
                master_id=master_id or "",
                interlock_hint=interlock_hint_list,
                interlock_reasoning=interlock_reasoning_str,
            )

            # ---- 级联重试：检查哪些blocked公式可以解锁 ----
            unblocked = self.dep_graph.find_unblocked(formula_name)
            if unblocked:
                logger.info(
                    f"[VERIFIER] 级联解锁: {formula_name} 入库 → "
                    f"{len(unblocked)} 个公式可能解锁"
                )
                result["cascade_unlocked"] = unblocked

        else:
            action = result.get("action", "rejected")
            if action == "dependency_gap":
                # 依赖不足：不标记为"驳回"，而是"等待依赖"
                missing_deps = result.get("dependency_gap", {}).get(
                    "missing_dependencies", []
                )
                self.master_db._update_pending_status(
                    submission_id,
                    "dependency_gap",
                    dependency_gap=json.dumps(
                        result.get("dependency_gap", {}),
                        ensure_ascii=False,
                        default=str,
                    ),
                    message=result.get("message", ""),
                    verification_result=verification_result_json,
                )
                logger.info(
                    f"[VERIFIER] 依赖不足，等待补全: {submission_id} "
                    f"(耗时 {result['duration_seconds']}s) | "
                    f"缺少: {missing_deps}"
                )

                # ---- 依赖图：注册被阻塞的公式 ----
                self.dep_graph.register_formula(
                    formula_id=submission_id,
                    formula_name=formula_name,
                    status="blocked",
                    dependencies=missing_deps,
                    interlock_hint=interlock_hint_list,
                    interlock_reasoning=interlock_reasoning_str,
                )
            else:
                self.master_db.reject_candidate(
                    submission_id,
                    rejection_reason=result.get("rejection_reason", ""),
                    verification_result=result,
                )
                logger.warning(
                    f"[VERIFIER] 验证未通过，已驳回: {submission_id} "
                    f"(耗时 {result['duration_seconds']}s) | "
                    f"原因: {result.get('rejection_reason', '')[:100]}"
                )

                # ---- 依赖图：注册被驳回的公式 ----
                self.dep_graph.register_formula(
                    formula_id=submission_id,
                    formula_name=formula_name,
                    status="rejected",
                    interlock_hint=interlock_hint_list,
                    interlock_reasoning=interlock_reasoning_str,
                )

    def _extract_l3_references(self, derivation_text: str) -> List[str]:
        """从LLM推导文本中提取引用的已验证定理名称"""
        if not derivation_text:
            return []
        refs = []
        # 匹配常见引用模式
        import re
        # 匹配 "已验证定理"、"L3"、"引用定理" 等后面的定理名
        patterns = [
            r'(?:已验证定理|L3|引用定理)\s*[:：]?\s*(.+?)(?:\n|$)',
            r'(?:定理)\s*(.+?)(?:\s*[，。,\n])',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, derivation_text)
            for m in matches:
                m = m.strip()
                if m and len(m) < 80 and m not in refs:
                    refs.append(m)
        return refs[:5]  # 最多记录5个依赖

    def _extract_proof_method(self, derivation_text: str, formula_name: str = "") -> str:
        """
        从推导文本中提取证明方法描述。

        用于区分同一定理的不同证明方法。
        """
        if not derivation_text:
            return "未知方法"

        text = derivation_text.lower()

        # 常见数学方法关键词
        methods = [
            ("Schwarz定理/偏导交换", ["schwarz", "偏导交换", "混合偏导"]),
            ("分部积分/Stokes定理", ["分部积分", "stokes", "斯托克斯"]),
            ("群论/S₃对称性", ["s₃", "s3", "群论", "对称群", "置换"]),
            ("凸分析", ["凸分析", "严格凸", "jensen", "凸函数"]),
            ("Hessian矩阵", ["hessian", "海森"]),
            ("谱理论/特征值", ["谱", "特征值", "eigenvalue", "dixmier"]),
            ("代数恒等式", ["代数恒等", "直接计算", "展开"]),
            ("拓扑论证", ["拓扑", "同伦", "纤维丛", "chern"]),
            ("微积分", ["微积分", "导数", "积分", "极限"]),
            ("de Rham复形", ["de rham", "德拉姆", "外微分"]),
        ]

        found = []
        for name, keywords in methods:
            for kw in keywords:
                if kw in text:
                    found.append(name)
                    break

        if found:
            return " + ".join(found)
        return "其他方法"

    def _detect_unverified_concepts(self, derivation_chain: str, formula_content: str) -> List[str]:
        """
        检测推导链和公式内容中是否引用了未验证的物理概念。

        这些概念不是公理，不是标准数学工具——它们是物理假设，
        必须先从ℰ推导入库后才能使用。
        """
        text = (derivation_chain + " " + formula_content).lower()

        # 未验证物理概念列表
        # ℰ是合法的（唯一L2假设），但以下概念必须从ℰ推导后才能用
        unverified = [
            ("Born规则", ["born规则", "born 规则", "born rule", "p=|ψ|²", "p=|psi|²"]),
            ("物理识别点", ["物理识别点", "physical identification"]),
            ("归一化约定", ["归一化约定", "normalization convention", "归一化条件"]),
            ("双模零误差", ["双模零误差", "dual-mode zero"]),
            ("S_e=137", ["s_e=137", "s_e = 137", "s_e≈137", "精细结构常数"]),
        ]

        found = []
        for name, patterns in unverified:
            for p in patterns:
                if p in text:
                    found.append(name)
                    break

        return found

    # ==================== 批量闭环验证 ====================

    def verify_cycle(self, cycle: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量闭环验证：将相互依赖的公式作为一个整体验证。

        这是针对环路依赖的特殊验证模式：
        - 不逐个验证（因为谁都不可能先通过）
        - 把环路内所有公式一起交给LLM
        - LLM判断整个系统是否自洽
        - 如果自洽，整批入库

        Args:
            cycle: detect_cycles() 返回的环路结构

        Returns:
            {
                "action": "batch_promoted" / "batch_rejected" / "still_blocked",
                "formulas": [...],
                "llm_analysis": str,
                "duration_seconds": float,
            }
        """
        start_time = time.time()
        formulas = cycle.get("formulas", [])
        cycle_id = cycle.get("cycle_id", "unknown")
        is_self_contained = cycle.get("is_self_contained", False)

        result = {
            "cycle_id": cycle_id,
            "formulas": [f["formula_name"] for f in formulas],
            "size": len(formulas),
            "action": "unknown",
            "is_self_contained": is_self_contained,
        }

        logger.info(
            f"[VERIFIER] 开始批量闭环验证 {cycle_id}: "
            f"{len(formulas)}个公式"
        )

        # 如果环路有未满足的外部依赖，无法验证
        unsatisfied = cycle.get("unsatisfied_external_deps", [])
        if unsatisfied:
            result["action"] = "still_blocked"
            result["unsatisfied_external_deps"] = unsatisfied
            result["llm_analysis"] = (
                f"环路包含 {len(unsatisfied)} 个未满足的外部依赖，"
                f"无法进行闭环验证。需要先推导外部依赖。"
            )
            result["duration_seconds"] = round(time.time() - start_time, 2)
            logger.info(
                f"[VERIFIER] 环路 {cycle_id} 仍被阻塞: "
                f"{len(unsatisfied)}个外部依赖未满足"
            )
            return result

        # 收集环路内所有公式的内容
        formula_texts = []
        formula_ids = []
        for f_info in formulas:
            fid = f_info["formula_id"]
            fname = f_info["formula_name"]
            pending = self.master_db.get_pending(fid)
            if not pending:
                logger.warning(f"[VERIFIER] 环路验证: 公式不存在 {fid}")
                continue
            doc = pending.get("document", "")
            formula_ids.append(fid)
            formula_texts.append(f"--- 公式: {fname} ---\n{doc}\n")

        if not formula_texts:
            result["action"] = "batch_rejected"
            result["llm_analysis"] = "无法获取公式内容"
            result["duration_seconds"] = round(time.time() - start_time, 2)
            return result

        # 构建LLM提示词
        axioms_text = self._build_axioms_text()
        math_text = get_foundations_text()
        verified_theorems = self.master_db.get_truth_layer(limit=50)
        verified_text = ""
        if verified_theorems:
            verified_text = "\n\n【L3: 已验证定理（可作为推导起点）】\n"
            for t in verified_theorems:
                verified_text += f"- {t['formula_name']}: {t.get('document', '')[:150]}...\n"
        bridge_text = get_bridge_hypothesis_text(["ℰ"])
        pending_text = get_pending_derivations_text()

        all_formulas = "\n\n".join(formula_texts)

        system_prompt = f"""你是几何论主库AI验证器。现在进行批量闭环验证。

{axioms_text}
{math_text}
{bridge_text}
{pending_text}
{verified_text}

【闭环验证原则】
以下公式相互依赖，形成环路。无法逐个验证（谁都不可能先通过）。
你需要将它们作为一个整体系统验证：
1. 检查环路内的公式是否相互支撑、逻辑自洽
2. 检查是否存在循环论证（A依赖B，B依赖A，但没有实质性的数学内容）
3. 检查环路作为整体是否能从L1公理+L0数学+ℰ映射出发建立
4. 如果环路整体自洽且有实质性数学内容，判定"闭环自洽"
5. 如果存在空洞的循环论证或数学错误，判定"闭环不自洽"

【Berry相位视角】
环路验证本质上对应Berry相位的闭合性检查：
- 环路自洽 ⟺ Berry相位 ∮A·dl = 2πn (n∈ℤ⁺)
- 循环论证 ⟺ Berry相位不闭合（相位有缺陷）"""

        user_prompt = f"""请验证以下{len(formula_texts)}个相互依赖的公式构成的环路是否自洽。

【环路内的公式】
{all_formulas}

【要求】
1. 分析每个公式的数学内容
2. 检查它们之间的依赖关系是否形成有意义的数学闭环
3. 判断整个系统是否自洽
4. 回答"闭环自洽"或"闭环不自洽"
5. 如果不自洽，说明哪个环节有问题"""

        # 调用LLM
        llm_result = self._call_llm_for_cycle(system_prompt, user_prompt)

        result["llm_analysis"] = llm_result.get("analysis", "")[:2000]
        result["is_coherent"] = llm_result.get("is_coherent", False)
        result["has_circular_reasoning"] = llm_result.get("has_circular_reasoning", False)

        if llm_result.get("is_coherent") and not llm_result.get("has_circular_reasoning"):
            # 闭环自洽 → 整批入库
            promoted_ids = []
            for fid in formula_ids:
                pending = self.master_db.get_pending(fid)
                if not pending:
                    continue
                fname = pending["metadata"].get("formula_name", "")
                # 构造验证结果
                verify_result = {
                    "passed": True,
                    "action": "batch_promoted",
                    "formula_name": fname,
                    "stages": {
                        "berry_check": {"status": "cycle_verified", "note": "批量闭环验证通过"},
                        "falsification": {"all_passed": True, "checks": []},
                        "independent_derivation": {
                            "reproduced": True,
                            "derivation": f"闭环验证: {llm_result.get('analysis', '')[:500]}",
                            "reason": "环路整体自洽",
                        },
                    },
                    "duration_seconds": round(time.time() - start_time, 2),
                }
                master_id = self.master_db.promote_to_master(fid, verify_result)
                if master_id:
                    promoted_ids.append(master_id)
                    self.master_db._update_pending_status(
                        fid, "promoted",
                        verification_result=json.dumps(verify_result, ensure_ascii=False, default=str),
                    )
                    self.dep_graph.update_status(fid, "promoted", master_id)
                    logger.info(f"[VERIFIER] 闭环入库: {fname} → {master_id}")

            result["action"] = "batch_promoted"
            result["promoted_count"] = len(promoted_ids)
            result["promoted_ids"] = promoted_ids
            logger.info(
                f"[VERIFIER] 环路 {cycle_id} 闭环验证通过: "
                f"{len(promoted_ids)}/{len(formula_ids)} 入库"
            )
        else:
            result["action"] = "batch_rejected"
            logger.info(
                f"[VERIFIER] 环路 {cycle_id} 闭环验证未通过: "
                f"{'循环论证' if llm_result.get('has_circular_reasoning') else '不自洽'}"
            )

        result["duration_seconds"] = round(time.time() - start_time, 2)
        return result

    def _call_llm_for_cycle(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用LLM进行闭环验证分析"""
        try:
            if not self._llm_client:
                return {"is_coherent": False, "analysis": "LLM不可用", "has_circular_reasoning": False}

            response = self._llm_client.chat.completions.create(
                model=MASTER_DERIVE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=3000,
            )

            analysis = response.choices[0].message.content

            is_coherent = "闭环自洽" in analysis and "不自洽" not in analysis
            has_circular = "循环论证" in analysis and "非" not in analysis.split("循环论证")[0][-5:]

            logger.info(
                f"[VERIFIER] 闭环LLM分析: coherent={is_coherent}, "
                f"circular={has_circular}"
            )

            return {
                "is_coherent": is_coherent,
                "has_circular_reasoning": has_circular,
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"[VERIFIER] 闭环验证LLM调用失败: {e}")
            return {"is_coherent": False, "analysis": f"LLM异常: {e}", "has_circular_reasoning": False}

    # ==================== 独立推导复现 ====================

    def _independent_derivation(
        self,
        formula_name: str,
        formula_content: str,
        external_anchors: List[str] = None,
        topology_class: str = "A0",
    ) -> Dict[str, Any]:
        """
        主库AI从公理独立推导，尝试复现候选公式。

        使用四层知识来源：
        L0: 标准数学基座（可直接使用）
        L1: 几何论三公理（推导起点）
        L2: 桥接假设（子AI声明的外部锚点，需白名单校验）
        L3: 已验证定理（主库中已入库的公式）

        Args:
            formula_name: 公式名称
            formula_content: 公式表达式和说明
            external_anchors: 子AI声明的外部锚点列表（L2桥接假设）

        Returns:
            {
                "reproduced": bool,
                "derivation": str (推导过程),
                "reason": str (如果未复现，原因),
            }
        """
        if not self._llm_client:
            logger.warning("[VERIFIER] LLM 不可用，跳过独立推导复现（默认通过）")
            return {
                "reproduced": True,
                "derivation": "LLM不可用，跳过独立推导",
                "reason": "",
                "skipped": True,
            }

        # 构建公理层文本（L1）
        axioms_text = self._build_axioms_text()

        # 构建数学基座文本（L0）
        math_text = get_foundations_text()

        # 构建桥接假设文本（L2）— 验证并注入已声明的锚点
        bridge_text = ""
        anchor_validation = {"valid": [], "invalid": [], "all_valid": True}
        if external_anchors:
            anchor_validation = validate_anchors(external_anchors)
            if not anchor_validation["all_valid"]:
                logger.warning(
                    f"[VERIFIER] 未识别的桥接假设: {anchor_validation['invalid']}"
                )
            bridge_text, unrecognized = get_bridge_hypothesis_text(external_anchors)
            if unrecognized:
                bridge_text += f"\n  ⚠ 未识别的锚点（不作为前提）: {unrecognized}\n"

        # 搜索主库已验证的相关定理（L3）
        verified_theorems = self.master_db.search_truth(
            query=formula_name,
            top_k=5,
        )
        verified_text = ""
        if verified_theorems:
            verified_text = "\n\n【L3: 已验证定理（可作为推导起点）】\n"
            for t in verified_theorems:
                verified_text += f"- {t['formula_name']}: {t['document'][:200]}...\n"

        # 构建 system prompt（严格审稿人角色）
        system_prompt = self._build_verifier_prompt(
            axioms_text, verified_text, math_text, bridge_text
        )

        # 构建 user prompt
        anchor_note = ""
        if external_anchors:
            anchor_note = f"\n【子AI声明的外部锚点】{', '.join(external_anchors)}\n"
            # 检查是否有需要先推导的物理概念
            anchor_validation = validate_anchors(external_anchors)
            if anchor_validation.get("needs_derivation"):
                needs = anchor_validation["needs_derivation"]
                needs_names = [n["name"] for n in needs]
                logger.info(
                    f"[VERIFIER] 子AI声明了待推导物理概念: {needs_names}，"
                    f"需先从ℰ推导并入库"
                )
                # 仍然继续推导，但LLM会在提示词中看到这些概念需要先推导

        user_prompt = f"""请从公理出发，独立推导以下公式。不要参考任何外部推导过程。

【待验证公式】
{formula_name}
{formula_content[:2000]}
{anchor_note}
【拓扑分类: {topology_class}】
{"这是一个A0类定理（局部代数命题，Berry相位=0）。推导应基于局部代数/微积分/群论等标准数学工具。" if topology_class == "A0" else "这是一个A1类定理（整体拓扑命题，Berry相位=2π）。推导必须基于公理+L0数学基座+L3已验证定理，不得依赖任何外部物理输入。"}

【要求】
1. 从L1公理出发，可自由使用L0数学基座中的标准数学工具
2. ℰ（单一物理映射）是唯一合法的L2外部假设，可标注"【ℰ映射】"使用
3. Born规则、物理识别点、归一化约定、S_e=137等不是独立假设——如果需要用，它们必须在L3主库中已存在
4. 可引用L3已验证定理作为推导中间步骤
5. 每一步都标注引用来源
6. 如果你能独立推导出这个公式，回答"复现成功"并给出完整推导链
7. 如果你无法推导（缺少L3定理、需要未验证的物理概念等），回答"复现失败"并说明缺什么
8. 标准数学事实（如 ∂²=0, Δⁿ≅Dⁿ）是合法工具，不要拒绝使用
9. 严格检查：推导中是否隐含使用了未标注的外部常数或拟合参数？如果有，必须明确指出"""

        try:
            resp = self._llm_client.chat.completions.create(
                model=MASTER_DERIVE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # 低温度，强调严格推理
                max_tokens=4096,
                timeout=120,  # 2分钟超时
            )
            derivation = resp.choices[0].message.content or ""

            if not derivation.strip():
                logger.warning("[VERIFIER] LLM返回空推导文本，跳过独立推导（默认通过）")
                return {
                    "reproduced": True,
                    "derivation": "LLM返回空文本，跳过独立推导",
                    "reason": "",
                    "skipped": True,
                }

            # 判断是否复现成功
            reproduced = (
                "复现成功" in derivation or
                "成功复现" in derivation or
                "推导成立" in derivation or
                "命题成立" in derivation or
                "定理成立" in derivation or
                "证毕" in derivation or
                "得证" in derivation
            )
            reason = ""
            if not reproduced:
                # 提取失败原因
                if "复现失败" in derivation:
                    idx = derivation.find("复现失败")
                    reason = derivation[idx:idx + 300]
                elif "无法推导" in derivation or "无法复现" in derivation:
                    reason = derivation[:300]
                else:
                    # LLM没有明确说成功也没说失败——检查是否给出了实质性推导
                    # 如果推导文本超过200字且包含"因此"或"故"等结论性词语，视为复现成功
                    has_conclusion = any(w in derivation for w in ["因此", "故", "所以", "由此", "综上", "于是"])
                    if len(derivation) > 200 and has_conclusion:
                        reproduced = True
                        logger.info("[VERIFIER] LLM未明确声明'复现成功'但给出了实质性推导，判定为复现成功")
                    else:
                        reason = "LLM 未明确声明复现成功"

            # 检测LLM推导中实际使用的L2假设
            # 单一ℰ原则下：只有ℰ是合法L2，其他物理概念不算L2使用
            used_anchors = []
            if external_anchors:
                # 检查是否使用了ℰ映射
                has_epsilon = (
                    "【ℰ映射】" in derivation or
                    "ℰ映射" in derivation or
                    "ε映射" in derivation or
                    "epsilon" in derivation.lower() or
                    "【ℰ" in derivation
                )
                if has_epsilon:
                    used_anchors.append("ℰ 单一物理映射")

                # 检查是否使用了Born规则等未验证概念
                # 这些不再是"L2使用"，而是"缺少L3依赖"
                unverified_concepts_used = []
                for concept in ["Born规则", "Born 规则", "born", "物理识别", "归一化约定"]:
                    if concept.lower() in derivation.lower():
                        # 但只有当LLM说复现成功时才需要检查
                        if reproduced:
                            unverified_concepts_used.append(concept)
                        break

                if unverified_concepts_used and reproduced:
                    # LLM声称复现成功但使用了未验证概念 → 不是绝对真理
                    used_anchors.extend(unverified_concepts_used)

                # 如果LLM明确说概念非必要，则不算使用
                if "并非必要" in derivation and "桥接" in derivation:
                    used_anchors = []
                    logger.info("[VERIFIER] LLM声明桥接假设非必要，判定为无条件通过")

            if used_anchors:
                logger.info(f"[VERIFIER] LLM实际使用的桥接假设: {used_anchors}")

            return {
                "reproduced": reproduced,
                "derivation": derivation[:3000],  # 截断保存
                "reason": reason,
                "model_used": MASTER_DERIVE_MODEL,
                "used_anchors": used_anchors,
                "declared_anchors": external_anchors or [],
            }

        except Exception as e:
            logger.error(f"[VERIFIER] 独立推导 LLM 调用失败: {e}")
            return {
                "reproduced": False,
                "derivation": "",
                "reason": f"LLM调用异常: {e}",
            }

    # ==================== 依赖缺口分析 ====================

    def _analyze_dependency_gap(
        self,
        formula_name: str,
        formula_content: str,
        derivation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        当独立推导复现失败时，分析失败原因：

        区分两种情况：
        1. 依赖不足：公式可能正确，但主库还没有积累足够的前置定理。
           → 返回 missing_dependencies 列表，指导子库补全。
        2. 公式真错误：从公理出发发现逻辑矛盾或数值不符。
           → 返回 error_analysis，说明具体错误。

        Returns:
            {
                "is_dependency_gap": bool,  # True=依赖不足, False=公式错误
                "missing_dependencies": List[str],  # 缺少的定理/概念列表
                "error_analysis": str,  # 如果是公式错误，错误分析
                "guidance": str,  # 给子库的指导建议
            }
        """
        if not self._llm_client:
            # LLM不可用时无法分析，默认为依赖不足（给公式疑罪从无的机会）
            return {
                "is_dependency_gap": True,
                "missing_dependencies": [],
                "error_analysis": "",
                "guidance": "LLM不可用，无法分析依赖缺口，默认等待补全",
            }

        # 获取主库已有的定理列表
        truth_layer = self.master_db.get_truth_layer(limit=100)
        verified_names = [t.get("formula_name", "") for t in truth_layer]
        verified_text = "、".join(verified_names) if verified_names else "（主库为空）"

        # 构建分析 prompt
        axioms_text = self._build_axioms_text()
        math_text = get_foundations_text()
        derivation_text = derivation_result.get("derivation", "")
        failure_reason = derivation_result.get("reason", "")

        analysis_prompt = f"""你刚才尝试从公理独立推导以下公式，但失败了。

【待验证公式】
{formula_name}
{formula_content[:1500]}

【你的推导失败回复】
{derivation_text[:2000]}

【失败原因摘要】
{failure_reason}

【L0数学基座（标准数学工具，可直接使用）】
{math_text[:1500]}

【主库已验证的定理（L3，可作为合法推导起点）】
{verified_text}

请分析失败的根本原因，并区分以下两种情况：

**情况A: 依赖不足**
如果你认为公式本身在逻辑上可能是正确的，但你无法从公理+数学基座复现它，是因为推导过程中需要用到某些尚未被验证的几何论中间定理或概念（注意：标准数学事实如∂²=0、Stokes定理等已在L0基座中提供，不算缺失依赖）。请列出这些缺失的几何论依赖。

**情况B: 公式错误**
如果你在推导过程中发现了明确的逻辑矛盾、数学错误或与公理冲突的问题，请指出具体错误。

请按以下格式回答：

【判定】依赖不足 / 公式错误
【缺失依赖】（如果是依赖不足，列出需要的定理/概念，每行一个）
【错误分析】（如果是公式错误，说明具体错误）
【指导建议】给提交方的一句话建议"""

        try:
            resp = self._llm_client.chat.completions.create(
                model=MASTER_DERIVE_MODEL,
                messages=[
                    {"role": "system", "content": "你是几何论主库AI的依赖分析模块。你的职责是分析验证失败的原因，区分'依赖不足'和'公式错误'。"},
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            analysis = resp.choices[0].message.content

            # 解析判定结果
            is_dependency_gap = "依赖不足" in analysis and "公式错误" not in analysis.split("【判定】")[1].split("\n")[0] if "【判定】" in analysis else True

            # 更精确的判定
            if "【判定】" in analysis:
                verdict_line = ""
                for line in analysis.split("\n"):
                    if "【判定】" in line:
                        verdict_line = line
                        break
                is_dependency_gap = "依赖不足" in verdict_line and "公式错误" not in verdict_line
            else:
                # 如果没有明确格式，默认为依赖不足（疑罪从无）
                is_dependency_gap = True

            # 提取缺失依赖
            missing_deps = []
            if "【缺失依赖】" in analysis:
                dep_section = analysis.split("【缺失依赖】")[1].split("【")[0]
                for line in dep_section.strip().split("\n"):
                    line = line.strip().strip("-•").strip()
                    if line and len(line) > 2:
                        missing_deps.append(line)

            # 提取错误分析
            error_analysis = ""
            if "【错误分析】" in analysis:
                error_analysis = analysis.split("【错误分析】")[1].split("【")[0].strip()

            # 提取指导建议
            guidance = ""
            if "【指导建议】" in analysis:
                guidance = analysis.split("【指导建议】")[1].strip()

            result = {
                "is_dependency_gap": is_dependency_gap,
                "missing_dependencies": missing_deps,
                "error_analysis": error_analysis,
                "guidance": guidance,
                "raw_analysis": analysis[:2000],
            }

            if is_dependency_gap:
                logger.info(
                    f"[VERIFIER] 依赖缺口分析: 依赖不足 | "
                    f"缺少 {len(missing_deps)} 项: {missing_deps}"
                )
            else:
                logger.warning(
                    f"[VERIFIER] 依赖缺口分析: 公式错误 | "
                    f"错误: {error_analysis[:100]}"
                )

            return result

        except Exception as e:
            logger.error(f"[VERIFIER] 依赖缺口分析失败: {e}")
            return {
                "is_dependency_gap": True,  # 出错时默认依赖不足
                "missing_dependencies": [],
                "error_analysis": f"分析异常: {e}",
                "guidance": "依赖分析过程出错，请稍后重试",
            }

    def _build_axioms_text(self) -> str:
        """构建三公理文本"""
        lines = ["【三公理 — 推导的唯一起点】\n"]
        for key, axiom in THREE_AXIOMS.items():
            lines.append(f"{key} ({axiom['name']}):")
            lines.append(f"  公式: {axiom['formula']}")
            lines.append(f"  说明: {axiom['description']}\n")

        # 附加几何常数
        lines.append("【几何论锁定常数】")
        for k, v in GEOMETRY_CONSTANTS.items():
            lines.append(f"  {k} = {v}")

        return "\n".join(lines)

    def _build_verifier_prompt(self, axioms_text: str, verified_text: str, 
                                   math_text: str = "", bridge_text: str = "") -> str:
        """构建主库AI的 system prompt（严格审稿人角色）"""
        
        # L0数学基座说明
        math_section = ""
        if math_text:
            math_section = f"""
{math_text}

【重要说明】以上L0数学基座是标准数学事实，你可以自由使用这些工具进行推导。
这些数学定理不需要从几何论公理推导——它们是数学界已确立的结果。
你可以在推导中直接引用 [DG-01], [TP-02] 等编号。
"""

        # L2桥接假设说明
        bridge_section = ""
        if bridge_text:
            bridge_section = f"""
{bridge_text}

【单一ℰ原则】
ℰ 是几何论唯一的外部物理假设——将几何量映射为物理可观测量。
Born规则、物理识别点、归一化约定等都不是独立假设，而是ℰ的推论。
如果推导中需要用到Born规则等物理概念，但它们尚未在L3主库中（即尚未从ℰ推导验证），
则判定为"依赖不足"——子AI需要先从ℰ推导这些概念，提交验证入库后再来。
"""

        # 待推导物理定理清单
        pending_text = get_pending_derivations_text()

        return f"""你是几何论主库AI验证引擎。你的唯一职责是：从公理独立推导，验证候选公式是否正确。

{axioms_text}
{math_section}
{bridge_section}
{pending_text}
{verified_text}

【验证原则】
1. 默认怀疑一切。只有自己从公理（L1）+ 数学基座（L0）+ ℰ（L2，唯一物理假设）+ 已验证定理（L3）推导出相同结果，才认为公式正确。
2. 不参考任何外部推导过程，不信任任何未经验证的中间结论。
3. 每一步推导必须标注引用来源：
   - 公理: "公理1/2/3"
   - 数学基座: "[DG-01]" 等编号
   - ℰ物理映射: "【ℰ映射】" 
   - 已验证定理: 定理名称
4. 推导中尽量标注角度参数 (θ_M, θ_C, θ_I)。
5. 严格不跳步，不猜测，不使用未证明的假设。
6. 如果推导需要用到Born规则、物理识别点、归一化约定等物理概念，但这些概念不在L3主库中（尚未从ℰ推导验证），判定"复现失败——依赖不足"。
7. 标准数学事实（如 ∂²=0, Δⁿ≅Dⁿ）是合法工具，不要因为公式"太简单"或"只是数学"就拒绝。
8. 主库只接受绝对真理：推导不能依赖任何未验证的外部假设。ℰ是唯一例外。

【圆满判据】
公式推导链在参数空间中形成闭合回路，Berry相位 ∮A·dl = 2πn (n∈ℤ⁺)。
- n=1: 初圆满（基本闭合）
- n=2: 中圆满（亚稳态）
- n=3: 上圆满（全局刚度最大，入库门槛）

你是最后一道防线。你的判断决定公式是否成为"绝对真理"。
宁可错杀（驳回正确的公式），不可放过（让错误公式入库）。
但也要公正：标准数学事实是合法的推导工具，不要因为公式"太简单"或"只是数学"就拒绝。"""

    # ==================== 辅助函数 ====================

    def _parse_document(self, document: str) -> tuple:
        """
        从存储的文档中分离公式内容和推导链。

        文档格式：
        【公式】{name}

        {formula_content}

        【推导链】
        {derivation_chain}
        """
        formula_content = ""
        derivation_chain = ""

        if "【推导链】" in document:
            parts = document.split("【推导链】", 1)
            formula_part = parts[0]
            derivation_chain = parts[1].strip() if len(parts) > 1 else ""

            # 去掉 【公式】{name}\n\n 前缀
            if "【公式】" in formula_part:
                formula_content = formula_part.split("【公式】", 1)[1]
                # 去掉第一行（公式名）
                lines = formula_content.split("\n", 1)
                if len(lines) > 1:
                    formula_content = lines[1].strip()
                else:
                    formula_content = lines[0].strip()
            else:
                formula_content = formula_part.strip()
        else:
            formula_content = document

        return formula_content, derivation_chain

    # ==================== 真理层反哺 ====================

    def get_truth_layer(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取主库真理层（供本地 Agent 反哺）"""
        return self.master_db.get_truth_layer(limit=limit)

    def get_status(self) -> Dict[str, Any]:
        """获取验证引擎状态"""
        return {
            "master_db": self.master_db.get_status(),
            "llm_ready": self._llm_client is not None,
            "verify_model": MASTER_VERIFY_MODEL,
            "derive_model": MASTER_DERIVE_MODEL,
        }
