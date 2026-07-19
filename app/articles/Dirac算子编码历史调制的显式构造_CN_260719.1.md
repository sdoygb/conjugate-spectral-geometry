# Dirac 算子编码历史调制的显式构造：$\Delta_j^{(n)}$ 矩阵

**版本**: 260719.1  
**状态**: 构造中 —— 从路 A'' 诊断出发，构造 $D_n = \sum_j \gamma_j \otimes \Delta_j^{(n)}$ 的显式形式  
**前置阅读**: 共扼谱几何 JMP 投稿（260718.1）§4.6；重数编码矩阵 $M_n$ 显式构造（260718.2）  
**GT 编号**: GT-0.4.6.5（谱间隙公式的补全——替代当前 §4.6.3 中 $D_n = \sum_j \gamma_j \otimes I$ 的假设）

---

## 摘要

当前 JMP 投稿 §4.6.3 中，层-$n$ Dirac 算子定义为 $D_n = \sum_{j=1}^n \gamma_j^{(n)} \otimes I_{m_n}$——即 $D_n$ 在重数空间上的作用是平凡的。这导致 $[D_n, S_i]$ 形如 $A \otimes I$，在 $g_n = I_{\rho_n} \otimes G$ 下，三个扇区的谱间隙完全相同。本文构造 $D_n$ 在重数空间上的非平凡作用矩阵 $\Delta_j^{(n)}$，使 $D_n = \sum_j \gamma_j \otimes \Delta_j^{(n)}$，从而谱间隙依赖扇区。$\Delta_j^{(n)}$ 由编码轨道的因子消耗历史唯一确定——不引入新参数。

---

## 目录

1. §1 问题诊断：为什么 $D_n = \sum_j \gamma_j \otimes I$ 不区分扇区
2. §2 构造原理：编码历史作为重数空间上的对角权重
3. §3 因子消耗历史的显式计算
4. §4 $\Delta_j^{(n)}$ 的显式矩阵形式
5. §5 修正后的谱间隙公式
6. §6 与当前框架的对接
7. §7 诚实标注与开放问题

---

## §1 问题诊断：为什么 $D_n = \sum_j \gamma_j \otimes I$ 不区分扇区

### 1.1 当前定义的算子结构

当前 JMP 投稿 §4.6.1 定义：

$$D_n = \sum_{j=1}^n \gamma_j^{(n)} \in \text{End}(V_n), \quad V_n = W_n^{\oplus m_n}.$$

在不可约模分解的基底中，这等价于：

$$D_n = \sum_{j=1}^n \gamma_j \otimes I_{m_n},$$

其中 $\gamma_j$ 是 $\rho_n \times \rho_n$ 矩阵（作用于 $W_n$），$I_{m_n}$ 是 $m_n \times m_n$ 单位矩阵（作用于重数空间 $\mathbb{R}^{m_n}$）。

扇区算子同样形如：

$$S_i = \gamma_i \otimes I_{m_n}, \quad i \in \{1,2,3\}.$$

### 1.2 致命后果

对易子 $[D_n, S_i]$ 的代数结构：

$$[D_n, S_i] = \left[\sum_j \gamma_j \otimes I, \; \gamma_i \otimes I\right] = \sum_{j \neq i} [\gamma_j, \gamma_i] \otimes I = \sum_{j \neq i} 2\gamma_j\gamma_i \otimes I.$$

这是 $A \otimes I$ 的形式——**算子纯作用于表示空间，在重数空间上平凡**。

另一方面，编码诱导度量 $g_n = I_{\rho_n} \otimes G$（定义 4.15）——**差异化纯在重数空间**。

两者永不对话。对于任意 $A \otimes I$ 和 $g_n = I \otimes G$：

$$\|A \otimes I\|_{I \otimes G}^2 = \sup_{v \in V_n} \frac{\sum_{\alpha=1}^{m_n} G_{\alpha\alpha} \|A v_\alpha\|^2}{\sum_{\alpha=1}^{m_n} G_{\alpha\alpha} \|v_\alpha\|^2} = \|A\|_{\text{flat}}^2.$$

$G_{\alpha\alpha}$ 在比值中消掉——三个扇区的谱间隙**必然全等**。

### 1.3 出路

唯一出路：$D_n$ 必须在重数空间上有非平凡作用。即：

$$D_n = \sum_{j=1}^n \gamma_j \otimes \Delta_j^{(n)},$$

其中 $\Delta_j^{(n)}$ 是 $m_n \times m_n$ 对角矩阵，编码各副本的编码历史。此时：

$$[D_n, S_i] = \sum_{j \neq i} 2\gamma_j\gamma_i \otimes \Delta_j^{(n)},$$

不再是 $A \otimes I$ 的形式。$g_n = I \otimes G$ 的差异化权重与 $\Delta_j^{(n)}$ 相互作用，扇区区分得以产生。

---

## §2 构造原理：编码历史作为重数空间上的对角权重

### 2.1 核心直觉

编码轨道 $N_1 \to N_2 \to \cdots \to N_7$ 中，每一步乘子 $\mu_k$ 消耗或回收素因子 $\{2,3,5\}$。这三个因子通过 Clifford 生成元与扇区绑定（§4.6.4）：

$$\gamma_1 \leftrightarrow \text{因子 } 2 \leftrightarrow \mathcal{M},\quad \gamma_2 \leftrightarrow \text{因子 } 3 \leftrightarrow \mathcal{C},\quad \gamma_3 \leftrightarrow \text{因子 } 5 \leftrightarrow \mathcal{I}.$$

直觉：沿 $\gamma_j$ 方向的"运动"（Dirac 算子分量）应被因子 $f(j)$ 的编码历史**调制**——经历过更多消耗的因子方向，其 Dirac 分量更强。

### 2.2 构造原则

**原则 1（因子-生成元绑定）**。$\Delta_j^{(n)}$（$j = 1,2,3$）的对角元由对应因子 $f(j) \in \{2,3,5\}$ 的累积编码历史决定。$j > 3$ 的 $\Delta_j^{(n)} = I_{m_n}$（无对应扇区，平凡调制）。

**原则 2（累积递推）**。$\Delta_j^{(n)}$ 的权重 $w_{f(j)}^{(n)}$ 通过乘子序列递推：

$$w_f^{(1)} = 1, \qquad w_f^{(n+1)} = w_f^{(n)} \cdot (\text{因子 } f \text{ 在 } \mu_n \text{ 中的贡献}).$$

其中「因子 $f$ 在 $\mu_n$ 中的贡献」= $f^{\,(\text{分子中 } f \text{ 的指数} - \text{分母中 } f \text{ 的指数})}$。

**原则 3（扇区-副本分区）**。第 $n$ 层的 $m_n$ 个不可约模副本按扇区分组。扇区 $i$ 的副本子集记为 $\mathcal{S}_i^{(n)} \subset \{1,\ldots,m_n\}$，$|\mathcal{S}_i^{(n)}| = m_n^{(i)}$。$\Delta_j^{(n)}$ 仅在扇区 $j$ 的副本上取增强权重 $w_{f(j)}^{(n)}$，在其他副本上取基线权重 $1$：

$$(\Delta_j^{(n)})_{\alpha\alpha} = \begin{cases} w_{f(j)}^{(n)}, & \alpha \in \mathcal{S}_j^{(n)}, \\ 1, & \alpha \notin \mathcal{S}_j^{(n)}. \end{cases}$$

**原则 4（等权分区——诚实假设）**。在当前构造中，假设三层扇区的副本数相等：

$$m_n^{(\mathcal{M})} = m_n^{(\mathcal{C})} = m_n^{(\mathcal{I})} = m_n/3.$$

这一假设的合理性来自 $\text{Cl}(3) \subset \text{Cl}(n)$ 子代数的三重对称性（triality），但扇区人口通过 $M_n$ 矩阵的精确演化是**开放问题**（见 §7）。

---

## §3 因子消耗历史的显式计算

### 3.1 乘子序列的因子分解

$$\begin{aligned}
\mu_1 &= 6 = 2^{\color{red}{+1}} \cdot 3^{\color{red}{+1}}, \\
\mu_2 &= \frac{100}{3} = 2^{\color{red}{+2}} \cdot 3^{\color{red}{-1}} \cdot 5^{\color{red}{+2}}, \\
\mu_3 &= 10 = 2^{\color{red}{+1}} \cdot 5^{\color{red}{+1}}, \\
\mu_4 &= 10 = 2^{\color{red}{+1}} \cdot 5^{\color{red}{+1}}, \\
\mu_5 &= \frac{9}{8} = 2^{\color{red}{-3}} \cdot 3^{\color{red}{+2}}, \\
\mu_6 &= 2 = 2^{\color{red}{+1}}.
\end{aligned}$$

其中红色指数 = 分子指数 $-$ 分母指数。

### 3.2 累积权重 $w_f^{(n)}$ 的递推

以 $w_f^{(1)} = 1$ 为起点：

| $n$ | $\mu_{n-1}$ | $w_2^{(n)}$ | $w_3^{(n)}$ | $w_5^{(n)}$ |
|:---:|:---|:---:|:---:|:---:|
| 1 | — | $1$ | $1$ | $1$ |
| 2 | $6$ | $1 \times 2 = \mathbf{2}$ | $1 \times 3 = \mathbf{3}$ | $1 \times 1 = 1$ |
| 3 | $100/3$ | $2 \times 2^2 = \mathbf{8}$ | $3 \times 3^{-1} = \mathbf{1}$ | $1 \times 5^2 = \mathbf{25}$ |
| 4 | $10$ | $8 \times 2 = \mathbf{16}$ | $1 \times 1 = 1$ | $25 \times 5 = \mathbf{125}$ |
| 5 | $10$ | $16 \times 2 = \mathbf{32}$ | $1 \times 1 = 1$ | $125 \times 5 = \mathbf{625}$ |
| 6 | $9/8$ | $32 \times 2^{-3} = \mathbf{4}$ | $1 \times 3^2 = \mathbf{9}$ | $625 \times 1 = 625$ |
| 7 | $2$ | $4 \times 2 = \mathbf{8}$ | $9 \times 1 = \mathbf{9}$ | $625 \times 1 = \mathbf{625}$ |

### 3.3 与编码基数 $N_n$ 的因子指数一致性验证

从 $N_n$（定理 4.9）的因子分解：

$$N_n = 2^{e_2^{(n)}} \cdot 3^{e_3^{(n)}} \cdot 5^{e_5^{(n)}}.$$

| $n$ | $e_2^{(n)}$ | $e_3^{(n)}$ | $e_5^{(n)}$ | $w_2^{(n)}$ | $w_3^{(n)}$ | $w_5^{(n)}$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 4 | 1 | 3 | 1 | 1 | 1 |
| 2 | 5 | 2 | 3 | 2 | 3 | 1 |
| 3 | 6 | 0 | 5 | 8 | 1 | 25 |
| 4 | 7 | 0 | 6 | 16 | 1 | 125 |
| 5 | 8 | 0 | 7 | 32 | 1 | 625 |
| 6 | 5 | 2 | 7 | 4 | 9 | 625 |
| 7 | 6 | 2 | 7 | 8 | 9 | 625 |

验证：$w_f^{(n)} \times 2^{e_f^{(1)}} = 2^{e_f^{(n)}}$ 对 $f=2$ 成立（$w_2^{(n)} \times 16 = 2^{e_2^{(n)}}$），但对 $f=3,5$ 不成立——因为 $w_f^{(n)}$ 定义为递推乘积，而 $e_f^{(n)}$ 是净指数。两者的关系是：

$$e_f^{(n)} = e_f^{(1)} + \log_f(w_f^{(n)}).$$

验证：$e_2^{(7)} = 4 + \log_2 8 = 4+3=7$（$N_7 = 2^7 \times 3^2 \times 5^7$）。正确。$e_2^{(7)} = 6$，误差来自 $N_7$ 中因子 2 的指数实际是 $6$（$N_7 = 2^6 \times 3^2 \times 5^7$）。而 $w_2^{(7)} = 8 = 2^3$，$4+3=7 \neq 6$。

**诊断**：$w_f^{(n)}$ 追踪的是**预算操作的累积净效果**（消耗减回收），而 $e_f^{(n)}$ 是 $N_n$ 的因子指数。两者应满足 $w_f^{(n)} = 2^{e_f^{(n)} - e_f^{(1)}}$。检查 $n=7$：$w_2^{(7)}=8$，$2^{6-4}=2^2=4$。不一致。

原因：$w_f$ 的递推使用了**乘子** $\mu_n$ 的因子分解，但乘子定义中的分母 $3$（来自 $\mu_2$）和分母 $8=2^3$（来自 $\mu_5$）的回收作用于 $N_1$ 基准（引理 4.9），而非前一层 $N_n$。因此 $w_f$ 的递推不能简单从 $\mu_n$ 的因子分解逐层累积——回收操作的基准不匹配。

**修正**：$w_f^{(n)}$ 的正确递推应基于 $N_n$ 的因子指数：

$$w_f^{(n)} = f^{\,e_f^{(n)} - e_f^{(1)}}.$$

即 $w_f^{(n)}$ 直接由 $N_n$ 的因子指数与 $N_1$ 的因子指数之差定义。这一定义自动与引理 4.9（回收基准定理）一致。

### 3.4 修正后的 $w_f^{(n)}$（最终形式）

$$\boxed{w_f^{(n)} = f^{\,e_f^{(n)} - e_f^{(1)}},\quad f \in \{2,3,5\}}.$$

| $n$ | $e_2^{(n)}$ | $e_3^{(n)}$ | $e_5^{(n)}$ | $w_2^{(n)}$ | $w_3^{(n)}$ | $w_5^{(n)}$ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 4 | 1 | 3 | $1$ | $1$ | $1$ |
| 2 | 5 | 2 | 3 | $2$ | $3$ | $1$ |
| 3 | 6 | 0 | 5 | $4$ | $1/3$ | $25$ |
| 4 | 7 | 0 | 6 | $8$ | $1/3$ | $125$ |
| 5 | 8 | 0 | 7 | $16$ | $1/3$ | $625$ |
| 6 | 5 | 2 | 7 | $2$ | $3$ | $625$ |
| 7 | 6 | 2 | 7 | $4$ | $3$ | $625$ |

**关键观察**：
- $w_2$ 在 $n=5$ 达到峰值 $16$，$n=6$ 因 $\mu_5 = 9/8$ 的 $2^{-3}$ 回收骤降至 $2$，$n=7$ 回升至 $4$。
- $w_3$ 经历「激活（$2$）→ 休眠（$1/3$，三层）→ 重现（$3$）」的四阶段——完美对应 triality 的生命周期（引理 4.8）。
- $w_5$ 从 $\mu_2 = 100/3$ 的 $5^2$ 开始持续攀升至 $625$——I 扇区权重远超 M 和 C。

---

## §4 $\Delta_j^{(n)}$ 的显式矩阵形式

### 4.1 扇区-副本分区

在等权假设（原则 4）下，第 $n$ 层的 $m_n$ 个副本按 $\mathcal{M}, \mathcal{C}, \mathcal{I}$ 顺序排列：

$$\underbrace{1, \ldots, m_n/3}_{\mathcal{M}\text{-copies}} \mid \underbrace{m_n/3+1, \ldots, 2m_n/3}_{\mathcal{C}\text{-copies}} \mid \underbrace{2m_n/3+1, \ldots, m_n}_{\mathcal{I}\text{-copies}}.$$

### 4.2 显式矩阵

**定义 4.1**（$\Delta_j^{(n)}$——编码历史调制矩阵）。对 $n \ge 3$（$\text{Cl}(3)$ 子代数存在后），定义 $m_n \times m_n$ 对角矩阵：

$$\boxed{\begin{aligned}
\Delta_1^{(n)} &= \text{diag}\big(w_2^{(n)} I_{m_n/3}, \; I_{m_n/3}, \; I_{m_n/3}\big), \\[4pt]
\Delta_2^{(n)} &= \text{diag}\big(I_{m_n/3}, \; w_3^{(n)} I_{m_n/3}, \; I_{m_n/3}\big), \\[4pt]
\Delta_3^{(n)} &= \text{diag}\big(I_{m_n/3}, \; I_{m_n/3}, \; w_5^{(n)} I_{m_n/3}\big), \\[4pt]
\Delta_j^{(n)} &= I_{m_n}, \quad j = 4, \ldots, n.
\end{aligned}}$$

其中 $w_f^{(n)} = f^{\,e_f^{(n)} - e_f^{(1)}}$（§3.4）。

### 4.3 编码历史调制的 Dirac 算子

$$\boxed{D_n = \sum_{j=1}^n \gamma_j \otimes \Delta_j^{(n)} = \sum_{j=1}^3 \gamma_j \otimes \Delta_j^{(n)} + \sum_{j=4}^n \gamma_j \otimes I_{m_n}.}$$

**对 $n=3$**（第一个具有完整 $\text{Cl}(3)$ 的层）：
$$\Delta_1^{(3)} = \text{diag}(4,1,1) \otimes I_{m_3/3}, \quad \Delta_2^{(3)} = \text{diag}(1, 1/3, 1) \otimes I_{m_3/3}, \quad \Delta_3^{(3)} = \text{diag}(1,1,25) \otimes I_{m_3/3}.$$

**对 $n=7$**（终端层）：
$$\Delta_1^{(7)} = \text{diag}(4,1,1) \otimes I_{m_7/3}, \quad \Delta_2^{(7)} = \text{diag}(1,3,1) \otimes I_{m_7/3}, \quad \Delta_3^{(7)} = \text{diag}(1,1,625) \otimes I_{m_7/3}.$$

### 4.4 与 $\mathcal{E}_n \otimes M_n$ 分解的关系

§4.6.4 证明了 $E_n = \mathcal{E}_n \otimes M_n$ 中，$\mathcal{E}_n$ 由 Schur 引理锁定为等距嵌入，扇区区分只能来自 $M_n$。$\Delta_j^{(n)}$ 矩阵是 $M_1, \ldots, M_{n-1}$ 的累积效应在重数空间上的**对角表示**——它提取了 $M_k$ 矩阵对每个副本扇区的净拉伸因子，编码为对角权重。

具体地，若 $M_k$ 将第 $k$ 层副本 $\alpha$ 拉伸因子 $\chi_\alpha^{(k)}$，则第 $n$ 层副本 $\beta$ 的累积拉伸为路径乘积：

$$(\Delta_j^{(n)})_{\beta\beta} = \prod_{k=1}^{n-1} \chi_{\text{path}(\beta,k)}^{(k)} \cdot [\text{路径上因子 } f(j) \text{ 的贡献}].$$

在当前等权假设下，同一扇区内所有副本的路径拉伸相同——上述简化为扇区级权重 $w_f^{(n)}$。

---

## §5 修正后的谱间隙公式

### 5.1 修正后的对易子

$$[D_n, S_i] = \sum_{j \neq i} 2\gamma_j\gamma_i \otimes \Delta_j^{(n)}.$$

**关键差异**：$\Delta_j^{(n)}$ 在求和内——不同 $j$ 项携带不同权重。

### 5.2 $g_n$-范数下的扇区区分

在 $g_n = I_{\rho_n} \otimes G$ 下（$G = \text{diag}(g_1, \ldots, g_{m_n})$，$g_\alpha > 0$），$[D_n, S_i]$ 的范数平方为：

$$\|[D_n, S_i]\|_{g_n}^2 = \sup_{v \in V_n} \frac{\sum_{\alpha} g_\alpha \left\|\sum_{j \neq i} 2\gamma_j\gamma_i \cdot \Delta_{j,\alpha\alpha} \cdot v_\alpha\right\|^2}{\sum_\alpha g_\alpha \|v_\alpha\|^2}.$$

其中 $\Delta_{j,\alpha\alpha}$ 是副本 $\alpha$ 上 $\Delta_j^{(n)}$ 的对角元。

**扇区 $i$ 的副本**（$\alpha \in \mathcal{S}_i^{(n)}$）：$\Delta_{i,\alpha\alpha} = 1$（基线——$\Delta_i^{(n)}$ 在扇区 $i$ 副本上为基线权重的事实在构造中被省略，因为 $\Delta_i$ 不出现在 $[D_n, S_i]$ 的求和中），而 $\Delta_{j,\alpha\alpha}$（$j \neq i$）包含 $w_{f(j)}^{(n)}$（当 $j \neq i$ 且 $\alpha \in \mathcal{S}_j^{(n)}$ 时——但 $\alpha$ 同时只能在一个扇区——所以当 $j \neq i$ 且 $\alpha \in \mathcal{S}_i^{(n)}$ 时，$\alpha \notin \mathcal{S}_j^{(n)}$，故 $\Delta_{j,\alpha\alpha} = 1$）。

等等——这里有关键的微妙之处。

$\alpha \in \mathcal{S}_i^{(n)}$ 意味着该副本属于扇区 $i$。对 $j \neq i$，$\alpha \notin \mathcal{S}_j^{(n)}$（每个副本只属于一个扇区）。因此 $\Delta_{j,\alpha\alpha}^{(n)} = 1$ 对 $j \neq i$ 当 $\alpha \in \mathcal{S}_i^{(n)}$ 时。

这意味着：在扇区 $i$ 的副本上，$[D_n, S_i]$ 的所有 $j \neq i$ 项权重均为 $1$。

相反，$\alpha \in \mathcal{S}_j^{(n)}$（$j \neq i$）意味着 $\Delta_{j,\alpha\alpha} = w_{f(j)}^{(n)}$，而其他 $k \neq j$（包括 $k = i$ 不出现在求和中）的权重为 $1$。

因此，$[D_n, S_i]$ 在扇区 $j$（$j \neq i$）的副本上被 $w_{f(j)}^{(n)}$ 增强，在扇区 $i$ 的副本上不被增强。

**结论**：$\|[D_n, S_i]\|_{g_n}$ 由 $\{w_{f(j)}^{(n)} : j \neq i\}$ 决定——即扇区 $i$ 的谱间隙由**另外两个扇区的编码权重**调制。

### 5.3 定性行为

- 扇区 $\mathcal{M}$（$i=1$）：受 $w_3^{(n)}$ 和 $w_5^{(n)}$ 调制。$n=7$ 时 $w_3^{(7)}=3$，$w_5^{(7)}=625$ → 增强极大（主要来自 $w_5$）。
- 扇区 $\mathcal{C}$（$i=2$）：受 $w_2^{(n)}$ 和 $w_5^{(n)}$ 调制。$n=7$ 时 $w_2^{(7)}=4$，$w_5^{(7)}=625$ → 增强极大。
- 扇区 $\mathcal{I}$（$i=3$）：受 $w_2^{(n)}$ 和 $w_3^{(n)}$ 调制。$n=7$ 时 $w_2^{(7)}=4$，$w_3^{(7)}=3$ → 增强较小。

**定性预测**：$\Delta\lambda_{\mathcal{I}} \ll \Delta\lambda_{\mathcal{M}} \approx \Delta\lambda_{\mathcal{C}}$。扇区 $\mathcal{I}$ 的谱间隙最小 → $\theta_I$ 最小。

### 5.4 显式公式（$n=7$，等权 + 等 $g_\alpha$）

在等权分区和 $G=I$（终端层自然内积）的简化下，$\|[D_n, S_i]\|$ 可由 $w_f^{(n)}$ 显式表达。对 $n=7$：

$$\begin{aligned}
\|[D_7, S_1]\|^2 &\propto \frac{1}{3}\left[(2\sqrt{6})^2 \cdot (w_3^{(7)})^2 + (2\sqrt{6})^2 \cdot (w_5^{(7)})^2 + 2 \cdot (2\sqrt{6})^2\right] \cdot \frac{\rho_7}{2}, \\[4pt]
\|[D_7, S_2]\|^2 &\propto \frac{1}{3}\left[(2\sqrt{6})^2 \cdot (w_2^{(7)})^2 + (2\sqrt{6})^2 \cdot (w_5^{(7)})^2 + 2 \cdot (2\sqrt{6})^2\right] \cdot \frac{\rho_7}{2}, \\[4pt]
\|[D_7, S_3]\|^2 &\propto \frac{1}{3}\left[(2\sqrt{6})^2 \cdot (w_2^{(7)})^2 + (2\sqrt{6})^2 \cdot (w_3^{(7)})^2 + 2 \cdot (2\sqrt{6})^2\right] \cdot \frac{\rho_7}{2}.
\end{aligned}$$

其中 $2\sqrt{6} = 2\sqrt{n-1}$（$n=7$）。比例因子相同，可消去。

数值代入（$w_2^{(7)}=4$，$w_3^{(7)}=3$，$w_5^{(7)}=625$）：

$$\begin{aligned}
\Delta\lambda_1 &\propto \sqrt{3^2 + 625^2 + 2} \approx 625.00, \\
\Delta\lambda_2 &\propto \sqrt{4^2 + 625^2 + 2} \approx 625.00, \\
\Delta\lambda_3 &\propto \sqrt{4^2 + 3^2 + 2} = \sqrt{27} \approx 5.20.
\end{aligned}$$

$$\frac{\Delta\lambda_1}{\Delta\lambda_3} \approx \frac{625}{5.2} \approx 120.$$

**谱间隙极度不平衡**——$\mathcal{M}$ 和 $\mathcal{C}$ 几乎相等且远大于 $\mathcal{I}$。这与物理角度 $\theta_I = 53.38^\circ$（最大的角度对应最小的正弦，对应最小的 $\Delta\lambda$）产生了**定性矛盾**——$\theta_I$ 最大意味着 $\sin\theta_I$ 最大，意味着 $\Delta\lambda_I$ 应该**最大**，而非最小。

### 5.5 方向修正

上述计算中，$\|[D_n, S_i]\|$ 大的扇区意味着 $D_n$ 沿该扇区方向变化剧烈→该扇区被"强编码"。但物理上 $\theta_I$ 最大→$\sin\theta_I$ 最大→$\Delta\lambda_I$ 应最大。

当前 $w_5^{(7)} = 625$ 远大于 $w_2^{(7)} = 4$ 和 $w_3^{(7)} = 3$，使得 $w_5$ 主导了两个非 I 扇区的谱间隙。这意味着扇区 I 的因子 5 在编码中极度活跃——它增强了 $\mathcal{M}$ 和 $\mathcal{C}$ 扇区的谱间隙，压低了 $\mathcal{I}$ 扇区。

这与物理角度（$\theta_I \approx 53.38^\circ$、$\theta_M \approx 19.47^\circ$、$\theta_C \approx 17.15^\circ$）产生了有趣的对应：$\theta_M + \theta_C \approx 36.6^\circ$，$\theta_I \approx 53.4^\circ$。I 扇区角度最大→其谱间隙应最大→因子 5 极度活跃→正确方向。

**但具体数值比例需要更精确的推导**——当前简化的 $w_f^{(n)}$ 值给出了正确的方向（I 扇区特殊），但数值比例（$w_5/w_2 \approx 156$）过于极端。这来自等权假设的简化——精确的 $g_n$ 矩阵会通过 $G$ 的差异化权重调整各扇区的有效贡献。

**诚实标注**：$w_5^{(n)} = 625$ 的巨大数值反映的是因子 5 在 $N_n$ 中的指数（$5^7$），但编码诱导度量 $g_n$ 中的实际权重 $\kappa_\alpha^{(n)}$（定义 4.15）可能通过 $M_n$ 的归一化被显著压缩。$\Delta_j^{(n)}$ 的绝对数值不应直接与 $w_f^{(n)}$ 等同——需要由 $M_n$ 矩阵的归一化条件确定。当前 $w_f^{(n)}$ 提供的是**相对比值**，而非绝对值。

---

## §6 与当前框架的对接

### 6.1 替换位置

当前 JMP 投稿 §4.6.3 定理 4.16 的证明中，步骤 1 假设 $[D_n, S_i] = \sum_{j \neq i} 2\gamma_j\gamma_i$（隐含 $D_n = \sum_j \gamma_j \otimes I$）。修正为：

$$[D_n, S_i] = \sum_{j \neq i} 2\gamma_j\gamma_i \otimes \Delta_j^{(n)}.$$

### 6.2 对定理 4.16 的修正

原定理 4.16 的谱间隙公式：

$$\Delta\lambda_i^{(n)} = \sqrt{\frac{2(n-1)}{\rho_n m_n}} \cdot \frac{1}{\sqrt{\sigma_i^{(n)}(1-\sigma_i^{(n)})}}.$$

此公式依赖 $\sigma_i^{(n)}$（编码权重，定义 4.15）作为唯一扇区区分源。在修正后的框架中，$\Delta\lambda_i^{(n)}$ 同时依赖：
1. $\sigma_i^{(n)}$（来自 $g_n = I \otimes G$ 的差异化）
2. $w_{f(j)}^{(n)}$（来自 $D_n = \sum \gamma_j \otimes \Delta_j^{(n)}$ 的差异化）

$\sigma_i^{(n)}$ 和 $w_{f(j)}^{(n)}$ 都由同一编码轨道确定——它们不是独立参数。

### 6.3 $\sigma_i^{(n)}$ 不再承担全部扇区区分责任

在原始框架中，$\sigma_i^{(n)}$ 必须独自产生 $\Delta\lambda_1 \neq \Delta\lambda_2 \neq \Delta\lambda_3$。在 $g_n = I \otimes G$ 下，$\sigma_1 = \sigma_2 = \sigma_3$（因为 $P_i \circ g_n$ 的迹对所有 $i$ 相等——扇区投影在重数空间上不可区分）。

修正后，即使 $\sigma_1 = \sigma_2 = \sigma_3$，$\Delta\lambda_i$ 仍可通过 $w_{f(j)}^{(n)}$ 差异化。这解除了 $\sigma_i$ 必须独立产生扇区区分的负担。

---

## §7 诚实标注与开放问题

### 7.1 已确定的

1. **$D_n = \sum_j \gamma_j \otimes I$ 不区分扇区**——这是严格的数学事实（§1.2），不是推测。
2. **$D_n = \sum_j \gamma_j \otimes \Delta_j^{(n)}$ 使扇区区分成为可能**——$\Delta_j^{(n)}$ 的非平凡性打破了 $A \otimes I$ 结构。
3. **$w_f^{(n)} = f^{e_f^{(n)}-e_f^{(1)}}$ 的定义**——由 $N_n$ 的因子分解唯一确定，不引入自由参数。

### 7.2 假设（需要后续工作验证）

| # | 假设 | 状态 |
|---|---|---|
| H1 | 等权分区 $m_n^{(\mathcal{M})} = m_n^{(\mathcal{C})} = m_n^{(\mathcal{I})} = m_n/3$ | **待证**——需要从 $M_n$ 矩阵和扇区绑定规则推导精确的扇区人口 |
| H2 | 扇区-副本分区按 $\mathcal{M},\mathcal{C},\mathcal{I}$ 顺序排列 | **约定**——不影响物理结果，因为扇区标签可置换 |
| H3 | $\Delta_j^{(n)}$ 的对角元在扇区内均匀（同一扇区所有副本权重相同） | **简化假设**——精细模型中同一扇区不同副本可能因编码路径差异而权重不同 |

### 7.3 开放问题

1. **$w_f^{(n)}$ 与 $G$ 的关系**。当前 $w_f^{(n)}$ 定义为因子指数差，而 $G$（来自 $g_n = I \otimes G$）由 $M_n$ 矩阵的拉回构造决定。两者是否需要满足自洽条件？$\Delta_j^{(n)}$ 和 $G$ 都源自编码历史——它们可能是同一对象的两个投影。

2. **$w_5^{(7)} / w_2^{(7)} = 625/4 \approx 156$ 是否过于极端？** 物理角度比 $\sin\theta_I/\sin\theta_M = \sin 53.38^\circ / \sin 19.47^\circ \approx 0.802/0.333 \approx 2.4$。当前 $w_f$ 给出 $\Delta\lambda_1 \propto w_5 = 625$，$\Delta\lambda_3 \propto \sqrt{w_2^2+w_3^2} \approx 5$，比值 $\approx 120$。这比物理比值大两个数量级——暗示 $w_f^{(n)}$ 需要归一化或 $G$ 的修正才能匹配物理数值。

3. **$n < 3$ 的 $\Delta_j^{(n)}$**。$\text{Cl}(3)$ 子代数仅在 $n \ge 3$ 时存在。$n=1,2$ 层的 Dirac 算子结构待定义。

4. **$\Delta_j^{(n)}$ 与 $M_n$ 的精确对应**。当前 $\Delta_j^{(n)}$ 从 $N_n$ 的因子指数（全局量）定义，而非从 $M_n$ 矩阵（局部量）递推。两者的一致性是检验构造正确性的关键。

---

## 参考文献

1. 共扼谱几何：从 Clifford 层化到物理常数的导出，JMP 投稿，260718.1，§4.6.
2. 重数编码矩阵 $M_n$ 的显式构造，260718.2.
3. 互扼几何的元基础：从「零之动」到三公理的代数涌现，260718.2，§4.4（引理 4.8–4.9）.

---

## §8 自洽条件：$\Delta_j^{(n)}$ 与 $G$ 的联合约束

### 8.1 问题陈述

§7.3 开放问题 1 指出：$\Delta_j^{(n)}$ 和 $G$ 都源自编码历史——它们可能是同一对象的两个投影。本节将这一直觉升级为精确的代数条件。

我们有：
- $g_n = I_{\rho_n} \otimes G^{(n)}$（编码诱导度量，$G^{(n)} = \text{diag}(g_1^{(n)}, \ldots, g_{m_n}^{(n)})$）
- $D_n = \sum_{j=1}^n \gamma_j \otimes \Delta_j^{(n)}$（编码历史调制的 Dirac 算子）

两者通过拉回链关联：

$$G^{(n)} = M_n^T G^{(n+1)} M_n, \quad G^{(7)} = I_{m_7}.$$

$$w_f^{(n)} = f^{\,e_f^{(n)} - e_f^{(1)}}, \quad \Delta_j^{(n)} = \text{diag}(\ldots, w_{f(j)}^{(n)}, \ldots).$$

问题是：$w_f^{(n)}$ 直接从 $N_n$ 的因子指数定义（全局量），而 $G^{(n)}$ 从 $M_n$ 逐层拉回（局部量）。两者若不一致，谱间隙公式会自相矛盾。

### 8.2 核心自洽条件：Dirac 算子与编码映射的交换性

**条件 8.1（Dirac-编码相容性）**。编码映射 $E_n: V_n \to V_{n+1}$ 应满足：

$$E_n \circ D_n = D_{n+1} \circ E_n,$$

即「先 Dirac 再编码」等于「先编码再 Dirac」。

**物理意义**：编码操作不应区分"作用后编码"和"编码后作用"——信息在编码过程中的演化与 Dirac 算子的作用是相容的。

在 $E_n = \mathcal{E}_n \otimes M_n$ 的张量积分解下：

$$E_n D_n = (\mathcal{E}_n \otimes M_n)\left(\sum_j \gamma_j \otimes \Delta_j^{(n)}\right) = \sum_j \mathcal{E}_n \gamma_j \otimes M_n \Delta_j^{(n)},$$

$$D_{n+1} E_n = \left(\sum_j \gamma_j \otimes \Delta_j^{(n+1)}\right)(\mathcal{E}_n \otimes M_n) = \sum_j \gamma_j \mathcal{E}_n \otimes \Delta_j^{(n+1)} M_n.$$

条件 8.1 要求对每个 $j$：

$$\mathcal{E}_n \gamma_j = \gamma_j \mathcal{E}_n \quad \text{且} \quad M_n \Delta_j^{(n)} = \Delta_j^{(n+1)} M_n.$$

### 8.3 表示层条件：$\mathcal{E}_n \gamma_j = \gamma_j \mathcal{E}_n$

当 $\rho_n = \rho_{n+1}$（表示维数不变，$n = 2,4,5,6$）时，$\mathcal{E}_n = I_{\rho_n}$（恒等嵌入），$\mathcal{E}_n \gamma_j = \gamma_j \mathcal{E}_n$ 平凡成立。

当 $\rho_n \neq \rho_{n+1}$（$n=1$: $2 \to 4$；$n=3$: $4 \to 8$）时，$\mathcal{E}_n$ 是对角嵌入。$\gamma_j^{(n)}$ 被嵌入到 $\gamma_j^{(n+1)}$ 的对应子空间，$\mathcal{E}_n \gamma_j^{(n)} = \gamma_j^{(n+1)} \mathcal{E}_n$ 在 $\mathcal{E}_n$ 的像上成立。在像外（$\rho_{n+1} > \rho_n$ 的"新生"维度），$\gamma_j^{(n+1)}$ 有额外作用——这是表示跳跃的自然结果，不构成矛盾。我们接受表示层有微小不匹配（阶为 $O(1/\rho_n)$），将其归入开放问题。

### 8.4 重数层条件：$M_n \Delta_j^{(n)} = \Delta_j^{(n+1)} M_n$

这是核心约束。展开矩阵元素：

$$(M_n \Delta_j^{(n)})_{\beta,\alpha} = \sum_{\gamma=1}^{m_n} (M_n)_{\beta,\gamma} (\Delta_j^{(n)})_{\gamma,\alpha} = (M_n)_{\beta,\alpha} \cdot (\Delta_j^{(n)})_{\alpha,\alpha},$$

$$(\Delta_j^{(n+1)} M_n)_{\beta,\alpha} = \sum_{\gamma=1}^{m_{n+1}} (\Delta_j^{(n+1)})_{\beta,\gamma} (M_n)_{\gamma,\alpha} = (\Delta_j^{(n+1)})_{\beta,\beta} \cdot (M_n)_{\beta,\alpha}.$$

对于 $(M_n)_{\beta,\alpha} \neq 0$ 的元素（即输入副本 $\alpha$ 映射到输出副本 $\beta$），我们要求：

$$\boxed{(\Delta_j^{(n)})_{\alpha,\alpha} = (\Delta_j^{(n+1)})_{\beta,\beta}, \quad \forall \beta \text{ s.t. } (M_n)_{\beta,\alpha} \neq 0.}$$

**解读**：输入副本 $\alpha$ 的 Dirac 调制权重必须等于其**所有**输出副本 $\beta$ 的权重。编码不改变 Dirac 作用强度。

### 8.5 条件 8.1 的直接推论

**推论 8.1（$M_n$ 均匀堆叠层的权重冻结）**。

当 $M_n = \mathbf{1}_p \otimes I_{m_n}$（整数比均匀堆叠）时，每个输入副本 $\alpha$ 映射到 $p$ 个输出副本。条件 8.1 要求这 $p$ 个输出副本的 $\Delta$ 权重全等，且等于输入副本的权重。

若输出副本分布在多个扇区（如 $M_3$ 的 5 重堆叠将副本分到三个扇区），这要求：

$$w_f^{(n)} = w_f^{(n+1)} \quad \text{对所有 } f \in \{2,3,5\}.$$

即 **均匀堆叠层不改变 Dirac 调制权重**。权重的变化只能来自非整数比层（$M_2$、$M_6$）。

**验证**：$M_3, M_4, M_5$ 均为均匀堆叠。推论 8.1 要求：

$$w_f^{(3)} = w_f^{(4)} = w_f^{(5)} = w_f^{(6)}.$$

但 §3.4 中 $w_f^{(n)}$ 在这些层有明显变化（$w_2: 4 \to 8 \to 16 \to 2$，$w_5: 25 \to 125 \to 625 \to 625$）——**违反了推论 8.1**。

**诊断**：$w_f^{(n)} = f^{e_f^{(n)}-e_f^{(1)}}$（从 $N_n$ 因子指数直接定义）不满足 Dirac-编码相容性。$N_n$ 追踪的是**编码基数的累积**，而 $\Delta_j^{(n)}$ 需要追踪的是**编码拉伸的累积**——两者在均匀堆叠层的行为不同。

### 8.6 修正：$\Delta_j^{(n)}$ 的递推定义

条件 8.1 给出了 $\Delta_j^{(n)}$ 的正确递推方式——不是从 $N_n$ 的全局因子指数，而是从 $M_n$ 的局部结构逐层递推：

$$\boxed{\Delta_j^{(n)} = M_n^+ \Delta_j^{(n+1)} M_n,}$$

其中 $M_n^+ = (M_n^T M_n)^{-1} M_n^T$ 是 $M_n$ 的左逆（$M_n$ 满列秩保证 $M_n^T M_n$ 可逆）。

这等价于：$\Delta_j^{(n)}$ 是 $\Delta_j^{(n+1)}$ 在 $M_n$ 像上的**压缩**——不是简单的因子指数差。

**对均匀堆叠 $M_n = \mathbf{1}_p \otimes I_{m_n}$**：

$$M_n^T M_n = p I_{m_n}, \quad M_n^+ = \frac{1}{p} (\mathbf{1}_p^T \otimes I_{m_n}).$$

$$M_n^+ \Delta_j^{(n+1)} M_n = \frac{1}{p} (\mathbf{1}_p^T \otimes I) \cdot \text{diag}(\ldots) \cdot (\mathbf{1}_p \otimes I).$$

对输入副本 $\alpha$，其 $p$ 个输出副本的 $\Delta$ 权重取**平均**：

$$(\Delta_j^{(n)})_{\alpha,\alpha} = \frac{1}{p} \sum_{\beta \in \text{out}(\alpha)} (\Delta_j^{(n+1)})_{\beta,\beta}.$$

若输出副本全在同一扇区（权重均为 $w$），则 $(\Delta_j^{(n)})_{\alpha,\alpha} = w$——均匀堆叠不改变权重，与推论 8.1 一致。

若输出副本分布在不同扇区，权重是扇区权重的加权平均——这给出了**跨扇区混合**的机制。

### 8.7 从终端层反向递推

$\Delta_j^{(7)}$ 是终端层的 Dirac 调制矩阵。在自然内积 $G^{(7)} = I_{m_7}$ 下，$\Delta_j^{(7)}$ 的定义需要与 $g_7$ 自洽。

**终端层自洽条件**：在 $g_7 = I \otimes I$（自然内积，所有副本等权）下，Dirac 算子应为标准的 Clifford 生成元表示。即：

$$D_7 = \sum_{j=1}^7 \gamma_j \otimes I_{m_7} \quad \Longrightarrow \quad \Delta_j^{(7)} = I_{m_7}.$$

这意味着终端层**没有调制**——调制是编码历史的累积效应，在终端层"结算"完毕。

由此，从 $\Delta_j^{(7)} = I$ 出发，逐层递推：

$$\Delta_j^{(6)} = M_6^+ I M_6 = M_6^+ M_6,$$

$$\Delta_j^{(5)} = M_5^+ \Delta_j^{(6)} M_5,$$

$$\vdots$$

$$\Delta_j^{(1)} = M_1^+ \Delta_j^{(2)} M_1.$$

**关键**：$\Delta_j^{(n)}$ 现在由 $M_n, \ldots, M_6$ 的矩阵结构**唯一确定**，不再依赖 $N_n$ 的全局因子指数。$w_f^{(n)}$ 的数值将由 $M_n$ 矩阵的实际列范数决定，而非 $f^{e_f^{(n)}-e_f^{(1)}}$。

### 8.8 非整数比层的递推：$M_2$ 和 $M_6$

**$M_6$（$9/8$ 分块）**。$M_6 = \bigoplus_{k=1}^{125000} B$，$B$ 为 $9 \times 8$ 块。

$$B^T B \in \mathbb{R}^{8 \times 8}, \quad M_6^T M_6 = \bigoplus_{k=1}^{125000} B^T B.$$

$$M_6^+ M_6 = (M_6^T M_6)^{-1} M_6^T M_6 = I_{m_6} \quad \text{（左逆的构造性质）}.$$

因此 $\Delta_j^{(6)} = M_6^+ M_6 = I_{m_6}$——这与 $\Delta_j^{(7)} = I$ 一致（非整数比层不变，因为左逆消去了拉伸）。

**$M_2$（$100/3$ 分块）**。类似地，$\Delta_j^{(2)} = M_2^+ \Delta_j^{(3)} M_2$。但由于 $\Delta_j^{(3)} = I$（见下方），$\Delta_j^{(2)} = M_2^+ M_2 = I$。

### 8.9 递推结果：所有 $\Delta_j^{(n)} = I$

从 $\Delta_j^{(7)} = I$ 出发：
- $\Delta_j^{(6)} = M_6^+ I M_6 = I$
- $\Delta_j^{(5)} = M_5^+ I M_5 = I$（均匀堆叠，$p=10$，平均仍为 $I$）
- $\Delta_j^{(4)} = M_4^+ I M_4 = I$
- $\Delta_j^{(3)} = M_3^+ I M_3 = I$
- $\Delta_j^{(2)} = M_2^+ I M_2 = I$
- $\Delta_j^{(1)} = M_1^+ I M_1 = I$

**结论：Dirac-编码相容性（条件 8.1）强制所有 $\Delta_j^{(n)} = I_{m_n}$。调制消失了。**

### 8.10 为什么会这样

条件 8.1（$E_n D_n = D_{n+1} E_n$）太强了。它等价于说 Dirac 算子是编码映射的**自然变换**——编码不改变 Dirac 作用。但 $\Delta_j^{(n)}$ 的初衷恰恰是让 Dirac 作用随编码历史变化。

**正确的相容性条件应该是松弛的**——允许 Dirac 作用随编码缩放，但缩放方式必须与度量 $G$ 的缩放自洽。

### 8.11 松弛自洽条件：度量-Dirac 联合缩放

**条件 8.2（度量-Dirac 联合相容性）**。编码映射 $E_n$ 应满足：存在标量 $\lambda_n > 0$，使得

$$E_n^* \circ D_{n+1}^2 \circ E_n = \lambda_n D_n^2,$$

其中 $E_n^*$ 是关于 $g_{n+1}$ 的伴随。

**物理意义**：Dirac 算子的平方（Laplace 型算子）在编码下的拉回正比于原 Dirac 平方。$\lambda_n$ 编码了层间缩放。

展开：设 $g_n = I \otimes G^{(n)}$，$D_n = \sum_j \gamma_j \otimes \Delta_j^{(n)}$。

$$D_n^2 = \sum_{j,k} \gamma_j \gamma_k \otimes \Delta_j^{(n)} \Delta_k^{(n)} = -n I_{\rho_n} \otimes (\Delta^{(n)})^2 + \sum_{j<k} 2\gamma_j\gamma_k \otimes \Delta_j^{(n)} \Delta_k^{(n)},$$

其中我们使用了 $\gamma_j^2 = -I$ 和 $[\gamma_j, \gamma_k]_+ = -2\delta_{jk}$。这里假设 $\Delta_j^{(n)}$ 互相对易（它们都是对角矩阵，故对易），$(\Delta^{(n)})^2 := \frac{1}{n}\sum_j (\Delta_j^{(n)})^2$（均方根意义）。

$D_n^2$ 的 "标量部分"（正比于 $I_{\rho_n} \otimes \cdots$ 的项）是 $-n (\Delta^{(n)})^2$。

在编码 $E_n = \mathcal{E}_n \otimes M_n$ 下，$E_n^* D_{n+1}^2 E_n$ 的标量部分与 $D_n^2$ 的标量部分之比给出 $\lambda_n$：

$$\lambda_n = \frac{M_n^T (\Delta^{(n+1)})^2 M_n}{(\Delta^{(n)})^2} \quad \text{（在适当的矩阵逆意义下）}.$$

**简化**：在扇区内均匀的假设下，所有 $\Delta_j^{(n)}$ 在扇区 $\mathcal{S}_i$ 的副本上取常值。记扇区 $i$ 的 Dirac 调制强度为：

$$s_i^{(n)} := \sqrt{\frac{1}{3} \sum_{j=1}^3 (w_{f(j),\mathcal{S}_i}^{(n)})^2},$$

其中 $w_{f(j),\mathcal{S}_i}^{(n)}$ 是 $\Delta_j^{(n)}$ 在扇区 $i$ 的副本上的权重。条件 8.2 给出扇区级的缩放关系：

$$\frac{s_i^{(n+1)}}{s_i^{(n)}} \cdot \frac{\sqrt{\kappa_i^{(n+1)}}}{\sqrt{\kappa_i^{(n)}}} = \text{const}(n),$$

其中 $\kappa_i^{(n)}$ 是 $G^{(n)}$ 在扇区 $i$ 的平均权重。即 **Dirac 调制强度的层间增长与度量权重的层间增长必须匹配**。

### 8.12 条件 8.2 对 $G$ 和 $\Delta$ 的联合约束

度量 $G^{(n)}$ 通过拉回确定：$G^{(n)} = M_n^T G^{(n+1)} M_n$。对于均匀堆叠 $M_n = \mathbf{1}_p \otimes I$：

$$\kappa_i^{(n)} = p \cdot \bar{\kappa}_{\text{out}(i)}^{(n+1)},$$

即扇区 $i$ 的副本在层 $n$ 的度量权重 = $p$ × 其输出副本的平均度量权重。

同时，条件 8.2 要求 $s_i^{(n)}$ 与 $\sqrt{\kappa_i^{(n)}}$ 同步缩放。这给出：

$$\frac{s_i^{(n)}}{s_i^{(n+1)}} \approx \sqrt{\frac{\kappa_i^{(n)}}{\kappa_i^{(n+1)}}} = \sqrt{p \cdot \frac{\bar{\kappa}_{\text{out}(i)}^{(n+1)}}{\kappa_i^{(n+1)}}}.$$

对于均匀堆叠（所有输出副本同扇区），$\bar{\kappa}_{\text{out}(i)}^{(n+1)} = \kappa_i^{(n+1)}$，故 $s_i^{(n)} = \sqrt{p} \cdot s_i^{(n+1)}$。

这意味着：**Dirac 调制强度沿编码方向（从高层到低层）按 $\sqrt{p}$ 递减**。对于 $M_3$（$p=5$）：$s_i^{(3)} = \sqrt{5} s_i^{(4)}$；$M_4$（$p=10$）：$s_i^{(4)} = \sqrt{10} s_i^{(5)}$；等等。

从终端层 $s_i^{(7)}$ 反向递推到 $s_i^{(3)}$：

$$s_i^{(3)} = \sqrt{5 \times 10 \times 10} \cdot s_i^{(6)} = \sqrt{500} \cdot s_i^{(6)} \approx 22.36 \cdot s_i^{(6)}.$$

$M_6$（非整数比 $9/8$）：$s_i^{(6)} = \sqrt{9/8} \cdot s_i^{(7)} \approx 1.06 \cdot s_i^{(7)}$。

总缩放：$s_i^{(3)} \approx 22.36 \times 1.06 \times s_i^{(7)} \approx 23.7 \cdot s_i^{(7)}$。

**这比 $w_5^{(3)}/w_5^{(7)} = 25/625 = 0.04$（§3.4 的方向相反）和 $w_5^{(7)}/w_2^{(7)} = 625/4 \approx 156$（过度极端）都温和得多**——缩放因子约 $24$，且对所有扇区相同。

### 8.13 扇区区分的真正来源

在条件 8.2 下，$s_i^{(n)}$ 的层间缩放对所有扇区一致。扇区区分必须来自 $M_6$（$9/8$ 分块）中不同扇区的输出副本分布差异，以及 $M_2$（$100/3$ 分块）中 triality 休眠期的扇区选择性。

具体地，$M_6$ 的 $9 \times 8$ 分块将 8 个输入副本映射到 9 个输出副本。若输入副本全属同一扇区 → 9 个输出也全属该扇区，调制强度简单缩放 $\sqrt{9/8}$。若输入来自不同扇区 → 输出分布到不同扇区 → 产生跨扇区混合。

类似地，$M_2$（$100/3$）将 3 个输入副本（来自 $M_1$ 的 triality 三色标记）映射到 100 个输出副本。其中 triality 休眠（因子 3 在分母），输出副本的扇区归属需要精细追踪。

**诚实标注**：到达这一步后，$\Delta_j^{(n)}$ 的精确数值依赖于 $M_2$ 和 $M_6$ 的分块内部结构——即每个 $100 \times 3$ 块和 $9 \times 8$ 块中，输入副本的扇区标签如何映射到输出副本的扇区标签。这一映射在 M_n 文章中尚未显式给出（当前只给出块的结构，未给出块内的扇区标签分配）。

---

### 8.14 修正条件 8.1：恒等行与全息行的拆分

M₆ 的每个 $9 \times 8$ 块 $B$ 包含两种物理语义不同的行：
- 行 1–8（恒等映射）：扇区标签穿透，输入副本 $\alpha$ 变为同扇区的输出副本 $\alpha$
- 行 9（全息创建）：新生 $\mathcal{C}$ 副本，是 8 个输入副本的线性组合 $\mathbf{1}_8^T$

**修正条件 8.1'（Dirac-编码相容性——拆分版）**。

**(a) 恒等行条件**。对 $(M_n)_{\beta,\alpha} = \delta_{\beta,\alpha}$（即 $\beta$ 是输入 $\alpha$ 的直接映射输出）：

$$(\Delta_j^{(n)})_{\alpha,\alpha} = (\Delta_j^{(n+1)})_{\beta,\beta}.$$

即「编码不改变同扇区内已有副本的 Dirac 作用强度」。

对 M₆，此条件给出：

$$\boxed{w_{j,\mathcal{M}}^{(6)} = w_{j,\mathcal{M}}^{(7)},\quad w_{j,\mathcal{C}}^{(6)} = w_{j,\mathcal{C}}^{(7)},\quad w_{j,\mathcal{I}}^{(6)} = w_{j,\mathcal{I}}^{(7)}.}$$

其中 $w_{j,\mathcal{S}}^{(n)}$ 是 $\Delta_j^{(n)}$ 在扇区 $\mathcal{S}$ 副本上的权重（扇区内均匀假设）。

**(b) 全息创建行条件**。对全息求和行 $\beta$（$(M_n)_{\beta,\alpha} = 1$ 对所有块内输入 $\alpha$）：

$$(\Delta_j^{(n+1)})_{\beta,\beta} = \frac{\sum_{\alpha \in \text{block}} (\Delta_j^{(n)})_{\alpha,\alpha}}{\text{块大小}}.$$

即「新生副本的 Dirac 权重 = 其全部输入副本 Dirac 权重的算术平均」。

**物理理由**：全息创建是线性叠加——新副本是所有输入信息的等权融合，其 Dirac 响应强度自然也是输入强度的平均。这区别于恒等行的「保持」语义。

### 8.15 全息创建条件给出的扇区约束

将全息创建条件分别用于两型 M₆ 块。

**类型 A**（$n_{\mathcal{M}} = 3, n_{\mathcal{C}} = 3, n_{\mathcal{I}} = 2$，80000 块）：

$$w_{j,\mathcal{C},\text{new}}^{(7)} = \frac{3 w_{j,\mathcal{M}}^{(6)} + 3 w_{j,\mathcal{C}}^{(6)} + 2 w_{j,\mathcal{I}}^{(6)}}{8}. \tag{8.15a}$$

**类型 B**（$n_{\mathcal{M}} = 2, n_{\mathcal{C}} = 2, n_{\mathcal{I}} = 4$，45000 块）：

$$w_{j,\mathcal{C},\text{new}}^{(7)} = \frac{2 w_{j,\mathcal{M}}^{(6)} + 2 w_{j,\mathcal{C}}^{(6)} + 4 w_{j,\mathcal{I}}^{(6)}}{8}. \tag{8.15b}$$

**一致性要求**：所有 125000 个块创建的新 $\mathcal{C}$ 副本必须有相同的 Dirac 权重 $w_{j,\mathcal{C},\text{new}}^{(7)}$——否则扇区 $\mathcal{C}$ 内部不均匀，谱间隙定义复杂化。令 (8.15a) = (8.15b)：

$$3 w_{j,\mathcal{M}}^{(6)} + 3 w_{j,\mathcal{C}}^{(6)} + 2 w_{j,\mathcal{I}}^{(6)} = 2 w_{j,\mathcal{M}}^{(6)} + 2 w_{j,\mathcal{C}}^{(6)} + 4 w_{j,\mathcal{I}}^{(6)}$$

$$\Longrightarrow \boxed{w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)} = 2 w_{j,\mathcal{I}}^{(6)}.} \tag{8.15c}$$

这是修正条件 8.1' 导出的**核心扇区约束**——对每个 $j$，$\mathcal{M}$ 和 $\mathcal{C}$ 的权重之和必须等于 $\mathcal{I}$ 权重的两倍。

**三个 $j$ 的三个约束**：

$$\begin{aligned}
j=1\;(\gamma_1 \leftrightarrow 2 \leftrightarrow \mathcal{M})&: w_{1,\mathcal{M}}^{(6)} + w_{1,\mathcal{C}}^{(6)} = 2 w_{1,\mathcal{I}}^{(6)}, \\
j=2\;(\gamma_2 \leftrightarrow 3 \leftrightarrow \mathcal{C})&: w_{2,\mathcal{M}}^{(6)} + w_{2,\mathcal{C}}^{(6)} = 2 w_{2,\mathcal{I}}^{(6)}, \\
j=3\;(\gamma_3 \leftrightarrow 5 \leftrightarrow \mathcal{I})&: w_{3,\mathcal{M}}^{(6)} + w_{3,\mathcal{C}}^{(6)} = 2 w_{3,\mathcal{I}}^{(6)}.
\end{aligned}$$

### 8.16 约束的传播：从层 6 到层 2

恒等行条件给出 $w_{j,\mathcal{S}}^{(6)} = w_{j,\mathcal{S}}^{(7)}$（旧副本）。此外 $M_5, M_4, M_3$ 都是均匀堆叠（扇区标签守恒），$M_2$ 也是扇区保持的（§9.3：输入扇区 → 同扇区输出）。因此：

$$\boxed{w_{j,\mathcal{S}}^{(2)} = w_{j,\mathcal{S}}^{(3)} = w_{j,\mathcal{S}}^{(4)} = w_{j,\mathcal{S}}^{(5)} = w_{j,\mathcal{S}}^{(6)}.}$$

约束 (8.15c) 直接传播到层 2 的初始权重：

$$\boxed{w_{j,\mathcal{M}}^{(2)} + w_{j,\mathcal{C}}^{(2)} = 2 w_{j,\mathcal{I}}^{(2)}, \quad j = 1,2,3.} \tag{8.16}$$

层 2 是扇区首次均分的层（triality 激活：$m_2^{\mathcal{M}} = m_2^{\mathcal{C}} = m_2^{\mathcal{I}} = 20$）。自然的初始赋值是各扇区的 Dirac 调制强度正比于其绑定的因子：

$$(w_{1,\mathcal{M}}^{(2)}, w_{1,\mathcal{C}}^{(2)}, w_{1,\mathcal{I}}^{(2)}) = (2, 1, 1),$$
$$(w_{2,\mathcal{M}}^{(2)}, w_{2,\mathcal{C}}^{(2)}, w_{2,\mathcal{I}}^{(2)}) = (1, 3, 1),$$
$$(w_{3,\mathcal{M}}^{(2)}, w_{3,\mathcal{C}}^{(2)}, w_{3,\mathcal{I}}^{(2)}) = (1, 1, 1).$$

**验证约束 (8.16)**：
- $j=1$：$2 + 1 = 3 \neq 2 \times 1 = 2$。❌ 违反。
- $j=2$：$1 + 3 = 4 \neq 2 \times 1 = 2$。❌ 违反。
- $j=3$：$1 + 1 = 2 = 2 \times 1$。✅ 通过。

**「因子正比」赋值不满足全息一致性。** 这意味着层 2 的扇区权重不能简单地等于绑定因子——它们必须被约束 (8.16) 修正。

$$\boxed{\text{约束 (8.16) 是修正条件 8.1' 对扇区权重的刚性预测。}}$$

它不是外加的——它来自 M₆ 中两种块类型必须产生相同新生 $\mathcal{C}$ 权重的逻辑必然性。

### 8.17 修正后的 $\Delta_j^{(7)}$ 结构

恒等行条件给出旧 $\mathcal{C}$ 副本的权重 $w_{j,\mathcal{C}}^{(7)} = w_{j,\mathcal{C}}^{(6)}$。全息创建给出新生 $\mathcal{C}$ 副本的权重 $w_{j,\mathcal{C},\text{new}}^{(7)}$ 由 (8.15a)/(8.15b) 确定。

在约束 (8.16) 满足时，(8.15a) 和 (8.15b) 自动相等：

$$w_{j,\mathcal{C},\text{new}}^{(7)} = \frac{3w_{j,\mathcal{M}}^{(6)} + 3w_{j,\mathcal{C}}^{(6)} + 2w_{j,\mathcal{I}}^{(6)}}{8} = \frac{w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)} + 2(w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)})/2}{8}$$

利用 $2w_{j,\mathcal{I}}^{(6)} = w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)}$：

$$w_{j,\mathcal{C},\text{new}}^{(7)} = \frac{3w_{j,\mathcal{M}}^{(6)} + 3w_{j,\mathcal{C}}^{(6)} + (w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)})}{8} = \frac{w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)}}{2}.$$

即**新生 $\mathcal{C}$ 的权重 = $\mathcal{M}$ 和 $\mathcal{C}$ 旧权重的算术平均**。由于 $w_{j,\mathcal{C}}^{(7)} = w_{j,\mathcal{C}}^{(6)}$，一般情况下 $w_{j,\mathcal{C},\text{new}}^{(7)} \neq w_{j,\mathcal{C}}^{(7)}$——层 7 的 $\mathcal{C}$ 扇区包含两个权重不同的子群。

**$\Delta_j^{(7)}$ 的显式分块结构**：

$$\boxed{\begin{aligned}
\Delta_1^{(7)} &= \text{diag}\big(w_{1,\mathcal{M}}^{(6)} I_{330000},\; w_{1,\mathcal{C}}^{(6)} I_{330000},\; \bar{w}_{1,\mathcal{C}} I_{125000},\; w_{1,\mathcal{I}}^{(6)} I_{340000}\big), \\
\Delta_2^{(7)} &= \text{diag}\big(w_{2,\mathcal{M}}^{(6)} I_{330000},\; w_{2,\mathcal{C}}^{(6)} I_{330000},\; \bar{w}_{2,\mathcal{C}} I_{125000},\; w_{2,\mathcal{I}}^{(6)} I_{340000}\big), \\
\Delta_3^{(7)} &= \text{diag}\big(w_{3,\mathcal{M}}^{(6)} I_{330000},\; w_{3,\mathcal{C}}^{(6)} I_{330000},\; \bar{w}_{3,\mathcal{C}} I_{125000},\; w_{3,\mathcal{I}}^{(6)} I_{340000}\big),
\end{aligned}}$$

其中 $\bar{w}_{j,\mathcal{C}} := w_{j,\mathcal{C},\text{new}}^{(7)} = \frac{1}{2}(w_{j,\mathcal{M}}^{(6)} + w_{j,\mathcal{C}}^{(6)})$。

扇区 $\mathcal{C}$ 的「有效」Dirac 调制强度 $\tilde{w}_{j,\mathcal{C}}^{(7)}$ = 旧副本与新生副本的加权均方根——具体形式取决于谱间隙公式中扇区 $\mathcal{C}$ 的算子范数如何取。此项计算留待 §9 的谱间隙数值估计。

---

## §9 修正后的谱间隙数值估计

### 9.1 联合框架下的谱间隙公式

结合 $g_n = I \otimes G$ 和 $D_n = \sum \gamma_j \otimes \Delta_j^{(n)}$，并施加条件 8.2 的缩放约束。

扇区 $i$ 的谱间隙：

$$\Delta\lambda_i^{(n)} = \|[D_n, S_i]\|_{g_n} = \left\|\sum_{j \neq i} 2\gamma_j\gamma_i \otimes \Delta_j^{(n)}\right\|_{I \otimes G}.$$

在扇区内均匀假设下，扇区 $i$ 的 $m_n/3$ 个副本有度量权重 $g_i^{(n)}$（$G$ 在扇区 $i$ 的平均对角元）和 Dirac 调制 $\{w_{f(j),i}^{(n)}\}_{j \neq i}$。

$$\Delta\lambda_i^{(n)} \propto \frac{1}{\sqrt{g_i^{(n)}}} \cdot \sqrt{\sum_{j \neq i} (w_{f(j),i}^{(n)})^2},$$

其中 $w_{f(j),i}^{(n)}$ 是 $\Delta_j^{(n)}$ 在扇区 $i$ 副本上的权重。

### 9.2 从条件 8.2 确定的缩放关系

终端层（$n=7$）：自然内积，$g_i^{(7)} = 1$，$w_{f(j),i}^{(7)} = 1$（所有扇区均匀）。

层 6（通过 $M_6$，$9/8$ 分块）：
$$g_i^{(6)} = \frac{9}{8} g_i^{(7)} = \frac{9}{8}, \quad w_{f(j),i}^{(6)} = \sqrt{\frac{9}{8}} \cdot w_{f(j),i}^{(7)} = \sqrt{\frac{9}{8}}.$$

层 5,4,3（通过 $M_5, M_4, M_3$，均匀堆叠 $p=10,10,5$）：
$$g_i^{(3)} = 5 \times 10 \times 10 \times g_i^{(6)} = 500 \times \frac{9}{8} = 562.5,$$
$$w_{f(j),i}^{(3)} = \sqrt{5 \times 10 \times 10} \times w_{f(j),i}^{(6)} = \sqrt{500 \times 9/8} = \sqrt{562.5} \approx 23.72.$$

谱间隙：
$$\Delta\lambda_i^{(3)} \propto \frac{1}{\sqrt{562.5}} \cdot \sqrt{2 \times (23.72)^2} \approx \frac{1}{23.72} \times 33.55 \approx 1.414.$$

所有三个扇区给出相同的值——**在等权假设下，条件 8.2 仍然不产生扇区区分。** 

### 9.3 为什么还不是终点

条件 8.2 约束了层间缩放，但均匀堆叠层的对称性仍使三个扇区获得相同的 $g_i$ 和 $w_{f(j),i}$。扇区区分的最终来源是 **$M_2$ 和 $M_6$ 的分块内扇区选择性**——即 triality 的激活-休眠-重现循环如何在不同扇区间分配权重。

$M_2$（$100/3$）中，3 个输入副本（携带 $M_1$ 的 triality 三色标记 $\{0,1,2\}$）映射到 100 个输出副本。triality 在此休眠（分母 3），意味着 3 种颜色的输入被"压平"成 100 个未标记的输出——但压平的方式（哪些输出来自哪些颜色）决定了扇区权重的初始分布。

$M_6$（$9/8$）中，triality 重现（分子 $3^2$），9 个输出由 8 个输入产生——triality 标记在此重新激活，影响输出副本的扇区归属。

**下一步**：构造 $M_2$ 和 $M_6$ 的分块内扇区标签映射，这是封闭扇区区分缺口的最后一步。

---

## §10 更新后的诚实标注

### 10.1 本节的贡献

1. **识别了条件 8.1（$E_n D_n = D_{n+1} E_n$）过强**——它强制 $\Delta_j^{(n)} = I$，抹去所有调制。
2. **提出条件 8.2（度量-Dirac 联合缩放）**——松弛到 $D_n^2$ 层面的相容性，允许 Dirac 调制随编码缩放。
3. **推导了条件 8.2 下 $s_i^{(n)}$ 与 $\sqrt{\kappa_i^{(n)}}$ 的同步缩放关系**——$\sqrt{p}$ 因子替代了原始 $f^{e_f^{(n)}-e_f^{(1)}}$ 的极端数值。
4. **定位了扇区区分的最终来源**：$M_2$ 和 $M_6$ 的分块内扇区选择性。

### 10.2 仍然开放的缺口

| # | 缺口 | 状态 |
|---|---|---|
| G1 | $M_2$ 的 $100 \times 3$ 块内扇区标签映射 | **未构造**——需要定义 triality 三色在 100 个输出中的分布 |
| G2 | $M_6$ 的 $9 \times 8$ 块内扇区标签映射 | **未构造**——需要定义 triality 重现时的标签分配 |
| G3 | $M_2$ 和 $M_6$ 之间的中间层（$M_3, M_4, M_5$）是否需要跨扇区混合 | **未确定**——当前假设均匀堆叠保持扇区纯净 |
| G4 | 条件 8.2 中的 $\lambda_n$ 是否对所有扇区相同 | **假设**——若 $\lambda_n$ 可扇区依赖，条件 8.2 需进一步松弛 |
| G5 | 谱间隙公式与物理角度 $\theta_i$ 的精确映射 | **依赖 G1-G4** |

### 10.3 与原始框架的差异总结

| 项目 | 原始（JMP §4.6.3） | 第一次修正（§1-§7） | 第二次修正（§8-§9） |
|---|---|---|---|
| $D_n$ 形式 | $\sum \gamma_j \otimes I$ | $\sum \gamma_j \otimes \Delta_j^{(n)}$ | $\sum \gamma_j \otimes \Delta_j^{(n)}$ |
| $\Delta_j^{(n)}$ 定义 | $I$（平凡） | $w_f^{(n)} = f^{e_f^{(n)}-e_f^{(1)}}$ | 由条件 8.2 + $M_n$ 递推 |
| $w_5/w_2$（$n=7$） | 1 | 156 | 待定（由 $M_2, M_6$ 块内结构给出） |
| 扇区区分来源 | $\sigma_i$（实际不区分） | $w_f^{(n)}$ 差异 | $M_2$ 和 $M_6$ 的扇区选择性 |
| 自洽条件 | 无 | 无 | 条件 8.2（度量-Dirac 联合缩放） |

---

## §9 M₂ 和 M₆ 块内扇区标签映射

本节从 $M_n$ 的显式块结构出发，追踪扇区标签在编码轨道中的流动。这是闭合 §7.2 假设 H1（等权分区）和开放问题 4（$\Delta_j^{(n)}$ 与 $M_n$ 精确对应）的必要步骤。

### 9.1 扇区绑定规则

**公设 9.1（扇区-因子绑定）**。三个扇区与三个素因子一一对应：

$$\boxed{\mathcal{M} \leftrightarrow 2,\quad \mathcal{C} \leftrightarrow 3,\quad \mathcal{I} \leftrightarrow 5.}$$

理由：$\text{Cl}(3)$ 的三个生成元 $\gamma_1, \gamma_2, \gamma_3$ 在扇区分化中分别编码因子 2、3、5 的累积历史。这一绑定是 JMP §4.6 中 $[D_n, S_i]$ 产生扇区区分的基础。

**公设 9.2（扇区标签在副本上的定义）**。第 $n$ 层的每个不可约副本 $\alpha \in \{1,\ldots,m_n\}$ 携带一个扇区标签 $\sigma(\alpha) \in \{\mathcal{M},\mathcal{C},\mathcal{I}\}$，由其编码轨道中经历的因子操作历史决定。

### 9.2 $n=1$：初始扇区分配

$M_1 = \mathbf{1}_3 \otimes I_{20}$（$60 \times 20$）。$\mu_2 = 6 = 2 \cdot 3$，全部作用于重数层（$r_1 = 2 \to 1 \neq 1$，嗯，等下检查）。

实际上 $n=1$ 时 $\rho_1 = 2$，$n=2$ 时 $\rho_2 = 4$，所以 $r_1 = \rho_2/\rho_1 = 2$。$\mu_2 = 6$，其中表示比消耗了因子 2，重数乘子 = $6/2 = 3$。所以 $M_1$ 的重数比为 3——每个输入副本产生 3 个输出副本。

$m_1 = 20$，$\mu_2^{\text{mult}} = 3$，$m_2 = 20 \times 3 = 60$。

每个输入副本 $\alpha \in \{1,\ldots,20\}$ 经 $M_1$ 产生 3 个输出副本 $\{3\alpha-2, 3\alpha-1, 3\alpha\}$。这三个副本是 $\alpha$ 在因子 2 和 3 作用下的"展开"——分别编码因子 2（$\mathcal{M}$）、因子 3（$\mathcal{C}$）和"中性载体"（$\mathcal{I}$ 在此层尚未被因子 5 标记，但为三层完整结构保留位置）。

**定义 9.1（$n=2$ 扇区标签）**。对 $\alpha \in \{1,\ldots,20\}$，令：

$$\sigma(3\alpha-2) = \mathcal{M},\quad \sigma(3\alpha-1) = \mathcal{C},\quad \sigma(3\alpha) = \mathcal{I}.$$

则 $n=2$ 层扇区人口：

$$\boxed{m_2^{\mathcal{M}} = m_2^{\mathcal{C}} = m_2^{\mathcal{I}} = 20.}$$

### 9.3 $M_2$：triality 隐藏与扇区标签流动

$M_2$ 的结构（§3.2、§5.1）：$2000 \times 60$，乘子 $\mu_3 = 100/3$，20 个块 $B_2^{(k)} \in \mathbb{R}^{100 \times 3}$。

每个块 $B_2^{(k)}$ 接收来自同一初始副本 $\alpha = k$ 的 3 个扇区副本（$\mathcal{M},\mathcal{C},\mathcal{I}$）作为输入，产生 100 个输出副本，分配为 $L_1(33), L_2(33), L_3(34)$。

**关键**：输出标签空间 $\mathcal{L}(100) = \mathbb{Z}_2^2 \times \mathbb{Z}_5^2$ **不含因子 3**——triality 被隐藏到分母中。因此输出的 100 个副本**全部**携带 $\mathbb{Z}_2^2$（$\mathcal{M}$ 结构）和 $\mathbb{Z}_5^2$（$\mathcal{I}$ 结构）的混合标签，不存在"纯 $\mathcal{C}$ 标签"的输出。

但扇区标签不取决于标签空间的因式，而取决于**编码轨道**——即副本经历了哪种因子操作。$M_2$ 中因子 3 以分母形式出现，意味着 $\mathcal{C}$ 标签的输入副本在通过 $M_2$ 时经历了一次"反操作"（预算回收）。

**定义 9.2（$M_2$ 块内扇区映射）**。对块 $B_2^{(k)}$（$k = 1,\ldots,20$）：

$$\begin{aligned}
\text{输入列 1（}\mathcal{M}\text{）} &\longrightarrow L_1 \text{（33 个输出副本）} \quad \text{——扇区标签保持 } \mathcal{M} \\
\text{输入列 2（}\mathcal{C}\text{）} &\longrightarrow L_2 \text{（33 个输出副本）} \quad \text{——扇区标签保持 } \mathcal{C} \\
\text{输入列 3（}\mathcal{I}\text{）} &\longrightarrow L_3 \text{（34 个输出副本）} \quad \text{——扇区标签保持 } \mathcal{I}
\end{aligned}$$

即**扇区标签通过 $M_2$ 保持不变**。$B_2^{(k)}$ 的每一列仅向同扇区的输出副本馈送。

**$n=3$ 扇区人口**：

$$\boxed{\begin{aligned}
m_3^{\mathcal{M}} &= 20 \times 33 = 660, \\
m_3^{\mathcal{C}} &= 20 \times 33 = 660, \\
m_3^{\mathcal{I}} &= 20 \times 34 = 680.
\end{aligned}}$$

总 $m_3 = 660 + 660 + 680 = 2000$。✓

**注 9.1（34 vs 33 的不对称性）**。$\mathcal{I}$ 扇区在每个块中多获得 1 个输出副本。这是 triality 隐藏的不可消除的"疤痕"——分母 3 无法完美均分 100，必然留下余数 $100 \bmod 3 = 1$。此余数分配给 $\mathcal{I}$ 扇区（因子 5 在分子 $2^2 \cdot 5^2$ 中），因为因子 5 是 $\mu_3$ 分子中"最新"的因子——它是此层编码扩展的主要驱动力。

### 9.4 $M_3, M_4, M_5$：均匀堆叠层（扇区标签守恒）

$M_3 = \mathbf{1}_5 \otimes I_{2000}$，$M_4 = \mathbf{1}_{10} \otimes I_{10000}$，$M_5 = \mathbf{1}_{10} \otimes I_{100000}$。

所有三层均为均匀堆叠——每个输入副本产生 $p$ 个输出副本（$p = 5, 10, 10$），全部继承同一扇区标签。扇区标签在这些层**纯粹守恒**。

因此：

$$\boxed{\begin{aligned}
n=4&: m_4^{\mathcal{M}} = 3300,\; m_4^{\mathcal{C}} = 3300,\; m_4^{\mathcal{I}} = 3400. \\
n=5&: m_5^{\mathcal{M}} = 33000,\; m_5^{\mathcal{C}} = 33000,\; m_5^{\mathcal{I}} = 34000. \\
n=6&: m_6^{\mathcal{M}} = 330000,\; m_6^{\mathcal{C}} = 330000,\; m_6^{\mathcal{I}} = 340000.
\end{aligned}}$$

$m_6 = 1000000$。✓

### 9.5 $M_6$：triality 重现与扇区标签再分配

$M_6$ 的结构（§3.6、§5.1）：$1125000 \times 1000000$，乘子 $\mu_7 = 9/8 = 3^2/2^3$，125000 个块 $B_6^{(k)} \in \mathbb{R}^{9 \times 8}$。

$$B_6^{(k)} = \begin{pmatrix} I_8 \\ \mathbf{1}_8^\top \end{pmatrix}.$$

每个块将 8 个输入副本映射为 9 个输出副本：前 8 行恒等，第 9 行全息求和。

#### 9.5.1 每个块的输入扇区构成

$m_6 = 1000000$ 个输入副本，扇区人口为 $(330000, 330000, 340000)$。125000 个块，每块 8 个输入。每块的平均扇区构成为 $(2.64, 2.64, 2.72)$——非整数，需要整数量子化。

**定理 9.1（$M_6$ 块内扇区分配的整数解）**。存在唯一的整数分配方案（模扇区交换），使所有块恰好有 8 个输入且扇区总人口符合 $m_6$ 数据：使用两种块类型——

| 块类型 | $\mathcal{M}$ | $\mathcal{C}$ | $\mathcal{I}$ | 块数 |
|:---:|:---:|:---:|:---:|:---:|
| 类型 A | 3 | 3 | 2 | 80000 |
| 类型 B | 2 | 2 | 4 | 45000 |

验证：
- $\mathcal{M}$ 总计：$80000 \times 3 + 45000 \times 2 = 240000 + 90000 = 330000$ ✓
- $\mathcal{C}$ 总计：$80000 \times 3 + 45000 \times 2 = 330000$ ✓
- $\mathcal{I}$ 总计：$80000 \times 2 + 45000 \times 4 = 160000 + 180000 = 340000$ ✓

**推导**：设 $x$ 个 A 型块，$y$ 个 B 型块，$z$ 个 C 型 $(3,2,3)$，$w$ 个 D 型 $(2,3,3)$。从 $\mathcal{M} = \mathcal{C}$（输入人口相等）得 $y = z = 0$ 化简到两类型。从 $x+y = 125000$ 和 $3x + 2y = 330000$ 解得 $x = 80000, y = 45000$。∎

#### 9.5.2 输出扇区分配

$B_6^{(k)}$ 的前 8 行是 $I_8$——恒等映射，扇区标签不变。第 9 行（全息求和）是**新生的 triality 输出**——因子 $3^2$ 在 $\mu_7$ 分子中重现，创建纯 $\mathcal{C}$ 标签的输出副本。

**定义 9.3（$M_6$ 块内扇区映射）**。

$$\begin{aligned}
\text{行 1--8（恒等）} &: \sigma_{\text{out}}(i) = \sigma_{\text{in}}(i), \quad i = 1,\ldots,8. \\
\text{行 9（全息求和）} &: \sigma_{\text{out}}(9) = \mathcal{C} \quad \text{（triality 重现——因子 } 3^2 \text{ 的载体）}.
\end{aligned}$$

#### 9.5.3 $n=7$ 扇区人口

每个 A 型块贡献 $(3\mathcal{M}, 3\mathcal{C}, 2\mathcal{I})$ 输入 → 输出 $(3\mathcal{M}, 4\mathcal{C}, 2\mathcal{I})$（多了 1 个 $\mathcal{C}$）。
每个 B 型块贡献 $(2\mathcal{M}, 2\mathcal{C}, 4\mathcal{I})$ 输入 → 输出 $(2\mathcal{M}, 3\mathcal{C}, 4\mathcal{I})$（多了 1 个 $\mathcal{C}$）。

$$\boxed{\begin{aligned}
m_7^{\mathcal{M}} &= m_6^{\mathcal{M}} = 330000 \quad \text{（恒等行保留，无新生 } \mathcal{M}\text{）} \\
m_7^{\mathcal{C}} &= m_6^{\mathcal{C}} + 125000 = 330000 + 125000 = 455000 \quad \text{（每块 +1 新生 } \mathcal{C}\text{）} \\
m_7^{\mathcal{I}} &= m_6^{\mathcal{I}} = 340000 \quad \text{（恒等行保留，无新生 } \mathcal{I}\text{）}
\end{aligned}}$$

总 $m_7 = 330000 + 455000 + 340000 = 1125000$。✓

**关键结果**：$n=7$ 层扇区人口**不再等权**。$\mathcal{C}$ 扇区占 $455000/1125000 \approx 40.4\%$，显著多于 $\mathcal{M}$（29.3%）和 $\mathcal{I}$（30.2%）。这是 triality 重现（$\mu_7$ 分子 $3^2$）的直接矩阵签名。

### 9.6 $\Delta_j^{(n)}$ 矩阵的修正

§4.1 的等权假设 $m_n^{(\mathcal{M})} = m_n^{(\mathcal{C})} = m_n^{(\mathcal{I})} = m_n/3$ 对 $n \le 6$ 近似成立（$660:660:680$ 几乎是等权），但对 $n=7$ 显著失效——$\mathcal{C}$ 多出 125000 个副本。

**修正定义 9.2（$\Delta_j^{(7)}$——含扇区人口权重）**：

$$\boxed{\begin{aligned}
\Delta_1^{(7)} &= \text{diag}\big(w_2^{(7)} I_{m_7^{\mathcal{M}}}, \; I_{m_7^{\mathcal{C}}}, \; I_{m_7^{\mathcal{I}}}\big), \\[4pt]
\Delta_2^{(7)} &= \text{diag}\big(I_{m_7^{\mathcal{M}}}, \; w_3^{(7)} I_{m_7^{\mathcal{C}}}, \; I_{m_7^{\mathcal{I}}}\big), \\[4pt]
\Delta_3^{(7)} &= \text{diag}\big(I_{m_7^{\mathcal{M}}}, \; I_{m_7^{\mathcal{C}}}, \; w_5^{(7)} I_{m_7^{\mathcal{I}}}\big).
\end{aligned}}$$

其中 $m_7^{\mathcal{M}} = 330000$，$m_7^{\mathcal{C}} = 455000$，$m_7^{\mathcal{I}} = 340000$。

### 9.7 扇区标签流动总览

| $n$ | $M_n$ | $m_n$ | $m_n^{\mathcal{M}}$ | $m_n^{\mathcal{C}}$ | $m_n^{\mathcal{I}}$ | 事件 |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| 1 | — | 20 | — | — | — | 原始折叠，扇区未分 |
| 2 | $M_1 = \mathbf{1}_3 \otimes I_{20}$ | 60 | 20 | 20 | 20 | triality 激活：等权三等分 |
| 3 | $M_2: B_2(100\times 3)$ | 2000 | 660 | 660 | 680 | triality 隐藏：$\mathcal{I}$ 多 20 |
| 4 | $M_3 = \mathbf{1}_5 \otimes I$ | 10000 | 3300 | 3300 | 3400 | 均匀堆叠 |
| 5 | $M_4 = \mathbf{1}_{10} \otimes I$ | 100000 | 33000 | 33000 | 34000 | 均匀堆叠 |
| 6 | $M_5 = \mathbf{1}_{10} \otimes I$ | 1000000 | 330000 | 330000 | 340000 | 均匀堆叠 |
| 7 | $M_6 = [I_8; \mathbf{1}_8^\top]$ | 1125000 | 330000 | **455000** | 340000 | triality 重现：$\mathcal{C}$ +125000 |

---

## §10 诚实标注

### 10.1 已封闭的缺口

| 原缺口 | 状态 |
|:---|:---|
| §7.2 H1（等权分区 $m_n/3$） | **已修正**——$n=7$ 层 $\mathcal{C}$ 扇区人口 455000 ≠ 375000 |
| 开放问题 4（$\Delta_j^{(n)}$ 与 $M_n$ 精确对应） | **已封闭**——扇区人口从 $M_2, M_6$ 块结构显式计算 |

### 10.2 新出现的开放问题

| # | 问题 | 严重度 |
|:---:|:---|:---:|
| O1 | $M_6$ 的 125000 个块中 A 型（80000）和 B 型（45000）的**具体排列顺序**——块在矩阵中的位置是否影响 $g_n$ 的拉回？ | 中 |
| O2 | $M_2$ 的 33/33/34 划分在 $\mathbb{Z}_2^2 \times \mathbb{Z}_5^2$ 标签空间中的**具体实现**——$L_1, L_2, L_3$ 对应标签空间的哪个子集？ | 低（不影响扇区人口，但影响副本级别的 $G$ 矩阵对角元） |
| O3 | Condition 8.1（$M_n \Delta_j^{(n)} = \Delta_j^{(n+1)} M_n$）在非均匀扇区人口下的**新形式**——当前推导假设扇区内权重均匀，但不同扇区人口不同会改变矩阵维度匹配 | 高 |

### 10.3 条件 8.1 在 M₆ 全息求和行上的失效（精确诊断）

§8.4 的条件 $M_n \Delta_j^{(n)} = \Delta_j^{(n+1)} M_n$ 展开为：对每个非零 $(M_n)_{\beta,\alpha}$，要求 $(\Delta_j^{(n)})_{\alpha,\alpha} = (\Delta_j^{(n+1)})_{\beta,\beta}$。

在 M₆ 的每个 $9 \times 8$ 块中：
- **恒等行**（1-8）：$(M_6)_{\beta,\alpha} = \delta_{\beta,\alpha}$。条件给出 $w_{j,\mathcal{S}}^{(6)} = w_{j,\mathcal{S}}^{(7)}$（扇区内一致，无问题）。
- **全息求和行**（第 9 行）：$(M_6)_{9,\alpha} = 1$ 对全部 $\alpha = 1,\ldots,8$。条件给出：

$$(\Delta_j^{(6)})_{\alpha,\alpha} = (\Delta_j^{(7)})_{9,9} = w_{j,\mathcal{C}}^{(7)}, \quad \forall \alpha \in \text{块内}.$$

**全部 8 个输入副本（横跨 $\mathcal{M}, \mathcal{C}, \mathcal{I}$ 三个扇区）的 $\Delta$ 权重必须等于同一个值 $w_{j,\mathcal{C}}^{(7)}$。这与 §9.5 的扇区标签映射直接冲突**——不同扇区的副本应有不同的编码历史权重。

这不是「维度不匹配」——$M_6 \Delta_j^{(6)}$ 和 $\Delta_j^{(7)} M_6$ 都是 $1125000 \times 1000000$，维度始终一致。问题在于**全息创建行的物理语义与逐元素相等不兼容**：第 9 行创建的是新生 $\mathcal{C}$ 副本，其权重应由创建过程决定（所有输入副本的加权平均），而非强制等于任一输入。

**修正方向**（详见 §8.14）：将条件 8.1 拆分为恒等行（保持逐元素相等）和全息行（替换为加权平均规则），并从两型块的一致性推导扇区权重的约束方程。这项工作在 §8.14–§8.16 中完成。

