# 阶段 1 基准：基线回归固化（full 数据，101 宇宙学）

- 日期：2026-08-20
- 数据：`wl_challenge/data/full/`（kappa_full.npy 6.83 GB，101 宇宙学 × 256 realization × 132019 像素，float16）
- 代码：`kappa-lab/scripts/run_baseline_regression.py`（复刻官方 `wl_challenge/baseline_official.py`，逐位对齐）
- 结果：`kappa-lab/results/baseline_regression/{metrics.json, chi2.npz}`
- 运行时间：961 s（16 分钟）

## 管道定义（与官方逐位一致）

1. 统计量：log10 P(l)，10 bin，l ∈ [100, 10⁴]（对数等距），像素 2 arcmin，掩模内填充
2. 噪声：加性高斯，σ_n = 0.02582（官方值），rng seed 42，消耗顺序与官方一致（训练 80 → 验证 21 → 扰动）
3. 仿真器：80 训练宇宙学 × 256 图 → μ(θ)、C(θ)（归一化 n−N_BIN−2=244）→ LinearNDInterpolator
4. 推断：30² 参数网格 MAP → χ²@MAP（最小马氏距离²）
5. 扰动（官方定义，作用于**无噪图**）：blur_1px / blur_2px（高斯模糊 σ=1,2 px）、extra_noise_0.5sn / extra_noise_1.0sn（额外加噪 0.5σ_n / 1.0σ_n）

## 基准指标（固化）

| 指标 | 数值 |
|---|---|
| 训练 χ² 中位数（80 宇宙学 × 256） | **6.865** |
| 验证 χ² 中位数（21 新宇宙学 × 256） | **7.212** |
| 种子敏感度 d（干净新宇宙学 vs 训练） | **+0.110**（TPR@FPR=0.0197） |
| blur_1px | d=+31.1，TPR@FPR=**1.000** |
| blur_2px | d=+5.70，TPR@FPR=**1.000** |
| extra_noise_0.5sn | d=+23.7，TPR@FPR=**1.000** |
| extra_noise_1.0sn | d=−0.010，TPR@FPR=0.0147（定义使然，见下） |

## 回归验证（对照官方备份 official_results_original.npz）

| 对比 | 数值 |
|---|---|
| Pearson r（tr_chi2） | 0.999999999997 |
| Pearson r（val_chi2） | 0.999999999999 |
| 最大逐点差（tr） | 1.22×10⁻⁴ |
| 最大逐点差（val） | 7.37×10⁻⁵ |

逐位一致（差异为 float32 舍入级）。**管道复现关闭**：后续一切方法（G1 几何管道、GP 仿真器、峰值计数等）以本表为对比锚点。

## extra_noise_1.0sn 不可检测的说明（非缺陷）

官方扰动定义：扰动作用于无噪图（`if perturb is not None: full = perturb(full)`，分支不加形状噪声）。因此"无噪图 + 1.0σ_n"在统计上恰好恢复训练分布（信号 + 1.0σ_n），与训练不可区分。d≈0、TPR≈0.015 是官方设置的自然结果，官方基线同此。blur 与 0.5σ_n 可检测是因为谱形/噪声水平偏离训练分布。

## 配置快照

seed=42，N_train=80，N_val=21，N_BIN=10，l∈[100,10⁴]，grid=30²，σ_n=0.025819888974716113，掩模 WIDE12H_bin2_2arcmin_mask.npy，label_newrealization.npy（101×256×5）。

## 复现

```bash
python3 kappa-lab/scripts/run_baseline_regression.py
# 输出：kappa-lab/results/baseline_regression/metrics.json
```
