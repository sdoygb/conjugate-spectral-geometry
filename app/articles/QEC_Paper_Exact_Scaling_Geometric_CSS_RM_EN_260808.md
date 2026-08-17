# Exact Loss-Scaling Laws for Reed–Muller CSS Codes: Geometric Classification, Transversal Operations, and Four-Order Experimental Discrimination

**Author**: Ouyang Guobin

**Affiliation**: Shunde District, Foshan, Guangdong Province, China

**Email**: sdoygb@gmail.com

**ORCID**: 0009-0006-0008-5894

---

## Abstract

We derive exact closed-form logical failure rates for the affine-complete Reed–Muller CSS codes $[[2^m,\, 2^m - 2\sum_{i=0}^{r}\tbinom{m}{i},\, 2^{r+1}]]$ ($2r < m-1$) under independent per-qubit tilted noise. The unified scaling law reads

$$\mathrm{loss}(\theta_{\max}) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta_{\max}^{2w_0} + O(\theta_{\max}^{2w_0+2}), \qquad w_0 = \lceil d/2\rceil,$$

where the degeneracy fraction $P(w_0)$ and the minimum-weight decoding failure rate $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$ are closed forms in Gaussian-binomial flat counts of $\mathrm{GF}(2)^m$, with class size $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$. The parity of the distance governs the mechanism: for the PG-complete family (odd $d = 3$) the types $XX, XY, YX, YY$ ($4/9$ of the layer) leave an $X$-component logical residual and fail, $XZ, ZX$ recover perfectly, and $YZ, ZY, ZZ$ leave a pure $Z$ logical operator that acts as $\pm 1$ on $|0_L\rangle$ (lossless): $\mathrm{fail}(2) = 4/9$; even $d$ gives $\mathrm{fail} = 1-\langle 1/v \rangle$, unifying the projective-geometric and affine-complete families. A universality theorem extends the result to arbitrary independent Pauli channels. We determine the transversal gate set $\{$Pauli, CNOT, $H$, diagonal phase gates, logical measurement$\}$: transversal $H$ is legal because the $X$- and $Z$-stabilizer spaces coincide, and transversal $S^{\otimes n}$ induces the exactly computed phase gate $\bar X_a \mapsto i^{|a|}\,\bar X_a$. All structural claims are verified by an $O(n^2)$ syndrome-structure certificate on codes up to $[[1024, 252, 32]]$. The four distinct leading exponents $\theta^4, \theta^8, \theta^{16}, \theta^{32}$ at fixed $n = 1024$ provide a closed-form experimental discriminator.

---

## 1. Introduction

### 1.1 Why exact failure-rate analysis

Quantum error correction promises to convert noisy physical qubits into reliable logical qubits, but the quantitative content of the promise is a scaling law: how the logical failure rate decays as the physical noise is reduced. The standard threshold theorems [1, 2, 3, 4] establish *existence* of a noise threshold below which arbitrarily low logical error rates are achievable, but they do not deliver *closed-form* failure rates for concrete codes. Numerical simulations supply rates for specific instances, yet they scale poorly with code size and offer no structural explanation of the exponents and coefficients observed.

This paper develops a complementary, fully analytic program for a distinguished family of CSS codes: the failure rate is computed in closed form — both exponent *and* coefficient — and every structural claim entering the computation is verified by an enumeration-free certificate that runs in $O(n^2)$ time on codes of up to 1024 physical qubits. The closed forms expose a direct quantitative link between the *geometry* of the code (affine flats of the ambient $\mathrm{GF}(2)^m$) and the *performance* (failure rate), a link that is invisible in threshold analysis and only partially visible in numerical studies.

Three consequences motivate the exact approach.

(i) **Experimental discrimination.** Different code families exhibit failure rates $\theta^4$, $\theta^8$, $\theta^{16}$, $\theta^{32}$ at fixed physical qubit budget ($n = 1024$). The exponents differ by orders of magnitude in the small-noise regime, providing a sharp quantitative discriminator — the prediction is entirely closed-form.

(ii) **Noise-model tomography.** The coefficient of the leading term is a function of the error-layer structure (degeneracy fraction $P(w_0)$ and failure rate $\mathrm{fail}(w_0)$). A measurement of the loss curve at two noise strengths separates the exponent (structure) from the coefficient (layer statistics), allowing the noise model itself to be tested.

(iii) **Recovery design.** The class-size closed form $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$ quantifies exactly how many error patterns share a syndrome with a given error $A$; the failure rate $1-\langle 1/v\rangle$ is the probability that minimum-weight decoding selects the wrong partner. This converts degeneracy from an obstacle into a precisely controlled resource.

### 1.2 Tilted noise and geometric completeness

The noise model studied here — *tilted coherent noise* — injects on each qubit an independent rotation

$$U(\theta_i) = \cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$$

by a random Pauli $E_i$, with angles $\theta_i \in [0, \theta_{\max}]$ bounded by a single parameter. Two features distinguish it from the depolarizing channel commonly assumed in threshold analyses. First, it is *coherent*: the state retains amplitude information, and the detection probability of a single-qubit rotation is exactly $\sin^2(\theta_i/2)$ — a closed form that is itself measurable. Second, it is *inhomogeneous*: different qubits receive different rotation angles, and only the upper bound $\theta_{\max}$ enters the scaling prediction. The expansion of the loss in powers of $\theta_{\max}$ is then organized by the *weight* of the injected error patterns, and each layer $w$ contributes $\theta_{\max}^{2w}$ with a coefficient built from three factors: the binomial $C(n,w)$, the degeneracy fraction $P(w)$ (fraction of weight-$w$ errors possessing a same-syndrome partner), and the decoding failure rate $\mathrm{fail}(w)$ (probability that minimum-weight decoding selects the wrong partner).

The central structural claim is that, for the code families studied here, all three factors are *geometrically determined*: $P(w)$ and $\mathrm{fail}(w)$ are closed forms in affine/projective flat counts of $\mathrm{GF}(2)^m$. We call such codes *geometrically complete* (Definition 2.4): (i) the minimum weight of non-trivial logical operators equals the distance $d$; (ii) the partner structure of errors of weight $w \ge d/2$ is governed by flat-counting closed forms. Two families satisfy the definition: the projective-geometric (PG-complete) Hamming CSS codes $[[2^m-1,\,2^m-1-2m,\,3]]$ and the affine-complete (AG-complete) Reed–Muller CSS codes $[[2^m,\, 2^m-2s,\, 2^{r+1}]]$ with $s = \dim \mathrm{RM}(r,m)$.

### 1.3 Contributions

1. **Unified scaling law (Theorem 16).** For any geometrically complete CSS code under independent tilted noise with bound $\theta_{\max}$, minimum-weight decoding yields the closed form
$$\mathrm{loss}(\theta_{\max}) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta_{\max}^{2w_0} + O(\theta_{\max}^{2w_0+2}),$$
with $w_0 = \lceil d/2 \rceil$; the leading exponent is $d$ for even $d$ and $d+1$ for odd $d$. The parity dichotomy of the failure rate is resolved: odd $d$ forces cross-layer partners and, at the $|0_L\rangle$ encoding, $\mathrm{fail}(2) = 4/9$ for the PG-complete family (the pure $Z$ logical residuals are lossless); even $d$ gives same-layer partners and $\mathrm{fail} = 1 - \langle 1/v\rangle$.

2. **Class-size and failure-rate closed forms (Theorems 17–18).** For the affine-complete family, the weight-$2^r$ layer has class size $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$ where $s = \dim \mathrm{aff}(A)$; consequently $\mathrm{fail}(w_0) = 1 - P(3)/2 - P(\le 2)\,2^{2-m}$ for $r=2$, $= 1 - 2^{1-m}$ for $r=1$, and $\approx 1/2$ for $r \ge 3$ (with exponentially small corrections). All entries of Table 3 are recovered from the closed forms.

3. **Pauli-channel universality (Theorem 21).** The scaling law holds verbatim for arbitrary independent per-qubit Pauli channels: with $X$-side error probability $\varepsilon$ (probability that the error operator contains $X$ or $Y$), the $X$-side failure rate equals $\sum_{w\ge w_0} C(n,w)\,\varepsilon^w(1-\varepsilon)^{n-w}\,\mathrm{fail}(w)$, with the same *unconditional* $\mathrm{fail}(w)$ as in the coherent case — the decoder is a deterministic function of syndrome and weight, and the channel enters only through $\varepsilon$. Coherent tilt: $\varepsilon = \sin^2(\theta/2)$; depolarizing: $\varepsilon = 2p/3$; phase damping (after twirling): $\varepsilon = 0$; amplitude damping (after twirling): $\varepsilon = \gamma/2$. Non-twirled coherent non-Pauli processes fall outside the framework (syndrome response becomes probabilistic); Pauli twirling — standard experimental practice [5, 6] — restores it.

4. **Enumeration-free verification (Section 3.3).** The structural claims entering the scaling law are verified without enumerating error patterns: column distinctness of the generator matrix implies full weight-2 detection in $O(n^2)$ time; the constant coordinate blocks cross-weight syndrome degeneracy (Theorem 5); quadratic monomials block weight-2 internal degeneracy for $r \ge 2$ (Theorem 6). The full structural certificate for $[[1024, 252, 32]]$ runs in 8.8 s.

5. **Transversal operations (Section 6).** The affine-complete family supports transversal Pauli, CNOT, and $H$ gates; transversal $S^{\otimes n}$ preserves the code space and induces the direction-dependent phase gate $\bar X_a \mapsto i^{|a|}\,\bar X_a$ with $\gamma_a = i^{|a|}$ (Theorem 23). The fault-tolerant operation set is $\{$transversal Pauli, CNOT, $H\} \cup \{$diagonal phase gates$\} \cup \{$logical measurement$\}$, and $T$ is interfaced by standard magic-state distillation — requiring only $d \ge 5$, satisfied by all members with $r \ge 2$.

6. **Four-order experimental discriminator (Section 8).** On a 64–1121 qubit platform, the members $[[1024, 1002, 4]]$, $[[1024, 912, 8]]$, $[[1024, 672, 16]]$, $[[1024, 252, 32]]$ predict loss slopes $\theta^4, \theta^8, \theta^{16}, \theta^{32}$ in log-log coordinates. The slope quadruple is a closed-form signature of the geometric structure; any deviation falsifies the class-size mechanism at the corresponding layer.

### 1.4 Related work

The relation of this work to the existing literature is analyzed in detail in Section 7. Briefly: the CSS construction is due to Calderbank–Shor [7] and Steane [2]; stabilizer formalism follows Gottesman [8]; Reed–Muller codes and their weight distributions are classical [9–12]; magic-state distillation follows Bravyi–Kitaev [13] and the fault-tolerance roadmaps and pedagogical surveys of Refs. [14, 15, 17]; threshold analyses for concatenated and topological codes are found in Refs. [3, 16]. The *exact closed-form failure-rate analysis with geometric coefficients* presented here appears to be new: standard treatments of Reed–Muller CSS codes (e.g., the Steane code $[[7,1,3]]$ as $\mathrm{RM}(1,3)$) focus on distance and thresholds, not on the layer-resolved degeneracy structure and its closed-form failure rates. Section 7 provides a systematic comparison, including the resolution of the 315/945 $= 1/3$ cross-weight degeneracy of the $[[15,7,3]]$ code observed in early numerical studies into the total loss fraction $4/9$ (the loss set $\{XX, XY, YX, YY\}$ differs from the cross-weight set $\{XX, ZZ, YY\}$: $ZZ$ shares a syndrome with a single-qubit error, but its residual is a pure $Z$ logical operator, which is lossless at the $|0_L\rangle$ encoding).

### 1.5 Structure of the paper

Section 2 collects the notation and the general framework: stabilizer formalism, CSS codes, Reed–Muller codes, the tilted noise model, and the definition of geometric completeness. Section 3 introduces the geometric families — the PG-complete codes (why $d = 3$ is locked) and the affine-complete codes (parameters, distance, enumeration-free verification, logical-operator counting, numerical verification). Section 4 develops the coherent-tilt formalism and the zero-loss structure: the detection closed form, the zero-loss theorem, and the degeneracy hierarchy (inclusion equivalence, the full-degeneracy boundary, and the closed-form degeneracy proportion). Section 5 states and proves the unified scaling law, the class-size and failure-rate closed forms, the next-to-leading order, and the Pauli-channel universality theorem, with instantiation on seven family members. Section 6 establishes the transversal operation set and the fault-tolerant interface to the $T$ gate. Section 7 compares with the existing literature. Section 8 presents the four-order experimental discriminator on a 64–1121 qubit platform, including the statistical criteria, the time budget, and the falsification conditions. Section 9 concludes.

**How to read this paper.** Three tracks are provided for readers of different backgrounds. *Theory track* (structure and proofs): Section 2 → Section 3 → Section 5 (Theorems 15–18) → Section 6, with Section 4 as background. *Experiment track* (discriminator protocol): Section 1.3 → Section 2.3 → Sections 5.2–5.3 → Section 8; the proofs of Sections 3.3–3.4 and Section 6 may be skimmed. *First-contact track* (intuition first): Section 1 → Sections 2.2–2.3 → Section 4.2 → Section 5.2 → Section 8.1; the notation table at the head of Section 2 is the companion reference. The canonical worked example throughout the paper is the minimal member $[[16,6,4]]$ ($m = 4$, $r = 1$): it is introduced in Section 3.2, its zero-loss structure is exhibited in Section 4.2, its closed-form loss is derived in Section 5.2, its transversal gates are verified in Section 6.5, and it provides the smallest-scale discriminator test in Section 8.1.

---

## 2. Preliminaries

**Notation.** The symbols used throughout are collected here for reference; each is defined again at first use.

| Symbol | Meaning |
|---|---|
| $[[n,k,d]]$ | code parameters: $n$ physical qubits, $k$ logical qubits, distance $d$ |
| $m$, $r$ | affine-geometry dimension ($\mathrm{AG}(m,2)$); Reed–Muller order, $2r < m-1$ |
| $\mathrm{RM}(r,m)$ | Reed–Muller code of degree-$r$ polynomials, $\dim = \sum_{i\le r}\binom{m}{i}$, $\min\mathrm{wt} = 2^{m-r}$ |
| $H$ | generator matrix of $\mathrm{RM}(r,m)$: evaluation rows of all monomials of degree $\le r$ |
| $C$, $C^\perp$ | stabilizer space $\mathrm{rowspace}(H)$; dual code = logical space $L$ |
| $\chi_A$ | error pattern supported on $A \subseteq \mathrm{AG}(m,2)$ |
| $\mathrm{wt}(\cdot)$ | Hamming weight |
| $\left[\begin{smallmatrix}m\\ k\end{smallmatrix}\right]_2$ | Gaussian binomial: number of $k$-dimensional subspaces of $\mathbb{F}_2^m$ |
| $\mathrm{flats}(m,k)$ | number of $k$-dimensional affine flats in $\mathrm{AG}(m,2)$ |
| $s$ | affine span dimension of a support $A$ |
| $v(A)$ | syndrome-class size of $\chi_A$ at weight $2^r$ (Theorem 18) |
| $w_0 = \lceil d/2 \rceil$ | leading loss layer |
| $C(n,w)$ | binomial coefficient |
| $P(w)$ | degeneracy fraction of the weight-$w$ layer |
| $\mathrm{fail}(w)$ | decoding failure rate of the weight-$w$ layer |
| $P'_r(m)$ | cross-layer degeneracy proportion at weight $2^r+1$ (Prop. 19) |
| $\theta_i$, $\theta_{\max}$ | tilt angle of qubit $i$; its common upper bound, the single noise parameter |
| $U(\theta_i)$ | coherent rotation $\cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$ |
| $\sin^2(\theta_i/2)$ | detection probability of a single-qubit injection (Prop. 8) |
| $\mathrm{loss}(\theta)$ | expected infidelity after optimal (minimum-weight) decoding |
| $c_d$ | leading coefficient of Theorem 16 |
| $\kappa_r(m)$ | logical-$Z$-flip fraction (Sec. 5.3) |
| $\varepsilon$ | $X$-side error probability of a general Pauli channel (Theorem 21) |
| $\langle \cdot \rangle$ | average over the angle distribution, or class-size-weighted average (context) |
| $|0_L\rangle$ | logical zero state |

### 2.1 Stabilizer formalism and CSS codes

Let $\mathcal{P}_n$ be the $n$-qubit Pauli group. A stabilizer code is the joint $+1$ eigenspace $\mathcal{C}(S)$ of an abelian subgroup $S \subset \mathcal{P}_n$ not containing $-I$; its parameters are written $[[n,k,d]]$, with $k$ logical qubits and distance $d$ equal to the minimum weight of a Pauli operator in the centralizer $\mathcal{Z}(S)$ that is not in $S$. The syndrome of an error $E$ is the list of commutation relations of $E$ with a fixed generating set of $S$; a decoding rule maps syndromes to recovery operators.

**CSS construction** [2, 7]. Let $C_2 \subseteq C_1 \subseteq \mathbb{F}_2^n$ be classical linear codes. The CSS code $\mathrm{CSS}(C_1, C_2)$ has stabilizer generated by $\{X_v : v \in C_2\} \cup \{Z_v : v \in C_1^\perp\}$, where $X_v = \bigotimes_i X^{v_i}$ and $Z_v = \bigotimes_i Z^{v_i}$. Its parameters satisfy $k = \dim C_1 - \dim C_2$ and

$$d = \min\big\{\mathrm{wt}(C_1 \setminus C_2),\; \mathrm{wt}(C_2^\perp \setminus C_1^\perp)\big\},$$

with $\mathrm{wt}(\mathcal{D})$ the minimum Hamming weight of a vector in $\mathcal{D}$. The logical zero state is $|0_L\rangle = \frac{1}{\sqrt{|C_2|}}\sum_{x \in C_2} |x\rangle$. Logical operators: for $a \in C_1 \setminus C_2$ (respectively $a \in C_2^\perp \setminus C_1^\perp$), $X_a$ (respectively $Z_a$) is a logical operator.

**Self-orthogonal symmetric CSS codes.** A CSS code of the form $\mathrm{CSS}(H, H)$ — written with a single matrix $H$ whose row space is the stabilizer space $C$ — has both $X$- and $Z$-stabilizers generated from the *same* space $C$, and is well defined precisely when $C$ is self-orthogonal, $C \subseteq C^\perp$. Then $X$-stabilizer space $=$ $Z$-stabilizer space $= C$, and $k = n - 2\dim C$. The logical spaces are $L = C^\perp$; non-trivial logical operators have supports in $C^\perp \setminus C$.

**Minimum-weight decoding.** Given syndrome $s$, the decoder selects a minimum-weight error $e$ with that syndrome and applies the corresponding recovery. If the true error and the selected representative differ by a logical operator (i.e., the syndrome class contains a non-trivial logical), the correction fails. The *decoding failure rate* $\mathrm{fail}(w)$ of a weight-$w$ layer is the probability that minimum-weight decoding fails for a uniformly random weight-$w$ error pattern; equivalently, the fraction of weight-$w$ patterns whose syndrome class has a non-unique minimum-weight representative.

### 2.2 Reed–Muller codes

Identify $\mathbb{F}_2^m$ with the $2^m$ points of the affine geometry $\mathrm{AG}(m,2)$.

**Definition 2.1** (Reed–Muller code). For $0 \le r \le m$, the Reed–Muller code $\mathrm{RM}(r,m)$ consists of all evaluation vectors $\big(f(p)\big)_{p \in \mathrm{AG}(m,2)}$ of polynomials $f \in \mathbb{F}_2[x_1,\dots,x_m]$ of degree $\le r$.

Standard facts [9, 11]:

$$\dim \mathrm{RM}(r,m) = \sum_{i=0}^{r} \binom{m}{i}, \qquad \min\mathrm{wt}\,\mathrm{RM}(r,m) = 2^{m-r},$$

and the **duality theorem**: $\mathrm{RM}(r,m)^\perp = \mathrm{RM}(m-r-1, m)$. In particular $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(r,m)^\perp$ if and only if $2r < m-1$ — the self-orthogonality condition that makes the symmetric code $\mathrm{CSS}(H,H)$ — $H$ the generator matrix of $\mathrm{RM}(r,m)$ — a valid CSS code.

Two counting inputs from affine geometry are used throughout. The number of $k$-dimensional affine flats in $\mathrm{AG}(m,2)$ is

$$\mathrm{flats}(m,k) = 2^{m-k}\left[\begin{matrix}m\\ k\end{matrix}\right]_2 = 2^{m-k}\prod_{i=0}^{k-1}\frac{2^{m-i}-1}{2^{k-i}-1},$$

with the Gaussian binomial $\bigl[\begin{smallmatrix}m\\ k\end{smallmatrix}\bigr]_2$; and the indicator functions of $k$-flats are exactly the minimum-weight vectors of $\mathrm{RM}(m-k, m)$: a $(k+1)$-flat indicator has weight $2^{k+1}$ and degree $m-k-1$.

**Weight layers.** We record the weight-parity structure needed in Section 5: every codeword of $\mathrm{RM}(r,m)$ with $r \le m-3$, $m \ge 4$, has weight $\equiv 0 \pmod 4$. (Indeed $\mathrm{RM}(m-2,m)$ is the even-weight subspace and the minimum weight $2^{m-r} \ge 8$; the congruence follows from the standard weight distribution of Reed–Muller codes [12].)

### 2.3 Tilted noise model and loss expansion

**Coherent tilted noise.** Each physical qubit $i$ receives an independent rotation $U(\theta_i) = \cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$ by a Pauli $E_i$, with $\theta_i \in [0, \theta_{\max}]$. The bound $\theta_{\max}$ is the single noise parameter. For a fixed injection pattern $\mathbf{E} = (E_1,\dots,E_n)$, the probability weight of the configuration is $\prod_i \sin^2(\theta_i/2)$ for the error part and $\prod_i \cos^2(\theta_i/2)$ for the identity part. Two measurable closed forms follow from the coherent structure:

- detection probability of a single-qubit injection: $\sin^2(\theta_i/2)$ (the syndrome flip probability);
- non-detected paths preserve fidelity: the projection back to the code space is exact.

These were verified to machine precision by the numerical studies of Sections 3.5 and 5.5; they are the experimental anchors of the model.

**Loss expansion.** Let $\mathrm{loss}(\theta_{\max})$ be the expected infidelity after optimal (minimum-weight) recovery, averaged over random angles $\theta_i \in [0,\theta_{\max}]$ and random Pauli types. Expanding in powers of $\theta_{\max}$:

$$\mathrm{loss}(\theta_{\max}) = \sum_{w \ge 1} C(n,w)\,P(w)\,\mathrm{fail}(w)\,\big\langle \sin^{2}(\theta/2) \big\rangle^{w} \,\big\langle \cos^{2}(\theta/2) \big\rangle^{n-w},$$

where the averages are over the angle distribution; for the uniform bound model, $\langle \sin^{2}(\theta/2)\rangle = \theta_{\max}^{2}/12 + O(\theta_{\max}^{4})$, and $\langle \cos^{2}(\theta/2)\rangle = 1 + O(\theta_{\max}^2)$. The three factors in the coefficient of $\theta_{\max}^{2w}$ are: $C(n,w)$ — the number of weight-$w$ injection supports; $P(w)$ — the *degeneracy fraction* of the weight-$w$ layer, i.e., the fraction of weight-$w$ errors possessing at least one distinct same-syndrome partner; and $\mathrm{fail}(w)$ — the *decoding failure rate* of that layer. A layer with no same-syndrome partners ($P(w) = 0$) contributes nothing; a layer with unique minimum-weight representatives has $\mathrm{fail}(w) = 0$; the leading surviving layer is $w_0 = \lceil d/2 \rceil$ (Theorem 9).

**Pauli-channel form.** For a general independent per-qubit Pauli channel with $X$-side error probability $\varepsilon$ (the probability that the error operator has an $X$ or $Y$ component; $Z$ errors are invisible to the $X$-syndrome), the $X$-side failure rate is

$$\mathrm{loss}(\varepsilon) = \sum_{w \ge 0} C(n,w)\,\varepsilon^w (1-\varepsilon)^{n-w}\,\mathrm{fail}(w).$$

The channel constants: coherent tilt $\varepsilon = \sin^2(\theta/2)$; depolarizing with rate $p$: $\varepsilon = 2p/3$; phase damping (twirled): $\varepsilon = 0$; amplitude damping (twirled): $\varepsilon = \gamma/2$. The universality of the coefficient sequence $\mathrm{fail}(w)$ across channels is Theorem 21.

### 2.4 Geometric completeness

**Definition 2.2** (Geometrically complete CSS code). A CSS code $[[n,k,d]]$ with stabilizer space $S = \mathrm{rowspace}(H)$ and logical space $L = S^\perp$ is *geometrically complete* if

(i) the minimum weight of $L \setminus S$ equals the distance $d$;

(ii) for every error weight $w \ge d/2$, the partner structure — the assignment of same-syndrome representatives — is governed by closed-form counts of affine/projective flats of $\mathrm{GF}(2)^m$: the class size $v(A)$ of an error support $A$ depends only on the affine span dimension $s = \dim \mathrm{aff}(A)$ through an explicit formula.

Two families satisfy the definition:

- **PG-complete codes**: $H$ columns = all nonzero vectors of $\mathbb{F}_2^m$ (the simplex code as stabilizer), parameters $[[2^m-1,\, 2^m-1-2m,\, 3]]$, logical space the Hamming code (Section 3.1);
- **AG-complete codes** (affine-complete): $H$ = generator matrix of $\mathrm{RM}(r,m)$ evaluated on all $2^m$ points of $\mathrm{AG}(m,2)$, parameters $[[2^m,\, 2^m - 2\dim\mathrm{RM}(r,m),\, 2^{r+1}]]$ for $2r < m-1$ (Section 3.2).

Both families are CSS codes in the standard sense; the "completeness" is a structural property of their syndrome geometry — the partner structure is exactly computable, not merely estimable.

---

## 3. Geometric families of CSS codes

### 3.1 Projective-geometric codes: why $d = 3$ is locked

The PG-complete family is obtained by taking as stabilizer space the simplex code: $H$ has as columns all nonzero vectors of $\mathbb{F}_2^m$ (points of the projective geometry $\mathrm{PG}(m-1,2)$), yielding the Hamming CSS codes $[[2^m-1,\, 2^m-1-2m,\, 3]]$ with $S = \mathrm{Simplex}(m)$ and $L = \mathrm{Hamming}(m)$. This family is the baseline against which the affine-complete family is measured:

- **Distance locked at 3.** Any two distinct nonzero vectors are linearly independent, so no weight-2 logical exists ($d \ge 3$); but projective closure — the XOR of any two columns is again a column — forces a weight-3 logical operator for every pair of columns (three collinear points). Hence $d = 3$ *structurally*.
- **Cross-weight degeneracy fraction 1/3; loss fraction 4/9.** For the $[[15,7,3]]$ member, exactly 315 of the 945 weight-2 errors share a syndrome with a single-qubit error (the types $XX$, $ZZ$, $YY$): the shared syndrome class contains a weight-3 logical operator, and after recovery a residual weight-3 logical error remains. The fraction 315/945 $= 1/3$ is the fraction of Pauli types whose syndrome coincides with that of a weight-1 error, by column-XOR closure — this is the *cross-weight* degeneracy, not the loss fraction. The loss fraction at the $|0_L\rangle$ encoding is $4/9$: the types $XX, XY, YX, YY$ (420 errors) leave a residual logical operator containing an $X$ component (the state is flipped to the orthogonal logical state); $XZ, ZX$ (210 errors) recover perfectly; $YZ, ZY, ZZ$ (315 errors) leave a pure $Z$ logical operator, which acts as $\pm 1$ on $|0_L\rangle$ and is lossless. Hence $\mathrm{fail}(2) = 420/945 = 4/9$, the factor $P(2)\,\mathrm{fail}(2)$ of Theorem 16.
- **Loss $\theta^4$.** With $w_0 = \lceil 3/2 \rceil = 2$, the leading layer is weight 2 with $\mathrm{fail}(2) = 4/9$ (the types $XX, XY, YX, YY$ leave an $X$-component logical residual; $XZ, ZX$ recover perfectly; $YZ, ZY, ZZ$ leave a pure $Z$ logical operator, lossless at the $|0_L\rangle$ encoding), giving $\mathrm{loss} \sim \theta^4$ with coefficient $(4/9)\,C(2^m-1,2)\,2^{-4}$; numerically measured log-log slopes 4.04–4.14 on $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$ and slope 3.99 on $[[15,7,3]]$ (fixed 4-qubit injection).

The locked distance $d = 3$ motivates the affine construction: to reach $d \ge 5$ one needs every 4 columns affinely independent — a 4-arc. In binary projective space the counting bound is $\sim 2^N/3$ but explicit 4-arcs are far smaller ($\mathrm{PG}(3,2)$ has at most 5 points), so the projective point-set path cannot reach large distances with positive rate. The resolution is to *change the column space*: evaluate at all $2^m$ points of the affine geometry, which yields the Reed–Muller CSS family with arbitrarily large distance.

### 3.2 Affine-complete codes: definition, parameters, distance

**Definition 3.1** (Affine-complete code). Let $\mathrm{RM}(r,m)$ be the Reed–Muller code of Section 2.2, with generator matrix $H$ whose rows are the evaluations of all monomials of degree $\le r$ on the $2^m$ points of $\mathrm{AG}(m,2)$. The affine-complete code is the symmetric CSS code $\mathrm{CSS}(H,H)$ with stabilizer space $C = \mathrm{RM}(r,m)$, subject to the self-orthogonality condition $C \subseteq C^\perp$.

**Theorem 1** (Self-orthogonality). $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(r,m)^\perp$ if and only if $2r < m-1$.

*Proof.* By the duality theorem, $\mathrm{RM}(r,m)^\perp = \mathrm{RM}(m-r-1,m)$, and $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(m-r-1,m)$ iff $r \le m-r-1$, i.e. $2r \le m-1$; the strict inequality is required because $r = (m-1)/2$ would make the code self-dual with $k = 0$. ∎

**Theorem 2** (Parameters). The affine-complete code has parameters

$$\big[\!\big[\,2^m,\; 2^m - 2\sum_{i=0}^{r}\tbinom{m}{i},\; 2^{r+1}\,\big]\!\big].$$

*Proof.* $n = 2^m$ by construction. Since $X$- and $Z$-stabilizer spaces both equal $C = \mathrm{RM}(r,m)$ with $\dim C = \sum_i \binom{m}{i}$ (Section 2.2), $k = n - 2\dim C$. The distance is Theorem 3. ∎

**Theorem 3** (Distance). The minimum distance of the affine-complete code $\mathrm{CSS}(H,H)$ is $d = 2^{r+1}$.

*Proof.* Non-trivial logical operators have supports in $C^\perp \setminus C = \mathrm{RM}(m-r-1,m) \setminus \mathrm{RM}(r,m)$. By the duality theorem the minimum weight of $C^\perp$ is $2^{m-(m-r-1)} = 2^{r+1}$, attained by the indicator of an $(r+1)$-flat. Strict self-orthogonality ($2r < m-1$ implies $m-r > r+1$) ensures $\mathrm{RM}(m-r-1,m) \not\subseteq \mathrm{RM}(r,m)$; in fact the weight-$2^{r+1}$ layer of $\mathrm{RM}(m-r-1,m)$ — the $(r+1)$-flat indicators — lies entirely outside $\mathrm{RM}(r,m)$ because $\min \mathrm{wt}\,\mathrm{RM}(r,m) = 2^{m-r} > 2^{r+1}$. Hence $d = 2^{r+1}$. ∎

Representative members (with $\dim C = s$):

| $r$, $m$ | parameters | $d$ | $\dim C$ |
|---|---|---|---|
| 1, 5 | $[[32, 20, 4]]$ | 4 | 6 |
| 1, 6 | $[[64, 50, 4]]$ | 4 | 7 |
| 2, 6 | $[[64, 20, 8]]$ | 8 | 22 |
| 2, 7 | $[[128, 70, 8]]$ | 8 | 29 |
| 3, 8 | $[[256, 70, 16]]$ | 16 | 93 |
| 3, 9 | $[[512, 252, 16]]$ | 16 | 130 |
| 4, 10 | $[[1024, 252, 32]]$ | 32 | 386 |

Table 1. Representative members of the affine-complete family.

Note that the codes themselves are classical: Reed–Muller CSS codes have been studied since the early days of quantum error correction (the Steane code is $\mathrm{RM}(1,3)$). The contribution of the present work is not the codes but the *verification method and the closed-form structure*: enumeration-free certificates, the zero-degeneracy structure, and the logical-operator counting of Sections 3.3–3.4, which feed the exact failure-rate analysis of Section 4.

The smallest member of the family, $[[16,6,4]]$ ($m = 4$, $r = 1$), is not listed in Table 1: it satisfies the self-orthogonality condition ($2r = 2 < m - 1 = 3$) and, being small enough for full enumeration and state-vector simulation, serves as the canonical worked example throughout this paper (Sections 4.2, 5.2, 6.5, and 8.1).

![Figure 1: family parameters](figures/fig1_family_params.png)

**Figure 1.** The affine-complete family at fixed $n = 1024$ ($m = 10$): logical dimension $k = 2^{10} - 2\dim\mathrm{RM}(r,10)$ (left axis) and distance $d = 2^{r+1}$ (right axis, logarithmic) versus $r$. The four members $[[1024,1002,4]]$, $[[1024,912,8]]$, $[[1024,672,16]]$, $[[1024,252,32]]$ share a single platform and noise environment; their distinct leading exponents $\theta^4, \theta^8, \theta^{16}, \theta^{32}$ are the basis of the experimental discriminator of Sec. 8 (open symbols: $r = 0$, $d = 2$).

### 3.3 Enumeration-free verification

Full enumeration of error patterns is infeasible at $n = 1024$ (there are $\binom{1024}{2} \approx 5.2\times 10^5$ weight-2 patterns, but $\binom{1024}{4} \approx 4.6\times 10^{10}$ weight-4 patterns and $\binom{1024}{16} \sim 10^{33}$ at the leading layer of $[[1024,252,32]]$). The following structural theorems replace enumeration by $O(n^2)$ certificates.

**Theorem 4** (Column distinctness implies full weight-2 detection). The evaluation columns of $\mathrm{RM}(r,m)$ are pairwise distinct on $\mathrm{AG}(m,2)$. Consequently every weight-2 error pattern is detected: for any two distinct positions $a, b$, the $X$-syndrome $\mathrm{col}_a \oplus \mathrm{col}_b \ne 0$, and the same holds for the $Z$-syndrome; all nine Pauli types of weight-2 errors are detected.

*Proof.* The constant coordinate (the evaluation of the monomial 1) together with the coordinate functions $x_1,\dots,x_m$ separate any two distinct points of $\mathrm{AG}(m,2)$: if $p \ne q$, some coordinate function differs, so the evaluation columns differ in the corresponding row. The syndrome of the weight-2 error $(a,b)$ is $\mathrm{col}_a \oplus \mathrm{col}_b$ (for the $X$-type) and the same combination for the $Z$-type; a mixed Pauli error has syndrome $\mathrm{col}_a \oplus \mathrm{col}_b$ on both sides. Nonzero in all cases. ∎

**Theorem 5** (Cross-weight zero degeneracy). No weight-1 error shares a syndrome with any weight-2 error: the cross-weight syndrome degeneracy of the affine-complete family is exactly 0 (contrast: 1/3 for the PG-complete family).

*Proof.* The syndrome of a single-qubit error $X_a$ is the column $\mathrm{col}_a$, whose constant coordinate is 1 (the evaluation of the constant monomial at $a$ is 1). The syndrome of a weight-2 $XX$ error is $\mathrm{col}_a \oplus \mathrm{col}_b$, whose constant coordinate is $1 \oplus 1 = 0$. The constant coordinate — the new ingredient of the affine construction, absent in the projective one — blocks the equality $0 \ne 1$. In the PG family the constant coordinate does not exist, and the XOR of two columns is again a column, producing the 1/3 cross-layer degeneracy. ∎

**Theorem 6** (Weight-2 layer complete uniqueness for $r \ge 2$). For $r \ge 2$, any two distinct weight-2 error patterns have distinct syndromes: the weight-2 layer has zero internal degeneracy, and the full recovery table is conflict-free at weights 1 and 2.

*Proof.* Suppose $\{a,b\} \ne \{a',b'\}$ share a syndrome. Then for every monomial $f$ of degree $\le r$, $f(a) + f(b) = f(a') + f(b')$. The linear part ($f = x_i$) gives $a + b = a' + b'$: the pairs form a parallelogram. The quadratic part ($f = x_i x_j$) gives $s_i \delta_j + s_j \delta_i = 0$ for all $(i,j)$, where $s = a+b$ and $\delta = a + a'$. A nontrivial solution requires $s \parallel \delta$; over $\mathbb{F}_2$, $s = \delta$, i.e., the pairs coincide — contradiction. Hence all syndromes are distinct. (For $r = 1$ the linear part is insufficient: parallelogram degeneracy appears, e.g. $\mathrm{RM}(1,5)$: 496 pairs collapse into 31 classes — the $r=1$ anomaly quantified in the failure-rate analysis of Section 5.) ∎

### 3.4 Logical-operator counting

**Theorem 7** (Logical-operator counting). The number of weight-$d$ logical operators of the $X$-type in $\mathrm{CSS}(\mathrm{RM}(r,m))$ equals the number of $(r+1)$-dimensional affine flats of $\mathrm{AG}(m,2)$:

$$N_{\mathrm{logic}} = 2^{\,m-r-1}\left[\begin{matrix}m\\ r+1\end{matrix}\right]_2 = 2^{\,m-r-1}\prod_{i=0}^{r}\frac{2^{m-i}-1}{2^{r+1-i}-1}.$$

*Proof.* The weight-$d = 2^{r+1}$ vectors of $C^\perp = \mathrm{RM}(m-r-1,m)$ are exactly the indicators of $(r+1)$-flats (Section 2.2), and their number is the flat count. Every such vector lies in $L \setminus C$ since $\min\mathrm{wt}\,\mathrm{RM}(r,m) = 2^{m-r} > 2^{r+1}$; each is a logical operator by Definition 2.2 ($L = S^\perp$). ∎

The closed form was verified by exhaustive enumeration at small sizes: $\mathrm{RM}(1,5)$: 1240 logical operators of weight 4, equal to the 2-flat count of $\mathrm{AG}(5,2)$; $\mathrm{RM}(1,6)$: 10416, the 2-flat count of $\mathrm{AG}(6,2)$ (full enumeration of $\binom{64}{4}$ patterns, 2.8 s).

### 3.5 Numerical verification

The enumeration-free certificates of Theorems 4–6 and the counting of Theorem 7 were executed for all seven members of Table 1 (symbolic bit-mask arithmetic):

| code | (a) col. distinct | (b) weight-2 pairs | (c) 3000 samples | (d) cross-wt. deg. | (e) internal deg. | time |
|---|---|---|---|---|---|---|
| $[[32,20,4]]$ | ✓ | 496 ✓ | ✓ | 0/496 | 31 classes ($r=1$) | 0.11 s |
| $[[64,20,8]]$ | ✓ | 2016 ✓ | ✓ | 0/2016 | 0 | 0.33 s |
| $[[128,70,8]]$ | ✓ | 8128 ✓ | ✓ | 0/8128 | 0 | 0.43 s |
| $[[256,70,16]]$ | ✓ | 32640 ✓ | ✓ | 0/32640 | 0 | 1.52 s |
| $[[512,252,16]]$ | ✓ | 130816 ✓ | ✓ | 0/130816 | 0 | 2.46 s |
| $[[1024,252,32]]$ | ✓ | 523776 ✓ | ✓ | 0/523776 | 0 | 8.78 s |

Table 2. Verification results. (c) = random weight-3..$d-1$ syndrome sampling (3000 per code); (d) = cross-weight degeneracy count; (e) = internal (same-weight) degeneracy count at weight 2.

All certificates pass. Notably $[[1024, 252, 32]]$ — a 1024-qubit code with distance 32 — receives a complete structural certificate in 8.8 s with memory at the kilobyte level: the enumeration-free method renders thousand-qubit codes analytically tractable, which is the enabling step for the exact failure-rate analysis of Section 5.


---

## 4. Coherent θ-tilted noise and the zero-loss structure

In this section we analyze the response of the geometric code families of Sec. 3 to coherent single-qubit rotations. The key structural facts are: (i) the detection probability of a single-qubit rotation admits the closed form $\sin^2(\theta/2)$; (ii) errors of weight below the threshold $d/2$ are *completely recoverable* (zero-loss theorem); (iii) degeneracy reappears at exactly the weight layer $w_0 = \lceil d/2\rceil$, and its structure is governed by inclusion in affine flats; (iv) as a consequence the logical loss of the optimal decoder scales as $\theta^{2\lceil d/2\rceil}$, with a coefficient fixed by flat counts.

### 4.1 Detection closed form and undetectable logical directions

Recall the injection model of Sec. 2.3: each physical qubit $i$ undergoes an independent coherent rotation
$U(\theta_i) = \cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$ with $E_i \in \{X_i,Y_i,Z_i\}$ and $\theta_i \le \theta_{\max}$. The syndrome of a stabilizer code is measured projectively; the detection outcome for a stabilizer generator $g$ is the sign of $\langle \psi | g | \psi \rangle$ after injection.

**Proposition 8 (Detection closed form).** Let $U(\theta) = \cos(\theta/2)\,I + i\sin(\theta/2)\,E$ be a coherent injection on a single qubit, with $E$ a Pauli error anticommuting with the measured stabilizer generator. Then:
(a) the detection probability is $p_{\det}(\theta) = \sin^2(\theta/2)$, independent of the code and of the syndrome line;
(b) the conditional fidelity of the undetected branch is exactly $1$ (undetected injection projects the state back into the code space);
(c) logical-operator injections $\bar X$ or $\bar Z$ produce identically zero syndrome; acting on the logical zero state, a $\bar Z$-type injection is a global phase (zero loss) and an $\bar X$-type injection produces loss $\sin^2(\theta/2)$.

*Verification.* Direct state-vector simulation over the codes $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$ for all qubits and all Pauli types, with $\theta \in [0.05, 0.4]$, gives maximum deviation from the closed forms of $3.8\times10^{-16}$ (detection rate) and $2.2\times10^{-16}$ (conditional fidelities) (this work). The closed form (a) is the probability that the $E$ component of the rotated state is detected; since $U(\theta)$ prepares the superposition $\cos(\theta/2)|\psi\rangle + i\sin(\theta/2)E|\psi\rangle$ and the $E$ branch anticommutes with $g$, the detected probability is $|\sin(\theta/2)|^2$. ∎

Property (b) is the "undetected injection is harmless" principle: a missed detection leaves the state inside the code space, so no logical information is destroyed; only the detected branch triggers recovery. Property (c) reflects that logical operators commute with all stabilizers by definition.

### 4.2 Zero-loss theorem

The following structural result shows that coherent injections of weight below $d/2$ are *perfectly* correctable: the minimal-weight decoder recovers them exactly, and the post-recovery loss is identically zero.

**Theorem 9 (Zero-loss theorem).** Let $\mathcal{C} = [[n,k,d]]$ be any CSS code of minimum distance $d$. Inject coherent rotations $U(\theta_j) = \exp(i\theta_j P_j/2)$ on an arbitrary set of $t \le \lfloor(d-1)/2\rfloor$ qubits, with $P_j$ Pauli operators and $\theta_j \le \theta_{\max}$ arbitrary. After syndrome measurement and minimal-weight decoding, the loss is identically zero: $\mathrm{loss} = 0$ for every realization.

*Proof.* Expand the injected state in the Pauli basis: it is a superposition of terms $\chi_S$, $S \subseteq$ (injected set), $|S| \le t$, where $\chi_S$ is the weight-$|S|$ error on $S$. Fix $S$ with $w = |S| \le \lfloor(d-1)/2\rfloor$. Suppose some error $R'$ of weight $w' < w$ has the same syndrome as $\chi_S$. Then $\chi_S \cdot R' \in C^{\perp}$ and its weight satisfies $w + w' - 2|S \cap R'| \le 2w - 1 \le d - 2 < d$, contradicting that $C^{\perp}$ has minimum weight $d$. Suppose instead a distinct error $R'$ of the same weight $w$ shares the syndrome; then $\chi_S \cdot R'$ has weight $\le 2w - 2 < d$, again a contradiction. Hence the syndrome of $\chi_S$ is unique, minimal-weight decoding selects $R = \chi_S$ uniquely, and recovery is perfect. Summing over branches, the loss vanishes. ∎

**Corollary 10.** For the affine-complete code $[[64,20,8]]$ (Sec. 3), any injection on $\le 3$ qubits produces identically zero loss after optimal recovery. For comparison, the projective-geometric code $[[15,7,3]]$ already loses at weight 2: collinear pairs share the syndrome of a single-qubit error (Sec. 3.1), so the minimal-weight decoder applies a single-qubit correction and leaves a weight-3 logical residual with $\theta^4$ loss.

The corollary quantifies "distance buys noise immunity": a $d=8$ code is perfectly immune to coherent disturbances on up to three qubits, whereas a $d=3$ code pays $\theta^4$ already for two-qubit joint disturbances.

For the canonical minimal member $[[16,6,4]]$ ($m = 4$, $r = 1$), Theorem 9 guarantees identically zero loss for every single-qubit injection ($w = 1 < d/2 = 2$); the only measurable signature is the detection probability $\sin^2(\theta/2)$ of Prop. 8 — a 16-qubit laboratory check of the zero-loss structure before scaling to the larger members of Table 1.

### 4.3 Degeneracy hierarchy: inclusion equivalence and the full-degeneracy boundary

The zero-loss theorem pins the first potentially lossy layer at weight $w_0 = \lceil d/2\rceil$. For the affine-complete families, $d = 2^{r+1}$ is even and $w_0 = 2^r$. Whether this layer is degenerate — and how degenerate — is decided by a purely geometric criterion.

**Theorem 11 (Inclusion equivalence).** Let $\mathcal{C} = CSS(RM(r,m))$ be an affine-complete code with $d = 2^{r+1}$ and $C^{\perp} = RM(m-r-1,m)$. For an $X$-error $\chi_A$ of weight $2^r$ ($A \subset AG(m,2)$, $|A| = 2^r$), the following are equivalent:
(i) $\chi_A$ has a distinct same-weight partner $\chi_B$ with identical syndrome;
(ii) $A$ is contained in some $(r+1)$-flat $P$ ($|P| = 2^{r+1}$).
In this case $B = P \setminus A$ (the complement partner) and $\chi_A \oplus \chi_B = \chi_P \in C^{\perp}$.

*Proof.* (ii)$\Rightarrow$(i): $B = P\setminus A$ has $|B| = 2^{r+1} - 2^r = 2^r$, and $\chi_P = \chi_A \oplus \chi_B$ is the indicator of an $s$-flat, which is a polynomial of degree $m - s$; with $s = r+1$ this lies in $RM(m-r-1,m) = C^{\perp}$. Hence $\mathrm{syndrome}(\chi_A) = \mathrm{syndrome}(\chi_B)$.
(i)$\Rightarrow$(ii): equal syndromes give $\chi_A \oplus \chi_B \in C^{\perp}$ of weight $\le 2^{r+1} = d$; since $d$ is the minimum weight of $C^{\perp}$, the weight equals $d$, so $\chi_A \oplus \chi_B$ is a minimum-weight vector of $C^{\perp}$. Minimum-weight vectors of $RM(m-r-1,m)$ are exactly the indicators of $(r+1)$-flats: writing $\chi_P = \prod_{i=1}^{m-r-1}(1 + \ell_i)$ with linearly independent affine forms $\ell_i$, the zero set $P = \{v : \ell_i(v) = 0\ \forall i\}$ is an affine subspace of dimension $m - (m-r-1) = r+1$. Thus $A \sqcup B = P$ and $A \subset P$. ∎

For weights $w < 2^r$ the same argument excludes degeneracy altogether: $\chi_A \oplus \chi_B$ would have weight $\le 2w < d$, absent from $C^{\perp}$. This recovers the zero-degeneracy of Sec. 3.3 for the layers below $d/2$ and extends it to all $w < 2^r$.

**Theorem 12 (Full-degeneracy boundary).** The weight-$2^r$ layer of $CSS(RM(r,m))$ is fully degenerate (every $2^r$-subset is contained in some $(r+1)$-flat) if and only if $r \le 2$.

*Proof.* $A \subset (r+1)$-flat iff the affine span of $A$ has dimension $\le r+1$ iff the $2^r - 1$ difference vectors of $A$ span a space of dimension $\le r+1$. For $r=1$ there is one difference vector (rank $\le 1 \le 2$); for $r=2$ the three difference vectors of a 4-subset satisfy rank $\le 3 = r+1$ (three vectors of $\mathbb{F}_2^m$ always span at most dimension 3). For $r \ge 3$, $2^r - 1 > r+1$, and a generic $2^r$-subset has affine span of dimension $2^r - 1$ (probability $\to 1$ as $m$ grows), hence is contained in no $(r+1)$-flat. ∎

*Numerical confirmation* ($m=8$, $10^5$ random 8-subsets): affine-span ranks 4, 5, 6, 7 occur with counts 15, 1839, 33744, 64402; 64.4% of 8-subsets have maximal rank 7, confirming that generic $2^r$-subsets avoid $(r+1)$-flats.

The boundary $r \le 2$ means: codes of distance $d = 4$ and $d = 8$ have *completely* degenerate middle layers, while $d \ge 16$ codes are only partially degenerate. The quantitative proportion is a pure combinatorial quantity.

**Proposition 13 (Degeneracy proportion, closed form).** For $CSS(RM(r,m))$, the fraction $P_r(m)$ of weight-$2^r$ errors possessing a same-weight partner is

$$P_r(m) = \frac{\mathrm{flats}(m,r{+}1)\,E(r{+}1,2^r) + \mathrm{flats}(m,r)}{\binom{2^m}{2^r}},$$

where $\mathrm{flats}(m,k) = 2^{m-k}\left[\begin{smallmatrix}m\\ k\end{smallmatrix}\right]_2$ counts $k$-flats of $AG(m,2)$ (Gaussian binomial times the translation factor $2^{m-k}$) and $E(k,s) = \binom{2^k}{s} - \sum_{j<k}\mathrm{flats}(k,j)\,E(j,s)$ counts $s$-subsets of a fixed $k$-flat with affine span exactly $k$ (inclusion–exclusion). The first term counts $2^r$-subsets with span exactly $r+1$ (partner = flat complement), the second counts $2^r$-subsets that are entire $r$-flats (span exactly $r$, single partner-free class per flat).

*Properties.* For $r = 1,2$ the formula evaluates to $1$ identically (combinatorial identities: every 2-subset spans $\le 2$ dimensions; every 4-subset spans $\le 3$). For $r = 3$: $P_3(6) = 7.56\times10^{-3}$, $P_3(7) = 8.49\times10^{-4}$, $P_3(8) = 1.007\times10^{-4}$, $P_3(9) = 1.227\times10^{-5}$, $P_3(10) = 1.514\times10^{-6}$, with successive ratios $\approx 8.2$–$8.9 \approx 2^3$, confirming the leading-order exponent $3(m-4)$ of the approximation $P_r(m) \approx 2^{-(2^r - r - 2)(m - r - 1)}$. The closed form matches three independent numerical criteria (rank test, combinatorial count, syndrome matching) for $[[256,70,16]]$ (measured $1.5\times10^{-4}$ and $1.2\times10^{-4}$ vs. $1.007\times10^{-4}$, within $1.3\sigma$) and $[[512,252,16]]$ ($2.0\times10^{-5}$ vs. $1.227\times10^{-5}$, $1\sigma$).

Two remarks are in order. First, the earlier "independent uniform rank distribution" estimate (Sternberg formula) overestimates the true proportion by a factor 6.6 for $m=8$: the difference vectors of an $s$-subset are subject to distinctness constraints and are not independent. Second, the proportion is *strictly positive for every $r \ge 1$*: any $(r+1)$-flat contains $2^{r+1}$ points, and any choice of $2^r$ of them satisfies the inclusion condition. Positivity — not fullness — is what the scaling law of Sec. 5 requires.

### 4.4 Distance–noise scaling law

Assembling the ingredients of this section:

**Theorem 14 (Distance–noise scaling law).** Let $\mathcal{C}$ be a geometrically complete CSS code of distance $d$ (projective-geometric, $d = 3$, or affine-complete, $d = 2^{r+1}$). Under independent coherent noise with per-qubit bound $\theta_{\max}$, the loss of the optimal (minimal-weight) decoder satisfies

$$\mathrm{loss}(\theta_{\max}) \;\sim\; \theta_{\max}^{\,2\lceil d/2\rceil} \quad (\theta_{\max} \to 0),$$

i.e. $\theta^4$ for $d = 3$ and $\theta^d$ for even $d$.

*Proof.* Expand the injected state into weight-$w$ branches with amplitudes of order $\theta^w$. Branches with $w < w_0 := \lceil d/2\rceil$ have unique syndromes (the argument of Theorem 9 applies verbatim) and contribute zero loss. At weight $w_0$, degeneracy is possible and, for the geometrically complete families, present with strictly positive proportion: for PG codes ($d=3$, $w_0=2$) every weight-2 error is degenerate (the collinear mechanism alone accounts for $1/3$ of the layer); for AG codes the inclusion equivalence (Theorem 11) and positivity of $P_r(m)$ guarantee degeneracy at $w_0 = 2^r$. Within a same-layer degenerate class of size $v$ the decoder errs with probability $(v-1)/v \ge 1/2$; for the PG family the $|0_L\rangle$-encoding loss fraction is $4/9$ (Theorem 17(i)). Hence the lowest nonvanishing loss order is $(\theta^{w_0})^2 = \theta^{2w_0}$, contributed by the weight-$w_0$ layer; higher-weight branches contribute $o(\theta^{2w_0})$. ∎

*Instantiation.* (i) $d = 3$: the codes $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$ exhibit measured log-log slopes $4.04, 4.12, 4.14$ over $\theta_{\max} \in [0.05, 0.4]$ (this work); the $[[15,7,3]]$ code with fixed 4-qubit injection gives loss $= 6\cos^4(\theta/2)\sin^4(\theta/2) \sim 3\theta^4/8$ with slope $3.99 \approx 4$ (this work). (ii) $d = 8$: the $[[64,20,8]]$ code, 4-qubit injection, exhibits slope $7.96 \approx 8$ and weight-4 branch failure rate $48.5\%$ (200 trials) against the theoretical $50.7\%$ (this work). The four-order gap $\theta^4$ vs. $\theta^8$ between $d=3$ and $d=8$ codes is the experimental discriminator of Sec. 8.

## 5. Unified scaling law and failure-rate closed forms

The scaling law of Theorem 14 fixes the exponent; the unified framework of this section fixes the *coefficients* in closed form. The loss expansion is organized by weight layers; each coefficient factorizes into a combinatorial count $C(n,w)$, a degeneracy proportion $P(w)$, and a conditional failure rate $\mathrm{fail}(w)$ that depends only on the syndrome geometry — not on the noise channel. This channel independence is the content of the Pauli-channel universality theorem (Sec. 5.5).

### 5.1 Branch-level loss expansion

**Theorem 15 (Branch-level loss expansion).** Let $\mathcal{C} = [[n,k,d]]$ be a geometrically complete CSS code, and let independent coherent rotations with common bound $\theta$ act on all $n$ qubits. The loss of minimal-weight decoding admits the expansion

$$\mathrm{loss}(\theta) = \sum_{w \ge w_0} C(n,w)\,P(w)\,\mathrm{fail}(w)\,\left(\tfrac{\theta}{2}\right)^{2w}\left(1 - \tfrac{\theta^2}{4}\right)^{n-w},$$

where $P(w)$ is the proportion of weight-$w$ errors with non-unique syndrome (degenerate errors) and $\mathrm{fail}(w)$ is the conditional decoding failure rate on the weight-$w$ layer.

*Proof sketch.* Each qubit's rotation expands as $\cos(\theta/2)\,I + i\sin(\theta/2)\,E$; a term with errors on exactly the set $S$, $|S| = w$, carries amplitude $\sin^w(\theta/2)\cos^{n-w}(\theta/2)$, hence probability weight $(\theta/2)^{2w}(1 - \theta^2/4)^{n-w}$ at leading order. There are $C(n,w)$ such sets; a fraction $P(w)$ lie in degenerate classes where the minimal-weight decoder can err; conditioned on degeneracy, the failure rate is $\mathrm{fail}(w)$. By Theorem 9 the layers $w < w_0$ have $P(w) = 0$; the sum starts at $w_0$. ∎

For $d$ odd, the layer $w_0 = (d+1)/2$ is degenerate. At the $|0_L\rangle$ encoding the loss of a degenerate class is governed by the *type* of its residual logical operator: a residual containing an $X$ component flips the state (loss); a pure $Z$ logical residual acts as $\pm 1$ on $|0_L\rangle$ (lossless). For the PG-complete family ($d = 3$) the types $XX, XY, YX, YY$ ($4/9$ of the layer) leave an $X$-component logical residual (the collinear operators $X_aX_bX_c$ and $Y_aY_bY_c$; $XX$ via the cross-layer partner $X_c$ at weight $d - w_0 = 1$), $XZ, ZX$ ($2/9$) recover perfectly, and $YZ, ZY, ZZ$ ($3/9$) leave a pure $Z$ logical operator: total $\mathrm{fail}(2) = 4/9$. For $d$ even, $w_0 = d/2$ and all partners are same-layer; within a class of size $v$ the decoder errs with probability $(v-1)/v$, so $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$, the average over classes. The class sizes themselves are closed: see Theorem 18.

### 5.2 Unified scaling law

**Theorem 16 (Unified scaling law — main theorem).** Let $\mathcal{C} = [[n,k,d]]$ be a geometrically complete CSS code. Under independent coherent noise with per-qubit bound $\theta$, the loss of the optimal decoder is

$$\mathrm{loss}(\theta) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta^{2w_0} \;+\; O\!\left(\theta^{2w_0+2}\right), \qquad w_0 = \lceil d/2\rceil,$$

with $C(n,w_0)$ the binomial coefficient, $P(w_0)$ the degeneracy proportion (Prop. 13 for AG codes; $P(2) = 1$ for PG codes) and $\mathrm{fail}(w_0)$ the parity-dependent failure rate of Theorem 17 below ($\mathrm{fail}(2) = 4/9$ for PG codes at the $|0_L\rangle$ encoding). Equivalently, $\mathrm{loss}(\theta) = c_d\,\theta^{2w_0} + o(\theta^{2w_0})$ with

$$c_d = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}.$$

*Proof.* Theorems 14 and 15: layers below $w_0$ vanish; the leading term is the $w = w_0$ branch of the expansion with $(1 - \theta^2/4)^{n-w_0} = 1 + O(\theta^2)$. ∎

**Theorem 17 (Parity theorem for the failure rate).** In the setting of Theorem 16:
(i) if $d$ is odd, the leading layer is degenerate, and at the $|0_L\rangle$ encoding the failure rate is the fraction of weight-$w_0$ errors whose residual logical operator contains an $X$ component (a pure $Z$ logical residual acts as $\pm 1$ on $|0_L\rangle$ and is lossless). For the PG-complete family ($d = 3$, $w_0 = 2$) the types $XX, XY, YX, YY$ ($4/9$ of the layer) leave an $X$-component logical residual (weight-3 collinear), the types $XZ, ZX$ ($2/9$) recover perfectly, and $YZ, ZY, ZZ$ ($3/9$) leave a pure $Z$ logical operator: $\mathrm{fail}(2) = 4/9$;
(ii) if $d$ is even, $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$, where $v$ runs over the degenerate class sizes at weight $w_0$ and $\langle \cdot \rangle$ is the class-size-weighted average.

*Proof.* (i) Under CSS split decoding the residual of a weight-$w_0$ error $\chi_A = X_x Z_z$ is $\chi_A R$ with $R = X_a Z_b$, where $a$ is the unique weight-$\le 1$ solution of $H a = H x$ and $b$ the unique weight-$\le 1$ solution of $H b = H z$ (for the PG-complete family every nonzero syndrome is a column, so a weight-1 solution always exists). If the residual is the identity the recovery is perfect; if it is a pure $Z$ logical operator it acts as $\pm 1$ on $|0_L\rangle$ (lossless); if it contains an $X$ component the state is flipped to the orthogonal logical state (loss). For the PG-complete family ($d = 3$): $X_aX_b$ (syndrome $(0, \mathrm{col}_a \oplus \mathrm{col}_b)$) leaves $X_aX_bX_c$; $X_aY_b$ and $Y_aX_b$ leave the same $X$-collinear residual; $Y_aY_b$ leaves $Y_aY_bY_c = X_aX_bX_c\,Z_aZ_bZ_c$; each contains an $X$ component: loss. $X_aZ_b$ and $Z_aX_b$ are recovered exactly. $Y_aZ_b$, $Z_aY_b$, $Z_aZ_b$ leave the pure $Z$ collinear operator $Z_aZ_bZ_c$: lossless. Hence $\mathrm{fail}(2) = 4/9$. (ii) All partners of a weight-$w_0$ error have weight $w_0$ (any lower weight would contradict uniqueness); the decoder chooses uniformly among the $v$ class members; exactly one is correct. ∎

For the affine-complete families the average $\langle 1/v \rangle$ is computable from the class-size closed form:

**Theorem 18 (Class-size closed form).** For $CSS(RM(r,m))$, let $A$ be a $2^r$-subset of $AG(m,2)$ with affine span of dimension $s$ ($0 \le s \le r+1$). The size of the syndrome class of $\chi_A$ at weight $2^r$ is

$$v(A) = 1 + \left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2,$$

the Gaussian binomial coefficient counting $(r+1-s)$-dimensional subspaces of the $(m-s)$-dimensional quotient $AG(m,2)/\mathrm{span}(A)$; the $+1$ counts $\chi_A$ itself.

*Proof sketch.* By Theorem 11, partners of $\chi_A$ are the complements $P \setminus A$ over all $(r+1)$-flats $P \supset A$. Flats containing $A$ correspond bijectively to flats of the quotient $AG(m,2)/\mathrm{span}(A)$ of dimension $(r+1-s)$; their number is the Gaussian binomial $\left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2$. ∎

*Instances.* $r = 1$ ($d = 4$): any 2-subset has span $s = 1$, giving $v = 1 + \left[\begin{smallmatrix}m-1\\ 1\end{smallmatrix}\right]_2 = 2^{m-1}$: classes of size $2^{m-1}$ (e.g. $v = 16$ for $[[32,20,4]]$, matching the "465 pairs $= 31\times 15$" enumeration; $v = 8$ for the minimal member $[[16,6,4]]$ with $m = 4$). For $[[16,6,4]]$ the leading layer is fully degenerate with uniform class size 8, and Theorem 16 gives the closed form

$$\mathrm{loss}(\theta) = C(16,2)\cdot\tfrac{7}{8}\cdot 2^{-4}\,\theta^4 + O(\theta^6) = \tfrac{105}{16}\,\theta^4 + O(\theta^6),$$

i.e. a slope-4 loss with closed-form coefficient $105/16 \approx 6.56$ — the smallest-scale instance of the discriminator of Section 8. $r = 2$ ($d = 8$): generic 4-subsets have $s = 3$, $v = 2$ (complement pairs — the 313,131 classes of $[[64,20,8]]$); coplanar 4-subsets have $s = 2$, $v = 2^{m-2}$ — the bimodal class structure $2$ / $2^{m-2}$. Consequently $\mathrm{fail}(4) = 1 - \langle 1/v\rangle = 0.507172131$ for $[[64,20,8]]$ (full enumeration: 322,245 of 635,376 weight-4 errors fail), matching the measured 50.7%.

### 5.3 Next-to-leading order: the $\theta^{d+2}$ term

The layer $w_0 + 1$ produces the first subleading order. Its degeneracy is *cross-layer* with partners at weight $w_0 - 1$:

**Proposition 19 (Weight-$(2^r+1)$ degeneracy).** For $CSS(RM(r,m))$, the proportion of weight-$(2^r+1)$ errors with a partner at weight $2^r - 1$ is

$$P'_r(m) = \frac{\mathrm{flats}(m,r{+}1)\,\binom{2^{r+1}}{2^r{+}1}}{\binom{2^m}{2^r{+}1}},$$

with values $P'_2(6) = 0.08197$, $P'_2(7) = 0.0400$, $P'_2(8) = 0.01976$, $P'_2(9) = 9.82\times10^{-3}$, $P'_2(10) = 4.90\times10^{-3}$; $P'_3(8) = 3.26\times10^{-6}$, $P'_3(9) = 1.95\times10^{-7}$.

*Proof sketch.* A partner $\chi_B$ of $\chi_{A'}$ ($|A'| = 2^r + 1$, $|B| = 2^r - 1$) requires $\chi_{A'} \oplus \chi_B \in C^{\perp}$ of weight $d$, i.e. the product is an $(r+1)$-flat indicator with $A' \sqcup B = P$. Since $|A'| = 2^r + 1$ exceeds the size of any $r$-flat, the span of $A'$ is automatically $r+1$; the count is the flat count times the choices of $A'$ inside $P$. ∎

**Theorem 20 ($\theta^{d+2}$ next-to-leading order).** For an affine-complete code of even distance $d = 2^{r+1}$,

$$\mathrm{loss}(\theta) = c_d\,\theta^{d} + C(n,2^r{+}1)\,P'_r(m)\,2^{-2(2^r+1)}\,\theta^{d+2} + o(\theta^{d+2}),$$

where $c_d$ is the coefficient of Theorem 16 and $P'_r(m)$ is given by Prop. 19.

*Proof sketch.* The weight-$(2^r+1)$ branch carries amplitude order $\theta^{2^r+1}$; on the degenerate fraction $P'_r(m)$ the minimal-weight decoder necessarily selects the weight-$(2^r - 1)$ partner (all lower weights are unique, and the partner class is the only match — the product with any weight-$\le 2^r$ error would have weight $d + 2 - 2|\cap|$ or $\ge 17$, absent from the $C^{\perp}$ weight spectrum, verified by 2000/2000 sampling for $[[256,70,16]]$). The residual is the flat indicator, a minimum-weight logical operator: certain failure, no $1/2$ factor. ∎

*Magnitudes.* For $r = 2$, $m = 6$: $P'_2(6) = 0.082$ vs. the leading per-error failure rate $\mathrm{fail}(4) = 0.507$ — the subleading term is visible; for $r = 3$, $m = 8$: $P'_3(8) = 3.3\times10^{-6}$ vs. $P_3(8)/2 \approx 5\times10^{-5}$ — essentially invisible. Large-distance codes are dominated ever more purely by $\theta^d$. The logical-$Z$ flip fraction at this order is $\kappa_r(m)$: the fraction of decoding failures whose residual minimum-weight logical operator $\chi_P$ anticommutes with the logical $Z$ observable $z_l$ — equivalently, the ratio of the logical-$Z$-flip loss to the decoding-failure loss. For the affine-complete family it is a closed form,

$$\kappa_r(m) = \frac{2^{(r+1)(m-r-1)}}{\left[\begin{smallmatrix}m\\ r+1\end{smallmatrix}\right]_2}.$$

Mechanism: the residual $\chi_P$ is the indicator of an $(r+1)$-flat $P$ (a minimum-weight vector of $C^\perp$), and the anticommutation phase is $\chi_P \cdot z_l = |P \cap z_l| \bmod 2$, where $z_l$ is supported on a fixed $(m-r-1)$-flat $W$ (complementary dimension). Writing $P = p + U$ with $\dim U = r+1$, we have $|P \cap z_l| \bmod 2 = [U \cap W = \{0\}]$: complementary subspaces intersect transversally in a single point (odd), non-complementary ones in $2^{\dim U \cap W}$ points (even). The direction $\mathrm{dir}(P) = U$ is uniform among the $(r+1)$-dimensional subspaces of $\mathbb{F}_2^m$, because the class structure of the leading layer depends only on the quotient geometry; the number of subspaces complementary to the fixed $W$ is $2^{(r+1)(m-r-1)}$ (complement-counting), and the total number of $(r+1)$-subspaces is the Gaussian binomial $\left[\begin{smallmatrix}m\\ r+1\end{smallmatrix}\right]_2$. Hence $\kappa$ is a code-intrinsic quantity: independent of the decoder's in-class selection rule and unchanged by coherent interference — e.g. $\kappa_1(4) = 0.4571$ reproduces the full state-vector simulation ratio $0.45$ of $[[16,6,4]]$, $\kappa_2(6) = 0.367025$ matches full enumeration of $[[64,20,8]]$, and the $m = 10$ values $0.3761, 0.3304, 0.3122, 0.3072$ ($r = 1,2,3,4$) are exactly those used in the experimental windows of Section 8. The flip fraction converts the decoding-failure coefficients of Theorem 16 into the experimentally measured logical-$Z$-flip coefficients.

### 5.4 Pauli-channel universality

The entire framework extends from coherent rotations to arbitrary independent per-qubit Pauli channels with no change to the failure rates:

**Theorem 21 (Pauli-channel universality).** Let the noise be an independent per-qubit Pauli channel with $X$-side error probability $\varepsilon$ (the probability that the error operator contains an $X$ or $Y$ component, i.e. flips the $X$-syndrome; $Z$ errors are invisible to the $X$-side). For a geometrically complete CSS code with minimal-weight decoding, the $X$-side decoding loss is

$$\mathrm{loss}(\varepsilon) = \sum_{w \ge w_0} C(n,w)\,\varepsilon^{w}(1-\varepsilon)^{n-w}\,\mathrm{fail}(w) = C(n,w_0)\,\varepsilon^{w_0}\,\mathrm{fail}(w_0) + C(n,w_0{+}1)\,\mathrm{fail}(w_0{+}1)\,\varepsilon^{w_0+1} + o(\varepsilon^{w_0+1}),$$

with $\mathrm{fail}(w)$ the *unconditional* weight-$w$ decoding failure rate — the product $P(w)\,\mathrm{fail}(w)$ of Theorem 15 — unchanged from the coherent case: the decoder is a deterministic function of syndrome and weight, and the channel is invisible to it. Indeed, the $X$-side action of $Y_i$ equals that of $X_i$ ($Y_i X_v = (-1)^{v_i} X_v Y_i$ flips the same $X$-syndrome bits), and $Z_i$ leaves the $X$-syndrome untouched.

*Proof.* The set of $X$-active errors $\mathcal{A} = \{i : e_i \in \{X_i, Y_i\}\}$ is independent per qubit with $P(|\mathcal{A}| = w) = C(n,w)\varepsilon^w(1-\varepsilon)^{n-w}$; conditioned on $\mathcal{A}$, the syndrome equals that of a pure $X$ injection, so the failure probability is $\mathrm{fail}(w)$; sum over $w$. ∎

**Channel constants.** The same formula covers all standard channels: coherent $\theta$-tilts have $\varepsilon = \sin^2(\theta/2)$ (Theorem 16 is the special case); depolarizing noise of rate $p$ has $\varepsilon = 2p/3$; phase damping (after Pauli twirl) has $\varepsilon = 0$ (pure $Z$); amplitude damping (after Pauli twirl) has $\varepsilon = \gamma/2$. *Boundary:* untwirled coherent non-Pauli processes (e.g. the raw amplitude-damping Kraus operator $K_1 = \sqrt{\gamma}|0\rangle\langle 1|$) respond probabilistically ($\pm 1$ with equal halves) rather than by deterministic syndrome flips, and fall outside the theorem; the standard Pauli-twirl experimental protocol brings them back inside.

*Verification* ($[[64,20,8]]$): (i) weight-4/5 layers with $X$/$Y$ mixtures (200,000 samples, equal halves) give failure rates exactly equal to pure-$X$ injection sample by sample; (ii) full enumeration gives $\mathrm{fail}(4) = 0.507172131$ (322,245/635,376) and $\mathrm{fail}(5) = 0.846994536$ (6,457,920/7,624,512); (iii) full depolarizing $p = 0.02$ (1,000,000 samples) gives measured loss $0.005944 \pm 0.000077$ vs. the closed form $\sum_{w\ge 4} C(64,w)(2p/3)^w(1-2p/3)^{64-w}\mathrm{fail}(w) = 0.005969$ (with $w \ge 6$ terms at $\mathrm{fail} \approx 0.85$ contributing $1.85\times10^{-4}$): agreement at $-0.33\sigma$.

### 5.5 Instantiation and verification

Table 3 lists the closed-form leading coefficients $c_d$ of Theorem 16 and Table 4 the corresponding numerical measurements (all this work). The formula column is evaluated with $\mathrm{fail}(w_0)$ from Theorem 17, $P(w_0)$ from Prop. 13 (AG) or $P(2) = 1$ (PG), and $w_0 = \lceil d/2\rceil$; the PG rows use the $|0_L\rangle$-encoding value $\mathrm{fail}(2) = 4/9$.

| Code              | $d$ | Leading order | Closed-form $c_d$                                      |
| ------------------------------ | ------ | ---------------- | ------------------------------------------------ |
| $[[7,1,3]]$       | 3   | $\theta^4$    | $\frac49 C(7,2)/144 = 0.0648$                          |
| $[[15,7,3]]$      | 3   | $\theta^4$    | $\frac49 C(15,2)/144 = 0.3241$                         |
| $[[32,20,4]]$     | 4   | $\theta^4$    | $\frac{15}{16} C(32,2)/16 = 29.06$                     |
| $[[64,20,8]]$     | 8   | $\theta^8$    | $0.5072\, C(64,4)/256 = 1.26\times10^{3}$              |
| $[[256,70,16]]$   | 16  | $\theta^{16}$ | $P_3(8)\cdot 0.5\, C(256,8)/2^{16} = 3.15\times10^{5}$ |
| $[[1024,1002,4]]$ | 4   | $\theta^4$    | $0.9980\, C(1024,2)/16 = 3.27\times10^{4}$             |
| $[[1024,912,8]]$  | 8   | $\theta^8$    | $0.5005\, C(1024,4)/256 = 8.90\times10^{7}$            |
| $[[1024,672,16]]$ | 16  | $\theta^{16}$ | $P_3(10)\,0.5\, C(1024,8)/2^{16} = 3.37\times10^{8}$   |
| $[[1024,252,32]]$ | 32  | $\theta^{32}$ | $P_4(10)\,0.5\, C(1024,16)/2^{32} = 2.45\times10^{8}$  |

Table 4. Numerical verification of the closed forms of Table 3; ✓ marks agreement within statistical error.

| Code              | $d$ | Numerical/experimental                                                           |
| -------------------------------- | ------- | ------------------------------------------------------------- |
| $[[7,1,3]]$       | 3   | slope 4.12; fit $c \approx 0.065$ ✓                                              |
| $[[15,7,3]]$      | 3   | slope 3.99 ✓; $420/945 = 4/9$ ✓; fit $c \approx 0.31$ ✓                          |
| $[[32,20,4]]$     | 4   | class size 16 (465 pairs $= 31\times15$) ✓                                       |
| $[[64,20,8]]$     | 8   | fail 48.5%/50.7%; slope 7.96 ✓                                                   |
| $[[256,70,16]]$   | 16  | $P_3(8) = 1.007\times10^{-4}$; measured $1.5\times10^{-4}$/ $1.2\times10^{-4}$ ✓ |
| $[[1024,1002,4]]$ | 4   | rep. count 512; directional syndrome 1023 ✓                                      |
| $[[1024,912,8]]$  | 8   | weight-4 full degeneracy; weight-5 cross-layer $0.004887$ ✓                      |
| $[[1024,672,16]]$ | 16  | weight-8 sampled $1.67\times10^{-6}$ ($0.9\sigma$) ✓                             |
| $[[1024,252,32]]$ | 32  | $m=6$ sampling 333 vs $310\pm18$ ($1.3\sigma$) ✓                                 |

(i) The $[[7,1,3]]$ and $[[15,7,3]]$ rows use the uniform-$\theta$ protocol of this work: independent averaging of the tilt angles inserts $\prod_{i\in A}\langle\theta_i^2\rangle/4^w = (\theta_{\max}^2/12)^w$ for the weight-$w$ branch, hence the denominator $12^{w_0} = 144$ for $w_0 = 2$; the remaining rows use the fixed-$\theta$ protocol of Theorem 16 with denominator $2^{2w_0}$.

The closed forms reproduce the measured slopes and failure rates across the entire family ladder $d = 3, 4, 8, 16, 32$ — nine codes, five distances, four orders of magnitude in $c_d$ — with all coefficients fixed by the closed forms.


## 6. Transversal operations on affine-complete codes

The gate set available to a code family is as important as its error-correction parameters. In this section we characterize the transversal operations of the affine-complete family $\mathrm{CSS}(H,H)$ with $2r < m-1$. Universal transversal gate sets are impossible in any finite-dimensional code (Eastin–Knill no-go theorem [18]), and the transversality structure of stabilizer codes is characterized in Ref. [19]; the family considered here saturates the Clifford part of the allowed set (Theorem 22). All statements are verified both symbolically and by state-vector simulation in Section 6.5.

### 6.1 Transversal Clifford subset

**Theorem 22 (Transversal Clifford subset).** For every affine-complete code $\mathrm{CSS}(H,H)$ with $2r < m-1$, the following gates are transversal:

(i) *Pauli gates.* $X_v$ and $Z_w$ for $v, w \in C$ are transversal stabilizers (single-qubit Paulis on the support); $X_v$ and $Z_w$ for $v, w \in C^\perp \setminus C$ implement the logical $X$ and $Z$ operators.

(ii) *CNOT.* The CNOT between corresponding physical qubits of two code blocks maps the code space to itself and implements the logical CNOT. This holds for all CSS codes by the standard argument: $X$ errors propagate from control to target, $Z$ errors from target to control, and the stabilizer structure $C_2 \subseteq C_1$ is preserved.

(iii) *Hadamard.* Since the $X$-stabilizer space and the $Z$-stabilizer space coincide (both equal $C$ by Definition 3.1), $H^{\otimes n}$ maps $X$-stabilizers to $Z$-stabilizers and implements the logical Hadamard.

*Proof.* (i) By Definition 3.1 the $X$- and $Z$-stabilizer spaces both equal $C$, so $X_v, Z_w$ are stabilizers for $v, w \in C$. The operator $X_v$ commutes with all $Z$-stabilizers $Z_w$ ($w \in C$) if and only if $v \cdot w = 0$ for every $w \in C$, i.e. $v \in C^\perp$; hence $X_v$ for $v \in C^\perp \setminus C$ is a non-trivial logical $X$ operator, and likewise $Z_w$ for $w \in C^\perp \setminus C$ implements logical $Z$. (ii) is the standard CSS property. (iii): $H^{\otimes n}$ conjugates $X_v \mapsto Z_v$; since the $X$- and $Z$-stabilizer spaces are identical, stabilizers map to stabilizers, and the logical operators transform accordingly. ∎

A useful closed form obtained in the program verification: the logical zero state satisfies

$$H^{\otimes n}|0_L\rangle = \frac{1}{\sqrt{|C^\perp|}} \sum_{y \in C^\perp} |y\rangle = |+_L\rangle,$$

which is exact to machine precision for $[[16,6,4]]$ (overlap $1.000000000000$).

### 6.2 Transversal phase gates

**Theorem 23 ($S^{\otimes n}$ phase characterization).** Let $S = \mathrm{diag}(1,i)$. For every affine-complete code with $2r < m-1$ and $m \ge 4$:

(i) $S^{\otimes n}$ preserves the code space. Indeed $S X_v S^\dagger = Y_v = X_v Z_v$, and $X_v, Z_v$ are stabilizers for $v \in C$ (self-orthogonality $v \cdot w = 0$ and even weight $|v|$), so $Y_v$ is a stabilizer.

(ii) The induced logical map is a *diagonal phase gate*: the logical zero state is preserved, $S^{\otimes n}|0_L\rangle = |0_L\rangle$, because all codewords of $C$ have weight $\equiv 0 \pmod 4$ (automatic for $r \le m-3$, which follows from $2r < m-1$ when $m \ge 4$).

(iii) A logical direction $a \in C^\perp \setminus C$ acquires the phase

$$\gamma_a = i^{|a|},$$

where $|a|$ is the Hamming weight. Consequently: directions with $|a| \equiv 0 \pmod 4$ are fixed; $|a| \equiv 2$ implements logical $Z$; $|a| \equiv 1$ implements logical $S$; $|a| \equiv 3$ implements $-i \cdot$ logical $S$.

*Proof.* (i) is the conjugation identity combined with the stabilizer closure argument. (ii): $S^{\otimes n}|x\rangle = i^{|x|}|x\rangle$ and $\langle 1_L^a | S^{\otimes n} | 0_L \rangle \propto \sum_{x \in C} i^{|x|} \langle x+a | x \rangle = 0$ for $a \neq 0$, so the induced map is diagonal. (iii): $\gamma_a = \langle 1_L^a | S^{\otimes n} | 1_L^a \rangle = \frac{1}{|C|} \sum_{x \in C} i^{|x+a|}$; using $|x+a| \equiv |x| + |a| - 2|x \cap a| \pmod 4$, $|x| \equiv 0 \pmod 4$ for $x \in C$, and $a \cdot x = |x \cap a| \equiv 0 \pmod 2$ for $a \in C^\perp$, we obtain $\gamma_a = i^{|a|}$. ∎

### 6.3 Fault-tolerant operation set and T-gate interface

**Corollary 24 (Fault-tolerant operation set).** The transversal operation set of the affine-complete family is

$$\{\text{transversal Pauli},\ \text{transversal CNOT},\ \text{transversal } H\} \;\cup\; \{\text{transversal phase gates } \mathrm{diag}(1, i^{|a|})\} \;\cup\; \{\text{logical measurement}\},$$

where logical $\bar Z$ is measured by $Z$-measurement on the support bits followed by classical parity, and logical $\bar X$ by transversal $H$ followed by $\bar Z$ measurement. The $T$ gate admits *no* transversal implementation (it lies outside the Clifford group); it is interfaced through standard magic-state distillation protocols (e.g., 15-to-1). Distillation requires only code distance $d \ge 5$; the affine-complete family has $d = 2^{r+1} \ge 8$ for $r \ge 2$, so it is a plug-and-play interface.

*Proof.* Direct compilation of Theorems 22–23; the distillation requirement is a standard literature result [13, 14, 20–22]. ∎

### 6.4 Error propagation and the decoding closure

**Proposition 25 (Bounded error propagation).** Under transversal gates, a single-qubit error propagates to at most two qubits (CNOT duplicates $X$ from control to target and $Z$ from target to control; $H$, $S$, and Pauli gates preserve the error count). There is *no diffusion*: the error count grows by at most a factor 2 per round, in contrast to non-transversal gates which can spread errors exponentially.

*Proof.* Direct tracking of Pauli operators through the Clifford circuit; the duplication rule for CNOT is the standard fault-tolerance statement. ∎

**Remark (closure with the decoding formalism).** Combining Proposition 25 with Theorem 21 (Pauli-channel universality), each round of error correction is independent: the probability that the error set has weight $\ge w_0$ is still controlled by the $\varepsilon^{w_0}$ scaling, so the decoding closed forms of Section 5 apply round by round. A complete fault-tolerance threshold analysis (including distillation resource accounting) is beyond the scope of this paper.

### 6.5 Program verification

State-vector simulation on $[[16,6,4]]$ and symbolic verification on $[[64,20,8]]$ confirm:

- **Transversal $H$**: $H^{\otimes 16}|0_L\rangle = |+_L\rangle$ exactly ($|\langle +_L | H^{\otimes 16} | 0_L \rangle| = 1.000000000000$; analytic form $H^{\otimes n}|0_L\rangle = \frac{1}{\sqrt{|C^\perp|}} \sum_{y \in C^\perp} |y\rangle$).
- **Transversal $S$**: $\alpha = \langle 0_L | S^{\otimes 16} | 0_L \rangle = 1.000000$ (all codewords of $\mathrm{RM}(1,4)$ have weight $\equiv 0 \pmod 4$); the six monomial logical directions ($|a| = 4$) give $\gamma = 1$, and the composite direction $x_1 x_2 + x_3 x_4$ ($|a| = 6$) gives $\gamma = -1$ — all matching $i^{|a|}$ exactly.
- **$[[64,20,8]]$**: 484 self-orthogonality pairs with zero violations; all 22 basis vectors and 2000 random combinations have weight $\equiv 0 \pmod 4$; $Y_v$ commutes with all stabilizer generators — the legality of transversal $H$ and $S$ is directly verified.

## 7. Relation to existing results

This section situates the present work against the relevant literature. We emphasize that our contribution is *not* a new family of codes — the Reed–Muller CSS construction is classical — but a new level of analysis: exact, closed-form failure-rate scaling for a geometrically complete family, together with an enumeration-free verification method and an experimental discriminator.

### 7.1 Stabilizer codes and the CSS construction

The stabilizer formalism [1, 8] and the Calderbank–Shor–Steane construction [2, 7, 23] provide the general framework in which all CSS codes live. Our Theorem 16 (unified scaling law) is a *quantitative refinement* of the standard distance-based heuristic that "a code of distance $d$ corrects errors of weight $< d/2$": we prove that the failure rate is dominated by weight $w_0 = \lceil d/2 \rceil$ errors and give the exact leading coefficient $C(n,w_0)P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}$, with the degeneracy structure resolved in closed form. The parity theorem (Theorem 17) refines the folklore that "odd-distance codes are worse": we show the precise mechanism — for odd $d$ the leading layer is degenerate and, at the $|0_L\rangle$ encoding, its failure rate is the fraction of errors whose residual logical operator contains an $X$ component, giving $\mathrm{fail}(2) = 4/9$ for the PG-complete family, while even-distance codes retain the fraction $\langle 1/v \rangle$ of recoverable classes throughout.

### 7.2 Reed–Muller codes in classical coding theory

The classical theory of Reed–Muller codes is mature: the duality theorem, weight distributions, and the minimum-weight characterization date to the 1970s [9–12]. Our use of the classical facts is standard, as is the quantum Reed–Muller construction itself [24] and its fault-tolerant use in code-conversion protocols [25]. What is new is the *quantum-side* closed form: the class-size formula $v(A) = 1 + [m-s; r+1-s]_2$ (Theorem 18) quantifies, in terms of Gaussian binomial coefficients, how many weight-$2^r$ errors share a syndrome — a quantity with no classical analogue, since classical decoding does not track the stabilizer equivalence. The inclusion-equivalence theorem (Theorem 11) gives a purely geometric characterization (containment in an $(r+1)$-flat) of degeneracy at the distance-critical layer.

### 7.3 Degenerate quantum codes

Degeneracy — multiple errors sharing a syndrome — is a distinctly quantum phenomenon, exploited since the early days of the field [16, 26]. Known exact analyses include the Shor 9-qubit code and Bacon–Shor codes, where partial degeneracy is understood case by case. Our contribution is a *systematic* treatment: the degeneracy hierarchy of Section 4.3 (zero degeneracy below $d/2$, inclusion equivalence at $d/2$, full-degeneracy boundary at $r \le 2$, closed-form proportion $P_r(m)$ above) applies to an infinite family with growing distance. The finding that full degeneracy is *impossible* for $d \ge 16$ (Theorem 12) is, to our knowledge, new and structurally restrictive: it shows that the "benign" fully-degenerate regime is confined to $d \in \{4, 8\}$ in this family.

### 7.4 Threshold theorems and quantum LDPC codes

Threshold theorems [3, 16] and the surface-code/toric-code analyses [15, 27, 28], constrained by the two-dimensional storage tradeoffs [32], establish asymptotic statements: below a threshold error rate, arbitrarily long computation is possible. Quantum LDPC codes [29–31] achieve constant-rate asymptotically good parameters. Both lines of work are *asymptotic*; they do not provide closed-form finite-size failure rates for specific code families. Our scaling law is complementary: for the RM-CSS family we give *exact* finite-size coefficients (Table 3), enabling direct experimental discrimination (Section 8) that asymptotic statements cannot provide. Conversely, our family has non-constant rate (approaching $1$ as $m$ grows for fixed $r$) and distance $d = 2^{r+1}$; it is not a contender for asymptotic good codes, but it is the *most precisely analyzable* family at the distances relevant to near-term experiments ($d = 4$–$32$).

### 7.5 Experimental context

The mainstream experimental route to logical qubits is the surface code [27], whose threshold behavior is well studied; real-time error correction with a small code was demonstrated early on [33]. Our discriminator protocol (Section 8) addresses a different question: given a physical platform with coherent (or incoherent) single-qubit noise of unknown strength profile — coherent errors are known to be substantially more damaging than their incoherent counterparts for surface codes [34] — can one *identify the noise class and the code's response* from logical failure rates alone? The four-order slope test $\theta^4/\theta^8/\theta^{16}/\theta^{32}$ across the 64–1121 qubit ladder provides a diagnostic that is orthogonal to surface-code benchmarking. The transversal Clifford subset of Section 6 is a further practical asset: the phase gate $\mathrm{diag}(1, i^{|a|})$ is implementable transversally in this family, which is not the case for generic CSS codes.

### 7.6 Positioning summary

| Aspect | This work | Standard analyses |
|---|---|---|
| Failure rate | Exact closed form, all orders | Asymptotic / Monte Carlo |
| Degeneracy | Closed-form class sizes | Case-by-case |
| Verification | Enumeration-free, $O(n^2)$ | Full enumeration (infeasible > 100 qubits) |
| Code family | RM-CSS, $d = 4$–$32$ | Surface / LDPC / concatenated |
| Experimental use | Slope discriminator $\theta^{2\lceil d/2 \rceil}$ | Threshold extrapolation |

## 8. Experimental discrimination of the four-order scaling law

The closed forms of Section 5 yield the predictions directly: the leading coefficient of the measured logical-$Z$-flip loss, $c_d = \kappa_r(m)\,C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}$ with $\kappa_r(m)$ the logical-$Z$ flip fraction of Sec. 5.3, is fixed entirely by the closed forms, and the integer exponent $d$ is fixed by the geometry of the logical classes. This section converts them into a falsifiable protocol on a 64–1121 qubit superconducting platform: measure the log–log slope of $\mathrm{loss}(\theta)$ for four tiers of the affine-complete family and test that the slopes equal $4, 8, 16, 32$ [35]. The design follows the closed-form framework of Sections 5 and 8; all numbers quoted below are closed-form values, not fits.

### 8.1 Discriminant objective and logic

**Objective.** In a single noise environment (one platform, one calibration), measure the loss function $\mathrm{loss}(\theta)$ of four AG-complete codes under coherent injection and test the geometric prediction

$$\mathrm{loss}(\theta) = c_d\,\theta^d + o(\theta^d), \qquad d \in \{4, 8, 16, 32\},$$

where $\theta$ is the angle of an identical single-qubit coherent rotation $R_x(\theta)$ applied to every qubit (pure-type injection about a fixed axis; the experimental loss is the logical-$Z$-flip rate of Sec. 5.3).

**Why the slope is a discriminant.** (a) Non-geometric heuristics (independent error models, typical-code behavior) cannot produce exact integer slopes with closed-form coefficients; (b) the tier windows on the $\theta$ axis are *ladder-separated* by the closed forms of $c_d$, and the ladder (including its gaps) cannot be obtained by post-fitting; (c) the intercepts $\ln c_d$ are fully predicted, and any deviation directly inverts to the experimental value of $\kappa\,\mathrm{fail}(w_0)$, which combined with the closed form of $\kappa$ (Sec. 5.3) yields $\mathrm{fail}(w_0)$ and hence an *indirect measurement of the class size* $v$ (Theorem 17: $\mathrm{fail}(w_0) = 1 - \sum_s P(s)/\bigl(v(s)\,P(w_0)\bigr)$).

**Smallest-scale test.** The same logic is testable at 16 qubits before engaging the 64–1121 qubit platform: the canonical member $[[16,6,4]]$ has slope 4 with the exact coefficient $105/16$ (Sec. 5.2), so its log–log intercept $\ln(105/16)$ is itself a closed-form prediction — a desktop check of the discriminator.

**Theoretical input** (closed forms for $m = 10$; $\ln c_d$ in the logical $Z$-flip version):

| Tier | Code | $d$ | $w_0$ | $\kappa_r(10)$ | $c_d$ (closed form $\times \kappa$) | $\ln c_d$ |
|---|---|---|---|---|---|---|
| $d{=}4$ | $[[1024,1002,4]]$ | 4 | 2 | 0.3761 | $0.9980\,C(1024,2)/16 \times 0.3761 = 1.23\times10^{4}$ | 9.417 |
| $d{=}8$ | $[[1024,912,8]]$ | 8 | 4 | 0.3304 | $0.5005\,C(1024,4)/256 \times 0.3304 = 2.94\times10^{7}$ | 17.197 |
| $d{=}16$ | $[[1024,672,16]]$ | 16 | 8 | 0.3122 | $1.514\times10^{-6}\cdot 0.5\,C(1024,8)/2^{16} \times 0.3122 = 1.05\times10^{8}$ | 18.470 |
| $d{=}32$ | $[[1024,252,32]]$ | 32 | 16 | 0.3072 | $3.383\times10^{-17}\cdot 0.5\,C(1024,16)/2^{32} \times 0.3072 = 7.53\times10^{7}$ | 18.137 |

The leading exponent is $2w_0 = d$ ($d$ even, same-layer degeneracy). All four codes share one platform, hence one noise environment — the discriminating power comes from the *relative* ladder, which is insensitive to platform-dependent calibration constants.

![Figure 2: scaling law](figures/fig2_scaling_law.png)

**Figure 2.** Parameter-free prediction of the logical-$Z$-flip loss (Sec. 8.1): $\mathrm{loss}(\theta_{\max}) = c_d\,\theta_{\max}^{d}$ with the closed-form coefficients $c_d = \kappa_r(10)\,C(1024,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}$ of the four 1024-qubit members. Solid segments mark the observable windows $10^{-3} \le \mathrm{loss} \le 0.5$ (Theorem 26); dashed extensions are the leading-order extrapolation outside the windows; dotted reference lines mark $\mathrm{loss} = 10^{-3}$ and $0.5$. Shaded bands are the two gaps $[0.107, 0.205]$ and $[0.302, 0.457]$, where the low tiers have already saturated while the high tiers still sit at baseline.

### 8.2 Platform–code matching (hard constraint)

AG-complete codes have $k = 2^m - 2\dim\mathrm{RM}(r,m)$; the constraint $k \ge 1$ fixes which tiers are measurable on which platform:

| Platform (qubits) | Measurable tiers | Instance codes | Comment |
|---|---|---|---|
| 64 | $d{=}4$, $d{=}8$ | $[[64,50,4]]$, $[[64,20,8]]$ | $m=6$; $[[64,20,8]]$ slope 7.96 verified by exact program |
| 127–133 | $d{=}4$, $d{=}8$ | $[[128,112,4]]$, $[[128,70,8]]$ | $m=7$; $d{=}16$ unmeasurable ($r=3$: $k = 128 - 2\cdot64 = 0$) |
| 256 | $d{=}16$ | $[[256,70,16]]$ | $m=8$ |
| 512 | $d{=}16$ | $[[512,252,16]]$ | $m=9$ |
| 1024–1121 | **all four tiers** | Table of §8.1 | same platform, same noise — the discriminant main site |

The main site is a 1121-qubit platform (1024 data qubits plus measurement, no ancillas; §8.4). The 64/256-qubit platforms serve as cross-checks (shorter codes, shallower circuits, lower baselines). The 1121-qubit scale is within reach of current superconducting processors, whose flagship demonstrations have now passed the surface-code threshold on comparable architectures [35–37].

### 8.3 Observable windows and $\theta$ scan

**Window definition.** The leading-order approximation $\mathrm{loss} = c_d\,\theta^d \in [10^{-3}, 0.5]$: below $10^{-3}$ more than $10^9$ shots are needed; above $0.5$ the leading order breaks down (sub-leading and saturation dominate).

**Theorem 26 (Window ladder).** On the 1024-qubit platform the four observable windows
$\mathcal{W}_d = \{\theta : 10^{-3} \le c_d\theta^d \le 0.5\}$ are

$$\mathcal{W}_4 = [0.017, 0.080], \qquad \mathcal{W}_8 = [0.049, 0.107], \qquad \mathcal{W}_{16} = [0.205, 0.302], \qquad \mathcal{W}_{32} = [0.457, 0.555],$$

with gaps $[0.107, 0.205]$ and $[0.302, 0.457]$ between tiers $8/16$ and $16/32$, and overlap $[0.049, 0.080]$ between tiers $4/8$.

*Proof.* Substitute the closed-form $c_d$ of §8.1 into $10^{-3} \le c_d\theta^d \le 0.5$ and solve for $\theta$; the ladder structure (windows separated by gaps, low tiers overlapping) follows from the closed-form coefficients, not from fitting. ∎

![Figure 3: windows](figures/fig3_windows.png)

**Figure 3.** The four observable windows $\mathcal{W}_d$ of Theorem 26 (solid bars): $\mathcal{W}_4 = [0.017, 0.080]$, $\mathcal{W}_8 = [0.049, 0.107]$, $\mathcal{W}_{16} = [0.205, 0.302]$, $\mathcal{W}_{32} = [0.457, 0.555]$, defined by $10^{-3} \le c_d\theta^d \le 0.5$. Gray bands are the gaps $[0.107, 0.205]$ and $[0.302, 0.457]$; the gold band is the overlap $[0.049, 0.080]$ of tiers 4 and 8, which provides an in-situ cross-check. Recommended five-point sampling inside each window is described in Sec. 8.3.

The ladder itself is a signature of the geometric prediction: the gaps are intervals where tiers $16/32$ still sit at baseline (below $10^{-3}$) while tiers $4/8$ have already saturated (above $0.5$) — a "double void" that cannot arise from a smooth fitted model. Recommended sampling points (with the sub-leading correction included) are five loss values per tier, e.g. for $d=4$: $\theta \in \{0.02, 0.03, 0.04, 0.05, 0.06\}$ giving $\mathrm{loss} \in [2\times10^{-3}, 1.6\times10^{-1}]$; the other tiers follow the same five-point design in their windows.

**Control of $\theta$.** Injection is a pure-type coherent rotation $R_x(\theta)$ about a fixed axis applied to every qubit with a single common angle. The common angle corresponds exactly to the branch amplitude $(\theta/2)^{2w}$ of the leading-order expansion (coefficient $2^{-2w_0}$), with no distribution-averaging factor. At the high end ($\theta \approx 0.5$, single-qubit rotations of order $30^\circ$) injection and noise are no longer separable — precisely the discriminating region: the geometric prediction demands exact $\theta^{32}$ scaling where a non-geometric model (e.g. independent bit-flip dominated $\theta^1$) would give slope 1–2.

### 8.4 Experimental protocol (brute-force measurement, single round)

The key difference from practical QEC: no non-destructive syndrome measurement and no rounds of error correction are needed. The protocol is a single round "prepare → inject → measure all qubits → classical reconstruction":

1. **Prepare $|0_L\rangle$**: Plotkin recursive encoding circuit for $\mathrm{RM}(r,m)$ ($O(nr)$ CNOTs, depth of order hundreds; $\sim 10^4$ CNOTs for $r=4$). The preparation fidelity need not exceed the injection region — the baseline is absorbed by a three-parameter fit (§8.5).
2. **Inject**: $R_x(\theta)$ on every qubit, common angle, fixed axis.
3. **Brute-force measurement (replica method)**: each shot splits into two replicas — replica A measured directly in the $Z$ basis; replica B measured after a per-qubit $H$ (equivalent to the $X$ basis). From the two bit strings one classically reconstructs (i) all $2\dim\mathrm{RM}(r,m)$ stabilizer values ($Z$-type from replica A, $X$-type from replica B); (ii) the logical $Z$ value (replica A). **No ancillas, no non-destructive measurements — the 1121-qubit platform needs only 1024 data qubits.**
4. **Decode (classical side)**: syndrome ($772$ bits for $r=4$) → minimum-weight decoding. Implemented by RPA (Reed–Muller recursive projection aggregation) or the geometric decoder (flat enumeration for error weights $\le w_0+1$). The pre-experiment must certify decoder equivalence at weights $\le w_0+1$ (§8.6).
5. **Estimate loss**: $\mathrm{loss}(\theta) = P(\text{decoded logical value} \neq 0_L)$ — the logical error rate (decoding failures plus preparation baseline).
6. **Statistics**: $N = 2\times10^5$ shots per point ($10^6$ for the low-$d{=}32$ endpoints); relative loss error $\sigma_{\mathrm{rel}} \approx \sqrt{1-\mathrm{loss}}/(\sqrt{N}\sqrt{\mathrm{loss}})$: $3.2\%$ at $\mathrm{loss} = 5\times10^{-3}$, $1.0\%$ at $0.05$, $0.5\%$ at $0.2$.

### 8.5 Statistical discrimination criteria

**Model.** Each tier is fitted independently with three parameters

$$\mathrm{loss}(\theta) = b + c\,\theta^d,$$

where $b$ is the baseline (encoding circuit and measurement errors) — not subtracted, but jointly estimated, the most robust treatment of the baseline; $d$ is estimated by nonlinear least squares (with a weighted linear regression $\ln\mathrm{loss} = d\ln\theta + \ln c$ on points with $\mathrm{loss} \gg b$ as cross-check).

**Theorem 27 (Discrimination power).** With $\sigma_{\mathrm{rel}} = 5\%$ and five points per tier, the slope estimate $\hat d$ of the fit $\mathrm{loss}(\theta) = b + c\theta^d$ has standard deviation

$$\sigma_d = 0.028,\ 0.062,\ 0.098,\ 0.198 \qquad (d = 4, 8, 16, 32),$$

and $\sigma_d = 0.12$ for tier 32 at $N = 10^6$. The separation between adjacent tiers is $\Delta d = 4$; the discrimination margin is $20$–$143\sigma$ across tiers.

*Proof.* With five points spread over the $\ln$-span $\Delta\ln\theta$ of the window, the slope error is $\sigma_d \approx \sigma_{\mathrm{rel}}/\sqrt{N_{\mathrm{eff}}}\,\Delta\ln\theta$ scaling (weighted regression variance), evaluated with the window spans of Theorem 26 ($\Delta\ln\theta = 1.099, 0.511, 0.323, 0.160$ for $d = 4, 8, 16, 32$). The margins follow from $\Delta d = 4$: $143\sigma$, $65\sigma$, $41\sigma$, $20\sigma$ ($33\sigma$ at $N = 10^6$). ∎

**Four tests.**

1. **Slope test** (main criterion): $|\hat d - d| \le 2\sigma$ on all four tiers independently. Since adjacent tiers differ by $\ge 4$, the resolution of the slopes $4/8/16/32$ is statistically overwhelming even at the worst tier ($16\sigma$ for $d{=}32$).
2. **Intercept test** (closed-form): $\ln \hat c_d$ agrees with the closed forms $\ln c_d = 9.417/17.197/18.470/18.137$ within $3\sigma$. Any deviation inverts to the experimental value of $\kappa\,\mathrm{fail}(w_0)$; combined with the closed form of $\kappa$ this yields $\mathrm{fail}(w_0)$ and hence an *experimental measurement of the class size* $v$ — a direct test of the geometric class-size closed form $v(A) = 1 + \left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2$.
3. **Gap test**: supplementary points at $\theta \in \{0.12, 0.15, 0.18\}$ must show (i) no $\theta^d$-type growth for tiers $16/32$ beyond $3\sigma$ of the baseline; (ii) a saturated plateau for tiers $4/8$. This independently confirms the window ladder.
4. **Control test**: same protocol with random Pauli injection (incoherent, depolarizing rate $p$ equivalent to $\theta$). The incoherent loss scales as $\sim p^2$ (Theorem 21: every independent per-qubit Pauli channel has the same failure structure with channel-dependent single-qubit error probability $\varepsilon$), so the slope should be $\approx 2 \neq d$ — excluding the confound that "the platform hardware noise itself scales as $\theta^d$".

### 8.6 Systematic errors and countermeasures

1. **Baseline $b$**: the 1024-qubit encoding circuit ($\sim 10^4$ CNOTs at $\sim 10^{-3}$ gate error) gives a baseline of order $10^{-2}$–$10^{-1}$. Countermeasures: three-parameter fit absorption plus error mitigation (randomized compiling, measurement calibration); if $b > 2\times10^{-3}$, drop the lowest point of tiers $4/32$ (where $\mathrm{loss} \sim 10^{-3}$) — e.g. $d{=}4$ uses $\{0.03, 0.04, 0.05, 0.06\}$ ($\Delta\ln = 0.69$, $\sigma_d \approx 0.05$) and $d{=}32$ uses $\{0.48, 0.50, 0.52, 0.54\}$ at $N = 10^6$ ($\sigma_d \approx 0.2$); the margins remain $> 10\sigma$.
2. **Decoder equivalence** (pre-experiment, classical side): RPA/geometric decoders must reproduce minimum-weight decoding at weights $\le w_0+1$ (branch-level exact program comparison); otherwise the closed-form coefficients are invalidated (the decoder is not the theoretical decoder).
3. **$R_x(\theta)$ calibration**: microwave pulse-area calibration; pulse errors varying with $\theta$ need separate randomized benchmarking (RB) calibration [38, 39]. The global pulse (common angle) removes per-qubit axis/angle control, and axis drift is suppressed by global uniformization.
4. **Crosstalk**: CNOT crosstalk shifts the effective injection angle — corrected by XEB/crosstalk calibration of the $\theta$ grid; residual effects enter $\sigma_{\mathrm{rel}}$.
5. **Finite length / sub-leading order**: at the window top ($\mathrm{loss} > 0.3$) the sub-leading contribution $\sim \theta^{d+2}$ has closed-form coefficient $c' = \kappa_r(m)\,C(n,w_0{+}1)\,P'(w_0{+}1)\,2^{-2(w_0+1)}$ (Theorem 20), with the residual $\chi_P$ remaining an $X$-logical and the flip ratio equal to the leading one. **Sub-leading discriminant**: the ratio $\rho = c'/c_d$ is a closed-form ratio ($\rho = 85.3$ for $d{=}4$; $\approx 0.45$–$0.50$ for the other tiers). The data are corrected *before* fitting: $\hat{L} \mapsto \hat{L}/(1+\rho\theta^2)$ (linear version $\ln\hat{L} - \ln(1+\rho\theta^2) = \ln c + d\ln\theta$); the residual slope after correction must vanish (otherwise the sub-leading closed form is falsified). **$c'$ must not be fitted as a free parameter** — with five points and four parameters the fit is underdetermined, and without the correction the $d{=}4$ slope is biased by $+0.31 \approx 15\sigma$ and the $d{=}32$ slope by $+1.7\sigma$, destroying the discrimination (power analysis).

### 8.7 Time budget

At $N$ shots per point and a shot period of $\sim 5$ ms ($\sim 10^4$ CNOTs + injection + measurement), $N = 2\times10^5$ costs $\sim 1000$ s per point:

| Item | Points | $N$ | Time |
|---|---|---|---|
| Main scan (17 points; $d{=}32$ low endpoints at $10^6$) | 17 | $2\times10^5$–$10^6$ | $\sim 5.2$ h |
| Gap region (3 points) | 3 | $2\times10^5$ | $\sim 0.8$ h |
| Control (random Pauli, 4 points) | 4 | $2\times10^5$ | $\sim 1.1$ h |
| Calibration (RB/XEB/baseline) | — | — | $\sim 2$ h |
| **Total** | | | **$\sim 9$–10 h (one platform-day)** |

On the 64/256-qubit backup platforms the circuits are shallower (shot period $\sim 0.5$–1 ms) and the budget halves.

### 8.8 Falsification conditions

1. Any tier with $|\hat d - d| > 2\sigma$ ($\sigma_d$ design values 0.02–0.25) → the loss scaling law fails (the core geometric prediction is refuted).
2. Slopes pass but intercepts deviate from the closed forms by $> 3\sigma$ → the coefficient structure fails; requires correcting $\kappa\,\mathrm{fail}(w_0)/P(w_0)$ (an experimental counterexample to the $\kappa$ lemma or the class-size closed form).
3. $\theta^d$-type growth of tiers $16/32$ in the gap region beyond $3\sigma$, or no saturated plateau for tiers $4/8$ → the window ladder fails.
4. The random-Pauli control gives the same slope as coherent injection ($\approx d$ for both, or both $= 2$) → the platform is decoherence-dominated; the discrimination is *not feasible* (not a theory failure — change platform or shorten circuits).
5. The sub-leading coefficient deviates from the Theorem 20 closed form by $> 3\sigma$ → the sub-leading structure is modified.

### 8.9 Scientific payoff and open problems

**Payoff if passed.** (i) Experimental confirmation of the four slopes $4/8/16/32 \pm 0.3$: under coherent noise the loss of AG-complete codes is fully determined by geometry (logical classes + flat counting), with all coefficients fixed by the closed forms; (ii) the intercepts give $\kappa\,\mathrm{fail}(w_0)$, hence $\mathrm{fail}(w_0)$ and the class size $v$ — an indirect experimental verification of the class-size closed form; (iii) the window ladder (including the gaps) is a unique, non-fittable signature of the geometric prediction; (iv) an experimental test of the sub-leading $\theta^{d+2}$ coefficient.

**Directions if it fails.** Incoherent admixture (experimental entry to the coherent/incoherent separation — the $\theta^2$ vs $\theta^d$ scaling split); finite-length effects ($n = 1024$ sub-leading corrections); decoder deviations from minimum-weight decoding; experimental deviations in the flat-counting assumption (degeneracy fraction $P(w_0)$); deviations of the $\kappa$ closed form.

**Open problems.**
1. Quantitative protocol for coherent/incoherent separation: the injection parameters of the random-Pauli control (mapping between depolarizing rate $p$ and $\theta$) need a closed form.
2. A rigorous proof that the RPA decoder matches minimum-weight decoding on the degenerate layer (weight $w_0$); currently a pre-experiment certification.
3. Effect of finite measurement errors of the brute-force protocol (readout fidelity $99\%$ → baseline $\sim 10^{-2}$) on the $d{=}32$ window: is readout error correction needed?
4. Statistical power of the gap test: optimal $\theta$ placement and shot allocation in the gap region.

## 9. Conclusion and outlook

### 9.1 Summary of results

We have developed a verification framework and exact closed-form theory for the affine-complete family of CSS codes $\mathrm{CSS}(H,H)$ with $H$ the generator matrix of $\mathrm{RM}(r,m)$ (stabilizer space $C = \mathrm{RM}(r,m)$, logical space $C^\perp = \mathrm{RM}(m-r-1,m)$, self-orthogonality $2r < m-1$). The main results:

1. **Verification without enumeration** (Theorem 4): the minimum-weight structure, zero-loss window, and class-size degeneracy of codes up to $n = 1024$ are certified by $M = n \cdot s$ operations (linear in the stabilizer dimension), replacing combinatorial enumeration; the method is classical-exact (integer arithmetic, branch-level checks against full enumeration on small codes).
2. **Parameter closed forms** (Theorems 1–3): $k = 2^m - 2\dim\mathrm{RM}(r,m)$, $d = 2^{r+1}$, validity iff $2r < m-1$; the $k \ge 1$ boundary $r \le \lfloor(m-2)/2\rfloor$ makes the family a four-order ladder $d = 4, 8, 16, 32$ on 1024 qubits.
3. **Zero-loss and degeneracy structure** (Theorems 5–7, 13–15): errors of weight $< d/2$ have unique syndromes (perfect recovery); the family is fully degenerate exactly for $d \in \{4, 8\}$; the full-degeneracy boundary is exact and small-code verified.
4. **Closed-form failure rates** (Theorems 16–21): class size $v(A) = 1 + \left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2$ (Gaussian binomial, $s$ the affine-hull dimension); failure rate $\mathrm{fail}(w) = 1 - \langle 1/v \rangle$; the unified scaling law $\mathrm{loss}(\theta) = c_d\,\theta^d$ with closed-form coefficient $c_d = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}$ (Theorem 16), converted to the measured logical-$Z$-flip rate by the closed-form flip fraction $\kappa_r(m)$ of Sec. 5.3 — verified instance by instance against exact programs ($[[64,20,8]]$ slope 7.96, $[[256,70,16]]$ full recovery, 1024-qubit closed forms).
5. **Transversal structure** (Theorems 22–23, Corollary 24, Proposition 25): transversal Clifford subset $\{P, \mathrm{CNOT}, H\}$; transversal phase gates $\gamma_a = i^{|a|}$ on logical directions $a \in C^\perp \setminus C$; a fault-tolerant operation set with the $T$-gate distillation interface (distance $d \ge 8$ satisfies the $d \ge 5$ requirement); bounded error propagation closes the loop with the per-round decoding analysis.
6. **Experimental discrimination** (Theorems 26–27): the four-tier window ladder on a 1121-qubit platform, slope discrimination at 20–143$\sigma$, one platform-day, and five falsification conditions.

### 9.2 Significance

**Scaling–geometry correspondence.** The full coefficient structure of the coherent-noise loss expansion (leading and sub-leading order) is determined by the flat-counting closed forms of $AG(m,2)$ / $PG(m-1,2)$: the coherent-noise behavior of a quantum error-correcting code *is* the geometry of its logical classes. The class-size closed form unifies the three previously separate instances — the 465 pairs of the $[[32,20,4]]$ code, the 313,131 classes of the weight-4 layer, the 512 representatives of the $r=1$ layer — as one formula.

**Parameter-free prediction and falsifiability.** Every coefficient entering the scaling law is closed-form; the experiment of Section 8 is a sharp test with five explicit falsification conditions. This is the qualitative difference between the present theory and post-fitted models of code performance.

**Exact analysis of degenerate codes.** Degeneracy is the reason quantum codes can exceed the classical Hamming bound, yet exact degenerate analyses are rare. The present family provides the first exact, closed-form treatment of a fully degenerate regime ($d \in \{4,8\}$) with a proven boundary, and the degenerate decoding failure rate is expressed through the Gaussian-binomial class sizes — a structure inaccessible to randomized-code typicality arguments.

**Engineering corrections.** The $r=1$ ($d=4$) tier loses about twice as much as the previously estimated coefficient (large $m$): threshold estimates $(cN)^{-1/d}$ are corrected accordingly; tiers $d=8/16$ are unaffected (dominant class size 2).

### 9.3 Open problems

1. **PG sub-leading order**: the $\theta^6$ coefficient of the PG-complete family ($d=3$): the cross-layer degeneracy structure of weight-3 with weight-2/1 layers.
2. **Degenerate classes of $r=3$**: the precise weight of the $P(s=3)$ correction in the failure-rate formula (of order $10^{-8}$ at $m=10$, negligible but not separately verified).
3. **Non-CSS perfect codes**: the mechanism of the $\theta^4$ scaling of the $[[5,1,3]]$ code (measured $c \approx 0.06$ vs branch-level $0.069$, same order) and its relation to the geometric-completeness framework.
4. **Complete statistics of class sizes**: the fraction of degenerate classes with $v = 2^{m-3}$ for $r=3$ — $\mathrm{flats}(m,3)/C(2^m,8) \approx 2.8\times10^{-11}$ at $m=10$, unreachable by sampling; the closed form is the final value.
5. **Coherent/incoherent separation**: a quantitative protocol mapping the random-Pauli control parameters ($p$ vs $\theta$).
6. **Decoder certification**: a rigorous proof of RPA/minimum-weight equivalence on the degenerate layer.

**Acknowledgments.** The author thanks the maintainers of the exact branch-level verification programs whose certificates underpin the numerical results of Sections 3.5 and 5.5, and the developers of the open-source numerical tools used in the simulations.

**Code availability.** The verification programs underlying the numerical results (exact enumeration of decoding-failure coefficients, state-vector simulations of coherent and incoherent noise, and transversal-gate checks) are available at https://doi.org/10.5281/zenodo.21843943.

## References

[1] P. W. Shor, "Scheme for reducing decoherence in quantum computer memory," Phys. Rev. A **52**, R2493 (1995).
[2] A. M. Steane, "Error correcting codes in quantum theory," Phys. Rev. Lett. **77**, 793 (1996).
[3] P. Aliferis, D. Gottesman, and J. Preskill, "Quantum accuracy threshold for concatenated distance-3 codes," Quantum Inf. Comput. **6**, 97 (2006).
[4] D. Aharonov and M. Ben-Or, "Fault-tolerant quantum computation with constant error rate," SIAM J. Comput. **38**, 1207 (2008).
[5] J. J. Wallman and J. Emerson, "Noise tailoring for scalable quantum computation via randomized compiling," Phys. Rev. A **94**, 052325 (2016).
[6] M. R. Geller and Z. Zhou, "Efficient error models for fault-tolerant architectures and the Pauli twirling approximation," Phys. Rev. A **88**, 012314 (2013).
[7] A. R. Calderbank and P. W. Shor, "Good quantum error-correcting codes exist," Phys. Rev. A **54**, 1098 (1996).
[8] D. Gottesman, "Stabilizer codes and quantum error correction," Phys. Rev. A **54**, 1862 (1997).
[9] F. J. MacWilliams and N. J. A. Sloane, *The Theory of Error-Correcting Codes* (North-Holland, 1977).
[10] I. S. Reed, "A class of multiple-error-correcting codes and the decoding scheme," IRE Trans. Inf. Theory **4**, 38 (1954).
[11] D. E. Muller, "Application of Boolean algebra to switching circuit design and to error detection," IRE Trans. Electron. Comput. **3**, 6 (1954).
[12] T. Kasami and N. Tokura, "On the weight structure of Reed–Muller codes," IEEE Trans. Inf. Theory **16**, 752 (1970).
[13] S. Bravyi and A. Kitaev, "Universal quantum computation with ideal Clifford gates and noisy ancillas," Phys. Rev. A **71**, 022316 (2005).
[14] E. T. Campbell, B. M. Terhal, and C. Vuillot, "Roads towards fault-tolerant universal quantum computation," Nature **549**, 172 (2017).
[15] E. Dennis, A. Kitaev, A. Landahl, and J. Preskill, "Topological quantum memory," J. Math. Phys. **43**, 4452 (2002).
[16] E. Knill, R. Laflamme, and W. H. Zurek, "Resilient quantum computation," Science **279**, 342 (1998).
[17] J. Roffe, "Quantum error correction: an introductory guide," Contemp. Phys. **60**, 226 (2019).
[18] B. Eastin and E. Knill, "Restrictions on transversal encoded quantum gate sets," Phys. Rev. Lett. **102**, 110502 (2009).
[19] B. Zeng, A. Cross, and I. L. Chuang, "Transversality versus universality for additive quantum codes," IEEE Trans. Inf. Theory **57**, 6272 (2011).
[20] S. Bravyi and J. Haah, "Magic state distillation with low overhead," Phys. Rev. A **86**, 052329 (2012).
[21] E. T. Campbell and M. Howard, "Unified framework for magic state distillation," Phys. Rev. Lett. **118**, 060501 (2017).
[22] J. Haah, M. B. Hastings, D. Poulin, and B. Wecker, "Magic state distillation with low space overhead and optimal asymptotic input count," Quantum **1**, 31 (2017).
[23] A. R. Calderbank, E. M. Rains, P. W. Shor, and N. J. A. Sloane, "Quantum error correction via codes over GF(4)," IEEE Trans. Inf. Theory **44**, 1369 (1998).
[24] A. M. Steane, "Quantum Reed–Muller codes," IEEE Trans. Inf. Theory **45**, 1701 (1999).
[25] J. T. Anderson, G. Duclos-Cianci, and D. Poulin, "Fault-tolerant conversion between the Steane and Reed–Muller quantum codes," Phys. Rev. Lett. **113**, 080501 (2014).
[26] E. Knill and R. Laflamme, "Theory of quantum error-correcting codes," Phys. Rev. A **55**, 900 (1997).
[27] A. G. Fowler, M. Mariantoni, J. M. Martinis, and A. N. Cleland, "Surface codes: Towards practical large-scale quantum computation," Phys. Rev. A **86**, 032324 (2012).
[28] R. Raussendorf and J. Harrington, "Fault-tolerant quantum computation with high threshold in two dimensions," Phys. Rev. Lett. **98**, 190504 (2007).
[29] P. Panteleev and G. Kalachev, "Quantum LDPC codes with almost linear minimum distance," IEEE Trans. Inf. Theory **68**, 213 (2022).
[30] A. Leverrier and G. Zémor, "Quantum Tanner codes," in *Proc. 63rd IEEE FOCS* (2022), pp. 872–883.
[31] N. P. Breuckmann and J. N. Eberhardt, "Quantum low-density parity-check codes," PRX Quantum **2**, 040101 (2021).
[32] S. Bravyi, D. Poulin, and B. Terhal, "Tradeoffs for reliable quantum information storage in 2D systems," Phys. Rev. Lett. **104**, 050503 (2010).
[33] E. Knill, "Quantum computing with realistically noisy devices," Nature **434**, 39 (2005).
[34] S. Bravyi, M. Englbrecht, R. König, and Y. Nirkhe, "Correcting coherent errors with surface codes," npj Quantum Inf. **4**, 55 (2018).
[35] Google Quantum AI and Collaborators, "Quantum error correction below the surface code threshold," Nature **625**, 74 (2024).
[36] Google Quantum AI, "Suppressing quantum errors by scaling a surface code logical qubit," Nature **614**, 676 (2023).
[37] M. Krinner, N. Lacroix, A. Remm, et al., "Realizing repeated quantum error correction in a distance-three surface code," Nature **605**, 669 (2022).
[38] E. Magesan, J. M. Gambetta, and J. Emerson, "Scalable and robust randomized benchmarking of quantum processes," Phys. Rev. Lett. **106**, 180504 (2011).
[39] T. Proctor, K. Rudinger, K. Young, M. Sarovar, and R. Blume-Kohout, "What randomized benchmarking actually measures," Phys. Rev. Lett. **124**, 010505 (2020).
