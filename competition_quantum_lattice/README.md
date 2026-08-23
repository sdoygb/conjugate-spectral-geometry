# 赛题二：量子计算攻击基于格的后量子密码算法

## 项目目标

面向格密码底层困难问题（SVP / MLWE），设计至少 2 种量子求解算法：

1. **量子穷举搜索 SVP（Grover 加速的系数枚举）**
2. **量子穷举搜索 MLWE 秘密/误差（Grover 加速的 BDD 原型）**

分析经典/量子复杂度，证明量子版本相对经典穷举具有**多项式（二次）加速**，并在本源量子云平台上进行小规模实验。

## 目录

```
docs/                  方案文档 + 复杂度证明 + 几何论攻击理论 + 互锁最优性讨论 + PQC谱刚性障碍与解决方案 + 广义谱刚性带定理 + ML-KEM/ML-DSA评估报告
src/pyqpanda/          量子线路代码（pyQPanda3，含几何论攻击原型 + 谓词 Oracle + 悟空提交）
src/                   谱刚性带数值验证 + 高 Λ_H 格构造
scripts/               运行脚本
results/               实验结果与数据说明
emails/                本源悟空机时申请邮件
```

## 运行环境

```bash
pip install pyqpanda3 numpy
```

## 快速运行

```bash
cd src/pyqpanda
python3 grover_search.py
python3 svp_grover_demo.py
python3 mlwe_grover_demo.py
```

## 提交材料

- 方案文档：`docs/方案文档.md`
- 实现源码：`src/pyqpanda/`
- 返回结果：`results/`
- 总结报告：见方案文档最后一章
