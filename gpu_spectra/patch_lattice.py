#!/usr/bin/env python3
"""一次性补丁：修复 lattice_lambdaH.py 中 f-string 跨行语法错误"""
path = 'gpu_spectra/lattice_lambdaH.py'
src = open(path).read()

old = """    verdict = max_dev_neg < 1e-9 and min_std_rnd > 1e-6
    print(f"  判定：{'✓ 定理 0.9.4.02 在 N=10^5 样本上确认（零方差来自 negacyclic 结构）' if verdict
          else '✗ 与定理预期不符，需检查'}")
    diag_check()"""

new = """    verdict = max_dev_neg < 1e-9 and min_std_rnd > 1e-6
    msg = ('✓ 定理 0.9.4.02 在 N=10^5 样本上确认（零方差来自 negacyclic 结构）'
           if verdict else '✗ 与定理预期不符，需检查')
    print(f"  判定：{msg}")
    diag_check()"""

assert old in src, "old text not found"
open(path, 'w').write(src.replace(old, new))
print("patched OK")
