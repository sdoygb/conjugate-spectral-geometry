# 实验结果说明

本目录保存 pyQPanda 本地模拟结果。真实“本源悟空”实验数据待申请机时后补充。

## 当前结果

- `grover_generic.txt`：5 量子比特通用 Grover 验证，目标态成功概率约 0.90
- `svp_grover.txt`：10 量子比特 SVP 原型，目标短向量成功概率约 0.9995
- `mlwe_grover.txt`：10 量子比特 MLWE 原型，目标解成功概率约 0.9995
- `spectral_band.txt`：谱刚性带数值验证（n=2/3/4）
- `high_lambda_lattice.txt`：高 $\Lambda_H$ 格构造验证，搜索空间可缩小到 0.7%–3%
- `geo_lattice_attack.txt`：完整几何论攻击原型（n=2/3/4），搜索空间显著缩小，Grover 成功概率 0.99+
- `quantum_oracle_attack.txt`：基于谓词（带内 + 范数阈值）的量子 Oracle 攻击，成功概率 0.94–0.996
- `pqc_spectral_analysis.txt`：PQC 类随机 q-ary 格谱刚性分布分析
- `wukong_circuit.originir`：9 量子比特谱刚性 Oracle Grover 线路（本源悟空提交用）
- `wukong_submit.txt`：线路参数与 OriginIR 输出
- `generalized_spectral_band.txt`：广义谱刚性带数值验证，高 $\Lambda_H^{(m)}$ 格压缩到 6%–13%
- `generalized_geo_attack.txt`：广义谱刚性带 Grover 攻击原型，包含模格/负循环结构实例（k=2,n=5 dim=10）

## 模拟环境

- pyqpanda3 0.3.2
- CPU 模拟器
- 20000 shots

## 真机实验计划

1. 使用本源悟空 10+ 量子比特设备
2. 运行 Grover 线路（10 qubit，25 次迭代）
3. 测量目标态频率
4. 与模拟结果对比，分析噪声影响
5. 数据补充至本目录
