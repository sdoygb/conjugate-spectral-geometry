# 4 Higgs Breathing Mode

**Number:** 4　　　**Version:** 260626.6

**Dependencies:** 0.0.3(260626.6), 0.0.5(260626.6), 0.0.6(260626.6), 0.0.7(260626.6), 0.1(260626.6), 0.1.1(260626.6), 0.1.2(260626.6), 0.2.1(260626.6), 0.2.1.1(260626.6), 0.2.2(260626.6), 0.2.3(260626.6), 0.3.1(260626.6), 0.3.5(260626.6)

---

## Abstract

This paper derives the geometric Lagrangian of the Higgs scalar breathing mode from the intrinsic geometry of the geometric constraint section, within the framework of the three axioms and the 0.X series. It honestly distinguishes three tiers: theorems, constructive assumptions, and conditional frameworks. Core theorem-level results: (i) The breathing mode is defined as the relative linear fluctuation of the square root of the Hessian determinant, with the Completeness Axiom automatically preserved; (ii) The 2D kinetic term is rigorously derived from pixel encoding and the continuum limit; (iii) The mass term coefficient $2\lambda_1$ is derived from the soft-mode restoring force (factor 2 involves a constructive estimate). Constructive assumptions/conditional frameworks: (iv) Area element–action correspondence $\delta S = -\Phi$; (v) Hessian global scaling hypothesis; (vi) Cubic and quartic potential terms; (vii) 4D kinetic term via Clifford reduction; (viii) Dimensional Bridge Higgs mass mapping (with constructive normalization convention) — bare value $m_H^{\text{bare}} = 125.41\ \text{GeV}$ (deviation $+0.05\%$), effective metric value $m_H^{\text{eff}} = 125.64\ \text{GeV}$ (deviation $+0.23\%$). Fermion Yukawa couplings are a working hypothesis. All numerical values synchronized to the 260626.6 baseline.

**Keywords:** Higgs mode; breathing mode; Hessian determinant; geometric Lagrangian; Dimensional Bridge; no symmetry breaking; theorem/assumption tiering

---

## Table of Contents

- Chapter 1　Three-Axiom Alignment and Breathing Mode Definition
  - §1.1　Statement of the Three Axioms and 260626.6 Parameter Synchronization
  - §1.2　Elimination of Angular Translation and Conformal Factor
  - §1.3　Definition via Hessian Determinant Fluctuation
  - §1.4　Completeness Preservation Theorem
- Chapter 2　Area Element–Action Correspondence and Hessian Response
  - §2.1　Area Element–Action Constructive Correspondence (Proposition 2.1)
  - §2.2　Hessian Global Scaling (Constructive Hypothesis 2.2)
- Chapter 3　Geometric Derivation of the Potential Terms
  - §3.1　Second-Order Curvature Restoring Force (Mass Term, Theorem 3.1)
  - §3.2　Cubic Self-Interaction (Constructive Hypothesis 3.2)
  - §3.3　Quartic Self-Interaction (Constructive Hypothesis 3.3)
  - §3.4　Potential Coefficient Locking and Honest Annotation
- Chapter 4　Geometric Derivation of the Kinetic Terms
  - §4.1　Holographic Information Field Pixel Encoding
  - §4.2　Continuum Limit (Theorem 4.2, 2D Rigorous)
  - §4.3　Clifford Reduction to 4D Spacetime (Conditional Framework)
- Chapter 5　Complete Lagrangian and Comparison with the Standard Model
  - §5.1　Rigorous Assembly and Honest Annotation
  - §5.2　Structural Correspondence and the Absence of Spontaneous Symmetry Breaking
- Chapter 6　Dimensional Bridge Mapping and Higgs Mass
  - §6.1　From Geometric Lagrangian to Physical Mass
  - §6.2　Geometric Motivation for the Constructive Normalization Convention $\pi/\sqrt{8}$
  - §6.3　Numerical Computation
  - §6.4　$m_H/m_W$ Consistency Check
- Chapter 7　Geometric Origin of Fermion Yukawa Couplings (Working Hypothesis)
- Chapter 8　Conclusion: Three-Tier Summary of Theorems / Assumptions / Hypotheses
- Appendix　Summary of Key Numerical Values
- References

---

## Chapter 1　Three-Axiom Alignment and Breathing Mode Definition

### §1.1　Statement of the Three Axioms and 260626.6 Parameter Synchronization

This paper is placed strictly within the three-axiom system of the 0.X series, with all parameters aligned to the 260626.6 version baseline:

**Axiom 1 (Completeness Axiom, 0.0.6/0.1/0.2.1)**:
$$\theta_M + \theta_C + \theta_I = 90^\circ$$

**Axiom 2 (Action Axiom, 0.0.7/0.2.1)**:
$$S = \sum_{i=1}^3 \frac{1}{\sin^2\theta_i} + \sum_{i<j} \frac{1}{\sin\theta_i \sin\theta_j}$$
Range $[24, +\infty)$, global minimum $S_{\min}=24$ at the symmetry point $(30^\circ,30^\circ,30^\circ)$.

**Axiom 3 (Mass Mapping Axiom, 0.1/0.3.1)**:
$$m = K \sin^3\theta_M$$
where $K = 839.758793\ \text{keV}$ (locked value, 0.3.1 Theorem 9.1).

**Locked Constants (260626.6 baseline)**:

| Symbol | Value | Source |
|:---|:---|:---|
| $\Lambda$ | $3$ | Three-partition proportion parameter (0.0.7 Proposition 2.0) |
| $k_0$ | $2$ | Binary compactness constant (0.0.7 Proposition 2.0) |
| $S_e$ | $137.035999084$ | Single-core mapping-layer geometric eigenquantity (0.1 §2.2; 0.3.1 Theorem 4.1) |
| $S_0$ | $137.0000000009$ | Bare reference-point six-term action (0.2.1 §2.1 direct computation) |
| $\lambda_1$ (bare) | $392.21\ \text{rad}^{-2}$ | Bare soft mode (0.2.1 §4.5) |
| $\lambda_2$ (bare) | $58760.77\ \text{rad}^{-2}$ | Bare hard mode (0.2.1 §4.5) |
| $\lambda_1^{\text{eff}}$ | $391.05\ \text{rad}^{-2}$ | Effective soft mode (0.1 Derived Item 2.2.4; dual-mode zero-error condition) |
| $\lambda_2^{\text{eff}}$ | $59324.3\ \text{rad}^{-2}$ | Effective hard mode (0.1 Derived Item 2.2.4; dual-mode zero-error condition) |
| $K$ | $839.758793\ \text{keV}$ | Mass quantum (0.3.1 Theorem 9.1) |
| $\chi_L$ | $1.5092231080 \times 10^{-10}\ \text{m}$ | Length mapping factor (0.3.1 §6.2) |
| $\chi_T$ | $3.6161912064 \times 10^{-17}\ \text{s}$ | Time mapping factor (0.3.1 §7.1) |
| $v_{\text{geo}}$ | $71.832113$ | Geometric velocity (0.3.1 §5.2) |

**Single-Core Mapping Declaration** (0.1 §1.3): The $\mathcal{M}$–$\mathcal{C}$ waist-edge coupling structure of the trifurcated tangent bundle corresponds to the electromagnetic interaction, with the electron as source mode and the photon as propagation mode. All derivations in this paper introduce no second independent physical mapping.

**Clarification of $S_0$ origin** (important correction): $S_0 = 137.0000000009$ is obtained by **direct computation** of the six-term action at the bare reference angles $(\theta_M^0,\theta_C^0,\theta_I^0) = (57.93^\circ, 26.16^\circ, 5.91^\circ)$ (0.2.1 §2.1); it is not "the integer part of $S_e$". $S_e = 137.035999084$ is an independent geometric eigenquantity of the single-core mapping layer. The difference $S_e - S_0 = 0.035999084$ is rigorously given by the seven-level recursion (0.2.1 §6).

Bare reference angles (0.2.1 §2.1):
$$\theta_M^0 = 57.9300000000^\circ,\quad \theta_C^0 = 26.1593112467^\circ,\quad \theta_I^0 = 5.9106887533^\circ$$

Constraint-section local coordinates $(\xi,\eta)$ (0.2.1 §4.1):
$$\xi = \theta_I - \theta_I^0,\quad \eta = (\theta_I + \theta_C) - (\theta_I^0 + \theta_C^0)$$

All derivations in this paper introduce no new axiom-level assumptions.

---

### §1.2　Elimination of Angular Translation and Conformal Factor

If the breathing mode were defined as a synchronous angular translation $\delta\theta_M = \delta\theta_C = \delta\theta_I = \Phi$, the sum would change by $3\Phi$, directly violating the Completeness Axiom. Hence the breathing mode cannot be a translation in angular space.

A conformal factor $\Omega(x) = 1 + \Phi/S_0$ would introduce a product-manifold conformal symmetry that is undefined in 0.X, constituting an external assumption without provenance, and is therefore excluded.

---

### §1.3　Definition via Hessian Determinant Fluctuation

In 0.2.1, the geometric constraint section $\Sigma$ is carved out of the Completeness Axiom plane (2D angular manifold) by the condition $S = \text{constant}$ on the six-term action, and is parameterized by local coordinates $(\xi,\eta)$. Its intrinsic geometry is characterized by the Hessian matrix:
$$H_{ij} = \frac{\partial^2 S}{\partial \xi_i \partial \xi_j}\bigg|_{\Sigma},\quad i,j \in \{1,2\}$$

At the bare reference point $(\xi=0,\eta=0)$, the section Hessian (0.2.1 §4.5):
$$H_0 = \begin{pmatrix} 58760.77 & -0.52 \\ -0.52 & 392.21 \end{pmatrix}\ \text{rad}^{-2}$$
$$\det H_0 = \lambda_1 \lambda_2 - H_{\xi\eta}^2 \approx 2.3047 \times 10^7\ \text{rad}^{-4}$$

**Definition 1.1 (Breathing Mode)**: The scalar field $\Phi(x)$ is defined as the relative linear fluctuation of the square root of the Hessian determinant, with the bare reference action $S_0$ as the sole scale:
$$\frac{\sqrt{\det H(\Phi)} - \sqrt{\det H_0}}{\sqrt{\det H_0}} \equiv \frac{\Phi(x)}{S_0}$$

That is:
$$\sqrt{\det H(\Phi)} = \sqrt{\det H_0} \cdot \left(1 + \frac{\Phi}{S_0}\right)$$

**Note 1.1 (Correspondence with area element dilation)**: Under the Hessian metric $g_{ab} = H_{ab}$, $\sqrt{\det H}$ is the area element density. $\Phi$ is thus equivalent to the linear dilation mode of the area element density. This definition is conceptually aligned with the concept of "scalar connection components" in 0.3.5 Theorem 10.3 (0.3.5 has not yet reached theorem status; see its self-description).

---

### §1.4　Completeness Preservation Theorem

**Theorem 1.2 (Automatic Completeness Preservation)**: Definition 1.1 operates only on the intrinsic geometric quantity $\det H$ of the Hessian and does not directly alter the angles $\theta_M, \theta_C, \theta_I$. Therefore the Completeness Axiom $\theta_M + \theta_C + \theta_I = 90^\circ$ is automatically preserved.

*Proof*: $H_{ij}$ are the second derivatives of $S$ on the constraint section; its determinant is an invariant of the intrinsic curvature of the section. $\Phi$ is defined through $\det H$ and does not touch the $\theta_i$ themselves. By 0.2.1 Theorem 3.5.6, the Completeness Axiom corresponds to a Lagrangian submanifold $\mathcal{L}_\eta$ on the symplectic manifold $(\mathcal{P}_\eta, \omega)$; $\Phi$ operates only on the Hessian metric and does not change the zero-set of the Lagrangian submanifold, so completeness is automatically preserved. $\square$

---

## Chapter 2　Area Element–Action Correspondence and Hessian Response

### §2.1　Area Element–Action Constructive Correspondence

**Proposition 2.1 (Area Element–Action Constructive Correspondence, Constructive Assumption)**: On the geometric constraint section $\Sigma$, the iso-surface variation $\delta S$ of the six-term action and the variation of the area element density satisfy the constructive correspondence:
$$\delta S = -S_0 \cdot \delta\left(\frac{\sqrt{\det H}}{\sqrt{\det H_0}}\right) = -\Phi$$

**Geometric motivation** (not a rigorous proof):
1. **Information cell number and area element density**: From the Holographic Screen model of 0.2.2, the number of information cells on the section, $N_{\text{cell}}$, is proportional to the area element density $\sqrt{\det H}$. In 0.2.2 Research Model 3.1, $N_{\text{info}} = (A/a^2) \cdot S_e$; the relation between information density and area provides heuristic support for this correspondence.
2. **Single-pixel action quantum**: From 0.0.7, $S = N_{\text{dec}} \cdot s_0$, where $s_0$ is the single-pixel action quantum. At the bare reference point, $S_0 = N_{\text{dec}}^0 \cdot s_0$.
3. **Information-conservation inverse relationship**: When the number of information cells changes by $\delta N_{\text{cell}}/N_{\text{cell}} = \Phi/S_0$, from the constraint $S_{\text{total}} = 0$, it is assumed that the decoherence depth carried by each cell changes inversely: $\delta N_{\text{dec}}/N_{\text{dec}}^0 = -\Phi/S_0$. This inverse relationship is a **constructive assumption**.

Under the above assumptions:
$$\delta S = s_0 \cdot \delta N_{\text{dec}} = s_0 \cdot N_{\text{dec}}^0 \cdot \left(-\frac{\Phi}{S_0}\right) = -S_0 \cdot \frac{\Phi}{S_0} = -\Phi$$

**Honest Annotation**: The correspondence $\delta S = -\Phi$ is the core input for the assembly of the potential terms in this paper. Its rigorous proof requires further axiomatization of the information field encoding of 0.2.2. It is currently a **constructive assumption**, not a rigorous theorem.

---

### §2.2　Hessian Global Scaling

**Constructive Hypothesis 2.2 (Hessian Global Scaling)**: From Definition 1.1 and the Spectral Rigidity Theorem of 0.2.1, it is hypothesized that the Hessian matrix under the breathing mode responds by global scaling:
$$H_{ij}(\Phi) = H_{ij}^{(0)} \cdot \left(1 + \frac{\Phi}{S_0}\right)$$

**Geometric motivation**: By Definition 1.1, $\sqrt{\det H(\Phi)} = \sqrt{\det H_0}(1 + \Phi/S_0)$. There are infinitely many ways to make the square root of the determinant obey this law. Global scaling $H_{ij} \propto (1 + \Phi/S_0)$ is the **simplest hypothesis** — both eigenvalues scale by the same factor, preserving eigen-directions and section topology, consistent with the physical picture of the breathing mode as a "uniform dilation." From the asymmetric twisted-bowl picture of 0.2.1, the bare reference point lies in the slope-waist region, with extreme curvature disparity between the $\xi$-direction (hard mode) and $\eta$-direction (soft mode) ($\Lambda_H \approx 150$). Global scaling means the breathing mode changes curvature in both directions by the same factor, the lowest-order isotropic approximation.

**Honest Annotation**: All derivations below that depend on $H_{ij}(\Phi) = H_{ij}^{(0)}(1 + \Phi/S_0)$ (including the cubic and quartic potential terms) are premised on this constructive hypothesis.

**Corollary 2.3** (rigorously derived from Definition 1.1 and Constructive Hypothesis 2.2):
$$\det H(\Phi) = \det H_0 \cdot \left(1 + \frac{\Phi}{S_0}\right)^2,\quad \sqrt{\det H(\Phi)} = \sqrt{\det H_0} \cdot \left(1 + \frac{\Phi}{S_0}\right)$$

---

## Chapter 3　Geometric Derivation of the Potential Terms

### §3.1　Second-Order Curvature Restoring Force (Mass Term)

**Theorem 3.1 (Mass Term Coefficient)**: The second-order coefficient of the potential for the breathing mode $\Phi$ is locked by the soft mode $\lambda_1$ and the 2D section structure to be $2\lambda_1$:
$$V^{(2)}(\Phi) = 2\lambda_1 \Phi^2$$

*Proof sketch*: From 0.2.1.1, the soft mode $\lambda_1$ is the curvature stiffness of the section in the $\eta$-direction. 0.2.1 Theorem 3.5.10 (Local Harmonic Oscillator Theorem) proves: the soft mode $\lambda_1$ is the linearized frequency $\sqrt{\lambda_1}$ of the Hamiltonian flow on the symplectic manifold $(\mathcal{P}_\eta, \omega)$. The breathing mode $\Phi$, as a scalar collective fluctuation, acquires its restoring force from the intrinsic elasticity of this symplectic-geometric structure.

In the 2D parameter space $(\xi,\eta)$, the Hessian eigenvalues are $\lambda_1(\Phi) = \lambda_1(1 + \Phi/S_0)$ and $\lambda_2(\Phi) = \lambda_2(1 + \Phi/S_0)$ (Constructive Hypothesis 2.2). The local expansion of $S$ in the neighborhood of the section is:
$$S(\xi,\eta;\Phi) = S_0 + \frac{1}{2}\lambda_1(\Phi)\xi^2 + \frac{1}{2}\lambda_2(\Phi)\eta^2 + H_{\xi\eta}(\Phi)\xi\eta + \cdots$$

The potential density is defined as the excess action integral of $S$ over a unit cell of the section. The unit cell area is defined by the spectral-rigidity characteristic scales $\xi_0 = 1/\sqrt{\lambda_1}$, $\eta_0 = 1/\sqrt{\lambda_2}$. Integration:
$$\int_{\text{cell}} [S(\xi,\eta;\Phi) - S_0]\,d\xi\,d\eta = \frac{1}{2}\lambda_1(\Phi)\xi_0^2\eta_0 + \frac{1}{2}\lambda_2(\Phi)\eta_0^2\xi_0 + \cdots$$

Substituting the characteristic scales, the soft-mode direction contributes $\propto \lambda_1(\Phi)/\lambda_1$, and the hard-mode direction contributes $\propto \lambda_2(\Phi)/\lambda_2$. Since $\lambda_2 \gg \lambda_1$, the hard-mode contribution, after the Freezing Theorem of 0.2.1.1, leaves the effective dynamics entirely dominated by the soft mode.

**Origin of the factor 2 (constructive estimate)**: In the area integral $d\xi\,d\eta$ over the 2D section, the two coordinate directions $\xi$ and $\eta$ contribute independently to the soft-mode response. The restoring force coefficient in the soft-mode direction $\eta$ is $\lambda_1$; the indirect contribution of the hard-mode direction $\xi$ to the soft mode via the cross-term $H_{\xi\eta}$ in the frozen limit, after linearization, yields an effective extra $\lambda_1$ (since $|H_{\xi\eta}| \approx 0.52 \ll \sqrt{\lambda_1\lambda_2} \approx 4800$, the cross-term contribution at order $\Phi^2$, after area integration, reduces to the $\lambda_1$ scale). Hence the total second-order coefficient is $2\lambda_1$.

**Honest Annotation**: The rigorous origin of the factor 2 involves a detailed computation of the cross-term in the hard-mode frozen limit and is currently a **constructive estimate**. The "theorem" status of Theorem 3.1's mass term coefficient $2\lambda_1$ applies to the coefficient structure (proportional to $\lambda_1$); the specific value of the factor 2 contains a constructive component. $\square$

**Note 3.1 (Convention alignment with standard scalar fields)**: The Lagrangian density convention in this paper is $\mathcal{L} = \frac{1}{2}(\partial\Phi)^2 - V(\Phi)$, with $V^{(2)} = 2\lambda_1\Phi^2$. The corresponding Klein–Gordon mass squared is $m_{\text{geo}}^2 = 4\lambda_1$ (in geometric units). The Dimensional Bridge mapping in later chapters converts $m_{\text{geo}}$ to a physical mass.

---

### §3.2　Cubic Self-Interaction

**Constructive Hypothesis 3.2**: From Constructive Hypothesis 2.2, the cubic term coefficient is locked by the scale of $S_0$:
$$\mathcal{L}_3 = -\frac{\lambda_1}{S_0}\Phi^3$$

**Derivation (dependent on Constructive Hypothesis 2.2 and Proposition 2.1)**: Substitute $H_{ij}(\Phi) = H_{ij}^{(0)}(1 + \Phi/S_0)$ into the area element density. The cubic term of the potential originates from the nonlinear response of $S$ to $\Phi$. By Proposition 2.1, the linear response of $S(\Phi)$ is $\delta S = -\Phi$. The higher-order response is determined by the nonlinear feedback of the Hessian scaling: when $\Phi$ is finite, the scaling of $H_{ij}$ alters the local gradient structure of $S$, yielding the third derivative of $S(\Phi)$ proportional to $\lambda_1/S_0^2$. After 2D area-integral scale analysis, the cubic coefficient is locked as $\lambda_1/S_0$.

**Honest Annotation**: Not an independent rigorous theorem. Depends on Constructive Hypothesis 2.2 and Proposition 2.1.

---

### §3.3　Quartic Self-Interaction

**Constructive Hypothesis 3.3**: Boundedness of higher-order curvature yields the quartic term:
$$\mathcal{L}_4 = -\frac{\lambda_1}{S_0^2}\Phi^4$$

This term guarantees that the potential is bounded below as $\Phi \to \infty$, preventing unbounded expansion of the section area.

**Honest Annotation**: Same as Constructive Hypothesis 3.2; depends on Constructive Hypothesis 2.2 and Proposition 2.1.

---

### §3.4　Potential Coefficient Locking and Honest Annotation

The geometric potential density is:
$$V(\Phi) = 2\lambda_1\Phi^2 + \frac{\lambda_1}{S_0}\Phi^3 + \frac{\lambda_1}{S_0^2}\Phi^4$$

**Status of each term**:
- $2\lambda_1\Phi^2$: **Theorem** (coefficient structure), factor 2 is a **constructive estimate**;
- $(\lambda_1/S_0)\Phi^3$: **Constructive Hypothesis**;
- $(\lambda_1/S_0^2)\Phi^4$: **Constructive Hypothesis**.

The coefficients $1/S_0$, $1/S_0^2$ are determined by the Hessian scale expansion, premised on Constructive Hypothesis 2.2. The cubic and quartic terms are not independent rigorous theorems.

---

## Chapter 4　Geometric Derivation of the Kinetic Terms

### §4.1　Holographic Information Field Pixel Encoding

From 0.2.2, the Holographic Screen information cells $N_{\text{info}} \approx 9 \times 10^{22}$ constitute a discrete information field. Each pixel $n$ on the geometric constraint section $\Sigma$ carries the Hessian area element density $\sqrt{\det H}$ as its intrinsic state.

**Definition 4.1 (Pixel Fluctuation)**: The fluctuation $\delta_n$ of pixel $n$ is defined as:
$$\delta_n = \frac{\Phi(x_n)}{S_0}$$

**Theorem 4.1 (Pixel Gradient Energy)**: The difference in fluctuations between neighboring pixels $n,m$ generates a configurational entropy cost:
$$\Delta S_{\text{info}} = \frac{1}{2} \sum_{\langle n,m\rangle} (\delta_n - \delta_m)^2$$

*Proof*: From the information field encoding of 0.2.2, a difference in pixel states leads to increased decoherence depth. In 0.0.7, the decoherence depth $N_{\text{dec}}$ is proportional to the squared information difference. $\square$

---

### §4.2　Continuum Limit

**Theorem 4.2 (2D Kinetic Term, Rigorous Theorem)**: In the continuum limit $a \to 0$ of the pixel spacing, the information entropy increase converts into the gradient energy of the area element:
$$\Delta S_{\text{info}} \rightarrow \frac{1}{2} \int_{\Sigma} (\partial_\mu \Phi)^2\,d\xi\,d\eta$$

where $\partial_\mu = (\partial/\partial\xi, \partial/\partial\eta)$ are derivatives on the $\Sigma$ parameter space.

*Proof*: $\delta_n - \delta_m \approx a \cdot \partial_\mu\Phi/S_0$. The sum $\sum \to \int d^2\xi/a^2$. From 0.2.2, the information cell area $a^2 \propto 1/\sqrt{\det H_0}$. The area element density $\sqrt{\det H_0}$ absorbs $a^2$, and the remaining coefficient is given as $1/2$ by 2D Gaussian integral normalization. $\square$

---

### §4.3　Clifford Reduction to 4D Spacetime (Conditional Framework)

**Conditional Framework Declaration (4D Kinetic Term)**: From the scale framework of 0.3.5 and the constructive discussion of the $\text{Cl}(9)$ threefold reduction in 0.1, the extension of the 2D section parameter space $(\xi,\eta)$ to 4D laboratory spacetime coordinates $x^\mu$ preserves the scalar nature of the field $\Phi$ under the Clifford algebraic reduction $\text{Cl}(9) \to \text{Cl}(3,1)$. Under this conditional framework:
$$\mathcal{L}_{\text{kin}} = \frac{1}{2}(\partial_\mu \Phi)^2$$

**Remarks**: 0.3.5 explicitly describes itself as a "scale framework" rather than a "unified interaction theorem"; its gauge group construction belongs to an open research direction. Hence the 4D kinetic term extension depends on the following **not fully proven** assumptions:
1. The mapping between the 2D parameter space $(\xi,\eta)$ and 4D Minkowski spacetime — currently a conditional framework;
2. A rigorous proof that the scalar field $\Phi$ preserves its scalar nature under the $\text{Cl}(3,1)$ reduction — pending further rigorization;
3. A rigorous derivation that the gradient energy takes the form $\partial_\mu\partial^\mu$ from the square of the Dirac operator $\slashed{D}^2$ — an open problem.

**Honest Annotation**: $\mathcal{L}_{\text{kin}} = \frac{1}{2}(\partial_\mu\Phi)^2$ as the 4D kinetic term is a **conditional framework**, not a rigorous theorem. The 2D kinetic term (Theorem 4.2) is a rigorous theorem.
