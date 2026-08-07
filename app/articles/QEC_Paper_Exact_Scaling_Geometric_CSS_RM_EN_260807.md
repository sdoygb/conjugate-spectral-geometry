# Exact Loss-Scaling Laws for Reed–Muller CSS Codes: Geometric Classification, Transversal Operations, and Four-Order Experimental Discrimination

**Author**: Ouyang Guobin

**Affiliation**: Foshan, Shunde District, Guangdong Province, China

---

## Abstract

We derive exact, closed-form expressions for the logical failure rate of self-orthogonal Reed–Muller CSS codes — the affine-complete family $[[2^m,\, 2^m - 2\sum_{i=0}^{r}\tbinom{m}{i},\, 2^{r+1}]]$, $2r < m-1$ — under independent per-qubit tilted noise with rotation bound $\theta_{\max}$. The unified scaling law states that, under minimum-weight decoding,

$$\mathrm{loss}(\theta_{\max}) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta_{\max}^{2w_0} + O(\theta_{\max}^{2w_0+2}), \qquad w_0 = \lceil d/2\rceil,$$

where the leading coefficient is fully explicit: $C(n,w_0)$ is a binomial factor, $P(w_0)$ the degeneracy fraction of the leading error layer, and the decoding failure rate $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$ is determined by the *class-size closed form* $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$, in which $s$ is the affine span dimension of the error support $A$ and the bracket is a Gaussian binomial. The parity of the distance governs the mechanism: odd $d$ forces cross-layer degeneracy and $\mathrm{fail} = 1$, whereas even $d$ gives same-layer degeneracy and $\mathrm{fail} = 1-\langle 1/v \rangle$ — this resolves the previously observed dichotomy between projective-geometric ($\theta^4$, $d=3$) and affine-complete ($\theta^d$) families within a single lemma chain. A universality theorem extends the scaling to arbitrary independent per-qubit Pauli channels: with $X$-side error probability $\varepsilon$, the same formula holds with $\varepsilon$ in place of $(\theta/2)^2$; depolarizing, coherent, and phase-damping channels are special cases. We further establish the transversal operation set $\{$Pauli, CNOT, $H\} \cup \{$diagonal phase gates$\} \cup \{$logical measurement$\}$: transversal $H$ is legal precisely because the $X$- and $Z$-stabilizer spaces coincide (self-orthogonality), and transversal $S^{\otimes n}$ induces a direction-dependent phase gate $\bar X_a \mapsto i^{|a|}\,\bar X_a$ whose character we compute exactly; the $T$ gate is interfaced through standard magic-state distillation, which requires only $d \ge 5$. All structural claims are verified by an enumeration-free method — an $O(n^2)$ syndrome-structure certificate replacing full enumeration — validated on seven family members up to $[[1024, 252, 32]]$ in seconds. The four distinct leading exponents $\theta^4, \theta^8, \theta^{16}, \theta^{32}$ for the members $[[1024, 1002, 4]]$, $[[1024, 912, 8]]$, $[[1024, 672, 16]]$, $[[1024, 252, 32]]$ provide a quantitative experimental discriminator on a 64–1121 qubit platform.

---

## 1. Introduction

### 1.1 Why exact failure-rate analysis

Quantum error correction promises to convert noisy physical qubits into reliable logical qubits, but the quantitative content of the promise is a scaling law: how the logical failure rate decays as the physical noise is reduced. The standard threshold theorems [1, 2, 16] establish *existence* of a noise threshold below which arbitrarily low logical error rates are achievable, but they do not deliver *closed-form* failure rates for concrete codes. Numerical simulations supply rates for specific instances, yet they scale poorly with code size and offer no structural explanation of the exponents and coefficients observed.

This paper develops a complementary, fully analytic program for a distinguished family of CSS codes: the failure rate is computed in closed form — both exponent *and* coefficient — and every structural claim entering the computation is verified by an enumeration-free certificate that runs in $O(n^2)$ time on codes of up to 1024 physical qubits. The closed forms expose a direct quantitative link between the *geometry* of the code (affine flats of the ambient $\mathrm{GF}(2)^m$) and the *performance* (failure rate), a link that is invisible in threshold analysis and only partially visible in numerical studies.

Three consequences motivate the exact approach.

(i) **Experimental discrimination.** Different code families exhibit failure rates $\theta^4$, $\theta^8$, $\theta^{16}$, $\theta^{32}$ at fixed physical qubit budget ($n = 1024$). The exponents differ by orders of magnitude in the small-noise regime, providing a sharp quantitative discriminator — no fitting parameters enter the prediction.

(ii) **Noise-model tomography.** The coefficient of the leading term is a function of the error-layer structure (degeneracy fraction $P(w_0)$ and failure rate $\mathrm{fail}(w_0)$). A measurement of the loss curve at two noise strengths separates the exponent (structure) from the coefficient (layer statistics), allowing the noise model itself to be tested.

(iii) **Recovery design.** The class-size closed form $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$ quantifies exactly how many error patterns share a syndrome with a given error $A$; the failure rate $1-\langle 1/v\rangle$ is the probability that minimum-weight decoding selects the wrong partner. This converts degeneracy from an obstacle into a precisely controlled resource.

### 1.2 Tilted noise and geometric completeness

The noise model studied here — *tilted coherent noise* — injects on each qubit an independent rotation

$$U(\theta_i) = \cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$$

by a random Pauli $E_i$, with angles $\theta_i \in [0, \theta_{\max}]$ bounded by a single parameter. Two features distinguish it from the depolarizing channel commonly assumed in threshold analyses. First, it is *coherent*: the state retains amplitude information, and the detection probability of a single-qubit rotation is exactly $\sin^2(\theta_i/2)$ — a closed form that is itself measurable. Second, it is *inhomogeneous*: different qubits receive different rotation angles, and only the upper bound $\theta_{\max}$ enters the scaling prediction. The expansion of the loss in powers of $\theta_{\max}$ is then organized by the *weight* of the injected error patterns, and each layer $w$ contributes $\theta_{\max}^{2w}$ with a coefficient built from three factors: the binomial $C(n,w)$, the degeneracy fraction $P(w)$ (fraction of weight-$w$ errors possessing a same-syndrome partner), and the decoding failure rate $\mathrm{fail}(w)$ (probability that minimum-weight decoding selects the wrong partner).

The central structural claim is that, for the code families studied here, all three factors are *geometrically determined*: $P(w)$ and $\mathrm{fail}(w)$ are closed forms in affine/projective flat counts of $\mathrm{GF}(2)^m$. We call such codes *geometrically complete* (Definition 2.4): (i) the minimum weight of non-trivial logical operators equals the distance $d$; (ii) the partner structure of errors of weight $w \ge d/2$ is governed by flat-counting closed forms. Two families satisfy the definition: the projective-geometric (PG-complete) Hamming CSS codes $[[2^m-1,\,2^m-1-2m,\,3]]$ and the affine-complete (AG-complete) Reed–Muller CSS codes $[[2^m,\, 2^m-2s,\, 2^{r+1}]]$ with $s = \dim \mathrm{RM}(r,m)$.

### 1.3 Contributions

1. **Unified scaling law (Theorem 4.1).** For any geometrically complete CSS code under independent tilted noise with bound $\theta_{\max}$, minimum-weight decoding yields the closed form
$$\mathrm{loss}(\theta_{\max}) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta_{\max}^{2w_0} + O(\theta_{\max}^{2w_0+2}),$$
with $w_0 = \lceil d/2 \rceil$; the leading exponent is $d$ for even $d$ and $d+1$ for odd $d$. The parity dichotomy of the failure rate is resolved: odd $d$ forces cross-layer partners and $\mathrm{fail} = 1$; even $d$ gives same-layer partners and $\mathrm{fail} = 1 - \langle 1/v\rangle$.

2. **Class-size and failure-rate closed forms (Theorem 4.2).** For the affine-complete family, the weight-$2^r$ layer has class size $v(A) = 1 + \bigl[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\bigr]_2$ where $s = \dim \mathrm{aff}(A)$; consequently $\mathrm{fail}(w_0) = 1 - P(3)/2 - P(\le 2)\,2^{2-m}$ for $r=2$, $= 1 - 2^{1-m}$ for $r=1$, and $\approx 1/2$ for $r \ge 3$ (with exponentially small corrections). All entries of the family table (Theorem 10.35.1.02 in the companion series) are recovered with no fitting parameter.

3. **Pauli-channel universality (Theorem 4.3).** The scaling law holds verbatim for arbitrary independent per-qubit Pauli channels: with $X$-side error probability $\varepsilon$ (probability that the error operator contains $X$ or $Y$), the $X$-side failure rate equals $\sum_{w\ge w_0} C(n,w)\,\varepsilon^w(1-\varepsilon)^{n-w}\,\mathrm{fail}(w)$, with the *same* $\mathrm{fail}(w)$ as in the coherent case — the decoder is a deterministic function of syndrome and weight, and the channel enters only through $\varepsilon$. Coherent tilt: $\varepsilon = \sin^2(\theta/2)$; depolarizing: $\varepsilon = 2p/3$; phase damping (after twirling): $\varepsilon = 0$; amplitude damping (after twirling): $\varepsilon = \gamma/2$. Non-twirled coherent non-Pauli processes fall outside the framework (syndrome response becomes probabilistic); Pauli twirling — standard experimental practice — restores it.

4. **Enumeration-free verification (Section 3.3).** The structural claims entering the scaling law are verified without enumerating error patterns: column distinctness of the generator matrix implies full weight-2 detection in $O(n^2)$ time; the constant coordinate blocks cross-weight syndrome degeneracy (Theorem 3.5); quadratic monomials block weight-2 internal degeneracy for $r \ge 2$ (Theorem 3.6). The full structural certificate for $[[1024, 252, 32]]$ runs in 8.8 s.

5. **Transversal operations (Section 5).** The affine-complete family supports transversal Pauli, CNOT, and $H$ gates; transversal $S^{\otimes n}$ preserves the code space and induces the direction-dependent phase gate $\bar X_a \mapsto i^{|a|}\,\bar X_a$ with $\gamma_a = i^{|a|}$ (Theorem 5.2). The fault-tolerant operation set is $\{$transversal Pauli, CNOT, $H\} \cup \{$diagonal phase gates$\} \cup \{$logical measurement$\}$, and $T$ is interfaced by standard magic-state distillation — requiring only $d \ge 5$, satisfied by all members with $r \ge 2$.

6. **Four-order experimental discriminator (Section 6).** On a 64–1121 qubit platform, the members $[[1024, 1002, 4]]$, $[[1024, 912, 8]]$, $[[1024, 672, 16]]$, $[[1024, 252, 32]]$ predict loss slopes $\theta^4, \theta^8, \theta^{16}, \theta^{32}$ in log-log coordinates. The slope quadruple is a parameter-free signature of the geometric structure; any deviation falsifies the class-size mechanism at the corresponding layer.

### 1.4 Related work

The relation of this work to the existing literature is analyzed in detail in Section 7. Briefly: the CSS construction is due to Calderbank–Shor [3] and Steane [2]; stabilizer formalism follows Gottesman [4]; Reed–Muller codes and their weight distributions are classical [6–9]; magic-state distillation follows Bravyi–Kitaev [14] and the fault-tolerance roadmaps of Refs. [13, 15]; threshold analyses for concatenated and topological codes are found in Refs. [11, 16]. The *exact closed-form failure-rate analysis with geometric coefficients* presented here appears to be new: standard treatments of Reed–Muller CSS codes (e.g., the Steane code $[[7,1,3]]$ as $\mathrm{RM}(1,3)$) focus on distance and thresholds, not on the layer-resolved degeneracy structure and its closed-form failure rates. Section 7 provides a systematic comparison, including the precise relationship to the 315/945 $= 1/3$ degeneracy of the $[[15,7,3]]$ code observed in early numerical studies.

### 1.5 Structure of the paper

Section 2 collects the notation and the general framework: stabilizer formalism, CSS codes, Reed–Muller codes, the tilted noise model, and the definition of geometric completeness. Section 3 introduces the geometric families — the PG-complete codes (why $d = 3$ is locked) and the affine-complete codes (parameters, distance, enumeration-free verification, logical-operator counting, numerical verification). Section 4 states and proves the unified scaling law, the class-size and failure-rate closed forms, and the Pauli-channel universality theorem. Section 5 establishes the transversal operation set. Section 6 presents the four-order experimental discriminator. Section 7 compares with the existing literature. Section 8 concludes. The Appendix documents the numerical procedures and the reproducibility data (code archived at Zenodo).

---

## 2. Preliminaries

### 2.1 Stabilizer formalism and CSS codes

Let $\mathcal{P}_n$ be the $n$-qubit Pauli group. A stabilizer code is the joint $+1$ eigenspace $\mathcal{C}(S)$ of an abelian subgroup $S \subset \mathcal{P}_n$ not containing $-I$; its parameters are written $[[n,k,d]]$, with $k$ logical qubits and distance $d$ equal to the minimum weight of a Pauli operator in the centralizer $\mathcal{Z}(S)$ that is not in $S$. The syndrome of an error $E$ is the list of commutation relations of $E$ with a fixed generating set of $S$; a decoding rule maps syndromes to recovery operators.

**CSS construction** [2, 3]. Let $C_2 \subseteq C_1 \subseteq \mathbb{F}_2^n$ be classical linear codes. The CSS code $\mathrm{CSS}(C_1, C_2)$ has stabilizer generated by $\{X_v : v \in C_2\} \cup \{Z_v : v \in C_1^\perp\}$, where $X_v = \bigotimes_i X^{v_i}$ and $Z_v = \bigotimes_i Z^{v_i}$. Its parameters satisfy $k = \dim C_1 - \dim C_2$ and

$$d = \min\big\{\mathrm{wt}(C_1 \setminus C_2),\; \mathrm{wt}(C_2^\perp \setminus C_1^\perp)\big\},$$

with $\mathrm{wt}(\mathcal{D})$ the minimum Hamming weight of a vector in $\mathcal{D}$. The logical zero state is $|0_L\rangle = \frac{1}{\sqrt{|C_2|}}\sum_{x \in C_2} |x\rangle$. Logical operators: for $a \in C_1 \setminus C_2$ (respectively $a \in C_2^\perp \setminus C_1^\perp$), $X_a$ (respectively $Z_a$) is a logical operator.

**Self-orthogonal symmetric CSS codes.** A CSS code of the form $\mathrm{CSS}(H, H)$ — written with a single matrix $H$ whose row space is the stabilizer space $C$ — has both $X$- and $Z$-stabilizers generated from the *same* space $C$, and is well defined precisely when $C$ is self-orthogonal, $C \subseteq C^\perp$. Then $X$-stabilizer space $=$ $Z$-stabilizer space $= C$, and $k = n - 2\dim C$. The logical spaces are $L = C^\perp$; non-trivial logical operators have supports in $C^\perp \setminus C$.

**Minimum-weight decoding.** Given syndrome $s$, the decoder selects a minimum-weight error $e$ with that syndrome and applies the corresponding recovery. If the true error and the selected representative differ by a logical operator (i.e., the syndrome class contains a non-trivial logical), the correction fails. The *decoding failure rate* $\mathrm{fail}(w)$ of a weight-$w$ layer is the probability that minimum-weight decoding fails for a uniformly random weight-$w$ error pattern; equivalently, the fraction of weight-$w$ patterns whose syndrome class has a non-unique minimum-weight representative.

### 2.2 Reed–Muller codes

Identify $\mathbb{F}_2^m$ with the $2^m$ points of the affine geometry $\mathrm{AG}(m,2)$.

**Definition 2.1** (Reed–Muller code). For $0 \le r \le m$, the Reed–Muller code $\mathrm{RM}(r,m)$ consists of all evaluation vectors $\big(f(p)\big)_{p \in \mathrm{AG}(m,2)}$ of polynomials $f \in \mathbb{F}_2[x_1,\dots,x_m]$ of degree $\le r$.

Standard facts [6, 8]:

$$\dim \mathrm{RM}(r,m) = \sum_{i=0}^{r} \binom{m}{i}, \qquad \min\mathrm{wt}\,\mathrm{RM}(r,m) = 2^{m-r},$$

and the **duality theorem**: $\mathrm{RM}(r,m)^\perp = \mathrm{RM}(m-r-1, m)$. In particular $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(r,m)^\perp$ if and only if $2r < m-1$ — the self-orthogonality condition that makes $\mathrm{CSS}(\mathrm{RM}(r,m), \mathrm{RM}(r,m))$ a valid CSS code.

Two counting inputs from affine geometry are used throughout. The number of $k$-dimensional affine flats in $\mathrm{AG}(m,2)$ is

$$\mathrm{flats}(m,k) = 2^{m-k}\left[\begin{matrix}m\\ k\end{matrix}\right]_2 = 2^{m-k}\prod_{i=0}^{k-1}\frac{2^{m-i}-1}{2^{k-i}-1},$$

with the Gaussian binomial $\bigl[\begin{smallmatrix}m\\ k\end{smallmatrix}\bigr]_2$; and the indicator functions of $k$-flats are exactly the minimum-weight vectors of $\mathrm{RM}(m-k, m)$: a $(k+1)$-flat indicator has weight $2^{k+1}$ and degree $m-k-1$.

**Weight layers.** We record the weight-parity structure needed in Section 5: every codeword of $\mathrm{RM}(r,m)$ with $r \le m-3$, $m \ge 4$, has weight $\equiv 0 \pmod 4$. (Indeed $\mathrm{RM}(m-2,m)$ is the even-weight subspace and the minimum weight $2^{m-r} \ge 8$; the congruence follows from the standard weight distribution of Reed–Muller codes [9].)

### 2.3 Tilted noise model and loss expansion

**Coherent tilted noise.** Each physical qubit $i$ receives an independent rotation $U(\theta_i) = \cos(\theta_i/2)\,I + i\sin(\theta_i/2)\,E_i$ by a Pauli $E_i$, with $\theta_i \in [0, \theta_{\max}]$. The bound $\theta_{\max}$ is the single noise parameter. For a fixed injection pattern $\mathbf{E} = (E_1,\dots,E_n)$, the probability weight of the configuration is $\prod_i \sin^2(\theta_i/2)$ for the error part and $\prod_i \cos^2(\theta_i/2)$ for the identity part. Two measurable closed forms follow from the coherent structure:

- detection probability of a single-qubit injection: $\sin^2(\theta_i/2)$ (the syndrome flip probability);
- non-detected paths preserve fidelity: the projection back to the code space is exact.

These were verified to machine precision in the companion numerical studies; they are the experimental anchors of the model.

**Loss expansion.** Let $\mathrm{loss}(\theta_{\max})$ be the expected infidelity after optimal (minimum-weight) recovery, averaged over random angles $\theta_i \in [0,\theta_{\max}]$ and random Pauli types. Expanding in powers of $\theta_{\max}$:

$$\mathrm{loss}(\theta_{\max}) = \sum_{w \ge 1} C(n,w)\,P(w)\,\mathrm{fail}(w)\,\big\langle \sin^{2w}(\theta/2) \big\rangle \,\big\langle \cos^{2(n-w)}(\theta/2) \big\rangle,$$

where the averages are over the angle distribution; for the uniform bound model, $\langle \sin^{2w}(\theta/2)\rangle = \theta_{\max}^{2w}/(4^w(2w+1)) + O(\theta_{\max}^{2w+2})$, and $\langle \cos^{2(n-w)}(\theta/2)\rangle = 1 + O(\theta_{\max}^2)$. The three factors in the coefficient of $\theta_{\max}^{2w}$ are: $C(n,w)$ — the number of weight-$w$ injection supports; $P(w)$ — the *degeneracy fraction* of the weight-$w$ layer, i.e., the fraction of weight-$w$ errors possessing at least one distinct same-syndrome partner; and $\mathrm{fail}(w)$ — the *decoding failure rate* of that layer. A layer with no same-syndrome partners ($P(w) = 0$) contributes nothing; a layer with unique minimum-weight representatives has $\mathrm{fail}(w) = 0$; the leading surviving layer is $w_0 = \lceil d/2 \rceil$ (Section 4, Lemma 4.1).

**Pauli-channel form.** For a general independent per-qubit Pauli channel with $X$-side error probability $\varepsilon$ (the probability that the error operator has an $X$ or $Y$ component; $Z$ errors are invisible to the $X$-syndrome), the $X$-side failure rate is

$$\mathrm{loss}(\varepsilon) = \sum_{w \ge 0} C(n,w)\,\varepsilon^w (1-\varepsilon)^{n-w}\,\mathrm{fail}(w).$$

The channel constants: coherent tilt $\varepsilon = \sin^2(\theta/2)$; depolarizing with rate $p$: $\varepsilon = 2p/3$; phase damping (twirled): $\varepsilon = 0$; amplitude damping (twirled): $\varepsilon = \gamma/2$. The universality of the coefficient sequence $\mathrm{fail}(w)$ across channels is Theorem 4.3.

### 2.4 Geometric completeness

**Definition 2.2** (Geometrically complete CSS code). A CSS code $[[n,k,d]]$ with stabilizer space $S = \mathrm{rowspace}(H)$ and logical space $L = S^\perp$ is *geometrically complete* if

(i) the minimum weight of $L \setminus S$ equals the distance $d$;

(ii) for every error weight $w \ge d/2$, the partner structure — the assignment of same-syndrome representatives — is governed by closed-form counts of affine/projective flats of $\mathrm{GF}(2)^m$: the class size $v(A)$ of an error support $A$ depends only on the affine span dimension $s = \dim \mathrm{aff}(A)$ through an explicit formula.

Two families satisfy the definition:

- **PG-complete codes**: $H$ columns = all nonzero vectors of $\mathbb{F}_2^m$ (the simplex code as stabilizer), parameters $[[2^m-1,\, 2^m-1-2m,\, 3]]$, logical space the Hamming code (Section 3.1);
- **AG-complete codes** (affine-complete): $H$ = generator matrix of $\mathrm{RM}(r,m)$ evaluated on all $2^m$ points of $\mathrm{AG}(m,2)$, parameters $[[2^m,\, 2^m - 2\dim\mathrm{RM}(r,m),\, 2^{r+1}]]$ for $2r < m-1$ (Section 3.2).

Both families are CSS codes in the standard sense; the "completeness" is a structural property of their syndrome geometry — the partner structure is exactly computable, not merely estimable.
