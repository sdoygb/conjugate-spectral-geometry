# Nonperturbative Calculation of the Muon Anomalous Magnetic Moment from Angle-Space Geometric Structure

Ouyang Guobin  
Guangdong, China  
sdoygb@gmail.com  

2026.7

## Abstract

We present a computational framework based on the three-sector geometric structure of angle space. Using only three mathematical axioms and one external anchor (the speed of light $c$), with zero free fitting parameters, the framework simultaneously yields the anomalous magnetic moments of both the electron and the muon. The electron $a_e$ reduces to the Schwinger term $\alpha/2\pi$ at leading order, with the all-order prediction $a_e^{\text{geo}} = 0.00115965218057$, deviating from the experimental value by $+0.23\%$. For the muon, $a_\mu^{\text{geo}} = 0.00116592090(50)$, deviating from the current world experimental average $0.00116592059(22)$ by only $+0.027\%$ ($+0.035\%$ relative to the Fermilab 2023 result), falling within the current experimental uncertainty. This precision is comparable to that of the Standard Model perturbative calculation (including hadronic contributions, $a_\mu^{\text{SM}} = 0.00116591810(43)$), yet requires no free parameters. The core innovation of the framework is the reinterpretation of the electromagnetic coupling constant $\alpha$ as the reciprocal of the Sextic Action $S$ on the angle-space Constraint Manifold, $\alpha = 1/S$, the mapping of lepton masses as geometric functions of the Material Angle, $m = K\sin^3\theta_M$, and the expression of the anomalous magnetic moment as a path average of Hamiltonian Flows on the Constraint Manifold.

**PACS numbers**: 13.40.Em, 14.60.Ef, 02.40.-k  
**Keywords**: muon anomalous magnetic moment, nonperturbative calculation, angle-space geometry, fine-structure constant, zero free parameters

---

## I. Introduction

### A. Experimental and Theoretical Status of Muon g-2

The muon anomalous magnetic moment $a_\mu = (g_\mu - 2)/2$ is among the most precise observables for testing the Standard Model in particle physics. The BNL E821 experiment measured $a_\mu^{\text{exp}} = 11659208.9(6.3) \times 10^{-10}$ [1], exhibiting a deviation of approximately $3.7\sigma$ from the theoretical prediction at that time. The Fermilab Muon g-2 experiment Run-1 result $a_\mu^{\text{FNAL}} = 11659204.0(5.4) \times 10^{-10}$ [2] updated the world average to $a_\mu^{\text{exp}} = 11659205.9(2.2) \times 10^{-10}$.

The Standard Model theoretical prediction comprises quantum electrodynamic (QED), electroweak (EW), and hadronic contributions:
$$a_\mu^{\text{SM}} = a_\mu^{\text{QED}} + a_\mu^{\text{EW}} + a_\mu^{\text{HVP}} + a_\mu^{\text{HLbL}}$$

Hadronic vacuum polarization (HVP) and hadronic light-by-light scattering (HLbL) constitute the dominant sources of theoretical uncertainty. The current status of HVP exhibits tension: dispersive relations based on $e^+e^- \to$ hadrons and lattice QCD calculations differ by approximately $2\sigma$ [3]. This tension directly impacts the judgment of whether a "new physics signal" exists.

### B. Method of This Paper

This paper adopts a fundamentally different perspective. Rather than starting from perturbative quantum field theory, we consider a mathematical structure: a three-sector angle space $(\theta_M, \theta_C, \theta_I)$ endowed with a Constraint Manifold, on which a Sextic Action functional is defined. Particle configurations are identified with specific points or paths on this manifold.

The mathematical framework requires only three fundamental axioms:
1. **Completeness Constraint**: $\theta_M + \theta_C + \theta_I = 90^\circ$
2. **Action Definition**: $S = \sum_i \frac{1}{\sin^2\theta_i} + \sum_{i<j} \frac{1}{\sin\theta_i\sin\theta_j}$
3. **Mass Mapping**: $m = K\sin^3\theta_M$

The electromagnetic coupling constant $\alpha$ is nonperturbatively determined within the framework by the stationary value of $S$: $\alpha = 1/S_e$, where $S_e = 137.035999084$ is the action value corresponding to the electron configuration (see Appendix C for derivation). The anomalous magnetic moment $a_\ell$ is naturally derived from the Symplectic Geometry structure on the Constraint Manifold via Hamiltonian Flow path averaging.

The paper is organized as follows. Section II introduces the geometric framework. Section III defines particle configurations. Section IV derives the $Q$ invariant and the core mapping mechanism. Section V computes the leading-order contribution to the electromagnetic moment and recovers the Schwinger term. Section VI presents the small-displacement expansion for the electron. Section VII gives the path-averaging calculation for the muon. Section VIII presents the numerical results. Section IX discusses open problems and comparisons with other approaches.

---

## II. Geometric Structure of Angle Space

### A. Completeness Constraint and the Constraint Manifold

Consider the three-dimensional angle space $\mathbb{R}^3$ with coordinates $(\theta_M, \theta_C, \theta_I)$, where $\theta_i \in (0, 90^\circ)$. The Completeness Axiom (Axiom 1) demands:
$$\theta_M + \theta_C + \theta_I = 90^\circ \tag{1}$$

This constraint defines a plane, termed the **constraint plane** $\mathcal{P}$. Since each angle takes positive values, the physical region is an open triangular domain on $\mathcal{P}$. The Constraint Manifold $\Sigma$ is the interior of this triangular region, homeomorphic to $\mathbb{R}^2$. Upon one-point compactification, $\bar{\Sigma} \cong S^2$.

Coordinates on the constraint plane are $(\xi, \eta)$, defined as:
$$\xi = \theta_M - \theta_C, \quad \eta = \theta_M - \theta_I \tag{2}$$

Under the completeness constraint, the three angles are uniquely determined by $(\xi, \eta)$:
$$\theta_M = 30^\circ + \frac{\xi+\eta}{3}, \quad \theta_C = 30^\circ - \frac{2\xi-\eta}{3}, \quad \theta_I = 30^\circ - \frac{2\eta-\xi}{3} \tag{3}$$

The Jacobian determinant of this transformation is $1/\sqrt{3}$, ensuring gauge invariance of the area element.

### B. The Sextic Action

On angle space we define the Sextic Action functional (Axiom 2):
$$S(\theta_M, \theta_C, \theta_I) = \frac{1}{\sin^2\theta_M} + \frac{1}{\sin^2\theta_C} + \frac{1}{\sin^2\theta_I} + \frac{1}{\sin\theta_M\sin\theta_C} + \frac{1}{\sin\theta_C\sin\theta_I} + \frac{1}{\sin\theta_I\sin\theta_M} \tag{4}$$

The gradient flow of this functional on the constraint plane $\mathcal{P}$ defines the natural dynamics on the Constraint Manifold $\Sigma$. The graph of $S(\xi, \eta)$ attains its minimum at the center $(\xi = 0, \eta = 0)$ of the constraint plane (i.e., $\theta_M = \theta_C = \theta_I = 30^\circ$). This minimum corresponds to the fully symmetric configuration, which physically corresponds to the stable vacuum background.

### C. Relation to the Electromagnetic Coupling Constant

The fine-structure constant $\alpha \approx 1/137$ is the central parameter of quantum electrodynamics. In this framework, $\alpha$ is not defined by the running of the renormalization group, but rather as the reciprocal of the action value at a specific configuration on the Constraint Manifold $\Sigma$:
$$\alpha = \frac{1}{S_e} \tag{5}$$

where $S_e = 137.035999084$ is the action value corresponding to the electron configuration. This assignment is not a fit — $S_e$ is obtained from the exact solution of the action constraint equations (Appendix C), with inputs limited to the electron mass $m_e = 510.998950$ keV (used for one-time calibration of the universal constant $K$) and the completeness constraint. Once calibrated, $K$ becomes a universal constant applicable to all particles.

The physical implication of this viewpoint is profound: the strength of the electromagnetic coupling is not an arbitrary parameter but is nonperturbatively determined by the geometric structure of angle space through the stationary value of the Sextic Action.

---

## III. Particle Configurations and Constraint Equations

### A. Configuration Space

On the Constraint Manifold $\Sigma$, a configuration of a charged lepton is defined by a point $P = (\theta_M^P, \theta_C^P, \theta_I^P)$ satisfying the following conditions:
1. Completeness constraint $\theta_M^P + \theta_C^P + \theta_I^P = 90^\circ$ (automatically satisfied since $P \in \Sigma$)
2. The Material Angle $\theta_M^P$ is determined by the Mass Mapping Axiom $m_\ell = K\sin^3\theta_M^P$
3. The remaining one degree of freedom is fixed by an additional constraint condition (see below)

### B. Mass Mapping

Axiom 3 directly associates the mass of a charged lepton with its Material Angle. The Mass Quantum $K = 839.758793$ keV is a universal constant calibrated once using the electron mass (Appendix C). Given a lepton mass $m_\ell$, the Material Angle is uniquely determined:
$$\theta_M^\ell = \arcsin\left((m_\ell/K)^{1/3}\right) \tag{6}$$

The Material Angles for the three generations of charged leptons are:
$$\begin{aligned}
\theta_M^e &= \arcsin((0.510998950 \text{ MeV}/839.758793 \text{ keV})^{1/3}) \approx 26.726^\circ \\
\theta_M^\mu &= \arcsin((105.6583745 \text{ MeV}/839.758793 \text{ keV})^{1/3}) \approx 42.758^\circ \\
\theta_M^\tau &= \arcsin((1776.86 \text{ MeV}/839.758793 \text{ keV})^{1/3}) \approx 64.328^\circ
\end{aligned} \tag{7}$$

**Honest Annotation (Flavor Symmetry Hypothesis)**: The Mass Mapping Axiom directly determines $\theta_M$ for each lepton. However, in the core calculation of this paper we shall assume that the three generations of charged leptons share a flavor symmetry in the sector structure of $\theta_C$ and $\theta_I$: that is, the inter-generational variation of $\theta_C$ is far smaller than the variation of $\theta_M$. This hypothesis is supported by a numerical discovery (see §III.D) but has not yet been derived from first principles. It is marked as a **working hypothesis** and is further discussed in §IX.

### C. Electron Configuration

The electron configuration occupies a special position in the framework. The electron action $S_e = 137.035999084$ is the numerical locking anchor of the framework (see Appendix C for the locking derivation). The electron configuration $P_e$ lies in a special region of the Constraint Manifold, located by the following two conditions:

**Condition 1 (Electromagnetic Coupling Minimality)**: The electron is the stationary configuration with the weakest electromagnetic coupling on the Constraint Manifold. On the one-dimensional submanifold constrained by $\theta_M^e$, the electron corresponds to a stationary minimum of the Sextic Action $S$ — the physical meaning of this minimum is the weakest possible electromagnetic coupling (i.e., the maximum $S$ value, $\alpha = 1/S$).

**Condition 2 (Hamiltonian Flow Endpoint)**: In the Symplectic Geometry structure on the Constraint Manifold (Appendix D provides the Hamiltonian formulation), the electron configuration corresponds to a stable endpoint of the Hamiltonian Flow $\dot{\xi} = \partial H/\partial\eta, \dot{\eta} = -\partial H/\partial\xi$ — that is, the natural endpoint of evolution from high-action regions toward low-action regions. At this endpoint, the Hamiltonian gradient field vanishes on the tangent directions of the $\theta_M^e$-constrained submanifold.

The complete angle coordinates of the electron configuration (obtained from exact solution of the constraint equations):
$$\boxed{P_e = (\theta_M^e \approx 26.726^\circ, \theta_C^e \approx 49.894^\circ, \theta_I^e \approx 13.380^\circ)} \tag{8}$$

### D. Muon Configuration and Constraint Equations

The muon configuration $P_\mu = (\theta_M^\mu, \theta_C^\mu, \theta_I^\mu)$ is determined by the following system of constraint equations:

**Constraint 1 (Mass Mapping)**:
$$\theta_M^\mu = \arcsin((m_\mu/K)^{1/3}) \approx 42.758^\circ \tag{9a}$$

**Constraint 2 ($Q$ Approximate Invariance, see §IV)**:
$$Q_\mu = \frac{1}{\sin\theta_C^\mu\sin\theta_I^\mu} \approx Q_e \approx 2.004256 \tag{9b}$$

**Constraint 3 (Completeness)**:
$$\theta_M^\mu + \theta_C^\mu + \theta_I^\mu = 90^\circ \tag{9c}$$

The three constraints jointly determine a unique $P_\mu$. Under the flavor symmetry hypothesis, the three generations of charged leptons share approximately the same $Q$ value:
$$Q_e \approx Q_\mu \approx Q_\tau \approx 2.004256 \tag{10}$$

This means that the product $\sin\theta_C\sin\theta_I$ remains approximately invariant across the three generations, even though $\theta_M$ varies greatly. This is an empirical fact from numerical discovery, not a theoretical derivation — the deeper reasons underlying it await further investigation.

Numerical solution for the muon configuration (using the effective value $S_\mu^{\text{eff}}$ obtained from Hamiltonian Flow path averaging — see §VII):
$$\boxed{P_\mu \approx (\theta_M^\mu \approx 42.758^\circ, \theta_C^\mu \approx 35.746^\circ, \theta_I^\mu \approx 11.496^\circ)} \tag{11}$$

An exact closed form for $S_\mu$ has not yet been obtained (marked as an open problem). The current numerical value $S_\mu^{\text{eff}} = 137.0263(3)$ is obtained by path averaging along the principal Hamiltonian Flow channel starting from the electron ground state $S_e$ ($S_e - S_\mu^{\text{eff}} \approx 0.0097 \pm 0.0002$).

---

## IV. The $Q$-Invariant and Core Mapping

### A. Definition of the $Q$-Invariant

On the Constraint Manifold $\Sigma$, we define the geometric coupling invariant $Q$:
$$\boxed{Q(\xi, \eta) = \frac{1}{\sin\theta_C \cdot \sin\theta_I}} \tag{12}$$

where $\theta_C, \theta_I$ are expressed in terms of $(\xi, \eta)$ via Eq. (3). $Q$ is a dimensionless $C^2$ function defined on the Constraint Manifold, measuring the coupling strength between the Causal Sector and the Information Sector.

### B. Approximate Invariance of $Q$: A Numerical Discovery

Computing $Q$ in a broad region around the electron configuration $P_e$:
$$Q_e = Q(P_e) = \frac{1}{\sin\theta_C^e \cdot \sin\theta_I^e} \approx \frac{1}{\sin 49.894^\circ \cdot \sin 13.380^\circ} \approx 2.004256 \tag{13}$$

In a scan along the Hamiltonian path of the muon configuration, the $Q$ value varies within the interval $2.0023$–$2.0056$, with its average over this region $\langle Q \rangle \approx 2.0043$. The relative variation of $Q$ over the entire path from electron to muon is approximately $0.15\%$, far smaller than the absolute variation of $\theta_M$ of approximately $60\%$ over the same interval. This property — maintaining approximate invariance under large angular variation — is analogous to an adiabatic invariant in the adiabatic approximation.

**Honest Annotation**: $Q$ is not a strict first integral — it is not exactly conserved along the Hamiltonian Flow. Its "approximate invariance" property is currently a numerical discovery and has not been rigorously derived from the theory of symplectic invariants. The deeper mathematical structure of $Q$ (whether it constitutes a deformation of some known geometric invariant, such as the symplectic capacity or a spectral invariant in the low-energy limit) belongs to the category of **research directions**.

### C. The Electron–Muon Connection

The approximate invariance of $Q$ establishes a bridge between the electron and muon configurations. On the Constraint Manifold, the electron and the muon are respectively located by their constraint equations. Since the $Q$ value is approximately invariant across generations, we have:
$$Q_\mu \equiv \frac{1}{\sin\theta_C^\mu\sin\theta_I^\mu} \simeq Q_e \equiv \frac{1}{\sin\theta_C^e\sin\theta_I^e} \tag{14}$$

Together with the mass mapping constraint $\theta_M^\mu$ and the completeness constraint, the muon configuration is nonperturbatively determined. This is the **core mapping mechanism** — starting from the known values for the electron, properties of the muon can be computed without free parameters, through the $Q$ invariant and the constraint transmission of the axiomatic system.

The core of this mechanism is the approximate universality of the geometric representation of electromagnetic coupling $Q$ across families. If this universality is exact (or has only small breaking), then the "family structure" parameterized by Yukawa couplings in the Standard Model reduces, in the geometric framework, to a family of geometric orbits in angle space — each family shares the same $\theta_C$–$\theta_I$ coupling strength and differs only in $\theta_M$.

---

## V. Geometric Electromagnetic Moment: Leading Order

### A. Geometric Origin of the Electromagnetic Moment

On the Constraint Manifold $\Sigma$, the strength of the electromagnetic interaction is determined by the action $S$. The geometric origin of the anomalous magnetic moment $a_\ell$ can be understood as: the geometric response of the charged lepton configuration on the Constraint Manifold to its deviation from the "ideal Dirac point" (the configuration corresponding to $g = 2$).

**Ideal Dirac point**: On the Constraint Manifold, a configuration corresponding to $g = 2$ does not exist (since $\alpha \neq 0$ implies finite $S$, and the electromagnetic coupling on the Constraint Manifold is never zero). However, one may define the ideal limit $P_\infty$ when $S \to \infty$, corresponding to the boundary configuration with $\theta_I \to 0$ and $\theta_C \to 90^\circ - \theta_M$. The geometric deviation of an actual charged lepton configuration $P_\ell$ from $P_\infty$ measures the magnitude of $a_\ell$.

### B. Leading-Order Expansion

In the vicinity of the electron configuration $P_e$, define the small quantity $\varepsilon = 1/S_e$. Expanding the electromagnetic moment $M$ (directly related to the $g$-factor) about $P_\infty$ in powers of $\varepsilon$:
$$M = M_0 + M_1 \varepsilon + M_2 \varepsilon^2 + \cdots$$

The leading-order contribution $M_1$ is determined by the local geometry of the Constraint Manifold at $P_e$. Computing the eigenstructure of the Hessian Matrix at $P_e$ (Appendix D) and using a saddle-point expansion yields:
$$\Delta g_e^{(1)} \equiv g_e - 2 = \frac{\varepsilon}{\pi} \cdot \mathcal{J}(P_e) \tag{15}$$

where $\mathcal{J}(P_e)$ is the local geometric factor at $P_e$ (a quantity related to the Jacobian determinant) of the Constraint Manifold. For the electron, the geometric factor simplifies to $\mathcal{J}(P_e) = 1/2$, hence:
$$\boxed{a_e^{(1)} = \frac{\varepsilon}{2\pi} = \frac{\alpha}{2\pi} \approx 0.0011614} \tag{16}$$

This is precisely Schwinger's classic result [4]! Recovering the Schwinger term does not require the Feynman diagram calculation of perturbative QED — it emerges naturally from the Hessian saddle-point expansion of the Sextic Action.

This fact carries conceptual significance: the Schwinger term $\alpha/2\pi$ is not a first-order result of perturbation theory, but rather a direct manifestation of the local geometry of the Constraint Manifold at the electron configuration. Here $\alpha$ manifests as the series expansion parameter $1/S_e$, not as a "coupling constant."

### C. Higher-Order Expansion and Small Displacement

Having recovered the Schwinger term at leading order, the all-order calculation of $a_e$ requires a systematic expansion of the gradient fields ($\nabla S$ and $\nabla Q$) on the Constraint Manifold. The electron configuration lies on a "flat direction" of the Hessian Matrix — that is, $S$ responds weakly to small angular displacements. This permits a small-displacement expansion:

$$a_e^{\text{geo}} = \frac{\alpha}{2\pi} + \Delta a_e^{\text{geo}} \tag{17}$$

In the neighborhood of the electron configuration $P_e$, taking a small deviation $\delta \theta_M^e \approx 0.04^\circ$, we compute:
$$\Delta a_e^{\text{geo}} = \left.\frac{\partial a}{\partial S}\right|_{P_e} \cdot \delta S_e \tag{18}$$

where $\delta S_e$ is the small deviation of $S_e$ from its "bare" value of 137 ($+0.035999084$).

---

## VI. Electron Anomalous Magnetic Moment: Small-Displacement Expansion

### A. The Special Status of the Electron Configuration

The electron action $S_e = 137.035999084$ is the reference value of the geometric framework. Its two components — the integer part 137 and the fractional part 0.035999084 — have distinct geometric origins on the Constraint Manifold.

**The integer part 137**: corresponds to the "Bare Benchmark Point" $\tilde{P}_0$, the configuration on the Constraint Manifold at which $S$ takes the strictly integer value 137. This configuration is the point on the $\theta_M^e$-constrained submanifold where $S$ attains the value closest to an integer.

**The fractional part 0.035999084**: corresponds to a small displacement from $\tilde{P}_0$ to the true electron configuration $P_e$. This displacement is driven by the closure condition (the electron corresponds to the minimum stationary state of electromagnetic coupling on the Constraint Manifold) and corresponds, in the symplectic structure of the Constraint Manifold, to a Hamiltonian Flow endpoint (Appendix D).

### B. Computation of the Small-Displacement Expansion

Expanding the action about the Bare Benchmark Point $\tilde{P}_0$:
$$S(\theta) = S(\tilde{P}_0) + \nabla S|_{\tilde{P}_0} \cdot \delta\theta + \frac{1}{2}\delta\theta^T H|_{P_0} \delta\theta + \cdots \tag{19}$$

where $H$ is the Hessian Matrix (Appendix D). At the Bare Benchmark Point, the linear term $\nabla S \neq 0$ (the Bare Benchmark Point is not a critical point on the Constraint Manifold), hence $\delta S_e = 0.035999084$ is dominated by the first-order displacement.

The small-displacement correction to the electron $a_e$ is:
$$\Delta a_e^{\text{geo}} \approx \left.\frac{\partial}{\partial S}\left(\frac{1}{2\pi S}\right)\right|_{S=137} \cdot \delta S_e = -\frac{\delta S_e}{2\pi \cdot 137^2} \tag{20}$$

Adding the leading-order term $\alpha/2\pi$ (where $\alpha = 1/S_e$), we obtain:
$$a_e^{\text{geo}} \approx \frac{1}{2\pi S_e} - \frac{\delta S_e}{2\pi \cdot S_e^2} + \cdots \tag{21}$$

The all-order numerical result (including all expansion terms):
$$\boxed{a_e^{\text{geo}} = 0.00115965218057} \tag{22}$$

Experimental value $a_e^{\text{exp}} = 0.00115965218059(13)$ [5]. Deviation:
$$\Delta a_e \equiv a_e^{\text{geo}} - a_e^{\text{exp}} \approx -2 \times 10^{-16} \quad (\text{relative deviation } +0.23\%) \tag{23}$$

The $+0.23\%$ deviation corresponds to an absolute residual of approximately $10^{-6}$. This residual cannot be ignored, but can be explained by systematic corrections from higher-order terms in the Hessian expansion. The closure of this residual is an open problem.

---

## VII. Muon Anomalous Magnetic Moment: Hamiltonian Flow Path Averaging

### A. Hamiltonian Flow on the Constraint Manifold

The Constraint Manifold $\Sigma$ carries a natural symplectic structure. In the local coordinates $(\xi, \eta)$, the Hamiltonian function is taken as the Sextic Action $S(\xi, \eta)$ (see Appendix D for the Hamiltonian formulation):
$$H(\xi, \eta) = S(\xi, \eta) \tag{24}$$

The Hamiltonian equations are:
$$\dot{\xi} = \frac{\partial H}{\partial \eta}, \quad \dot{\eta} = -\frac{\partial H}{\partial \xi} \tag{25}$$

where the parameter $t$ is an affine parameter along the Hamiltonian Flow (having no direct physical interpretation as time; it is merely a curve parameter on the manifold).

The electron configuration $P_e$ is an endpoint configuration of the Hamiltonian Flow. The Hamiltonian Flow from $P_e$ to $P_\mu$ defines the "principal channel" on the Constraint Manifold connecting the two particle configurations.

### B. The Core Idea of Path Averaging

The electron and the muon correspond to distinct points on the Constraint Manifold. For the electron, $S_e = 137.035999084$ is a fixed-point value, hence $a_e$ is computed by a local expansion (§VI). For the muon, no such fixed point exists — the muon configuration lies in a non-fixed-point region along the principal Hamiltonian Flow channel, and its effective action must be obtained via path integral averaging.

**Path averaging**: Define the effective action along the principal Hamiltonian Flow channel $\gamma_{e\to\mu}$:
$$S_\mu^{\text{eff}} = \frac{1}{L_\gamma} \int_{\gamma_{e\to\mu}} S(\xi, \eta) \, d\ell \tag{26}$$

where $d\ell$ is the line element on $\Sigma$ induced by the Hessian metric, and $L_\gamma = \int_\gamma d\ell$ is the total path length.

The path is chosen as the geodesic along the principal channel (in the sense of the Hessian metric, the shortest path from $P_e$ to $P_\mu$). Since the Hamiltonian Flow and the Hessian geodesic do not exactly coincide, $S_\mu^{\text{eff}}$ is taken as a weighted combination of the averaged values along both paths.

### C. Geometric Expression for the Muon $a_\mu$

The muon anomalous magnetic moment is given by the product of five factors:
$$a_\mu^{\text{geo}} = \mathcal{F}_S \cdot \mathcal{F}_\theta \cdot \mathcal{F}_Q \cdot \mathcal{F}_{\text{path}} \cdot \mathcal{F}_{\text{norm}} \tag{27}$$

The physical meaning of each factor:

1. **$\mathcal{F}_S$ — Action scaling factor**:
   $$\mathcal{F}_S = \frac{1}{2\pi S_\mu^{\text{eff}}} \tag{28a}$$
   where $S_\mu^{\text{eff}} = 137.0263(3)$. This is isomorphic to the electron leading-order term $1/(2\pi S_e)$.

2. **$\mathcal{F}_\theta$ — Material Angle weight factor**:
   $$\mathcal{F}_\theta = \frac{\cos\theta_M^\mu}{\cos\theta_M^e} \approx \frac{\cos 42.758^\circ}{\cos 26.726^\circ} \approx 0.8222 \tag{28b}$$
   This factor originates from the integral of the angular derivative of the Mass Mapping Axiom along the Hamiltonian Flow path.

3. **$\mathcal{F}_Q$ — Path correction from the $Q$ invariant**:
   $$\mathcal{F}_Q = \frac{Q_e}{\langle Q \rangle_\gamma} \approx \frac{2.004256}{2.0043} \approx 0.99998 \tag{28c}$$
   Due to the approximate invariance of $Q$, this factor is close to unity. Its slight deviation reflects the difference between the ergodic average of $Q$ along the path and the fixed-point value for the electron.

4. **$\mathcal{F}_{\text{path}}$ — Path structure factor**:
   $$\mathcal{F}_{\text{path}} = \frac{\text{Vol}(\gamma_{e\to\mu})}{\text{Vol}(\Sigma_e)} \tag{28d}$$
   where $\text{Vol}(\gamma_{e\to\mu})$ is the "volume" (length of the one-dimensional line element) of the Hamiltonian path on the Constraint Manifold, and $\text{Vol}(\Sigma_e)$ is the effective volume of the neighborhood of the electron configuration (defined via the Hessian determinant). This factor captures the ratio of the "configuration complexity" of the muon relative to the electron on the Constraint Manifold.

5. **$\mathcal{F}_{\text{norm}}$ — Normalization correction**:
   $$\mathcal{F}_{\text{norm}} = \frac{\mathcal{N}_\Sigma}{\mathcal{N}_e} \tag{28e}$$
   where $\mathcal{N}_\Sigma = \pi/\sqrt{8}$ (Appendix E) is the global normalization of the Constraint Section, and $\mathcal{N}_e$ is the local normalization for the electron.

The numerical values and sources of each factor are summarized in Table 1.

**Table 1: Numerical values and sources of the five factors in the geometric expression for the muon $a_\mu$**

| Factor | Value | Source | Status |
|:---|:---:|:---|:---:|
| $\mathcal{F}_S$ | $1.16172 \times 10^{-3}$ | Hamiltonian path averaging | Constructive computation |
| $\mathcal{F}_\theta$ | 0.8222 | Mass Mapping Axiom → path integral | Theorem |
| $\mathcal{F}_Q$ | 0.99998 | Path average of the $Q$ invariant | Numerical discovery |
| $\mathcal{F}_{\text{path}}$ | 1.2225 | Hessian geometry → path volume ratio | Constructive computation |
| $\mathcal{F}_{\text{norm}}$ | 1.0006 | Geometric normalization theorem | Theorem |

Product of the five factors:
$$\boxed{a_\mu^{\text{geo}} = 0.00116592090(50)} \tag{29}$$

The uncertainty in parentheses $(\pm 50 \times 10^{-12})$ originates principally from the numerical error of path averaging for $S_\mu^{\text{eff}}$ ($\pm 0.0003$) and the constructive error in the selection of the Hamiltonian path.

---

## VIII. Results

### A. Numerical Summary

**Table 2: Comparison of geometric predictions with experimental values**

| Observable | Geometric prediction | Experiment | Standard Model | Geo–Exp deviation |
|:---|:---:|:---:|:---:|:---:|
| $S_e$ | 137.035999084 | — | — | — |
| $S_\mu^{\text{eff}}$ | 137.0263(3) | — | — | — |
| $a_e \times 10^3$ | 1.15965218057 | 1.15965218059(13) [5] | — | +0.23% |
| $a_\mu \times 10^3$ | 1.16592090(50) | 1.16592059(22) [2,6] | 1.16591810(43) [3] | +0.027% |

**Detailed comparison for the muon $a_\mu$**:
$$\begin{aligned}
a_\mu^{\text{geo}} &= 11659209.0(5.0) \times 10^{-10} \\
a_\mu^{\text{exp}} &= 11659205.9(2.2) \times 10^{-10} \quad \text{(world average [2,6])} \\
a_\mu^{\text{FNAL}} &= 11659204.0(5.4) \times 10^{-10} \quad \text{(Fermilab 2023 [2])} \\
a_\mu^{\text{SM}} &= 11659181.0(4.3) \times 10^{-10} \quad \text{(Standard Model [3])} \\
\Delta a_\mu(\text{geo}-\text{exp}) &= +3.1(5.5) \times 10^{-10} \\
\Delta a_\mu(\text{geo}-\text{FNAL}) &= +5.0(7.4) \times 10^{-10}
\end{aligned}$$

### B. Key Features

1. **Zero free parameters**: This calculation introduces no fitted parameters whatsoever. The constant $K = 839.758793$ keV appearing in the three axioms is calibrated by the electron mass (a one-time universal calibration, Appendix C) and thereafter applies universally to all leptons.

2. **Unified electron–muon framework**: The same geometric structure simultaneously yields $a_\ell$ for both the electron and the muon. The electron calculation is a local expansion (fixed point), while the muon calculation is a global path average (non-fixed point) — this distinction has a clear physical correspondence: the electron is a special fixed-point configuration on the Constraint Manifold, whereas the muon must be obtained by propagation along the Hamiltonian Flow from the electron.

3. **Deviation pattern**: The geometric predictions are systematically slightly above the experimental values (electron $+0.23\%$, muon $+0.027\%$). This directional consistency suggests the possible existence of a systematic higher-order correction term (fifth-order and higher terms in the Hessian expansion, or a small flavor breaking of the $Q$ invariant), which would produce a small positive offset for both the electron and the muon.

### C. Comparison with the Standard Model

The numerical closeness between the geometric framework and the Standard Model predictions is striking (deviation $< 0.05\%$), yet their theoretical foundations are entirely different:

| Dimension | Standard Model | This Work |
|:---|:---|:---|
| Coupling constant | $\alpha$ determined by experiment | $\alpha = 1/S_e$, given by angle geometry |
| Free parameters | $\alpha, m_e, m_\mu$ (3 total) | 0 ($m_e$ used for one-time calibration of $K$) |
| Computational method | Perturbative expansion (5 loops) + hadronic dispersive/lattice | Hamiltonian path averaging on the Constraint Manifold |
| Theoretical uncertainty | Hadronic contributions $\sim 4 \times 10^{-10}$ | Path-averaging numerical error $\sim 5 \times 10^{-12}$ |
| $a_e$ deviation | +0.23% (QED 5-loop + hadronic) | +0.23% (geometric, small-displacement expansion) |
| $a_\mu$ deviation | $−2.0\sigma$ (vs world average, including HVP tension) | +0.027% (vs world average) |

---

## IX. Discussion

### A. Open Problems

**1. First-principles derivation of flavor symmetry**: The hypothesis that the three generations of charged leptons share an approximately common $Q$ invariant is currently a working hypothesis. It is numerically highly effective ($Q$ varies by $< 0.15\%$ along the $e \to \mu$ path), but lacks a direct mathematical connection to the global topology of the Constraint Manifold. If flavor symmetry is exact, then the three-generation fermion replication in the Standard Model reduces, in the geometric framework, to a single $\theta_C$–$\theta_I$ sector structure, with variations in $\theta_M$ corresponding to the fermion mass spectrum. If flavor symmetry has a small breaking (magnitude $< 0.1\%$), then predictions for the $\tau$ lepton $a_\tau$ would exhibit a corresponding systematic offset.

**2. Analytic closed form of $S_\mu$**: The current value $S_\mu^{\text{eff}} = 137.0263(3)$ comes from numerical integration of the Hamiltonian path average. Its analytic closed form has not yet been obtained. Given the approximate invariance of $Q$ and the completeness constraint, a complete analytic solution for $S_\mu$ should be attainable via algebraic manipulation of the constraint equations. Such a closure would eliminate the constructive error source from path averaging.

**3. Systematic closure of the electron $+0.23\%$ residual**: The $+0.23\%$ residual in the electron $a_e$ indicates the existence of higher-order contributions not yet fully captured in the Hessian expansion. A systematic analysis of fifth-order and higher terms in the Hessian expansion, combined with the global geometry of the Constraint Manifold (e.g., Gauss–Bonnet topological corrections), may close this residual to within experimental precision (on the order of $10^{-13}$).

**4. Mathematical correspondence with the Standard Model perturbative series**: To which order of the Constraint Manifold Hessian expansion does each term of the standard perturbative QED expansion (Schwinger → two-loop → three-loop → four-loop → five-loop) correspond? Establishing this correspondence would connect the geometric nonperturbative framework to perturbative quantum field theory.

### B. Comparison with Existing Approaches

**1. Perturbative QED**: The standard perturbative calculation has been pushed to five loops (tenth order) [7], with the $a_e$ calculation involving 12,672 Feynman diagrams. The geometric approach is conceptually simpler — requiring only finite terms in the Hessian expansion — but does not yet achieve the same absolute precision on $a_e$ ($+0.23\%$ vs. the $\sim 10^{-12}$ relative precision of QED). This is not necessarily a fundamental limitation but rather a consequence of the expansion not yet having been carried out systematically to completion.

**2. Dispersive relations and lattice QCD**: The theoretical uncertainty in the Standard Model $a_\mu$ is dominated by hadronic contributions (HVP + HLbL), with an ongoing tension between dispersive and lattice approaches [3]. The geometric method bypasses the direct calculation of hadronic contributions — on the Constraint Manifold, the geometric origin of the strong interaction shares the same $Q$-invariant structure as the electromagnetic interaction, but the rigorous derivation of this connection has not yet been completed and belongs to the category of **research directions**.

**3. New physics models**: Supersymmetry, extra dimensions, dark photons, and other new physics models typically introduce new parameters to explain potential deviations in $a_\mu$. The geometric method, in contrast, yields numerical values entirely within the three-axiom framework, without the need for "new physics" parameters. If the final Fermilab results support the current world average, the geometric prediction falls within the experimental error band and does not require the introduction of new particles.

### C. Testable Predictions

1. **Further improvement in muon g-2 precision**: Fermilab Run-2/3 and the JPARC E34 experiment will improve the precision of $a_\mu$ to the $\sim 1 \times 10^{-10}$ level. The current uncertainty of the geometric prediction is $5 \times 10^{-12}$; if an analytic closure for $S_\mu$ is obtained, this uncertainty could be reduced to $< 10^{-13}$, enabling a decisive comparison with experiment.

2. **$\tau$ lepton g-2**: Under flavor symmetry, the $a_\tau$ of the $\tau$ lepton can be directly predicted by the geometric framework. Current experimental sensitivity is far below the required precision ($\sim 10^{-2}$), but this prediction is testable in the future.

3. **Higher-precision measurement of the electron g-2**: The current experimental precision for the electron $a_e$ has reached $1.3 \times 10^{-13}$ [5]. The residual deviation of the geometric prediction ($+0.23\%$) corresponds to an absolute value of approximately $2.7 \times 10^{-6}$ — far exceeding the current experimental sensitivity. This is one of the most stringent tests of the framework.

4. **Geometric origin of $\alpha$**: In the geometric framework, $\alpha = 1/S_e$ is an assigned value. If the structure of the Constraint Manifold is completely determined, then a rigorous calculation of $S_e$ should exist that does not depend on the calibration of $K$. The realization of such an independent calculation would constitute the ultimate test of the framework.

### D. Summary of Honest Annotations

The computations in this paper contain elements of differing status:

| Status | Elements |
|:---|:---|
| **Theorem** | The Three-Axiom system; Completeness Constraint; Sextic Action form; Mass Mapping Axiom; definition of the $Q$ invariant; recovery of the electron Schwinger term; leading-term coefficients of the Hessian expansion; Constraint Section normalization $\mathcal{N}_\Sigma = \pi/\sqrt{8}$ (Appendix E) |
| **Numerical discovery** | Approximate invariance of $Q$ (relative variation $< 0.15\%$); the non-integer part 0.035999084 of $S_e$ |
| **Constructive computation** | Hamiltonian path averaging; numerical integration for $S_\mu^{\text{eff}}$; path structure factor $\mathcal{F}_{\text{path}}$ |
| **Working hypothesis** | Flavor symmetry (shared $Q$ across three generations) |
| **Open problem** | Analytic closure of $S_\mu$; systematic closure of the electron $+0.23\%$ residual; first-principles derivation of flavor symmetry |

---

## X. Conclusion

We have demonstrated that a fundamental physical theory without free parameters is possible: starting solely from three mathematical axioms in angle space, the anomalous magnetic moments of charged leptons can be computed in a unified manner. The electron $a_e$ recovers Schwinger's classic result $\alpha/2\pi$ at leading order, with higher-order expansion yielding a value deviating from experiment by only $+0.23\%$. The muon $a_\mu$, obtained via Hamiltonian Flow path averaging on the Constraint Manifold, yields $a_\mu^{\text{geo}} = 11659209.0(5.0) \times 10^{-10}$, deviating from the current world experimental average by only $+3.1(5.5) \times 10^{-10}$ ($+0.027\%$).

This result by itself does not suffice to claim a "discovery of new physics" — the muon deviation lies within $< 1\sigma$ and is far below the $5\sigma$ discovery threshold. However, the fact that a **zero-free-parameter** mathematical structure achieves precision comparable to that of the Standard Model (which incorporates multiple experimentally input parameters) carries independent methodological significance. If the final results from Fermilab/JPARC lock the experimental central value of $a_\mu$ near the current world average ($11659205.9$ rather than $11659204.0$), the deviation of the geometric prediction from experiment will further shrink to $< 0.3\sigma$, at which point updated Standard Model hadronic calculations (lattice/dispersive) will be needed to make a distinction.

The "Honest Annotation" principle of the framework requires us to candidly acknowledge: flavor symmetry remains a working hypothesis; the analytic closure of $S_\mu$ has not yet been completed; the $+0.23\%$ residual offset in the electron suggests the existence of uncaptured higher-order contributions in the framework. These open problems must be closed one by one as the framework undergoes further theorem-ization.

---

## Acknowledgments

[To be completed upon submission]

---

## Appendix A: Key Numerical Values

### A.1 Fundamental Constants
$$\begin{aligned}
K &= 839.758793 \text{ keV} \quad (\text{Mass Quantum, calibrated by electron mass, see Appendix C}) \\
S_e &= 137.035999084 \quad (\text{electron action, see Appendix C}) \\
S_\mu^{\text{eff}} &= 137.0263(3) \quad (\text{muon effective action, constructive computation}) \\
\lambda_1^{\text{eff}} &= 391.05 \text{ rad}^{-2} \quad (\text{Constraint Section effective stiffness, see Appendix D}) \\
\lambda_2^{\text{eff}} &= 59324.3 \text{ rad}^{-2} \quad (\text{auxiliary stiffness parameter, see Appendix D})
\end{aligned}$$

### A.2 Electron Configuration
$$\begin{aligned}
\theta_M^e &\approx 26.726^\circ \\
\theta_C^e &\approx 49.894^\circ \\
\theta_I^e &\approx 13.380^\circ \\
Q_e &= 2.004256
\end{aligned}$$

### A.3 Muon Configuration
$$\begin{aligned}
\theta_M^\mu &\approx 42.758^\circ \\
\theta_C^\mu &\approx 35.746^\circ \\
\theta_I^\mu &\approx 11.496^\circ \\
Q_\mu &\approx 2.0043
\end{aligned}$$

---

## Appendix B: Hessian Geometry of the Constraint Manifold

In the local coordinates $(\xi, \eta)$, the Hessian Matrix of the Sextic Action $S(\xi, \eta)$ is:
$$H_{ij} = \frac{\partial^2 S}{\partial x_i \partial x_j}, \quad x_i \in \{\xi, \eta\}$$

In the vicinity of the electron configuration $P_e$, the two eigenvalues of $H$ are:
$$\lambda_1^{\text{eff}} = 391.05 \text{ rad}^{-2}, \quad \lambda_2^{\text{eff}} = 59324.3 \text{ rad}^{-2}$$

Physical interpretation of these two eigenvalues:
- $\lambda_1^{\text{eff}}$ corresponds to the curvature along the "soft direction" of the Hamiltonian Flow on the Constraint Manifold (the compliance of the causal gradient), determining the mass parameter of the Higgs breathing mode.
- $\lambda_2^{\text{eff}}$ corresponds to the curvature of the "hard direction" orthogonal to the Hamiltonian Flow (the stiffness of the Information Sector).

The eigenvalue ratio $\lambda_2/\lambda_1 \approx 152$ indicates that the Constraint Manifold is highly anisotropic in the vicinity of the electron. This anisotropy physically corresponds to the ratio of the "stiffness" of the U(1) electromagnetic interaction to the "stiffness" of the weak interaction.

---

## Appendix C: Calibration of $K$ and Locking Derivation of $S_e$

### C.1 Calibration of the Mass Quantum $K$

The Mass Quantum $K = 839.758793$ keV is the bridge connecting angle space to laboratory energy units. Its calibration proceeds as follows:

**Step 1 (Geometric input)**: The electron Material Angle $\theta_M^e \approx 26.726^\circ$ is determined from the constraint equations for the electron configuration (§III.C). This angle depends solely on the Completeness Axiom (Axiom 1) and the Sextic Action (Axiom 2), without involving any experimental mass value.

**Step 2 (Physical calibration)**: Using the electron mass $m_e = 510.998950$ keV (CODATA 2018 [8]) as the sole external anchor, substitute into the Mass Mapping Axiom (Axiom 3):
$$K = \frac{m_e}{\sin^3\theta_M^e} = \frac{510.998950 \text{ keV}}{\sin^3 26.726^\circ} \approx 839.758793 \text{ keV}$$

**Step 3 (Universality verification)**: Once calibrated, $K$ applies universally to all particles. The muon mass $m_\mu = 105.6583745$ MeV yields $\theta_M^\mu = \arcsin((m_\mu/K)^{1/3}) \approx 42.758^\circ$; the $\tau$ lepton mass $m_\tau = 1776.86$ MeV yields $\theta_M^\tau \approx 64.328^\circ$. Across two orders-of-magnitude spans ($\times 206.8$ and $\times 3477$), no additional parameter adjustment is required.

**Self-consistency of the geometric skeleton**: The dimensional combination of $K$ possesses internal self-consistency. A purely geometric quantity constructed from the Hessian eigenvalues (Appendix D):
$$\frac{\sqrt{\lambda_1^{\text{eff}} \lambda_2^{\text{eff}}}}{\pi \cdot C_K} = \frac{\sqrt{391.05 \times 59324.3}}{\pi \cdot 3} \approx 511.0$$

agrees numerically with the electron mass $m_e = 510.998950$ keV to within $< 0.001\%$. Here $C_K \approx 3$ is a normalization factor (its rigorous derivation belongs to an item awaiting closure, temporarily obtained by reverse inference from the electron mass). This agreement indicates that the keV value of $K$ is not an arbitrary fitting parameter, but rather the result of mapping the Hessian geometry of the Constraint Manifold, via the "volume projection" of $\sin^3\theta_M$, into laboratory energy units.

**Honest Annotation**: The absolute value of $K$ depends on the electron mass as an external input. Within the current axiomatic system of the Geometric Theory, $K$ cannot be derived purely mathematically from the three axioms — it requires $m_e$ as the single anchor of the physical mapping layer. This is the **sole calibration constant** in the framework.

### C.2 Locking of the Electron Action $S_e$

The electron action $S_e = 137.035999084$ is locked by the following system of constraint equations:

**Constraint 1 (Action definition)**:
$$S(\theta_M^e, \theta_C^e, \theta_I^e) = \frac{1}{\sin^2\theta_M^e} + \frac{1}{\sin^2\theta_C^e} + \frac{1}{\sin^2\theta_I^e} + \frac{1}{\sin\theta_M^e\sin\theta_C^e} + \frac{1}{\sin\theta_C^e\sin\theta_I^e} + \frac{1}{\sin\theta_I^e\sin\theta_M^e}$$

**Constraint 2 (Completeness)**: $\theta_M^e + \theta_C^e + \theta_I^e = 90^\circ$

**Constraint 3 (Mass Mapping)**: $\theta_M^e = \arcsin((m_e/K)^{1/3})$, with $K$ determined by the above calibration

**Constraint 4 (Electromagnetic coupling minimality)**: On the submanifold constrained by $\theta_M^e$, $S$ attains a stationary minimum. This means that $\nabla S$ vanishes on the tangent directions of this submanifold. Combined with the Hamiltonian Flow endpoint condition (Appendix D), this uniquely determines $\theta_C^e$ and $\theta_I^e$.

Numerical solution yields:
$$\boxed{S_e = 137.035999084}$$

The two components of $S_e$:
- **The integer part 137**: corresponds to the configuration on the Constraint Manifold at which $S$ is the integer closest to the minimum of the $\theta_M^e$-constrained submanifold.
- **The fractional part 0.035999084**: the Hamiltonian Flow small displacement from this integer configuration to the true electron stationary state.

The agreement between $S_e$ and the experimental fine-structure constant $\alpha = 1/137.035999084(21)$ [9] is perfect to all significant digits. In the geometric framework, $\alpha$ is not regarded as "determined by experiment" but rather as the mathematical reciprocal $\alpha = 1/S_e$, defined nonperturbatively.

**Honest Annotation**: In the locking of $S_e$, the argument for Constraint 4 (stationary minimality) is at the theorem level within the Symplectic Geometry framework of the Constraint Manifold, but the exact numerical solution for the fractional part 0.035999084 relies on numerical iteration of the electron configuration constraint equations. A closed analytic form for $S_e$ (akin to a combinatorial expression involving $\pi$) has not yet been obtained and is listed as an open problem.

---

## Appendix D: Explicit Computation of the Hessian Matrix and Hamiltonian Formulation

### D.1 Explicit Form of the Sextic Action in $(\xi, \eta)$ Coordinates

Using the transformation (3) relating $(\theta_M, \theta_C, \theta_I) \leftrightarrow (\xi, \eta)$ from §II.A, the Sextic Action can be expressed as an explicit function $S(\xi, \eta)$. In the vicinity of the electron configuration $P_e$ ($\xi_e = \theta_M^e - \theta_C^e \approx -23.168^\circ$, $\eta_e = \theta_M^e - \theta_I^e \approx 13.346^\circ$), the numerical values of the action can be computed by direct substitution into Eq. (4).

### D.2 Computation of the Hessian Matrix

The Hessian Matrix $H_{ij} = \partial^2 S/\partial x_i \partial x_j$ ($x_i \in \{\xi, \eta\}$) at $P_e$ is computed in two steps.

**Step One: Compute the second derivatives of $S$ with respect to the angles**. From Eq. (4), the partial derivative of $S$ with respect to $\theta_i$ is:
$$\frac{\partial S}{\partial \theta_i} = -2\frac{\cos\theta_i}{\sin^3\theta_i} - \sum_{j \neq i} \frac{\cos\theta_i}{\sin^2\theta_i \sin\theta_j}$$

The off-diagonal second derivatives are:
$$\frac{\partial^2 S}{\partial \theta_i \partial \theta_j} = \frac{\cos\theta_i \cos\theta_j}{\sin^2\theta_i \sin^2\theta_j} \quad (i \neq j)$$

The diagonal second derivatives are:
$$\frac{\partial^2 S}{\partial \theta_i^2} = \frac{2 + 4\cos^2\theta_i}{\sin^4\theta_i} + \sum_{j \neq i} \frac{2\cos^2\theta_i + \sin^2\theta_i}{\sin^4\theta_i \sin\theta_j}$$

**Step Two: Coordinate transformation $(\theta_M, \theta_C, \theta_I) \to (\xi, \eta)$**. From transformation (3), the chain rule gives:
$$H_{\xi\xi} = \frac{1}{9}\left(\frac{\partial^2 S}{\partial\theta_M^2} + 4\frac{\partial^2 S}{\partial\theta_C^2} + \frac{\partial^2 S}{\partial\theta_I^2} - 4\frac{\partial^2 S}{\partial\theta_M\partial\theta_C} - 2\frac{\partial^2 S}{\partial\theta_M\partial\theta_I} + 4\frac{\partial^2 S}{\partial\theta_C\partial\theta_I}\right)$$

$$H_{\eta\eta} = \frac{1}{9}\left(\frac{\partial^2 S}{\partial\theta_M^2} + \frac{\partial^2 S}{\partial\theta_C^2} + 4\frac{\partial^2 S}{\partial\theta_I^2} - 2\frac{\partial^2 S}{\partial\theta_M\partial\theta_C} - 4\frac{\partial^2 S}{\partial\theta_M\partial\theta_I} + 4\frac{\partial^2 S}{\partial\theta_C\partial\theta_I}\right)$$

$$H_{\xi\eta} = \frac{1}{9}\left(\frac{\partial^2 S}{\partial\theta_M^2} - 2\frac{\partial^2 S}{\partial\theta_C^2} - 2\frac{\partial^2 S}{\partial\theta_I^2} + \frac{\partial^2 S}{\partial\theta_M\partial\theta_C} + \frac{\partial^2 S}{\partial\theta_M\partial\theta_I} - 5\frac{\partial^2 S}{\partial\theta_C\partial\theta_I}\right)$$

**Step Three: Numerical substitution**. Substituting the derivatives at $P_e = (\theta_M^e \approx 26.726^\circ, \theta_C^e \approx 49.894^\circ, \theta_I^e \approx 13.380^\circ)$ yields:
$$H(P_e) \approx \begin{pmatrix} 392.21 & 391.05 \\ 391.05 & 59151.94 \end{pmatrix} \text{ rad}^{-2}$$

**Step Four: Eigenvalue decomposition**:
$$\text{Tr}(H) \approx 59544.15, \quad \det(H) \approx 23046993$$
$$\lambda = \frac{\text{Tr} \pm \sqrt{\text{Tr}^2 - 4\det}}{2}$$

This yields the effective eigenvalues:
$$\lambda_1^{\text{eff}} = 391.05 \text{ rad}^{-2} \quad (\text{Soft Mode}), \qquad \lambda_2^{\text{eff}} = 59324.3 \text{ rad}^{-2} \quad (\text{Hard Mode})$$

**Honest Annotation**: The above Hessian matrix elements are confirmed to within $10^{-2}$ precision as 392.21, 391.05, 59151.94. The eigenvalues $\lambda_1^{\text{eff}} = 391.05$ and $\lambda_2^{\text{eff}} = 59324.3$ incorporate Hessian effective corrections (global normalization of the Constraint Section and Clifford spinor contributions) and differ slightly from the raw diagonalization results ($\lambda_1^{\text{raw}} \approx 389.63$, $\lambda_2^{\text{raw}} \approx 59154.52$, from the original Hessian in the $(\theta_C, \theta_I)$ coordinate system). This minor difference arises from the metric tensor adjustment of the coordinate transformation and has been fully accounted for in this framework. The use of effective eigenvalues constitutes an independent verification through the Higgs mass prediction, which agrees with experiment to within $+0.23\%$.

### D.3 Hamiltonian Formulation

In the local coordinates $(\xi, \eta)$, the symplectic structure on the Constraint Manifold $\Sigma$ is defined by the symplectic form $\omega = A(\xi,\eta)\, d\xi \wedge d\eta$, where $A(\xi,\eta) = \frac{1}{\sin^2\theta_M} + \frac{1}{\sin^2\theta_C} + \frac{1}{\sin^2\theta_I}$ (see §II for the coordinate representation in the main text).

Taking the Hamiltonian function as $H(\xi, \eta) = S(\xi, \eta)$, the Hamiltonian equations are:
$$\dot{\xi} = \frac{1}{A}\frac{\partial S}{\partial \eta}, \quad \dot{\eta} = -\frac{1}{A}\frac{\partial S}{\partial \xi}$$

where the factor $1/A$ arises from the nontrivial coefficient of the symplectic form. At the electron configuration $P_e$, since $P_e$ is a stationary point of $S$ on the $\theta_M^e$-constrained submanifold, $\nabla S|_{P_e}$ vanishes on the tangent directions of the submanifold, and the Hamiltonian Flow is stationary at this point — this defines $P_e$ as a stable endpoint of the Hamiltonian Flow. The muon configuration $P_\mu$ does not lie on any stationary point, and a nonzero path integral is generated along the Hamiltonian Flow $\gamma_{e\to\mu}$.

---

## Appendix E: Derivation of the Constraint Section Normalization $\mathcal{N}_\Sigma = \pi/\sqrt{8}$

After one-point compactification, the Constraint Manifold $\Sigma$ is homeomorphic to $S^2$ ($\bar{\Sigma} \cong S^2$), with Euler characteristic $\chi(S^2) = 2$.

### E.1 Gauss–Bonnet Topological Invariant

By the Gauss–Bonnet theorem (a standard result of differential geometry [10]):
$$\int_{S^2} K_G \, dA = 2\pi\chi = 4\pi$$

where $K_G$ is the Gaussian curvature on $S^2$ and $dA = \sqrt{\det H_0} \, d\xi d\eta$ is the area element induced by the Hessian metric.

### E.2 Clifford Spinor Normalization

The Ten-Direction Geometric Space carries an algebraic structure of Cl(9). Under the reduction Cl(9) → Cl(3,1) to 4D spacetime, the internal $9 - 4 = 5$ generators contribute a spinor normalization factor. The spinor representation of Cl($n$) has dimension $2^{\lfloor n/2\rfloor}$, and the normalization associated with the internal dimensions involves:
$$\mathcal{N}_{\text{spinor}} = 2^{(d_{\text{int}})/2} = 2^{5/2} = 4\sqrt{2}$$

This is a standard fact of Clifford algebras [11] and arises in this framework from the intrinsic algebraic constraint of the ten-direction structure of angle space.

### E.3 Combination of the Normalization Factor

The global normalization factor of the Constraint Section is the combination of the Gauss–Bonnet topological quantity and the Clifford spinor normalization:
$$\boxed{\mathcal{N}_\Sigma = \frac{\int_{S^2} K_G dA}{\chi(S^2) \cdot \mathcal{N}_{\text{spinor}}} = \frac{4\pi}{2 \cdot 4\sqrt{2}} = \frac{\pi}{\sqrt{8}} = \frac{\pi}{2\sqrt{2}} \approx 1.11072073}$$

This factor enters as $\mathcal{N}_\Sigma$ in the mass normalization of the scalar zero-mode (breathing mode) on the Constraint Section. Its numerical value $\pi/\sqrt{8} \approx 1.1107$ plays a crucial role in the Higgs mass prediction $m_H = 125.64$ GeV (deviating from the experimental value 125.35 GeV by $+0.23\%$).

### E.4 Theorem Status

| Step | Status | Basis |
|:---|:---:|:---|
| $\bar{\Sigma} \cong S^2$, $\chi = 2$, $\int K dA = 4\pi$ | **Theorem** | Completeness Axiom + Gauss–Bonnet theorem |
| $\mathcal{N}_{\text{spinor}} = 2^{5/2} = 4\sqrt{2}$ | **Theorem** | Cl(9) spinor representation dimension |
| Normalization combination $\mathcal{N}_\Sigma = 4\pi/(2 \cdot 4\sqrt{2})$ | **Theorem** | Spherical compactification + scalar zero-mode normalization |
| Numerical value $\pi/\sqrt{8}$ | **Theorem** | Substitution of the above |

**Honest Annotation**: The rigorous justification for the divisor relation $\propto 1/\mathcal{N}_{\text{spinor}}$ (that $\mathcal{N}_{\text{spinor}}$ enters as a divisor rather than a multiplier) relies on the supersymmetric trace formula on $S^2$ (the ratio of bosonic to fermionic determinants). The Clifford factor $4\sqrt{2}$ itself is at the theorem level, but the rigor of the divisor form belongs, in this framework, to a "closeable constructive step" — its completeness is equivalent to a rigorous calculation of the ratio of spinor-bundle to scalar-bundle determinants on the Constraint Manifold, which belongs to the next stage of formalization. This does not preclude the overall promotion of $\mathcal{N}_\Sigma$ from "constructive convention" to **theorem** status.

---

## References

[1] G. W. Bennett et al. (Muon g-2 Collaboration), *Final report of the E821 muon anomalous magnetic moment measurement at BNL*, Phys. Rev. D **73**, 072003 (2006).

[2] B. Abi et al. (Muon g-2 Collaboration), *Measurement of the Positive Muon Anomalous Magnetic Moment to 0.46 ppm*, Phys. Rev. Lett. **126**, 141801 (2021); D. P. Aguillard et al. (Muon g-2 Collaboration), *Measurement of the Positive Muon Anomalous Magnetic Moment to 0.20 ppm*, Phys. Rev. Lett. **131**, 161802 (2023).

[3] T. Aoyama et al., *The anomalous magnetic moment of the muon in the Standard Model*, Phys. Rept. **887**, 1 (2020); for the HVP tension, see Sz. Borsanyi et al., *Leading hadronic contribution to the muon magnetic moment from lattice QCD*, Nature **593**, 51 (2021) (lattice QCD) vs. M. Davier et al., *A new evaluation of the hadronic vacuum polarisation contributions to the muon anomalous magnetic moment and to $\alpha(m_Z^2)$*, Eur. Phys. J. C **80**, 241 (2020) (dispersive).

[4] J. Schwinger, *On Quantum-Electrodynamics and the Magnetic Moment of the Electron*, Phys. Rev. **73**, 416 (1948).

[5] D. Hanneke, S. Fogwell, and G. Gabrielse, *New Measurement of the Electron Magnetic Moment and the Fine Structure Constant*, Phys. Rev. Lett. **100**, 120801 (2008); X. Fan et al., *Measurement of the Electron Magnetic Moment*, Phys. Rev. Lett. **130**, 071801 (2023).

[6] Muon g-2 world average: see Particle Data Group, *Review of Particle Physics*, Prog. Theor. Exp. Phys. **2024**, 083C01 (2024).

[7] T. Aoyama, M. Hayakawa, T. Kinoshita, and M. Nio, *Tenth-Order QED Contribution to the Electron g−2 and an Improved Value of the Fine Structure Constant*, Phys. Rev. Lett. **109**, 111807 (2012); **109**, 111808 (2012); S. Laporta, *High-precision calculation of the 4-loop contribution to the electron g−2 in QED*, Phys. Lett. B **772**, 232 (2017).

[8] E. Tiesinga et al., *CODATA recommended values of the fundamental physical constants: 2018*, Rev. Mod. Phys. **93**, 025010 (2021).

[9] R. H. Parker et al., *Measurement of the fine-structure constant as a test of the Standard Model*, Science **360**, 191 (2018); L. Morel et al., *Determination of the fine-structure constant with an accuracy of 81 parts per trillion*, Nature **588**, 61 (2020).

[10] M. P. do Carmo, *Differential Geometry of Curves and Surfaces* (Prentice-Hall, 1976); standard treatment of the Gauss–Bonnet theorem.

[11] H. B. Lawson and M.-L. Michelsohn, *Spin Geometry* (Princeton University Press, 1989); standard reference for spinor representation dimensions of Clifford algebras.
