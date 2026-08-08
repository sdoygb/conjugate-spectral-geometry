# -*- coding: utf-8 -*-
"""逐个触发验证 5 条新提交的公式，打印验证结果。"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_client import get_master_client

client = get_master_client()

submission_ids = [
    ("54a53a0a097f4e27", "引理 1.3.2.01（投影强度恒等式）"),
    ("b8a148f564c67d79", "引理 1.4.2.01（投影强度）"),
    ("7eb9aee18370cff9", "引理 1.4.3.02（三正弦恒等式）"),
    ("e3e8f00135f9dda6", "引理 1.6.2.01（Schur 刚性）"),
    ("1ce3b85d070de3bc", "定义 22（良性互扼）"),
]

for sid, name in submission_ids:
    print(f"\n===== 验证: {name} ({sid}) =====")
    try:
        result = client._post("/v1/master/verify", {"submission_id": sid})
        if result is None:
            print("返回 None（请求失败）")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print("异常:", e)
    time.sleep(2)
