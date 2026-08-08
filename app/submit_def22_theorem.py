# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, '.')
from master_client import get_master_client

client = get_master_client()

sub = {
    "formula_name": "定理 1.6.1.01（良性互扼判定）",
    "formula_content": "设 P、Q 为真理层中两条推导链。P 与 Q 形成良性互扼，当且仅当同时满足：(1) P⟹Q：P 的结论是 Q 的前提；(2) Q⟹P：Q 的结论是 P 的前提；(3) 外部锚定：存在独立于 P、Q 的外部约束 C，使 P 和 Q 都满足 C；(4) 唯一性：在约束 C 下，P 与 Q 的互扼解唯一。条件 (3) 排除循环论证：P、Q 并非彼此互证，而是被独立外部约束共同锚定。",
    "derivation_chain": "【依赖】公理（零之动）、定理 0.3.1.01（Bott 周期）、引理 0.2.2.01（半单分裂）\n【推导】\n步骤1: 由公理（零之动），δ 的非平凡自映射产生区分结构，任意推导链 P、Q 均为区分结构的迭代展开；\n步骤2: （必要性）若 P、Q 良性互扼，则互扼蕴含双向蕴含（条件1、2），良性蕴含外部锚定与唯一性（条件3、4），故良性互扼蕴含四条件；\n步骤3: （充分性）设四条件成立，条件(1)(2) 给出 P、Q 的互扼闭链；\n步骤4: 条件(3) 的实例存在性：定理 0.3.1.01 给出 Bott 周期 δ⁸（Berry 相位 2π，独立于任何推导链），引理 0.2.2.01 给出 Cl(3) ≅ ℍ⊕ℍ 半单分裂（独立于乘子序列）——二者均为独立外部约束的实例，故 P、Q 被外部约束共同锚定，非循环论证；\n步骤5: 条件(4) 的代数基础：定理 0.3.1.01 的维数序列 1,2,4,4,8,8,8,8,16 不含连续参数（刚性），互扼解在 C 下唯一；\n步骤6: 四条件联合蕴含 P、Q 构成良性互扼。∎",
    "topology_class": "A0",
    "external_anchors": [],
    "local_verification": {"berry_phase": 0, "n_value": 1, "is_consummated": True, "level": "初圆满"},
    "priority_hint": False,
    "interlock_hint": [],
    "interlock_reasoning": ""
}

r = client.submit_formula(**sub)
print(json.dumps(r, ensure_ascii=False, indent=2))
if r and r.get("submission_id"):
    sid = r["submission_id"]
    print("SUBMISSION_ID:", sid)
    try:
        if hasattr(client, "verify"):
            v = client.verify(sid)
            print("VERIFY:", json.dumps(v, ensure_ascii=False, indent=2))
        else:
            import requests
            v = requests.post("http://localhost:5001/v1/master/verify",
                              json={"submission_id": sid},
                              headers={"Authorization": "Bearer master-ai-verify"},
                              timeout=60).json()
            print("VERIFY:", json.dumps(v, ensure_ascii=False, indent=2))
    except Exception as e:
        print("VERIFY_ERROR:", e)
