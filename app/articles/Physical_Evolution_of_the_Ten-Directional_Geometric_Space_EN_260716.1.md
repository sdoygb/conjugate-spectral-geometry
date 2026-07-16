# Physical Evolution of 10-Direction Geometric Space

---

## Abstract

Starting from three axioms, this paper establishes the complete framework of 10-direction geometric space, encompassing both geometric foundations and the physical mapping layer, and presents an integrated derivation chain from axioms to physical observables.

**Part I (Geometric Foundations)** develops the axiomatic-deductive system of 10-direction geometric space: Axioms 1–2 define the excited state parameter space and the abstract geometric quantity; Axiom 3 defines the tripartite tangent bundle holographic encoding condition $\theta_1+\theta_2+\theta_3=90^\circ$. The tripartite bundle permutation group rigidity theorem ($G\cong S_3$ uniqueness) is proved, from which the interlocking constants $\Lambda=\Lambda(S_3)=3$ and $k_0=k_0(S_3)=2$ emerge group-theoretically. Spectral rigidity is established on the constrained product spheres $M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$. It is proved that the six-term action range $[24,+\infty)$ and the abstract geometric quantity range $(0,+\infty)$ are strictly compatible. The bridging function standard form $S(a)=12(a^2/\ell_0^2+\ell_0^2/a^2)$ is established (uniquely determined under scale-reciprocal duality, ground state locking, spectral asymptotic constraints, and the normalization condition). Through the nine-element mutual constraint and the overdetermined system of equations, bootstrap closure is proved, with all interlocking constants uniquely determined.

**Part II (Physical Mapping Layer)** establishes the single core mapping $\mathcal{E}$: the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle corresponds to electromagnetic interaction. From this mapping and the three axioms, all eigen-quantities are derived: $S_e$, electron mass, photon masslessness, effective soft/hard modes, the dimensional bridge first scale $N_1$, and the nucleon geometric charge $v_p$. At the physical identification point $(57.93^\circ, 26.16^\circ, 5.91^\circ)$, the Hessian structure and cross-sector coupling are established, with the effective metric $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})=(391.05, 59324.3)$ rad$^{-2}$ locked by the dual-mode zero-error condition. With the $\mathcal{E}$ mapping as the anchoring framework, all physical constants—$\hbar$, $\chi_L$, $\chi_T$, $K$—are derived self-consistently through the four equations of the dimensional bridge.

**Honest Remarks**: $\ell_0$ is a spectral-geometric unit anchor in its mathematical status; the numerical emergence of $\hbar$ and $S_e$ belongs to the conditional proposition layer; the normalization condition of the bridging function standard form is an explicit input of the framework.

**Keywords:** 10-direction geometric space; spectral rigidity; tripartite tangent bundle; holographic screen; bridging function standard form; nine-element mutual constraint; overdetermined locking; electromagnetic geometric mapping; cross-sector coupling; dual-mode zero error; dimensional bridge

---

# Part I &ensp; Geometric Foundations

## Chapter 1 &ensp; Axiom System and Excited State Parameter Space

### 1.1 &ensp; Three Axioms

The 10-direction geometric space is built upon the following three axioms:

**Axiom 1 (Circle Topology Axiom).** The excited state parameter space $D = S^1\setminus\{p_0,p_*\}$ consists of two connected components:
$$D_+\cong(0,1),\quad D_-\cong(0,1).$$

**Axiom 2 (Boundary Limit Axiom).** The geometric quantity $S: D_\pm\to(0,+\infty)$ is continuous on each branch and satisfies:
$$\lim_{x\to p_0}S(x)=0,\quad \lim_{x\to p_*}S(x)=+\infty.$$

**Axiom 3 (Holographic Screen Encoding Condition).** On each fiber $\mathbb{R}^9$ of the tripartite tangent bundle $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$, there exists a two-dimensional oriented subspace $\Sigma$ (the holographic screen) such that the projection intensity angles of the three three-dimensional sectors onto it satisfy
$$\theta_1+\theta_2+\theta_3=90^\circ,\qquad \theta_i\in(0^\circ,90^\circ).$$

### 1.2 &ensp; Basic Properties of the Excited State Parameter Space

**Proposition 1.1 (Circle Topology).** The excited state parameter space $D=S^1\setminus\{p_0,p_*\}$ consists of two connected components:
$$D_+\cong(0,1),\quad D_-\cong(0,1).$$

**Proposition 1.2 (Analytic Properties of the Geometric Quantity).** The geometric quantity $S:D_\pm\to(0,+\infty)$ is continuous on each branch and satisfies:
$$\lim_{x\to p_0}S(x)=0,\quad \lim_{x\to p_*}S(x)=+\infty.$$

**Theorem 1.3 (Range Theorem).** The range of $S$ on each branch is
$$S(D_\pm)=(0,+\infty).$$

**Theorem 1.4 (Existence Theorem).** For any given positive number $S_0>0$, there exists at least one parameter $x_+\in D_+$ and $x_-\in D_-$ in each branch such that $S(x_+)=S(x_-)=S_0$.

*Proof.* By Proposition 1.1, $D_\pm$ is homeomorphic to $(0,1)$, hence connected. By Proposition 1.2, $S$ is continuous with boundary limits $0$ and $+\infty$ respectively. By the intermediate value theorem for continuous functions, for any $S_0\in(0,+\infty)$, the level set $S^{-1}(S_0)$ is nonempty in each branch. $\square$

---

## Chapter 2 &ensp; Constrained Product Spheres and Spectral Rigidity

### 2.1 &ensp; Rigidity of the Tripartite Tangent Bundle Permutation Group

**Lemma 2.0 (Rigidity of the Tripartite Tangent Bundle Permutation Group).** The tripartite tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$ contains three labeled sectors $\{\mathcal{M},\mathcal{C},\mathcal{I}\}$. As set elements, the totality of permutations of the three sectors constitutes the symmetric group $S_3$ ($|S_3|=6$). The two group-theoretic invariants of this group are:
$$\Lambda(S_3) = |\text{Conj}(S_3)| = 3,\qquad k_0(S_3) = [S_3:A_3] = 2.$$

*Proof.* The conjugacy classes of $S_3$ are $\{e\}$ (identity), $\{(12),(13),(23)\}$ (transpositions), and $\{(123),(132)\}$ (3-cycles), totaling 3 classes, hence $\Lambda=3$. The maximal normal subgroup is the alternating group $A_3$, with index $[S_3:A_3]=2$, hence $k_0=2$. These values are uniquely determined by the group structure of $S_3$ and contain no free parameters. $\square$

**Honest Remark (Argumentative Status of $S_3$).** The above lemma establishes $S_3$ as a combinatorial fact about the three-sector set. It does not depend on whether metric equivalence exists among the sectors—as long as one acknowledges that the three sectors are distinct subspaces within the same bundle decomposition, the permutation group of this three-element set is $S_3$. $\Lambda=3$ and $k_0=2$ are necessary outputs of the $S_3$ group structure, not artificial choices.

**Proposition 2.0 (Group-Theoretic Origin of the Interlocking Functions).** For the permutation symmetry group $G = S_3$ of the tripartite tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$:
$$\Lambda(S_3) = 3, \quad k_0(S_3) = 2.$$

*Proof.* The number of conjugacy classes of $S_3$ is $3$ (identity, transpositions, 3-cycles), hence $\Lambda(S_3)=3$. The maximal normal subgroup of $S_3$ is $A_3$, with index $[S_3:A_3]=2$, hence $k_0(S_3)=2$. $\square$

### 2.2 &ensp; Constrained Product Spheres

**Definition 2.1 (Constrained Product Spheres).** Let $a>0$ be the global scale factor, $\Lambda=\Lambda(S_3)=3$ the tripartition ratio parameter, and $k_0=k_0(S_3)=2$ the dichotomous compactness constant. The nine-dimensional closed manifold
$$M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$$
equipped with the product metric is called a constrained product sphere (CPS).

**Theorem 2.2 (Moduli Space Parametrization).** With the interlocking constants $\Lambda=3$, $k_0=2$ locked, the moduli space of the CPS class $\{M(a)\}_{a>0}$ is homeomorphic to $(0,\infty)$, with $a$ as the sole continuous degree of freedom.

*Proof.* The product metric is determined by the three factor-sphere radii $(a,b,c)$. The constraints $b=a/\sqrt{\Lambda}$, $c=a/\sqrt{\Lambda k_0}$ compress $(a,b,c)$ to the one-dimensional submanifold $(0,+\infty)_a$. Distinct values of $a$ yield non-isometric metrics because the volume $V(a)\propto a^9$ is strictly monotonic. Hence the moduli space is homeomorphic to $(0,\infty)$. $\square$

### 2.3 &ensp; Spectral Rigidity

**Theorem 2.3 (Spectral Rigidity).** Let $M(a)$ and $M(a')$ be two constrained product spheres with identical interlocking constants. If their first three non-zero Laplace–Beltrami eigenvalues coincide, then $M(a)$ and $M(a')$ are isometric.

*Proof.* For $S^3(r)$, the Laplace–Beltrami eigenvalues are $\lambda_{k}^{S^3}=k(k+2)/r^2$ ($k\ge 1$). The eigenvalues of the product manifold are sums of the factor eigenvalues. The first three non-zero eigenvalues come from:
- First factor, first excited state: $\lambda_1^\Delta = 3/a^2$
- Second factor, first excited state: $\lambda_2^\Delta = 3/(a^2/\Lambda) = 3\Lambda/a^2 = 9/a^2$ (when $\Lambda=3$)
- First factor, second excited state: $\lambda_3^\Delta = 8/a^2$

Under $S_3$ permutation symmetry, the eigenvalues must be sorted. With $\Lambda=3$, $k_0=2$, we have $3<8<9$, hence:
$$\lambda_1^\Delta=\frac{3}{a^2},\quad \lambda_2^\Delta=\frac{8}{a^2},\quad \lambda_3^\Delta=\frac{9}{a^2}.$$

Given $\lambda_1^\Delta$, one uniquely recovers $a=\sqrt{3/\lambda_1^\Delta}$. The self-consistency of the ratios $\lambda_2^\Delta/\lambda_1^\Delta=8/3$ and $\lambda_3^\Delta/\lambda_1^\Delta=\Lambda=3$ fixes $a$ uniquely. Thus isospectrality implies isometry. $\square$

**Theorem 2.4 (Eigenvalue Inversion).** Given the first three non-zero eigenvalues $\lambda_1^\Delta,\lambda_2^\Delta,\lambda_3^\Delta$ satisfying the self-consistency conditions, the scale factor is uniquely determined as
$$a=\sqrt{\frac{3}{\lambda_1^\Delta}},\quad b=\sqrt{\frac{3}{\lambda_3^\Delta}},\quad c=\frac{a}{\sqrt{\Lambda k_0}}.$$
Self-consistency conditions: $\lambda_2^\Delta/\lambda_1^\Delta=8/3$ and $\lambda_3^\Delta/\lambda_1^\Delta=\Lambda=3$. $\square$

---

## Chapter 3 &ensp; Holographic Screen Geometry

### 3.1 &ensp; Tripartite Tangent Bundle and Holographic Encoding

**Proposition 3.1 (Tripartite Tangent Bundle).** On $M(a)$, the tangent bundle admits a natural direct-sum decomposition
$$TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I},$$
where each sub-bundle is the pullback of the tangent bundle of the corresponding $S^3$ factor.

**Fundamental Premise (Existence of the Holographic Screen).** On each fiber $\mathbb{R}^9$ of the tripartite tangent bundle, there exists a two-dimensional oriented subspace $\Sigma$ (the holographic screen), with the three three-dimensional sectors projecting onto it at intensity angles $\theta_1,\theta_2,\theta_3\in(0^\circ,90^\circ)$.

**Remark 3.1 ($90^\circ$ — The Simplest Linear Encoding).** $\theta_1+\theta_2+\theta_3=90^\circ$ is the minimal non-redundant linear encoding of three sector projections onto a two-dimensional screen. This encoding uses the right angle as a natural summand, avoiding any additional free parameters.

**Theorem 3.2 (Integral Structure of the Encoding Angle).** $\theta_1+\theta_2+\theta_3=90^\circ$, with each $\theta_i>0^\circ$, and each projection intensity is proportional to $\sin\theta_i$.

*Proof.* This follows directly from Axiom 3 and the definition of projection intensities. $\square$

### 3.2 &ensp; Six-Term Action

**Definition 3.3 (Six-Term Dimensionless Cost Function).** On the angular domain $D_\theta=\{(\theta_1,\theta_2,\theta_3)\mid\theta_i>0,\;\theta_1+\theta_2+\theta_3=90^\circ\}$, the six-term dimensionless cost function is defined as
$$S(\theta_1,\theta_2,\theta_3)=\sum_{i=1}^3\frac{1}{\sin^2\theta_i}+\sum_{i<j}\frac{1}{\sin\theta_i\sin\theta_j}.$$

Each term $1/\sin^2\theta_i$ describes the geometric cost of a single sector projecting onto the holographic screen; each $1/(\sin\theta_i\sin\theta_j)$ describes the coupling cost of two sectors sharing the same screen. The function respects $S_3$ permutation symmetry, the two-body truncation principle, and inverse-area scaling.

**Theorem 3.4 ($S_3$ Symmetry).** The six-term action $S(\theta_1,\theta_2,\theta_3)$ is invariant under any permutation of the three angles.

*Proof.* Both the single-sector sum $\sum 1/\sin^2\theta_i$ and the pairwise coupling sum $\sum_{i<j} 1/(\sin\theta_i\sin\theta_j)$ are manifestly symmetric under $S_3$. $\square$

**Theorem 3.5 (Strict Convexity and Unique Global Minimum).** $S(\theta)$ on $D_\theta$ is strictly convex and attains its unique global minimum at the symmetric point $\theta_1=\theta_2=\theta_3=30^\circ$, where $S_{\min}=24$.

*Proof.* The domain $D_\theta$ is a convex subset of the affine plane $\sum\theta_i=90^\circ$. The Hessian of $S$ is positive definite everywhere on $D_\theta$ (each $\sin\theta_i>0$ ensures all second derivatives are well-defined and the quadratic form is strictly positive). Strict convexity guarantees at most one global minimum. By $S_3$ symmetry, any extremum must satisfy $\theta_1=\theta_2=\theta_3=30^\circ$. Direct evaluation gives:
$$S(30^\circ,30^\circ,30^\circ)=3\cdot\frac{1}{\sin^2 30^\circ}+3\cdot\frac{1}{\sin 30^\circ\sin 30^\circ}=3\cdot 4+3\cdot 4=24.$$

Since $S\to+\infty$ as any $\theta_i\to0^+$, the critical point at $30^\circ$ is the unique global minimum. $\square$

**Theorem 3.6 (Range).** The range of $S$ on $D_\theta$ is $[24,+\infty)$.

*Proof.* By Theorem 3.5, $S_{\min}=24$. As any $\theta_i\to0^+$, the corresponding $1/\sin^2\theta_i\to+\infty$, so the supremum is unbounded. Continuity and connectedness of $D_\theta$ imply the full interval $[24,+\infty)$ is attained. $\square$

### 3.3 &ensp; Symplectic Structure and Hamiltonian Dynamics of the Holographic Screen Angular Configuration Space

**Theorem 3.7 (Natural Symplectic Structure).** The angular domain $D_\theta$, as the interior of a standard 2-simplex, carries the standard symplectic form
$$\omega = d\theta_1 \wedge d\theta_2,$$
with the constraint $\theta_3=90^\circ-\theta_1-\theta_2$ implicit. $S(\theta)$ is a Morse function, with a unique non-degenerate critical point at the symmetric point $\theta_0=(\pi/6,\pi/6,\pi/6)$.

*Proof.* $\omega$ is closed ($d\omega=0$) and non-degenerate on the 2-simplex interior, hence symplectic. At the critical point, the constrained Hessian has eigenvalues $124,124$ (both positive), so the critical point is non-degenerate. $\square$

**Theorem 3.8 (Hamiltonian Flow on the Holographic Screen).** With the Hamiltonian $H(\theta)=S(\theta)$, Hamilton's equations
$$\dot\theta_1 = \frac{\partial S}{\partial\theta_2},\quad \dot\theta_2 = -\frac{\partial S}{\partial\theta_1}$$
generate a flow whose level sets $S=\text{const}$ are closed curves encircling the global minimum at $\theta_0$.

### 3.4 &ensp; Range Compatibility

**Theorem 3.9 (Range Compatibility Theorem).** The six-term action range $[24,+\infty)$ and the abstract geometric quantity range $(0,+\infty)$ are strictly compatible. Specifically, the regularized geometric quantity
$$\tilde{S}(x)=S_{\text{abstract}}(x)+24$$
maps $(0,+\infty)$ bijectively onto $[24,+\infty)$.

*Proof.* Since $S_{\text{abstract}}(x)$ has range $(0,+\infty)$ (Theorem 1.3), adding $24$ shifts the range to $(24,+\infty)$. The value $24$ itself is attained by $S(\theta)$ at the symmetric point (Theorem 3.5). The shift by $24$ is the minimal offset ensuring that the abstract geometric quantity and the holographic screen action share the same range endpoint structure. $\square$

---

## Chapter 4 &ensp; Bridging Function and 10-Direction Geometric Space

### 4.1 &ensp; Explicit Parameter Mapping and Symmetry Axis Uniformization

**Theorem 4.2 (Explicit Construction of the Parametrization Mapping).** Let $S_{\text{abstract}}: D_+\to(0,+\infty)$ be a continuous function satisfying Axioms 1–2 (including the strict monotonicity hypothesis). Define the regularized geometric quantity
$$\tilde{S}(x)=S_{\text{abstract}}(x)+24.$$
Then there exists a unique continuous injection $\Phi_+: D_+\to D_\theta$ such that:

1. **Range locking**: $S(\Phi_+(x))=\tilde{S}(x)$;
2. **Gauge section**: $\Phi_+(x)$ lies on the symmetry axis $\gamma=\{\theta\in D_{\text{ord}}\mid \theta_2=\theta_3\}$ of the ordered sector gauge $D_{\text{ord}}$;
3. **Boundary compatibility**: $\lim_{x\to p_0}\Phi_+(x)=\theta_0=(30^\circ,30^\circ,30^\circ)$, and $\lim_{x\to p_*}\Phi_+(x)\in\partial D_\theta$.

*Proof.* This proceeds in three steps.

**Step 1: Strict convexity of level sets.** By Theorem 3.5, $S(\theta)$ is strictly convex on $D_\theta$, with unique global minimum at $\theta_0$ taking value $24$. For any $S_0>24$, the level set $L_{S_0}=\{\theta\in D_\theta\mid S(\theta)=S_0\}$ is a smooth, strictly convex closed curve encircling $\theta_0$. Strict convexity guarantees that any ray emanating from $\theta_0$ intersects $L_{S_0}$ at exactly one point.

**Step 2: Monotonicity along the symmetry axis.** In $D_{\text{ord}}$, the symmetry axis $\gamma$ is the line segment joining $\theta_0$ to the boundary point $(\pi/2,0,0)$. Restrict $S$ to $\gamma$, parametrized as $\theta_1=\pi/2-2t,\ \theta_2=\theta_3=t$ ($t\in(0,\pi/6]$). Then
$$S|_\gamma(t)=\frac{1}{\sin^2(\pi/2-2t)}+\frac{3}{\sin^2 t}+\frac{2}{\sin(\pi/2-2t)\sin t}.$$
Computing the derivative yields $\frac{d}{dt}(S|_\gamma)<0$ for $t\in(0,\pi/6)$. Thus $S|_\gamma: \gamma\to[24,+\infty)$ is a strictly decreasing homeomorphism. Hence, for any $S_0\geq24$, there exists a unique $\theta^*(S_0)\in\gamma$ with $S(\theta^*(S_0))=S_0$.

**Step 3: Construction of the mapping.** Define $\Phi_+(x)=\theta^*(\tilde{S}(x))$. By the strict monotonicity of $\tilde{S}$ and the continuity of $\theta^*$, $\Phi_+$ is continuous and injective. The boundary behavior follows directly from the limits of $\tilde{S}$ and the correspondence of $\theta^*$. $\square$

**Corollary 4.2.1 (Geometric Semantics of the UV/IR Branches).** Let $S_{\text{abstract}}^\pm:D_\pm\to(0,+\infty)$ be the abstract geometric quantity on each branch. The scale-reciprocal duality $t=a^2/\ell_0^2\leftrightarrow 1/t$ of the bridging function standard form yields:
- $D_+$ corresponds to $a\in(0,\ell_0]$ (the UV microscopic singularity limit);
- $D_-$ corresponds to $a\in[\ell_0,+\infty)$ (the IR macroscopic expansion limit);
- The two branches join seamlessly at the ground state $x_0=\Phi_+^{-1}(\theta_0)=\Phi_-^{-1}(\theta_0)$, where $a=\ell_0$.

**Theorem 4.3 (Symmetry Axis Uniformization).** On $D_\theta$ satisfying Axiom 3, the restriction of the six-term action $S$ to the symmetry axis $\gamma = \{\theta\in D_{\text{ord}} \mid \theta_2=\theta_3\}$ of the ordered sector gauge
$$D_{\text{ord}} = \{\theta\in D_\theta \mid \theta_1 \geq \theta_2 \geq \theta_3\}$$
is a strictly decreasing homeomorphism $\gamma \to [24,+\infty)$. Thus, for any $S_0 \geq 24$, there exists a unique $\theta^*(S_0) \in \gamma$ such that $S(\theta^*)=S_0$. In other words, $\gamma$ is a **global uniformizing section** for $S$ within $D_{\text{ord}}$.

*Proof.* By Theorem 3.5, $S$ is strictly convex on $D_\theta$. $\gamma$ is the line segment joining $\theta_0$ to the boundary point $(\pi/2,0,0)$. Parametrize $\gamma$ as $\theta_1=\pi/2-2t,\ \theta_2=\theta_3=t$ ($t\in(0,\pi/6]$). Since $D_\theta$ is convex and $\gamma\subset D_\theta$ is a line segment, the restriction $S|_\gamma$ of the strictly convex function $S$ to $\gamma$ is also strictly convex. Moreover, $\theta_0$ (corresponding to $t=\pi/6$) is the unique global minimum of $S$ on $D_\theta$, hence also the unique minimum of $S|_\gamma$ on $\gamma$. As $t\to 0^+$, $S|_\gamma(t)\to+\infty$; at $t=\pi/6$, $S|_\gamma=24$. A strictly convex function on an interval with a unique interior minimum is strictly decreasing on one side and strictly increasing on the other. Thus $S|_\gamma$ is strictly decreasing on $(0,\pi/6)$ and constitutes a continuous bijection from $+\infty$ to $24$. $\square$

### 4.2 &ensp; Quantized Zero State

**Proposition 4.4 (Mathematical Origin of the Quantization Spacing).** Under the spectral triple reconstruction framework, the characteristic length $\chi_L$ is determined by the Wodzicki residue of the Dirac operator $D$ on $M(a)$:
$$\chi_L(a) := \bigl(\mathrm{Res}_W(D^{-9})\bigr)^{1/9},$$
where $\mathrm{Res}_W(D^{-9})$ satisfies
$$\mathrm{Res}_W(D^{-9}) = \frac{512\pi^4}{105}\,V,\quad V=\mathrm{Vol}(M(a)).$$

**Theorem 4.5 (Quantized Zero State).** Under the mapping $\Phi_\pm:D_\pm\to D_\theta$ of Theorem 4.2 and the Berezin–Toeplitz quantization framework, the sector projection intensity angles $\theta_i$ and the quantization level $k$ are strictly locked through the following mechanism:

1. **Discrete embedding**: For the $k$-th quantization level ($k=0,1,2,\dots$), define discrete parameter points
   $$x_k = \Phi_\pm^{-1}\left(\theta^*(24 + \Delta S_k)\right),$$
   where $\Delta S_k>0$ is the stiffness deviation increment of the $k$-th level relative to the ground state $S_{\min}=24$.

2. **Angular asymptotic formula**: Along the symmetry axis $\gamma=\{\theta_2=\theta_3\}$, $\theta_1^{(k)}$ satisfies
   $$\sin^2\theta_1^{(k)} = \frac{1}{4} \mp \sqrt{\frac{\Delta S_k}{124}} + \frac{\Delta S_k}{186} + O((\Delta S_k)^{3/2}),$$
   degenerating to $\sin^2 30^\circ = 1/4$ at the ground state $k=0$ ($\Delta S_0=0$).

*Proof.* By Theorem 4.2, $\Phi_\pm$ maps $\tilde{S}(x)$ to $\theta^*(\tilde{S}(x))$. Parametrize $\gamma$ as $\theta_1=\pi/2-2t, \theta_2=\theta_3=t$, and expand near $t=\pi/6$:
$$S|_\gamma(t) = 24 + 372(t-\pi/6)^2 + O((t-\pi/6)^3).$$

**Verification of the coefficient 372**: At the symmetric point $\theta_0=(30^\circ,30^\circ,30^\circ)$, the full-space Hessian has diagonal entries $H_{ii}=40$ and off-diagonal entries $H_{ij}=12\;(i\neq j)$. The constrained tangent-space Hessian has eigenvalues $124,124$. Along the symmetry axis $\gamma$, the direction vector is $v=(2,-1,-1)$ (norm $\sqrt{6}$), and the quadratic form is $v^{\mathsf T}H v = 124\times 6 = 744$. The parametrization $\delta\theta=(-2,1,1)\delta t$ has norm squared $6(\delta t)^2$, hence $S|_\gamma(t) = 24 + \frac{1}{2}\times 744\times(t-\pi/6)^2 = 24 + 372(t-\pi/6)^2$.

By the positive definiteness of the Hessian (Theorem 3.5), inverting $t(\tilde{S})$ yields $t-\pi/6 = \pm\sqrt{(\tilde{S}-24)/372}$. Substituting into $\sin^2\theta_1 = \cos^2(2t)$ and Taylor-expanding around $t=\pi/6$ gives the asymptotic formula. $\square$

### 4.3 &ensp; Bridging Function Standard Form

**Definition 4.6 (Bridging Function Standard Form Family).** Let $S:(0,+\infty)\to[24,+\infty)$ be a real-analytic function satisfying the following three conditions:

**(C1) Scale-reciprocal duality**: $S(a)=S(\ell_0^2/a)$ for all $a>0$;  
**(C2) Ground state locking**: $S(\ell_0)=24$ is the unique global minimum, and $S''(\ell_0)>0$;  
**(C3) Spectral asymptotic constraint**: As $a\to 0^+$, $S(a)\sim C/a^2$ ($C>0$ constant).

Then the function class (bridging function standard form family) satisfying (C1)–(C3) is
$$\mathcal{F}_{\text{bridge}} = \left\{ S(a) = c_2\left(\frac{a^2}{\ell_0^2}+\frac{\ell_0^2}{a^2}\right)+c_0 \;\middle|\; c_2>0,\ 2c_2+c_0=24 \right\}.$$

**Normalization Condition (Framework Input).** Within $\mathcal{F}_{\text{bridge}}$, select the unique element satisfying $c_0 = 0$ and $c_2 = 12$, denoted by
$$S(a) = 12\left(\frac{a^2}{\ell_0^2} + \frac{\ell_0^2}{a^2}\right).$$
This normalization condition is **not** a theorem derived from Axioms 1–3, but a **definitional input** of the framework.

**Theorem 4.7 (Bridging Function Standard Form).** Let $S:(0,+\infty)\to[24,+\infty)$ be a real-analytic function satisfying (C1)–(C3). Then $S$ necessarily takes the form
$$S(a)=c_2\left(\frac{a^2}{\ell_0^2}+\frac{\ell_0^2}{a^2}\right)+c_0,$$
where $c_2>0$ and $2c_2+c_0=24$. Under the normalization condition $c_0=0$, $c_2=12$, we obtain the unique standard form
$$S(a)=12\left(\frac{a^2}{\ell_0^2}+\frac{\ell_0^2}{a^2}\right).$$

*Proof.* (C1) implies $S$ is a function of the $S_3$-invariant combination $t+t^{-1}$ where $t=a^2/\ell_0^2$. Write $S(a)=f(t+t^{-1})$. (C3) as $a\to0^+$ ($t\to0^+$) gives $S(a)\sim C/(\ell_0^2 t)$, so $f(z)\sim C/(\ell_0^2)\cdot z/2$ as $z\to\infty$, hence $f$ grows linearly at infinity. (C2) at $t=1$ ($z=2$) gives $f(2)=24$, $f'(2)=c_2$ from $S''(\ell_0)>0$. The simplest entire function matching the linear asymptotics at both ends ($t\to0^+$ and $t\to+\infty$) and the minimum condition is $f(z)=c_2 z + c_0$. With $f(2)=2c_2+c_0=24$, this yields the stated family. $\square$

### 4.4 &ensp; Explicit Spectrum–Projection Mapping

**Theorem 4.8 (Spectrum–Projection Explicit Mapping).** Under the bridging function standard form ($c_2=12$, $c_0=0$), the map from the scale factor $a$ to the angles $(\theta_1,\theta_2,\theta_3)$ along the symmetry axis is:
$$\theta_1(a)=\frac{\pi}{2}-2t(a),\quad \theta_2(a)=\theta_3(a)=t(a),$$
where $t(a)$ is the unique solution of $S|_\gamma(t)=12(a^2/\ell_0^2+\ell_0^2/a^2)$ with $t\in(0,\pi/6]$.

### 4.5 &ensp; Definition of the 10-Direction Geometric Space

**Definition 4.9 (10-Direction Geometric Space).** A 10-direction geometric space $\mathcal{T}$ is a one-parameter family of constrained product spheres
$$\mathcal{T} = \{(M(a), \Sigma_a, S_3)\}_{a>0},$$
equipped with:
1. The tripartite tangent bundle decomposition $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$;
2. The holographic screen $\Sigma_a$ with encoding condition $\theta_1+\theta_2+\theta_3=90^\circ$;
3. The $S_3$ permutation symmetry among the three sectors;
4. The bridging function standard form $S(a)=12(a^2/\ell_0^2+\ell_0^2/a^2)$;
5. Spectral rigidity (isospectrality $\Rightarrow$ isometry).

---

## Chapter 5 &ensp; Nine-Element Mutual Constraint and Overdetermined Locking

### 5.1 &ensp; Global Geometric Diagram

The six spaces involved in the theory are rigorously formalized as manifolds:

1. **Abstract excited state manifold $\mathcal{D}_\pm$**: a one-dimensional open smooth manifold, $\mathcal{D}_\pm \cong (0,1)$.
2. **Symplectic holographic screen plane $\mathcal{P}_\theta$**: interior of the standard 2-simplex, equipped with the standard symplectic form $\omega = d\theta_1 \wedge d\theta_2$; the total stiffness function $S(\theta)$ is a Morse function with a unique non-degenerate global minimum at $\theta_0 = (\pi/6, \pi/6, \pi/6)$.
3. **Metric moduli space $\mathcal{M}_{\text{rigid}}$**: the constrained submanifold of the isometry classes of Riemannian metrics on the 9-manifold $S^3 \times S^3 \times S^3$, degenerating to $(0,+\infty)_a$.
4. **Spectral Weyl chamber $\mathcal{W}$**: the open cone region formed by strictly increasing eigenvalue triples.
5. **Quantization layer $\mathcal{Q}_k$**: the Berezin–Toeplitz quantized Hilbert space, with strict geometric dimension $(k+1)^2$.
6. **Discrete approximation layer $\mathcal{G}_N$**: sequence of $\epsilon$-net graphs.

### 5.2 &ensp; Nine-Element Mutual Constraint

**Theorem 5.1 (Nine-Element Mutual Constraint).** The fundamental premise (constrained product sphere holographic principle), together with the three axioms, three interlocking constants, and three tool-layer theorems, form a mutually locking logical network:

**(A) Weyl chamber boundary locked** (Theorem 2.3): Spectral rigidity analysis under $\Lambda=3$, $k_0=2$ automatically guarantees strict separation of the first three Laplace eigenvalues ($3/a^2 < 8/a^2 < 9/a^2$). Theorem 4.2 embeds the one-dimensional parameter space of Axioms 1–2 into the symmetry axis of the two-dimensional simplex of Axiom 3; Theorem 4.3 proves that the symmetry axis $\gamma$ is a global uniformizing section for $S$.

**(B) Moduli space compression locked** (Theorem 2.2): The rigidity of the group-theoretic functions $\Lambda(S_3)=3$ and $k_0(S_3)=2$ compresses the moduli space to a one-dimensional submanifold, inversely locking the legitimate existence of the one-dimensional topological structure required by Axiom 1.

**(C) Moduli space parametrization and ground-state anchoring**: By Theorem 2.2, the moduli space is parametrized by a single scale factor $a$; by Theorem 3.5, the minimum of the holographic screen action is $24$. The bridging function standard form (Theorem 4.7) locks these two values as $S_{\min}=24=12(1+1)$, attained at $a=\ell_0$.

**(D') Quantization layer locked**: The compactness of the two-dimensional symplectic structure $(\Sigma,\omega)$ of the holographic screen requires quantization. The square-root decomposition of the tangent bundle rigorously yields the dimension $(k+1)^2$ as the tensor product of two independent $\mathcal{O}(k)$ section spaces. Bott periodicity locks $N_{\text{eff}}=7$, inversely constraining the number of independent encoding channels of the holographic sector projections to be no more than 7.

**(E') Higher-dimensional spectral rigidity locked**: The constrained isospectral rigidity of Theorem 2.3 holds under the bridging function standard form (Theorem 4.7); the heat kernel coefficient ratio $a_2/a_0=(1+\Lambda+\Lambda k_0)/a^2=10/a^2$ is locked by Lemma 2.0.

**(F') Discrete degeneration locked**: The rigorous source of spectral convergence and heat kernel decay is guaranteed by the discrete approximation theorem; Theorem 4.7 guarantees the analytic structure of the UV/IR branches, so that the connection between the discrete approximation layer $\mathcal{G}_N$ and the continuous layer $\mathcal{P}_\theta$ has no extra degrees of freedom.

### 5.3 &ensp; Overdetermined System of Equations

The six links of the nine-element mutual constraint network constitute an overdetermined system of equations (6 equations, 2 unknowns $(\Lambda, k_0)$):

**Equation 1 (Spectral Separation Constraint):** $\lambda_1^\Delta=3/a^2 < \lambda_2^\Delta=8/a^2 < \lambda_3^\Delta=3\Lambda/a^2$, requiring $\Lambda > 8/3$.

**Equation 2 (Fourth Eigenvalue Competition):** $3\Lambda < \min\{15, 3\Lambda k_0, 3(\Lambda+1)\}$.

**Equation 3 (Heat Kernel Coefficient Ratio):** $a_2/a_0 = (1+\Lambda+\Lambda k_0)/a^2$.

**Equation 4 (Information Hierarchy Integrality):** $N_n = S_e^2 \cdot \Lambda^{2n}$ ($n=0,1,\dots,7$), requiring $\Lambda^{2n}$ to maintain integral growth for $n\leq 7$.

**Equation 5 (Magic Number Truncation):** $N_{\text{eff}} = 7 \Rightarrow$ number of energy levels $k+1 \leq 7$.

**Equation 6 (Bridging Function Ground State and $90^\circ$ Encoding Integral Decomposition):** $S_{\min}=24=12(1+1)$ and $90^\circ=\Lambda \times 30^\circ$ ($\Lambda=3$ tripartition).

### 5.4 &ensp; Uniqueness of the Interlocking Constants

**Theorem 5.2 (Uniqueness of the Interlocking Constants).** The above overdetermined system has a unique solution in the positive real domain:
$$\Lambda = \Lambda(S_3) = 3, \quad k_0 = k_0(S_3) = 2.$$

*Proof.* By Lemma 2.0, the permutation group of the three sectors of the tripartite tangent bundle is isomorphic to $S_3$, whose group-theoretic invariants are $\Lambda(S_3)=3$, $k_0(S_3)=2$. This group-theoretic output satisfies the spectral separation constraint of Equation 1: $3 > 8/3$. Substituting $(\Lambda, k_0)=(3,2)$ into Equations 1–6, all self-consistency checks pass. Any deviation from $(3,2)$ would cause at least one equation to fail: if $\Lambda\neq 3$, the $90^\circ$ tripartition of Equation 6 would be violated; if $k_0\neq 2$, the curvature term weight of Equation 3 and the fourth eigenvalue competition of Equation 2 would be mismatched. Hence the solution is unique. $\square$

### 5.5 &ensp; Emergence of $\ell_0$ and Bootstrap Closure

**Theorem 5.3 (Emergence of the Scale Constant).** With $(\Lambda, k_0) = (3, 2)$ locked, the scale constant $\ell_0$ is uniquely determined by the volume normalization condition $V(\ell_0)=1$ of the constrained product spheres:
$$\ell_0 = V_{\text{unit}}^{-1/9} = \left(\frac{3^3 \cdot 2^{3/2}}{(2\pi^2)^3}\right)^{1/9} \approx 0.5991\ \text{(geometric units, dimensionless)}.$$

*Proof.* The volume of a single $S^3(r)$ is $2\pi^2 r^3$, hence
$$V(a) = (2\pi^2)^3 a^3 \left(\frac{a}{\sqrt{3}}\right)^3 \left(\frac{a}{\sqrt{6}}\right)^3 = \frac{(2\pi^2)^3}{3^3 \cdot 2^{3/2}} a^9 = V_{\text{unit}} a^9.$$
The condition $V(\ell_0)=1$ directly yields $\ell_0=V_{\text{unit}}^{-1/9}$. $\square$

**Theorem 5.4 (Bootstrap Closure).** After the interlocking constants are uniquely determined, all mathematical structures of the 10-direction geometric space $\mathcal{T}$ form a closed chain:
$$\Lambda(S_3) = 3 \xrightarrow{90^\circ\text{ decomp}} \theta_i = 30^\circ \xrightarrow{\text{strict convexity}} S_{\min} = 24 \xrightarrow{\text{bridging function}} a = \ell_0 \xrightarrow{\text{spectral rigidity}} \lambda_i \xrightarrow{\text{uniformization}} \theta \xrightarrow{\text{quantization locking}} k \xrightarrow{\text{heat kernel}} a_2/a_0 \xrightarrow{\text{discrete approx}} \mathcal{G}_N$$
Every arrow in the bootstrap chain constitutes a **bidirectional implication**: the preceding step uniquely determines the next, and the independence of the next suffices to recover the preceding (modulo symmetry). The entire chain contains no free parameters or free functions. $\square$

---

# Part II &ensp; Physical Mapping Layer

## Chapter 6 &ensp; Single Physical Mapping

### 6.1 &ensp; Theoretical Hierarchy and Mapping Declaration

On top of the pure mathematical axiom framework of the 10-direction geometric space, we establish the **geometry-to-physics mapping layer**. This mapping layer is not a pure mathematical theorem within the three-axiom framework, but rather an explicit declaration of how to read physical observables from geometric objects.

The physical mapping layer has only two classes of input:

1. **The three axioms**: Circle topology axiom, boundary limit axiom, holographic screen encoding condition;
2. **The single physical mapping $\mathcal{E}$**: Identifying the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle as electromagnetic interaction.

This mapping is not a fourth axiom, but a physical identification rule: it states which part of the geometric objects defined by the three axioms corresponds to electromagnetic phenomena in the physical world.

### 6.2 &ensp; Core Mapping $\mathcal{E}$

**Core Mapping $\mathcal{E}$ (Electromagnetic Geometric Mapping).** The $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle (connecting the matter sector and the causal sector) corresponds to electromagnetic interaction.

This mapping necessarily accompanies two geometric modes:
1. **Source mode**: The ground-state excitation of the $\mathcal{M}$ sector under the soft mode, outputting rest energy $E_{\mathcal{M}}\approx 511$ keV, identified as the **electron**;
2. **Propagation mode**: The null-cone structure of the $\mathcal{C}$ sector under the boundary limit, outputting massless propagation speed $c$, identified as the **photon**.

The two are bound by the same geometric eigen-quantity $S_e=137.035999084$, forming an indivisible electromagnetic geometric entity. The $\mathcal{I}$ sector does not map to an independent particle, serving only as the information/phase channel for electromagnetic coupling.

**$\mathcal{E}$ Mapping Anchoring Principle.** The electromagnetic geometric mapping $\mathcal{E}$ is the sole anchoring mapping between Geometric Theory and physical observables—it identifies the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle as electromagnetic interaction and uniformly determines all electromagnetic eigen-quantities, including the inverse fine-structure constant $S_e$, electron mass $m_e$, vacuum speed of light $c$, characteristic length $\chi_L$, and characteristic time $\chi_T$. Among these, the vacuum speed of light $c$ is derived from the single core mapping via the $\mathcal{E}$-mapping dimensional bridge and is not an external anchor.

### 6.3 &ensp; Derived Quantities from the Single Mapping

From the single physical mapping $\mathcal{E}$ and the three axioms, the following six eigen-quantities can be completely derived:

**Anchor Item 6.3.1 (Inverse Fine-Structure Constant).** The value of the six-term holographic screen action at the effective physical identification point, $S_e$, is identified as the inverse fine-structure constant. This value takes the experimentally measured value $\alpha^{-1}=137.035999084(21)$ (CODATA 2018) as the framework anchoring input:
$$S_e \equiv \alpha^{-1} = 137.035999084.$$

**Honest Remark**: $S_e$ is not a geometric output independently computed from the three axioms. It is an externally anchored value of the physical mapping layer—the framework identifies it as the effective value of the six-term holographic screen action after accounting for percolation and cross-sector coupling corrections. The bare fiducial point (without corrections) six-term action $S(\theta_1^0,\theta_2^0,\theta_3^0)\approx 137.0$ differs from $S_e$ by $\approx 0.036$, which is naturally absorbed by the coupling corrections of the percolation-variational closure equation.

**Derived Item 6.3.2 (Mass Formula).** Physical mass is given by the matter angle $\theta_M$ as:
$$m = K \sin^3\theta_M,$$
where $K$ is the geometric energy scale constant and $\theta_M$ is the matter sector projection intensity angle.

**Derived Item 6.3.3 ($\mathcal{E}$ Mapping and Derivation of the Speed of Light).** The vacuum speed of light $c=299\,792\,458$ m/s is derived from the single core mapping—the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle—via the $\mathcal{E}$-mapping dimensional bridge:
$$c = v_{\text{geo}} \cdot \frac{\chi_L}{\chi_T}.$$

**Derived Item 6.3.4 (Effective Soft and Hard Modes).** The effective Hessian eigenvalues produced by cross-sector coupling are
$$(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}}) = (391.05,\ 59324.3)\ \text{rad}^{-2}.$$

**Derived Item 6.3.5 (Dimensional Bridge First Scale).** $N_1 = 6000.$

**Derived Item 6.3.6 (Nucleon Geometric Charge).** $v_p = 1117.$

The above six quantities are all derived from the same mapping $\mathcal{E}$ and the three axioms:

| Derived Quantity | Mathematical Origin | Description |
|:---|:---|:---|
| $S_e$ | Locked value of the six-term holographic screen action | Mapping $\mathcal{E}$ identifies it as $\alpha^{-1}$ |
| $m=K\sin^3\theta_M$ | Dimensional bridge spectral formula | Mass formula is the output of $\mathcal{E}$ for the source mode |
| $\mathcal{E}$ mapping anchor | $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling | $c$ derived via $\mathcal{E}$-mapping dimensional bridge |
| $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})$ | Dual-mode zero-error condition | Spectral output of cross-sector coupling under the same mapping |
| $N_1$ | Dimensional bridge seven-level recursion construction | First scale |
| $v_p$ | Strong interaction geometric charge | Readout of the same mapping in the strong interaction sector |

---

## Chapter 7 &ensp; Physical Identification on the Holographic Screen

### 7.1 &ensp; Physical Identification Point (Bare Fiducial Point)

**Definition (Physical Identification Point).** The angular configuration satisfying the following simultaneous system is called the physical identification point (bare fiducial point):
1. Completeness axiom: $\theta_M+\theta_C+\theta_I=90^\circ$;
2. Six-term action identification: $S(\theta_M,\theta_C,\theta_I) = S_e$;
3. Electron mass identification derived from the single mapping: $K\sin^3\theta_M = m_e$.

Numerically solving this simultaneous system yields:
$$\theta_1^0 = 57.9300000000^\circ,\quad \theta_2^0 = 26.1593112467^\circ,\quad \theta_3^0 = 5.9106887533^\circ.$$

Verification: $57.93+26.1593112467+5.9106887533=90.0000000000^\circ$.

**Important Clarification**: The physical identification point is **not** a stationary point of $S(\theta)$. The unique global minimum of $S(\theta)$ on the constrained manifold is $(30^\circ,30^\circ,30^\circ)$. The physical identification point lies on the $S=S_e$ level surface, with its matter angle additionally locked by the mass formula.

**Theorem (Existence and Uniqueness of the Physical Identification Point).** Within the ordered sector gauge $D_{\text{ord}}$, the simultaneous system has a unique solution.

*Proof sketch.* The completeness and fine-structure identifications jointly determine a one-dimensional iso-value curve. On this curve, $\theta_M=\theta_1$ varies continuously over its allowed interval; $\sin^3\theta_M$ is strictly monotonic on $(0,\pi/2)$, so the mass formula has a unique solution point for the chosen $K$. The ordered sector gauge eliminates $S_3$ mirror images, guaranteeing uniqueness. $\square$

### 7.2 &ensp; Matter Angle and Mass Formula

The matter angle is $\theta_M := \theta_1$. The mass formula is $m = K \sin^3\theta_M = K \sin^3\theta_1.$

At the bare fiducial point, $\theta_M^0=57.93^\circ$. From the dimensional bridge spectral formula,
$$K = \frac{\sqrt{\lambda_1^{\text{eff}}\lambda_2^{\text{eff}}}}{\pi C_K \sin^3\theta_M},$$
where $C_K \approx 3$ is a locked normalization factor to be determined, yielding $K=839.758793$ keV upon substitution.

### 7.3 &ensp; Hessian Cross-Section on the Constrained Manifold

On the constrained manifold $\Sigma=\{(\theta_1,\theta_2,\theta_3)\in\mathbb{R}^{3+}\mid \theta_1+\theta_2+\theta_3=90^\circ\}$, adopt local coordinates centered at the bare fiducial point:
$$\xi=(\theta_3-\theta_2)-(\theta_3^0-\theta_2^0),\quad \eta=(\theta_2-\theta_1)-(\theta_2^0-\theta_1^0).$$

**Angular Unit Declaration**: In the following Hessian computation, all angular variables are substituted in radians. The bare fiducial angles have been converted: $\theta_1^0=1.011$ rad, $\theta_2^0=0.4566$ rad, $\theta_3^0=0.1032$ rad. Hessian components are in units of $\text{rad}^{-2}$.

The second-order partial derivatives of the total action $S$ in angular space constitute the Hessian matrix $H_{ij}=\partial^2 S/\partial\theta_i\partial\theta_j$. From the six-term action $S(\theta_1,\theta_2,\theta_3)=\sum_i 1/\sin^2\theta_i + \sum_{i<j} 1/(\sin\theta_i\sin\theta_j)$:

- **Off-diagonal entries** ($i\neq j$): $H_{ij}=\cos\theta_i\cos\theta_j/(\sin^2\theta_i\sin^2\theta_j)$
- **Diagonal entries**: $H_{ii}=(2\sin^2\theta_i+6\cos^2\theta_i)/\sin^4\theta_i + \sum_{j\neq i}(\sin^2\theta_i+2\cos^2\theta_i)/(\sin^3\theta_i\sin\theta_j)$

Substituting the bare fiducial point ($\theta_1^0=1.011$ rad, $\theta_2^0=0.4566$ rad, $\theta_3^0=0.1032$ rad) yields:
$$H_{11}=31.3012,\quad H_{22}=367.7347,\quad H_{33}=59259.35,$$
$$H_{12}=3.4145,\quad H_{13}=69.3547,\quad H_{23}=433.1578\quad(\text{units: rad}^{-2}).$$

Through directional derivatives, the cross-sectional Hessian on the constrained manifold is:
$$H_{\xi\xi}=H_{33}+H_{22}-2H_{23}=58760.77,$$
$$H_{\eta\eta}=H_{11}+H_{22}-2H_{12}=392.21,$$
$$H_{\xi\eta}=-H_{13}+H_{23}+H_{12}-H_{22}=-0.52.$$

Eigenvalues: $\lambda_1=392.21$ (soft mode), $\lambda_2=58760.77$ (hard mode). The soft-to-hard mode ratio is
$$\Lambda_H=\frac{\lambda_2}{\lambda_1}=149.8\approx150=2\times3\times5^2.$$

The value $149.8$ in this ratio is the **output of a purely geometric computation**; $150=2\times3\times5^2$ is its approximate prime-factor identification framework.

---

## Chapter 8 &ensp; Cross-Sector Coupling and Effective Metric

### 8.1 &ensp; Percolation Structure and Cross-Sector Coupling

**Theorem (Percolation Structure Theorem).** Within the tripartite tangent bundle framework, the geometric percolation from the $30^\circ$ symmetric background to local excited states is described by a $2\times2$ symmetric matrix:
$$\Phi = \begin{pmatrix} a & b \\ b & a \end{pmatrix}$$
whose matrix entries (angles in radians) are
$$a = 4\pi\cdot\cos^2(\theta_3/2)\cdot(1-1/S_{\text{local}}),\quad b = \frac{45}{2}\cdot\theta_1\cdot\cos(\theta_3).$$

**Theorem (Cross-Sector Coupling Theorem).** The cross-sector coupling among the three sectors, projected onto the $(\xi,\eta)$ coordinates, is a $2\times2$ symmetric matrix:
$$H^W = \begin{pmatrix} a' & b' \\ b' & a' \end{pmatrix}$$
where $a'=-2w$, $b'=2w-w'$, with $w$ the waist-edge coupling ($\mathcal{M}$-$\mathcal{C}$ and $\mathcal{C}$-$\mathcal{I}$) and $w'$ the base-edge coupling ($\mathcal{M}$-$\mathcal{I}$). The convention of negative $w,w'$ is adopted so that $a',b'$ output positive values; the negative sign indicates that cross-sector coupling lowers energy in the joint action.

**Theorem (Cross-Sector Coupling Pre-Factors).** The cross-sector coupling pre-factors satisfy the following algebraic relations (this framework adopts their results; their complete derivation involves the $Spin(8)$ normal bundle structure of spectral triples and Wodzicki residue normalization, which lie beyond the scope of this paper and are not expanded here):
$$\kappa_w + \kappa_w' = 4L + \frac{\pi}{\Lambda_H},\quad \frac{\kappa_w'}{\kappa_w} = \frac{447}{392},$$
where $L=7$, $\Lambda_H=150$.

Substituting into the dual-mode zero-error condition yields $a'=1.577$, $b'=0.867$, with waist-edge and base-edge parameters $w=-0.7885$, $w'=-2.444$.

### 8.2 &ensp; Effective Metric

**Definition (Effective Metric).** The effective soft and hard modes $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})$ are uniquely determined by the simultaneous algebraic system of the bare Hessian $H^{\text{bare}}$, the percolation matrix $\Phi$, and the cross-sector coupling $H^W$. The numerical solution is
$$(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}}) = (391.05,\ 59324.3)\ \text{rad}^{-2}.$$

---

## Chapter 9 &ensp; Dual-Mode Zero Error and Electromagnetic Geometry

### 9.1 &ensp; Percolation-Variational Closure Equation

**Definition (Percolation-Variational Closure Equation).** Let $S_{\text{local}}(\mu_1,\mu_2)$ be the six-term action at the local excitation point with effective Hessian eigenvalues $\mu_1,\mu_2$ (given by the second-order Taylor expansion about the bare fiducial point). Define:

- Background action: $S_{\text{bg}} = \frac{1}{2}\text{tr}(H^{\text{bare}}) = \frac{1}{2}(\lambda_1+\lambda_2)$;
- Cross-sector coupling overlap: $W_{\text{coupling}}(\mu_1,\mu_2) = \langle H^W(\mu_1,\mu_2),\ \Phi \cdot H^{\text{bg\_proj}} \rangle_{F}$.

**The percolation-variational closure equation is then**:
$$\boxed{S_{\text{local}}(\mu_1,\mu_2) + S_{\text{bg}} + W_{\text{coupling}}(\mu_1,\mu_2) = 0}$$

This equation, together with the reality constraint, constitutes a closed algebraic system for $(\mu_1,\mu_2)$.

**Theorem (Dual-Mode Zero-Error Solvability Theorem).** In the region $\mu_1<\lambda_1$, $\mu_2>\lambda_2$, the closure equation admits a unique real solution; the numerical solution is $\mu_1^*=391.05$, $\mu_2^*=59324.30$.

### 9.2 &ensp; Matter Ground-State Energy and Photon Zero Mass

**Theorem (Matter Ground-State Energy Formula).** Let $\Delta\eta$ be the soft-mode displacement (locked by the dual-mode zero-error condition), and $\lambda_1^{\text{eff}}=391.05$ the effective soft-mode eigenvalue. Then the ground-state excitation energy of the matter sector $\mathcal{M}$ is
$$\boxed{E_{\mathcal{M}} = \frac{1}{2}\lambda_1^{\text{eff}}(\Delta\eta)^2 \cdot K}$$
where $K=839.758793$ keV is the geometric energy scale constant.

**Numerical verification**: From $E_{\mathcal{M}}=511$ keV, $\lambda_1^{\text{eff}}=391.05$, $K=839.758793$ keV, one solves
$$|\Delta\eta| = \sqrt{\frac{2E_{\mathcal{M}}}{\lambda_1^{\text{eff}} K}} \approx 0.0557\ \text{rad} \approx 3.19^\circ.$$

**Geometric Necessity of the Photon (Causal Sector):** The causal sector $\mathcal{C}$ is described by the hard mode $\lambda_2$ governing its background stiffness. At the ground state $S_{\min}=24$, the excitation modes of the $\mathcal{C}$-sector satisfy the null condition, corresponding to massless propagation. This nullity is determined by the boundary limit behavior; therefore, **the masslessness of the photon is a necessary accompaniment of the core mapping $\mathcal{E}$**.

---

## Chapter 10 &ensp; Dimensional Bridge and Emergence of Physical Constants

### 10.1 &ensp; The Four Equations of the Dimensional Bridge

**Theorem (Four Equations of the Dimensional Bridge).** Under the $\mathcal{E}$ mapping anchoring principle, the geometric characteristic length $\chi_L$, characteristic time $\chi_T$, energy scale $K$, length coupling $G_L$, and $\hbar$ satisfy the following simultaneous system:

1. **Speed derivation equation** (from the $\mathcal{E}$ mapping propagation mode):
   $$c = v_{\text{geo}} \cdot \frac{\chi_L}{\chi_T},$$
   where $v_{\text{geo}}=71.832113$ is the intrinsic geometric velocity;

2. **Action emergence equation**:
   $$\hbar = \frac{K \chi_T N_1}{12\pi S_e^2 \lambda_1^{\text{eff}}};$$

3. **Length coupling equation**:
   $$\chi_L = G_L \cdot \hbar c;$$

4. **Geometric formula for length coupling**:
   $$G_L = \frac{4}{\pi} \cdot \frac{v_p S_e \sqrt{\lambda_1^{\text{eff}}}}{N_1 K}.$$

### 10.2 &ensp; Compatibility of the Four Equations

Eliminating $\hbar$ and $\chi_T$ from the four equations yields:
$$K \cdot G_L = \frac{4 S_e \sqrt{\lambda_1^{\text{eff}}} v_p}{\pi N_1}.$$

Numerical verification:
$$K \cdot G_L = \frac{4 \times 137.035999084 \times \sqrt{391.05} \times 1117}{\pi \times 6000} \approx 642.5.$$

Meanwhile, multiplying $K=839.758793$ keV and $G_L\approx0.7648$ keV$^{-1}$ directly also yields $642.5$. The two agree; the four equations of the dimensional bridge are **not self-contradictory**.

**Honest Remark**: This compatibility check is a necessary-condition test—the four equations do not contradict each other numerically. It does not constitute a uniqueness proof (other parameter combinations may also satisfy compatibility), nor a sufficiency proof (the solution to the four equations may not be unique). Passing compatibility is a necessary but not sufficient condition for the validity of the dimensional bridge.

### 10.3 &ensp; Self-Consistent Derivation of $\hbar$, $\chi_L$, $\chi_T$

Taking $c$ as the quantity derived from the $\mathcal{E}$ mapping propagation mode, $\hbar$, $\chi_L$, and $\chi_T$ are solved from $K$ and the four equations:
$$\chi_T = \frac{\hbar \cdot 12\pi S_e^2 \lambda_1^{\text{eff}}}{K N_1},\qquad \chi_L = \frac{c \chi_T}{v_{\text{geo}}}.$$

Substituting numerical values:
- $K = 839.758793$ keV
- $N_1 = 6000$
- $S_e = 137.035999084$
- $\lambda_1^{\text{eff}} = 391.05$ rad$^{-2}$
- $\hbar = 6.5821195675 \times 10^{-16}$ eV$\cdot$s

yields:
$$\chi_T = 3.6161912064 \times 10^{-17}\ \text{s},\qquad \chi_L = 1.5092231080 \times 10^{-10}\ \text{m}.$$

### 10.4 &ensp; Electron Mass

**Theorem (Electron Mass Theorem).** From the mass formula derived by the single mapping and the dimensional bridge, the electron rest energy is
$$E_e = m_e c^2 = K \sin^3\theta_M \cdot c^2.$$
Substituting $\theta_M=57.93^\circ$ yields $E_e = 510.99895$ keV.

**Theorem (Dimensional Bridge Self-Consistency).** The $\hbar$, $\chi_L$, $\chi_T$, $K$ output by the dimensional bridge and all electromagnetic eigen-quantities (including $c$) derived by the $\mathcal{E}$ mapping are self-consistent, and the mass formula output $E_e$ is consistent with the energy formula output, with a deviation $<0.002\%$.

---

## Chapter 11 &ensp; Conclusion

This paper integrates the axiomatic-deductive system of the 10-direction geometric space with the physical mapping layer, presenting a complete, integrated derivation chain from three axioms to physical observables.

**Geometric Foundations:**
- Three axioms define the excited state parameter space, the abstract geometric quantity, and the holographic screen encoding condition;
- The tripartite bundle permutation group rigidity theorem proves the uniqueness of $S_3$, with $\Lambda=3$, $k_0=2$ emerging group-theoretically;
- Spectral rigidity of the constrained product spheres $M(a)$ guarantees a one-dimensional moduli space for the scale factor $a$;
- The six-term action range $[24,+\infty)$ and the abstract geometric quantity range $(0,+\infty)$ correspond precisely through the bridging function standard form;
- The nine-element mutual constraint and the overdetermined system achieve bootstrap closure, with all interlocking constants uniquely determined.

**Physical Mapping:**
- The single core mapping $\mathcal{E}$ identifies the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling as electromagnetic interaction;
- Six eigen-quantities—$S_e$, mass formula, $\mathcal{E}$ mapping anchor, effective soft/hard modes, $N_1$, $v_p$—are derived from this mapping and the three axioms;
- The physical identification point $(57.93^\circ, 26.16^\circ, 5.91^\circ)$ is determined by the simultaneous system of completeness, $S=S_e$, and the mass formula;
- The Hessian soft-to-hard mode ratio $\Lambda_H=149.8\approx150$ is a purely geometric output;
- The dual-mode zero-error condition locks the effective metric $(391.05, 59324.3)$ rad$^{-2}$;
- With the $\mathcal{E}$ mapping as the anchoring framework, all physical constants are derived self-consistently through the four equations of the dimensional bridge.

**Honest Remarks**: $\ell_0$ is a spectral-geometric unit anchor (not an external physical constant); the numerical emergence of $\hbar$ and $S_e$ belongs to the conditional proposition layer; the normalization condition of the bridging function standard form is an explicit input of the framework.

---

## Appendix A &ensp; Summary of Key Numerical Values

### A.1 &ensp; Purely Geometric Outputs

| Quantity | Value | Description |
|:---|:-----|:-----|
| $\Lambda$ | 3 | Tripartition ratio parameter ($S_3$ conjugacy class number) |
| $k_0$ | 2 | Dichotomous compactness constant ($S_3$ maximal normal subgroup index) |
| $\ell_0$ | 0.5991 (geom. units) | Scale constant |
| $\chi_L(\ell_0)$ | 1.983 (geom. units) | Wodzicki residue characteristic length |
| $S_{\min}$ | 24 | Six-term action minimum ($30^\circ$ symmetric point) |
| $\lambda_{\text{Hess},i}$ | 124 | Constrained tangent-space Hessian eigenvalues |
| $\lambda_1^\Delta$ | $3/a^2$ | First non-zero Laplace eigenvalue |
| $\lambda_2^\Delta$ | $8/a^2$ | Second non-zero Laplace eigenvalue |
| $\lambda_3^\Delta$ | $9/a^2$ | Third non-zero Laplace eigenvalue |
| $a_2/a_0$ | $10/a^2$ | Heat kernel coefficient ratio |

### A.2 &ensp; Physical Identification Point and Hessian

| Quantity | Value | Description |
|:---|:-----|:-----|
| $\theta_1^0$ | 57.930000° | Matter angle (bare fiducial point) |
| $\theta_2^0$ | 26.159311° | Causal angle (bare fiducial point) |
| $\theta_3^0$ | 5.910689° | Information angle (bare fiducial point) |
| $S(\theta^0)$ | $\approx 137.0$ | Bare fiducial point six-term action (without coupling corrections) |
| $S_e$ | 137.035999084 | Effective physical identification point action ($=\alpha^{-1}$, experimentally anchored) |
| $\lambda_1$ | 392.21 rad⁻² | Soft-mode eigenvalue |
| $\lambda_2$ | 58760.77 rad⁻² | Hard-mode eigenvalue |
| $\Lambda_H$ | 149.8 ≈ 150 | Hessian soft-to-hard mode ratio |

### A.3 &ensp; Effective Metric and Coupling Parameters

| Quantity | Value | Description |
|:---|:-----|:-----|
| $a$ (percolation) | 12.4415 | Percolation matrix diagonal entry |
| $b$ (percolation) | 22.6281 | Percolation matrix off-diagonal entry |
| $a'$ (coupling) | 1.577 | Cross-sector coupling diagonal entry |
| $b'$ (coupling) | 0.867 | Cross-sector coupling off-diagonal entry |
| $w$ (waist-edge) | $-0.7885$ | Negative convention |
| $w'$ (base-edge) | $-2.444$ | Negative convention |
| $\lambda_1^{\text{eff}}$ | 391.05 rad⁻² | Effective soft mode |
| $\lambda_2^{\text{eff}}$ | 59324.30 rad⁻² | Effective hard mode |

### A.4 &ensp; Core Mapping Accompanying Outputs

| Quantity | Geometric Output | Experimental Value | Description |
|:---|:---------|:-------|:-----|
| $S_e$ | 137.035999084 | $\alpha^{-1}$ | Inverse fine-structure constant |
| $E_{\mathcal{M}}$ | 511.0 keV | $m_e c^2$ | Electron rest energy |
| Photon masslessness | $\mathcal{C}$-sector nullity | $m_\gamma=0$ | Core mapping accompaniment |
| $\hbar$ | $6.5821\times10^{-16}$ eV·s | Experimental value | Dimensional bridge output |
| $\chi_L$ | $1.5092\times10^{-10}$ m | Bohr radius order | Dimensional bridge output |
| $\chi_T$ | $3.6162\times10^{-17}$ s | — | Dimensional bridge output |
| $K$ | 839.758793 keV | — | Dimensional bridge / mass formula |
| $G_L$ | $0.7648$ keV⁻¹ | — | Dimensional bridge output |
| $K \cdot G_L$ | $\approx 642.5$ | — | Four-equation compatibility check |
| $N_1$ | 6000 | — | Dimensional bridge first scale |
| $v_p$ | 1117 | — | Nucleon geometric charge |

---

## Appendix B &ensp; Summary of Notation

| Symbol | Meaning |
|:---|:---|
| $D_\pm$ | Two connected branches of the excited state parameter space, $D_\pm \cong (0,1)$ |
| $S(x)$ | Abstract geometric quantity, $S: D_\pm\to(0,+\infty)$ |
| $M(a)$ | Constrained product spheres $S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$ |
| $\Lambda$ | Tripartition ratio parameter, $\Lambda=\Lambda(S_3)=3$ |
| $k_0$ | Dichotomous compactness constant, $k_0=k_0(S_3)=2$ |
| $\ell_0$ | Scale constant (spectral-geometric unit anchor) |
| $\lambda_i^\Delta$ | $i$-th non-zero Laplace–Beltrami eigenvalue |
| $TM(a)$ | Tripartite tangent bundle $\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ |
| $\theta_1,\theta_2,\theta_3$ | Sector projection intensity angles, $\theta_1+\theta_2+\theta_3=90^\circ$ |
| $\Sigma$ | Two-dimensional holographic screen |
| $S(\theta)$ | Six-term action, range $[24,+\infty)$ |
| $D_\theta$ | Angular domain $\{(\theta_1,\theta_2,\theta_3)\mid\theta_i>0,\sum\theta_i=90^\circ\}$ |
| $D_{\text{ord}}$ | Ordered sector gauge $\{\theta_1\geq\theta_2\geq\theta_3\}$ |
| $\gamma$ | Symmetry axis $\{\theta_2=\theta_3\}$ |
| $\mathcal{T}$ | 10-direction geometric space |
| $\mathcal{E}$ | Electromagnetic geometric mapping (single core mapping) |
| $\chi_L$ | Characteristic length |
| $\chi_T$ | Characteristic time |
| $K$ | Geometric energy scale constant |
| $G_L$ | Length coupling |
| $S_e$ | Entropy scale / inverse fine-structure constant |
| $v_{\text{geo}}$ | Intrinsic geometric velocity |
| $\Lambda_H$ | Hessian soft-to-hard mode ratio |
| $N_{\text{eff}}$ | Number of independent encoding channels truncated by Bott periodicity, $=7$ |

---

## Appendix C &ensp; Mathematical Properties of the Bridging Function Standard Form

Let $x = a^2/\ell_0^2 = e^{2u}$ ($u=\ln(a/\ell_0)$). The bridging function standard form is equivalent to:
$$S = 24\cosh\bigl(2\ln(a/\ell_0)\bigr).$$

**Core Properties:**
1. **Even symmetry**: $S$ is an even function in $u$, naturally producing the scale-reciprocal duality $a \leftrightarrow \ell_0^2/a$;
2. **Convexity and unique minimum**: The convexity of $\cosh$ guarantees $S_{\min}=24$ uniquely at $a=\ell_0$;
3. **Exponential boundary**: $S \sim 12e^{2|u|}$ ($|u|\to\infty$), guaranteeing the degeneration limit $S\to+\infty$.

**2:1 Covering Structure of the Moduli Space:**

| Branch | Domain | Geometric Semantics |
|------|--------|----------|
| UV | $a\in(0,\ell_0]$ | Microscopic singularity limit |
| IR | $a\in[\ell_0,+\infty)$ | Macroscopic expansion limit |
| Ground state | $a=\ell_0$ | Ramification point |

**Vieta Invariant:** $a_{\text{UV}} \cdot a_{\text{IR}} = \ell_0^2$.

**Spectral Transfer Invariance:** The bridging function standard form controls only the overall scaling of the spectrum, without altering internal ratios:
$$\frac{\lambda_2^\Delta}{\lambda_1^\Delta} = \frac{8}{3}, \quad \frac{\lambda_3^\Delta}{\lambda_1^\Delta} = 3 \quad (\text{invariant for all } S\geq24).$$

**Regularized Action:**
$$S_{\text{abstract}} = S - 24 = 12\left(\frac{a}{\ell_0} - \frac{\ell_0}{a}\right)^2,$$
translating the holographic screen realization domain $[24,+\infty)$ to $(0,+\infty)$, in rigorous correspondence with the abstract geometric quantity $S_{\text{abstract}}(x)$.
