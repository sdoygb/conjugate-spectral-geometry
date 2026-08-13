#!/usr/bin/env python3
"""
符号验证引擎 —— 共扼谱几何推导的代数自动检查。

用法:
  # 等式验证（符号化简后比较）
  python3 symbolic_verify.py eq "sin(x)**2 + cos(x)**2" "1"

  # 数值代入验证
  python3 symbolic_verify.py num "sin(theta)**3" --subs "{theta: 0.523599}" --expected 0.125 --tol 1e-6

  # 带度数的三角验证（自动转换弧度）
  python3 symbolic_verify.py num "sin(30*pi/180)**3" --expected 0.125

  # 化简
  python3 symbolic_verify.py simplify "(x+1)**3 - x**3 - 3*x**2 - 3*x - 1"

  # 导数验证
  python3 symbolic_verify.py deriv "x**3 * sin(x)" x

  # 矩阵运算验证
  python3 symbolic_verify.py matrix --A "[[1,2],[3,4]]" --B "[[5,6],[7,8]]" --op multiply

  # 扫描文章中的验证块
  python3 symbolic_verify.py scan 3.10_三代轻子质量刚性_CN_260808.md

  # 质量公式专用验证
  python3 symbolic_verify.py mass --C 839.759 --theta 30 --expected 104.97 --unit keV
"""

import sys
import re
import json
import math
import argparse
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

try:
    import sympy as sp
    from sympy import sin, cos, tan, pi, sqrt, Symbol, symbols, Matrix, simplify, expand, trigsimp
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    print("[WARN] SymPy 未安装。请运行: pip3 install sympy")

# ============================================================================
# 共扼谱几何常量
# ============================================================================
GT_CONSTANTS = {
    "K": 839.759,        # keV, 普适质量量子
    "Lambda": 3,         # 结构常数 Λ
    "k0": 2,             # 结构常数 k₀
    "DeltaTheta": 5,     # 结构常数 ΔΘ
    "kappa_c": 1000.0,   # 色态标度因子 (MeV/keV)
    "pi": math.pi,
    "deg_to_rad": math.pi / 180.0,
}

# ============================================================================
# 核心验证函数
# ============================================================================

def verify_equality(lhs_str: str, rhs_str: str, assumptions: str = "") -> Tuple[bool, str]:
    """符号验证两个表达式是否相等（化简后比较）。"""
    try:
        x, y, z, t = symbols('x y z t')
        theta = Symbol('theta', real=True)
        # 注入共扼谱几何常量
        local_dict = {
            'sin': sin, 'cos': cos, 'tan': tan, 'pi': pi, 'sqrt': sqrt,
            'x': x, 'y': y, 'z': z, 't': t, 'theta': theta,
            'K': GT_CONSTANTS['K'],
            'Lambda': GT_CONSTANTS['Lambda'],
            'k0': GT_CONSTANTS['k0'],
            'DeltaTheta': GT_CONSTANTS['DeltaTheta'],
        }
        lhs = sp.sympify(lhs_str, locals=local_dict)
        rhs = sp.sympify(rhs_str, locals=local_dict)
        diff = sp.simplify(lhs - rhs)
        is_zero = diff == 0

        if is_zero:
            return True, f"✓ 等式成立: {lhs_str} == {rhs_str}"
        else:
            # 尝试数值验证（随机取点）
            try:
                import random
                ok = True
                local_dict_num = {k: v for k, v in local_dict.items() if isinstance(v, (int, float))}
                for _ in range(5):
                    subs = {x: random.uniform(0.1, 5.0), y: random.uniform(0.1, 5.0),
                            z: random.uniform(0.1, 5.0), t: random.uniform(0.1, 5.0),
                            theta: random.uniform(0.1, math.pi/2)}
                    if abs(float((lhs.subs(subs) - rhs.subs(subs)).evalf())) > 1e-10:
                        ok = False
                        break
                if ok:
                    return True, f"✓ 数值验证通过（符号化简未归零但数值一致）: {lhs_str} == {rhs_str}"
            except:
                pass
            return False, f"✗ 等式不成立:\n  lhs - rhs = {diff}\n  化简后非零"
    except Exception as e:
        return False, f"✗ 解析错误: {e}"


def verify_numerical(expression: str, substitutions: Dict[str, float],
                     expected: float, tolerance: float = 1e-10) -> Tuple[bool, str]:
    """数值代入验证。"""
    try:
        x, y, z, t = symbols('x y z t')
        theta = Symbol('theta', real=True)
        local_dict = {
            'sin': sin, 'cos': cos, 'tan': tan, 'pi': pi, 'sqrt': sqrt,
            'x': x, 'y': y, 'z': z, 't': t, 'theta': theta,
            'K': GT_CONSTANTS['K'],
            'Lambda': GT_CONSTANTS['Lambda'],
            'k0': GT_CONSTANTS['k0'],
            'DeltaTheta': GT_CONSTANTS['DeltaTheta'],
        }
        expr = sp.sympify(expression, locals=local_dict)
        # 使用 local_dict 中的符号做代换（避免 Symbol 重新创建导致不匹配）
        subs_map = {}
        for k, v in substitutions.items():
            if k in local_dict:
                subs_map[local_dict[k]] = v
            else:
                subs_map[Symbol(k)] = v
        result = float(expr.subs(subs_map).evalf())
        diff = abs(result - expected)

        if diff < tolerance:
            return True, f"✓ 数值一致: {expression}|subs = {result:.10f}, expected = {expected}, diff = {diff:.2e}"
        else:
            rel_err = diff / abs(expected) if expected != 0 else float('inf')
            return False, (f"✗ 数值偏差: {expression}|subs = {result:.10f}, "
                          f"expected = {expected}, diff = {diff:.2e}, rel_err = {rel_err:.2e}")
    except Exception as e:
        return False, f"✗ 计算错误: {e}"


def simplify_expression(expression: str) -> Tuple[bool, str]:
    """化简表达式。"""
    try:
        x, y, z, t = symbols('x y z t')
        theta = Symbol('theta', real=True)
        local_dict = {
            'sin': sin, 'cos': cos, 'tan': tan, 'pi': pi, 'sqrt': sqrt,
            'x': x, 'y': y, 'z': z, 't': t, 'theta': theta,
            'K': GT_CONSTANTS['K'],
            'Lambda': GT_CONSTANTS['Lambda'],
            'k0': GT_CONSTANTS['k0'],
            'DeltaTheta': GT_CONSTANTS['DeltaTheta'],
        }
        expr = sp.sympify(expression, locals=local_dict)
        simplified = sp.simplify(expr)
        trig_simplified = sp.trigsimp(simplified)
        return True, f"  原始: {expression}\n  化简: {simplified}\n  三角化简: {trig_simplified}"
    except Exception as e:
        return False, f"✗ 化简错误: {e}"


def verify_derivative(expression: str, variable: str) -> Tuple[bool, str]:
    """计算并显示导数。"""
    try:
        x, y, z, t = symbols('x y z t')
        theta = Symbol('theta', real=True)
        var_map = {'x': x, 'y': y, 'z': z, 't': t, 'theta': theta}
        local_dict = {
            'sin': sin, 'cos': cos, 'tan': tan, 'pi': pi, 'sqrt': sqrt,
            'x': x, 'y': y, 'z': z, 't': t, 'theta': theta,
        }
        expr = sp.sympify(expression, locals=local_dict)
        v = var_map.get(variable, Symbol(variable))
        deriv = sp.diff(expr, v)
        simplified = sp.simplify(deriv)
        return True, (f"  d/d{variable}({expression}) =\n"
                     f"  原始: {deriv}\n"
                     f"  化简: {simplified}\n"
                     f"  三角化简: {sp.trigsimp(simplified)}")
    except Exception as e:
        return False, f"✗ 求导错误: {e}"


def verify_matrix(A_str: str, B_str: str, operation: str) -> Tuple[bool, str]:
    """矩阵运算验证。"""
    try:
        A = Matrix(eval(A_str))
        B = Matrix(eval(B_str))

        if operation == 'multiply':
            result = A * B
        elif operation == 'add':
            result = A + B
        elif operation == 'sub':
            result = A - B
        elif operation == 'det':
            result = A.det()
        elif operation == 'eigenvals':
            result = A.eigenvals()
        elif operation == 'inverse':
            result = A.inv()
        else:
            return False, f"✗ 未知操作: {operation}"

        return True, f"  A {operation} B =\n  {sp.pretty(result)}"
    except Exception as e:
        return False, f"✗ 矩阵运算错误: {e}"


# ============================================================================
# 质量公式专用验证
# ============================================================================

def verify_mass_formula(C: float, theta_deg: float, expected: float,
                        unit: str = "keV", n: int = 3) -> Tuple[bool, str]:
    """验证 m = C · sin^n(θ) 形式的质量公式。"""
    theta_rad = theta_deg * math.pi / 180
    sin_val = math.sin(theta_rad)
    sin_n = sin_val ** n
    m = C * sin_n

    err = abs(m - expected)
    rel_err = err / expected if expected != 0 else float('inf')
    ok = rel_err < 1e-3  # 0.1% 容差

    lines = [
        f"  质量公式: m = {C} × sin^{n}({theta_deg}°)",
        f"  θ_rad = {theta_rad:.6f}",
        f"  sin(θ) = {sin_val:.6f}",
        f"  sin^{n}(θ) = {sin_n:.6f}",
        f"  m = {C} × {sin_n:.6f} = {m:.4f} {unit}",
        f"  期望值 = {expected} {unit}",
        f"  偏差 = {err:.4f} {unit} ({rel_err*100:.4f}%)",
    ]

    if ok:
        return True, "✓ " + "\n  ".join(lines)
    else:
        return False, "✗ 质量公式偏差过大:\n  " + "\n  ".join(lines)


# ============================================================================
# 文章扫描模式
# ============================================================================

def scan_article(filepath: str) -> Dict[str, Any]:
    """扫描文章中的验证块并运行验证。"""
    path = Path(filepath)
    if not path.exists():
        # 尝试在 articles 目录下查找
        articles_dir = Path(__file__).parent.parent / "articles"
        path = articles_dir / filepath
        if not path.exists():
            return {"error": f"文件不存在: {filepath}"}

    content = path.read_text(encoding='utf-8')
    results = {"file": str(path), "blocks": [], "passed": 0, "failed": 0}

    # 匹配验证块: ```verify <type>\n...\n```
    verify_pattern = re.compile(
        r'```verify\s+(\w+)\s*\n(.*?)```',
        re.DOTALL
    )

    for match in verify_pattern.finditer(content):
        vtype = match.group(1)
        body = match.group(2).strip()
        block_result = {"type": vtype, "body": body[:200]}

        try:
            if vtype == 'equality' or vtype == 'eq':
                lhs_m = re.search(r'lhs:\s*(.+)', body)
                rhs_m = re.search(r'rhs:\s*(.+)', body)
                if lhs_m and rhs_m:
                    ok, msg = verify_equality(lhs_m.group(1).strip(), rhs_m.group(1).strip())
                    block_result["result"] = ok
                    block_result["message"] = msg
                else:
                    block_result["result"] = False
                    block_result["message"] = "缺少 lhs/rhs 字段"

            elif vtype == 'numerical' or vtype == 'num':
                expr_m = re.search(r'expression:\s*(.+)', body)
                subs_m = re.search(r'substitutions:\s*(\{.*?\})', body)
                exp_m = re.search(r'expected:\s*([\d.e+\-]+)', body)
                tol_m = re.search(r'tolerance:\s*([\d.e+\-]+)', body)

                if expr_m and exp_m:
                    expr = expr_m.group(1).strip()
                    subs = json.loads(subs_m.group(1)) if subs_m else {}
                    expected = float(exp_m.group(1))
                    tolerance = float(tol_m.group(1)) if tol_m else 1e-10
                    ok, msg = verify_numerical(expr, subs, expected, tolerance)
                    block_result["result"] = ok
                    block_result["message"] = msg
                else:
                    block_result["result"] = False
                    block_result["message"] = "缺少 expression/expected 字段"

            elif vtype == 'simplify':
                expr_m = re.search(r'expression:\s*(.+)', body)
                if expr_m:
                    ok, msg = simplify_expression(expr_m.group(1).strip())
                    block_result["result"] = ok
                    block_result["message"] = msg

            elif vtype == 'mass':
                c_m = re.search(r'C:\s*([\d.e+\-]+)', body)
                t_m = re.search(r'theta:\s*([\d.e+\-]+)', body)
                e_m = re.search(r'expected:\s*([\d.e+\-]+)', body)
                u_m = re.search(r'unit:\s*(\w+)', body)
                if c_m and t_m and e_m:
                    C = float(c_m.group(1))
                    theta = float(t_m.group(1))
                    expected = float(e_m.group(1))
                    unit = u_m.group(1) if u_m else "keV"
                    ok, msg = verify_mass_formula(C, theta, expected, unit)
                    block_result["result"] = ok
                    block_result["message"] = msg

            else:
                block_result["result"] = False
                block_result["message"] = f"未知验证类型: {vtype}"

        except Exception as e:
            block_result["result"] = False
            block_result["message"] = f"执行错误: {e}"

        results["blocks"].append(block_result)
        if block_result["result"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

    return results


# ============================================================================
# CLI
# ============================================================================

def parse_subs(subs_str: str) -> Dict[str, float]:
    """解析代入字典，支持度数自动转换。
    '{theta: 30}' -> {'theta': 30.0} (注意：显示使用度数，但内部用弧度需在表达式中处理)
    '{x: 3, y: 4}' -> {'x': 3.0, 'y': 4.0}
    """
    subs = {}
    # 去除花括号
    s = subs_str.strip().strip('{}')
    for pair in s.split(','):
        pair = pair.strip()
        if ':' in pair:
            k, v = pair.split(':', 1)
            subs[k.strip()] = float(v.strip())
    return subs


def main():
    parser = argparse.ArgumentParser(
        description='共扼谱几何符号验证引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s eq "sin(x)**2 + cos(x)**2" "1"
  %(prog)s num "x**2 + 2*x + 1" --subs "{x: 3}" --expected 16
  %(prog)s num "sin(theta)**3" --subs "{theta: 0.523599}" --expected 0.125
  %(prog)s simplify "(x+1)**3 - x**3 - 3*x**2 - 3*x - 1"
  %(prog)s deriv "x**3 * sin(x)" x
  %(prog)s mass --C 839.759 --theta 57.93 --expected 511.0 --unit keV
  %(prog)s scan 3.10_三代轻子质量刚性_CN_260808.md
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='验证命令')

    # eq: 等式验证
    eq_parser = subparsers.add_parser('eq', help='验证两个表达式相等')
    eq_parser.add_argument('lhs', help='左侧表达式')
    eq_parser.add_argument('rhs', help='右侧表达式')
    eq_parser.add_argument('--assumptions', default='', help='变量假设')

    # num: 数值代入验证
    num_parser = subparsers.add_parser('num', help='数值代入验证')
    num_parser.add_argument('expression', help='表达式')
    num_parser.add_argument('--subs', default='{}', help='代入字典, 如 {x:3,y:4}')
    num_parser.add_argument('--expected', type=float, required=True, help='期望值')
    num_parser.add_argument('--tol', type=float, default=1e-10, help='容差')

    # simplify: 化简
    simp_parser = subparsers.add_parser('simplify', help='化简表达式')
    simp_parser.add_argument('expression', help='要化简的表达式')

    # deriv: 导数验证
    deriv_parser = subparsers.add_parser('deriv', help='计算导数')
    deriv_parser.add_argument('expression', help='表达式')
    deriv_parser.add_argument('variable', help='求导变量')

    # matrix: 矩阵运算
    mat_parser = subparsers.add_parser('matrix', help='矩阵运算验证')
    mat_parser.add_argument('--A', required=True, help='矩阵A, 如 [[1,2],[3,4]]')
    mat_parser.add_argument('--B', required=True, help='矩阵B')
    mat_parser.add_argument('--op', default='multiply',
                           choices=['multiply', 'add', 'sub', 'det', 'eigenvals', 'inverse'])

    # mass: 质量公式专用
    mass_parser = subparsers.add_parser('mass', help='质量公式专用验证')
    mass_parser.add_argument('--C', type=float, required=True, help='质量标度因子')
    mass_parser.add_argument('--theta', type=float, required=True, help='角度(度)')
    mass_parser.add_argument('--expected', type=float, required=True, help='期望质量')
    mass_parser.add_argument('--unit', default='keV', help='单位')
    mass_parser.add_argument('--power', type=int, default=3, help='sin的幂次(默认3)')

    # scan: 扫描文章
    scan_parser = subparsers.add_parser('scan', help='扫描文章中的验证块')
    scan_parser.add_argument('filepath', help='文章路径或文件名')

    # check: 快速检查常量
    check_parser = subparsers.add_parser('check', help='检查共扼谱几何常量')
    check_parser.add_argument('--all', action='store_true', help='显示所有常量')

    args = parser.parse_args()

    if not HAS_SYMPY:
        print("✗ SymPy 未安装。请运行: pip3 install sympy")
        sys.exit(1)

    if args.command == 'eq':
        ok, msg = verify_equality(args.lhs, args.rhs, args.assumptions)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'num':
        subs = parse_subs(args.subs)
        ok, msg = verify_numerical(args.expression, subs, args.expected, args.tol)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'simplify':
        ok, msg = simplify_expression(args.expression)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'deriv':
        ok, msg = verify_derivative(args.expression, args.variable)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'matrix':
        ok, msg = verify_matrix(args.A, args.B, args.op)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'mass':
        ok, msg = verify_mass_formula(args.C, args.theta, args.expected, args.unit, args.power)
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == 'scan':
        results = scan_article(args.filepath)
        if "error" in results:
            print(f"✗ {results['error']}")
            sys.exit(1)
        print(f"\n{'='*60}")
        print(f"扫描: {results['file']}")
        print(f"验证块: {len(results['blocks'])} | ✓ 通过: {results['passed']} | ✗ 失败: {results['failed']}")
        print(f"{'='*60}")
        for i, blk in enumerate(results['blocks']):
            status = "✓" if blk['result'] else "✗"
            print(f"\n[{i+1}] {status} {blk['type']}")
            print(f"  {blk['message'][:300]}")
        print()
        sys.exit(0 if results['failed'] == 0 else 1)

    elif args.command == 'check':
        print("共扼谱几何常量:")
        for k, v in GT_CONSTANTS.items():
            print(f"  {k:15s} = {v}")
        # 结构常数关系检验
        print(f"\n  结构常数关系:")
        print(f"  Λ × k₀ × ΔΘ = {GT_CONSTANTS['Lambda']} × {GT_CONSTANTS['k0']} × {GT_CONSTANTS['DeltaTheta']} = {GT_CONSTANTS['Lambda']*GT_CONSTANTS['k0']*GT_CONSTANTS['DeltaTheta']}")
        print(f"  sin³(30°) = {math.sin(math.pi/6)**3:.6f}")
        print(f"  sin³(30°) in fraction = 1/8 = {1/8}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
