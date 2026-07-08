"""
master_ai — 主库AI：专职圆满检测的验证引擎

架构定位：
  本地 Agent 产出候选公式 → 本地自检（初圆满）→ 提交主库AI
  主库AI 独立从公理重推导 → Berry回路闭合检测 → §9.6证伪检查 → 数值吻合 → 入库
  主库已验证公式 → 反哺给所有本地 Agent 作为只读真理层

核心模块：
  config.py          — 配置与几何论常数
  master_db.py       — 主库数据库（append-only ChromaDB）
  berry_checker.py   — Berry回路闭合检测器（核心）
  falsification.py   — §9.6 四条证伪条件检查器
  verifier.py        — 验证引擎（整合三重检查）
  server.py          — API服务（submit/verify/status）
"""

__version__ = "0.1.0"
__all__ = ["config", "master_db", "berry_checker", "falsification", "verifier", "server"]
