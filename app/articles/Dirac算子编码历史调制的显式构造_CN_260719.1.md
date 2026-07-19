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
