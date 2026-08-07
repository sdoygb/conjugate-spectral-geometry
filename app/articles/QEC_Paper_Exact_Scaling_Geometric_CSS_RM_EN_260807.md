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

---

## 3. Geometric families of CSS codes

### 3.1 Projective-geometric codes: why $d = 3$ is locked

The PG-complete family is obtained by taking as stabilizer space the simplex code: $H$ has as columns all nonzero vectors of $\mathbb{F}_2^m$ (points of the projective geometry $\mathrm{PG}(m-1,2)$), yielding the Hamming CSS codes $[[2^m-1,\, 2^m-1-2m,\, 3]]$ with $S = \mathrm{Simplex}(m)$ and $L = \mathrm{Hamming}(m)$. This family was analyzed in detail in the companion series; its structure is the baseline against which the affine-complete family is measured:

- **Distance locked at 3.** Any two distinct nonzero vectors are linearly independent, so no weight-2 logical exists ($d \ge 3$); but projective closure — the XOR of any two columns is again a column — forces a weight-3 logical operator for every pair of columns (three collinear points). Hence $d = 3$ *structurally*.
- **Cross-weight degeneracy fraction 1/3.** For the $[[15,7,3]]$ member, exactly 315 of the 945 weight-2 errors share a syndrome with a single-qubit error: the shared syndrome class contains a weight-3 logical operator, and after recovery a residual weight-3 logical error remains. The fraction 315/945 $= 1/3$ is the fraction of Pauli types (XX, ZZ, YY among the nine) whose syndrome coincides with that of a weight-1 error, by column-XOR closure.
- **Loss $\theta^4$.** With $w_0 = \lceil 3/2 \rceil = 2$, the leading layer is weight 2 with $\mathrm{fail}(2) = 1$ (cross-layer partner always chosen), giving $\mathrm{loss} \sim \theta^4$ with coefficient $(1/3)\,C(2^m-1,2)\,2^{-4}$; numerically measured log-log slopes 3.99–4.14 on $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$.

The locked distance $d = 3$ motivates the affine construction: to reach $d \ge 5$ one needs every 4 columns affinely independent — a 4-arc. In binary projective space the counting bound is $\sim 2^N/3$ but explicit 4-arcs are far smaller ($\mathrm{PG}(3,2)$ has at most 5 points), so the projective point-set path cannot reach large distances with positive rate. The resolution is to *change the column space*: evaluate at all $2^m$ points of the affine geometry, which yields the Reed–Muller CSS family with arbitrarily large distance.

### 3.2 Affine-complete codes: definition, parameters, distance

**Definition 3.1** (Affine-complete code). Let $\mathrm{RM}(r,m)$ be the Reed–Muller code of Section 2.2, with generator matrix $H$ whose rows are the evaluations of all monomials of degree $\le r$ on the $2^m$ points of $\mathrm{AG}(m,2)$. The affine-complete code is the symmetric CSS code $\mathrm{CSS}(H,H)$ with stabilizer space $C = \mathrm{RM}(r,m)$, subject to the self-orthogonality condition $C \subseteq C^\perp$.

**Theorem 1** (Self-orthogonality). $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(r,m)^\perp$ if and only if $2r < m-1$.

*Proof.* By the duality theorem, $\mathrm{RM}(r,m)^\perp = \mathrm{RM}(m-r-1,m)$, and $\mathrm{RM}(r,m) \subseteq \mathrm{RM}(m-r-1,m)$ iff $r \le m-r-1$, i.e. $2r \le m-1$; the strict inequality is required because $r = (m-1)/2$ would make the code self-dual with $k = 0$. ∎

**Theorem 2** (Parameters). The affine-complete code has parameters

$$\big[\!\big[\,2^m,\; 2^m - 2\sum_{i=0}^{r}\tbinom{m}{i},\; 2^{r+1}\,\big]\!\big].$$

*Proof.* $n = 2^m$ by construction. Since $X$- and $Z$-stabilizer spaces both equal $C = \mathrm{RM}(r,m)$ with $\dim C = \sum_i \binom{m}{i}$ (Section 2.2), $k = n - 2\dim C$. The distance is Theorem 3. ∎

**Theorem 3** (Distance). The minimum distance of $\mathrm{CSS}(\mathrm{RM}(r,m), \mathrm{RM}(r,m))$ is $d = 2^{r+1}$.

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

### 3.3 Enumeration-free verification

Full enumeration of error patterns is infeasible at $n = 1024$ (there are $\binom{1024}{2} \approx 5.2\times 10^5$ weight-2 patterns, but $\binom{1024}{4} \approx 4.6\times 10^{10}$ weight-4 patterns and $\binom{1024}{16} \sim 10^{33}$ at the leading layer of $[[1024,252,32]]$). The following structural theorems replace enumeration by $O(n^2)$ certificates.

**Theorem 4** (Column distinctness implies full weight-2 detection). The evaluation columns of $\mathrm{RM}(r,m)$ are pairwise distinct on $\mathrm{AG}(m,2)$. Consequently every weight-2 error pattern is detected: for any two distinct positions $a, b$, the $X$-syndrome $\mathrm{col}_a \oplus \mathrm{col}_b \ne 0$, and the same holds for the $Z$-syndrome; all nine Pauli types of weight-2 errors are detected.

*Proof.* The constant coordinate (the evaluation of the monomial 1) together with the coordinate functions $x_1,\dots,x_m$ separate any two distinct points of $\mathrm{AG}(m,2)$: if $p \ne q$, some coordinate function differs, so the evaluation columns differ in the corresponding row. The syndrome of the weight-2 error $(a,b)$ is $\mathrm{col}_a \oplus \mathrm{col}_b$ (for the $X$-type) and the same combination for the $Z$-type; a mixed Pauli error has syndrome $\mathrm{col}_a \oplus \mathrm{col}_b$ on both sides. Nonzero in all cases. ∎

**Theorem 5** (Cross-weight zero degeneracy). No weight-1 error shares a syndrome with any weight-2 error: the cross-weight syndrome degeneracy of the affine-complete family is exactly 0 (contrast: 1/3 for the PG-complete family).

*Proof.* The syndrome of a single-qubit error $X_a$ is the column $\mathrm{col}_a$, whose constant coordinate is 1 (the evaluation of the constant monomial at $a$ is 1). The syndrome of a weight-2 $XX$ error is $\mathrm{col}_a \oplus \mathrm{col}_b$, whose constant coordinate is $1 \oplus 1 = 0$. The constant coordinate — the new ingredient of the affine construction, absent in the projective one — blocks the equality $0 \ne 1$. In the PG family the constant coordinate does not exist, and the XOR of two columns is again a column, producing the 1/3 cross-layer degeneracy. ∎

**Theorem 6** (Weight-2 layer complete uniqueness for $r \ge 2$). For $r \ge 2$, any two distinct weight-2 error patterns have distinct syndromes: the weight-2 layer has zero internal degeneracy, and the full recovery table is conflict-free at weights 1 and 2.

*Proof.* Suppose $\{a,b\} \ne \{a',b'\}$ share a syndrome. Then for every monomial $f$ of degree $\le r$, $f(a) + f(b) = f(a') + f(b')$. The linear part ($f = x_i$) gives $a + b = a' + b'$: the pairs form a parallelogram. The quadratic part ($f = x_i x_j$) gives $s_i \delta_j + s_j \delta_i = 0$ for all $(i,j)$, where $s = a+b$ and $\delta = a + a'$. A nontrivial solution requires $s \parallel \delta$; over $\mathbb{F}_2$, $s = \delta$, i.e., the pairs coincide — contradiction. Hence all syndromes are distinct. (For $r = 1$ the linear part is insufficient: parallelogram degeneracy appears, e.g. $\mathrm{RM}(1,5)$: 496 pairs collapse into 63 classes — the $r=1$ anomaly quantified in the failure-rate analysis of Section 4.) ∎

### 3.4 Logical-operator counting

**Theorem 7** (Logical-operator counting). The number of weight-$d$ logical operators of the $X$-type in $\mathrm{CSS}(\mathrm{RM}(r,m))$ equals the number of $(r+1)$-dimensional affine flats of $\mathrm{AG}(m,2)$:

$$N_{\mathrm{logic}} = 2^{\,m-r-1}\left[\begin{matrix}m\\ r+1\end{matrix}\right]_2 = 2^{\,m-r-1}\prod_{i=0}^{r}\frac{2^{m-i}-1}{2^{r+1-i}-1}.$$

*Proof.* The weight-$d = 2^{r+1}$ vectors of $C^\perp = \mathrm{RM}(m-r-1,m)$ are exactly the indicators of $(r+1)$-flats (Section 2.2), and their number is the flat count. Every such vector lies in $L \setminus C$ since $\min\mathrm{wt}\,\mathrm{RM}(r,m) = 2^{m-r} > 2^{r+1}$; each is a logical operator by Lemma 4.1 below (syndrome zero). ∎

The closed form was verified by exhaustive enumeration at small sizes: $\mathrm{RM}(1,5)$: 1240 logical operators of weight 4, equal to the 2-flat count of $\mathrm{AG}(5,2)$; $\mathrm{RM}(1,6)$: 10416, the 2-flat count of $\mathrm{AG}(6,2)$ (full enumeration of $\binom{64}{4}$ patterns, 2.8 s).

### 3.5 Numerical verification

The enumeration-free certificates of Theorems 4–6 and the counting of Theorem 7 were executed for all seven members of Table 1 (symbolic bit-mask arithmetic; code archived at Zenodo, see Appendix):

| code | (a) col. distinct | (b) weight-2 pairs | (c) 3000 samples | (d) cross-wt. deg. | (e) internal deg. | time |
|---|---|---|---|---|---|---|
| $[[32,20,4]]$ | ✓ | 496 ✓ | ✓ | 0/496 | 63 classes ($r=1$) | 0.11 s |
| $[[64,20,8]]$ | ✓ | 2016 ✓ | ✓ | 0/2016 | 0 | 0.33 s |
| $[[128,70,8]]$ | ✓ | 8128 ✓ | ✓ | 0/8128 | 0 | 0.43 s |
| $[[256,70,16]]$ | ✓ | 32640 ✓ | ✓ | 0/32640 | 0 | 1.52 s |
| $[[512,252,16]]$ | ✓ | 130816 ✓ | ✓ | 0/130816 | 0 | 2.46 s |
| $[[1024,252,32]]$ | ✓ | 523776 ✓ | ✓ | 0/523776 | 0 | 8.78 s |

Table 2. Verification results. (c) = random weight-3..$d-1$ syndrome sampling (3000 per code); (d) = cross-weight degeneracy count; (e) = internal (same-weight) degeneracy count at weight 2.

All certificates pass. Notably $[[1024, 252, 32]]$ — a 1024-qubit code with distance 32 — receives a complete structural certificate in 8.8 s with memory at the kilobyte level: the enumeration-free method renders thousand-qubit codes analytically tractable, which is the enabling step for the exact failure-rate analysis of Section 4.


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

*Verification.* Direct state-vector simulation over the codes $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$ for all qubits and all Pauli types, with $\theta \in [0.05, 0.4]$, gives maximum deviation from the closed forms of $3.8\times10^{-16}$ (detection rate) and $2.2\times10^{-16}$ (conditional fidelities) [10.29 §3.2]. The closed form (a) is the probability that the $E$ component of the rotated state is detected; since $U(\theta)$ prepares the superposition $\cos(\theta/2)|\psi\rangle + i\sin(\theta/2)E|\psi\rangle$ and the $E$ branch anticommutes with $g$, the detected probability is $|\sin(\theta/2)|^2$. ∎

Property (b) is the "undetected injection is harmless" principle: a missed detection leaves the state inside the code space, so no logical information is destroyed; only the detected branch triggers recovery. Property (c) reflects that logical operators commute with all stabilizers by definition.

### 4.2 Zero-loss theorem

The following structural result shows that coherent injections of weight below $d/2$ are *perfectly* correctable: the minimal-weight decoder recovers them exactly, and the post-recovery loss is identically zero.

**Theorem 9 (Zero-loss theorem).** Let $\mathcal{C} = [[n,k,d]]$ be any CSS code of minimum distance $d$. Inject coherent rotations $U(\theta_j) = \exp(i\theta_j P_j/2)$ on an arbitrary set of $k \le \lfloor(d-1)/2\rfloor$ qubits, with $P_j$ Pauli operators and $\theta_j \le \theta_{\max}$ arbitrary. After syndrome measurement and minimal-weight decoding, the loss is identically zero: $\mathrm{loss} = 0$ for every realization.

*Proof.* Expand the injected state in the Pauli basis: it is a superposition of terms $\chi_S$, $S \subseteq$ (injected set), $|S| \le k$, where $\chi_S$ is the weight-$|S|$ error on $S$. Fix $S$ with $w = |S| \le \lfloor(d-1)/2\rfloor$. Suppose some error $R'$ of weight $w' < w$ has the same syndrome as $\chi_S$. Then $\chi_S \cdot R' \in C^{\perp}$ and its weight satisfies $w + w' - 2|S \cap R'| \le 2w - 1 \le d - 2 < d$, contradicting that $C^{\perp}$ has minimum weight $d$. Suppose instead a distinct error $R'$ of the same weight $w$ shares the syndrome; then $\chi_S \cdot R'$ has weight $\le 2w - 2 < d$, again a contradiction. Hence the syndrome of $\chi_S$ is unique, minimal-weight decoding selects $R = \chi_S$ uniquely, and recovery is perfect. Summing over branches, the loss vanishes. ∎

**Corollary 10.** For the affine-complete code $[[64,20,8]]$ (Sec. 3), any injection on $\le 3$ qubits produces identically zero loss after optimal recovery. For comparison, the projective-geometric code $[[15,7,3]]$ already loses at weight 2: collinear pairs share the syndrome of a single-qubit error (Sec. 3.1), so the minimal-weight decoder applies a single-qubit correction and leaves a weight-3 logical residual with $\theta^4$ loss.

The corollary quantifies "distance buys noise immunity": a $d=8$ code is perfectly immune to coherent disturbances on up to three qubits, whereas a $d=3$ code pays $\theta^4$ already for two-qubit joint disturbances.

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

*Proof.* Expand the injected state into weight-$w$ branches with amplitudes of order $\theta^w$. Branches with $w < w_0 := \lceil d/2\rceil$ have unique syndromes (the argument of Theorem 9 applies verbatim) and contribute zero loss. At weight $w_0$, degeneracy is possible and, for the geometrically complete families, present with strictly positive proportion: for PG codes ($d=3$, $w_0=2$) the collinear mechanism gives proportion $1/3$; for AG codes the inclusion equivalence (Theorem 11) and positivity of $P_r(m)$ guarantee degeneracy at $w_0 = 2^r$. Within a degenerate class the decoder errs with probability $(v-1)/v \ge 1/2$. Hence the lowest nonvanishing loss order is $(\theta^{w_0})^2 = \theta^{2w_0}$, contributed by the weight-$w_0$ layer; higher-weight branches contribute $o(\theta^{2w_0})$. ∎

*Instantiation.* (i) $d = 3$: the codes $[[5,1,3]]$, $[[7,1,3]]$, $[[9,1,3]]$ exhibit measured log-log slopes $4.04, 4.12, 4.14$ over $\theta_{\max} \in [0.05, 0.4]$ [10.29 §3.1]; the $[[15,7,3]]$ code with fixed 4-qubit injection gives loss $= 6\cos^4(\theta/2)\sin^4(\theta/2) \sim 3\theta^4/8$ with slope $3.99 \approx 4$ [10.31]. (ii) $d = 8$: the $[[64,20,8]]$ code, 4-qubit injection, exhibits slope $7.96 \approx 8$ and weight-4 branch failure rate $48.5\%$ (200 trials) against the theoretical $50.7\%$ [10.31]. The four-order gap $\theta^4$ vs. $\theta^8$ between $d=3$ and $d=8$ codes is the experimental discriminator of Sec. 8.

## 5. Unified scaling law and failure-rate closed forms

The scaling law of Theorem 14 fixes the exponent; the unified framework of this section fixes the *coefficients* in closed form. The loss expansion is organized by weight layers; each coefficient factorizes into a combinatorial count $C(n,w)$, a degeneracy proportion $P(w)$, and a conditional failure rate $\mathrm{fail}(w)$ that depends only on the syndrome geometry — not on the noise channel. This channel independence is the content of the Pauli-channel universality theorem (Sec. 5.5).

### 5.1 Branch-level loss expansion

**Theorem 15 (Branch-level loss expansion).** Let $\mathcal{C} = [[n,k,d]]$ be a geometrically complete CSS code, and let independent coherent rotations with common bound $\theta$ act on all $n$ qubits. The loss of minimal-weight decoding admits the expansion

$$\mathrm{loss}(\theta) = \sum_{w \ge w_0} C(n,w)\,P(w)\,\mathrm{fail}(w)\,\left(\tfrac{\theta}{2}\right)^{2w}\left(1 - \tfrac{\theta^2}{4}\right)^{n-w},$$

where $P(w)$ is the proportion of weight-$w$ errors with non-unique syndrome (degenerate errors) and $\mathrm{fail}(w)$ is the conditional decoding failure rate on the weight-$w$ layer.

*Proof sketch.* Each qubit's rotation expands as $\cos(\theta/2)\,I + i\sin(\theta/2)\,E$; a term with errors on exactly the set $S$, $|S| = w$, carries amplitude $\sin^w(\theta/2)\cos^{n-w}(\theta/2)$, hence probability weight $(\theta/2)^{2w}(1 - \theta^2/4)^{n-w}$ at leading order. There are $C(n,w)$ such sets; a fraction $P(w)$ lie in degenerate classes where the minimal-weight decoder can err; conditioned on degeneracy, the failure rate is $\mathrm{fail}(w)$. By Theorem 9 the layers $w < w_0$ have $P(w) = 0$; the sum starts at $w_0$. ∎

For $d$ odd, the layer $w_0 = (d+1)/2$ is *cross-layer* degenerate: partners live at weight $d - w_0 = (d-1)/2 < w_0$, so minimal-weight decoding necessarily selects the lower-weight partner, leaving a weight-$d$ logical residual: failure is certain, $\mathrm{fail}(w_0) = 1$. For $d$ even, $w_0 = d/2$ and partners are same-layer; within a class of size $v$ the decoder errs with probability $(v-1)/v$, so $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$, the average over classes. The class sizes themselves are closed: see Theorem 18.

### 5.2 Unified scaling law

**Theorem 16 (Unified scaling law — main theorem).** Let $\mathcal{C} = [[n,k,d]]$ be a geometrically complete CSS code. Under independent coherent noise with per-qubit bound $\theta$, the loss of the optimal decoder is

$$\mathrm{loss}(\theta) = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}\,\theta^{2w_0} \;+\; O\!\left(\theta^{2w_0+2}\right), \qquad w_0 = \lceil d/2\rceil,$$

with $C(n,w_0)$ the binomial coefficient, $P(w_0)$ the degeneracy proportion (Prop. 13 for AG codes; $1/3$ for PG codes), and $\mathrm{fail}(w_0)$ the parity-dependent failure rate of Theorem 17 below. Equivalently, $\mathrm{loss}(\theta) = c_d\,\theta^{2w_0} + o(\theta^{2w_0})$ with

$$c_d = C(n,w_0)\,P(w_0)\,\mathrm{fail}(w_0)\,2^{-2w_0}.$$

*Proof.* Theorems 12 and 13: layers below $w_0$ vanish; the leading term is the $w = w_0$ branch of the expansion with $(1 - \theta^2/4)^{n-w_0} = 1 + O(\theta^2)$. ∎

**Theorem 15 (Parity theorem for the failure rate).** In the setting of Theorem 14:
(i) if $d$ is odd, $\mathrm{fail}(w_0) = 1$ (cross-layer degeneracy: the partner has weight $d - w_0 < w_0$, minimal-weight decoding selects it with certainty, and the residual is a minimum-weight logical operator);
(ii) if $d$ is even, $\mathrm{fail}(w_0) = 1 - \langle 1/v \rangle$, where $v$ runs over the degenerate class sizes at weight $w_0$ and $\langle \cdot \rangle$ is the class-size-weighted average.

*Proof.* (i) Let $\chi_A$ be degenerate with partner $\chi_B$, $|B| = d - w_0$. Since $|B| < w_0$ and all weights $< w_0$ have unique syndromes, the syndrome of $\chi_A$ is matched by the unique weight-$|B|$ error; minimal-weight decoding selects $\chi_B$; the residual $\chi_A\chi_B$ has weight $d$ and lies in $C^{\perp}$ (equal syndromes), i.e. is a logical operator; the state is flipped: failure. (ii) All partners of a weight-$w_0$ error have weight $w_0$ (any lower weight would contradict uniqueness); the decoder chooses uniformly among the $v$ class members; exactly one is correct. ∎

For the affine-complete families the average $\langle 1/v \rangle$ is computable from the class-size closed form:

**Theorem 16 (Class-size closed form).** For $CSS(RM(r,m))$, let $A$ be a $2^r$-subset of $AG(m,2)$ with affine span of dimension $s$ ($0 \le s \le r+1$). The size of the syndrome class of $\chi_A$ at weight $2^r$ is

$$v(A) = 1 + \left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2,$$

the Gaussian binomial coefficient counting $(r+1-s)$-dimensional subspaces of the $(m-s)$-dimensional quotient $AG(m,2)/\mathrm{span}(A)$; the $+1$ counts $\chi_A$ itself.

*Proof sketch.* By Theorem 10, partners of $\chi_A$ are the complements $P \setminus A$ over all $(r+1)$-flats $P \supset A$. Flats containing $A$ correspond bijectively to flats of the quotient $AG(m,2)/\mathrm{span}(A)$ of dimension $(r+1-s)$; their number is the Gaussian binomial $\left[\begin{smallmatrix}m-s\\ r+1-s\end{smallmatrix}\right]_2$. ∎

*Instances.* $r = 1$ ($d = 4$): any 2-subset has span $s = 1$, giving $v = 1 + \left[\begin{smallmatrix}m-1\\ 1\end{smallmatrix}\right]_2 = 2^{m-1}$: classes of size $2^{m-1}$ (e.g. $v = 16$ for $[[32,12,4]]$, matching the "465 pairs $= 31\times 15$" enumeration). $r = 2$ ($d = 8$): generic 4-subsets have $s = 3$, $v = 2$ (complement pairs — the 313,131 classes of $[[64,20,8]]$); coplanar 4-subsets have $s = 2$, $v = 2^{m-2}$ — the bimodal class structure $2$ / $2^{m-2}$. Consequently $\mathrm{fail}(4) = 1 - \langle 1/v\rangle = 0.507172131$ for $[[64,20,8]]$ (full enumeration: 322,245 of 635,376 weight-4 errors fail), matching the measured 50.7%.

### 5.3 Next-to-leading order: the $\theta^{d+2}$ term

The layer $w_0 + 1$ produces the first subleading order. Its degeneracy is *cross-layer* with partners at weight $w_0 - 1$:

**Proposition 11 (Weight-$(2^r+1)$ degeneracy).** For $CSS(RM(r,m))$, the proportion of weight-$(2^r+1)$ errors with a partner at weight $2^r - 1$ is

$$P'_r(m) = \frac{\mathrm{flats}(m,r{+}1)\,\binom{2^{r+1}}{2^r{+}1}}{\binom{2^m}{2^r{+}1}},$$

with values $P'_2(6) = 0.08197$, $P'_2(7) = 0.0400$, $P'_2(8) = 0.01976$, $P'_2(9) = 9.82\times10^{-3}$, $P'_2(10) = 4.90\times10^{-3}$; $P'_3(8) = 3.26\times10^{-6}$, $P'_3(9) = 1.95\times10^{-7}$.

*Proof sketch.* A partner $\chi_B$ of $\chi_{A'}$ ($|A'| = 2^r + 1$, $|B| = 2^r - 1$) requires $\chi_{A'} \oplus \chi_B \in C^{\perp}$ of weight $d$, i.e. the product is an $(r+1)$-flat indicator with $A' \sqcup B = P$. Since $|A'| = 2^r + 1$ exceeds the size of any $r$-flat, the span of $A'$ is automatically $r+1$; the count is the flat count times the choices of $A'$ inside $P$. ∎

**Theorem 17 ($\theta^{d+2}$ next-to-leading order).** For an affine-complete code of even distance $d = 2^{r+1}$,

$$\mathrm{loss}(\theta) = c_d\,\theta^{d} + P'_r(m)\,\theta^{d+2} + o(\theta^{d+2}),$$

where $c_d$ is the coefficient of Theorem 14 and $P'_r(m)$ is given by Prop. 11.

*Proof sketch.* The weight-$(2^r+1)$ branch carries amplitude order $\theta^{2^r+1}$; on the degenerate fraction $P'_r(m)$ the minimal-weight decoder necessarily selects the weight-$(2^r - 1)$ partner (all lower weights are unique, and the partner class is the only match — the product with any weight-$\le 2^r$ error would have weight $d + 2 - 2|\cap|$ or $\ge 17$, absent from the $C^{\perp}$ weight spectrum, verified by 2000/2000 sampling for $[[256,70,16]]$). The residual is the flat indicator, a minimum-weight logical operator: certain failure, no $1/2$ factor. ∎

*Magnitudes.* For $r = 2$, $m = 6$: $c_{10} = 0.082$ vs. $c_8 = 0.507$ — the subleading term is visible; for $r = 3$, $m = 8$: $c_{18} = 3.3\times10^{-6}$ vs. $c_{16} \approx 5\times10^{-5}$ — essentially invisible. Large-distance codes are dominated ever more purely by $\theta^d$. The logical-$Z$ flip fraction at this order is $\kappa_r(m)$ (see Sec. 5.6), with measured values $0.367025$ for $[[64,20,8]]$ (full enumeration) matching the closed form.

### 5.4 Pauli-channel universality

The entire framework extends from coherent rotations to arbitrary independent per-qubit Pauli channels with no change to the failure rates:

**Theorem 18 (Pauli-channel universality).** Let the noise be an independent per-qubit Pauli channel with $X$-side error probability $\varepsilon$ (the probability that the error operator contains an $X$ or $Y$ component, i.e. flips the $X$-syndrome; $Z$ errors are invisible to the $X$-side). For a geometrically complete CSS code with minimal-weight decoding, the $X$-side decoding loss is

$$\mathrm{loss}(\varepsilon) = \sum_{w \ge w_0} C(n,w)\,\varepsilon^{w}(1-\varepsilon)^{n-w}\,\mathrm{fail}(w) = C(n,w_0)\,\varepsilon^{w_0}\,P(w_0)\,\mathrm{fail}(w_0) + C(n,w_0{+}1)\,\mathrm{fail}(w_0{+}1)\,\varepsilon^{w_0+1} + o(\varepsilon^{w_0+1}),$$

with the *same* $\mathrm{fail}(w)$ as in Theorem 13: the decoder is a deterministic function of syndrome and weight, and the channel is invisible to it. Indeed, the $X$-side action of $Y_i$ equals that of $X_i$ ($Y_i X_v = (-1)^{v_i} X_v Y_i$ flips the same $X$-syndrome bits), and $Z_i$ leaves the $X$-syndrome untouched.

*Proof.* The set of $X$-active errors $\mathcal{A} = \{i : e_i \in \{X_i, Y_i\}\}$ is independent per qubit with $P(|\mathcal{A}| = w) = C(n,w)\varepsilon^w(1-\varepsilon)^{n-w}$; conditioned on $\mathcal{A}$, the syndrome equals that of a pure $X$ injection, so the failure probability is $\mathrm{fail}(w)$; sum over $w$. ∎

**Channel constants.** The same formula covers all standard channels: coherent $\theta$-tilts have $\varepsilon = \sin^2(\theta/2)$ (Theorem 14 is the special case); depolarizing noise of rate $p$ has $\varepsilon = 2p/3$; phase damping (after Pauli twirl) has $\varepsilon = 0$ (pure $Z$); amplitude damping (after Pauli twirl) has $\varepsilon = \gamma/2$. *Boundary:* untwirled coherent non-Pauli processes (e.g. the raw amplitude-damping Kraus operator $K_1 = \sqrt{\gamma}|0\rangle\langle 1|$) respond probabilistically ($\pm 1$ with equal halves) rather than by deterministic syndrome flips, and fall outside the theorem; the standard Pauli-twirl experimental protocol brings them back inside.

*Verification* ($[[64,20,8]]$): (i) weight-4/5 layers with $X$/$Y$ mixtures (200,000 samples, equal halves) give failure rates exactly equal to pure-$X$ injection sample by sample; (ii) full enumeration gives $\mathrm{fail}(4) = 0.507172131$ (322,245/635,376) and $\mathrm{fail}(5) = 0.846994536$ (6,457,920/7,624,512); (iii) full depolarizing $p = 0.02$ (1,000,000 samples) gives measured loss $0.005944 \pm 0.000077$ vs. the closed form $\sum_{w\ge 4} C(64,w)(2p/3)^w(1-2p/3)^{64-w}\mathrm{fail}(w) = 0.005969$ (with $w \ge 6$ terms at $\mathrm{fail} \approx 0.85$ contributing $1.85\times10^{-4}$): agreement at $-0.33\sigma$.

### 5.5 Instantiation and verification

Table 2 lists the closed-form leading coefficients $c_d$ of Theorem 14 against numerical measurements. The formula column is evaluated with $\mathrm{fail}(w_0)$ from Theorem 15, $P(w_0)$ from Prop. 10 (AG) or $1/3$ (PG), and $w_0 = \lceil d/2\rceil$.

| Code | $d$ | Leading order | Closed-form $c_d$ | Numerical/experimental | Source |
|---|---|---|---|---|---|
| $[[7,1,3]]$ | 3 | $\theta^4$ | $\frac13 C(7,2)/144 = 0.0486$ | slope 4.12; fit $c \approx 0.10$ (same order) | [10.29] |
| $[[15,7,3]]$ | 3 | $\theta^4$ | $\frac13 C(15,2)/144 = 0.2431$ | slope 3.99; $315/945 = 1/3$ ✓ | [10.29,10.31] |
| $[[32,12,4]]$ | 4 | $\theta^4$ | $\frac{15}{16} C(32,2)/16 = 29.06$ | class size 16 (465 pairs $= 31\times15$) ✓ | [10.32] |
| $[[64,20,8]]$ | 8 | $\theta^8$ | $0.5072\, C(64,4)/256 = 1.26\times10^{3}$ | fail 48.5%/50.7%; slope 7.96 ✓ | [10.31] |
| $[[256,70,16]]$ | 16 | $\theta^{16}$ | $P_3(8)\cdot 0.5\, C(256,8)/2^{16} = 6.16\times10^{3}$ | $P_3(8) = 1.007\times10^{-4}$; measured $1.5\times10^{-4}$/ $1.2\times10^{-4}$ ✓ | [10.32,10.33] |
| $[[1024,1002,4]]$ | 4 | $\theta^4$ | $0.9980\, C(1024,2)/16 = 3.27\times10^{4}$ | rep. count 512; directional syndrome 1023 ✓ | [10.34] |
| $[[1024,912,8]]$ | 8 | $\theta^8$ | $0.5005\, C(1024,4)/256 = 8.90\times10^{7}$ | weight-4 full degeneracy; weight-5 cross-layer $0.004887$ ✓ | [10.34] |
| $[[1024,672,16]]$ | 16 | $\theta^{16}$ | $P_3(10)\,0.5\, C(1024,8)/2^{16} = 3.37\times10^{8}$ | weight-8 sampled $1.67\times10^{-6}$ ($0.9\sigma$) ✓ | [10.34] |
| $[[1024,252,32]]$ | 32 | $\theta^{32}$ | $P_4(10)\,0.5\, C(1024,16)/2^{32} = 2.45\times10^{8}$ | $m=6$ sampling 333 vs $310\pm18$ ($1.3\sigma$) ✓ | [10.34] |

*Notes.* (i) The $[[7,1,3]]$, $[[15,7,3]]$, $[[32,12,4]]$ rows use the uniform-$\theta$ protocol of [10.29]: averaging $\langle \theta^{2w}\rangle = \theta_{\max}^{2w}/(2w+1)$ inserts the factor $1/9 = (1/3)^2$ for the weight-2 branch, hence denominators $144 = 16 \cdot 9$; the remaining rows use the fixed-$\theta$ protocol of Theorem 14 with denominator $2^{2w_0}$. (ii) The logical-$Z$-flip version of the coefficient is $\kappa_r(m)$ times the decoding-failure version (Sec. 5.3), e.g. $[[32,12,4]]$: $29.06 \to 12.0$; $[[64,20,8]]$: $1.26\times10^3 \to 4.63\times10^2$; $[[1024,\cdot,4]]$: $3.27\times10^4 \to 1.23\times10^4$; $[[1024,\cdot,8]]$: $8.90\times10^7 \to 2.94\times10^7$; $[[1024,\cdot,16]]$: $3.37\times10^8 \to 1.05\times10^8$; $[[1024,\cdot,32]]$: $2.45\times10^8 \to 7.53\times10^7$; PG rows keep $\kappa = 1$. (iii) The non-CSS perfect code $[[5,1,3]]$ shows measured $c \approx 0.06$ vs. the branch-level value $C(5,2)/144 = 0.069$ of the same order — its mechanism is outside the geometric-completeness framework (open question).

The closed forms reproduce the measured slopes and failure rates across the entire family ladder $d = 3, 4, 8, 16, 32$ — nine codes, five distances, four orders of magnitude in $c_d$ — with no free parameters.
