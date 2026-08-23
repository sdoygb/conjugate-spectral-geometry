# Issue #434 准备笔记（本地，未公开）

日期：2026-08-14。状态：等待 #567/#568 review，未在 GitHub 上行动。

## 需求解读

- **#434 标题**：Add example: computing logical error rates of individual logical operators in a memory experiment.
- 标签：enhancement, example；来源："From discussions with Jonathan Baker"（IBM Quantum）。
- perlinm 指的方向（2 条评论）：用 sinter 的 `custom_counts` + Stim 的 `count_observable_error_combos`。
- HaoTy 指的方向：tqec 的实现 `src/tqec/simulation/split.py`。

## 技术验证（已完成）

- qldpc 的 decoder（CompiledSubgraphDecoder）返回 per-shot per-observable flips 矩阵 → `count_observable_error_combos=True` 可用 ✓
- dev 脚本：`workspace/qLDPC/examples/logical_error_rates/dev_m2_individual_obs.py`（split_counts_for_observables + 冒烟测试）
- 环境：.venv311 + ldpc 2.4.1（新装，BP-LSD 需要）

## 验证结果（[[16,6,4]] QRM，X 基，d=4 rounds，depolarizing circuit noise）

| p | shots | joint rate | per-observable rates | spread |
|---|---|---|---|---|
| 5e-3 | 7850 | 0.392 | [0.208, 0.137, 0.215, 0.177, 0.211, 0.210] | 1.56 |
| 1e-3 | 2594 | 0.079 | [0.042, 0.019, 0.044, 0.034, 0.033, 0.040] | 2.35 |

**发现**：observable #2（index 1）错误率显著低于其余 5 个。p=5e-3 时 1079 vs ~1650 counts（Δ ≈ 570 ≫ 3σ=100），是结构性效应，不是统计噪声。低 p 下 spread 未收敛（反而略升），说明不对称来自 circuit 布局 / 解码器偏好，而非高 p 噪声区现象。

**这正是 #434 要展示的价值**：联合错误率掩盖 observable 间 ~1.5-2.3 倍的差异。

## Notebook 8 设计草稿（8_individual_logical_operators.ipynb）

对齐官方风格（notebook 2 的函数结构 + common.get_label + sinter.plot_error_rate）：

1. 复用 run_memory_experiments，加 `count_observable_error_combos=True`
2. `split_counts_for_observables`（obs_mistake_mask 拆分，qldpc 风格 docstring，与 tqec split.py 思路同源但独立实现）
3. 演示码：QuantumReedMullerCode(1,4)（我们 #567 的码，形成 PR 间联动）
4. 图 1：joint rate vs per-observable rates（loglog，per-obs 用同一色系散点/箱线）
5. 讨论点：
   - 方向完备性（weight-1 完美恢复）是解码前的解析性质；per-observable 差异是解码后的采样性质，两者可同框对照
   - observable #2 的受保护现象 → 结构不对称的物理来源问题（open question，留给维护者/社区讨论）

## 行动节奏

1. 不动 GitHub，等 perlinm 对 #567 的正式 review
2. review 到来后：回应时关联 #434（"#568 的解析侧 + 已备好采样侧 example，可发新 PR"）
3. #567 合并后：提交 notebook 8（新 PR，小、独立、带图）
4. 记账：#102（docstring RTD）或 #266（RingArray 加速）作为下一个改进候选
