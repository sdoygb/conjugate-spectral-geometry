#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补跑 E（对抗基族）+ F（真实参数）部分——复用 verify_spectral_band_1057 模块。"""
import sys, time
sys.path.insert(0, "geo_qec")
import verify_spectral_band_1057 as V

t0 = time.time()
fams_e = V.part_e()
print(f"[E 用时 {time.time()-t0:.0f}s]", flush=True)
t0 = time.time()
qq_f = V.part_f()
print(f"[F 用时 {time.time()-t0:.0f}s]", flush=True)
print("=" * 78)
print("E 汇总:", [(name, f"δ²={q['delta2']:.3g}", f"平凡={q['trivial']}") for name, q in fams_e])
print("F 汇总:", f"Λ_H={qq_f['Lambda_H']:.6f} Λ_max={qq_f['Lambda_max']:.3g} "
      f"δ²={qq_f['delta2']:.3g} log10δ²={V.log10_d2(qq_f['delta2']):.1f}")
