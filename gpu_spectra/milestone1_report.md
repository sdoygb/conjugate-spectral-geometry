# 里程碑 1：零方差定律大规模验证报告（RX570 GPU）

日期：2026-08-22
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
目标：0.9 §4.1–4.3 零方差定律的 N=10^5 大规模确认（原经验确认 N=20，10.58 P2）

## 方法

- **GPU**：AMD Radeon RX 570（32 CU / 2048 SP，Apple OpenCL 1.2，FP64 可用）
- **管线**：gram_kernel.cl（格生成 + Gram 组装，1 WG = 1 格，全部在显存内完成，避开 PCIe x4 瓶颈）
  + jacobi_kernel.cl v2.1（批量 cyclic Jacobi，1 WG = 1 矩阵，double，local mem 精简支持 64×64 顶格）
- **结构**（定理 0.9.4.02）：A 为 d×d negacyclic 矩阵（系数均匀 Z_q，q=3329），
  B = [[A, I_d], [0, qI_d]]，G = BB^T = [[AA^T + I_d, qI_d], [qI_d, q²I_d]]（2d×2d）
- **谱刚性比**（定义 0.9.4.01）：Λ_H = λ_2 / λ_1（G 特征值升序）

## 验证链（先证工具正确，再信结果）

| 检查 | 结果 |
|---|---|
| G 对称性（GPU 生成拷回 numpy 检查） | max\|G−G^T\| < 1e-9 ✓ |
| G 正定性 | 全部 λ > 0 ✓ |
| GPU Jacobi vs numpy eigvalsh（同一 G） | max\|Δλ\|=8.3e-7，rel=1.4e-15 ✓ |
| 收敛质量 <offdiag²> | 2.0e-26（特征值机器精度） |

## 结果

### 1) negacyclic 无调制格：Λ_H ≡ 1（零方差定律）——N=10^5 确认

| 维度 | 平台 | N | mean(Λ_H) | std | max\|Λ_H−1\| |
|---|---|---|---|---|---|
| d=16（G 32×32） | GPU | 100,000 | 1.0000000000 | **3.2e-13** | 8.4e-12 |
| d=32（G 64×64） | numpy 补充 | 512 | 1.0000000000 | 5.6e-12 | 1.1e-10 |

- 10^5 样本零方差（std=3.2e-13 ≈ double 机器精度，来自简并特征值数值分裂）
- **对比 0.9 原经验确认 N=20：样本量提升 5000 倍**，断言强度从"经验"到"数值定理级"
- d=32 确认无维度依赖（定理 0.9.4.02 对任意 d 成立）

### 2) diag 对照（定理 0.9.4.11）：Λ_H = M² 精确

| 参数 | N | mean(Λ_H) | 期望 | std | max\|Λ_H−M²\| |
|---|---|---|---|---|---|
| B=diag(1,10,…,10)，n=32 | 4,096 | 100.000000 | M²=100 | **0.0（完全零）** | 0.0 |

- 完全零方差（std=0，精确到 double 表示）——与定理一致

### 3) 一般随机对照（非 negacyclic）：Λ_H 大幅波动

| 维度 | 平台 | N | mean(Λ_H) | std | min |
|---|---|---|---|---|---|
| d=16 | GPU | 2,048 | 1.25e6 | 3.7e7 | 1.06 |

- 一般随机 A 的 AA^T 特征值不成对 ⟹ Λ_H 波动（std 3.7e7 vs negacyclic 3.2e-13，**对比度 ~10^20**）
- 确证 0.9 注（归因修正）：零方差来自 negacyclic 结构（共轭谱对称），**不是**随机化

## 性能

| 任务 | 吞吐 | N=10^5 耗时 |
|---|---|---|
| d=16（G 32×32）批量 Jacobi | ~4,750 mat/s | 21 s |

瓶颈：cyclic Jacobi 的 pair 串行 + 双 barrier（496 pairs × 2），GPU 利用率 ~30%（见 v3 优化路线）。

## 已知限制与 v3 路线

1. **Apple OpenCL local mem 顶格**：64×64 double 矩阵 = 32KB 恰好等于 gfx803 限制，编译失败
   → d=32 用 numpy 补充（已足够）；d≥64 需要上三角打包存储（16KB，支持到 128×128）或 blocked Jacobi
2. **PRNG**：xorshift64star（非加密级，统计用途足够；如需可换 PCG）
3. **v3 优化**：blocked Jacobi（多对同时旋转）、每 WG 多矩阵、上三角 local 存储

## 文件清单

- `gpu_spectra/gram_kernel.cl` — 格生成 + Gram 组装（mode 运行时参数）
- `gpu_spectra/jacobi_kernel.cl` — 批量 cyclic Jacobi v2.1
- `gpu_spectra/batch_jacobi.py` — Jacobi 包装 + 原始验证
- `gpu_spectra/lambda_H.py` — 里程碑 1 验证与全量（verify / full）

## 对 0.9 的潜在更新（待用户确认）

0.9 §4.3 经验确认（10.58 P2，N=20）可升级为："GPU 数值确认 2026-08-22：N=10^5（d=16，q=3329）std=3.2e-13，N=512（d=32）std=5.6e-12；diag 对照 M=10 精确 M²（N=4096，std=0）；一般随机对照 std=3.7e7——零方差来自 negacyclic 结构（共轭谱对称），与归因修正注一致。"
