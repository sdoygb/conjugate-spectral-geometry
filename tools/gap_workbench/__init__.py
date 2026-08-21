#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gap_workbench —— 5线程并行推理 + 反向审计协议 工作台

把"多线并行推理 → 结果保留 → 横向对比收敛 → 反向审计"的方法固化为程序：
- 工作台：缺口(锚点/目标/五线/证据缓存/死胡同/结论链)的状态管理
- 收敛判据：≥2 条闭合线独立同向 + 无冲突线（硬性规则，防确认偏差）
- 反向审计：收敛后对结论链逐环节验证（✅/⚠️/❌/📌），证据反推，全内存操作
- 持久化：JSON 状态文件 + Markdown 报告

用法见 cli.py（python3 tools/gap_workbench/cli.py --help）
"""
from .models import (
    Gap, Line, Evidence, AuditItem,
    LINE_OPEN, LINE_DEAD, LINE_CLOSED, LINE_PARTIAL,
    EV_VERIFIED, EV_FLAGGED, EV_FAILED, EV_OUTSCOPE,
    GAP_TYPES,
)
from .workbench import Workbench, WorkbenchError
from .templates import suggest_lines
from .derive import DerivationFlow, suggest_derivation_lines

__version__ = "0.2.0"
