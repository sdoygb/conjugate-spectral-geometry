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
import threading
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
        # 全局写锁：串行化所有ChromaDB写入，防止SQLite "database is locked"
        self._write_lock = threading.Lock()

        # 永久编号计数器文件（原子递增，永不回收）
        self._seq_file = os.path.join(self.persist_dir, "master_seq.json")

        self._init_embedding()
        self._init_db()
        self._init_seq()

    def _write(self, collection, operation: str, *args, **kwargs):
        """
        串行化ChromaDB写入操作。所有写操作（add/update/delete/upsert）
        必须通过此方法执行，防止多worker并发写入导致SQLite锁冲突。

        读取操作不需要串行化，可以直接调用collection.get/query。
        """
        with self._write_lock:
            method = getattr(collection, operation)
            return method(*args, **kwargs)

    def _init_seq(self):
        """初始化永久编号计数器。为已有公式补编号。"""
        if not os.path.exists(self._seq_file):
            # 首次启动：扫描已有公式，按verified_at排序分配编号
            all_truth = self.master_collection.get(include=["metadatas"]) if self.master_collection else {"ids": [], "metadatas": []}
            existing_nums = []
            max_num = 0
            for mid, meta in zip(all_truth.get("ids", []), all_truth.get("metadatas", [])):
                num = meta.get("permanent_number")
                if num is not None:
                    try:
                        n = int(num)
                        existing_nums.append((mid, n))
                        if n > max_num:
                            max_num = n
                    except (ValueError, TypeError):
                        pass

            if not existing_nums and all_truth.get("ids"):
                # 没有任何编号：按入库顺序分配
                sorted_items = []
                for mid, meta in zip(all_truth["ids"], all_truth["metadatas"]):
                    verified_at = meta.get("verified_at", "")
                    sorted_items.append((mid, verified_at))
                sorted_items.sort(key=lambda x: x[1])

                for i, (mid, _) in enumerate(sorted_items, 1):
                    meta = all_truth["metadatas"][all_truth["ids"].index(mid)]
                    meta["permanent_number"] = str(i)
                    self._write(self.master_collection, 'update', ids=[mid], metadatas=[meta])
                max_num = len(sorted_items)
                logger.info(f"[MASTER-DB] 为 {max_num} 条已有公式分配永久编号 1-{max_num}")

            with open(self._seq_file, 'w') as f:
                json.dump({"next_number": max_num + 1}, f)
            logger.info(f"[MASTER-DB] 永久编号计数器初始化: next={max_num + 1}")

    def _next_seq(self) -> int:
        """原子递增并返回下一个永久编号。调用方必须已持有 _write_lock 或在单线程上下文中。"""
        with open(self._seq_file, 'r') as f:
            data = json.load(f)
        num = data["next_number"]
        data["next_number"] = num + 1
        with open(self._seq_file, 'w') as f:
            json.dump(data, f)
        return num

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
        priority_hint: bool = False,
        interlock_hint: Optional[List[str]] = None,
        interlock_reasoning: str = "",
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
                    self._write(
                        self.pending_collection, 'add',
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
            "priority_hint": str(priority_hint).lower(),
            "verified_priority": "false",  # 主库验证后的实际优先级
            "dependents_count": "0",  # 有多少pending公式依赖这个
            "interlock_hint": json.dumps(interlock_hint or [], ensure_ascii=False),
            "interlock_reasoning": interlock_reasoning or "",
        }

        # 存储完整内容到 metadata 的 json 字段
        doc_text = f"【公式】{formula_name}\n\n{formula_content}\n\n【推导链】\n{derivation_chain}"

        self._write(
            self.pending_collection, 'add',
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

    def list_pending(self, limit: int = 500, include_archived: bool = False) -> List[Dict[str, Any]]:
        """列出所有待验证的候选公式（含验证结果摘要）

        Args:
            limit: 最大返回数
            include_archived: 是否包含已归档/已撤回的记录（默认不包含）
        """
        result = self.pending_collection.get(
            include=["metadatas"],
            limit=limit
        )
        items = []
        hidden_statuses = {"archived", "withdrawn"} if not include_archived else set()
        for i, mid in enumerate(result["ids"]):
            meta = result["metadatas"][i]
            status = meta.get("status", "pending")
            if status in hidden_statuses:
                continue
            item = {
                "submission_id": mid,
                "formula_name": meta.get("formula_name", ""),
                "source_agent": meta.get("source_agent", ""),
                "topology_class": meta.get("topology_class", ""),
                "status": meta.get("status", "pending"),
                "submitted_at": meta.get("submitted_at", ""),
                "processed_at": meta.get("processed_at", ""),
                "priority_hint": meta.get("priority_hint", "false") == "true",
                "verified_priority": meta.get("verified_priority", "false") == "true",
                "dependents_count": int(meta.get("dependents_count", "0")),
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
            # 包含重复信息
            if meta.get("duplicate_of"):
                item["duplicate_of"] = meta["duplicate_of"]
                item["duplicate_similarity"] = meta.get("duplicate_similarity", "")
            # 包含替代证明信息
            if meta.get("suspected_duplicate_of"):
                item["suspected_duplicate_of"] = meta["suspected_duplicate_of"]
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
                        "master_id": vr.get("master_id", ""),
                        "message": vr.get("message", ""),
                        "used_anchors": vr.get("used_anchors", []),
                        "is_interlocked": vr.get("is_interlocked", False),
                        "interlock_type": vr.get("interlock_type", ""),
                        "interlock_group": vr.get("interlock_group", []),
                        "interlock_batch_ready": vr.get("interlock_batch_ready", False),
                    }
                except:
                    pass
            items.append(item)
        return items

    def verify_priority_claims(self) -> Dict[str, Any]:
        """
        验证所有声明了priority_hint的公式，检查它们是否真的被大量pending公式依赖。

        对每个priority_hint=true的pending公式：
        1. 取其formula_name
        2. 在所有其他pending公式的推导链中搜索是否引用了这个名称
        3. 如果被≥2个公式引用，verified_priority=true
        4. 更新dependents_count

        Returns:
            {"verified": int, "rejected": int, "details": [...]}
        """
        all_pending = self.pending_collection.get(include=["metadatas", "documents"])
        if not all_pending["ids"]:
            return {"verified": 0, "rejected": 0, "details": []}

        # 收集所有pending公式的名称和推导链
        all_names = []
        all_chains = []
        for i, meta in enumerate(all_pending["metadatas"]):
            all_names.append(meta.get("formula_name", ""))
            all_chains.append(all_pending["documents"][i] if all_pending["documents"] else "")

        verified_count = 0
        rejected_count = 0
        details = []

        for i, meta in enumerate(all_pending["metadatas"]):
            if meta.get("priority_hint", "false") != "true":
                continue

            sub_id = all_pending["ids"][i]
            formula_name = meta.get("formula_name", "")

            # 在其他pending公式的推导链中搜索这个名称
            # 取formula_name的关键部分（去掉版本号、序号等）
            search_name = formula_name.split("（")[0].split("(")[0].strip()
            if len(search_name) < 3:
                search_name = formula_name

            dependents = 0
            for j, chain in enumerate(all_chains):
                if i == j:
                    continue  # 跳过自己
                if search_name in chain or formula_name in chain:
                    dependents += 1

            # 更新metadata
            is_verified = dependents >= 2
            meta["dependents_count"] = str(dependents)
            meta["verified_priority"] = str(is_verified).lower()

            self._write(
                self.pending_collection, 'update',
                ids=[sub_id],
                metadatas=[meta],
            )

            if is_verified:
                verified_count += 1
                logger.info(
                    f"[MASTER-DB] 优先级验证通过: {formula_name} "
                    f"(被{dependents}个pending公式依赖)"
                )
            else:
                rejected_count += 1
                logger.info(
                    f"[MASTER-DB] 优先级声明无效: {formula_name} "
                    f"(仅被{dependents}个pending公式依赖，需≥2)"
                )

            details.append({
                "submission_id": sub_id,
                "formula_name": formula_name,
                "dependents_count": dependents,
                "verified": is_verified,
            })

        logger.info(
            f"[MASTER-DB] 优先级验证完成: {verified_count}个通过, "
            f"{rejected_count}个无效"
        )

        return {
            "verified": verified_count,
            "rejected": rejected_count,
            "details": details,
        }

    def list_pending_by_priority(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        按优先级排序列出待验证公式。

        排序规则：
        1. verified_priority=true 的最优先
        2. priority_hint=true 但未验证的次之
        3. 普通公式按提交时间排序

        包含状态：
        - pending: 从未验证过
        - dependency_gap: 之前因依赖不足被卡，可能现在依赖已满足
        不包含：processing（正在验证）、promoted（已入库）、rejected（已拒绝）、archived、withdrawn
        rejected的公式不重新拾取，避免worker空转
        """
        items = self.list_pending(limit=limit)
        # 只返回可重新验证的状态
        retryable_statuses = {"pending", "dependency_gap"}
        pending_items = [item for item in items if item.get("status") in retryable_statuses]

        def priority_score(item):
            verified = item.get("verified_priority", "false") == "true"
            hinted = item.get("priority_hint", "false") == "true"
            deps = int(item.get("dependents_count", "0"))
            status = item.get("status", "")
            # pending最优先，dependency_gap次之，rejected最后
            status_order = {"pending": 0, "dependency_gap": 1, "rejected": 2}.get(status, 3)
            if verified:
                return (0, status_order, -deps)
            elif hinted:
                return (1, status_order, -deps)
            else:
                return (2, status_order, 0)

        pending_items.sort(key=priority_score)
        return pending_items

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
            logger.info(
                f"[MASTER-DB] 同名公式已入库: {formula_name} (id={master_id})，返回已有master_id"
            )
            # 同名但验证通过 → 标记为promoted（与首次入库一致）
            self._update_pending_status(
                submission_id, "promoted",
                verification_result=json.dumps(verification_result, ensure_ascii=False, default=str),
            )
            return master_id

        # 组装主库记录
        # 提取Berry角度数据用于长期积累
        berry_data = verification_result.get("stages", {}).get("berry_check", {})
        angle_points = berry_data.get("path_points", [])
        berry_phase = berry_data.get("berry_phase", 0.0)
        berry_n = berry_data.get("n_value", 0)
        berry_status = berry_data.get("status", "no_angle_data")

        master_metadata = {
            "master_id": master_id,
            "permanent_number": str(self._next_seq()),  # 永久编号，一入库不回收
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

        self._write(
            self.master_collection, 'add',
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
        self._write(
            self.pending_collection, 'update',
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
                "permanent_number": int(meta.get("permanent_number", "0")) if meta.get("permanent_number") else 0,
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
        # 注册新PIA（允许多个PIA注册，不再单次锁死）
        metadata = {
            "pia_id": pia_id,
            "name": name,
            "geometric_content": geometric_content,
            "physical_identification": physical_identification,
            "geometric_theorem_id": geometric_theorem_id,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
        }

        self._write(
            self.pia_collection, 'add',
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

    def force_promote_pia(self) -> Dict[str, Any]:
        """
        将已注册的PIA（ℰ映射）强制入库为绝对真理。

        ℰ是物理世界与几何理论的唯一映射——语义声明，不是可验证的数学命题。
        它通过PIA注册流程登记，不需要通过三层验证协议。
        入库后永久锁死，不再接受任何新的物理映射或物理假设。

        Returns:
            {"success": bool, "master_id": str, "message": str}
        """
        pia = self.get_pia()
        if not pia:
            return {
                "success": False,
                "message": "PIA尚未注册，无法入库",
            }

        pia_id = pia["pia_id"]
        formula_name = f"ℰ 映射（{pia['name']}）"

        # 检查是否已入库
        master_id = f"master_pia_{pia_id}"
        existing = self.master_collection.get(ids=[master_id], include=["metadatas"])
        if existing["ids"]:
            logger.info(f"[MASTER-DB] PIA已入库: {formula_name} (id={master_id})")
            return {
                "success": True,
                "master_id": master_id,
                "message": f"ℰ映射已入库为绝对真理 (id={master_id})",
            }

        # 组装主库记录——PIA的特殊记录
        master_metadata = {
            "master_id": master_id,
            "formula_name": formula_name,
            "source_agent": "pia_registration",
            "verified_at": datetime.now().isoformat(),
            "verification_result": json.dumps({
                "passed": True,
                "action": "pia_force_promoted",
                "message": "PIA语义声明，直接入库，不经三层验证",
                "stages": {
                    "topology_check": {"passed": True, "note": "PIA不参与拓扑分类"},
                    "berry_check": {"skipped": True, "note": "PIA是语义声明，不适用Berry检查"},
                    "falsification": {"skipped": True, "note": "PIA是语义声明，不适用证伪检查"},
                    "independent_derivation": {"skipped": True, "note": "PIA是语义声明，不经推导复现"},
                },
            }, ensure_ascii=False),
            "status": "verified",
            "original_submission": "",
            "topology_class": "PIA",
            "berry_status": "pia_anchor",
            "berry_phase": "0",
            "berry_n_value": "0",
            "berry_path_points": "[]",
            "source_trace": "[]",
            "source_risk_level": "clean",
            "berry_closure": "closed",
            "is_pia": "true",
            "pia_id": pia_id,
            "pia_locked": "true",
            "pia_physical_identification": pia.get("physical_identification", ""),
            "pia_geometric_content": pia.get("geometric_content", ""),
        }

        doc_text = (
            f"【PIA物理识别锚点】{formula_name}\n\n"
            f"【几何内容】{pia.get('geometric_content', '')}\n\n"
            f"【物理识别】{pia.get('physical_identification', '')}\n\n"
            f"【性质】语义声明，不经数学验证。"
            f"这是框架中唯一允许的几何→物理映射，入库后永久锁死。"
        )

        self._write(
            self.master_collection, 'add',
            ids=[master_id],
            documents=[doc_text],
            metadatas=[master_metadata],
        )

        logger.info(
            f"[MASTER-DB] PIA强制入库: {formula_name} (id={master_id})。"
            f"物理映射已永久锁死。"
        )

        return {
            "success": True,
            "master_id": master_id,
            "message": (
                f"ℰ映射已入库为绝对真理 (id={master_id})。"
                f"物理映射已永久锁死——以后不再接受任何新的物理映射或物理假设。"
            ),
        }

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

        self._write(self.master_collection, 'update', ids=[master_id], metadatas=[meta])

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

        self._write(self.master_collection, 'update', ids=[into_id], metadatas=[meta_into])

        # 删除被合并的定理
        self._write(self.master_collection, 'delete', ids=[from_id])

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

        self._write(
            self.master_collection, 'update',
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
        self._write(self.master_collection, 'update', ids=[master_id], metadatas=[meta])
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
        # 统计各状态的pending记录数
        pending_total = 0  # 全部记录
        pending_active = 0  # 不含archived/withdrawn
        pending_by_status = {}  # 按状态分
        if self.pending_collection:
            all_pending = self.pending_collection.get(include=["metadatas"])
            for meta in all_pending.get("metadatas", []):
                status = meta.get("status", "pending")
                pending_total += 1
                pending_by_status[status] = pending_by_status.get(status, 0) + 1
                if status not in ("archived", "withdrawn"):
                    pending_active += 1

        # 真正"待验证"的 = pending + processing + dependency_gap + rejected
        # 不含 promoted（已入库）、archived、withdrawn
        waiting_verification = sum(
            pending_by_status.get(s, 0)
            for s in ("pending", "processing", "dependency_gap", "rejected",
                      "waiting_dependencies", "duplicate", "alternative_proof")
        )

        return {
            "initialized": self._initialized,
            "master_formulas_count": self.master_count,
            "pending_count": waiting_verification,  # 真正待验证的
            "pending_active": pending_active,  # 全部活跃记录（含promoted）
            "pending_total": pending_total,  # 全部记录（含archived/withdrawn）
            "pending_by_status": pending_by_status,  # 按状态明细
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
