---
title: "3　Quantum Entanglement and the Geometric Theorem of the Tsirelson Bound"
subtitle: "Geometric Limit of Holographic Screen Pixel Correlations"
version: "260626.6"
date: "2026-06-26"
---

> **Article Number:** 3　　**Version:** 260626.6
>
> **Dependencies:** 0.0.3(260626.6), 0.0.5(260626.6), 0.0.6(260626.6), 0.0.7(260626.6), 0.1(260626.6), 0.1.1(260626.6), 0.1.2(260626.6), 0.2.1(260626.6), 0.2.1.1(260626.6), 0.2.3(260626.6), 0.2.4(260626.6), 0.3.1(260626.6), 0.3.5(260626.6)
>
> **Declaration of Geometric Intrinsic Quantities**: All geometric parameter values in this article are derived from the locked outputs of the single physical mapping of 0.1 and the dimensional bridge of 0.3.1. $S_e=137.035999084$ is the geometric intrinsic quantity of the single core mapping layer (0.1 Derived Item 2.2.1; 0.3.1 Theorem 4.1). $\lambda_1^{\text{eff}}=391.05\ \text{rad}^{-2}$ and $\lambda_2^{\text{eff}}=59324.3\ \text{rad}^{-2}$ are the effective Hessian soft/hard modes after cross-sector coupling (0.1 Derived Item 2.2.4; 0.1 Theorem 6.2). $\theta_M^0=57.93^\circ$, $\theta_C^0=26.16^\circ$, $\theta_I^0=5.91^\circ$ are the bare reference configuration angles (0.2.1 §2.1). $K=839.758793\ \text{keV}$ is the mass quantum (0.3.1 Theorem 9.1). $\chi_L=1.5092231080\times10^{-10}\ \text{m}$, $\chi_T=3.6161912064\times10^{-17}\ \text{s}$, $\hbar=6.5821195675\times10^{-16}\ \text{eV}\cdot\text{s}$ are the dimensional bridge outputs (0.3.1 §6–§7). The speed of light $c=299792458\ \text{m/s}$ is the sole external anchor (0.1 Postulate 1.1). This article does not employ the wavefunction hypothesis, Bell's original derivation, nor introduce Planck's constant as an external input.


# Abstract

This article reconstructs the theory of quantum entanglement on the basis of the three axioms of Geometric Theory, the Nine-Element Mutual Arrest Constraint, and all theorems of the 0.X series (version 260626.6), within the framework of holographic screen pixel structure, using the **single core mapping** (ℰ: ℳ–𝒞 waist-edge coupling → electromagnetic interaction) as the sole physical mapping input. Principal results: (i) Within the framework of holographic screen pixel structure, the information field equation is rigorously derived from the local harmonic oscillator theorem of 0.2.1 (Theorem 3.5.10); pixels are defined by ℐ-sector harmonic oscillator eigenfunctions, with minimum resolvable angle $\Delta\xi_{\min}=2\lambda_2^{-1/4}$; (ii) A geometric definition of entanglement is established—two $S$-minima on the geometric constraint section $\Sigma_\eta$ achieve geometric maximal entanglement through ℐ-sector freezing and ℳ-sector antipodal locking, with variational stability jointly guaranteed by the Nine-Element Mutual Arrest Constraint and cross-sector coupling structure; (iii) The Two-Level Theorem is proved—the low-energy non-trivial excitation space of a geometrically maximally entangled pair is exactly 2-dimensional; (iv) Under the physical mapping conventions, the correlation function $C(\vec{a},\vec{b})=-\vec{a}\cdot\vec{b}$ is derived; (v) In the hypothetical limit $\lambda_2^{\text{eff}}\to\infty$, information field localization is proved, giving a CHSH combination algebraic upper bound of $2$; (vi) Under the condition that $\lambda_2^{\text{eff}}$ is finite and the correlation mapping is accepted, the supremum of the CHSH combination is proved to be $2\sqrt{2}$. In the Appendix, the mapping capacity of Geometric Theory for interference phenomena is demonstrated under the external input hypothesis of a double-slit topological defect; this Appendix does not satisfy the 0.0.X + single core mapping closed-loop criterion.


# 1. Holographic Screen Pixel Theorem

## 1.0 Declaration of the Nine-Element Mutual Arrest Constraint

The following structures treated in this chapter are subject to the Nine-Element Mutual Arrest constraint (0.3.1 Theorem 3.1a; 0.2.1 §1.4):

- **ℐ-sector freezing** (Definition 2.2, Condition 1): corresponds to the hard-mode freezing of the three information-realm elements $(e_7,e_8,e_9)$ among the nine elements—the high-stiffness directions dominated by $\lambda_2^{\text{eff}}$ suppress the information-realm elements to a constant background;
- **Bott periodicity cutoff** (Corollary 1.1a): the cutoff $n_{\text{eff}}\le 7$ is the pixel-level manifestation of $N_{\text{eff}}=7$ in the Nine-Element Mutual Arrest (0.0.7 Theorem 6.3);
- **Soft-hard mode separation** $\lambda_2^{\text{eff}}/\lambda_1^{\text{eff}}=151.7$: corresponds to the stiffness ratio of the Nine-Element Mutual Arrest, locking the scale separation of the dimensional mapping;
- **Tri-decomposition frame** $\{e_1,\dots,e_9\}$: $\{e_1,e_2,e_3\}$ corresponds to the ℳ-sector, $\{e_4,e_5,e_6\}$ to the 𝒞-sector, $\{e_7,e_8,e_9\}$ to the ℐ-sector; its first-order condition $[[D,a],Jb^*J^{-1}]=0$ is restricted to soft mode $\lambda_1^{\text{eff}}$ in the ℳ-sector and hard mode $\lambda_2^{\text{eff}}$ in the $𝒞\oplusℐ$ sector (0.3.1 §3.1a).

## 1.1 Information Field on the Geometric Constraint Section

By the theorem of 0.0.7, the geometric constraint section $\Sigma_\eta\subset\Sigma$ is a 2-dimensional active submanifold, with Hausdorff dimension $D_f=2.000$. By the theorems of 0.2.1 and 0.2.1.1, the tangent bundle of $\Sigma_\eta$ admits a tri-decomposition

$$T\Sigma=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I},$$

and the completeness axiom $\theta_M+\theta_C+\theta_I=\pi/2$ holds.

**Definition 1.1 (Information Field Equation).** The information field $\Psi$ on $\Sigma_\eta$ is derived from the Hamiltonian of the local harmonic oscillator theorem of 0.2.1 (Theorem 3.5.10). In geometric units ($\hbar=1$), the stationary information field satisfies:

$$\left[-\frac{1}{2}\Delta_{\Sigma_\eta} + \frac{1}{2}\lambda_1^{\text{eff}}\eta^2 + \frac{1}{2}\lambda_2^{\text{eff}}\xi^2\right]\Psi = E\Psi,$$

where $\Delta_{\Sigma_\eta}$ is the Laplace-Beltrami operator on $\Sigma_\eta$, $\lambda_1^{\text{eff}}=391.05\ \text{rad}^{-2}$ is the effective soft mode, and $\lambda_2^{\text{eff}}=59324.3\ \text{rad}^{-2}$ is the effective hard mode (0.1 Derived Item 2.2.4; 0.1 Theorem 6.2). This equation is strictly guaranteed by 0.2.1 Theorem 3.5.10: within a Darboux neighborhood of the symplectic manifold $(\mathcal{P}_\eta,\omega)$, the quadratic expansion of the Hamiltonian $H=S(\theta)-S_3$ intrinsically yields the harmonic oscillator structure of the ℐ-sector and the ℳ-𝒞 subspace.

*Geometric Legitimacy Note*: The distinction between Definition 1.1 and 0.2.1 Theorem 3.5.10 is as follows: 0.2.1 Theorem 3.5.10 gives an approximate Hamiltonian $\hat{H} \approx -\frac{\hbar^2}{2}\Delta_{\Sigma_\eta} + \frac{1}{2}\lambda_1\eta^2 + \frac{1}{2}\lambda_2\xi^2$ within a local Darboux neighborhood (geometric units $\hbar=1$); Definition 1.1 promotes this to a global stationary equation on $\Sigma_\eta$. Under the ℐ-sector freezing approximation (see §1.2 below), ℐ and ℳ-𝒞 are approximately decoupled, and the information field equation reduces to a harmonic oscillator equation in the ℐ-direction.

## 1.2 Hard Mode and Characteristic Equation

By 0.2.1 §4.5, the hard-mode eigenvalue of the section Hessian, after cross-sector coupling correction, is

$$\lambda_2^{\text{eff}}=59324.3\ \mathrm{rad}^{-2}.$$

In the one-dimensional approximation of the ℐ-sector (by the completeness axiom and the $(\xi,\eta)$ decoupling structure of 0.2.1 §4.5, with $H_{\xi\eta}=-0.52\approx0$, the ℐ-direction and ℳ-𝒞 subspace are approximately decoupled to second order; the geometric origin of this decoupling is the hard-mode freezing of the three information-realm elements in the Nine-Element Mutual Arrest — 0.3.1 §3.1a), the information field $\Psi_{\mathcal{I}}$ satisfies the harmonic oscillator equation:

$$\left(-\frac{\mathrm{d}^2}{\mathrm{d}\xi^2}+\lambda_2^{\text{eff}}\xi^2\right)\phi_n = \mu_n\phi_n,\quad \xi\in\mathcal{I},$$

where $\mu_n = (2n+1)\sqrt{\lambda_2^{\text{eff}}}$ are the harmonic oscillator eigenvalues.

**Proposition 1.1 (Pixel Orthonormal Basis).** The normalized solutions $\{\phi_n\}_{n=0}^{\infty}$ of the above harmonic oscillator equation constitute a complete orthonormal basis of $L^2(\mathcal{I})$, with ground state

$$\phi_0(\xi)=\left(\frac{\sqrt{\lambda_2^{\text{eff}}}}{\pi}\right)^{1/4}\exp\left(-\frac{\sqrt{\lambda_2^{\text{eff}}}}{2}\xi^2\right),$$

and $n$-th excited state $\phi_n(\xi)=H_n((\lambda_2^{\text{eff}})^{1/4}\xi)\,\phi_0(\xi)$, where $H_n$ are the Hermite polynomials.

*Proof.* The equation is of standard harmonic oscillator type ($m=1$, $\omega=\sqrt{\lambda_2^{\text{eff}}}$); orthonormal completeness follows directly from Sturm-Liouville theory. The ground state form is determined by $\phi_0''/\phi_0=\lambda_2^{\text{eff}}\xi^2-\sqrt{\lambda_2^{\text{eff}}}$ and the normalization $\int|\phi_0|^2\mathrm{d}\xi=1$. This solution form is uniquely determined by the linearization of the local symplectic structure via 0.2.1 Theorem 3.5.10; Geometric Theory supplies the Hessian origin of the parameter $\lambda_2^{\text{eff}}$ (after cross-sector coupling correction, 0.1 Theorem 6.2). ∎

**Note 1.1**: This corrects the erroneous form $(-\mathrm{d}^2/\mathrm{d}\xi^2+\lambda_2)\phi_n=\mu_n\phi_n$ in version 260622.6 of this article. That form confused the harmonic oscillator potential $\lambda_2\xi^2$ with a constant potential $\lambda_2$, and was inconsistent with the given ground state solution $\phi_0\propto\exp(-\sqrt{\lambda_2}\xi^2/2)$. The correct form is a harmonic oscillator equation, with ground state width controlled by $\lambda_2^{-1/4}$.

**Corollary 1.1a (Bott Periodicity Cutoff).** Although the mathematical form is an infinite-dimensional Hermite basis, the physically effective excitations are restricted by the seven-layer cutoff theorem of 0.2.2/0.2.3: the analytically accessible information hierarchy of the material realm is strictly limited to $n_{\text{eff}}\le 7$ (0.0.7 Theorem 6.3), with higher modes $n>7$ confined by Bott periodicity $8$ cutoff. This cutoff is the direct pixel-level manifestation of $N_{\text{eff}}=7$ in the Nine-Element Mutual Arrest (0.3.1 §3.1a). Hence the effective degrees of freedom for pixel encoding are finite-dimensional.

## 1.3 Minimum Resolvable Angle

**Definition 1.2 (Pixel).** A pixel on $\Sigma_\eta$ is the effective support set occupied by a single eigenfunction $\phi_n$ of the information field in the ℐ-sector.

**Constructive Definition 1.3 (Minimum Resolvable Angle).** The minimum resolvable angle between two adjacent pixels in the ℐ-sector is defined by the characteristic width of the ground state $\phi_0$:

$$\Delta\xi_{\min}=2(\lambda_2^{\text{eff}})^{-1/4}.$$

*Constructive Note.* The full width at half maximum (FWHM) of the ground state $\phi_0$ is $2\sqrt{\ln2}\,(\lambda_2^{\text{eff}})^{-1/4}$. As an operational definition, we take twice the characteristic width $2(\lambda_2^{\text{eff}})^{-1/4}$ as the minimum resolvable angle, such that the support sets of $\phi_0(\xi-\Delta\xi_{\min}/2)$ and $\phi_0(\xi+\Delta\xi_{\min}/2)$ are just separated at $1/e$ peak height. This definition is a constructive hypothesis, conceptually borrowing the spirit of the Rayleigh criterion by analogy; rigorous justification requires independent derivation from the information-theoretic resolution limit of the Sturm-Liouville orthonormal basis. Current status is labeled as "geometric analog construction."

Substituting the numerical value:
$$\Delta\xi_{\min}=2\times(59324.3)^{-1/4}=2\times0.06406=0.1281\ \mathrm{rad}.$$

*Comparison*: Version 260622.6 used the erroneous formula $\pi/(2\sqrt{\lambda_2})\approx6.48\times10^{-3}$ rad, due to the incorrect form of the information field equation (constant potential rather than harmonic oscillator potential), leading to underestimation of the pixel scale. The harmonic oscillator ground state width $\lambda_2^{-1/4}$ is far larger than the $\lambda_2^{-1/2}$ scale.

**Corollary 1.3 (Quantization).** The finiteness of $\lambda_2^{\text{eff}}$ quantizes the ℐ-sector angle in harmonic oscillator energy levels. If $\lambda_2^{\text{eff}}\to\infty$, then $\Delta\xi_{\min}\to0$, and pixel encoding tends toward the continuum.

## 1.4 Connection to the Spectral Triple Toolkit

The dimensionful constants $\chi_L$, $\hbar$, $K$ used in this section are derived from the spectral triple framework of the 0.3.1 dimensional bridge (0.3.1 Theorems 3.1–3.5):

- The spectral origin of $\chi_L$ is the ℳ-sector Wodzicki residue (0.3.1 Theorem 3.2, $C_J$ to be determined);
- The spectral origin of $K$ is the ℳ-sector Dixmier trace (0.3.1 Theorem 3.4, $C_m$ to be determined);
- The spectral origin of $\hbar$ is the 9-dimensional heat kernel spectral asymmetry term (0.3.1 Theorems 3.3/3.5).

The pixel quantization (harmonic oscillator basis) of this article is a simplified treatment under the ℐ-sector freezing approximation. In the full spectral triple framework, pixels should be given by the restriction of the eigenspinors of the Dirac operator $D$ on $M(a)$ to $\Sigma_\eta$, corresponding to the natural continuation of Toeplitz quantization (0.0.6 §6). The current Hermite basis construction is the ℐ-frozen limit approximation of this continuous quantization; rigorous treatment awaits follow-up work.


# 2. Geometric Definition of Entanglement

## 2.1 $S$-Minima and Particles

By the theorems of 0.0.5/0.0.6, local depressions (isolated minima of $S$) on $\Sigma_\eta$ correspond to stable particle states. The electron ground state corresponds to $S_e=137.035999084$ (0.1 Derived Item 2.2.1).

**Single Core Mapping Declaration.** The entanglement theory of this article is strictly built upon the single core mapping layer (0.1 §1.3): all readout directions and measurement mappings are realized through ℳ-𝒞 waist-edge coupling (electromagnetic sector), necessarily accompanied by a massive source mode (electron, $E_{\mathcal{M}}\approx511\ \text{keV}$) and a massless propagation mode (photon, speed $c$), both sharing the same coupling constant $S_e=137.035999084$; the ℐ sector does not map to an independent particle, serving only as an information/phase channel. The speed of light $c$ is the sole external anchor (0.1 Postulate 1.1).

**Definition 2.1 (Correlation Geodesic).** Let $p_A,p_B\in\Sigma_\eta$ be two $S$-minima. A curve $\gamma_{AB}:[0,1]\to\Sigma_\eta$ connecting $p_A,p_B$ is called a **correlation geodesic** if the projection of $\gamma_{AB}$ onto the ℳ-sector is a geodesic, and its projection onto the ℐ-sector is a constant.

**Definition 2.2 (Geometric Maximal Entanglement).** Two $S$-minima $p_A,p_B$ are said to be **geometrically maximally entangled** if their correlation geodesic $\gamma_{AB}$ satisfies:

1. **ℐ-sector freezing**: $\xi_A=\xi_B$, i.e., the projection of $\gamma_{AB}$ onto ℐ is a single point;
2. **ℳ-sector antipodal locking**: the projection of $\gamma_{AB}$ onto the ℳ-sector $S^3$ is a closed geodesic (great circle), with $p_A,p_B$ located at antipodal points of this great circle.

The variational stability of this configuration is jointly guaranteed by the following geometric structures:

**(i) Nine-Element Mutual Arrest Constraint** (0.3.1 Theorem 3.1a): the first-order condition $[[D,a],Jb^*J^{-1}]=0$ imposes hard-mode freezing in the ℐ-sector; the high stiffness of $\lambda_2^{\text{eff}}$ strongly suppresses deviations in the ℐ-direction, so that $\xi_A=\xi_B$ is a stable condition;

**(ii) Cross-sector coupling structure** (0.1 Theorems 4.2/4.3): the infiltration matrix $\Phi$ and cross-sector coupling $H^W=[[2w,w'-2w],[w'-2w,2w]]$ (waist edge $w=-0.7885$, base edge $w'=-2.444$) constitute the algebraic constraints of the ℳ-𝒞-ℐ trifurcated tangent bundle;

**(iii) Weak coupling condition** (0.1/0.4): the information-realm block correlation parameter $\gamma=H_{CI}/\sqrt{H_{CC}\cdot H_{II}}=0.0928\ll1$ ensures weak coupling between the causal field and information field, so that antipodal points are promoted to stable extrema under the constraints.

Definition 2.2 is a **working definition** of geometric maximal entanglement; its correspondence with the "maximally entangled state" of quantum mechanics is a convention of the physical mapping layer (see §4 Correlation Function), not an intrinsic theorem of Geometric Theory.

*Geometric Interpretation.* Condition 1 is guaranteed by the ℐ-sector harmonic oscillator structure: if two pixels are separated in the ℐ-sector by $\Delta\xi<\Delta\xi_{\min}$, their information fields are approximately indistinguishable in the $L^2$ sense. Geometric maximal entanglement requires $\Delta\xi=0$, i.e., sharing the same ℐ-sector pixel. Condition 2 is derived from the minimum action principle $S_{\text{total}}=0$ and the above cross-sector coupling structure: on the ℳ-sector $S^3$, the extremal curve connecting two points is a geodesic; antipodal points become stable extrema under the joint constraints of ℐ-freezing and waist-edge coupling.

## 2.2 Rigorous Definition of the Entanglement String

**Definition 2.3 (Geometric Entanglement String).** The **geometric entanglement string** $\mathcal{E}_{AB}$ of a geometrically maximally entangled pair $(p_A,p_B)$ is the image of the correlation geodesic $\gamma_{AB}$ in $\Sigma_\eta$, equipped with the induced connection $\nabla^{\mathcal{I}}$ derived from $S_{\text{total}}=0$.

**Proposition 2.1 (Length of the Geometric Entanglement String).** The geometric length $L(\mathcal{E}_{AB})$ of the geometric entanglement string $\mathcal{E}_{AB}$ is determined by the geodesic distance on the ℳ-sector $S^3$:

$$L(\mathcal{E}_{AB})=\pi R_{\mathcal{M}},$$

where $R_{\mathcal{M}}$ is the effective curvature radius of the ℳ-sector. The identification $R_{\mathcal{M}}^{-2}=\lambda_1^{\text{eff}}/2$ is a working hypothesis of this article—$\lambda_1^{\text{eff}}=391.05\ \text{rad}^{-2}$ is the effective soft-mode Hessian eigenvalue (dimension $\text{rad}^{-2}$); identifying it as the sectional curvature of $S^3$ requires additional geometric justification (the scalar curvature of $S^3(r)$ is $6/r^2$, sectional curvature is $1/r^2$). This identification has not been rigorously proved in 0.X.X and is currently labeled as "geometric correspondence hypothesis."

Substituting $\lambda_1^{\text{eff}}=391.05\ \text{rad}^{-2}$:
$$R_{\mathcal{M}}=\sqrt{\frac{2}{391.05}}=0.07151\ \text{rad},\quad L(\mathcal{E}_{AB})=\pi R_{\mathcal{M}}=0.2247\ \text{rad}.$$

This length is independent of the 3-dimensional spatial distance into which $\Sigma_\eta$ is embedded. ∎


# 3. The Two-Level Theorem

## 3.1 Low-Energy Excitation Space

Consider the joint information field $\Psi_{AB}$ of a geometrically maximally entangled pair $(p_A,p_B)$ on $\Sigma_\eta$. By the theorem of 0.2.3, the soft mode $\lambda_1^{\text{eff}}=391.05\ \text{rad}^{-2}$ controls the diffusion scale of the ℳ-sector.

**Theorem 3.1 (Two-Level Theorem).** Let the ℳ-sector geodesic distance satisfy $d_{\mathcal{M}}(p_A,p_B)<\pi/\sqrt{\lambda_1^{\text{eff}}}$. Then the low-energy non-trivial excitation space of the joint information field $\Psi_{AB}$ (the relative excitation space, after subtracting the constant ground state/center-of-mass mode of the joint information field, with energy below $2\lambda_1^{\text{eff}}$) is exactly 2-dimensional, spanned by the two antiphase branches of the first zonal harmonic function on the ℳ-sector.

*Proof.* By the theorem of 0.2.1, the ℳ-sector corresponds to an $S^3$ factor. The eigenvalues of the Laplace-Beltrami operator on $S^3$ are $\ell(\ell+2)/R_{\mathcal{M}}^2$ ($\ell=0,1,2,\ldots$), where $\ell=0$ is the constant ground state, $\ell=1$ is the 4-fold degenerate first excited state with eigenvalue $3\lambda_1^{\text{eff}}/2$; $\ell=2$ has eigenvalue $4\lambda_1^{\text{eff}}$.

By the completeness axiom $\theta_M+\theta_C+\theta_I=\pi/2$ and the 2-dimensional constraint of $\Sigma_\eta$, the effective projection of the ℳ-sector onto $\Sigma_\eta$ is realized by the projection map $P_{\mathcal{M}}:\mathcal{M}\to\Sigma_\eta$ of 0.0.6. Under the Nine-Element Mutual Arrest constraint (0.3.1 Theorem 3.1a), the first-order condition of the tri-decomposition frame $\{e_1,\dots,e_9\}$ gives the tangent space of the ℳ-sector ($e_1,e_2,e_3$) a projection of rank 2 onto the 2-dimensional tangent plane of $\Sigma_\eta$. Hence the 4-fold degeneracy is partially broken, retaining only 2 zonal modes adapted to the tangent space of $\Sigma_\eta$, denoted $\Phi_+,\Phi_-$, satisfying $\Phi_-(\vec{x})=\Phi_+(-\vec{x})$ (antipodal antiphase).

The $\ell=0$ constant ground state corresponds to the global phase/center-of-mass degree of freedom of the joint information field, which is frozen and subtracted in the relative coordinate description of the entangled pair (the geometric mechanism of this subtraction is compatible with the completeness axiom: center-of-mass motion corresponds to global translation of $\theta_M$, which does not contribute to relative phase under ℐ-freezing conditions); the remaining $\ell=1$ first excited state retains 2 dimensions under the rank-2 restriction of the projection map. The low-energy cutoff threshold $2\lambda_1^{\text{eff}}$ lies between the $\ell=1$ eigenvalue $3\lambda_1^{\text{eff}}/2$ and the $\ell=2$ eigenvalue $4\lambda_1^{\text{eff}}$, hence the non-trivial excitation space dimension is 2. ∎

*Physical Mapping Note*: This 2-dimensional space corresponds, at the physical mapping layer, to the state space of a qubit. Geometric Theory does not independently predict the post-measurement state evolution of quantum mechanics; it provides only the geometric description of states.

**Definition 3.2 (Information Basis States).** Denote the orthonormal basis of the two-level space by $\varepsilon_1,\varepsilon_2$, satisfying

$$\varepsilon_1(\vec{x})=\Phi_+(\vec{x}),\quad \varepsilon_2(\vec{x})=\Phi_-(\vec{x})=\Phi_+(-\vec{x}),$$

where $\vec{x}$ are coordinates on the ℳ-sector $S^3$.


# 4. The Correlation Function Theorem

## 4.1 Readout Directions and Measurement Results

**Definition 4.1 (Readout Direction).** Choose a unit vector $\vec{a}$ on the ℳ-sector $S^3$ (i.e., a point on $S^3\subset\mathbb{R}^4$), called the readout direction.

**Definition 4.2 (Geometric-Measurement Correspondence — Physical Mapping Layer Convention).** As a **physical mapping convention**, the measurement result $m(\vec{a})$ of the information field $\Psi$ in the readout direction $\vec{a}$ is defined as the sign of the zonal projection of $\Psi$ at $\vec{a}$:

$$m(\vec{a})=\operatorname{sgn}\left(\int_{S^3}\Psi(\vec{x})Z_{\vec{a}}(\vec{x})\mathrm{d}\mu\right)\in\{+1,-1\},$$

where $Z_{\vec{a}}(\vec{x})=\vec{a}\cdot\vec{x}$ is the first zonal harmonic function. The correspondence of this definition with spin measurement results in standard quantum mechanics is a hypothesis of the bridging layer, not an intrinsic definition of Geometric Theory.

*Note.* By Theorem 3.1, a low-energy excitation $\Psi=c_1\varepsilon_1+c_2\varepsilon_2$ has projection $c_1\vec{a}\cdot\vec{x}_++c_2\vec{a}\cdot\vec{x}_-$ on $Z_{\vec{a}}$, with sign determined by the coefficient ratio.

## 4.2 Correlation Function

**Definition 4.3 (Correlation Function).** For a geometrically maximally entangled pair $(p_A,p_B)$, let $\vec{a}$ be the readout direction of $p_A$ and $\vec{b}$ be the readout direction of $p_B$. The correlation function $C(\vec{a},\vec{b})$ is defined as the geometric mean of the product of measurement results over the information field ensemble:

$$C(\vec{a},\vec{b})=\big\langle m_A(\vec{a})m_B(\vec{b})\big\rangle_{\Sigma},$$

where $\langle\cdot\rangle_{\Sigma}$ is the information field ensemble average naturally defined by the induced connection $\nabla^{\mathcal{I}}$ of the geometric entanglement string and the symplectic structure $(\mathcal{P}_\eta,\omega)$ of $\Sigma_\eta$ (0.2.1 Theorem 3.5.1).

**Mapping-Layer Proposition 4.1 (Correlation Function).** For a geometrically maximally entangled pair, under the following physical mapping conventions:

> **Convention A (Antipodal Antiphase)**: the ℳ-coordinate of $p_B$ satisfies $\vec{x}_B=-\vec{x}_A$, hence $m_B(\vec{b})=-m_A(\vec{b})$;
>
> **Convention B (Born Rule Correspondence)**: under the natural symplectic measure of $\Sigma_\eta$, the single-depression response to two readout directions satisfies $\langle m_A(\vec{a})m_A(\vec{b})\rangle_{\Sigma}=\vec{a}\cdot\vec{b}$. This equality is a geometric property of $S^3$ harmonic functions under ensemble averaging; in the physical mapping it corresponds to the Born rule of quantum mechanics. This correspondence is **not** a theorem derived from the three axioms, but a mapping-layer convention translating the measurement rules of quantum mechanics into geometric language.

we have

$$C(\vec{a},\vec{b})=-\vec{a}\cdot\vec{b}=-\cos\theta_{ab},$$

where $\theta_{ab}$ is the geodesic angle between $\vec{a},\vec{b}$ on the ℳ-sector $S^3$.

*Derivation.* By Convention A, $m_B(\vec{b})=-m_A(\vec{b})$. By Convention B, $\langle m_A(\vec{a})m_A(\vec{b})\rangle_{\Sigma}=\vec{a}\cdot\vec{b}$. Hence

$$C(\vec{a},\vec{b})=\big\langle m_A(\vec{a})(-m_A(\vec{b}))\big\rangle_{\Sigma}=-\vec{a}\cdot\vec{b}.$$

∎

**Honest Annotation**: The conclusion $C(\vec{a},\vec{b})=-\vec{a}\cdot\vec{b}$ of Proposition 4.1 is mathematically equivalent in form to the correlation function of a spin singlet state in quantum mechanics, but this is **a derived result after accepting Convention A and Convention B**. Convention A has a relatively solid geometric foundation (antipodal locking → antiphase, guaranteed by Definition 2.2); Convention B is the core bridge of the physical mapping, whose rigor is equivalent to "deriving the Born rule from the three axioms"—this is one of the core open problems of Geometric Theory. Hence the status of Proposition 4.1 is a **mapping-layer proposition**, not an intrinsic theorem of Geometric Theory.
# 5. CHSH Combination and the Classical Limit

## 5.1 Geometrization of Measurement Settings

**Definition 5.1 (CHSH Configuration).** On the ℳ-sector $S^3$, select four readout directions:

- Particle $A$: $\vec{a}_1,\vec{a}_2$
- Particle $B$: $\vec{b}_1,\vec{b}_2$

**Definition 5.2 (CHSH Combination).**

$$S_{\text{CHSH}}=C(\vec{a}_1,\vec{b}_1)+C(\vec{a}_1,\vec{b}_2)+C(\vec{a}_2,\vec{b}_1)-C(\vec{a}_2,\vec{b}_2).$$

## 5.2 The Classical Limit Theorem

**Theorem 5.1 (Classical Limit).** Consider the hypothetical limiting case $\lambda_2^{\text{eff}}\to\infty$, where the ℐ-sector is fully compactified. This limit does not represent actual physics (in Geometric Theory, $\lambda_2^{\text{eff}}=59324.3$ is a fixed constant, 0.1 Theorem 6.2); it serves only as a thought experiment to contrast the difference between classical and quantum correlations. In this limit, the information field is localized, and the algebraic upper bound of the CHSH combination is $2$.

*Proof.* When $\lambda_2^{\text{eff}}\to\infty$, by Constructive Definition 1.3, the ℐ-sector pixels become infinitely dense ($\Delta\xi_{\min}\to0$), and the information field is fully localized. The ℐ-freezing of the geometric entanglement string $\mathcal{E}_{AB}$ is lifted, and the ℳ-sectors of $p_A,p_B$ are fully decoupled. Hence $m_A(\vec{a})$ depends only on the local geometry of $p_A$, and $m_B(\vec{b})$ depends only on the local geometry of $p_B$; the two are approximately independent in the limit. Substituting into Definition 5.2:

$$|S_{\text{CHSH}}|\le |m_B(\vec{b}_1)+m_B(\vec{b}_2)|+|m_B(\vec{b}_1)-m_B(\vec{b}_2)|=2.$$

This theorem does not rely on Bell's inequality; it is a purely algebraic corollary in the geometric limit. ∎

*Note.* This upper bound $2$ is a purely algebraic consequence of factorization in the $\lambda_2^{\text{eff}}\to\infty$ limit, requiring no hidden-variable distribution hypothesis as in Bell's original derivation.


# 6. The Tsirelson Theorem

## 6.1 Preservation of Nonlocal Correlations

**Theorem 6.1 (Tsirelson Bound).** Under the discrete encoding with finite $\lambda_2^{\text{eff}}$ (i.e., with ℐ-sector freezing effective), and accepting the correlation mapping of Proposition 4.1, the CHSH combination satisfies

$$|S_{\text{CHSH}}|\le 2\sqrt{2}.$$

The supremum $2\sqrt{2}$ is attained by the following configuration:

$$\vec{b}_1\perp\vec{b}_2,\quad \vec{a}_1=\frac{\vec{b}_1+\vec{b}_2}{|\vec{b}_1+\vec{b}_2|},\quad \vec{a}_2=\frac{\vec{b}_1-\vec{b}_2}{|\vec{b}_1-\vec{b}_2|}.$$

*Proof.* By Proposition 4.1, $C(\vec{a},\vec{b})=-\vec{a}\cdot\vec{b}$. Substituting into Definition 5.2:

$$S_{\text{CHSH}}=-\vec{a}_1\cdot(\vec{b}_1+\vec{b}_2)-\vec{a}_2\cdot(\vec{b}_1-\vec{b}_2).$$

By the Cauchy-Schwarz inequality:

$$S_{\text{CHSH}}\le|\vec{a}_1||\vec{b}_1+\vec{b}_2|+|\vec{a}_2||\vec{b}_1-\vec{b}_2|=|\vec{b}_1+\vec{b}_2|+|\vec{b}_1-\vec{b}_2|,$$

Let $\vec{b}_1\cdot\vec{b}_2=\cos\theta$; then $|\vec{b}_1+\vec{b}_2|=2\cos(\theta/2)$, $|\vec{b}_1-\vec{b}_2|=2\sin(\theta/2)$. Hence

$$S_{\text{CHSH}}\le 2(\cos(\theta/2)+\sin(\theta/2))\le 2\sqrt{2},$$

with equality when $\theta=\pi/2$ (i.e., $\vec{b}_1\perp\vec{b}_2$) and $\vec{a}_1\parallel(\vec{b}_1+\vec{b}_2)$, $\vec{a}_2\parallel(\vec{b}_1-\vec{b}_2)$. Then $|S_{\text{CHSH}}|=2\sqrt{2}$. ∎

## 6.2 Why $2\sqrt{2}$

**Structural Note 6.2.** $2\sqrt{2}=\sqrt{8}$ is directly related to the 2-dimensionality of the ℳ-sector readout plane. Numerically, the appearance of $\sqrt{8}$ has a potential correspondence with the eight-dimensional structure containing $\text{Spin}(8)$ triality within the even subalgebra $Cl^0(9)\cong Cl(8)$ of the $Cl(9)$ interaction framework of 0.3.5 (0.3.5 §2). The Tsirelson supremum is strictly locked by Cauchy-Schwarz optimization in the 2-dimensional Euclidean geometry of the ℳ-sector; the connection of its deep algebraic origin with the 8-dimensional Clifford algebra of $Cl(8)$ and the overall structure of the trifurcated tangent bundle $T\Sigma=\mathcal{M}\oplus\mathcal{C}\oplus\mathcal{I}$ is an open problem, to be explored in subsequent articles.


# 7. Conclusion

(1) **Pixel Theorem**: Holographic screen pixels are defined by ℐ-sector harmonic oscillator eigenfunctions (Proposition 1.1); the minimum resolvable angle $\Delta\xi_{\min}=2(\lambda_2^{\text{eff}})^{-1/4}=0.1281$ rad is a constructive definition based on the characteristic width of the harmonic oscillator ground state (Constructive Definition 1.3); rigorous justification requires independent derivation from the information-theoretic resolution limit of the Sturm-Liouville orthonormal basis. This article corrects the formal error in the information field equation of version 260622.6 (constant potential → harmonic oscillator potential). The Bott periodicity cutoff ensures that effective pixel degrees of freedom are finite ($n_{\text{eff}}\le7$). The Nine-Element Mutual Arrest constraint (0.3.1 §3.1a) is the deep geometric origin of ℐ-sector freezing and the Bott cutoff.

(2) **Entanglement Definition**: Geometric maximal entanglement is the geometric configuration of two $S$-minima on $\Sigma_\eta$ with ℐ-sector freezing and ℳ-sector antipodal locking. Variational stability is jointly guaranteed by the Nine-Element Mutual Arrest constraint (0.3.1 Theorem 3.1a), cross-sector coupling structure (0.1 Theorems 4.2/4.3: waist edge $w=-0.7885$, base edge $w'=-2.444$), and weak coupling parameter $\gamma=0.0928$. The geometric entanglement string length $L(\mathcal{E}_{AB})=\pi R_{\mathcal{M}}=0.2247$ rad (using effective soft mode $\lambda_1^{\text{eff}}=391.05$).

(3) **Two-Level Theorem**: The low-energy non-trivial excitation space of a geometrically maximally entangled pair is exactly 2-dimensional, spanned by the two antiphase branches of the first zonal harmonic function on $S^3$; the "qubit" is a product of geometric spectral rigidity (physical mapping layer correspondence). The $\ell=0$ constant ground state is frozen and subtracted in the relative coordinate description.

(4) **Correlation Function**: Accepting antipodal antiphase (Convention A, guaranteed by Definition 2.2) and Born rule correspondence (Convention B, physical mapping convention), $C(\vec{a},\vec{b})=-\vec{a}\cdot\vec{b}$. Proposition 4.1 is a mapping-layer proposition, not an intrinsic theorem of Geometric Theory.

(5) **Classical Limit**: In the hypothetical $\lambda_2^{\text{eff}}\to\infty$ limit, the information field is localized, and the CHSH combination upper bound $2$ is an algebraic identity of factorization.

(6) **Tsirelson Theorem**: Accepting the correlation mapping of Proposition 4.1, $|S_{\text{CHSH}}|\le2\sqrt{2}$ is strictly locked by Cauchy-Schwarz optimization in the 2-dimensional Euclidean geometry of the ℳ-sector. The value $2\sqrt{2}=\sqrt{8}$ has a potential correspondence with the algebraic structure of $Cl(8)$.

(7) **Closed-Loop Status**: Chapters 1–6 of this article are completed within the closure of 0.0.X + single core mapping, introducing no independent hypotheses beyond the Nine-Element Mutual Arrest and the three axioms. Convention A is guaranteed by the geometric configuration of Definition 2.2; Convention B is an external correspondence of the physical mapping layer, labeled as an open core problem. Appendix A demonstrates the mapping capacity of Geometric Theory for interference phenomena under the external input hypothesis of a double-slit topological defect, and does not satisfy the closed-loop criterion.

(8) **Version Upgrade**: 260622.6 → 260626.6. Principal changes: corrected information field equation (constant potential → harmonic oscillator potential); comprehensive parameter upgrade to effective metric values ($\lambda_1^{\text{eff}}=391.05$, $\lambda_2^{\text{eff}}=59324.3$); explicit introduction of Nine-Element Mutual Arrest constraint (§1.0); strict labeling of all theorem/proposition statuses; corrected source citations; Chapter 7 moved to Appendix A.


# Appendix A: Electron Double-Slit Interference Theorem (Geometric Model Conjecture)

**External Input Declaration**: This Appendix demonstrates the mapping capacity of Geometric Theory for interference phenomena under the external input hypothesis of a double-slit topological defect. The hypothesis assumes the existence of two disjoint topological holes on $\Sigma_\eta$ (removal of two small disks, corresponding to the double slit); this hypothesis is not a theorem derived from the ℰ mapping or the three axioms, but an external geometric input. Hence this Appendix **does not satisfy** the closed-loop criterion that "0.0.X + single core mapping suffices to compute all quantities, requiring no further anchors or inputs." Status is labeled as **geometric model conjecture**.

## A.1 Topological Defects and Circulating Flows

**Definition A.1 (Double-Slit Defect — External Hypothesis).** On $\Sigma_\eta$, the double slits $A,B$ are two disjoint topological holes (removal of two small disks), with center separation $d_\eta$ (geometric intrinsic quantity).

**Model Description A.1 (Circulating Flow Decomposition).** When a single $S$-minimum (electron) propagates to the double-slit plane, due to the topological non-triviality of $\Sigma_\eta$ (doubly connected region), the information field $\Psi$ decomposes into two circulating flow branches $\Psi_A,\Psi_B$, propagating around slits $A,B$ respectively. By the 2-dimensionality of $\Sigma_\eta$, after removing the two disks, $H_1(\Sigma_\eta\setminus\{A,B\})=\mathbb{Z}\oplus\mathbb{Z}$. Under the Dirichlet zero boundary condition specified by the infiltration function analytic framework of 0.2.1.1, the information field, as a harmonic section on $\Sigma_\eta$, satisfies winding number conservation in topologically non-trivial regions, hence decomposes into two branches respectively encircling the two holes.

## A.2 Phase Difference and Connection

**Proposition A.1 (Phase Theorem).** The phase difference between the two circulating flow branches $\Psi_A,\Psi_B$ at the detection screen is

$$\Delta\phi=\sqrt{\lambda_1^{\text{eff}}}\cdot\Delta L_\eta,$$

where $\Delta L_\eta=|L_A-L_B|$ is the difference in geometric angular path lengths of the two branches on $\Sigma_\eta$ (unit: rad).

*Derivation.* By the local harmonic oscillator theorem of 0.2.1 (Theorem 3.5.10), in Darboux coordinates, the Hamiltonian flow in the soft-mode direction yields the phase connection $\omega=\sqrt{\lambda_1^{\text{eff}}}\,\mathrm{d}\eta$ (geometric units $\hbar=1$). The circulating flow phase is given by the integral of the connection along the path: $\phi_{A,B}=\int_{\gamma_{A,B}}\omega$. Hence $\Delta\phi=\sqrt{\lambda_1^{\text{eff}}}\oint_{\gamma_A-\gamma_B}\mathrm{d}\eta=\sqrt{\lambda_1^{\text{eff}}}\Delta L_\eta$. ∎

*Note*: The phase connection $\omega=\sqrt{\lambda_1^{\text{eff}}}\,\mathrm{d}\eta$ is here constructed in the soft-mode direction; its relationship to 0.2.1 Theorem 3.5.4 (Hamiltonian Flow Frequency Theorem, giving frequency $\sqrt{\det H}/A_0$) is: under the ℐ-freezing approximation, the soft-mode direction $\eta$ evolves independently, with its phase accumulation rate controlled by $\sqrt{\lambda_1^{\text{eff}}}$. Rigorous derivation requires starting from the full Hamiltonian of 0.2.1 Theorem 3.5.10, in the $(\xi,\eta)$ decoupling limit.

## A.3 Interference Fringes

**Proposition A.2 (Fringe Spacing).** Under the far-field condition $L_\eta\gg d_\eta$, the spacing between adjacent bright fringes (fringe spacing) is

$$\Delta x_\eta=\frac{2\pi L_\eta}{\sqrt{\lambda_1^{\text{eff}}}d_\eta}.$$

*Derivation.* Bright fringe condition $\Delta\phi=2n\pi$, path difference $\Delta L_\eta\approx d_\eta x_\eta/L_\eta$ (far-field approximation). Substitute into Proposition A.1. ∎

## A.4 Dimensional Bridge Conversion and Numerical Verification

By the 0.3.1 dimensional bridge, laboratory length $x=\chi_L x_\eta$. Fringe spacing:

$$\Delta x=\chi_L\Delta x_\eta=\frac{2\pi\chi_L L}{\sqrt{\lambda_1^{\text{eff}}}d}.$$

**Proposition A.3 (Geometric Correspondence of the de Broglie Wavelength).** Define the geometric characteristic momentum $p_0$ satisfying $\chi_L p_0=\hbar$ (0.3.1 dimensional bridge triple lock). Then the fringe spacing can be written as

$$\Delta x=\frac{\lambda L}{d},\quad \lambda=\frac{2\pi\hbar}{p}=\frac{h}{p}.$$

**Numerical Verification.** Take experimental parameters: accelerating voltage $U=50\ \text{V}$, slit separation $d=1.0\ \mu\text{m}$, screen distance $L=1.0\ \text{m}$. Using 0.3.1 locked constants:

- $m_e=510.99895\ \text{keV}/c^2$ (0.1 Derived Item 2.2.2)
- $\hbar=6.5821195675\times10^{-16}\ \text{eV}\cdot\text{s}$ (0.3.1 Theorem 7.2)
- $c=299792458\ \text{m/s}$ (sole external anchor)

Kinetic energy $E_k=50\ \text{eV}$, non-relativistic momentum $pc=\sqrt{2m_ec^2E_k}=7148.4\ \text{eV}$, wavelength $\lambda=hc/(pc)$. From $\hbar c=1.973269804\times10^{-7}\ \text{eV}\cdot\text{m}$:

$$\lambda=\frac{2\pi\times1.97327\times10^{-7}}{7148.4}=1.734\times10^{-10}\ \text{m}=1.734\ \text{\AA}.$$

Fringe spacing $\Delta x=\lambda L/d=1.734\times10^{-4}\ \text{m}=0.1734\ \text{mm}$. This result agrees with the standard quantum mechanical formula $\lambda=h/p$ to within $10^{-4}$ relative precision. However, note: $h$ here is a **0.3.1 dimensional bridge derived quantity**, not an external input.

**Honest Annotation**: The derivation in this Appendix takes the external input of a double-slit topological defect as its premise (Definition A.1), and does not satisfy the closed-loop criterion. Its retention as an Appendix is for the purpose of demonstrating the mapping capacity of Geometric Theory for interference phenomena under the topological defect hypothesis, while honestly labeling its conjectural status.


# Appendix B: Table of Endogenous Constants

| Constant | Value | Geometric Origin |
|:---|:---|:---|
| $S_e$ | $1.37035999084\times10^2$ | Geometric intrinsic quantity of single core mapping layer (0.1 Derived Item 2.2.1) |
| $\lambda_1^{\text{eff}}$ | $3.9105\times10^2\ \text{rad}^{-2}$ | Effective soft mode (0.1 Theorem 6.2) |
| $\lambda_2^{\text{eff}}$ | $5.93243\times10^4\ \text{rad}^{-2}$ | Effective hard mode (0.1 Theorem 6.2) |
| $\lambda_2^{\text{eff}}/\lambda_1^{\text{eff}}$ | $1.517\times10^2$ | Effective soft-hard mode ratio (Nine-Element Mutual Arrest stiffness ratio, 0.3.1 §3.1a) |
| $\Delta\xi_{\min}$ | $2(\lambda_2^{\text{eff}})^{-1/4}=0.1281\ \text{rad}$ | Pixel minimum resolvable angle (Constructive Definition 1.3) |
| $R_{\mathcal{M}}$ | $\sqrt{2/\lambda_1^{\text{eff}}}=0.07151\ \text{rad}$ | ℳ-sector effective curvature radius (working hypothesis) |
| $L(\mathcal{E}_{AB})$ | $\pi R_{\mathcal{M}}=0.2247\ \text{rad}$ | Geometric entanglement string length (Proposition 2.1) |
| $\chi_L$ | $1.5092231080\times10^{-10}\ \text{m}$ | Length mapping factor (0.3.1 §6) |
| $\hbar$ | $6.5821195675\times10^{-16}\ \text{eV}\cdot\text{s}$ | Dimensional bridge derived (0.3.1 Theorem 7.2) |
| $K$ | $839.758793\ \text{keV}$ | Mass quantum (0.3.1 Theorem 9.1) |
| $m_e$ | $510.99895\ \text{keV}/c^2$ | Electron mass (0.1 Derived Item 2.2.2) |
| $w$ | $-0.7885$ | Waist-edge coupling (0.1 Theorem 4.3) |
| $w'$ | $-2.444$ | Base-edge coupling (0.1 Theorem 4.3) |
| $\gamma$ | $0.0928$ | Block correlation parameter (0.4) |
| $S_{\text{CHSH}}$ (classical limit) | $2$ | Classical Limit Theorem (§5.2, hypothetical limit) |
| $S_{\text{CHSH}}$ (quantum) | $2\sqrt{2}\approx2.828427$ | Tsirelson Theorem (§6.1, accepting Conventions A+B) |


# Document Version Notes

> **Article Number:** 3　　**Title:** Quantum Entanglement and the Geometric Theorem of the Tsirelson Bound　　**Version:** 260626.6
>
> **Revision Record (260622.6 → 260626.6):**
>
> - **Version number**: 260622.6 → 260626.6; all dependencies upgraded to 260626.6
> - **§1.0 (new)**: Explicit introduction of the Nine-Element Mutual Arrest constraint declaration, connecting ℐ-sector freezing, Bott periodicity cutoff, soft-hard mode separation, and tri-decomposition frame structure to the Nine-Element Mutual Arrest framework of 0.3.1 §3.1a and 0.2.1 §1.4
> - **§1.1**: Corrected information field equation — from $(\Delta_{\Sigma_\eta}+\Lambda)\Psi=0$ (erroneous: Λ parameter of unclear origin) to $[-\frac{1}{2}\Delta_{\Sigma_\eta}+\frac{1}{2}\lambda_1^{\text{eff}}\eta^2+\frac{1}{2}\lambda_2^{\text{eff}}\xi^2]\Psi=E\Psi$, rigorously derived from 0.2.1 Theorem 3.5.10
> - **§1.2**: Corrected ℐ-sector characteristic equation — from $(-\mathrm{d}^2/\mathrm{d}\xi^2+\lambda_2)\phi_n=\mu_n\phi_n$ (erroneous: constant potential) to $(-\mathrm{d}^2/\mathrm{d}\xi^2+\lambda_2^{\text{eff}}\xi^2)\phi_n=\mu_n\phi_n$ (harmonic oscillator potential), self-consistent with ground state $\phi_0\propto\exp(-\sqrt{\lambda_2^{\text{eff}}}\xi^2/2)$
> - **§1.3**: Corrected minimum resolvable angle — from $\pi/(2\sqrt{\lambda_2})\approx6.48\times10^{-3}$ rad (based on erroneous equation) to $2(\lambda_2^{\text{eff}})^{-1/4}=0.1281$ rad (based on harmonic oscillator ground state width); this definition labeled as "geometric analog construction" (Constructive Definition 1.3)
> - **§1.4 (new)**: Spectral triple toolkit connection note, labeling the spectral origins of $\chi_L$ (Wodzicki residue), $K$ (Dixmier trace), $\hbar$ (heat kernel asymmetry term) (0.3.1 §3), noting that the Hermite basis is the ℐ-frozen approximation of Toeplitz quantization
> - **§2.1**: Single core mapping declaration aligned to 0.1 §1.3; variational stability argument of Definition 2.2 changed from vague "0.2.1 soft mode theorem" to explicit three sources: (i) Nine-Element Mutual Arrest constraint (ii) cross-sector coupling structure (iii) weak coupling condition
> - **§2.2**: Identification $R_{\mathcal{M}}^{-2}=\lambda_1^{\text{eff}}/2$ in Proposition 2.1 honestly labeled as "working hypothesis" ($S^3$ scalar curvature is $6/r^2$, not $\lambda_1$); length value updated using $\lambda_1^{\text{eff}}=391.05$
> - **§3.1**: Rank-2 projection argument of Two-Level Theorem connected to Nine-Element Mutual Arrest first-order condition (0.3.1 Theorem 3.1a), replacing previously vague "0.0.7 constraint mapping" citation; ℓ=0 freezing subtraction supplemented with compatibility note regarding completeness axiom
> - **§4**: Theorem 4.1 downgraded to "Mapping-Layer Proposition 4.1"; correlation function derivation explicitly decomposed into Convention A (antipodal antiphase, guaranteed by Definition 2.2) and Convention B (Born rule correspondence, physical mapping convention); removed previous false claim of "intrinsic geometric equality of $S^3$ harmonic functions"
> - **§5–§6**: Unified parameter usage to $\lambda_2^{\text{eff}}$ in Theorems 5.1/6.1; premise of Theorem 6.1 explicitly labeled as "accepting the correlation mapping of Proposition 4.1"
> - **Former Chapter 7 → Appendix A**: Double-slit interference removed from main text, placed in Appendix A and labeled as "geometric model conjecture"; explicitly declared not satisfying 0.0.X + single core mapping closed-loop criterion (due to dependence on external input hypothesis of double-slit topological defect); phase connection citation to 0.2.1 corrected
> - **Comprehensive parameter upgrade**: bare values $(\lambda_1=392.21,\ \lambda_2=58760.77)$ → effective values $(\lambda_1^{\text{eff}}=391.05,\ \lambda_2^{\text{eff}}=59324.3)$; removed precision estimate skip claiming "bare vs. effective metric difference <0.3% negligible"
> - **Source citation corrections**: Removed all non-existent "0.2.1 Theorem 3.5.4 (soft mode theorem) → phase connection" citations; 0.0.7 constraint mapping citation changed to 0.0.6 projection mapping + Nine-Element Mutual Arrest first-order condition; 0.2.1 Theorem 3.5.10 citation method corrected
> - **Strict labeling of theorem/proposition statuses**: Theorem 1.1 → Proposition 1.1; Theorem 1.2 → Constructive Definition 1.3; Theorem 2.1 → Proposition 2.1 (with working hypothesis note); Theorem 4.1 → Mapping-Layer Proposition 4.1; Appendix A Theorems 7.2/7.3/7.4 → Propositions A.1/A.2/A.3 (conjectural layer)
> - **Appendix B constant table**: All values updated to effective metric version; newly added length $L(\mathcal{E}_{AB})$, etc.
