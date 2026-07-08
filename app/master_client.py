"""
master_client.py — 子AI端主库通信模块

三条通信通道：
  1. fetch_truth()       — 拉取主库真理层，存入本地 master_truth collection（只读）
  2. submit_formula()    — 提交候选公式到主库待验证队列
  3. check_submission()  — 查询验证状态和结果

设计原则：
  - 子AI只能读主库真理，不能修改
  - 提交后异步等待，不阻塞本地工作
  - 网络异常时优雅降级，不影响本地AI正常工作
"""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入 requests，不可用时降级
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("[MASTER-CLIENT] requests 未安装，主库通信不可用")

# 从环境变量读取主库配置
MASTER_AI_URL = os.getenv('MASTER_AI_URL', 'http://localhost:5001')
MASTER_AI_TOKEN = os.getenv('MASTER_AI_TOKEN', 'master-ai-verify')

# 真理同步间隔（秒），避免频繁请求
TRUTH_SYNC_INTERVAL = int(os.getenv('TRUTH_SYNC_INTERVAL', '3600'))  # 默认1小时


class MasterClient:
    """
    子AI端主库通信客户端

    用法：
        client = MasterClient()
        client.fetch_truth(knowledge_base)     # 同步真理到本地
        sub_id = client.submit_formula(...)     # 提交候选
        result = client.check_submission(sub_id) # 查询结果
    """

    def __init__(self, url: str = "", token: str = ""):
        self.url = url or MASTER_AI_URL
        self.token = token or MASTER_AI_TOKEN
        self._last_truth_sync = 0.0  # 上次真理同步时间戳
        self._truth_cache: List[Dict] = []  # 真理层缓存
        self._available = REQUESTS_AVAILABLE and bool(self.url)

        if self._available:
            logger.info(f"[MASTER-CLIENT] 主库通信就绪: {self.url}")
        else:
            logger.warning("[MASTER-CLIENT] 主库通信不可用（缺少 requests 或 URL 未配置）")

    @property
    def is_available(self) -> bool:
        """主库通信是否可用"""
        return self._available

    def _headers(self) -> Dict[str, str]:
        """构建请求头（带认证）"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, timeout: int = 10) -> Optional[Dict]:
        """GET 请求封装（绕过系统代理，直连localhost）"""
        if not self._available:
            return None
        try:
            resp = requests.get(
                f"{self.url}{path}",
                headers=self._headers(),
                timeout=timeout,
                proxies={"http": None, "https": None},  # 绕过代理
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"[MASTER-CLIENT] GET {path} 返回 {resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"[MASTER-CLIENT] GET {path} 失败: {e}")
            return None

    def _post(self, path: str, data: Dict, timeout: int = 30) -> Optional[Dict]:
        """POST 请求封装（绕过系统代理，直连localhost）"""
        if not self._available:
            return None
        try:
            resp = requests.post(
                f"{self.url}{path}",
                headers=self._headers(),
                json=data,
                timeout=timeout,
                proxies={"http": None, "https": None},  # 绕过代理
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                # 非200状态码也要返回JSON响应体——撤回等操作的403/404/409是正常业务错误
                try:
                    body = resp.json()
                    logger.warning(f"[MASTER-CLIENT] POST {path} 返回 {resp.status_code}: {str(body)[:200]}")
                    return body
                except:
                    logger.warning(f"[MASTER-CLIENT] POST {path} 返回 {resp.status_code}: {resp.text[:200]}")
                    return None
        except Exception as e:
            logger.warning(f"[MASTER-CLIENT] POST {path} 失败: {e}")
            return None

    # ==================== 通道1: 真理反哺（只读） ====================

    def fetch_truth(self, knowledge_base=None, force: bool = False) -> List[Dict[str, Any]]:
        """
        从主库拉取真理层，存入本地 master_truth collection。

        Args:
            knowledge_base: VectorKnowledgeBase 实例（用于存储真理到本地）
            force: 是否强制同步（忽略时间间隔）

        Returns:
            真理层公式列表
        """
        if not self._available:
            return self._truth_cache

        # 时间间隔控制
        now = time.time()
        if not force and (now - self._last_truth_sync) < TRUTH_SYNC_INTERVAL:
            logger.debug("[MASTER-CLIENT] 真理同步间隔未到，跳过")
            return self._truth_cache

        result = self._get("/v1/master/truth", timeout=15)
        if result is None:
            return self._truth_cache

        formulas = result.get("formulas", [])
        self._truth_cache = formulas
        self._last_truth_sync = now

        logger.info(
            f"[MASTER-CLIENT] 真理层同步完成: {len(formulas)} 个已验证公式 "
            f"(主库总计 {result.get('master_total', 0)})"
        )

        # 存入本地 knowledge_base 的 master_truth collection
        if knowledge_base is not None and formulas:
            self._store_truth_locally(knowledge_base, formulas)

        return formulas

    def _store_truth_locally(self, knowledge_base, formulas: List[Dict]):
        """将主库真理存入本地 master_truth collection（只读标记）"""
        try:
            # 获取或创建 master_truth collection
            if not hasattr(knowledge_base, 'master_truth_collection') or \
               knowledge_base.master_truth_collection is None:
                if knowledge_base.client is None:
                    return
                knowledge_base.master_truth_collection = knowledge_base.client.get_or_create_collection(
                    name="master_truth",
                    metadata={"description": "主库下发的已验证真理（只读，不可修改）"},
                )
                logger.info("[MASTER-CLIENT] 创建 master_truth collection")

            col = knowledge_base.master_truth_collection

            # 清空旧真理，写入新真理（全量替换）
            existing = col.get()
            if existing["ids"]:
                col.delete(ids=existing["ids"])

            for formula in formulas:
                col.add(
                    ids=[formula.get("master_id", f"truth_{int(time.time())}")],
                    documents=[formula.get("document", "")],
                    metadatas=[{
                        "master_id": formula.get("master_id", ""),
                        "formula_name": formula.get("formula_name", ""),
                        "verified_at": formula.get("verified_at", ""),
                        "source": "master_ai",  # 标记来源
                        "readonly": "true",  # 只读标记
                    }],
                )

            logger.info(f"[MASTER-CLIENT] {len(formulas)} 个真理已存入本地 master_truth collection")

        except Exception as e:
            logger.warning(f"[MASTER-CLIENT] 存储真理到本地失败: {e}")

    def search_truth(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在本地缓存的真理层中搜索。

        Args:
            query: 搜索文本
            top_k: 返回数量

        Returns:
            匹配的真理公式列表
        """
        if not self._truth_cache:
            return []

        # 简单关键词匹配（向量搜索需要 knowledge_base 实例）
        results = []
        query_lower = query.lower()
        for formula in self._truth_cache:
            doc = formula.get("document", "").lower()
            name = formula.get("formula_name", "").lower()
            if query_lower in doc or query_lower in name:
                results.append(formula)
                if len(results) >= top_k:
                    break

        # 如果关键词匹配不足，返回全部
        if len(results) < top_k:
            for formula in self._truth_cache:
                if formula not in results:
                    results.append(formula)
                    if len(results) >= top_k:
                        break

        return results

    # ==================== 通道2: 提交候选公式 ====================

    def submit_formula(
        self,
        formula_name: str,
        formula_content: str,
        derivation_chain: str,
        source_agent: str = "",
        local_verification: Optional[Dict] = None,
        external_anchors: Optional[List[str]] = None,
        topology_class: str = "A0",
    ) -> Optional[str]:
        """
        提交候选公式到主库待验证队列。

        Args:
            formula_name: 公式名称/标题
            formula_content: 公式的数学表达式和推导过程
            derivation_chain: 推导链（引用了哪些公理/定理）
            source_agent: 提交方标识（本机IP或主机名）
            local_verification: 本地自检结果
            external_anchors: 外部锚点列表（L2桥接假设，唯一合法值为"ℰ"）
            topology_class: 拓扑分类 A0（局部代数）或 A1（整体拓扑）

        Returns:
            submission_id（成功）或 None（失败）
        """
        if not self._available:
            logger.warning("[MASTER-CLIENT] 主库不可用，无法提交")
            return None

        # 自动识别来源
        if not source_agent:
            source_agent = self._detect_agent_id()

        data = {
            "formula_name": formula_name,
            "formula_content": formula_content,
            "derivation_chain": derivation_chain,
            "source_agent": source_agent,
            "local_verification": local_verification or {},
            "external_anchors": external_anchors or [],
            "topology_class": topology_class,
        }

        result = self._post("/v1/master/submit", data, timeout=15)
        if result and "submission_id" in result:
            sub_id = result["submission_id"]
            logger.info(f"[MASTER-CLIENT] 候选公式已提交: {formula_name} → {sub_id}")
            return sub_id

        logger.warning(f"[MASTER-CLIENT] 提交失败: {formula_name}")
        return None

    def _detect_agent_id(self) -> str:
        """自动识别本机标识"""
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"{hostname}@{local_ip}"
        except Exception:
            return "unknown_agent"

    # ==================== 通道3: 查询验证状态 ====================

    def check_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        查询候选公式的验证状态和完整结果。

        Returns:
            {
                "submission_id": "xxx",
                "status": "pending" | "promoted" | "rejected" | "dependency_gap" | "waiting_dependencies",
                "formula_name": "...",
                "rejection_reason": "...",  # 如果被驳回
                "verification_summary": {...},  # 三重检查结果摘要
                "dependency_gap": {...},  # 如果是依赖不足
                "message": "...",  # 主库给子AI的消息
            }
        """
        if not self._available:
            return None

        result = self._get(f"/v1/master/pending?limit=500", timeout=10)
        if result is None:
            return None

        # 从列表中找到目标提交（支持前缀匹配）
        for item in result.get("pending", []):
            full_id = item.get("submission_id", "")
            if full_id == submission_id or full_id.startswith(submission_id):
                return item

        return None

    def get_verification_result(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        获取完整的验证结果（包含三重检查详情和依赖缺口分析）。

        与 check_submission 不同，这个方法返回完整的验证日志，
        包括 Berry 检测、证伪检查、独立推导的详细结果。
        """
        if not self._available:
            return None

        # 先查 pending 状态
        result = self._get(f"/v1/master/pending?limit=500", timeout=10)
        if result:
            for item in result.get("pending", []):
                full_id = item.get("submission_id", "")
                if full_id == submission_id or full_id.startswith(submission_id):
                    status = item.get("status", "")
                    if status in ("promoted", "rejected", "dependency_gap"):
                        # 已处理，尝试获取详细结果
                        # pending 中的 metadata 可能包含验证结果
                        return item

        return None

    # ==================== 辅助方法 ====================

    def get_master_status(self) -> Optional[Dict]:
        """获取主库状态"""
        return self._get("/v1/master/status", timeout=10)

    def health_check(self) -> bool:
        """检查主库是否在线"""
        result = self._get("/health", timeout=5)
        return result is not None and result.get("status") == "ok"

    def trigger_verify(self, submission_id: str = "") -> Optional[Dict]:
        """
        请求主库触发验证。

        注意：根据架构设计，验证通常由主库自动触发。
        此方法仅供管理员手动触发使用。

        Args:
            submission_id: 指定验证的提交ID，留空则验证最早的待验证公式

        Returns:
            验证结果
        """
        data = {}
        if submission_id:
            data["submission_id"] = submission_id

        # 验证可能耗时较长（LLM推导），设置较长超时
        return self._post("/v1/master/verify", data, timeout=120)

    def withdraw_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        撤回已提交的候选公式。

        每个子AI只能撤回自己提交的公式，不能撤回其他AI的提交。
        只能撤回未入库的公式（pending/waiting/processing状态）。
        已入库(promoted)的公式不可撤回。

        Args:
            submission_id: 要撤回的提交ID

        Returns:
            {
                "status": "withdrawn" / "error",
                "message": "...",
                "formula_name": "...",
                "previous_status": "..."
            }
        """
        if not self._available:
            logger.warning("[MASTER-CLIENT] 主库不可用，无法撤回")
            return None

        source_agent = self._detect_agent_id()

        data = {
            "submission_id": submission_id,
            "source_agent": source_agent,
        }

        result = self._post("/v1/master/withdraw", data, timeout=10)
        if result is None:
            logger.warning(f"[MASTER-CLIENT] 撤回失败: {submission_id}")
            return None

        if result.get("status") == "withdrawn":
            logger.info(
                f"[MASTER-CLIENT] 撤回成功: {result.get('formula_name', '')} "
                f"(原状态: {result.get('previous_status', '')})"
            )
        else:
            logger.warning(
                f"[MASTER-CLIENT] 撤回失败: {result.get('message', '')}"
            )

        return result


# ==================== 全局单例 ====================

_master_client: Optional[MasterClient] = None


def get_master_client() -> MasterClient:
    """获取全局 MasterClient 单例"""
    global _master_client
    if _master_client is None:
        _master_client = MasterClient()
    return _master_client


def init_master_client(url: str = "", token: str = "") -> MasterClient:
    """显式初始化 MasterClient（用于启动时配置）"""
    global _master_client
    _master_client = MasterClient(url=url, token=token)
    return _master_client
