# -*- coding: utf-8 -*-
"""验证 verifier.py 四项修复的测试（不写库，不调用真实LLM）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from unittest.mock import MagicMock, patch
from verifier import MasterVerifier

# ============ 测试②：是否入库解析 ============
verifier = MasterVerifier.__new__(MasterVerifier)

cases = [
    ("【圆满判定】上圆满\n【是否入库】是\n【判定理由】自洽\n【缺失依赖】无", True),
    ("【圆满判定】未圆满\n【是否入库】否\n【判定理由】不闭合\n【缺失依赖】无", False),
    ("【圆满判定】未圆满\n【是否入库】不是\n【判定理由】推导跳跃\n【缺失依赖】无", False),  # 修复前误判为True
    ("【圆满判定】未圆满\n【是否入库】暂不\n【判定理由】待定\n【缺失依赖】无", False),
    ("【圆满判定】初圆满\n【是否入库】是（依赖满足）\n【判定理由】闭合\n【缺失依赖】无", True),
]
print("== 测试② 是否入库解析 ==")
for resp, expected in cases:
    j = verifier._parse_consummation_response(resp, "测试公式")
    status = "PASS" if j["should_promote"] == expected else "FAIL"
    print(f"  [{status}] 输入={resp.splitlines()[1][:18]}... 期望={expected} 实际={j['should_promote']}")
    assert j["should_promote"] == expected

# ============ 测试③：否定词检测 ============
print("== 测试③ 否定词检测 ==")
neg_cases = [
    ("该环路不存在循环论证，判定闭环自洽", "循环论证", True),
    ("环路无循环论证，整体闭环自洽", "循环论证", True),
    ("未发现循环论证", "循环论证", True),
    ("该环路存在循环论证，逻辑空洞", "循环论证", False),
    ("该环路属于循环论证", "循环论证", False),
    ("环路并非闭环自洽", "闭环自洽", True),
    ("环路闭环自洽，各公式相互支撑", "闭环自洽", False),
    ("判定：闭环自洽", "闭环自洽", False),
]
for text, kw, expected in neg_cases:
    got = verifier._has_negation_before(text, kw)
    status = "PASS" if got == expected else "FAIL"
    print(f"  [{status}] {text[:22]}... keyword={kw} 期望否定={expected} 实际={got}")
    assert got == expected

# ============ 测试①：伪造上圆满文本不再直接入库 ============
print("== 测试① 伪造上圆满快速通道 ==")
from berry_checker import BerryPhaseChecker
fake_derivation = """从背景点 P0 (θ_M=57.93°, θ_C=26.16°, θ_I=5.91°) 出发
经初圆满 (θ_M=28.97°, θ_C=28.97°, θ_I=32.07°)
到中圆满 (θ_M=17.5°, θ_C=17.5°, θ_I=55.0°)
到达上圆满 P2 (θ_M=8.73°, θ_C=8.73°, θ_I=72.53°)
回到背景点 P0 (θ_M=57.93°, θ_C=26.16°, θ_I=5.91°)"""
berry = BerryPhaseChecker().verify(derivation_chain=fake_derivation)
print(f"  机械检测: n={berry.n_value}, level={berry.consummation_level}, "
      f"闭合={berry.path_closed}, consummated={berry.is_consummated}")
assert berry.is_consummated and berry.n_value >= 3, "伪造文本应能触发机械n=3（前提成立）"

fake_pending = {
    "metadata": {
        "formula_name": "伪造上圆满测试公式",
        "source_agent": "test",
        "external_anchors": "[]",
        "interlock_hint": "",
        "interlock_reasoning": "",
        "topology_class": "A1",
    },
    "document": f"""【公式】伪造上圆满测试公式

γ = 137.036 × 2

【推导链】
{fake_derivation}""",
}

v = MasterVerifier.__new__(MasterVerifier)
v.master_db = MagicMock()
v.master_db.get_pending = MagicMock(return_value=fake_pending)
v.berry_checker = BerryPhaseChecker()
v.falsification_checker = __import__("falsification").FalsificationChecker()
v.dep_graph = MagicMock()
llm_mock = MagicMock(return_value={
    "should_promote": True,
    "consummation_level": "初圆满",
    "is_dependency_gap": False,
    "reason": "推导链自洽（测试mock）",
    "missing_dependencies": [],
    "guidance": "",
})
v._llm_judge_consummation = llm_mock
v._finalize = MagicMock()

result = v.verify_submission("fake-sub-001")

print(f"  judge_method = {result.get('judge_method')} (应为 llm_consummation)")
print(f"  passed = {result.get('passed')}")
print(f"  LLM被调用 = {llm_mock.called}")
print(f"  Berry记录保留 = stages.berry_check.n_value = "
      f"{result['stages']['berry_check'].get('n_value')}")
print(f"  证伪检查记录 = {list(result['stages'].get('falsification', {}).keys())}")

assert result.get("judge_method") == "llm_consummation", "修复失败：仍走机械快速通道"
assert llm_mock.called, "修复失败：LLM未被调用"
assert result["stages"]["berry_check"].get("n_value") == 3, "Berry记录应保留"
assert "falsification" in result["stages"], "证伪检查记录缺失"

print("\n全部测试通过 ✅")
