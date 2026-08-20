# kappa-lab

弱透镜（WL）仿真器 / 推断 / 分布外（OoD）检测实验室。

**组织方式参考 galpy**：物理实体一个文件、tests/ 扁平按功能命名、doc 独立目录。
**数据来源**：FAIR Universe Weak Lensing ML Uncertainty Challenge
（arXiv:2604.14451, zenodo 20056065, CC-BY-4.0）。
**几何化轨道**：见 `docs/geometrization_proposal.md`——所有几何预言必须通过
`kappa_lab/geo/validate.py` 的三关审查（闭合性 / 先验性 / 无循环）。

## 结构

```
kappa-lab/
├── kappa_lab/
│   ├── stats/        # 统计量：功率谱、峰值计数
│   ├── emulator/     # 仿真器：GP、插值器
│   ├── inference/    # 推断：网格 MAP、MCMC
│   ├── ood/          # OoD 分数
│   ├── geo/          # 几何层：标度预言 + 三关审查
│   └── util/         # mask、binning
├── tests/            # test_功能.py
├── docs/             # 可行性论证等
└── scripts/          # 可复现的检验/回归脚本
```

## 数据

- `wl_challenge/data/sampled_*`：3 宇宙学 × 30 仿真（本地可用）
- `wl_challenge/data/full/`：101 宇宙学 × 256 仿真（需下载，见 `wl_challenge/download.py`）

## 快速开始

```bash
python scripts/check_spectral_index.py   # 第一条几何检验：P(l) 局部谱指数 vs 几何指数族
```
