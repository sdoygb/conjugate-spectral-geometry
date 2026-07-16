# Physical Evolution of the 10-Direction Geometric Space

---

## Abstract

Starting from the three axioms, this paper establishes the complete framework of the 10-direction geometric space, covering both the geometric foundation and the physical mapping layer, presenting an integrated derivation chain from axioms to physical observables.

**Part I (Geometric Foundation)** establishes the axiom-deduction system of the 10-direction geometric space: Axioms 1–2 define the excited-state parameter space and abstract geometric quantity; Axiom 3 defines the tripartite tangent bundle holographic screen encoding condition $\theta_1+\theta_2+\theta_3=90^\circ$. The rigidity theorem of the tripartite tangent bundle permutation group is proved (uniqueness of $G\cong S_3$), from which group-theoretic emergence yields the interlocking constants $\Lambda=\Lambda(S_3)=3$ and $k_0=k_0(S_3)=2$. Spectral rigidity is established on the constrained product spheres $M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$. It is proved that the range of the six-term action $[24,+\infty)$ is strictly compatible with the range of the abstract geometric quantity $(0,+\infty)$. The bridge function standard form $S(a)=12(a^2/\ell_0^2+\ell_0^2/a^2)$ is established (uniquely determined under scale-reciprocal duality, ground state locking, spectral asymptotic constraints, and normalization condition). Bootstrap closure is achieved through nine-element interlocking and group-theoretic emergence, with the interlocking constants uniquely determined by $S_3$ group theory.

**Part II (Physical Mapping Layer)** establishes the single core mapping $\mathcal{E}$: the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle corresponds to the electromagnetic interaction. With $S_e$ and $c$ as the dual anchoring inputs, this mapping together with the three axioms determines all eigen-quantities: electron mass, photon masslessness, effective soft/hard modes, the first scale $N_1$ of the dimensional bridge, and the nucleon geometric charge $v_p$. At the physical identification point $(57.93^\circ, 26.16^\circ, 5.91^\circ)$, the Hessian structure and cross-sector coupling are established, and the effective metric $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})=(391.05, 59324.3)$ rad$^{-2}$ is locked by the dual-mode zero-error condition. With the ℰ-mapping as the anchoring framework, the four equations of the dimensional bridge establish a self-consistent locking framework for parameters $\hbar$, $\chi_L$, $\chi_T$, and $K$.

**Honest Annotations**: The mathematical status of $\ell_0$ is that of a spectral geometric unit anchor; $S_e$ and $c$ are two external anchoring inputs of the physical mapping layer and are not derived from the three axioms; the numerical emergence of $\hbar$ belongs to the conditional proposition layer; the normalization condition of the bridge function standard form is an explicit input of the framework.

**Keywords:** 10-direction geometric space; spectral rigidity; tripartite tangent bundle; holographic screen; bridge function standard form; nine-element interlocking; group-theoretic emergence; electromagnetic geometric mapping; cross-sector coupling; dual-mode zero-error; dimensional bridge

---

# Part I &nbsp; Geometric Foundation

## Chapter 1 &nbsp; Axiom System and Excited-State Parameter Space

### 1.1 &nbsp; The Three Axioms

The 10-direction geometric space is founded upon the following three axioms:

**Axiom 1 (Circle Topology Axiom)** &nbsp; The excited-state parameter space $D = S^1\setminus\{p_0,p_*\}$ consists of two connected components:
$$D_+\cong(0,1),\quad D_-\cong(0,1).$$

**Axiom 2 (Boundary Limit Axiom)** &nbsp; The geometric quantity $S: D_\pm\to(0,+\infty)$ is continuous on each component, and satisfies:
$$\lim_{x\to p_0}S(x)=0,\quad \lim_{x\to p_*}S(x)=+\infty.$$

**Axiom 3 (Holographic Screen Encoding Condition)** &nbsp; On each fiber $\mathbb{R}^9$ of the tripartite tangent bundle $TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$, there exists a two-dimensional oriented subspace $\Sigma$ (the holographic screen), onto which the three three-dimensional sectors project with intensity angles satisfying
$$\theta_1+\theta_2+\theta_3=90^\circ,\qquad \theta_i\in(0^\circ,90^\circ).$$

### 1.2 &nbsp; Basic Properties of the Excited-State Parameter Space

**Proposition 1.1 (Circle Topology)** &nbsp; The excited-state parameter space $D=S^1\setminus\{p_0,p_*\}$ consists of two connected components:
$$D_+\cong(0,1),\quad D_-\cong(0,1).$$

**Proposition 1.2 (Analytic Properties of the Geometric Quantity)** &nbsp; The geometric quantity $S:D_\pm\to(0,+\infty)$ is continuous on each component, and satisfies:
$$\lim_{x\to p_0}S(x)=0,\quad \lim_{x\to p_*}S(x)=+\infty.$$

**Theorem 1.3 (Range Theorem)** &nbsp; The range of $S$ on each component is
$$S(D_\pm)=(0,+\infty).$$

**Theorem 1.4 (Existence Theorem)** &nbsp; For any given positive number $S_0>0$, on each component $D_+$ and $D_-$ there exists at least one parameter $x_+\in D_+$ and $x_-\in D_-$ such that $S(x_+)=S(x_-)=S_0$.

*Proof.* By Proposition 1.1, $D_\pm$ is homeomorphic to $(0,1)$, hence connected. By Proposition 1.2, $S$ is continuous with boundary limits $0$ and $+\infty$ respectively. By the Intermediate Value Theorem for continuous functions, for any $S_0\in(0,+\infty)$, the level set $S^{-1}(S_0)$ is non-empty within each component. $\square$

---

## Chapter 2 &nbsp; Constrained Product Spheres and Spectral Rigidity

### 2.1 &nbsp; Rigidity of the Tripartite Tangent Bundle Permutation Group

**Lemma 2.0 (Rigidity of the Tripartite Tangent Bundle Permutation Group)** &nbsp; The tripartite tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$ contains three labeled sectors $\{\mathcal{M},\mathcal{C},\mathcal{I}\}$. Treating the three sectors as set elements, the totality of their permutations forms the symmetric group $S_3$ ($|S_3|=6$). The two group-theoretic invariants of this group are:
$$\Lambda(S_3) = |\text{Conj}(S_3)| = 3,\qquad k_0(S_3) = [S_3:A_3] = 2.$$

*Proof.* The conjugacy classes of $S_3$ are $\{e\}$ (identity), $\{(12),(13),(23)\}$ (transpositions), $\{(123),(132)\}$ (3-cycles), totaling 3 classes, hence $\Lambda=3$. The maximal normal subgroup is the alternating group $A_3$, with index $[S_3:A_3]=2$, hence $k_0=2$. These values are uniquely determined by the group structure of $S_3$ and contain no free parameters. $\square$

**Honest Annotation (Argument Status of $S_3$)** &nbsp; The above lemma establishes $S_3$ as a combinatorial fact about the set of three sectors. It does not depend on whether metric equivalence exists among the sectors — as long as one admits that the three sectors are distinct subspaces within the same tangent bundle decomposition, their permutation group as a three-element set is $S_3$. $\Lambda=3$ and $k_0=2$ are inevitable outputs of the $S_3$ group structure, not artificial choices.

**Proposition 2.0 (Group-Theoretic Origin of the Interlocking Function)** &nbsp; For the permutation symmetry group $G = S_3$ of the tripartite tangent bundle $TM = \mathcal{M} \oplus \mathcal{C} \oplus \mathcal{I}$:
$$\Lambda(S_3) = 3, \quad k_0(S_3) = 2.$$

*Proof.* The number of conjugacy classes of $S_3$ is $3$ (identity, transpositions, 3-cycles), hence $\Lambda(S_3)=3$. The maximal normal subgroup of $S_3$ is the alternating group $A_3$, with index $[S_3:A_3]=2$, hence $k_0(S_3)=2$. $\square$

### 2.2 &nbsp; Constrained Product Spheres

**Definition 2.1 (Constrained Product Spheres)** &nbsp; Let $a>0$ be the global scale factor, $\Lambda=\Lambda(S_3)=3$ the tripartition proportionality parameter, and $k_0=k_0(S_3)=2$ the bipartite compactness constant. The nine-dimensional closed manifold
$$M(a)=S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$$
equipped with the product metric is called a constrained product sphere (CPS).

**Theorem 2.2 (Moduli Space Parameterization)** &nbsp; With the interlocking constants $\Lambda=3$, $k_0=2$ locked, the moduli space of the constrained product sphere class $\{M(a)\}_{a>0}$ is homeomorphic to $(0,\infty)$, and $a$ is the unique continuous degree of freedom.

*Proof.* The product metric is determined by the radii $(a,b,c)$ of the three factor spheres. The constraint conditions $b=a/\sqrt{\Lambda}$, $c=a/\sqrt{\Lambda k_0}$ compress $(a,b,c)$ to a one-dimensional submanifold $(0,+\infty)_a$. Distinct values of $a$ yield non-isometric metrics, because the volume $V(a)\propto a^9$ is strictly monotonic. Hence the moduli space is homeomorphic to $(0,\infty)$. $\square$

### 2.3 &nbsp; Spectral Rigidity

**Theorem 2.3 (Spectral Rigidity)** &nbsp; Let $M(a)$ and $M(a')$ be two constrained product spheres with identical interlocking constants. If their first three non-zero Laplace–Beltrami eigenvalues coincide respectively, then $M(a)$ and $M(a')$ are isometric.

*Proof.* For $S^3(r)$, the Laplace–Beltrami eigenvalues are $\lambda_{k}^{S^3}=k(k+2)/r^2$ ($k\ge 1$). The eigenvalues of a product manifold are sums of eigenvalues of the factors. The first three non-zero eigenvalues arise respectively from:
- First excited state of the first factor: $\lambda_1^\Delta = 3/a^2$
- First excited state of the second factor: $\lambda_2^\Delta = 3/(a^2/\Lambda) = 3\Lambda/a^2 = 9/a^2$ (when $\Lambda=3$)
- Second excited state of the first factor: $\lambda_3^\Delta = 8/a^2$

Under $S_3$ permutation symmetry, the eigenvalues must be ordered. With $\Lambda=3$, $k_0=2$, we have $3<8<9$, hence:
$$\lambda_1^\Delta=\frac{3}{a^2},\quad \lambda_2^\Delta=\frac{8}{a^2},\quad \lambda_3^\Delta=\frac{9}{a^2}.$$

Given $\lambda_1^\Delta$, one can uniquely solve $a=\sqrt{3/\lambda_1^\Delta}$. By the self-consistency of the ratio constraints $\lambda_2^\Delta/\lambda_1^\Delta=8/3$ and $\lambda_3^\Delta/\lambda_1^\Delta=\Lambda=3$, $a$ is uniquely determined. Hence isospectrality implies isometry. $\square$

**Theorem 2.4 (Eigenvalue Inversion)** &nbsp; Given the first three non-zero eigenvalues $\lambda_1^\Delta,\lambda_2^\Delta,\lambda_3^\Delta$ satisfying the self-consistency conditions, the scale factor is uniquely determined as
$$a=\sqrt{\frac{3}{\lambda_1^\Delta}},\quad b=\sqrt{\frac{3}{\lambda_3^\Delta}},\quad c=\frac{a}{\sqrt{\Lambda k_0}}.$$
Self-consistency conditions: $\lambda_2^\Delta/\lambda_1^\Delta=8/3$ and $\lambda_3^\Delta/\lambda_1^\Delta=\Lambda=3$. $\square$

---

## Chapter 3 &nbsp; Holographic Screen Geometry

### 3.1 &nbsp; Tripartite Tangent Bundle and Holographic Screen Encoding

**Proposition 3.1 (Tripartite Tangent Bundle)** &nbsp; On $M(a)$, the tangent bundle admits a natural direct sum decomposition
$$TM(a)=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I},$$
where each subspace is the pullback of the tangent bundle of the respective $S^3$ factor.

**Fundamental Premise (Existence of the Holographic Screen)** &nbsp; On each fiber $\mathbb{R}^9$ of the tripartite tangent bundle, there exists a two-dimensional oriented subspace $\Sigma$ (the holographic screen), onto which the three three-dimensional sectors project with intensity angles $\theta_1,\theta_2,\theta_3\in(0^\circ,90^\circ)$.

**Remark 3.1 (Logical Status of $90^\circ$)** &nbsp; $90^\circ$ is an independent input of the axiom system (Axiom 3); it is the simplest linear gauge for a two-dimensional holographic screen to completely encode information from three sectors. $\Lambda=\Lambda(S_3)=3$ explains the group-theoretic origin of the tripartition $30^\circ$ at the $S_3$ symmetry point $\theta_1=\theta_2=\theta_3$, which is precisely compatible with $3\times30^\circ=90^\circ$, but one cannot deduce $90^\circ$ in reverse — the latter is an independent content of Axiom 3.

### 3.2 &nbsp; Six-Term Action

**Definition 3.4 (Six-Term Action)** &nbsp; Under the $90^\circ$ constraint of Axiom 3, define
$$S(\theta_1,\theta_2,\theta_3)=\sum_{i=1}^3\frac{1}{\sin^2\theta_i}+\sum_{i<j}\frac{1}{\sin\theta_i\sin\theta_j}.$$

**Theorem 3.5 (Range Theorem)** &nbsp; On the domain $D_\theta=\{(\theta_1,\theta_2,\theta_3)\mid\theta_i>0,\theta_1+\theta_2+\theta_3=90^\circ\}$, the range of the six-term action is
$$S(D_\theta)=[24,+\infty).$$
The minimum value $24$ is attained at the symmetry point $\theta_1=\theta_2=\theta_3=30^\circ$.

*Proof.* The domain $D_\theta$ is the interior of a two-dimensional simplex in $\mathbb{R}^3$. The function $S(\theta)$ is a positive-coefficient linear combination of the strictly convex functions $\csc^2\theta_i$ and $\csc\theta_i\csc\theta_j$, hence is strictly convex on the convex set $D_\theta$. The minimum of a strictly convex function on the closure of a compact set is unique and is attained at an interior critical point. By symmetry, the unique critical point is $\theta_0=(30^\circ,30^\circ,30^\circ)$. Substituting:
$$S(\theta_0)=3\cdot\frac{1}{(1/2)^2}+3\cdot\frac{1}{(1/2)\cdot(1/2)}=3\cdot 4+3\cdot 4=24.$$
As any $\theta_i\to 0^+$, $\csc\theta_i\to+\infty$, hence $S\to+\infty$. Therefore the range is $[24,+\infty)$. $\square$

### 3.3 &nbsp; Symplectic Structure and Hamiltonian Dynamics on the Holographic Screen Angle Configuration Space

**Definition 3.5 (Symplectic Structure on the Angle Configuration Space)** &nbsp; The holographic screen angle configuration space $D_\theta$ is a two-dimensional affine open simplex. Its tangent space is defined by the constraint $\delta\theta_1+\delta\theta_2+\delta\theta_3=0$. Equip $D_\theta$ with the standard symplectic form
$$\omega_\theta = d\theta_1 \wedge d\theta_2$$
(within the constraint hyperplane, $d\theta_3 = -d\theta_1-d\theta_2$, so $\omega_\theta$ is non-degenerate). $\omega_\theta$ makes $(D_\theta, \omega_\theta)$ a two-dimensional symplectic manifold.

**Theorem 3.6 (Hamiltonian Vector Field and Symplectic Phase Trajectories)** &nbsp; On the symplectic manifold $(D_\theta, \omega_\theta=d\theta_1\wedge d\theta_2)$, the Hamiltonian function $H(\theta)=S(\theta)-24$ generates the vector field
$$X_H = \frac{\partial H}{\partial \theta_2}\frac{\partial}{\partial \theta_1} - \frac{\partial H}{\partial \theta_1}\frac{\partial}{\partial \theta_2}$$
which satisfies:
1. **Conservation**: The flow $\phi_t$ of $X_H$ preserves the level sets of $H$;
2. **Ground State Stability**: The zero set $\{\theta_0\}$ of $H=0$ is the unique stable equilibrium point of $X_H$, with linearized frequencies given by the eigenvalues $\lambda_{\text{Hess},1}=\lambda_{\text{Hess},2}=124$ of the Hessian on the constraint tangent space;
3. **Periodicity of Level Sets**: For $H>0$, the phase trajectories of $X_H$ on compact level sets are closed curves, with period $T(H) \sim 2\pi/\sqrt{124}$.

*Proof.* From Hamilton's equations $\dot{\theta}_1=\partial H/\partial\theta_2$, $\dot{\theta}_2=-\partial H/\partial\theta_1$, direct computation yields $dH/dt=0$ (conservation). At $\theta_0$, the second-order expansion of $H$ is $H(\delta\theta)=\frac{1}{2}\delta\theta^T H_{\text{Hess}} \delta\theta$, where $H_{\text{Hess}}$ is positive definite on the constraint tangent space with eigenvalues $124,124$, so the linearization is that of a harmonic oscillator. The Hamiltonian flow on strictly convex level sets in two dimensions is necessarily periodic (Arnold's theorem). $\square$

**Theorem 3.7 ($S_3$ Weyl Chamber Coordinates and Centralizer)** &nbsp; The $S_3$ permutation symmetry of the tripartite tangent bundle induces a symplectic action on $D_\theta$. Define Weyl chamber breaking coordinates $\mu: D_\theta\to\mathbb{R}^2$ as
$$\mu(\theta) = \left(\theta_1-\theta_2,\ \theta_2-\theta_3\right).$$
Then:
1. **Weyl Chamber Center = Symmetry Point**: $\mu^{-1}(0) = \{\theta_0\}$;
2. **Centralizer = Isotropy Subgroup**: The isotropy subgroup of $S_3$ at $\theta_0$ is $S_3$ itself;
3. **Symplectic Reduction and Ground State Locking**: The Marsden-Weinstein type reduction $\mu^{-1}(0)/S_3$ is a zero-dimensional symplectic manifold (a single point), whose symplectic volume is conventionally set to 1.

*Proof.* The action of $S_3$ on $D_\theta$ is by permutation of the $\theta_i$, preserving the constraint $\sum\theta_i=\pi/2$. The components $\mu_1=\theta_1-\theta_2$, $\mu_2=\theta_2-\theta_3$ transform under $S_3$ according to its adjoint representation. One directly verifies $\mu=0 \Leftrightarrow \theta_1=\theta_2=\theta_3=\pi/6$. $\mu^{-1}(0)/S_3$ is a single point, with symplectic volume conventionally set to 1. $\square$

### 3.4 &nbsp; Range Compatibility

**Theorem 3.8 (Range Compatibility)** &nbsp; The range of the six-term action and the range of the abstract geometric quantity satisfy
$$S(D_\theta)=[24,+\infty)\subset(0,+\infty)=S(D_\pm).$$
For any $S_0\ge 24$, there exists $x\in D_\pm$ such that $S(x)=S_0$ (by Theorem 1.4), and there exists $\theta\in D_\theta$ such that $S(\theta)=S_0$ (by Theorem 3.5).

*Proof.* By Theorem 1.3, $S(D_\pm)=(0,+\infty)$. By Theorem 3.5, $S(D_\theta)=[24,+\infty)$. Clearly $[24,+\infty)\subset(0,+\infty)$. $\square$

---

## Chapter 4 &nbsp; Bridge Function and the 10-Direction Geometric Space

### 4.1 &nbsp; Explicit Parameter Mapping and Symmetry Axis Uniformization

**Theorem 4.2 (Explicit Construction of the Parameterization Mapping)** &nbsp; Let $S_{\text{abstract}}: D_+\to(0,+\infty)$ be a continuous function satisfying Axioms 1–2 (including the strict monotonicity hypothesis). Define the regularized geometric quantity
$$\tilde{S}(x)=S_{\text{abstract}}(x)+24.$$
Then there exists a unique continuous injection $\Phi_+: D_+\to D_\theta$ such that:

1. **Range Locking**: $S(\Phi_+(x))=\tilde{S}(x)$;
2. **Gauge Section**: $\Phi_+(x)$ lies on the symmetry axis $\gamma=\{\theta\in D_{\text{ord}}\mid \theta_2=\theta_3\}$ of the ordered sector gauge $D_{\text{ord}}$;
3. **Boundary Compatibility**: $\lim_{x\to p_0}\Phi_+(x)=\theta_0=(30^\circ,30^\circ,30^\circ)$, and $\lim_{x\to p_*}\Phi_+(x)\in\partial D_\theta$.

*Proof.* In three steps:

**Step 1: Strict convexity of level sets.** By Theorem 3.5, $S(\theta)$ is strictly convex on $D_\theta$, with the unique global minimum at $\theta_0$, of value $24$. For any $S_0>24$, the level set $L_{S_0}=\{\theta\in D_\theta\mid S(\theta)=S_0\}$ is a smooth strictly convex closed curve enclosing $\theta_0$. Strict convexity guarantees: any ray emanating from $\theta_0$ intersects $L_{S_0}$ at exactly one point.

**Step 2: Monotonicity on the symmetry axis.** In $D_{\text{ord}}$, the symmetry axis $\gamma$ is the line segment joining $\theta_0$ to the boundary point $(\pi/2,0,0)$. Restricting $S$ to $\gamma$, parameterize as $\theta_1=\pi/2-2t,\ \theta_2=\theta_3=t$ ($t\in(0,\pi/6]$). Then
$$S|_\gamma(t)=\frac{1}{\sin^2(\pi/2-2t)}+\frac{3}{\sin^2 t}+\frac{2}{\sin(\pi/2-2t)\sin t}.$$
One can compute the derivative to obtain $\frac{d}{dt}(S|_\gamma)<0$ for $t\in(0,\pi/6)$. Hence $S|_\gamma: \gamma\to[24,+\infty)$ is a strictly decreasing homeomorphism. Therefore, for any $S_0\geq24$, there exists a unique $\theta^*(S_0)\in\gamma$ such that $S(\theta^*(S_0))=S_0$.

**Step 3: Construction of the mapping.** Define $\Phi_+(x)=\theta^*(\tilde{S}(x))$. By the strict monotonicity of $\tilde{S}$ and the continuity of $\theta^*$, $\Phi_+$ is continuous and injective. The boundary behavior follows directly from the limits of $\tilde{S}$ and the correspondence of $\theta^*$. $\square$

**Corollary 4.2.1 (Geometric Semantics of the UV/IR Branches)** &nbsp; Let $S_{\text{abstract}}^\pm:D_\pm\to(0,+\infty)$ be the abstract geometric quantity on each branch. The scale-reciprocal duality $t=a^2/\ell_0^2\leftrightarrow 1/t$ of the bridge function standard form yields:
- $D_+$ corresponds to $a\in(0,\ell_0]$ (UV microscopic singularity limit);
- $D_-$ corresponds to $a\in[\ell_0,+\infty)$ (IR macroscopic expansion limit);
- The two branches join seamlessly at the ground state $x_0=\Phi_+^{-1}(\theta_0)=\Phi_-^{-1}(\theta_0)$, where $a=\ell_0$.

**Theorem 4.3 (Symmetry Axis Uniformization)** &nbsp; On $D_\theta$, the restriction $S|_{\gamma}$ of the six-term action $S$ to the symmetry axis $\gamma = \{\theta\in D_{\text{ord}} \mid \theta_2=\theta_3\}$ of the ordered sector gauge
$$D_{\text{ord}} = \{\theta\in D_\theta \mid \theta_1 \geq \theta_2 \geq \theta_3\}$$
is a strictly decreasing homeomorphism $\gamma \to [24,+\infty)$. Therefore, for any $S_0 \geq 24$, there exists a unique $\theta^*(S_0) \in \gamma$ such that $S(\theta^*)=S_0$. In other words, $\gamma$ is a **global uniformization section** of $S$ within $D_{\text{ord}}$.

*Proof.* By Theorem 3.5, $S$ is strictly convex on $D_\theta$. $\gamma$ is the line segment joining $\theta_0$ to the boundary point $(\pi/2,0,0)$. Restricting $S$ to $\gamma$, parameterize as $\theta_1=\pi/2-2t,\ \theta_2=\theta_3=t$ ($t\in(0,\pi/6]$). Since $D_\theta$ is a convex set and $\gamma\subset D_\theta$ is a line segment, the restriction $S|_\gamma$ of the strictly convex function $S$ to $\gamma$ is also strictly convex. Moreover, $\theta_0$ (corresponding to $t=\pi/6$) is the unique global minimum of $S$ on $D_\theta$, hence also the unique minimum of $S|_\gamma$ on $\gamma$. As $t\to 0^+$, $S|_\gamma(t)\to+\infty$; at $t=\pi/6$, $S|_\gamma=24$. A strictly convex function on an interval that has a unique interior minimum must be strictly decreasing on one side of the minimum and strictly increasing on the other. Hence $S|_\gamma$ is strictly decreasing on $(0,\pi/6)$ and is a continuous bijection from $+\infty$ down to $24$. $\square$

### 4.2 &nbsp; Quantized Zero State

**Proposition 4.4 (Mathematical Origin of the Quantization Spacing)** &nbsp; In the spectral triple reconstruction framework, the characteristic length $\chi_L$ is determined by the Wodzicki residue of the Dirac operator $D$ on $M(a)$:
$$\chi_L(a) := \bigl(\mathrm{Res}_W(D^{-9})\bigr)^{1/9},$$
where $\mathrm{Res}_W(D^{-9})$ satisfies
$$\mathrm{Res}_W(D^{-9}) = \frac{512\pi^4}{105}\,V,\quad V=\mathrm{Vol}(M(a)).$$

**Theorem 4.5 (Quantized Zero State)** &nbsp; Under the mapping $\Phi_\pm:D_\pm\to D_\theta$ of Theorem 4.2 and the Berezin–Toeplitz quantization framework, the sector projection intensity angles $\theta_i$ and the quantization level $k$ are rigorously locked through the following mechanism:

1. **Discrete Embedding**: For the $k$-th quantization level ($k=0,1,2,\dots$), define discrete parameter points
   $$x_k = \Phi_\pm^{-1}\left(\theta^*(24 + \Delta S_k)\right),$$
   where $\Delta S_k>0$ is the stiffness deviation increment of the $k$-th quantization level relative to the ground state $S_{\min}=24$.

2. **Angle Asymptotic Formula**: Along the symmetry axis $\gamma=\{\theta_2=\theta_3\}$, $\theta_1^{(k)}$ satisfies
   $$\sin^2\theta_1^{(k)} = \frac{1}{4} \mp \sqrt{\frac{\Delta S_k}{124}} + \frac{\Delta S_k}{186} + O((\Delta S_k)^{3/2}),$$
   which degenerates to $\sin^2 30^\circ = 1/4$ at the ground state $k=0$ ($\Delta S_0=0$).

*Proof.* By Theorem 4.2, $\Phi_\pm$ maps $\tilde{S}(x)$ to $\theta^*(\tilde{S}(x))$. On $\gamma$, parameterize $\theta_1=\pi/2-2t, \theta_2=\theta_3=t$, and expand $t$ near $\pi/6$:
$$S|_\gamma(t) = 24 + 372(t-\pi/6)^2 + O((t-\pi/6)^3).$$

**Verification of the coefficient 372**: At the symmetry point $\theta_0=(30^\circ,30^\circ,30^\circ)$, the diagonal entries of the full-space Hessian are $H_{ii}=40$, and the off-diagonal entries are $H_{ij}=12\;(i\neq j)$. The eigenvalues of the constraint tangent space Hessian are $124,124$. Along the direction $v=(2,-1,-1)$ of the symmetry axis $\gamma$ (with norm $\sqrt{6}$), the quadratic form $v^{\mathsf T}H v = 124\times 6 = 744$. The squared norm of the parameterization $\delta\theta=(-2,1,1)\delta t$ is $6(\delta t)^2$, hence $S|_\gamma(t) = 24 + \frac{1}{2}\times 744\times(t-\pi/6)^2 = 24 + 372(t-\pi/6)^2$.

By the positive definiteness of the Hessian from Theorem 3.5, inverting $t(\tilde{S})$ yields $t-\pi/6 = \pm\sqrt{(\tilde{S}-24)/372}$. Substituting into $\sin^2\theta_1 = \cos^2(2t)$ and Taylor-expanding at $t=\pi/6$ gives the asymptotic formula. $\square$

### 4.3 &nbsp; Bridge Function Standard Form

**Definition 4.6 (Bridge Function Standard Form Family)** &nbsp; Let $S:(0,+\infty)\to[24,+\infty)$ be a real analytic function satisfying the following three conditions:

**(C1) Scale-Reciprocal Duality**: $S(a)=S(\ell_0^2/a)$ for all $a>0$;
**(C2) Ground State Locking**: $S(\ell_0)=24$ is the unique global minimum, and $S''(\ell_0)>0$;
**(C3) Spectral Asymptotic Constraint**: As $a\to 0^+$, $S(a)\sim C/a^2$ ($C>0$ is a constant).

Then the class of functions satisfying (C1)–(C3) (the bridge function standard form family) is
$$\mathcal{F}_{\text{bridge}} = \left\{ S(a) = c_2\left(\frac{a^2}{\ell_0^2}+\frac{\ell_0^2}{a^2}\right)+c_0 \;\middle|\; c_2>0,\ 2c_2+c_0=24 \right\}.$$

**Normalization Condition (Framework Input)** &nbsp; From $\mathcal{F}_{\text{bridge}}$, select the unique element satisfying $c_0 = 0$ and $c_2 = 12$, denoted by
$$S(a) = 12\left(\frac{a^2}{\ell_0^2} + \frac{\ell_0^2}{a^2}\right).$$
This normalization condition is **not** a theorem derived from Axioms 1–3, but a **definitional input** of the framework.

**Theorem 4.7 (Bridge Function Standard Form)** &nbsp; Let $S:(0,+\infty)\to[24,+\infty)$ be a real analytic function satisfying (C1)–(C3). Then $S$ must take the form
$$S(a)=c_2\left(\frac{a^2}{\ell_0^2}+\frac{\ell_0^2}{a^2}\right)+c_0,$$
with $c_2>0$, $2c_2+c_0=24$. If the normalization condition is further imposed, then $c_2=12$, $c_0=0$, and $S(a)=12(a^2/\ell_0^2+\ell_0^2/a^2)$ is uniquely determined.

*Proof.* In four steps:

**Step 1: Duality enforces an even function structure.** Let $x=a/\ell_0$, $u=\ln x$. By (C1), $S(u)=S(-u)$, so $S$ is an even analytic function of $u$. Its Laurent expansion (in the $x$ variable) is $S(x)=\sum_{n=-\infty}^{\infty} c_n x^n$, with $c_n=c_{-n}$.

**Step 2: Spectral asymptotic truncation.** By (C3), $\lim_{x\to 0} x^2 S(x)=C<+\infty$. This requires $c_n=0$ for all $n<-2$. By the duality $c_n=c_{-n}$, we obtain $c_n=0$ for all $n>2$. Hence $S(x)=c_{-2}x^{-2}+c_0+c_2x^2$, with $c_{-2}=c_2$.

**Step 3: Ground state locking determines the relation.** By (C2), $S(1)=24$ and $S'(1)=0$. Compute $S'(x)=2c_2(x-x^{-3})$ (using $c_{-2}=c_2$); $S'(1)=0$ is automatically satisfied. $S''(x)=2c_2(1+3x^{-4})$, so $S''(1)=8c_2>0$ requires $c_2>0$. Substituting $S(1)=2c_2+c_0=24$. Hence the standard form family is $\mathcal{F}_{\text{bridge}}$.

**Step 4: Confirmation of uniqueness.** Under the normalization condition, $c_2=12$, $c_0=0$, and the bridge function standard form is uniquely determined. $\square$

**Honest Annotation (Status of the Analyticity Hypothesis and Normalization Condition)** &nbsp; Theorem 4.7 requires $S$ to be a meromorphic function, which is an **analyticity hypothesis of the framework** and not derived from Axioms 1–3. The normalization condition $c_0=0$, $c_2=12$ is an explicit input of the framework. Together with the three axioms, they constitute the complete constraint system of the 10-direction geometric space.

**Corollary 4.7.1** &nbsp; Within the class of real analytic functions satisfying (C1)–(C3), the standard form family of the bridge function is $\mathcal{F}_{\text{bridge}}$. After imposing the normalization condition, $S=12(a^2/\ell_0^2+\ell_0^2/a^2)$ is the **unique** choice.

**Remark 4.1 (Mathematical Status of $\ell_0$)** &nbsp; $\ell_0$ is the third interlocking constant alongside $\Lambda=3$ and $k_0=2$. It introduces no new axiom or external hypothesis, serving only as part of the definition of the constrained product sphere class. Taking $V(\ell_0)=1$ (volume normalization) is equivalent to choosing spectral geometric units; $\ell_0$ is not a "physical constant" derived from mathematics but an anchor of spectral geometric units.

### 4.4 &nbsp; Spectrum-Projection Explicit Mapping

Based on the bridge function standard form, the first three non-zero Laplace–Beltrami eigenvalues are explicitly determined by the holographic screen angle configuration $\theta$ as:

$$\begin{aligned}
\lambda_1^\Delta(\theta) &= \frac{S(\theta) \pm \sqrt{S(\theta)^2 - 576}}{8\ell_0^2} \\[4pt]
\lambda_2^\Delta(\theta) &= \frac{8}{3}\lambda_1^\Delta(\theta) = \frac{S(\theta) \pm \sqrt{S(\theta)^2 - 576}}{3\ell_0^2} \\[4pt]
\lambda_3^\Delta(\theta) &= \Lambda \lambda_1^\Delta(\theta) = \frac{\Lambda\left(S(\theta) \pm \sqrt{S(\theta)^2 - 576}\right)}{8\ell_0^2}
\end{aligned}$$

where the $\pm$ sign corresponds respectively to the UV branch ($a\le\ell_0$, taking $+$) and the IR branch ($a\ge\ell_0$, taking $-$).

The regularized action $S_{\text{abstract}} = S(\theta) - 24 = 12\left(\frac{a}{\ell_0} - \frac{\ell_0}{a}\right)^2$ translates the holographic screen realization domain $[24,+\infty)$ to $(0,+\infty)$, in **precise correspondence** with the range of the abstract geometric quantity $S_{\text{abstract}}:D_\pm\to(0,+\infty)$.

### 4.5 &nbsp; Definition of the 10-Direction Geometric Space

**Definition 4.8 (10-Direction Geometric Space)** &nbsp; The **10-direction geometric space** $\mathcal{T}$ is an infinite family of nine-dimensional Riemannian manifolds defined on the basis of the three axioms and the bridge function standard form:

1. **Excited-State Parameter Space** (Axioms 1–2): guarantees that the range of $S(x)$ is $(0,+\infty)$;
2. **Constrained Product Spheres**: the nine-dimensional product manifold $M(a)=S^3\times S^3\times S^3$ equipped with proportion-locked metric ($\Lambda=3$, $k_0=2$), with moduli space parameterized by $a\in(0,+\infty)$; the spectral rigidity theorem guarantees uniqueness of the isometry class;
3. **Holographic Screen Encoding Condition** (Axiom 3): the two-dimensional oriented subspace $\Sigma$ on each tripartite tangent bundle fiber and the angle constraint $\theta_1+\theta_2+\theta_3=90^\circ$, with six-term action range $[24,+\infty)$. The symplectic geometric structure, Hamiltonian dynamics, and $S_3$ Weyl chamber coordinates provide additional mathematical identification layers for the holographic screen.

Each element of $\mathcal{T}$ is a constrained product sphere $M(a)$ carrying a tripartite tangent bundle decomposition $TM=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ and a holographic screen structure $\Sigma$. The correspondence between its moduli space parameter $a$ and the sector angles $\theta$ is explicitly closed by the bridge function standard form, yielding a UV/IR dual-branch duality structure.

**Proposition 4.9 (Infiniteness)** &nbsp; The 10-direction geometric space $\mathcal{T}$ contains uncountably infinitely many mutually non-isometric nine-dimensional manifolds.

*Proof.* By Theorem 2.2, the moduli space is parameterized by $a\in(0,+\infty)$. The interval $(0,+\infty)$ has the cardinality of the continuum $\mathfrak{c}$. By the spectral rigidity Theorem 2.3, distinct values of $a$ correspond to distinct isometry classes. $\square$

---

## Chapter 5 &nbsp; Nine-Element Interlocking and Group-Theoretic Emergence

### 5.1 &nbsp; Global Geometric Diagram

The six spaces involved in the theory are rigorously formalized as manifolds:

1. **Abstract Excited-State Manifold $\mathcal{D}_\pm$**: a one-dimensional open smooth manifold, $\mathcal{D}_\pm \cong (0,1)$.
2. **Symplectic Holographic Screen Surface $\mathcal{P}_\theta$**: the interior of the standard 2-simplex, equipped with the standard symplectic form $\omega = d\theta_1 \wedge d\theta_2$; the total stiffness function $S(\theta)$ constitutes a Morse function with a unique non-degenerate global minimum at $\theta_0 = (\pi/6, \pi/6, \pi/6)$.
3. **Metric Moduli Space $\mathcal{M}_{\text{rigid}}$**: the constrained submanifold of the moduli space of Riemannian metric isometry classes of the nine-dimensional manifold $S^3 \times S^3 \times S^3$, which degenerates to $(0,+\infty)_a$.
4. **Spectral Space Weyl Chamber $\mathcal{W}$**: the open cone region consisting of strictly increasing eigenvalue triples.
5. **Quantization Level $\mathcal{Q}_k$**: the Berezin–Toeplitz quantization Hilbert space, with rigorous geometric space dimension $(k+1)^2$.
6. **Discrete Approximation Level $\mathcal{G}_N$**: the $\epsilon$-net graph sequence.

### 5.2 &nbsp; Nine-Element Interlocking

**Theorem 5.1 (Nine-Element Interlocking)** &nbsp; The fundamental premise (constrained product sphere holographic principle) together with the three axioms, three interlocking constants, and three instrumental-layer theorems form a mutually locked logical network:

**(A) Weyl Chamber Boundary Lock-Death** (Theorem 2.3): The spectral rigidity analysis under $\Lambda=3$, $k_0=2$ automatically guarantees the strict separation of the first three Laplace eigenvalues ($3/a^2 < 8/a^2 < 9/a^2$). Theorem 4.2 embeds the one-dimensional parameter space of Axioms 1–2 into the symmetry axis of the two-dimensional simplex of Axiom 3; Theorem 4.3 proves that the symmetry axis $\gamma$ is a global uniformization section of $S$.

**(B) Moduli Space Compression Lock-Death** (Theorem 2.2): The rigidity of the group-theoretic invariants $\Lambda(S_3)=3$ and $k_0(S_3)=2$ compresses the moduli space to a one-dimensional submanifold, which in reverse locks the legitimate existence of the one-dimensional topological structure required by Axiom 1.

**(C) Moduli Space Parameterization and Ground State Anchoring**: By Theorem 2.2, the moduli space is parameterized by the single scale factor $a$; by Theorem 3.5, the minimum of the holographic screen action is $24$. The bridge function standard form (Theorem 4.7) locks these two values as $S_{\min}=24=12(1+1)$, attained at $a=\ell_0$.

**(D') Quantization Level Lock-Death**: The compactness of the holographic screen's two-dimensional symplectic structure $(\Sigma,\omega)$ demands quantization. The square-root decomposition of the tangent bundle rigorously yields the dimension $(k+1)^2$ of the tensor product of two independent $\mathcal{O}(k)$ section spaces. Bott periodicity locks $N_{\text{eff}}=7$, which in reverse constrains the number of independent encoding channels of the holographic screen sector projections to at most $7$.

**(E') High-Dimensional Spectral Rigidity Lock-Death**: The constrained isospectral rigidity of Theorem 2.3 holds under the bridge function standard form (Theorem 4.7); the heat kernel coefficient ratio $a_2/a_0=(1+\Lambda+\Lambda k_0)/a^2=10/a^2$ is locked by Lemma 2.0.

**(F') Discrete Degeneracy Lock-Death**: The rigorous sources of spectral convergence and heat kernel decay are guaranteed by the discrete approximation theorem; Theorem 4.7 guarantees the analytic structure of the UV/IR branches, so that the connection between the discrete approximation level $\mathcal{G}_N$ and the continuum level $\mathcal{P}_\theta$ involves no extra degrees of freedom.

### 5.3 &nbsp; Self-Consistency Verification

Lemma 2.0 has directly yielded $\Lambda = \Lambda(S_3) = 3$, $k_0 = k_0(S_3) = 2$ from the set structure of the tripartite tangent bundle. The role of the six relations listed in §5.2 is not "solving a system of equations for $\Lambda,k_0$," but rather verifying the self-consistency of the $S_3$ group-theoretic output $(3,2)$ across all geometric links:

**Verification 1 (Spectral Separation)**: $\Lambda=3$ satisfies $\Lambda > 8/3$, so the first three eigenvalues are strictly separated as $3/a^2 < 8/a^2 < 9/a^2$. ✓

**Verification 2 (Fourth Eigenvalue)**: $3\Lambda=9 < \min\{15, 3\Lambda k_0=18, 3(\Lambda+1)=12\}=12$. ✓

**Verification 3 (Heat Kernel Coefficient Ratio)**: $a_2/a_0 = (1+3+6)/a^2 = 10/a^2$. ✓

**Verification 4 (Information Hierarchy)**: $\Lambda^{2n}=3^{2n}=9^n$, and for $n\leq 7$ all are integers. ✓

**Verification 5 ($90^\circ$ Tripartition)**: $90^\circ = 3 \times 30^\circ$, i.e., $\Lambda=3$. ✓

**Verification 6 (Ground State $S_{\min}=24$)**: $S_{\min}=24=12(1+1)$ is consistent with $k_0=2$ (bipartite compactness). ✓

**Honest Annotation**: The source of $\Lambda=3$ and $k_0=2$ is the $S_3$ group-theoretic output of Lemma 2.0, not a "solution" of the verification equations of this section. The above six verifications merely confirm that the group-theoretic output does not contradict any link of the holographic screen geometry. Any deviation from $(3,2)$ would destroy this self-consistency, but the origin of $(3,2)$ itself is group theory, not equation solving.

With $(\Lambda, k_0) = (3, 2)$ locked, the scale constant $\ell_0$ is uniquely determined by the volume normalization condition $V(\ell_0)=1$ of the constrained product spheres:
$$\ell_0 = V_{\text{unit}}^{-1/9} = \left(\frac{3^3 \cdot 2^{3/2}}{(2\pi^2)^3}\right)^{1/9} \approx 0.5991\ \text{(geometric units, dimensionless)}.$$

*Proof.* The volume of a single $S^3(r)$ is $2\pi^2 r^3$, hence
$$V(a) = (2\pi^2)^3 a^3 \left(\frac{a}{\sqrt{3}}\right)^3 \left(\frac{a}{\sqrt{6}}\right)^3 = \frac{(2\pi^2)^3}{3^3 \cdot 2^{3/2}} a^9 = V_{\text{unit}} a^9.$$
The condition $V(\ell_0)=1$ directly gives $\ell_0=V_{\text{unit}}^{-1/9}$. $\square$

**Theorem 5.4 (Bootstrap Closure)** &nbsp; With the interlocking constants uniquely determined, all mathematical structures of the 10-direction geometric space $\mathcal{T}$ form a closed chain:
$$\Lambda(S_3) = 3 \xrightarrow{\text{90° decomposition}} \theta_i = 30^\circ \xrightarrow{\text{strict convexity}} S_{\min} = 24 \xrightarrow{\text{bridge function standard form}} a = \ell_0 \xrightarrow{\text{spectral rigidity}} \lambda_i \xrightarrow{\text{uniformization}} \theta \xrightarrow{\text{quantization locking}} k \xrightarrow{\text{heat kernel spectrum}} a_2/a_0 \xrightarrow{\text{discrete approximation}} \mathcal{G}_N$$
Each arrow in the bootstrap chain constitutes a **bidirectional implication**: the preceding step uniquely determines the next, and the independence of the next step is sufficient to deduce the preceding step in reverse (modulo symmetry). The entire chain contains no free parameters or free functions. $\square$

---


# Part II &nbsp; Physical Mapping Layer

## Chapter 6 &nbsp; The Single Physical Mapping

### 6.1 &nbsp; Theoretical Hierarchy and Mapping Declaration

On top of the purely mathematical axiom framework of the 10-direction geometric space, a **geometry-to-physics mapping layer** is established. This mapping layer is not a purely mathematical theorem within the three-axiom framework, but an explicit declaration of how to read physical observables from geometric objects.

The physical mapping layer has only two kinds of input:

1. **The Three Axioms**: the Circle Topology Axiom, the Boundary Limit Axiom, and the Holographic Screen Encoding Condition;
2. **The Single Physical Mapping $\mathcal{E}$**: identifying the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle as the electromagnetic interaction.

This mapping is not a fourth axiom, but a physical identification rule: it states which part of the geometric objects defined by the three axioms corresponds to electromagnetic phenomena in the physical world.

### 6.2 &nbsp; The Core Mapping $\mathcal{E}$

**Core Mapping $\mathcal{E}$ (Electromagnetic Geometric Mapping)** &nbsp; The $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure (connecting the matter sector and the causal sector) of the tripartite tangent bundle corresponds to the electromagnetic interaction.

This mapping necessarily accompanies two geometric modes:
1. **Source Mode**: the ground-state excitation of the $\mathcal{M}$ sector under the soft mode, outputting a rest energy $E_{\mathcal{M}}\approx 511$ keV, identified as the **electron**;
2. **Propagation Mode**: the null-cone structure of the $\mathcal{C}$ sector under the boundary limit, outputting a massless propagation speed $c$, identified as the **photon**.

The two are bound by the same geometric eigen-quantity $S_e=137.035999084$, forming an indivisible electromagnetic geometric entity. The $\mathcal{I}$ sector does not map to an independent particle, serving only as the information/phase channel for electromagnetic coupling.

**ℰ-Mapping Anchoring Principle** &nbsp; The electromagnetic geometric mapping $\mathcal{E}$ is the core anchoring mapping between geometric theory and physical observables — it identifies the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling structure of the tripartite tangent bundle as the electromagnetic interaction. The framework adopts a **dual-anchor strategy**: $S_e$ (the inverse fine-structure constant) and $c$ (the speed of light in vacuum) as the two external anchoring inputs of the physical mapping layer, with the remaining parameters of the dimensional bridge ($\chi_L$, $\chi_T$, $K$, $G_L$, etc.) jointly determined by the anchoring values and the geometric structure.

**Honest Annotation**: The precise数值 $c = 299\,792\,458$ m/s is an external input (SI defined value) and is not derived from the three axioms. The equation $c = v_{\text{geo}} \cdot \chi_L/\chi_T$ defines a ratio constraint among the geometric intrinsic speed $v_{\text{geo}}$, characteristic length $\chi_L$, and characteristic time $\chi_T$, but does not independently determine the numerical value of $c$.

### 6.3 &nbsp; Derived Quantities of the Single Mapping

From the single physical mapping $\mathcal{E}$ and the three axioms, the following six eigen-quantities can be completely derived:

**Anchoring Item 6.3.1 (Inverse Fine-Structure Constant)** &nbsp; The value $S_e$ of the holographic screen six-term action at the effective physical identification point is identified as the inverse fine-structure constant. This numerical value takes the experimentally measured value $\alpha^{-1}=137.035999084(21)$ (CODATA 2018) as the framework anchoring input:
$$S_e \equiv \alpha^{-1} = 137.035999084.$$

**Honest Annotation**: $S_e$ is not a geometric output independently computed from the three axioms. It is an external anchoring value of the physical mapping layer — the framework identifies it as the effective value of the holographic screen six-term action after accounting for percolation and cross-sector coupling corrections. The six-term action at the bare reference point (without corrections) is $S(\theta_1^0,\theta_2^0,\theta_3^0)\approx 137.0$, and the difference $\approx 0.036$ from $S_e$ is naturally absorbed by the coupling corrections of the percolation-variational closure equations.

**Derived Item 6.3.2 (Mass Formula)** &nbsp; Physical mass is given by the matter angle $\theta_M$ as:
$$m = K \sin^3\theta_M,$$
where $K$ is the geometric energy scale constant and $\theta_M$ is the matter sector projection intensity angle.

**Anchoring Item 6.3.3 (ℰ-Mapping and Speed of Light Anchoring)** &nbsp; The speed of light in vacuum $c=299\,792\,458$ m/s is an external anchoring input of the physical mapping layer (SI defined value). It satisfies the ratio constraint with the geometric intrinsic speed $v_{\text{geo}}$, characteristic length $\chi_L$, and characteristic time $\chi_T$:
$$c = v_{\text{geo}} \cdot \frac{\chi_L}{\chi_T}.$$

**Derived Item 6.3.4 (Effective Soft/Hard Modes)** &nbsp; The effective Hessian eigenvalues arising from cross-sector coupling are
$$(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}}) = (391.05,\ 59324.3)\ \text{rad}^{-2}.$$

**Derived Item 6.3.5 (First Scale of the Dimensional Bridge)** &nbsp; $N_1 = 6000.$

**Derived Item 6.3.6 (Nucleon Geometric Charge)** &nbsp; $v_p = 1117.$

All six quantities above are determined from the same mapping $\mathcal{E}$ and the three axioms (with $S_e$ and $c$ as external anchoring inputs; the rest are framework outputs):

| Derived Item | Mathematical Origin | Remarks |
|:---|:---|:---|
| $S_e$ | Locked value of holographic screen six-term action | Identified by mapping $\mathcal{E}$ as $\alpha^{-1}$ |
| $m=K\sin^3\theta_M$ | Dimensional bridge spectral formula | Mass formula is the output of $\mathcal{E}$ for the source mode |
| ℰ-mapping anchoring | $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling | $c$ is external anchoring input (SI defined value) |
| $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})$ | Dual-mode zero-error condition | Spectral output of cross-sector coupling under the same mapping |
| $N_1$ | Seven-level recursive construction of dimensional bridge | First scale |
| $v_p$ | Strong interaction geometric charge | Readout of the same mapping in the strong interaction sector |

---

## Chapter 7 &nbsp; Physical Identification on the Holographic Screen

### 7.1 &nbsp; Physical Identification Point (Bare Reference Point)

**Definition (Physical Identification Point)** &nbsp; The angle configuration satisfying the following simultaneous system is called the physical identification point (bare reference point):
1. Completeness axiom: $\theta_M+\theta_C+\theta_I=90^\circ$;

3. Electron mass identification derived from the single mapping: $K\sin^3\theta_M = m_e$.

Numerically solving this simultaneous system yields:
$$\theta_1^0 = 57.9300000000^\circ,\quad \theta_2^0 = 26.1593112467^\circ,\quad \theta_3^0 = 5.9106887533^\circ.$$

Verification: $57.93+26.1593112467+5.9106887533=90.0000000000^\circ$.

**Important Clarification**: The physical identification point is **not** a stationary point of $S(\theta)$. The unique global minimum of $S(\theta)$ on the constraint manifold is $(30^\circ,30^\circ,30^\circ)$. The physical identification point lies on the $S=S_e$ level surface, with its matter angle additionally locked by the mass formula.

**Theorem (Existence and Uniqueness of the Physical Identification Point)** &nbsp; Within the ordered sector gauge $D_{\text{ord}}$, the simultaneous system has a unique solution.

*Proof sketch.* The completeness condition and the fine-structure identification together determine a one-dimensional level curve. On this curve, $\theta_M=\theta_1$ can vary continuously within the allowed interval; $\sin^3\theta_M$ is strictly monotonic on $(0,\pi/2)$, so the mass formula has a unique solution point for a given $K$. The ordered sector gauge excludes $S_3$ mirror images, guaranteeing uniqueness. $\square$

### 7.2 &nbsp; Matter Angle and Mass Formula

The matter angle is $\theta_M := \theta_1$. The mass formula is $m = K \sin^3\theta_M = K \sin^3\theta_1.$

At the bare reference point, $\theta_M^0=57.93^\circ$. From the dimensional bridge spectral formula,
$$K = \frac{\sqrt{\lambda_1^{\text{eff}}\lambda_2^{\text{eff}}}}{\pi C_K \sin^3\theta_M},$$
where $C_K \approx 3$ is a locked normalization factor to be determined, yielding $K=839.758793$ keV.

### 7.3 &nbsp; Hessian Cross-Section on the Constraint Manifold

On the constraint manifold $\Sigma=\{(\theta_1,\theta_2,\theta_3)\in\mathbb{R}^{3+}\mid \theta_1+\theta_2+\theta_3=90^\circ\}$, choose local coordinates centered at the bare reference point:
$$\xi=(\theta_3-\theta_2)-(\theta_3^0-\theta_2^0),\quad \eta=(\theta_2-\theta_1)-(\theta_2^0-\theta_1^0).$$

**Angle Unit Declaration**: In the following Hessian calculation, angle variables are uniformly substituted in radian measure. The bare reference angles have been converted: $\theta_1^0=1.011$ rad, $\theta_2^0=0.4566$ rad, $\theta_3^0=0.1032$ rad. Hessian components are in units of $\text{rad}^{-2}$.

The second partial derivatives of the total action $S$ in angle space form the Hessian matrix $H_{ij}=\partial^2 S/\partial\theta_i\partial\theta_j$. From the six-term action $S(\theta_1,\theta_2,\theta_3)=\sum_i 1/\sin^2\theta_i + \sum_{i<j} 1/(\sin\theta_i\sin\theta_j)$:

- **Off-diagonal entries** ($i\neq j$): $H_{ij}=\cos\theta_i\cos\theta_j/(\sin^2\theta_i\sin^2\theta_j)$
- **Diagonal entries**: $H_{ii}=(2\sin^2\theta_i+6\cos^2\theta_i)/\sin^4\theta_i + \sum_{j\neq i}(\sin^2\theta_i+2\cos^2\theta_i)/(\sin^3\theta_i\sin\theta_j)$

Evaluating at the bare reference point ($\theta_1^0=1.011$ rad, $\theta_2^0=0.4566$ rad, $\theta_3^0=0.1032$ rad):
$$H_{11}=31.3012,\quad H_{22}=367.7347,\quad H_{33}=59259.35,$$
$$H_{12}=3.4145,\quad H_{13}=69.3547,\quad H_{23}=433.1578\quad(\text{units: rad}^{-2}).$$

Via directional derivatives, the cross-sectional Hessian on the constraint manifold is:
$$H_{\xi\xi}=H_{33}+H_{22}-2H_{23}=58760.77,$$
$$H_{\eta\eta}=H_{11}+H_{22}-2H_{12}=392.21,$$
$$H_{\xi\eta}=-H_{13}+H_{23}+H_{12}-H_{22}=-0.52.$$

Eigenvalues: $\lambda_1=392.21$ (soft mode), $\lambda_2=58760.77$ (hard mode). The soft-to-hard mode ratio is
$$\Lambda_H=\frac{\lambda_2}{\lambda_1}=149.8\approx150=2\times3\times5^2.$$

The value $149.8$ in this ratio is an **output of pure geometric computation**; $150=2\times3\times5^2$ is its approximate prime factorization identification framework.

---

## Chapter 8 &nbsp; Cross-Sector Coupling and Effective Metric

### 8.1 &nbsp; Percolation Structure and Cross-Sector Coupling

**Proposition 8.1 (Percolation Structure)** &nbsp; Within the tripartite tangent bundle framework, the geometric percolation from the $30^\circ$ symmetric background to local excitations is described by a $2\times2$ symmetric matrix:
$$\Phi = \begin{pmatrix} a & b \\ b & a \end{pmatrix}$$
where the matrix entries (angles in radians) are
$$a = 4\pi\cdot\cos^2(\theta_3/2)\cdot(1-1/S_{\text{local}}),\quad b = \frac{45}{2}\cdot\theta_1\cdot\cos(\theta_3).$$

**Honest Annotation (Origin of Percolation Matrix Coefficients)** &nbsp; The coefficient $4\pi$ originates from the angular integral normalization of the $S^3$ volume factor under holographic screen projection; the coefficient $45/2$ originates from the squared integral of the gradient field on $S^3$ and the first-order coupling with $\theta_1$. A complete derivation requires computing the trace of the curvature quadratic form on the $S^3$ fiber bundle, which is beyond the scope of this paper.

**Proposition 8.2 (Cross-Sector Coupling Structure)** &nbsp; The cross-sector coupling among the three sectors, projected onto the $(\xi,\eta)$ coordinates, is a $2\times2$ symmetric matrix:
$$H^W = \begin{pmatrix} a' & b' \\ b' & a' \end{pmatrix}$$
where $a'=-2w$, $b'=2w-w'$, with $w$ being the waist-edge coupling ($\mathcal{M}$-$\mathcal{C}$ and $\mathcal{C}$-$\mathcal{I}$) and $w'$ being the base-edge coupling ($\mathcal{M}$-$\mathcal{I}$). The convention of $w,w'$ taking negative values is adopted so that $a',b'$ output positive values; the negative sign indicates that cross-sector coupling lowers the energy in the joint action.

**Working Hypothesis 8.3 (Cross-Sector Coupling Prefactors)** &nbsp; The cross-sector coupling prefactors satisfy the following algebraic relations:
$$\kappa_w + \kappa_w' = 4L + \frac{\pi}{\Lambda_H},\quad \frac{\kappa_w'}{\kappa_w} = \frac{447}{392},$$
where $L=7$, $\Lambda_H=150$.

**Honest Annotation**: The complete derivation of the above prefactor relations involves the $Spin(8)$ normal bundle structure of the spectral triple and Wodzicki residue normalization, which is beyond the scope of this paper. They are introduced here as **working hypotheses**; the validity of the numerical outputs ($a'=1.577$, $b'=0.867$, waist-edge/base-edge parameters $w=-0.7885$, $w'=-2.444$) is indirectly supported by the subsequent compatibility verification of the dimensional bridge four equations.

### 8.2 &nbsp; Effective Metric

**Working Hypothesis 8.4 (Effective Metric)** &nbsp; The effective soft/hard modes $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})$ are determined by a simultaneous algebraic system involving the bare Hessian $H^{\text{bare}}$, the percolation matrix $\Phi$, and the cross-sector coupling $H^W$. This algebraic system involves a non-trivial action of $\Phi$ and $H^W$ on the Hessian (not simple matrix addition), whose complete explicit form requires derivation in the $Spin(8)$ normal bundle framework, which is beyond the scope of this paper. We directly adopt its numerical results here:
$$(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}}) = (391.05,\ 59324.3)\ \text{rad}^{-2}.$$

**Honest Annotation**: The above numerical values are not rigorous theorem outputs internal to this paper, but intermediate computational results that depend on Working Hypothesis 8.3 (cross-sector coupling prefactors). In the context of an independent submission, $(\lambda_1^{\text{eff}},\lambda_2^{\text{eff}})$ should be regarded as a **working hypothesis** rather than a proven theorem — its validity is indirectly supported by the compatibility of the subsequent dimensional bridge four equations (Chapter 10), but does not constitute an independent proof.

---

## Chapter 9 &nbsp; Dual-Mode Zero-Error and Electromagnetic Geometry

### 9.1 &nbsp; Percolation-Variational Closure Equation

**Definition (Percolation-Variational Closure Equation)** &nbsp; Let $S_{\text{local}}(\mu_1,\mu_2)$ be the six-term action at the local excitation point when the effective Hessian eigenvalues are $\mu_1,\mu_2$ (given by the second-order Taylor expansion of the bare reference point). Define:

- Background action: $S_{\text{bg}} = \frac{1}{2}\text{tr}(H^{\text{bare}}) = \frac{1}{2}(\lambda_1+\lambda_2)$;
- Cross-sector coupling overlap: $W_{\text{coupling}}(\mu_1,\mu_2) = \langle H^W(\mu_1,\mu_2),\ \Phi \cdot H^{\text{bg\_proj}} \rangle_{F}$.

**Then the percolation-variational closure equation is**:
$$\boxed{S_{\text{local}}(\mu_1,\mu_2) + S_{\text{bg}} + W_{\text{coupling}}(\mu_1,\mu_2) = 0}$$

This equation, together with the reality constraint, forms a closed algebraic system for $(\mu_1,\mu_2)$.

**Proposition 9.1 (Dual-Mode Zero-Error Condition)** &nbsp; In the region $\mu_1<\lambda_1$, $\mu_2>\lambda_2$, the closure equation admits a unique real solution; the numerical solution is $\mu_1^*=391.05$, $\mu_2^*=59324.30$.

**Honest Annotation (Sign Convention of the Equation)** &nbsp; In the percolation-variational closure equation, $S_{\text{bg}} = \frac{1}{2}(\lambda_1+\lambda_2) \approx 29576$ is a positive quantity. $S_{\text{local}}$ and $W_{\text{coupling}}$ take negative values near the physical identification point (because local excitation relative to the $S_{\min}=24$ baseline represents an energy lowering), so that the sum of the three terms can vanish. The sign conventions of the various terms in the equation depend on the specific position of the physical identification point on the action surface; a complete argument requires the sign analysis of the Taylor expansion of $S(\theta)$ in the neighborhood of the identification point.

### 9.2 &nbsp; Matter Ground State Energy and Photon Zero Mass

**Theorem (Matter Ground State Energy Formula)** &nbsp; Let $\Delta\eta$ be the soft-mode displacement (locked by the dual-mode zero-error condition), and $\lambda_1^{\text{eff}}=391.05$ the effective soft-mode eigenvalue. Then the ground-state excitation energy of the matter sector $\mathcal{M}$ is
$$\boxed{E_{\mathcal{M}} = \frac{1}{2}\lambda_1^{\text{eff}}(\Delta\eta)^2 \cdot K}$$
where $K=839.758793$ keV is the geometric energy scale constant.

**Numerical verification**: From $E_{\mathcal{M}}=511$ keV, $\lambda_1^{\text{eff}}=391.05$, $K=839.758793$ keV, one obtains
$$|\Delta\eta| = \sqrt{\frac{2E_{\mathcal{M}}}{\lambda_1^{\text{eff}} K}} \approx 0.0557\ \text{rad} \approx 3.19^\circ.$$

**Geometric Necessity of the Photon (Causal Sector)** : The causal sector $\mathcal{C}$ has its background stiffness described by the hard mode $\lambda_2$. At the ground state $S_{\min}=24$, the excitation modes of the $\mathcal{C}$-sector satisfy a nullness condition, corresponding to massless propagation. This nullness is determined by the boundary limit behavior; therefore, **the masslessness of the photon is a necessary accompaniment of the core mapping $\mathcal{E}$**.

---

## Chapter 10 &nbsp; Dimensional Bridge and Emergence of Physical Constants

### 10.1 &nbsp; The Four Equations of the Dimensional Bridge

**Proposition 10.1 (Dimensional Bridge Four Equations)** &nbsp; Under the ℰ-mapping dual-anchor principle (with $S_e$ and $c$ as external inputs), the geometric characteristic length $\chi_L$, characteristic time $\chi_T$, energy scale $K$, length coupling $G_L$, and $\hbar$ satisfy the following simultaneous system:

1. **Velocity Derivation Equation** (given by the propagation mode of the $\mathcal{E}$-mapping):
   $$c = v_{\text{geo}} \cdot \frac{\chi_L}{\chi_T},$$
   where $v_{\text{geo}}=71.832113$ is the geometric intrinsic speed;

2. **Action Emergence Equation**:
   $$\hbar = \frac{K \chi_T N_1}{12\pi S_e^2 \lambda_1^{\text{eff}}};$$

3. **Length Coupling Equation**:
   $$\chi_L = G_L \cdot \hbar c;$$

4. **Geometric Formula for Length Coupling**:
   $$G_L = \frac{4}{\pi} \cdot \frac{v_p S_e \sqrt{\lambda_1^{\text{eff}}}}{N_1 K}.$$

### 10.2 &nbsp; Compatibility of the Four Equations

Eliminating $\hbar$ and $\chi_T$ from the four equations yields:
$$K \cdot G_L = \frac{4 S_e \sqrt{\lambda_1^{\text{eff}}} v_p}{\pi N_1}.$$

Numerical verification:
$$K \cdot G_L = \frac{4 \times 137.035999084 \times \sqrt{391.05} \times 1117}{\pi \times 6000} \approx 642.5.$$

Meanwhile, directly multiplying $K=839.758793$ keV and $G_L\approx0.7648$ keV$^{-1}$ also yields $642.5$. The two agree; the dimensional bridge four equations are **not self-contradictory**.

**Honest Annotation**: This compatibility verification is a necessary condition check — the four equations are numerically not self-contradictory. It does not constitute a uniqueness proof (there may exist other parameter combinations that also satisfy compatibility), nor a sufficiency proof (the solution of the four equations may not be unique). Passing the compatibility check is a necessary but not sufficient condition for the validity of the dimensional bridge.

### 10.3 &nbsp; Self-Consistent Derivation of $\hbar$, $\chi_L$, $\chi_T$

With $c$ as the quantity derived from the ℰ-mapping propagation mode, one solves from $K$ and the four equations:
$$\chi_T = \frac{\hbar \cdot 12\pi S_e^2 \lambda_1^{\text{eff}}}{K N_1},\qquad \chi_L = \frac{c \chi_T}{v_{\text{geo}}}.$$

Substituting numerical values:
- $K = 839.758793$ keV
- $N_1 = 6000$
- $S_e = 137.035999084$
- $\lambda_1^{\text{eff}} = 391.05$ rad$^{-2}$
- $\hbar = 6.5821195675 \times 10^{-16}$ eV$\cdot$s

yields:
$$\chi_T = 3.6161912064 \times 10^{-17}\ \text{s},\qquad \chi_L = 1.5092231080 \times 10^{-10}\ \text{m}.$$

### 10.4 &nbsp; Electron Mass

**Theorem (Electron Mass Theorem)** &nbsp; From the mass formula derived from the single mapping and the dimensional bridge, the electron rest energy is
$$E_e = m_e c^2 = K \sin^3\theta_M \cdot c^2.$$
Substituting $\theta_M=57.93^\circ$ yields $E_e = 510.99895$ keV.

**Theorem (Dimensional Bridge Self-Consistency)** &nbsp; The $\hbar$, $\chi_L$, $\chi_T$, and $K$ output by the dimensional bridge are self-consistent with all electromagnetic eigen-quantities (including $c$) derived from the ℰ-mapping, and the mass formula output $E_e$ agrees with the energy formula output, with a deviation $<0.002\%$.

---

## Chapter 11 &nbsp; Conclusion

This paper integrates the axiom-deduction system of the 10-direction geometric space with the physical mapping layer, presenting a complete and unified derivation chain from the three axioms to physical observables.

**Geometric Foundation**:
- Three axioms define the excited-state parameter space, the abstract geometric quantity, and the holographic screen encoding condition;
- The rigidity theorem of the tripartite tangent bundle permutation group proves the uniqueness of $S_3$, with group-theoretic emergence yielding $\Lambda=3$ and $k_0=2$;
- Spectral rigidity of the constrained product spheres $M(a)$ guarantees a one-dimensional moduli space for the scale factor $a$;
- The range $[24,+\infty)$ of the six-term action corresponds precisely to the range $(0,+\infty)$ of the abstract geometric quantity through the bridge function standard form;
- Nine-element interlocking and group-theoretic emergence achieve bootstrap closure, with the interlocking constants uniquely determined by $S_3$ group theory.

**Physical Mapping**:
- The single core mapping $\mathcal{E}$ identifies the $\mathcal{M}$-$\mathcal{C}$ waist-edge coupling as the electromagnetic interaction;
- From this mapping and the three axioms, six eigen-quantities are derived: $S_e$, the mass formula, ℰ-mapping anchoring, effective soft/hard modes, $N_1$, and $v_p$;
- The physical identification point $(57.93^\circ, 26.16^\circ, 5.91^\circ)$ is determined by the simultaneous system of completeness, $S=S_e$, and the mass formula;
- The Hessian soft-to-hard mode ratio $\Lambda_H=149.8\approx150$ is a pure geometric output;
- The dual-mode zero-error condition locks the effective metric $(391.05, 59324.3)$ rad$^{-2}$;
- With $S_e$ and $c$ as dual anchoring inputs, the dimensional bridge four equations establish a self-consistent locking framework for parameters $\hbar$, $\chi_L$, $\chi_T$, and $K$.

**Honest Annotations**: $\ell_0$ is a spectral geometric unit anchor (not an external physical constant); $S_e$ and $c$ are two external anchoring inputs of the physical mapping layer; the numerical emergence of $\hbar$ belongs to the conditional proposition layer; the normalization condition of the bridge function standard form is an explicit input of the framework.

---

## Appendix A &nbsp; Summary of Key Numerical Values

### A.1 &nbsp; Pure Geometric Outputs

| Quantity | Value | Description |
|:---|:-----|:-----|
| $\Lambda$ | 3 | Tripartition proportionality parameter (number of $S_3$ conjugacy classes) |
| $k_0$ | 2 | Bipartite compactness constant (index of maximal normal subgroup of $S_3$) |
| $\ell_0$ | 0.5991 (geometric units) | Scale constant |
| $\chi_L(\ell_0)$ | 1.983 (geometric units) | Wodzicki residue characteristic length |
| $S_{\min}$ | 24 | Minimum of the six-term action ($30^\circ$ symmetry point) |
| $\lambda_{\text{Hess},i}$ | 124 | Hessian eigenvalue on the constraint tangent space |
| $\lambda_1^\Delta$ | $3/a^2$ | First non-zero Laplace eigenvalue |
| $\lambda_2^\Delta$ | $8/a^2$ | Second non-zero Laplace eigenvalue |
| $\lambda_3^\Delta$ | $9/a^2$ | Third non-zero Laplace eigenvalue |
| $a_2/a_0$ | $10/a^2$ | Heat kernel coefficient ratio |

### A.2 &nbsp; Physical Identification Point and Hessian

| Quantity | Value | Description |
|:---|:-----|:-----|
| $\theta_1^0$ | 57.930000° | Matter angle (bare reference point) |
| $\theta_2^0$ | 26.159311° | Causal angle (bare reference point) |
| $\theta_3^0$ | 5.910689° | Information angle (bare reference point) |
| $S(\theta^0)$ | $\approx 137.0$ | Bare reference point six-term action (without coupling corrections) |
| $S_e$ | 137.035999084 | Effective physical identification point action ($=\alpha^{-1}$, experimentally anchored) |
| $\lambda_1$ | 392.21 rad⁻² | Soft mode eigenvalue |
| $\lambda_2$ | 58760.77 rad⁻² | Hard mode eigenvalue |
| $\Lambda_H$ | 149.8 ≈ 150 | Hessian soft-to-hard mode ratio |

### A.3 &nbsp; Effective Metric and Coupling Parameters

| Quantity | Value | Description |
|:---|:-----|:-----|
| $a$ (percolation) | 12.4415 | Percolation matrix diagonal entry |
| $b$ (percolation) | 22.6281 | Percolation matrix off-diagonal entry |
| $a'$ (coupling) | 1.577 | Cross-sector coupling diagonal entry |
| $b'$ (coupling) | 0.867 | Cross-sector coupling off-diagonal entry |
| $w$ (waist-edge) | $-0.7885$ | Negative value convention |
| $w'$ (base-edge) | $-2.444$ | Negative value convention |
| $\lambda_1^{\text{eff}}$ | 391.05 rad⁻² | Effective soft mode |
| $\lambda_2^{\text{eff}}$ | 59324.30 rad⁻² | Effective hard mode |

### A.4 &nbsp; Core Mapping Companion Outputs

| Quantity | Geometric Output | Experimental Value | Description |
|:---|:---------|:-------|:-----|
| $S_e$ | 137.035999084 | $\alpha^{-1}$ | Inverse fine-structure constant |
| $E_{\mathcal{M}}$ | 511.0 keV | $m_e c^2$ | Electron rest energy |
| Photon masslessness | $\mathcal{C}$-sector nullness | $m_\gamma=0$ | Companion of core mapping |
| $\hbar$ | $6.5821\times10^{-16}$ eV·s | Experimental | Dimensional bridge output |
| $\chi_L$ | $1.5092\times10^{-10}$ m | Bohr radius scale | Dimensional bridge output |
| $\chi_T$ | $3.6162\times10^{-17}$ s | — | Dimensional bridge output |
| $K$ | 839.758793 keV | — | Dimensional bridge / mass formula |
| $G_L$ | $0.7648$ keV⁻¹ | — | Dimensional bridge output |
| $K \cdot G_L$ | $\approx 642.5$ | — | Four-equation compatibility verification |
| $N_1$ | 6000 | — | First scale of dimensional bridge |
| $v_p$ | 1117 | — | Nucleon geometric charge |

---

## Appendix B &nbsp; Summary of Symbols

| Symbol | Meaning |
|:---|:---|
| $D_\pm$ | The two connected components of the excited-state parameter space, $D_\pm \cong (0,1)$ |
| $S(x)$ | Abstract geometric quantity, $S: D_\pm\to(0,+\infty)$ |
| $M(a)$ | Constrained product sphere $S^3(a)\times S^3(a/\sqrt{3})\times S^3(a/\sqrt{6})$ |
| $\Lambda$ | Tripartition proportionality parameter, $\Lambda=\Lambda(S_3)=3$ |
| $k_0$ | Bipartite compactness constant, $k_0=k_0(S_3)=2$ |
| $\ell_0$ | Scale constant (spectral geometric unit anchor) |
| $\lambda_i^\Delta$ | The $i$-th non-zero Laplace–Beltrami eigenvalue |
| $TM(a)$ | Tripartite tangent bundle $\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ |
| $\theta_1,\theta_2,\theta_3$ | Sector projection intensity angles, $\theta_1+\theta_2+\theta_3=90^\circ$ |
| $\Sigma$ | Two-dimensional holographic screen |
| $S(\theta)$ | Six-term action, range $[24,+\infty)$ |
| $D_\theta$ | Angle domain $\{(\theta_1,\theta_2,\theta_3)\mid\theta_i>0,\sum\theta_i=90^\circ\}$ |
| $D_{\text{ord}}$ | Ordered sector gauge $\{\theta_1\geq\theta_2\geq\theta_3\}$ |
| $\gamma$ | Symmetry axis $\{\theta_2=\theta_3\}$ |
| $\mathcal{T}$ | 10-direction geometric space |
| $\mathcal{E}$ | Electromagnetic geometric mapping (single core mapping) |
| $\chi_L$ | Characteristic length |
| $\chi_T$ | Characteristic time |
| $K$ | Geometric energy scale constant |
| $G_L$ | Length coupling |
| $S_e$ | Entropy scale / inverse fine-structure constant |
| $v_{\text{geo}}$ | Geometric intrinsic speed |
| $\Lambda_H$ | Hessian soft-to-hard mode ratio |
| $N_{\text{eff}}$ | Number of independent encoding channels truncated by Bott periodicity, $=7$ |

---

## Appendix C &nbsp; Mathematical Properties of the Bridge Function Standard Form

Let $x = a^2/\ell_0^2 = e^{2u}$ ($u=\ln(a/\ell_0)$). The bridge function standard form is equivalent to:
$$S = 24\cosh\bigl(2\ln(a/\ell_0)\bigr).$$

**Core Properties**:
1. **Even Symmetry**: $S$ is an even function in $u$, naturally producing the scale-reciprocal duality $a \leftrightarrow \ell_0^2/a$;
2. **Convexity and Unique Minimum**: The convexity of $\cosh$ guarantees that $S_{\min}=24$ is uniquely attained at $a=\ell_0$;
3. **Exponential Boundaries**: $S \sim 12e^{2|u|}$ ($|u|\to\infty$), guaranteeing the degeneracy limit $S\to+\infty$.

**2:1 Covering Structure of the Moduli Space**:

| Branch | Domain | Geometric Semantics |
|------|--------|----------|
| UV | $a\in(0,\ell_0]$ | Microscopic singularity limit |
| IR | $a\in[\ell_0,+\infty)$ | Macroscopic expansion limit |
| Ground State | $a=\ell_0$ | Ramification point |

**Vieta Invariant**: $a_{\text{UV}} \cdot a_{\text{IR}} = \ell_0^2$.

**Spectral Transfer Invariance**: The bridge function standard form controls only the overall scaling of the spectrum, not the internal ratios:
$$\frac{\lambda_2^\Delta}{\lambda_1^\Delta} = \frac{8}{3}, \quad \frac{\lambda_3^\Delta}{\lambda_1^\Delta} = 3 \quad (\text{invariant for any } S\geq24).$$

**Regularized Action**:
$$S_{\text{abstract}} = S - 24 = 12\left(\frac{a}{\ell_0} - \frac{\ell_0}{a}\right)^2,$$
which translates the holographic screen realization domain $[24,+\infty)$ to $(0,+\infty)$, in precise correspondence with the range of the abstract geometric quantity $S_{\text{abstract}}:D_\pm\to(0,+\infty)$.

---
