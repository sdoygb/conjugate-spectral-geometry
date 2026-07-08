"""
master_db.py — 主库数据库管理

主库是 append-only 的：公式一旦通过验证写入，不可修改、不可删除。
如果后来发现问题，标记为 "suspended"（存疑），但记录保留。

主库 ChromaDB 包含两个 collection：
  - master_formulas: 已通过上圆满验证的公式（只读真理层）
  - pending_submissions: 待验证的候选公式（临时存储）
"""
import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from config import (
    logger,
    MASTER_DB_DIR,
    SILICONFLOW_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    GEOMETRY_CONSTANTS,
)

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.error("[MASTER-DB] chromadb 未安装，主库不可用")


class MasterDatabase:
    """
    主库数据库：存储经过上圆满验证的绝对真理公式。

    设计原则：
    1. append-only: 写入后不可修改，只能标记状态
    2. 只读真理层: 已验证公式对本地 Agent 只读开放
    3. 可追溯: 每条记录包含完整推导链和验证日志
    """

    def __init__(self):
        self.persist_dir = MASTER_DB_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = None
        self.master_collection = None     # 已验证公式（只读真理层）
        self.pending_collection = None    # 待验证候选公式
        self.suspended_set = set()        # 被标记存疑的公式ID
        self._initialized = False
        self._embedding_fn = None

        self._init_embedding()
        self._init_db()

    def _init_embedding(self):
        """初始化 SiliconFlow embedding（与本地一致，1024维）"""
        if not SILICONFLOW_API_KEY:
            logger.warning("[MASTER-DB] SILICONFLOW_API_KEY 未配置，向量检索不可用")
            return
        try:
            import openai
            self._embedding_fn = _SiliconFlowEmbedding(
                api_key=SILICONFLOW_API_KEY,
                model=EMBEDDING_MODEL,
            )
            logger.info(f"[MASTER-DB] Embedding 就绪: {EMBEDDING_MODEL} ({EMBEDDING_DIM}维)")
        except Exception as e:
            logger.error(f"[MASTER-DB] Embedding 初始化失败: {e}")

    def _init_db(self):
        """初始化 ChromaDB 和 collection"""
        if not CHROMADB_AVAILABLE:
            return
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            col_kwargs = {}
            if self._embedding_fn:
                col_kwargs["embedding_function"] = self._embedding_fn

            self.master_collection = self.client.get_or_create_collection(
                name="master_formulas",
                metadata={"description": "上圆满验证通过的绝对真理公式（只读）"},
                **col_kwargs
            )
            self.pending_collection = self.client.get_or_create_collection(
                name="pending_submissions",
                metadata={"description": "待验证的候选公式（临时存储）"},
                **col_kwargs
            )
            # PIA: 物理识别锚点（唯一允许的物理映射，与公理并列但性质不同）
            # 全局只允许注册一个PIA——注册后锁死，不再允许新的物理映射
            self.pia_collection = self.client.get_or_create_collection(
                name="pia_registry",
                metadata={"description": "物理识别锚点注册表（全局唯一，锁死后不可新增）"},
            )
            self._load_suspended()
            self._initialized = True
            logger.info(
                f"[MASTER-DB] 初始化完成 | "
                f"已验证公式: {self.master_collection.count()} | "
                f"待验证: {self.pending_collection.count()}"
            )
        except Exception as e:
            logger.error(f"[MASTER-DB] 初始化失败: {e}")

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def master_count(self) -> int:
        if self.master_collection:
            return self.master_collection.count()
        return 0

    # ==================== 候选公式提交 ====================

    def submit_candidate(
        self,
        formula_name: str,
        formula_content: str,
        derivation_chain: str,
        source_agent: str = "unknown",
        local_verification: Optional[Dict] = None,
        external_anchors: Optional[List[str]] = None,
        topology_class: str = "A0",
    ) -> str:
        """
        本地 Agent 提交候选公式到待验证队列。

        提交时自动做嵌入相似度检查：
        - >0.98 与已入库定理精确重复 → 拒收，返回duplicate
        - 0.85-0.98 疑似重复 → 标记suspected_duplicate，验证时LLM判断等价性
        - <0.85 正常提交

        Args:
            formula_name: 公式名称/标题
            formula_content: 公式的数学表达式和推导过程
            derivation_chain: 推导链（引用了哪些公理/定理）
            source_agent: 提交方标识
            local_verification: 本地自检结果（初圆满检测结果）
            external_anchors: 子AI声明的外部锚点列表（L2桥接假设）
            topology_class: 拓扑分类 A0（局部代数，Berry相位=0）或 A1（整体拓扑，Berry相位=2π）

        Returns:
            submission_id: 提交ID，用于后续查询验证状态
        """
        submission_id = hashlib.md5(
            f"{formula_name}{time.time()}".encode()
        ).hexdigest()[:16]

        # ---- 嵌入相似度去重检查 ----
        doc_text = f"【公式】{formula_name}\n\n{formula_content}\n\n【推导链】\n{derivation_chain}"
        suspected_duplicate_of = ""
        duplicate_status = ""

        try:
            # 查询已入库定理中的相似项
            query_result = self.master_collection.query(
                query_texts=[doc_text],
                n_results=3,
                include=["metadatas", "distances"],
            )

            if query_result["distances"] and query_result["distances"][0]:
                best_distance = query_result["distances"][0][0]
                # ChromaDB默认用余弦距离，distance越小越相似
                # 转换为相似度: similarity = 1 - distance/2 (余弦距离范围0-2)
                best_similarity = 1 - best_distance / 2

                if best_similarity > 0.98:
                    # 精确重复——拒收
                    existing_id = query_result["ids"][0][0]
                    existing_name = query_result["metadatas"][0][0].get("formula_name", "")
                    logger.info(
                        f"[MASTER-DB] 精确重复拒收: {formula_name} ≈ {existing_name} "
                        f"(similarity={best_similarity:.4f})"
                    )
                    # 仍创建pending记录但标记为duplicate，方便子AI看到
                    metadata = {
                        "submission_id": submission_id,
                        "formula_name": formula_name,
                        "source_agent": source_agent,
                        "status": "duplicate",
                        "submitted_at": datetime.now().isoformat(),
                        "local_verification": json.dumps(local_verification or {}, ensure_ascii=False),
                        "external_anchors": json.dumps(external_anchors or [], ensure_ascii=False),
                        "topology_class": topology_class,
                        "duplicate_of": existing_id,
                        "duplicate_similarity": str(round(best_similarity, 4)),
                    }
                    self.pending_collection.add(
                        ids=[submission_id],
                        documents=[doc_text],
                        metadatas=[metadata],
                    )
                    return submission_id

                elif best_similarity > 0.85:
                    # 疑似重复——标记，验证时LLM判断
                    suspected_duplicate_of = query_result["ids"][0][0]
                    duplicate_status = "suspected_duplicate"
                    logger.info(
                        f"[MASTER-DB] 疑似重复: {formula_name} ≈ "
                        f"{query_result['metadatas'][0][0].get('formula_name', '')} "
                        f"(similarity={best_similarity:.4f})"
                    )
        except Exception as e:
            logger.warning(f"[MASTER-DB] 去重检查异常: {e}")

        metadata = {
            "submission_id": submission_id,
            "formula_name": formula_name,
            "source_agent": source_agent,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
            "local_verification": json.dumps(local_verification or {}, ensure_ascii=False),
            "external_anchors": json.dumps(external_anchors or [], ensure_ascii=False),
            "topology_class": topology_class,
            "suspected_duplicate_of": suspected_duplicate_of,
        }

        # 存储完整内容到 metadata 的 json 字段
        doc_text = f"【公式】{formula_name}\n\n{formula_content}\n\n【推导链】\n{derivation_chain}"

        self.pending_collection.add(
            ids=[submission_id],
            documents=[doc_text],
            metadatas=[metadata],
        )
        logger.info(f"[MASTER-DB] 收到候选公式: {formula_name} (id={submission_id}, from={source_agent})")
        return submission_id

    def get_pending(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """获取待验证公式的完整信息"""
        result = self.pending_collection.get(
            ids=[submission_id],
            include=["documents", "metadatas"]
        )
        if not result["ids"]:
            return None
        return {
            "submission_id": submission_id,
            "document": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    def list_pending(self, limit: int = 500) -> List[Dict[str, Any]]:
        """列出所有待验证的候选公式（含验证结果摘要）"""
        result = self.pending_collection.get(
            include=["metadatas"],
            limit=limit
        )
        items = []
        for i, mid in enumerate(result["ids"]):
            meta = result["metadatas"][i]
            item = {
                "submission_id": mid,
                "formula_name": meta.get("formula_name", ""),
                "source_agent": meta.get("source_agent", ""),
                "topology_class": meta.get("topology_class", ""),
                "status": meta.get("status", "pending"),
                "submitted_at": meta.get("submitted_at", ""),
                "processed_at": meta.get("processed_at", ""),
            }
            # 包含外部锚点
            anchors_str = meta.get("external_anchors", "")
            if anchors_str:
                try:
                    item["external_anchors"] = json.loads(anchors_str) if isinstance(anchors_str, str) else anchors_str
                except:
                    item["external_anchors"] = []
            # 包含驳回原因
            if meta.get("rejection_reason"):
                item["rejection_reason"] = meta["rejection_reason"]
            # 包含依赖缺口
            if meta.get("dependency_gap"):
                try:
                    item["dependency_gap"] = json.loads(meta["dependency_gap"]) if isinstance(meta["dependency_gap"], str) else meta["dependency_gap"]
                except:
                    item["dependency_gap"] = {"raw": str(meta["dependency_gap"])[:500]}
            # 包含验证结果摘要
            if meta.get("verification_result"):
                try:
                    vr = json.loads(meta["verification_result"]) if isinstance(meta["verification_result"], str) else meta["verification_result"]
                    stages = vr.get("stages", {})
                    item["verification_summary"] = {
                        "berry_check": stages.get("berry_check", {}).get("consummation_level", ""),
                        "berry_n_value": stages.get("berry_check", {}).get("n_value", 0),
                        "berry_passed": stages.get("berry_check", {}).get("is_consummated", False),
                        "berry_skipped": stages.get("berry_check", {}).get("skipped", False),
                        "falsification_passed": stages.get("falsification", {}).get("all_passed", False),
                        "derivation_reproduced": stages.get("independent_derivation", {}).get("reproduced", False),
                        "derivation_skipped": stages.get("independent_derivation", {}).get("skipped", False),
                        "dependency_gap": stages.get("dependency_gap_analysis", {}).get("is_dependency_gap", False),
                        "missing_dependencies": stages.get("dependency_gap_analysis", {}).get("missing_dependencies", []),
                        "action": vr.get("action", ""),
                        "message": vr.get("message", ""),
                        "used_anchors": vr.get("used_anchors", []),
                    }
                except:
                    pass
            items.append(item)
        return items

    # ==================== 验证入库 ====================

    def promote_to_master(
        self,
        submission_id: str,
        verification_result: Dict[str, Any],
    ) -> str:
        """
        将通过验证的候选公式晋升到主库（append-only）。

        Args:
            submission_id: 候选公式ID
            verification_result: 主库AI的完整验证结果

        Returns:
            master_id 如果成功入库，空字符串如果失败
        """
        pending = self.get_pending(submission_id)
        if not pending:
            logger.error(f"[MASTER-DB] 候选公式不存在: {submission_id}")
            return ""

        # 生成主库公式ID（不可变）
        formula_name = pending["metadata"].get("formula_name", "unnamed")
        master_id = f"master_{hashlib.md5(formula_name.encode()).hexdigest()[:12]}"

        # 检查是否已存在（同名公式不重复入库）
        existing = self.master_collection.get(ids=[master_id], include=["metadatas"])
        if existing["ids"]:
            logger.warning(f"[MASTER-DB] 公式已存在: {formula_name} (id={master_id})，跳过重复入库")
            # 更新待验证状态为 duplicate
            self._update_pending_status(submission_id, "duplicate")
            return ""

        # 组装主库记录
        # 提取Berry角度数据用于长期积累
        berry_data = verification_result.get("stages", {}).get("berry_check", {})
        angle_points = berry_data.get("path_points", [])
        berry_phase = berry_data.get("berry_phase", 0.0)
        berry_n = berry_data.get("n_value", 0)
        berry_status = berry_data.get("status", "no_angle_data")

        master_metadata = {
            "master_id": master_id,
            "formula_name": formula_name,
            "source_agent": pending["metadata"].get("source_agent", ""),
            "verified_at": datetime.now().isoformat(),
            "verification_result": json.dumps(verification_result, ensure_ascii=False),
            "status": "verified",
            "original_submission": submission_id,
            # 拓扑分类（Berry相位锚点体系）
            "topology_class": pending["metadata"].get("topology_class", "A0"),
            # Berry角度积累数据
            "berry_status": berry_status,
            "berry_phase": str(berry_phase),
            "berry_n_value": str(berry_n),
            "berry_path_points": json.dumps(angle_points, ensure_ascii=False) if angle_points else "[]",
            # 来源溯源（Berry相位第一层检查）
            "source_trace": "[]",  # 初始为空，后续通过annotate_source填充
            "source_risk_level": "unaudited",  # unaudited / clean / low / medium / high
            "berry_closure": "pending",  # pending / closed / broken
        }

        self.master_collection.add(
            ids=[master_id],
            documents=[pending["document"]],
            metadatas=[master_metadata],
        )

        # 更新待验证状态
        self._update_pending_status(submission_id, "promoted")

        logger.info(
            f"[MASTER-DB] 公式晋升入库: {formula_name} → {master_id} | "
            f"主库总数: {self.master_collection.count()}"
        )
        return master_id

    def reject_candidate(
        self,
        submission_id: str,
        rejection_reason: str,
        verification_result: Dict[str, Any],
    ) -> bool:
        """驳回候选公式，附驳回理由"""
        self._update_pending_status(
            submission_id,
            "rejected",
            rejection_reason=rejection_reason,
            verification_result=verification_result,
        )
        logger.info(f"[MASTER-DB] 公式被驳回: {submission_id} | 理由: {rejection_reason[:100]}")
        return True

    def _update_pending_status(
        self,
        submission_id: str,
        status: str,
        **extra,
    ):
        """更新待验证公式的状态"""
        pending = self.get_pending(submission_id)
        if not pending:
            return
        meta = pending["metadata"]
        meta["status"] = status
        meta["processed_at"] = datetime.now().isoformat()
        for k, v in extra.items():
            meta[k] = v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)
        # ChromaDB 的 update
        self.pending_collection.update(
            ids=[submission_id],
            metadatas=[meta],
        )

    # ==================== 真理层读取（反哺） ====================

    def get_truth_layer(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取主库真理层快照（供本地 Agent 反哺使用）。
        只返回 status=verified 且未被 suspend 的公式。
        """
        if not self.master_collection:
            return []
        result = self.master_collection.get(
            include=["documents", "metadatas"],
            limit=limit
        )
        items = []
        for i, mid in enumerate(result["ids"]):
            meta = result["metadatas"][i]
            if mid in self.suspended_set or meta.get("status") == "suspended":
                continue
            items.append({
                "master_id": mid,
                "formula_name": meta.get("formula_name", ""),
                "document": result["documents"][i],
                "verified_at": meta.get("verified_at", ""),
                "berry_status": meta.get("berry_status", "no_angle_data"),
                "berry_phase": float(meta.get("berry_phase", "0")),
                "berry_n_value": int(meta.get("berry_n_value", "0")),
                "berry_path_points": json.loads(meta.get("berry_path_points", "[]")) if meta.get("berry_path_points") else [],
                "source_trace": json.loads(meta.get("source_trace", "[]")) if meta.get("source_trace") else [],
                "source_risk_level": meta.get("source_risk_level", "unaudited"),
                "berry_closure": meta.get("berry_closure", "pending"),
            })
        return items

    def search_truth(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """在主库真理层中语义搜索（供主库AI推导时引用已验证定理）"""
        if not self.master_collection or not self._embedding_fn:
            return []
        results = self.master_collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        items = []
        for i, mid in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            if mid in self.suspended_set or meta.get("status") == "suspended":
                continue
            items.append({
                "master_id": mid,
                "formula_name": meta.get("formula_name", ""),
                "document": results["documents"][0][i],
                "distance": results["distances"][0][i],
            })
        return items

    # ==================== 物理识别锚点（PIA） ====================

    def register_pia(
        self,
        pia_id: str,
        name: str,
        geometric_content: str,
        physical_identification: str,
        geometric_theorem_id: str = "",
    ) -> Dict[str, Any]:
        """
        注册物理识别锚点（PIA）。

        PIA是几何→物理的桥接规则，与公理1-3并列但性质不同：
        - 公理定义几何结构（数学命题，可验证）
        - PIA定义几何→物理的对应（语义声明，不可验证，只能登记）

        全局只允许一个PIA。注册后锁死，不再允许新的物理映射。
        这保证了框架的"单一物理映射"原则——以后不再引入物理量和物理映射。

        Args:
            pia_id: PIA标识（如 "ℰ"）
            name: 名称（如 "单一物理映射"）
            geometric_content: 几何内容描述（如 "S_e=137.036，六项作用量Dixmier迹极值"）
            physical_identification: 物理识别声明（如 "S_e ↦ α⁻¹（精细结构常数倒数）"）
            geometric_theorem_id: 对应的已入库几何定理ID（如ℰ_geo的master_id）

        Returns:
            {"success": bool, "message": str, "locked": bool}
        """
        # 检查是否已有PIA注册
        existing = self.pia_collection.get(include=["metadatas"])
        if existing["ids"]:
            # 已有PIA——锁死，不允许新增
            existing_meta = existing["metadatas"][0]
            return {
                "success": False,
                "message": (
                    f"PIA已锁死。已注册: {existing_meta.get('pia_id', '')} "
                    f"({existing_meta.get('name', '')})。"
                    f"框架只允许单一物理映射，不再接受新的PIA注册。"
                ),
                "locked": True,
                "existing": {
                    "pia_id": existing_meta.get("pia_id", ""),
                    "name": existing_meta.get("name", ""),
                    "registered_at": existing_meta.get("registered_at", ""),
                },
            }

        # 注册新PIA
        metadata = {
            "pia_id": pia_id,
            "name": name,
            "geometric_content": geometric_content,
            "physical_identification": physical_identification,
            "geometric_theorem_id": geometric_theorem_id,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "locked": "true",  # 注册后锁死
        }

        self.pia_collection.add(
            ids=[pia_id],
            documents=[f"PIA: {name}\n几何内容: {geometric_content}\n物理识别: {physical_identification}"],
            metadatas=[metadata],
        )

        logger.info(
            f"[MASTER-DB] PIA注册成功: {pia_id} ({name})。"
            f"框架已锁死，不再接受新的物理映射。"
        )

        return {
            "success": True,
            "message": f"PIA {pia_id} 注册成功。框架已锁死，不再接受新的物理映射。",
            "locked": True,
            "pia_id": pia_id,
        }

    def get_pia(self) -> Optional[Dict[str, Any]]:
        """获取已注册的PIA（如果有）"""
        if not self.pia_collection:
            return None
        result = self.pia_collection.get(include=["metadatas", "documents"])
        if not result["ids"]:
            return None
        meta = result["metadatas"][0]
        return {
            "pia_id": meta.get("pia_id", ""),
            "name": meta.get("name", ""),
            "geometric_content": meta.get("geometric_content", ""),
            "physical_identification": meta.get("physical_identification", ""),
            "geometric_theorem_id": meta.get("geometric_theorem_id", ""),
            "registered_at": meta.get("registered_at", ""),
            "locked": meta.get("locked", "false") == "true",
            "document": result["documents"][0] if result["documents"] else "",
        }

    def is_pia_registered(self) -> bool:
        """检查PIA是否已注册（用于验证器判断ℰ是否合法）"""
        return self.get_pia() is not None

    # ==================== 替代证明 & 定期自查 ====================

    def add_alternative_proof(
        self,
        master_id: str,
        proof_data: Dict[str, Any],
    ) -> bool:
        """
        为已入库定理附加替代证明。

        当一个公式验证通过，但真理库中已存在数学等价的定理时，
        不重复入库，而是把新的证明方法附加到已有定理上。

        Args:
            master_id: 已有定理的master_id
            proof_data: {
                "method": "推导方法描述",
                "derivation_chain": "推导链",
                "source_agent": "提交者",
                "verification_result": {...},
                "submission_id": "原始提交ID",
            }
        """
        result = self.master_collection.get(ids=[master_id], include=["metadatas"])
        if not result["ids"]:
            logger.warning(f"[MASTER-DB] 替代证明失败: 定理不存在 {master_id}")
            return False

        meta = result["metadatas"][0]
        existing_proofs = json.loads(meta.get("alternative_proofs", "[]"))
        proof_id = f"proof_{len(existing_proofs) + 2}"  # proof_1是原始证明
        proof_data["proof_id"] = proof_id
        proof_data["added_at"] = datetime.now().isoformat()
        existing_proofs.append(proof_data)

        meta["alternative_proofs"] = json.dumps(existing_proofs, ensure_ascii=False)
        meta["proof_count"] = str(len(existing_proofs) + 1)  # +1 for original

        self.master_collection.update(ids=[master_id], metadatas=[meta])

        logger.info(
            f"[MASTER-DB] 替代证明附加: {meta.get('formula_name', '')} "
            f"← {proof_data.get('method', '')} (from {proof_data.get('source_agent', '')})"
        )
        return True

    def find_similar_in_master(
        self,
        text: str,
        threshold: float = 0.85,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        在已入库定理中查找与给定文本相似的内容。

        Returns:
            [{"master_id", "formula_name", "similarity", "metadata"}]
        """
        try:
            query_result = self.master_collection.query(
                query_texts=[text],
                n_results=limit,
                include=["metadatas", "distances"],
            )

            results = []
            if not query_result["distances"] or not query_result["distances"][0]:
                return results

            for i, dist in enumerate(query_result["distances"][0]):
                similarity = 1 - dist / 2
                if similarity >= threshold:
                    meta = query_result["metadatas"][0][i]
                    results.append({
                        "master_id": query_result["ids"][0][i],
                        "formula_name": meta.get("formula_name", ""),
                        "similarity": round(similarity, 4),
                        "metadata": meta,
                    })

            return results
        except Exception as e:
            logger.warning(f"[MASTER-DB] 相似度查询异常: {e}")
            return []

    def self_audit(self) -> Dict[str, Any]:
        """
        定期自查：扫描已入库定理，发现重复/近似/多证。

        对每对相似度>0.85的定理进行分类：
        - >0.98: 精确重复 → 建议合并
        - 0.90-0.98: 近似重复 → 需要LLM判断等价性
        - 0.85-0.90: 相关定理 → 可能是不同表述或相关结论

        Returns:
            {
                "total_audited": int,
                "exact_duplicates": [...],
                "suspected_duplicates": [...],
                "related_theorems": [...],
                "multi_proof_theorems": [...],
                "suggestions": [...],
            }
        """
        all_formulas = self.master_collection.get(
            include=["metadatas", "documents"],
        )

        total = len(all_formulas["ids"])
        logger.info(f"[SELF-AUDIT] 开始自查: {total}个已入库定理")

        exact_duplicates = []
        suspected_duplicates = []
        related_theorems = []
        multi_proof = []
        suggestions = []

        # 逐对比较
        for i in range(total):
            id_i = all_formulas["ids"][i]
            name_i = all_formulas["metadatas"][i].get("formula_name", "")
            doc_i = all_formulas["documents"][i]

            for j in range(i + 1, total):
                id_j = all_formulas["ids"][j]
                name_j = all_formulas["metadatas"][j].get("formula_name", "")
                doc_j = all_formulas["documents"][j]

                # 快速名称检查
                name_i_short = name_i.split("（")[0].split("(")[0].strip().lower()
                name_j_short = name_j.split("（")[0].split("(")[0].strip().lower()

                # 嵌入相似度检查
                try:
                    query_result = self.master_collection.query(
                        query_texts=[doc_i],
                        n_results=10,
                        include=["metadatas", "distances"],
                    )

                    # 找到j的相似度
                    for k, match_id in enumerate(query_result["ids"][0]):
                        if match_id == id_j:
                            dist = query_result["distances"][0][k]
                            sim = 1 - dist / 2

                            pair = {
                                "theorem_a": {"id": id_i, "name": name_i},
                                "theorem_b": {"id": id_j, "name": name_j},
                                "similarity": round(sim, 4),
                            }

                            if sim > 0.98:
                                pair["type"] = "exact_duplicate"
                                pair["suggestion"] = f"合并: '{name_i}' 和 '{name_j}' 是精确重复"
                                exact_duplicates.append(pair)
                                suggestions.append({
                                    "action": "merge",
                                    "from": id_j,
                                    "into": id_i,
                                    "reason": f"精确重复 (sim={sim:.4f})",
                                })
                            elif sim > 0.90:
                                pair["type"] = "suspected_duplicate"
                                pair["suggestion"] = f"需LLM判断: '{name_i}' 和 '{name_j}' 可能等价"
                                suspected_duplicates.append(pair)
                            elif sim > 0.85:
                                pair["type"] = "related"
                                pair["suggestion"] = f"相关定理: '{name_i}' 和 '{name_j}' 内容接近"
                                related_theorems.append(pair)
                            break
                except:
                    pass

            # 检查多证
            meta_i = all_formulas["metadatas"][i]
            proof_count = int(meta_i.get("proof_count", "1"))
            if proof_count > 1:
                multi_proof.append({
                    "master_id": id_i,
                    "formula_name": name_i,
                    "proof_count": proof_count,
                })

        result = {
            "total_audited": total,
            "exact_duplicates": exact_duplicates,
            "suspected_duplicates": suspected_duplicates,
            "related_theorems": related_theorems,
            "multi_proof_theorems": multi_proof,
            "suggestions": suggestions,
        }

        logger.info(
            f"[SELF-AUDIT] 自查完成: "
            f"精确重复={len(exact_duplicates)}, "
            f"疑似重复={len(suspected_duplicates)}, "
            f"相关={len(related_theorems)}, "
            f"多证={len(multi_proof)}"
        )

        return result

    def merge_theorems(self, from_id: str, into_id: str) -> bool:
        """
        合并两个重复定理。

        把from_id的证明数据和等价表述合并到into_id中，然后删除from_id。

        Args:
            from_id: 被合并的定理ID（将被删除）
            into_id: 保留的定理ID
        """
        result_from = self.master_collection.get(ids=[from_id], include=["metadatas"])
        result_into = self.master_collection.get(ids=[into_id], include=["metadatas"])

        if not result_from["ids"] or not result_into["ids"]:
            logger.warning(f"[MASTER-DB] 合并失败: 定理不存在")
            return False

        meta_from = result_from["metadatas"][0]
        meta_into = result_into["metadatas"][0]

        # 把from的证明作为替代证明附加到into
        from_proofs = json.loads(meta_from.get("alternative_proofs", "[]"))
        into_proofs = json.loads(meta_into.get("alternative_proofs", "[]"))

        # from的原始证明也作为替代证明
        from_original = {
            "proof_id": f"proof_{len(into_proofs) + 2}",
            "method": f"原证明 (from merged {meta_from.get('formula_name', '')})",
            "source_agent": meta_from.get("source_agent", ""),
            "verification_result": meta_from.get("verification_result", ""),
            "added_at": datetime.now().isoformat(),
        }
        into_proofs.append(from_original)
        into_proofs.extend(from_proofs)

        meta_into["alternative_proofs"] = json.dumps(into_proofs, ensure_ascii=False)
        meta_into["proof_count"] = str(len(into_proofs) + 1)

        # 记录合并历史
        merge_history = json.loads(meta_into.get("merge_history", "[]"))
        merge_history.append({
            "merged_from": from_id,
            "merged_name": meta_from.get("formula_name", ""),
            "merged_at": datetime.now().isoformat(),
        })
        meta_into["merge_history"] = json.dumps(merge_history, ensure_ascii=False)

        self.master_collection.update(ids=[into_id], metadatas=[meta_into])

        # 删除被合并的定理
        self.master_collection.delete(ids=[from_id])

        logger.info(
            f"[MASTER-DB] 定理合并: {meta_from.get('formula_name', '')} ({from_id}) → "
            f"{meta_into.get('formula_name', '')} ({into_id})"
        )
        return True

    # ==================== 来源溯源（Berry相位第一层） ====================

    def annotate_source(
        self,
        master_id: str,
        source_trace: List[Dict[str, Any]],
        risk_level: str,
        berry_closure: str,
    ) -> bool:
        """
        为已入库公式标注来源溯源信息。

        source_trace 结构:
        [
            {
                "element": "12",              # 公式中的元素
                "element_type": "coefficient",  # coefficient / form / constant / assumption
                "source": "谱特征值数值匹配",   # 来源描述
                "traceable_to": "external",    # axiom1 / axiom2 / axiom3 / L0_math / L3_ℰ / external
                "is_external_input": True,     # 是否外部输入
                "note": "文章0.0.7§5.2标注为定义性输入"
            },
            ...
        ]

        risk_level: clean / low / medium / high
        berry_closure: closed（无外部输入）/ broken（有外部输入断点）
        """
        result = self.master_collection.get(ids=[master_id], include=["metadatas"])
        if not result["ids"]:
            logger.warning(f"[MASTER-DB] 来源标注失败: 公式不存在 {master_id}")
            return False

        meta = result["metadatas"][0]
        meta["source_trace"] = json.dumps(source_trace, ensure_ascii=False)
        meta["source_risk_level"] = risk_level
        meta["berry_closure"] = berry_closure
        meta["source_audited_at"] = datetime.now().isoformat()

        self.master_collection.update(
            ids=[master_id],
            metadatas=[meta],
        )

        ext_count = sum(1 for s in source_trace if s.get("is_external_input"))
        logger.info(
            f"[MASTER-DB] 来源标注: {meta.get('formula_name', '')[:30]} | "
            f"风险={risk_level} Berry闭合={berry_closure} "
            f"外部输入={ext_count}/{len(source_trace)}"
        )
        return True

    def get_source_audit(self) -> Dict[str, Any]:
        """获取全部公式的来源溯源审计摘要"""
        result = self.master_collection.get(
            include=["metadatas"],
            limit=500,
        )

        total = 0
        risk_counts = {"unaudited": 0, "clean": 0, "low": 0, "medium": 0, "high": 0}
        closure_counts = {"pending": 0, "closed": 0, "broken": 0}
        flagged = []

        for i, mid in enumerate(result["ids"]):
            meta = result["metadatas"][i]
            if meta.get("status") == "suspended":
                continue
            total += 1

            risk = meta.get("source_risk_level", "unaudited")
            closure = meta.get("berry_closure", "pending")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            closure_counts[closure] = closure_counts.get(closure, 0) + 1

            if risk in ("high", "medium") or closure == "broken":
                trace = json.loads(meta.get("source_trace", "[]")) if meta.get("source_trace") else []
                ext_inputs = [t for t in trace if t.get("is_external_input")]
                flagged.append({
                    "master_id": mid,
                    "formula_name": meta.get("formula_name", ""),
                    "risk_level": risk,
                    "berry_closure": closure,
                    "external_inputs": [
                        {"element": t.get("element", ""), "source": t.get("source", "")}
                        for t in ext_inputs
                    ],
                })

        return {
            "total_formulas": total,
            "risk_distribution": risk_counts,
            "closure_distribution": closure_counts,
            "flagged_count": len(flagged),
            "flagged_formulas": flagged,
        }

    # ==================== 存疑管理 ====================

    def suspend_formula(self, master_id: str, reason: str) -> bool:
        """
        将已入库公式标记为存疑（不删除，保留记录）。
        后续依赖此公式的推导需要重新审查。
        """
        result = self.master_collection.get(ids=[master_id], include=["metadatas"])
        if not result["ids"]:
            return False
        meta = result["metadatas"][0]
        meta["status"] = "suspended"
        meta["suspended_at"] = datetime.now().isoformat()
        meta["suspend_reason"] = reason
        self.master_collection.update(ids=[master_id], metadatas=[meta])
        self.suspended_set.add(master_id)
        logger.warning(f"[MASTER-DB] 公式标记存疑: {master_id} | 原因: {reason}")
        return True

    def _load_suspended(self):
        """启动时加载存疑公式集合"""
        if not self.master_collection:
            return
        result = self.master_collection.get(include=["metadatas"])
        for i, mid in enumerate(result["ids"]):
            if result["metadatas"][i].get("status") == "suspended":
                self.suspended_set.add(mid)
        if self.suspended_set:
            logger.warning(f"[MASTER-DB] 加载了 {len(self.suspended_set)} 个存疑公式")

    # ==================== 统计 ====================

    def get_status(self) -> Dict[str, Any]:
        """获取主库状态摘要"""
        return {
            "initialized": self._initialized,
            "master_formulas_count": self.master_count,
            "pending_count": self.pending_collection.count() if self.pending_collection else 0,
            "suspended_count": len(self.suspended_set),
            "embedding_ready": self._embedding_fn is not None,
        }


class _SiliconFlowEmbedding:
    """SiliconFlow embedding（与 app/knowledge.py 保持一致）"""

    def __init__(self, api_key: str, model: str = "BAAI/bge-m3"):
        import openai
        self.client = openai.OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        self.model = model
        self._dim = EMBEDDING_DIM

    def name(self) -> str:
        return f"siliconflow({self.model})"

    def __call__(self, input):
        import re as _re
        all_embeddings = []
        for text in input:
            text = text.replace('\x00', '').replace('\r', '')
            text = _re.sub(r'\s+', ' ', text).strip()
            if len(text) > 2000:
                text = text[:2000]
            if not text:
                all_embeddings.append([0.0] * self._dim)
                continue
            try:
                resp = self.client.embeddings.create(model=self.model, input=[text])
                all_embeddings.extend([d.embedding for d in resp.data])
            except Exception as e:
                logger.warning(f"[MASTER-DB] embedding 失败: {e}")
                all_embeddings.append([0.0] * self._dim)
        return all_embeddings

    def embed_query(self, input: str):
        text = input if isinstance(input, str) else str(input)
        text = text.replace('\x00', '').replace('\r', '')
        import re as _re
        text = _re.sub(r'\s+', ' ', text).strip()
        if len(text) > 2000:
            text = text[:2000]
        try:
            resp = self.client.embeddings.create(model=self.model, input=[text])
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.error(f"[MASTER-DB] embed_query 失败: {e}")
            return [[0.0] * self._dim]
