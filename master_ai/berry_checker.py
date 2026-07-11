"""
berry_checker.py — Berry回路闭合检测器

核心验证逻辑：检测公式的推导链在几何参数空间中是否形成闭合回路，
且 Berry 相位等于 2π 的整数倍。

圆满判据（32号 §12.6）：
    ∮_Γ A · dl = 2π · n,  n ∈ ℤ⁺

其中 Γ 是推导链在约束截面 Σ 上的参数路径，A 是 Berry 联络。

实现方式：
1. 从推导链中提取每一步引用的角度参数变化（θ_M, θ_C, θ_I）
2. 在参数空间中构建路径 Γ
3. 计算 Berry 相位 ∮ A · dl
4. 检查是否为 2π 整数倍

检测层级对应三级圆满：
  n=1 → 初圆满（基本闭合，本地自检门槛）
  n=2 → 中圆满（亚稳态，交叉验证级）
  n=3 → 上圆满（全局刚度最大，主库入库门槛）
"""
import re
import math
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from config import (
    logger,
    GEOMETRY_CONSTANTS,
    VERIFICATION_TOLERANCE,
)


@dataclass
class DerivationStep:
    """推导链中的一个步骤"""
    step_index: int
    reference: str           # 引用的公理/定理编号
    operation: str           # 操作描述
    theta_M: Optional[float] = None  # 此步的 θ_M
    theta_C: Optional[float] = None  # 此步的 θ_C
    theta_I: Optional[float] = None  # 此步的 θ_I
    raw_text: str = ""       # 原始文本片段


@dataclass
class BerryPhaseResult:
    """Berry相位检测结果"""
    path_closed: bool                 # 路径是否闭合
    berry_phase: float                # 计算得到的 Berry 相位（rad）
    target_2pi_n: float               # 最近的 2π 整数倍
    n_value: int                      # n 值（1=初圆满, 2=中圆满, 3=上圆满）
    closure_error: float              # 闭合误差 |phase - 2πn|（rad）
    is_consummated: bool              # 是否圆满（在容差内）
    consummation_level: str           # 圆满级别
    path_steps: List[DerivationStep]  # 推导路径
    path_points: List[Tuple[float, float, float]]  # 参数空间路径点
    detail: str = ""                  # 详细说明


class BerryPhaseChecker:
    """
    Berry 回路闭合检测器

    从公式推导链中提取参数路径，计算 Berry 相位，判断是否圆满。
    """

    def __init__(self):
        self.gc = GEOMETRY_CONSTANTS
        self.tol = VERIFICATION_TOLERANCE["berry_phase_2pi_tolerance"]
        # 已知角度锚点（从几何论文章中提取的精确值）
        self.angle_anchors = self._build_angle_anchors()

    def _build_angle_anchors(self) -> Dict[str, Tuple[float, float, float]]:
        """构建已知角度锚点库（θ_M, θ_C, θ_I）"""
        return {
            # 背景点 P0
            "background": (57.93, 26.16, 5.91),
            "P0": (57.93, 26.16, 5.91),
            # 初圆满
            "initial": (28.97, 28.97, 32.07),
            "初圆满": (28.97, 28.97, 32.07),
            # 中圆满
            "middle": (17.5, 17.5, 55.0),
            "中圆满": (17.5, 17.5, 55.0),
            # 上圆满 P2
            "upper": (8.73, 8.73, 72.53),
            "P2": (8.73, 8.73, 72.53),
            "上圆满": (8.73, 8.73, 72.53),
            # 电子构型
            "electron": (57.93, 26.16, 5.91),
            "电子": (57.93, 26.16, 5.91),
            # 缪子构型
            "muon": (31.94, 31.94, 26.12),
            "缪子": (31.94, 31.94, 26.12),
            # 30度背景点（几何中心）
            "center": (30.0, 30.0, 30.0),
            "30度": (30.0, 30.0, 30.0),
        }

    # ==================== 推导链解析 ====================

    def parse_derivation_chain(self, derivation_text: str) -> List[DerivationStep]:
        """
        从推导链文本中提取参数路径。

        识别模式：
        - 角度引用：θ_M=57.93°, theta_I ≈ 72.53°, 等
        - 锚点引用：初圆满、上圆满、P0、P2 等
        - 公理引用：公理1、公理2、公理3、axiom
        - 定理引用：定理1.1、命题2.3、等
        """
        steps = []
        # 按行或分步标记分割
        lines = re.split(r'[\n；;]|→|=>|步骤|step', derivation_text)

        angle_pattern = re.compile(
            r'(?:θ|theta|angle)[_\s]*([MCI])\s*[=≈]\s*([\d.]+)\s*°?',
            re.IGNORECASE
        )
        anchor_pattern = re.compile(
            r'(背景点|P0|P2|初圆满|中圆满|上圆满|electron|muon|30度|center|background|initial|middle|upper)',
            re.IGNORECASE
        )
        ref_pattern = re.compile(
            r'(公理\s*[123]|axiom\s*[123]|定理\s*[\d.]+|命题\s*[\d.]+|引理\s*[\d.]+|推论\s*[\d.]+|文章\s*[\d.]+)',
            re.IGNORECASE
        )

        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 3:
                continue

            step = DerivationStep(
                step_index=len(steps),
                reference="",
                operation=line[:100],
                raw_text=line,
            )

            # 提取角度
            angles = angle_pattern.findall(line)
            for label, value in angles:
                val = float(value)
                if label.upper() == 'M':
                    step.theta_M = val
                elif label.upper() == 'C':
                    step.theta_C = val
                elif label.upper() == 'I':
                    step.theta_I = val

            # 提取锚点
            anchors = anchor_pattern.findall(line)
            if anchors and not all([step.theta_M, step.theta_C, step.theta_I]):
                for anchor in anchors:
                    key = anchor.lower().strip()
                    if key in self.angle_anchors:
                        tm, tc, ti = self.angle_anchors[key]
                        if step.theta_M is None:
                            step.theta_M = tm
                        if step.theta_C is None:
                            step.theta_C = tc
                        if step.theta_I is None:
                            step.theta_I = ti
                        break

            # 提取引用
            refs = ref_pattern.findall(line)
            if refs:
                step.reference = refs[0]

            # 只有包含角度信息的步骤才加入路径
            if any([step.theta_M is not None, step.theta_C is not None, step.theta_I is not None]):
                # 补全缺失角度（用公理1约束）
                step = self._complete_angles(step)
                steps.append(step)
            elif refs:
                # 有引用但无角度的步骤也保留（作为推导链深度证据）
                steps.append(step)

        return steps

    def _complete_angles(self, step: DerivationStep) -> DerivationStep:
        """用公理1（θ_M+θ_C+θ_I=90°）补全缺失的角度"""
        known = []
        if step.theta_M is not None:
            known.append(('M', step.theta_M))
        if step.theta_C is not None:
            known.append(('C', step.theta_C))
        if step.theta_I is not None:
            known.append(('I', step.theta_I))

        if len(known) == 2:
            # 已知两个，求第三个
            labels = {'M', 'C', 'I'}
            known_labels = {k for k, _ in known}
            missing = labels - known_labels
            if missing:
                missing_label = missing.pop()
                sum_known = sum(v for _, v in known)
                missing_val = 90.0 - sum_known
                if missing_label == 'M':
                    step.theta_M = round(missing_val, 2)
                elif missing_label == 'C':
                    step.theta_C = round(missing_val, 2)
                else:
                    step.theta_I = round(missing_val, 2)
        elif len(known) == 1:
            # 只知道一个角度，不假设对称，只记录已知角度
            label, val = known[0]
            if label == 'I':
                step.theta_I = round(val, 2)
            elif label == 'M':
                step.theta_M = round(val, 2)
            elif label == 'C':
                step.theta_C = round(val, 2)

        return step

    # ==================== Berry 相位计算 ====================

    def compute_berry_phase(
        self,
        path_points: List[Tuple[float, float, float]],
    ) -> Tuple[float, bool]:
        """
        计算参数空间路径的 Berry 相位。

        根据32号文章 §9.6 证伪条件4，Berry 相位表现为**阶跃量子化**：
        每当路径穿越一个圆满态锚点（初圆满/中圆满/上圆满），相位跃变 2π。
        不是连续积分，而是离散阶跃。

        量子化规则：
        - 穿越初圆满锚点（θ_I ≈ 32.07°）  → 跃变 +2π (n=1)
        - 穿越中圆满锚点（θ_I ≈ 55.0°）   → 跃变 +2π (n=2)
        - 穿越上圆满锚点（θ_I ≈ 72.53°）  → 跃变 +2π (n=3)
        - 路径必须闭合（回到起点）才形成有效回路

        Args:
            path_points: 参数空间路径点列表 [(θ_M, θ_C, θ_I), ...]（角度制）

        Returns:
            (berry_phase_rad, is_closed)
        """
        if len(path_points) < 2:
            return 0.0, False

        # 圆满态锚点（θ_I 值和对应的跃变量）
        anchor_phases = [
            (32.07, 2 * math.pi),   # 初圆满: +2π
            (55.0,  2 * math.pi),   # 中圆满: +2π
            (72.53, 2 * math.pi),   # 上圆满: +2π
        ]
        anchor_tolerance = 2.0  # 度，穿越容差

        # 检查路径是否闭合（首尾点重合）
        start = path_points[0]
        end = path_points[-1]
        closure_distance = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(start, end))
        )
        is_closed = closure_distance < 3.0  # 3度容差

        if not is_closed:
            return 0.0, False  # 不闭合的路径无 Berry 相位

        # 统计穿越的圆满态锚点数量
        gamma = 0.0
        crossed_anchors = []

        for anchor_theta_i, phase_jump in anchor_phases:
            # 检查路径是否穿越此锚点的 θ_I 值
            for k in range(len(path_points) - 1):
                theta_i_k = path_points[k][2]
                theta_i_next = path_points[k + 1][2]

                # 穿越 = θ_I 从一侧到另一侧
                if (theta_i_k < anchor_theta_i <= theta_i_next) or \
                   (theta_i_k > anchor_theta_i >= theta_i_next):
                    # 检查是否在锚点容差范围内（取穿越点的中值）
                    mid_theta_i = (theta_i_k + theta_i_next) / 2
                    if abs(mid_theta_i - anchor_theta_i) < anchor_tolerance + abs(theta_i_next - theta_i_k) / 2:
                        gamma += phase_jump
                        crossed_anchors.append(anchor_theta_i)
                        break  # 每个锚点只计一次

        return gamma, is_closed

    # ==================== 圆满判定 ====================

    def check_consummation(self, berry_phase: float) -> Tuple[int, str, float, bool]:
        """
        判定 Berry 相位对应的圆满级别。

        Returns:
            (n_value, level_name, target_2pi_n, is_consummated)
        """
        two_pi = 2 * math.pi
        # 找最近的 n 值
        n_float = berry_phase / two_pi
        n_nearest = max(1, round(n_float))
        target = n_nearest * two_pi
        error = abs(berry_phase - target)

        is_ok = error <= self.tol

        if n_nearest == 1:
            level = "初圆满"
        elif n_nearest == 2:
            level = "中圆满"
        elif n_nearest >= 3:
            level = "上圆满"
        else:
            level = "未圆满"

        return n_nearest, level, target, is_ok

    # ==================== 主检测入口 ====================

    def verify(
        self,
        derivation_chain: str,
        formula_content: str = "",
    ) -> BerryPhaseResult:
        """
        完整的 Berry 回路闭合检测。

        Args:
            derivation_chain: 推导链文本
            formula_content: 公式内容（辅助分析）

        Returns:
            BerryPhaseResult 检测结果
        """
        # 1. 解析推导链
        steps = self.parse_derivation_chain(derivation_chain)

        # 2. 提取参数空间路径（无论深度如何，只要有角度就记录）
        path_points = []
        for step in steps:
            if all([step.theta_M is not None, step.theta_C is not None, step.theta_I is not None]):
                path_points.append((step.theta_M, step.theta_C, step.theta_I))

        if len(path_points) == 0:
            # 没有角度数据，返回空记录（不拦截）
            return BerryPhaseResult(
                path_closed=False,
                berry_phase=0.0,
                target_2pi_n=0.0,
                n_value=0,
                closure_error=999.0,
                is_consummated=False,
                consummation_level="未圆满",
                path_steps=steps,
                path_points=[],
                detail="推导链未包含角度参数，无Berry数据可记录",
            )

        if len(path_points) < 2:
            # 有少量角度点，记录但不计算相位
            return BerryPhaseResult(
                path_closed=False,
                berry_phase=0.0,
                target_2pi_n=0.0,
                n_value=0,
                closure_error=999.0,
                is_consummated=False,
                consummation_level="未圆满",
                path_steps=steps,
                path_points=path_points,
                detail=f"记录{len(path_points)}个角度点，不足以计算Berry相位",
            )

        # 3. 计算 Berry 相位
        berry_phase, is_closed = self.compute_berry_phase(path_points)

        # 4. 判定圆满级别
        n_value, level, target, is_consummated = self.check_consummation(berry_phase)
        closure_error = abs(berry_phase - target)

        detail = (
            f"路径点数: {len(path_points)} | "
            f"Berry相位: {berry_phase:.4f} rad = {berry_phase / (2 * math.pi):.4f} × 2π | "
            f"最近整数: n={n_value} (目标 {target:.4f}) | "
            f"闭合误差: {closure_error:.6f} rad (容差 {self.tol}) | "
            f"判定: {level}"
        )

        logger.info(f"[BERRY] {detail}")

        return BerryPhaseResult(
            path_closed=is_closed,
            berry_phase=round(berry_phase, 6),
            target_2pi_n=round(target, 6),
            n_value=n_value,
            closure_error=round(closure_error, 6),
            is_consummated=is_consummated,
            consummation_level=level,
            path_steps=steps,
            path_points=path_points,
            detail=detail,
        )

    def result_to_dict(self, result: BerryPhaseResult) -> Dict[str, Any]:
        """将检测结果转为字典（用于 JSON 序列化）"""
        return {
            "path_closed": result.path_closed,
            "berry_phase": result.berry_phase,
            "berry_phase_2pi_ratio": round(result.berry_phase / (2 * math.pi), 6),
            "target_2pi_n": result.target_2pi_n,
            "n_value": result.n_value,
            "closure_error": result.closure_error,
            "is_consummated": result.is_consummated,
            "consummation_level": result.consummation_level,
            "path_point_count": len(result.path_points),
            "derivation_depth": len(result.path_steps),
            "path_points": result.path_points,
            "detail": result.detail,
        }
