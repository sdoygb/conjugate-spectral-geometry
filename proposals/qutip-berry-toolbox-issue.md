# [Feature Request] Parameter-space Berry curvature / Chern number toolbox with gauge-consistency test suite

> 目标仓库：QuTiP（qutip/qutip）
> 草案日期：2026-08-14
> 状态：测试用例已数值验证，待发布

---

## Problem

QuTiP has excellent tools for time evolution, steady states, and Bloch-sphere
visualization, but no unified numerical interface for geometric (Berry)
quantities over a parameter space: Berry phase, connection, curvature, and
Chern number. This is a recurring user need — see the QuTiP Google Group
thread "Help computing Berry phase, connection and curvature". Users today
hand-roll discretization schemes (Fukui–Hatsugai–Suzuki on a k-mesh,
Stokes/Wilson-loop methods) with no standard way to verify gauge fixing, mesh
convergence, or global consistency. `qutip-lattice` covers lattice models but
does not expose a general parameter-space geometric toolkit; stand-alone
packages such as `pyqula` implement Berry quantities but are tied to
tight-binding lattice structures.

## Proposed feature

A small, dependency-light module (e.g. `qutip.berry`, or a `qutip-geometry`
community package) that takes a parameterized Hamiltonian `H(θ)` plus a
parameter-space mesh and returns gauge-invariant outputs:

1. **Abelian case**: Berry connection A(θ), Berry curvature F(θ) on a
   2-torus / 2-sphere mesh; Chern number C = (1/2π) ∫ F with integer
   quantization check.
2. **Non-abelian case**: multi-band (degenerate-subspace) Berry curvature via
   the projector method (Kato), trace / Chern character.
3. **Gauge-fixing strategy**: parallel-transport gauge or projector-based
   gauge-free formulation, so users never manipulate raw eigenstate phases.
4. **Built-in consistency tests**:
   - quantization: C computed independently by FHS lattice formula and
     Stokes/Wilson loop must agree and be integer within tolerance;
   - gauge invariance: outputs invariant under local U(1) re-gauging;
   - **zero-sum constraint test**: for Hamiltonians whose parameter space
     decomposes into sectors with a global constraint Σ_s ∫ F_s = 0 (the
     discrete analogue of multi-band sum rules such as the Nielsen–Ninomiya
     total-Chern-number constraint), the tool verifies the sum to machine
     precision — a strong end-to-end test that catches mesh errors and gauge
     errors simultaneously.

## Test cases

We are happy to contribute a reference implementation together with these
test cases:

1. **Two-level monopole** (standard): H(θ,φ) = −(sinθ cosφ σ₁ + sinθ sinφ σ₂
   + cosθ σ₃) on S² (inverted monopole, so the occupied lower band carries
   C = +1) — validates basic correctness against the analytic result.
2. **Three-sector zero-sum**: three distinct parameter-space sectors whose
   lower-band Chern numbers are individually non-zero and sum to zero:
   - Sector A: inverted monopole on S², C = +1
   - Sector B: Qi–Wu–Zhang model H = sin k₁ σ₁ + sin k₂ σ₂ +
     (1 − cos k₁ − cos k₂) σ₃ on T², C = +1
   - Sector C: double-cover QWZ H = sin 2k₁ σ₁ + sin k₂ σ₂ +
     (−1 − cos 2k₁ − cos k₂) σ₃ on T², C = −2
   
   The *global* constraint (+1) + (+1) + (−2) = 0 is the only invariant, so
   this exercises the zero-sum machinery end to end.
3. **Degenerate-band non-abelian**: two nearly degenerate bands on a 2-torus,
   validating the projector method against the abelian limit away from
   degeneracies.

## Scope questions for maintainers

- Would this fit better in `qutip` core, in `qutip-lattice`, or as a new
  community package under the QuTiP org?
- Preferred mesh/discretization conventions (FHS vs Wilson loop) for the API?

## Willing to contribute

Yes — we can open a draft PR with the module skeleton + tests within a few
weeks of scope agreement.

---

## 内部备注（不随 issue 发布）

- 零和测试用例的动机在 CSG 中是扇区结构零和 S_M + S_C + S_I = 0（0.7），对外包装为
  Nielsen–Ninomiya 型总能带陈数零和——主流物理语言，无身份暴露。
- 三扇区零和已数值验证（`proposals/qutip_berry_zerosum_test.py`，2026-08-14）：
  - N = 16/32/64/128 全配置下 A = +1.000000000000、B = +1.000000000000、
    C = −2.000000000000，均精确到 12 位小数；
  - 零和 A+B+C ~ 10⁻¹⁵（机器精度）；
  - 随机局域 U(1) 相位扰动下陈数差 2.2×10⁻¹⁶，规范不变性通过。
- 脚本是纯 NumPy 参考实现，验证的是 FHS 公式与测试用例数学本身；
  PR 阶段再包 Qobj 接口并带入 CSG 具体数值资产；issue 阶段不提身份、不提文章编号。
- 发布前提醒：维护者可能追问扇区 C 双覆盖模型的动机——回答口径："winding-2 map is
  the simplest way to get a non-trivial |C|>1 sector without touching degeneracies"，
  纯工程理由，不涉理论。
