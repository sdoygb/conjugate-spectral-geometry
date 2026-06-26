
# Mathematical Theory of the Ten-Direction Geometric Space

## An Axiomatic Framework for Constrained Product Spheres and Spectral Geometry

**Ouyang Guobin**  
*Guangdong, China*

---

**Version: 260626.6**

---

**Revision Notes:** This version (260626.6) includes the following corrections relative to the previous version (260622.6):

1. Corrected the erroneous claim of $D_3$ equivariant uniqueness in the "Detailed Supplement" box of Theorem 4.1, now consistent with the main text Step 1 and Remark 4.1′;
2. Corrected the statement regarding the independent status of Axiom 3 in Theorem 9.1(A), now consistent with Remarks 4.1/4.2;
3. Corrected the statement regarding the status of $\hbar$ in Theorem 8.6, now consistent with the honest annotation of Corollary 7.1;
4. Corrected the $\hat{A}(M(a))$ entry in Appendix A symbol table, now consistent with Theorem 7.2;
5. Unified references to Theorem 4.5 (the original text mixed "Theorem 4.5" and "Theorem 4.5′");
6. Corrected the title of Theorem 7.2 to distinguish $\hat{A}$-class from $\hat{A}$-genus;
7. Refined the Nijenhuis tensor statement in Theorem 4.1 Step 2;
8. Added forward reference note where Theorem 5.3 is cited early;
9. Added division-of-labor note for Lemma 3.0 and Theorem 3.0′.

---

**Abstract**

This paper establishes an axiomatic mathematical framework — the Ten-Direction Geometric Space — that integrates the topological analysis of the excitation parameter space, the spectral rigidity of constrained product sphere classes, the holographic screen encoding structure on the trifurcated tangent bundle, and the spectral convergence of discrete graph approximations into a logically self-consistent pure mathematical theory. Based on three fundamental axioms and three interlocking constants, this paper rigorously proves:

1. The range theorem and existence theorem for the abstract geometric quantity $S$;
2. The spectral rigidity theorem for the nine-dimensional constrained product sphere $M(a)=S^3(a)\times S^3(a/\sqrt{\Lambda})\times S^3(a/\sqrt{\Lambda k_0})$;
3. The range $[24,+\infty)$ and strict convexity of the six-term action on the holographic screen;
4. The scale-reciprocal self-dual bridging axiom and explicit spectrum-projection mapping;
5. The Berezin–Toeplitz quantization layer of the holographic screen and the algebraic origin of the magic number sequence $2,8,18,32,50,72,98$;
6. The spectral convergence of discrete graph approximations and information field degeneracy;
7. The extended locking structure of the Nine-Principle Mutual Containment, integrating rigorous results from the tool layer into a unified logical network.

This paper establishes a pure mathematical bridge between noncommutative spectral geometry and constrained Riemannian geometry. All physical mappings are explicitly marked as conditional propositions.

**Keywords:** axiomatic framework; spectral rigidity; product spheres; holographic screen; symplectic geometry; deformation quantization; graph Laplacian; heat kernel; Bott periodicity; spectral action

---

## Chapter 1 Introduction

### 1.1 Theoretical Background and Motivation

This paper constructs a mathematical framework from geometric axioms to physical constant mappings. In this framework, the topological properties of the excitation parameter space, the spectral rigidity of high-dimensional product manifolds, the encoding structure of the two-dimensional holographic screen, and the spectral convergence of discrete approximations are integrated into a logically self-consistent pure mathematical system.

This paper adopts the following axiomatic strategy:

**Three Fundamental Axioms**:
- **Axiom 1 (Circle Topology Axiom)**: The excitation parameter space $D$ is obtained from $S^1$ by removing the vacuum point $p_0$ and the degeneration point $p_*$;
- **Axiom 2 (Boundary Limit Axiom)**: The geometric quantity $S$ is continuous on $D$, satisfying the vacuum limit $S\to 0$ and the degeneration limit $S\to+\infty$;
- **Axiom 3 (Holographic Screen Encoding Condition)**: On each fiber of the trifurcated tangent bundle $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$, there exists a two-dimensional oriented subspace $\Sigma$ (the holographic screen), with sector projection intensity angles satisfying $\theta_1+\theta_2+\theta_3=90^\circ$.

**Three Interlocking Constants**: $\Lambda=\Lambda(S_3)=3$ (tripartition proportionality parameter, the number of conjugacy classes of $S_3$, rigorously computed in Proposition 3.0), $k_0=k_0(S_3)=2$ (binary compactness constant, the index of the maximal normal subgroup of $S_3$, rigorously computed in Proposition 3.0), $\ell_0>0$ (scale constant, locked by the spectral unit selection theorem and the ground state condition).

### 1.2 The Role and Positioning of the Tool Layer Framework

This paper integrates three mathematical tool layers, each providing rigorous foundations for the core framework from different dimensions:

- **Chapter 6** ($S^2$ deformation quantization): Provides rigorous foundations for deformation quantization on the holographic screen $\Sigma\cong S^2$ and the magic number sequence;
- **Chapter 7** ($M(a)$ spectral rigidity and Dirac index): Provides rigorous foundations for constrained isospectral rigidity of $M(a)$ and classification of Laplace low-energy modes, and provides rigorous geometric theorems for normal bundle curvature and Hessian soft/hard mode locking;
- **Chapter 8** (Discrete graph approximation and spectral convergence): Provides rigorous foundations for spectral convergence of discrete graph approximations of the holographic screen and heat kernel decay.

### 1.3 Main Results and Structural Organization

This paper establishes a complete mathematical framework based on three axioms:

1. **Axiom 1 and Axiom 2** (Chapter 2): Circle topology and boundary limits of the excitation parameter space, yielding the range $(0,+\infty)$ and existence theorem for the abstract geometric quantity;
2. **Chapter 3** (Constrained product spheres and spectral rigidity): Moduli space parametrization and uniqueness of isometry classes for $M(a)=S^3(a)\times S^3(a/\sqrt{\Lambda})\times S^3(a/\sqrt{\Lambda k_0})$;
3. **Holographic screen encoding condition** (Chapter 4): Equal-proportion projection from three sectors of the trifurcated tangent bundle to the two-dimensional holographic screen ($\Lambda=3$ locks each at $30^\circ$), yielding $\theta_1+\theta_2+\theta_3=90^\circ$, range $[24,+\infty)$ for the six-term action, with minimum $24$ realized precisely at the symmetric point $30^\circ$, and $S$ strictly convex on $D_\theta$;
4. **Chapter 5** (Unification of the Ten-Direction Geometric Space): Range coordination, bridging axiom, explicit spectrum-projection mapping, and the bridging function canonical form theorem;
5. **Chapter 6** (Deformation quantization of the holographic screen): Algebraic origin of the magic number sequence $2,8,18,32,50,72,98$ and Bott periodicity truncation $N_{\text{eff}}=7$;
6. **Chapter 7** (Higher-dimensional spectral geometry): Dirac index, spectral action algebraic relations, normal bundle curvature-Hessian locking;
7. **Chapter 8** (Discrete approximation and information field degeneracy): Graph Laplacian spectral convergence, heat kernel decay, Weyl's law;
8. **Chapter 9** (Nine-Principle Mutual Containment): Three axioms, three interlocking constants, three tool layer theorems form a mutually locking logical network;
9. **Chapter 10** (Overdetermined locking and bootstrap closure): Establishment of the overdetermined system and the uniqueness proof for interlocking constants, together with the formalized dependency theorem chain.

### 1.4 Theoretical Boundaries and Annotation System

This paper adopts a strict tripartite classification of propositions:

- **Mathematical Theorems (Theorem X.Y)**: Rigorously derived from Axioms 1–3 and standard mathematical tools, without dependence on any physical experience or experimental data. Their truth values are guaranteed by the axiom system and logical rules.
- **Conditional Propositions (Proposition X.Y* or Theorem X.Y*)**: Valid under specific geometric-physical correspondence assumptions (e.g., "the gauge field $F_A$ is identified with the $U(1)$ subcomponent of the normal bundle Spin connection"). Their mathematical derivation is rigorous, but the geometric-physical identification belongs to the framework's explicit conditions.
- **Physical Mappings (Mapping X.Y or Remark [Physical Mapping])**: Relate mathematical outputs to experimental constants (e.g., $\alpha^{-1}\approx 137.035999084$). Their numerical agreement belongs to empirical observation and does not constitute mathematical proof for the axiom system.

Uniform annotation: Physical mappings and conditional assumptions are explicitly marked with footnotes or `remark` environments, to avoid confusing the reader between mathematical necessity and physical correspondence.

---

## Chapter 2 Axiomatization of the Excitation Parameter Space

### 2.1 Axiom 1 (Topology of the Parameter Space)

**Axiom 1 (Circle Topology Axiom)** The excitation parameter space $D$ is obtained from the one-dimensional compact connected manifold $S^1$ (the circle) by removing two distinct points $p_0$ and $p_*$:

$$D = S^1 \setminus \{p_0, p_*\}, \qquad p_0 \neq p_*$$

The two removed points are respectively called the **vacuum point** ($p_0$) and the **degeneration point** ($p_*$). Consequently, $D$ consists of two connected components:

$$D_+ \cong (0,1), \qquad D_- \cong (0,1)$$

Each component is homeomorphic to an open interval. The parameter $x \in D_\pm$ labels the excitation state.

**Lemma 2.1 (Topological Structure of the Components)** Let $S^1$ be the standard unit circle $\{e^{i\phi} \mid \phi \in [0,2\pi)\}$. Removing two points $p_0=e^{i\phi_0}$ and $p_*=e^{i\phi_*}$ (assume without loss of generality $0\leq \phi_0 < \phi_* < 2\pi$), then $S^1\setminus\{p_0,p_*\}$ has exactly two connected components:
$$D_+ = \{e^{i\phi} \mid \phi_0 < \phi < \phi_*\}, \quad D_- = \{e^{i\phi} \mid \phi_* < \phi < \phi_0+2\pi\}.$$
Each component, as a subspace of $S^1$, is homeomorphic to the open interval $(0,1)$.

*Proof.* Consider the standard covering map $\pi: \mathbb{R} \to S^1$, $\pi(\phi)=e^{i\phi}$. On $\mathbb{R}$, $\pi^{-1}(S^1\setminus\{p_0,p_*\}) = \mathbb{R}\setminus\{\phi_0+2k\pi, \phi_*+2k\pi \mid k\in\mathbb{Z}\}$. Each connected component of this set is an open interval $(\phi_0+2k\pi, \phi_*+2k\pi)$ or $(\phi_*+2k\pi, \phi_0+2(k+1)\pi)$. Since the restriction of $\pi$ to an interval of length $2\pi$ is a homeomorphism, the images of these open intervals in $S^1$ are precisely $D_+$ and $D_-$. Each open interval is homeomorphic to $(0,1)$, hence $D_\pm \cong (0,1)$. $\square$

### 2.2 Axiom 2 (Analytic Properties of the Geometric Quantity)

**Axiom 2 (Boundary Limit Axiom)** On the parameter space $D$ there exists a geometric quantity $S: D \to (0,+\infty)$, satisfying:

1. **Continuity**: $S$ is continuous on each connected component $D_\pm$;
2. **Vacuum limit**: As $x$ approaches $p_0$ along either component, $\lim_{x \to p_0} S(x) = 0$;
3. **Degeneration limit**: As $x$ approaches $p_*$ along either component, $\lim_{x \to p_*} S(x) = +\infty$.

**Remark 2.1** Axiom 2 does not require $S$ to have the same functional expression on $D_+$ and $D_-$, nor does it require $S$ to be continuous on the whole $D$ ($p_0$ and $p_*$ are not in $D$). Hence $S$ may be two different functions on the two independent components, provided each satisfies the boundary conditions.

### 2.3 Range Theorem

**Theorem 2.1 (Range)** Under Axioms 1 and 2, the range of $S$ on each connected component $D_\pm$ is $S(D_\pm) = (0, +\infty)$.

*Proof.* By Axiom 1, $D_\pm \cong (0,1)$ is connected. By Axiom 2, $S$ is continuous on $D_\pm$, hence the image $S(D_\pm)$ is a connected subset of $\mathbb{R}$, i.e., an interval. By the vacuum limit, $\inf S(D_\pm) = 0$; by the degeneration limit, $\sup S(D_\pm) = +\infty$. Since $p_0, p_* \notin D$, the endpoints $0$ and $+\infty$ are not attained. Hence $S(D_\pm) = (0, +\infty)$. $\square$

**Detailed Explanation:** The connectedness argument can be further expanded as follows. Let $D_+ \cong (0,1)$, $S: D_+ \to \mathbb{R}$ continuous. Suppose $S(D_+)$ were not an interval, then there would exist $\alpha < \beta < \gamma$ such that $\alpha, \gamma \in S(D_+)$ but $\beta \notin S(D_+)$. Let $U = S^{-1}((-\infty, \beta))$ and $V = S^{-1}((\beta, +\infty))$, then $U,V$ are disjoint open sets in $D_+$, and $U\cup V = D_+$, contradicting the connectedness of $D_+$. Hence $S(D_+)$ must be an interval. Combined with the boundary limits, this interval must be $(0,+\infty)$.

### 2.4 Existence Theorem and Strict Monotonicity Hypothesis

**Theorem 2.2 (Existence)** For any given positive number $S_0 > 0$, on each component $D_+$ and $D_-$ there exists at least one excitation state $x_+ \in D_+$ and $x_- \in D_-$ such that $S(x_+) = S(x_-) = S_0$.

*Proof.* By Theorem 2.1, $S(D_\pm) = (0, +\infty)$. For any $S_0 > 0$, clearly $S_0 \in (0, +\infty)$. Hence $S^{-1}(S_0) \cap D_\pm \neq \varnothing$. $\square$

**Definition 2.1′ (Strict Monotonicity Hypothesis)** If $S$ is strictly monotonic on $D_\pm$, then for any $S_0>0$, $x_+$ and $x_-$ in Theorem 2.2 are uniquely determined. Strict monotonicity is **not** a theorem derived from Axioms 1–2, but a **constructive hypothesis** of the framework. Its introduction is equivalent to requiring that $S$ constitutes a global coordinate function on $D_\pm$.

*Proof.* A strictly monotonic continuous function is injective, hence the preimage is unique. $\square$

---

## Chapter 3 Constrained Product Spheres and Spectral Rigidity

### 3.0 Group-Theoretic Origin of the Interlocking Functions

**Lemma 3.0 (Rigidity of the Trifurcated Tangent Bundle Permutation Group)** Let $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$ be the trifurcated tangent bundle, and $G$ its sector permutation symmetry group. If $G$ acts faithfully and transitively on the three sectors and contains arbitrary two-sector transpositions, then $G \cong S_3$, and $S_3$ is the unique finite group satisfying these conditions.

*Proof.* A faithful permutation group on three objects must be a subgroup of $S_3$. Transitivity requires orbit size 3, hence $|G| \geq 3$. The transitive subgroups of $S_3$ are only $A_3 \cong \mathbb{Z}_3$ (cyclic) and $S_3$ itself. If transpositions (odd permutations) are required, $A_3$ is insufficient, and the only possibility is $S_3$. $\square$

**Definition 3.0 (Interlocking Function and Compactness Function)** Let $G$ be a finite group. Define:
- **Interlocking function** $\Lambda(G) := |\text{Conj}(G)|$ (number of conjugacy classes, which by the fundamental theorem of representation theory equals the number of irreducible complex representations of $G$);
- **Compactness function** $k_0(G) := [G : N_{\max}]$ (index of the maximal normal subgroup).

**Proposition 3.0** For the permutation symmetry group $G = S_3$ of the trifurcated tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$:
$$\Lambda(S_3) = 3, \quad k_0(S_3) = 2.$$

*Proof.* The conjugacy class decomposition of $S_3$ is: identity $\{e\}$ (1), transpositions $\{(12),(13),(23)\}$ (3), 3-cycles $\{(123),(132)\}$ (2), for a total of 3 conjugacy classes, hence $\Lambda(S_3)=|\text{Conj}(S_3)|=3$.

The normal subgroups of $S_3$ are only $\{e\}$ and $A_3 \cong \mathbb{Z}_3$ (the alternating subgroup). The maximal normal subgroup is $A_3$, with index $[S_3 : A_3] = 6/3 = 2$, hence $k_0(S_3)=2$. $\square$

**Remark 3.0** By Lemma 3.0, $S_3$ is the unique choice for the trifurcated tangent bundle permutation symmetry group. The interlocking constants $\Lambda=3$ and $k_0=2$ are not freely chosen parameters, but necessary values of group-theoretic functions on $S_3$. If the trifurcated tangent bundle had $S_4$ permutation symmetry (four-sector structure), then $\Lambda(S_4)=5$, $k_0(S_4)=2$, which would be a completely different theory from the Ten-Direction Geometric Theory. The reason the Ten-Direction Geometric Theory locks $\Lambda=3$, $k_0=2$ is that its group structure is $S_3$ (three sectors), and Lemma 3.0 has already proved the uniqueness of this group choice.

**Theorem 3.0′ (Rigidity of Trifurcated Tangent Bundle Sector Permutations)** Let $M = S^3 \times S^3 \times S^3$ be equipped with the product metric, and suppose there exists a tangent bundle decomposition $TM = \mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ such that the three sectors are completely equivalent at the metric level (i.e., any permutation induces an isometric automorphism). Then:
1. The sector permutation group $G$ of this decomposition must contain all two-sector transpositions;
2. The finite group satisfying (1) is uniquely isomorphic to $S_3$.

Furthermore, $\Lambda(G)=|\text{Conj}(S_3)|=3$ and $k_0(G)=[S_3:A_3]=2$ are necessary outputs of group-theoretic functions.

*Proof.* (1) If the three sectors are metrically equivalent, then any transposition (e.g., $\mathcal{M}\leftrightarrow\mathcal{C}$) preserves the product metric, hence induces an isometric automorphism. Therefore all two-sector transpositions belong to $G$.

(2) By Lemma 3.0, a transitive permutation group containing transpositions can only be $S_3$. Hence $G\cong S_3$ is not an artificial choice, but a necessary consequence of non-trivial permutations under the threefold equivalence structure. $\square$

### 3.1 Definitions and Assumptions

**Definition 3.1 (Constrained Product Sphere)** Let $a > 0$ be the global scale factor. By Theorem 3.0′ and Proposition 3.0, the group-theoretic functions of the trifurcated tangent bundle permutation group $S_3$ yield:
$$\Lambda = \Lambda(S_3) = 3 \quad \text{(tripartition proportionality parameter)}, \quad k_0 = k_0(S_3) = 2 \quad \text{(binary compactness constant)}, \quad \ell_0 > 0 \quad \text{(scale constant, locked by the spectral unit selection theorem and ground state condition)}.$$

The nine-dimensional closed manifold

$$M(a) = S^3(a) \times S^3(a/\sqrt{3}) \times S^3(a/\sqrt{6})$$

equipped with the product metric $g = g_a \oplus g_{a/\sqrt{3}} \oplus g_{a/\sqrt{6}}$ is called a **Constrained Product Sphere** (CPS). Denote

$$b = \frac{a}{\sqrt{3}}, \quad c = \frac{a}{\sqrt{6}}.$$

The scale ordering $a > b > c$ holds strictly ($1 > 1/\sqrt{3} > 1/\sqrt{6}$).

**Remark 3.1 (Triviality of the Tangent Bundle)** Since $S^3$ as a Lie group $SU(2)$ is parallelizable, its tangent bundle $TS^3$ is trivial. The tangent bundle of a product manifold is the direct sum of the tangent bundles of the factors, hence $TM(a)$ is automatically trivial. Therefore, tangent bundle triviality holds automatically in this class and need not be listed as an additional hypothesis.

**Remark 3.2 (Properties of the Interlocking Constants)** The constants $\Lambda=3$, $k_0=2$ are directly computed from the $S_3$ group structure by Theorem 3.0′ and Proposition 3.0; $\ell_0$ is locked by the self-consistent output of the Nine-Principle Mutual Containment network. None of the three are freely chosen parameters: $\Lambda$ and $k_0$ are necessary values of the group-theoretic functions $|\text{Conj}(S_3)|$ and $[S_3:A_3]$; $\ell_0$ is uniquely determined by the joint constraints of the spectral separation condition, heat kernel coefficient ratio, information hierarchy nesting, and magic number truncation (see Chapters 9–10). As a positive real parameter, $\ell_0$ is locked by the spectral unit selection theorem and the ground state condition $S_{\min}=24$, providing a numerical anchor for the spectrum-projection bridge, but does not participate in the one-dimensional parametrization of the moduli space.

### 3.2 Parametrization of the Moduli Space

**Theorem 3.1 (Parametrization of the Moduli Space)** Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0′ and Proposition 3.0 are locked, the moduli space of the **constrained product sphere class** $\{M(a)\}_{a>0}$ (manifolds defined in Definition 3.1 equipped with the standard product metric and satisfying the proportionality constraints $b=a/\sqrt{\Lambda}, c=a/\sqrt{\Lambda k_0}$) is homeomorphic to the open interval $(0, \infty)$, where $a$ is the unique continuous degree of freedom (global scale factor). Different $a$ correspond to different isometry classes.

**Theorem 3.1′ (First Eigenvalue as a Coordinate)** Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0′ and Proposition 3.0 are locked, the spectral mapping
$$\sigma_1: (0,\infty) \to (0,\infty), \quad a \mapsto \lambda_1^\Delta(a) = \frac{3}{a^2}$$
is a diffeomorphism. Hence, the first non-zero Laplace eigenvalue $\lambda_1^\Delta$ itself constitutes a **global coordinate** on the moduli space $\{M(a)\}_{a>0}$ of the constrained product sphere class, and the spectral characteristic signature $(1,\ 8/3,\ \Lambda)$ is independent of $a$.

*Proof.* $\sigma_1$ is continuous, strictly monotonically decreasing, with $\lim_{a\to 0^+}\sigma_1(a)=+\infty$, $\lim_{a\to+\infty}\sigma_1(a)=0$. Hence $\sigma_1$ is a homeomorphism $(0,\infty)\to(0,\infty)$; moreover, since $\sigma_1'(a)=-6/a^3\neq 0$, the inverse map is smooth, so it is a diffeomorphism. $\square$

**Remark 3.1′ (Status of the Defined Class)** This theorem studies the **defined class** $\{M(a)\}$ — i.e., the subset of product spheres satisfying the specific proportionality constraints of Definition 3.1 — and not "all manifolds diffeomorphic to $S^3\times S^3\times S^3$ whose first three Laplace eigenvalues satisfy the spectral characteristic signature." The moduli space of the latter (the more general isospectral class) may be larger, and this paper makes no claim to its complete classification.

*Proof.* By Definition 3.1, the factors are spheres characterized by radii $(a,b,c)$, and the ratios of $b$ and $c$ to $a$ are locked by $\Lambda$ and $k_0$. Hence, with $(k_0, \Lambda, \ell_0)$ fixed, the unique continuous degree of freedom is the global scale $a$. Since $S^3$ is parallelizable, $TM(a)$ is automatically trivial, and the topology is uniquely determined. Thus the moduli space is completely parametrized by $a \in (0, \infty)$, with different $a$ giving different curvature radii and hence different isometry classes. $\square$

**Detailed Argument:** The rigor of the isometry class distinction can be further elaborated. Suppose $a \neq a'$; then the first factor $S^3(a)$ and $S^3(a')$ have different radii. Since $S^3(R)$ has diameter $\pi R$ and volume $2\pi^2 R^3$, isometric manifolds must have identical diameter and volume. If $M(a)$ and $M(a')$ were isometric, their diameters and volumes would have to be equal. For the product metric, the diameter formula is
$$\text{diam}(M(a)) = \pi\sqrt{a^2+b^2+c^2} = \pi a\sqrt{1+\frac{1}{\Lambda}+\frac{1}{\Lambda k_0}},$$
where $b=a/\sqrt{\Lambda}$, $c=a/\sqrt{\Lambda k_0}$. Since $\Lambda$ and $k_0$ are locked interlocking constants, $\sqrt{1+1/\Lambda+1/(\Lambda k_0)}$ is a positive constant independent of $a$, so $\text{diam}(M(a))$ is a strictly monotonic function of $a$. Hence $a=a'$, and different $a$ correspond to different isometry classes.

### 3.3 Explicit Computation of Laplace Eigenvalues

**Proposition 3.1 (Spectral Separation on Product Manifolds)** For the constrained product sphere $M(a)$, the eigenvalues of the Laplace–Beltrami operator $\Delta_g$ are

$$\lambda_{p,q,r}^\Delta = \frac{p(p+2)}{a^2} + \frac{q(q+2)}{b^2} + \frac{r(r+2)}{c^2}, \quad p,q,r \in \mathbb{N}_0.$$

where $p=q=r=0$ corresponds to the zero eigenvalue (constant function), and non-zero eigenvalues begin at $p+q+r \geq 1$.

*Proof.* On a product manifold, the Laplace operator separates as $\Delta_g = \Delta_1 + \Delta_2 + \Delta_3$, where $\Delta_i$ is the Laplace operator on each factor. It is known that on $S^3(R)$, the eigenvalue corresponding to the $p$-th order spherical harmonic is $p(p+2)/R^2$, hence the total eigenvalue is the sum of the three. $\square$

**Supplementary Explanation:** The standard derivation of Laplace eigenvalues on $S^3(R)$ is as follows. Embed $S^3(R)$ into $\mathbb{R}^4$ as $\{x\in\mathbb{R}^4: |x|=R\}$. The restriction of a degree-$p$ homogeneous harmonic polynomial in $\mathbb{R}^4$ to $S^3(R)$ gives a spherical harmonic. By separation of the Euclidean Laplacian into radial and angular parts, $\Delta_{\mathbb{R}^4} = \partial_r^2 + \frac{3}{r}\partial_r + \frac{1}{r^2}\Delta_{S^3}$. For a homogeneous function of degree $p$, $f(r,\theta)=r^p Y(\theta)$, $\Delta_{\mathbb{R}^4}f=0$ yields $\Delta_{S^3}Y = -p(p+2)Y$. On $S^3(R)$, the metric scale factor is $R^2$, so the eigenvalue is $p(p+2)/R^2$.

**Proposition 3.2 (Explicit Expressions for the First Three Eigenvalues)** Under the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ locked by Theorem 3.0′ and Proposition 3.0, the first three non-zero eigenvalues of $M(a)$ are:

| Mode (p,q,r) | Eigenvalue Expression | Ratio to 3/a² |
|:---|:---|:---|
| (1,0,0) | 3/a² | 1 |
| (2,0,0) | 8/a² | 8/3 ≈ 2.667 |
| (0,1,0) | 3Λ/a² = 9/a² | Λ = 3 |
| (0,0,1) | 3Λk₀/a² = 18/a² | Λk₀ = 6 |
| (1,1,0) | 3/a² + 3Λ/a² = 12/a² | Λ+1 = 4 |

*Proof.* By Proposition 3.1, the eigenvalues of each candidate mode are computed as shown in the table above.

Since the interlocking constant $\Lambda=3$, we have $3\Lambda/a^2 = 9/a^2 > 8/a^2$, so the $(0,1,0)$ mode is strictly greater than the $(2,0,0)$ mode. Since $k_0=2$, we have $3\Lambda k_0/a^2 = 18/a^2 > 9/a^2$, so the $(0,0,1)$ mode is strictly greater than the $(0,1,0)$ mode. Other combinations (such as $(1,0,1)$, $(0,2,0)$, etc.) have larger numerical values. Hence the first three non-zero eigenvalues are exactly given by the first three rows of the table above. $\square$

### 3.4 Eigenvalue Ordering and Spectral Characteristic Signature

**Theorem 3.2 (Eigenvalue Ordering)** For any $a > 0$ and with the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ locked by Theorem 3.0′ and Proposition 3.0, the first four non-zero eigenvalues satisfy

$$\lambda_1^\Delta = \frac{3}{a^2} < \lambda_2^\Delta = \frac{8}{a^2} < \lambda_3^\Delta = \frac{3\Lambda}{a^2} < \lambda_4^\Delta = \min\left\{\frac{3\Lambda k_0}{a^2},\ \frac{3(\Lambda+1)}{a^2}\right\}.$$

*Proof.* The candidate mode $(0,0,1)$ gives $3\Lambda k_0/a^2$, the candidate mode $(1,1,0)$ gives $3(\Lambda+1)/a^2$, and the candidate mode $(0,2,0)$ gives $8\Lambda/a^2$. Since $k_0>1$ and $\Lambda>8/3$, all three are strictly greater than $\lambda_3^\Delta=3\Lambda/a^2$. Comparing $(0,2,0)$ and $(1,1,0)$: $8\Lambda > 3(\Lambda+1)$ holds when $\Lambda>3/5$, so under $\Lambda>8/3$, $8\Lambda/a^2 > 3(\Lambda+1)/a^2$ always holds. Comparing $(0,2,0)$ and $(0,0,1)$: the relative size of $8\Lambda$ and $3\Lambda k_0$ depends on $k_0$; when $k_0>8/3$, $3\Lambda k_0 > 8\Lambda$, and when $1<k_0<8/3$, $8\Lambda > 3\Lambda k_0$. Therefore the fourth eigenvalue is determined by $\min\{3\Lambda k_0, 3(\Lambda+1)\}/a^2$, while $(0,2,0)$ does not enter the top four (under $\Lambda>8/3$ it is greater than $(1,1,0)$, and only when $k_0<8/3$ could it be less than $(0,0,1)$, but even then it remains greater than $(1,1,0)$). Other candidate modes (such as $(3,0,0)$ etc.) have larger numerical values. $\square$

**Remark 3.4** Under the interlocking constants $\Lambda=3$, $k_0=2$, we have $3\Lambda k_0/a^2 = 18/a^2 > 3(\Lambda+1)/a^2 = 12/a^2$, so $\lambda_4^\Delta = 12/a^2 = 3(\Lambda+1)/a^2$. This ordering is uniquely determined by the interlocking constants.

**Corollary 3.1 (Characteristic Signature)** The ratios

$$\frac{\lambda_2^\Delta}{\lambda_1^\Delta} = \frac{8}{3}, \quad \frac{\lambda_3^\Delta}{\lambda_1^\Delta} = \Lambda$$

are universal constants (for fixed $\Lambda$) independent of $a$ and $k_0$, and can serve as the **spectral characteristic signature** (spectral signature) of the constrained product sphere class. If the ratio of the first two non-zero eigenvalues of some product sphere is not $8/3$, then it does not belong to this class.

### 3.5 Recovering the Scale Factor from the First Three Eigenvalues

**Theorem 3.3 (Inversion Formula)** Given the first three non-zero Laplace eigenvalues $\lambda_1^\Delta$, $\lambda_2^\Delta$, $\lambda_3^\Delta$ of $M(a)$, the scale factors can be uniquely recovered:

$$a = \sqrt{\frac{3}{\lambda_1^\Delta}}, \quad b = \sqrt{\frac{3}{\lambda_3^\Delta}}, \quad c = \frac{a}{\sqrt{\Lambda k_0}} = \sqrt{\frac{3}{\Lambda k_0 \cdot \lambda_1^\Delta}}.$$

**Self-consistency Condition** A triple of positive numbers $(\lambda_1, \lambda_2, \lambda_3)$ are the first three non-zero eigenvalues of some $M(a)$ if and only if

$$\lambda_2 = \frac{8}{3}\lambda_1 \quad \text{and} \quad \lambda_3 = \Lambda(S_3) \lambda_1 = 3\lambda_1.$$

In this case, $a = \sqrt{3/\lambda_1}$.

*Proof.* By Theorem 3.2, $\lambda_1^\Delta = 3/a^2 \Rightarrow a = \sqrt{3/\lambda_1^\Delta}$; $\lambda_3^\Delta = 3/b^2 \Rightarrow b = \sqrt{3/\lambda_3^\Delta}$; by the proportionality constraint of Definition 3.1, $c = a/\sqrt{\Lambda k_0}$. The self-consistency condition follows directly from $\lambda_2^\Delta = 8/a^2$ and $\lambda_3^\Delta = 3\Lambda/a^2$. $\square$

**Lemma 3.1 (One-to-one Correspondence between Spectral Data and Geometry)** Under the premise that the interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$ determined by Theorem 3.0′ and Proposition 3.0 are locked, there exists an explicit one-to-one mapping between the first three non-zero Laplace eigenvalues and the scale factors $(a,b,c)$. Given $\lambda_1^\Delta$, $\lambda_2^\Delta$, $\lambda_3^\Delta$, $(a,b,c)$ can be uniquely recovered; conversely, given $(a,b,c)$, the first three eigenvalues can be uniquely computed.

### 3.6 Spectral Rigidity Theorem

**Theorem 3.4 (Spectral Rigidity of the Constrained Product Sphere)** Let $M(a)$ and $M(a')$ be two constrained product spheres with identical interlocking constants $(\Lambda=\Lambda(S_3)=3, k_0=k_0(S_3)=2, \ell_0>0)$. If their Laplace–Beltrami operators have identical first three non-zero eigenvalues, then $M(a)$ and $M(a')$ are isometric.

*Proof.* By Proposition 3.2, the first non-zero Laplace eigenvalue is $\lambda_1^\Delta=3/a^2$. If $M(a')$ is isospectral to $M(a)$, then $\lambda_1^{\Delta}(a')=\lambda_1^{\Delta}(a)$, i.e., $3/a'^2=3/a^2$. Since $a,a'>0$, this yields $a'=a$. By the proportionality constraints of Definition 3.1, $b=a/\sqrt{\Lambda}$, $c=a/\sqrt{\Lambda k_0}$, the scale triple $(a,b,c)$ is uniquely determined, hence $M(a')$ and $M(a)$ are isometric. $\square$

**Remark 3.1** The spectral rigidity of this theorem stems from the fact that the moduli space is parametrized by a single scale factor. Since isometry classes of constrained product spheres satisfying Definition 3.1 with locked interlocking constants are labeled uniquely by $a$, and the first three Laplace eigenvalues (in fact the first alone suffices) uniquely determine $a$, two manifolds with identical first three eigenvalues must belong to the same isometry class.

**Remark 3.2 (Completeness of the First Eigenvalue)** In the single-parameter family $\{M(a)\}_{a>0}$ with locked interlocking constants, the moduli space is one-dimensional. The first non-zero eigenvalue $\lambda_1^\Delta = 3/a^2$ itself already constitutes a complete coordinate on the moduli space (bijective with $a$). The latter two of the first three eigenvalues provide self-consistency checks (must satisfy the $8/3$ and $\Lambda$ ratios) and serve as the spectral characteristic signature of this class, used to determine whether a given manifold belongs to this class.

### 3.7 Compatibility with Classical Counterexamples

**Theorem 3.5** Sunada-type isospectral non-isometric counterexamples do not exist in the constrained product sphere class.

*Proof.* Sunada's method requires a non-trivial fundamental group and finite covers. $M(a)$ is a product of $S^3 \times S^3 \times S^3$. Since $S^3$ is simply connected, the product is also simply connected, with trivial fundamental group. Hence Sunada's method is inapplicable to this class. $\square$

### 3.8 Dimensional Necessary Condition for Spectral Rigidity

Let $\mathcal{F}$ be a class of Riemannian manifolds, and $\mathcal{M}$ its moduli space (i.e., the set of isometry classes). Assume $\mathcal{M}$ has a smooth manifold structure of dimension $d$. Define the spectral map $\sigma_k$ sending each isometry class to the vector of its first $k$ non-zero Laplace eigenvalues:

$$\sigma_k: \mathcal{M} \to \mathbb{R}^k, \quad [g] \mapsto (\lambda_1^\Delta, \lambda_2^\Delta, \dots, \lambda_k^\Delta).$$

**Theorem 3.6 (Dimensional Necessary Condition for Spectral Rigidity)** Let $\mathcal{M}$ be the moduli space of some manifold class, of finite dimension $d$. If the first $k$ Laplace eigenvalues can achieve spectral rigidity (i.e., $\sigma_k$ is injective), then necessarily $d \leq k$. Under the interlocking constants determined by Theorem 3.0′ and Proposition 3.0, the moduli space of $\{M(a)\}_{a>0}$ has dimension $d=1$, so only $k\geq1$ is needed to satisfy the necessary condition.

*Proof.* Suppose $d > k$. Since eigenvalues depend continuously on the metric, the spectral map $\sigma_k$ is continuous. If $\sigma_k$ is injective, then $\sigma_k$ gives a continuous injection from the $d$-dimensional manifold $\mathcal{M}$ into $\mathbb{R}^k$.

By **Brouwer's Invariance of Domain**: If $U \subset \mathbb{R}^d$ is open and $f: U \to \mathbb{R}^k$ is a continuous injection, then $f(U)$ is open in $\mathbb{R}^k$ (with respect to the subspace topology). However, every point of a $d$-dimensional manifold $\mathcal{M}$ has an open neighborhood $U$ homeomorphic to $\mathbb{R}^d$. If $d > k$, then $f(U)$ as a subset of $\mathbb{R}^k$ cannot have topological dimension exceeding $k$, whereas the topological dimension of $U$ is $d > k$, contradicting Invariance of Domain ($f(U)$ cannot be open in $\mathbb{R}^k$ because its topological dimension is insufficient). Therefore, a $d$-dimensional manifold cannot be mapped continuously and injectively into $\mathbb{R}^k$ when $d > k$.

Hence, if $d > k$, a continuous injection $\sigma_k$ cannot exist. Spectral rigidity requires $d \leq k$. $\square$

**Detailed Explanation:** The core of Brouwer's Invariance of Domain is: if $U\subset\mathbb{R}^d$ is open and $f:U\to\mathbb{R}^d$ is a continuous injection, then $f(U)$ is also open. When $d>k$, regarding $\mathbb{R}^k$ as a subspace of $\mathbb{R}^d$, no continuous injection $f:U\to\mathbb{R}^k$ (with $U\subset\mathbb{R}^d$ open) can exist, because $f(U)$ has no interior in $\mathbb{R}^d$ (its topological dimension is $k<d$), while Invariance of Domain requires $f(U)$ to be open in $\mathbb{R}^d$. A more direct argument: if $d>k$, then the image $f(U)\subset\mathbb{R}^k$ of any open set $U$ in $\mathbb{R}^d$ has Lebesgue measure zero (since $\mathbb{R}^k$ has measure zero in $\mathbb{R}^d$), but a continuous injection maps open sets to open sets (in the relative topology), and an open set in $\mathbb{R}^k$ has measure zero in $\mathbb{R}^d$, contradicting the fact that $U$ has positive measure in $\mathbb{R}^d$.

**Remark 3.6′ (Dimension Counting Argument)** Theorem 3.6 can also be derived directly from standard differential topology dimension counting: if $d>k$, then any open set $U$ of a $d$-dimensional manifold $\mathcal{M}$ cannot be embedded into $\mathbb{R}^k$ via a continuous injection (since the topological dimension of $\mathbb{R}^k$ is $k<d$). Therefore, injectivity of the spectral map $\sigma_k$ requires $d\leq k$. The moduli space of the present constrained product sphere class has dimension $d=1$, so $k\geq 1$ satisfies the necessary condition; this paper uses $k=3$ to provide self-consistency checks and spectral characteristic signatures.

**Corollary 3.2** In the constrained product sphere class $\{M(a)\}_{a>0}$ (with interlocking constants locked by Theorem 3.0′ and Proposition 3.0), the moduli space dimension is $d = 1$. Hence only $k \geq 1$ eigenvalues are needed to satisfy the necessary condition $d \leq k$; this paper uses $k = 3$ eigenvalues, which not only satisfies the necessary condition but also provides self-consistency checks and spectral characteristic signatures.

### 3.9 Compatibility with Classical Isospectral Counterexamples

**Theorem 3.7 (Inapplicability of Sunada-type Counterexamples)** $\pi_1(M(a))=0$, hence Sunada's method is inapplicable.

*Proof.* $\pi_1(S^3)=0$ ($S^3$ is simply connected). By the fundamental group formula for product spaces, $\pi_1(M(a))=\pi_1(S^3)\times\pi_1(S^3)\times\pi_1(S^3)=0$. Sunada's method requires the existence of a finite group $\Gamma$ acting freely on a manifold $\tilde{M}$ such that $M=\tilde{M}/\Gamma$ and $\Gamma$ has almost-conjugate but non-conjugate subgroups. Since $\pi_1(M(a))=0$, no non-trivial covering exists, so Sunada's construction cannot be implemented. $\square$

**Theorem 3.8 (Inapplicability of Milnor-type Flat Torus Counterexamples)** $M(a)$ has positive sectional curvature (as a product of $S^3$'s), not flat, so Milnor's 16-dimensional flat torus isospectral pairs are inapplicable to this class.

*Proof.* $S^3(R)$ equipped with the standard metric has sectional curvature $1/R^2>0$. The sectional curvature of a product manifold is non-negative (by O'Neill's formula) and is positive in at least some directions. Hence $M(a)$ is not flat. Milnor's isospectral flat torus counterexamples rely on special spectral properties of flat metrics (such as modular transformations of theta functions), which do not hold on positively curved manifolds. $\square$

**Theorem 3.9 (Inapplicability of Gordon–Webb–Wolpert-type Counterexamples)** The construction of planar isospectral region pairs depends on the isometry group of the Euclidean plane and boundary conditions of the wave equation. $M(a)$ is a closed manifold (without boundary), and its spectrum is the global spectrum of the Laplace–Beltrami operator, not the Dirichlet/Neumann spectrum of a planar region, so this class of counterexamples is inapplicable.

*Proof.* The Gordon–Webb–Wolpert counterexample constructs planar regions with identical Dirichlet spectrum (or Neumann spectrum) but different shapes. This construction relies on:
1. The planar Euclidean geometry of the regions;
2. The specific form of boundary conditions (Dirichlet or Neumann);
3. Discrete subgroups of the isometry group (such as Fuchsian groups).
$M(a)$ is a compact Riemannian manifold without boundary, and its Laplace spectrum is the global spectrum, not involving boundary conditions. Moreover, $M(a)$ has positive curvature, not Euclidean planar. Hence this class of counterexamples is inapplicable. $\square$

**Remark 3.3** The above compatibility theorems show that the constrained product sphere class $\{M(a)\}$ is naturally immune to several mainstream directions of classical isospectral constructions, which enhances the robustness of Theorem 3.4.

---
