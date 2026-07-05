# Mathematical Theory of Tenfang Geometric Space

## An Axiomatic Framework for Constrained Product Spheres and Spectral Geometry

**Ouyang Guobin**  
*Guangdong, China*

---

**Version: 260707.7**

---

**Abstract**

This paper establishes a rigorous axiomatic mathematical framework — the Tenfang Geometric Space — integrating the topological analysis of the excited-state parameter space, the spectral rigidity of constrained product sphere classes, the holographic screen encoding structure on the trisected tangent bundle, and the spectral convergence of discrete graph approximations into a logically self-consistent pure mathematical theory. Based on three fundamental axioms and three interlocking constants, this paper rigorously proves:

1. The range theorem and existence theorem for the abstract geometric quantity $S$;
2. The spectral rigidity theorem for the 9-dimensional constrained product sphere $M(a)=S^3(a)\times S^3(a/\sqrt{\Lambda})\times S^3(a/\sqrt{\Lambda k_0})$;
3. The six-term action range $[24,+\infty)$ and strict convexity of the trisected tangent bundle holographic screen;
4. The canonical form of the scale-reciprocal self-dual bridge function and the explicit spectrum-projection mapping;
5. The Berezin–Toeplitz quantization layer of the holographic screen and the algebraic origin of the magic number sequence $2,8,18,32,50,72,98$;
6. Spectral convergence of discrete graph approximations and information field degeneration;
7. The extended interlocking structure of the Nine Primes, incorporating the rigorous results of the tool layers into a unified logical network.

This paper establishes a pure mathematical bridge between noncommutative spectral geometry and constrained Riemannian geometry, with all physical mappings explicitly labeled as conditional propositions.

**Keywords:** axiomatic framework; spectral rigidity; product spheres; holographic screen; symplectic geometry; deformation quantization; graph Laplacian; heat kernel; Bott periodicity; spectral action

---

## Chapter 1 Introduction

### 1.1 Theoretical Background and Motivation

This paper constructs a mathematical framework from geometric axioms to physical constant mappings. Within this framework, the topological properties of the excited-state parameter space, the spectral rigidity of high-dimensional product manifolds, the encoding structure of two-dimensional holographic screens, and the spectral convergence of discrete approximations are integrated into a logically self-consistent pure mathematical system.

This paper adopts the following axiomatic strategy:

**Three Fundamental Axioms**:
- **Axiom 1 (Circle Topology Axiom)**: The excited-state parameter space $D$ is obtained from $S^1$ by removing the vacuum point $p_0$ and the degenerate point $p_*$;
- **Axiom 2 (Boundary Limit Axiom)**: The geometric quantity $S$ is continuous on $D$, satisfying the vacuum limit $S\to 0$ and the degenerate limit $S\to+\infty$;
- **Axiom 3 (Holographic Screen Encoding Condition)**: On each fiber of the trisected tangent bundle $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$, there exists a 2-dimensional oriented subspace $\Sigma$ (holographic screen), with sector projection intensity angles satisfying $\theta_1+\theta_2+\theta_3=90^\circ$.

**Three Interlocking Constants**: $\Lambda=\Lambda(S_3)=3$ (the trisection proportionality parameter, the number of conjugacy classes of $S_3$, rigorously computed in Proposition 3.0), $k_0=k_0(S_3)=2$ (the dyadic compactness constant, the index of the maximal normal subgroup of $S_3$, rigorously computed in Proposition 3.0), $\ell_0>0$ (the scale constant, locked by the spectral unit selection theorem and the ground state condition).

### 1.2 Role and Positioning of the Tool Layer Framework

This paper integrates three mathematical tool layers, each providing rigorous foundations for the core framework from different dimensions:

- **Chapter 6** ($S^2$ Deformation Quantization): Provides rigorous foundations for deformation quantization on the holographic screen $\Sigma\cong S^2$ and the magic number sequence;
- **Chapter 7** ($M(a)$ Spectral Rigidity and Dirac Index): Provides rigorous foundations for the constrained isospectral rigidity of $M(a)$ and the classification of Laplace low-energy modes, and provides rigorous geometric theorems for the locking of normal bundle curvature and Hessian soft/hard modes;
- **Chapter 8** (Discrete Graph Approximation and Spectral Convergence): Provides rigorous foundations for the spectral convergence and heat kernel decay of discrete graph approximations of the holographic screen.

### 1.3 Main Results and Structure

This paper establishes a complete mathematical framework based on three axioms:

1. **Axiom 1 and Axiom 2** (Chapter 2): The circle topology and boundary limits of the excited-state parameter space, yielding the abstract geometric quantity range $(0,+\infty)$ and the existence theorem;
2. **Chapter 3** (Constrained Product Spheres and Spectral Rigidity): The moduli space parametrization and isometry class uniqueness of $M(a)=S^3(a)\times S^3(a/\sqrt{\Lambda})\times S^3(a/\sqrt{\Lambda k_0})$;
3. **Holographic Screen Encoding Condition** (Chapter 4): The equal-proportion projection ($\Lambda=3$ locks each at $30^\circ$) from the three sectors of the trisected tangent bundle to the 2-dimensional holographic screen, yielding $\theta_1+\theta_2+\theta_3=90^\circ$, the six-term action range $[24,+\infty)$, with the minimum $24$ exactly realized at the symmetric point $30^\circ$, and $S$ being strictly convex on $D_\theta$;
4. **Chapter 5** (Unification of the Tenfang Geometric Space): Range compatibility, canonical bridge function form and normalization condition (constructive concept), explicit spectrum-projection mapping, and bridge function canonical form (constructive concept);
5. **Chapter 6** (Deformation Quantization of the Holographic Screen): The algebraic origin of the magic number sequence $2,8,18,32,50,72,98$ and the Bott periodicity cutoff $N_{\text{eff}}=7$;
6. **Chapter 7** (Higher-Dimensional Spectral Geometry): Dirac index, spectral action algebraic relations, normal bundle curvature–Hessian locking;
7. **Chapter 8** (Discrete Approximation and Information Field Degeneration): Graph Laplacian spectral convergence, heat kernel decay, Weyl's law;
8. **Chapter 9** (Nine Primes Interlocking): Three axioms, three interlocking constants, and three tool layer theorems form a mutually locked logical network;
9. **Chapter 10** (Overdetermined Locking and Bootstrap Closure): The construction of the overdetermined system and the uniqueness proof of the interlocking constants, along with the complete formalization of the dependency theorem chain.

### 1.4 Theoretical Boundaries and Notation System

This paper adopts the following strict classification of propositions into three categories:

- **Mathematical Theorems (Theorem X.Y)**: Rigorously derived from Axioms 1–3 and standard mathematical tools, independent of any physical experience or experimental data. Their truth values are guaranteed by the axiomatic system and logical rules.
- **Conditional Propositions (Proposition X.Y* or Theorem X.Y*)**: Hold under specific geometric-physical correspondence assumptions (e.g., "the gauge field $F_A$ is identified with the $U(1)$ sub-component of the normal bundle Spin connection"). Their mathematical derivations are rigorous, but the geometric-physical identification belongs to the explicit conditions of the framework.
- **Physical Mappings (Mapping X.Y or Remark [Physical Mapping])**: Relate mathematical outputs to experimental constants (e.g., $\alpha^{-1}\approx 137.035999084$). Their numerical agreement is an empirical observation and does not constitute a mathematical proof of the axiomatic system.

Unified notation: Physical mappings and conditional assumptions are all explicitly labeled with footnotes or `remark` environments to avoid confusing the reader between mathematical necessity and physical correspondence.

---

## Chapter 2 Axiomatization of the Excited-State Parameter Space

### 2.1 Axiom 1 (Topology of the Parameter Space)

**Axiom 1 (Circle Topology Axiom)** The excited-state parameter space $D$ is obtained from the one-dimensional compact connected manifold $S^1$ (the circle) by removing two distinct points $p_0$ and $p_*$:

$$D = S^1 \setminus \{p_0, p_*\}, \qquad p_0 \neq p_*$$

The two removed points are respectively called the **vacuum point** ($p_0$) and the **degenerate point** ($p_*$). Consequently, $D$ consists of two connected components:

$$D_+ \cong (0,1), \qquad D_- \cong (0,1)$$

Each component is homeomorphic to an open interval. The parameter $x \in D_\pm$ labels excited states.

**Lemma 2.1 (Topological Structure of the Components)** Let $S^1$ be the standard unit circle $\{e^{i\phi} \mid \phi \in [0,2\pi)\}$. Removing two points $p_0=e^{i\phi_0}$ and $p_*=e^{i\phi_*}$ (assume without loss of generality $0\leq \phi_0 < \phi_* < 2\pi$), then $S^1\setminus\{p_0,p_*\}$ has exactly two connected components:
$$D_+ = \{e^{i\phi} \mid \phi_0 < \phi < \phi_*\}, \quad D_- = \{e^{i\phi} \mid \phi_* < \phi < \phi_0+2\pi\}.$$
Each component, as a subspace of $S^1$, is homeomorphic to the open interval $(0,1)$.

*Proof.* Consider the standard covering map $\pi: \mathbb{R} \to S^1$, $\pi(\phi)=e^{i\phi}$. On $\mathbb{R}$, $\pi^{-1}(S^1\setminus\{p_0,p_*\}) = \mathbb{R}\setminus\{\phi_0+2k\pi, \phi_*+2k\pi \mid k\in\mathbb{Z}\}$. Each connected component of this set is an open interval $(\phi_0+2k\pi, \phi_*+2k\pi)$ or $(\phi_*+2k\pi, \phi_0+2(k+1)\pi)$. Since the restriction of $\pi$ to an interval of length $2\pi$ is a homeomorphism, the images of these open intervals in $S^1$ are precisely $D_+$ and $D_-$. Each open interval is homeomorphic to $(0,1)$, hence $D_\pm \cong (0,1)$. $\square$

### 2.2 Axiom 2 (Analytic Properties of the Geometric Quantity)

**Axiom 2 (Boundary Limit Axiom)** On the parameter space $D$ there exists a geometric quantity $S: D \to (0,+\infty)$, satisfying:

1. **Continuity**: $S$ is continuous on each connected component $D_\pm$;
2. **Vacuum Limit**: As $x$ approaches $p_0$ along either component, $\lim_{x \to p_0} S(x) = 0$;
3. **Degenerate Limit**: As $x$ approaches $p_*$ along either component, $\lim_{x \to p_*} S(x) = +\infty$.

**Remark 2.1** Axiom 2 does not require $S$ to have the same functional expression on $D_+$ and $D_-$, nor does it require $S$ to be continuous on all of $D$ ($p_0$ and $p_*$ are not in $D$). Thus $S$ can be different functions on the two independent components, as long as each satisfies the boundary conditions.

### 2.3 Range Theorem

**Theorem 2.1** (Range) Under Axioms 1 and 2, the range of $S$ on each connected component $D_\pm$ is $S(D_\pm) = (0, +\infty)$.

*Proof.* By Axiom 1, $D_\pm \cong (0,1)$ is connected. By Axiom 2, $S$ is continuous on $D_\pm$, so the image $S(D_\pm)$ is a connected subset of $\mathbb{R}$, i.e., an interval. By the vacuum limit, $\inf S(D_\pm) = 0$; by the degenerate limit, $\sup S(D_\pm) = +\infty$. Since $p_0, p_* \notin D$, the endpoints $0$ and $+\infty$ are not attained. Hence $S(D_\pm) = (0, +\infty)$. $\square$

**Detailed Explanation:** The connectedness argument can be further elaborated as follows. Let $D_+ \cong (0,1)$, $S: D_+ \to \mathbb{R}$ continuous. Suppose $S(D_+)$ is not an interval, then there exist $\alpha < \beta < \gamma$ such that $\alpha, \gamma \in S(D_+)$ but $\beta \notin S(D_+)$. Let $U = S^{-1}((-\infty, \beta))$ and $V = S^{-1}((\beta, +\infty))$, then $U,V$ are disjoint open sets in $D_+$, and $U\cup V = D_+$, contradicting the connectedness of $D_+$. Hence $S(D_+)$ must be an interval. Combined with the boundary limits, this interval must be $(0,+\infty)$.

### 2.4 Existence Theorem and Strict Monotonicity Assumption

**Theorem 2.2** (Existence) For any given positive number $S_0 > 0$, on each component $D_+$ and $D_-$ there exists at least one excited state $x_+ \in D_+$ and $x_- \in D_-$ such that $S(x_+) = S(x_-) = S_0$.

*Proof.* By Theorem 2.1, $S(D_\pm) = (0, +\infty)$. For any $S_0 > 0$, clearly $S_0 \in (0, +\infty)$. Hence $S^{-1}(S_0) \cap D_\pm \neq \varnothing$. $\square$

**Definition 2.1' (Strict Monotonicity Assumption)** If $S$ is strictly monotonic on $D_\pm$, then for any $S_0>0$, the points $x_+$ and $x_-$ in Theorem 2.2 are uniquely determined. Strict monotonicity is **not** a theorem derived from Axioms 1–2, but rather a **constructive assumption** of the framework. Its introduction is equivalent to requiring that $S$ constitutes a global coordinate function on $D_\pm$.

*Proof.* A strictly monotonic continuous function is injective, hence the preimage is unique. $\square$

---

## Chapter 3 Constrained Product Spheres and Spectral Rigidity

### 3.0 Group-Theoretic Origin of the Interlocking Functions

**Lemma 3.0 (Rigidity of the Trisected Tangent Bundle Permutation Group)** Let $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$ be the trisected tangent bundle, and let $G$ be its sector permutation symmetry group. If $G$ acts faithfully and transitively on the three sectors, and contains the transposition of any two sectors, then $G \cong S_3$, and $S_3$ is the unique finite group satisfying this condition.

*Proof.* The faithful permutation group of three objects must be a subgroup of $S_3$. Transitivity requires an orbit size of 3, so $|G| \geq 3$. The transitive subgroups of $S_3$ are only $A_3 \cong \mathbb{Z}_3$ (cyclic) and $S_3$ itself. If transpositions (odd permutations) are required, $A_3$ is insufficient, and the only possibility is $S_3$. $\square$

**Definition 3.0 (Interlocking Function and Compactness Function)** Let $G$ be a finite group. Define:
- **Interlocking function** $\Lambda(G) := |\text{Conj}(G)|$ (the number of conjugacy classes, equal by the fundamental theorem of representation theory to the number of irreducible complex representations of $G$);
- **Compactness function** $k_0(G) := [G : N_{\max}]$ (the index of the maximal normal subgroup).

**Proposition 3.0** For the permutation symmetry group $G = S_3$ of the trisected tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$:
$$\Lambda(S_3) = 3, \quad k_0(S_3) = 2.$$

*Proof.* The conjugacy class decomposition of $S_3$ is: identity $\{e\}$ (1 element), transpositions $\{(12),(13),(23)\}$ (3 elements), 3-cycles $\{(123),(132)\}$ (2 elements), totaling 3 conjugacy classes, hence $\Lambda(S_3)=|\text{Conj}(S_3)|=3$.

The normal subgroups of $S_3$ are only $\{e\}$ and $A_3 \cong \mathbb{Z}_3$ (the alternating subgroup). The maximal normal subgroup is $A_3$, whose index is $[S_3 : A_3] = 6/3 = 2$, hence $k_0(S_3)=2$. $\square$

**Remark 3.0** By Lemma 3.0, $S_3$ is the unique choice for the permutation symmetry group of the trisected tangent bundle. The interlocking constants $\Lambda=3$ and $k_0=2$ are not freely chosen parameters, but the inevitable values of group-theoretic functions evaluated on $S_3$. If the trisected tangent bundle possessed $S_4$ permutation symmetry (a four-sector structure), then $\Lambda(S_4)=5$, $k_0(S_4)=2$, which would be an entirely different theory from Tenfang geometry. The reason Tenfang geometry locks in $\Lambda=3$, $k_0=2$ is that its group structure is $S_3$ (three sectors), and Lemma 3.0 has proven the uniqueness of this group choice.

**Theorem 3.0' (Rigidity of Trisected Tangent Bundle Sector Permutations)** Let $M = S^3 \times S^3 \times S^3$ be equipped with the product metric, and suppose there exists a tangent bundle decomposition $TM = \mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ such that the three sectors are completely equivalent at the metric level (i.e., any permutation induces an isometric automorphism). Then:
1. The sector permutation group $G$ of this decomposition must contain all two-sector transpositions;
2. The finite group satisfying (1) is uniquely isomorphic to $S_3$.

Furthermore, $\Lambda(G)=|\text{Conj}(S_3)|=3$, $k_0(G)=[S_3:A_3]=2$ are the inevitable outputs of group-theoretic functions.

*Proof.* (1) If the three sectors are metrically equivalent, then any transposition (e.g., $\mathcal{M}\leftrightarrow\mathcal{C}$) preserves the product metric and hence induces an isometric automorphism. Therefore all two-sector transpositions belong to $G$.

(2) By Lemma 3.0, a transitive permutation group containing transpositions can only be $S_3$. Hence $G\cong S_3$ is not an artificial choice but an inevitable consequence of non-trivial permutations under the trisected equivalence structure. $\square$

### 3.1 Definitions and Assumptions

**Definition 3.1** (Constrained Product Sphere) Let $a > 0$ be the global scale factor. By Theorem 3.0' and Proposition 3.0, the group-theoretic function outputs of the trisected tangent bundle permutation group $S_3$ are:
$$\Lambda = \Lambda(S_3) = 3 \quad \text{(trisection proportionality parameter)}, \quad k_0 = k_0(S_3) = 2 \quad \text{(dyadic compactness constant)}, \quad \ell_0 > 0 \quad \text{(scale constant, locked by the spectral unit selection theorem and the ground state condition)}.$$

The 9-dimensional closed manifold

$$M(a) = S^3(a) \times S^3(a/\sqrt{3}) \times S^3(a/\sqrt{6})$$

equipped with the product metric $g = g_a \oplus g_{a/\sqrt{3}} \oplus g_{a/\sqrt{6}}$ is called a **Constrained Product Sphere** (CPS). Write

$$b = \frac{a}{\sqrt{3}}, \quad c = \frac{a}{\sqrt{6}}.$$

The scale ordering $a > b > c$ holds strictly ($1 > 1/\sqrt{3} > 1/\sqrt{6}$).

**Remark 3.1** (Triviality of the Tangent Bundle) Since $S^3$, as the Lie group $SU(2)$, is parallelizable, its tangent bundle $TS^3$ is trivial. The tangent bundle of a product manifold is the direct sum of the tangent bundles of the factors, hence $TM(a)$ is automatically trivial. Thus the triviality of the tangent bundle holds automatically in this class and need not be listed as an additional hypothesis.

**Remark 3.2** (Properties of the Interlocking Constants) The constants $\Lambda=3$ and $k_0=2$ are directly computed from the $S_3$ group-theoretic structure by Theorem 3.0' and Proposition 3.0; $\ell_0$ is locked by the self-consistent output of the Nine Primes interlocking network. None of the three is an artificially chosen free parameter: $\Lambda$ and $k_0$ are the inevitable values of the group-theoretic functions $|\text{Conj}(S_3)|$ and $[S_3:A_3]$; $\ell_0$ is uniquely determined by the joint constraints of the spectral separation condition, heat kernel coefficient ratios, information hierarchy nesting, and magic number cutoff (see Chapters 9–10). $\ell_0$, as a positive real parameter, is locked by the spectral unit selection theorem and the ground state condition $S_{\min}=24$, providing a numerical anchor for the spectrum-projection bridge, but does not participate in the one-dimensional parametrization of the moduli space.

### 3.2 Parametrization of the Moduli Space

**Theorem 3.1** (Parametrization of the Moduli Space) Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0' and Proposition 3.0 are locked, the moduli space of the **constrained product sphere class** $\{M(a)\}_{a>0}$ (manifolds in Definition 3.1 equipped with the standard product metric and satisfying the proportionality constraints $b=a/\sqrt{\Lambda}, c=a/\sqrt{\Lambda k_0}$) is homeomorphic to the open interval $(0, \infty)$, where $a$ is the unique continuous degree of freedom (global scale factor). Different $a$ correspond to different isometry classes.

**Theorem 3.1' (First Eigenvalue as a Coordinate)** Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0' and Proposition 3.0 are locked, the spectral map
$$\sigma_1: (0,\infty) \to (0,\infty), \quad a \mapsto \lambda_1^\Delta(a) = \frac{3}{a^2}$$
is a diffeomorphism. Hence, the first non-zero Laplace eigenvalue $\lambda_1^\Delta$ itself constitutes a **global coordinate** for the moduli space $\{M(a)\}_{a>0}$ of the constrained product sphere class, and the spectral signature $(1,\ 8/3,\ \Lambda)$ is independent of $a$.

*Proof.* $\sigma_1$ is continuous, strictly monotonically decreasing, with $\lim_{a\to 0^+}\sigma_1(a)=+\infty$ and $\lim_{a\to+\infty}\sigma_1(a)=0$. Thus $\sigma_1$ is a homeomorphism $(0,\infty)\to(0,\infty)$; moreover, since $\sigma_1'(a)=-6/a^3\neq 0$, the inverse map is smooth, hence it is a diffeomorphism. $\square$

**Remark 3.1' (Status of the Defined Class)** This theorem studies the **defined class** $\{M(a)\}$ — i.e., the subset of product spheres satisfying the specific proportionality constraints of Definition 3.1 — rather than "all manifolds diffeomorphic to $S^3\times S^3\times S^3$ whose first three Laplace eigenvalues satisfy the spectral signature." The moduli space of the latter (more general isospectral class) may be larger, and this paper makes no claim to completely classify it.

*Proof.* By Definition 3.1, the submetrics are spherical, characterized by radii $(a,b,c)$, and the ratios of $b$ and $c$ to $a$ are locked by $\Lambda$ and $k_0$. Hence, with $(k_0, \Lambda, \ell_0)$ fixed, the unique continuous degree of freedom is the global scale $a$. Since $S^3$ is parallelizable, $TM(a)$ is automatically trivial, and the topology is uniquely determined. Thus the moduli space is fully parametrized by $a \in (0, \infty)$, with different $a$ giving different curvature radii and hence different isometry classes. $\square$

**Detailed Argument:** The rigor of distinguishing isometry classes can be further explained. Let $a \neq a'$. Then the first factor $S^3(a)$ and $S^3(a')$ have different radii. Since the diameter of $S^3(R)$ is $\pi R$ and its volume is $2\pi^2 R^3$, isometric manifolds must have equal diameters and volumes. If $M(a)$ and $M(a')$ were isometric, their diameters and volumes would have to be equal. For the product metric, the diameter formula is
$$\text{diam}(M(a)) = \pi\sqrt{a^2+b^2+c^2} = \pi a\sqrt{1+\frac{1}{\Lambda}+\frac{1}{\Lambda k_0}},$$
where $b=a/\sqrt{\Lambda}$ and $c=a/\sqrt{\Lambda k_0}$. Since $\Lambda$ and $k_0$ are interlocking constants, $\sqrt{1+1/\Lambda+1/(\Lambda k_0)}$ is a positive constant independent of $a$, so $\text{diam}(M(a))$ is a strictly monotonic function of $a$. Hence $a=a'$, and different $a$ correspond to different isometry classes.

### 3.3 Explicit Computation of Laplace Eigenvalues

**Proposition 3.1** (Spectral Separation on Product Manifolds) For the constrained product sphere $M(a)$, the full set of eigenvalues of the Laplace–Beltrami operator $\Delta_g$ is

$$\lambda_{p,q,r}^\Delta = \frac{p(p+2)}{a^2} + \frac{q(q+2)}{b^2} + \frac{r(r+2)}{c^2}, \quad p,q,r \in \mathbb{N}_0.$$

Here $p=q=r=0$ corresponds to the zero eigenvalue (constant function), and non-zero eigenvalues begin at $p+q+r \geq 1$.

*Proof.* On a product manifold, the Laplace operator separates as $\Delta_g = \Delta_1 + \Delta_2 + \Delta_3$, where $\Delta_i$ is the Laplace operator on each factor. It is known that on $S^3(R)$, the eigenvalue corresponding to the $p$-th order spherical harmonic is $p(p+2)/R^2$, so the total eigenvalue is the sum of the three. $\square$

**Supplementary Explanation:** The standard derivation of Laplace eigenvalues on $S^3(R)$ is as follows. Embed $S^3(R)$ in $\mathbb{R}^4$ as $\{x\in\mathbb{R}^4: |x|=R\}$. The restriction of a degree-$p$ homogeneous harmonic polynomial on $\mathbb{R}^4$ to $S^3(R)$ yields a spherical harmonic. From the separation of the Euclidean Laplacian into radial and angular parts, $\Delta_{\mathbb{R}^4} = \partial_r^2 + \frac{3}{r}\partial_r + \frac{1}{r^2}\Delta_{S^3}$. For a degree-$p$ homogeneous function $f(r,\theta)=r^p Y(\theta)$, $\Delta_{\mathbb{R}^4}f=0$ yields $\Delta_{S^3}Y = -p(p+2)Y$. On $S^3(R)$, the metric scaling factor is $R^2$, so the eigenvalue is $p(p+2)/R^2$.

**Proposition 3.2** (Explicit Expressions for the First Three Eigenvalues) Under the locking of the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0' and Proposition 3.0, the first three non-zero eigenvalues of $M(a)$ are:

| Mode (p,q,r) | Eigenvalue Expression | Ratio to 3/a² |
|:---|:---|:---|
| (1,0,0) | 3/a² | 1 |
| (2,0,0) | 8/a² | 8/3 ≈ 2.667 |
| (0,1,0) | 3Λ/a² = 9/a² | Λ = 3 |
| (0,0,1) | 3Λk₀/a² = 18/a² | Λk₀ = 6 |
| (1,1,0) | 3/a² + 3Λ/a² = 12/a² | Λ+1 = 4 |

*Proof.* By Proposition 3.1, the eigenvalues of the candidate modes are computed as in the table above.

Since the interlocking constant $\Lambda=3$, we have $3\Lambda/a^2 = 9/a^2 > 8/a^2$, so the $(0,1,0)$ mode is strictly larger than the $(2,0,0)$ mode. Since $k_0=2$, we have $3\Lambda k_0/a^2 = 18/a^2 > 9/a^2$, so the $(0,0,1)$ mode is strictly larger than the $(0,1,0)$ mode. Other combinations (such as $(1,0,1)$, $(0,2,0)$, etc.) have even larger numerical values. Hence the first three non-zero eigenvalues are precisely those given by the first three rows of the table above. $\square$

### 3.4 Eigenvalue Ordering and Spectral Signature

**Theorem 3.2** (Eigenvalue Ordering) For any $a > 0$ and under the locking of the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0' and Proposition 3.0, the first four non-zero eigenvalues satisfy

$$\lambda_1^\Delta = \frac{3}{a^2} < \lambda_2^\Delta = \frac{8}{a^2} < \lambda_3^\Delta = \frac{3\Lambda}{a^2} < \lambda_4^\Delta = \min\left\{\frac{3\Lambda k_0}{a^2},\ \frac{3(\Lambda+1)}{a^2}\right\}.$$

*Proof.* The candidate mode $(0,0,1)$ yields $3\Lambda k_0/a^2$, the candidate mode $(1,1,0)$ yields $3(\Lambda+1)/a^2$, and the candidate mode $(0,2,0)$ yields $8\Lambda/a^2$. Since $k_0>1$ and $\Lambda>8/3$, all three are strictly larger than $\lambda_3^\Delta=3\Lambda/a^2$. Comparing $(0,2,0)$ with $(1,1,0)$: $8\Lambda > 3(\Lambda+1)$ holds when $\Lambda>3/5$, so under $\Lambda>8/3$, $8\Lambda/a^2 > 3(\Lambda+1)/a^2$ always holds. Comparing $(0,2,0)$ with $(0,0,1)$: the relative size of $8\Lambda$ and $3\Lambda k_0$ depends on $k_0$; when $k_0>8/3$, $3\Lambda k_0 > 8\Lambda$, and when $1<k_0<8/3$, $8\Lambda > 3\Lambda k_0$. Hence the fourth eigenvalue is determined by $\min\{3\Lambda k_0, 3(\Lambda+1)\}/a^2$, and $(0,2,0)$ does not enter the first four (under $\Lambda>8/3$, it is larger than $(1,1,0)$, and only when $k_0<8/3$ might it be smaller than $(0,0,1)$, but even then it exceeds $(1,1,0)$). The remaining candidate modes (such as $(3,0,0)$, etc.) have even larger numerical values. $\square$

**Remark 3.4** Under the interlocking constants $\Lambda=3$, $k_0=2$, we have $3\Lambda k_0/a^2 = 18/a^2 > 3(\Lambda+1)/a^2 = 12/a^2$, so $\lambda_4^\Delta = 12/a^2 = 3(\Lambda+1)/a^2$. This ordering is uniquely determined by the interlocking constants.

**Corollary 3.1** (Spectral Signature) The ratios

$$\frac{\lambda_2^\Delta}{\lambda_1^\Delta} = \frac{8}{3}, \quad \frac{\lambda_3^\Delta}{\lambda_1^\Delta} = \Lambda$$

are universal constants independent of $a$ and $k_0$ (for fixed $\Lambda$), and can serve as the **spectral signature** of the constrained product sphere class. If the ratio of the first two non-zero eigenvalues of a product sphere is not $8/3$, it does not belong to this class.

### 3.5 Recovering Scale Factors from the First Three Eigenvalues

**Theorem 3.3** (Inverse Formula) Given the first three non-zero Laplace eigenvalues $\lambda_1^\Delta$, $\lambda_2^\Delta$, $\lambda_3^\Delta$ of $M(a)$, the scale factors can be uniquely recovered:

$$a = \sqrt{\frac{3}{\lambda_1^\Delta}}, \quad b = \sqrt{\frac{3}{\lambda_3^\Delta}}, \quad c = \frac{a}{\sqrt{\Lambda k_0}} = \sqrt{\frac{3}{\Lambda k_0 \cdot \lambda_1^\Delta}}.$$

**Self-Consistency Condition** A triplet of positive numbers $(\lambda_1, \lambda_2, \lambda_3)$ are the first three non-zero eigenvalues of some $M(a)$ if and only if

$$\lambda_2 = \frac{8}{3}\lambda_1 \quad \text{and} \quad \lambda_3 = \Lambda(S_3) \lambda_1 = 3\lambda_1.$$

In that case $a = \sqrt{3/\lambda_1}$.

*Proof.* By Theorem 3.2, $\lambda_1^\Delta = 3/a^2 \Rightarrow a = \sqrt{3/\lambda_1^\Delta}$; $\lambda_3^\Delta = 3/b^2 \Rightarrow b = \sqrt{3/\lambda_3^\Delta}$; by the proportionality constraint of Definition 3.1, $c = a/\sqrt{\Lambda k_0}$. The self-consistency condition follows directly from $\lambda_2^\Delta = 8/a^2$ and $\lambda_3^\Delta = 3\Lambda/a^2$. $\square$

**Lemma 3.1** (One-to-One Correspondence Between Spectral Data and Geometry) Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0' and Proposition 3.0 are locked, there exists an explicit one-to-one mapping between the first three non-zero Laplace eigenvalues and the scale factors $(a,b,c)$. Given $\lambda_1^\Delta$, $\lambda_2^\Delta$, $\lambda_3^\Delta$, one can uniquely recover $(a,b,c)$; conversely, given $(a,b,c)$, one can uniquely compute the first three eigenvalues.

### 3.6 Spectral Rigidity Theorem

**Theorem 3.4** (Spectral Rigidity of Constrained Product Spheres) Let $M(a)$ and $M(a')$ be two constrained product spheres with the same interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$. If their Laplace–Beltrami operators have the same first three non-zero eigenvalues, then $M(a)$ and $M(a')$ are isometric.

*Proof.* By Proposition 3.2, the first non-zero Laplace eigenvalue is $\lambda_1^\Delta=3/a^2$. If $M(a')$ is isospectral to $M(a)$, then $\lambda_1^{\Delta}(a')=\lambda_1^{\Delta}(a)$, i.e., $3/a'^2=3/a^2$. Since $a,a'>0$, we obtain $a'=a$. By the proportionality constraints $b=a/\sqrt{\Lambda}$, $c=a/\sqrt{\Lambda k_0}$ in Definition 3.1, the scale triplet $(a,b,c)$ is uniquely determined, so $M(a')$ and $M(a)$ are isometric. $\square$

**Remark 3.1** The origin of spectral rigidity in this theorem lies in the fact that the moduli space is parametrized by a single scale factor. Since the isometry classes of constrained product spheres satisfying Definition 3.1 with locked interlocking constants are uniquely labeled by $a$, and the first three Laplace eigenvalues (in fact the first one alone suffices) uniquely determine $a$, two manifolds sharing the same first three eigenvalues must belong to the same isometry class.

**Remark 3.2** (Completeness of the First Eigenvalue) In the one-parameter family $\{M(a)\}_{a>0}$ with locked interlocking constants, the moduli space is one-dimensional. The first non-zero eigenvalue $\lambda_1^\Delta = 3/a^2$ itself already constitutes a complete coordinate on the moduli space (bijective with $a$). The latter two of the first three eigenvalues provide self-consistency checks (they must satisfy the ratios $8/3$ and $\Lambda$), and serve as the spectral signature of the class, used to determine whether a given manifold belongs to this class.

### 3.7 Compatibility with Classical Counterexamples

**Theorem 3.5** Sunada-type isospectral non-isometric counterexamples do not exist in the constrained product sphere class.

*Proof.* Sunada's method requires a non-trivial fundamental group and finite covers. $M(a)$ is a product of $S^3 \times S^3 \times S^3$. Since $S^3$ is simply connected, the product is also simply connected, with trivial fundamental group. Hence Sunada's method is not applicable in this class. $\square$

### 3.8 Dimensional Necessary Condition for Spectral Rigidity

Let $\mathcal{F}$ be a class of Riemannian manifolds, and let $\mathcal{M}$ be its moduli space (i.e., the set of isometry classes). Assume $\mathcal{M}$ has the structure of a smooth manifold of dimension $d$. Define the spectral map $\sigma_k$ sending each isometry class to the vector of its first $k$ non-zero Laplace eigenvalues:

$$\sigma_k: \mathcal{M} \to \mathbb{R}^k, \quad [g] \mapsto (\lambda_1^\Delta, \lambda_2^\Delta, \dots, \lambda_k^\Delta).$$

**Theorem 3.6** (Dimensional Necessary Condition for Spectral Rigidity) Let $\mathcal{M}$ be the moduli space of a class of manifolds, of finite dimension $d$. If the first $k$ Laplace eigenvalues can achieve spectral rigidity (i.e., $\sigma_k$ is injective), then necessarily $d \leq k$. Under the interlocking constants determined by Theorem 3.0' and Proposition 3.0, the moduli space of $\{M(a)\}_{a>0}$ has dimension $d=1$, so $k\geq 1$ suffices to satisfy the necessary condition.

*Proof.* Suppose $d > k$. Since eigenvalues depend continuously on the metric, the spectral map $\sigma_k$ is continuous. If $\sigma_k$ is injective, then $\sigma_k$ gives a continuous injection from the $d$-dimensional manifold $\mathcal{M}$ into $\mathbb{R}^k$.

By **Brouwer's Invariance of Domain Theorem**: If $U \subset \mathbb{R}^d$ is open and $f: U \to \mathbb{R}^k$ is a continuous injection, then $f(U)$ is open in $\mathbb{R}^k$ (in the subspace topology). However, every point of the $d$-dimensional manifold $\mathcal{M}$ has an open neighborhood $U$ homeomorphic to $\mathbb{R}^d$. If $d > k$, the topological dimension of $f(U)$ as a subset of $\mathbb{R}^k$ cannot exceed $k$, whereas the topological dimension of $U$ is $d > k$, contradicting the Invariance of Domain theorem ($f(U)$ cannot be open in $\mathbb{R}^k$ because its topological dimension is insufficient). Hence a $d$-dimensional manifold cannot be injected continuously into $\mathbb{R}^k$ when $d > k$.

Thus if $d > k$, the continuous injection $\sigma_k$ cannot exist. Spectral rigidity requires $d \leq k$. $\square$

**Detailed Explanation:** The core of Brouwer's Invariance of Domain theorem is: if $U\subset\mathbb{R}^d$ is open and $f:U\to\mathbb{R}^d$ is a continuous injection, then $f(U)$ is also open. When $d>k$, viewing $\mathbb{R}^k$ as a subspace of $\mathbb{R}^d$, no continuous injection $f:U\to\mathbb{R}^k$ (with $U\subset\mathbb{R}^d$ open) can exist, because $f(U)$ would have no interior points in $\mathbb{R}^d$ (its topological dimension is $k<d$), while Invariance of Domain would require $f(U)$ to be open in $\mathbb{R}^d$ (if one considers the embedding of $\mathbb{R}^k$ into $\mathbb{R}^d$). A more direct argument: if $d>k$, then for any open set $U$ in $\mathbb{R}^d$, the image $f(U)\subset\mathbb{R}^k$ has Lebesgue measure zero (since $\mathbb{R}^k$ has measure zero in $\mathbb{R}^d$), but a continuous injection maps open sets to open sets (in the relative topology), and an open set in $\mathbb{R}^k$ has measure zero in $\mathbb{R}^d$, contradicting the fact that $U$ has positive measure in $\mathbb{R}^d$.

**Remark 3.6' (Dimension Counting Argument)** Theorem 3.6 can also be derived directly from the standard dimension counting of differential topology: if $d>k$, then no open set $U$ of the $d$-dimensional manifold $\mathcal{M}$ can be embedded into $\mathbb{R}^k$ via a continuous injection (since the topological dimension of $\mathbb{R}^k$ is $k<d$). Hence the injectivity of the spectral map $\sigma_k$ requires $d\leq k$. For the constrained product sphere class, the moduli space dimension is $d=1$, so $k\geq 1$ suffices for the necessary condition; this paper uses $k=3$ to provide self-consistency checks and a spectral signature.

**Corollary 3.2** In the constrained product sphere class $\{M(a)\}_{a>0}$ (with interlocking constants locked by Theorem 3.0' and Proposition 3.0), the moduli space dimension is $d = 1$. Hence only $k \geq 1$ eigenvalues are needed to satisfy the necessary condition $d \leq k$; this paper uses $k = 3$ eigenvalues, which not only satisfies the necessary condition, but also provides self-consistency checks and a spectral signature.

### 3.9 Compatibility with Classical Isospectral Counterexamples

**Theorem 3.7** (Inapplicability of Sunada-type Counterexamples) The fundamental group of $M(a)$ is $\pi_1(M(a))=0$, so Sunada's method is not applicable.

*Proof.* $\pi_1(S^3)=0$ ($S^3$ is simply connected). By the fundamental group formula for product spaces, $\pi_1(M(a))=\pi_1(S^3)\times\pi_1(S^3)\times\pi_1(S^3)=0$. Sunada's method requires the existence of a finite group $\Gamma$ acting freely on a manifold $\tilde{M}$ such that $M=\tilde{M}/\Gamma$ and $\Gamma$ has almost-conjugate but non-conjugate subgroups. Since $\pi_1(M(a))=0$, no non-trivial coverings exist, so Sunada's construction cannot be implemented. $\square$

**Theorem 3.8** (Inapplicability of Milnor-type Flat Torus Counterexamples) $M(a)$ has positive sectional curvature (as a product of $S^3$ spheres), is non-flat, hence Milnor's 16-dimensional flat torus isospectral pairs do not apply to this class.

*Proof.* $S^3(R)$ equipped with the standard metric has sectional curvature $1/R^2>0$. The sectional curvature of a product manifold is non-negative (by O'Neill's formula), and is positive in at least some directions. Hence $M(a)$ is non-flat. Milnor's isospectral flat torus counterexamples rely on the special spectral properties of flat metrics (such as modular transformations of theta functions), which do not hold on positively curved manifolds. $\square$

**Theorem 3.9** (Inapplicability of Gordon–Webb–Wolpert-type Counterexamples) The construction of planar isospectral region pairs relies on the isometry group of the Euclidean plane and the boundary conditions of the wave equation. $M(a)$ is a closed manifold (without boundary), and its spectrum is the global spectrum of the Laplace–Beltrami operator, not the Dirichlet/Neumann spectrum of a planar region, so this class of counterexamples does not apply.

*Proof.* The Gordon–Webb–Wolpert counterexample constructs planar regions with identical Dirichlet (or Neumann) spectra but different shapes. This construction relies on:
1. The planar Euclidean geometry of the regions;
2. The specific form of the boundary conditions (Dirichlet or Neumann);
3. Discrete subgroups of the isometry group (such as Fuchsian groups).
$M(a)$ is a compact Riemannian manifold without boundary, and its Laplace spectrum is a global spectrum, not involving boundary conditions. Moreover, the curvature of $M(a)$ is positive, not Euclidean planar. Hence this class of counterexamples does not apply. $\square$

**Remark 3.3** The above compatibility theorems demonstrate that the constrained product sphere class $\{M(a)\}$ is naturally immune in multiple mainstream directions of classical isospectral constructions, thereby strengthening the robustness of Theorem 3.4.
