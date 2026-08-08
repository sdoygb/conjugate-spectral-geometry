"""Full-noise state-vector simulation of [[7,1,3]] and [[15,7,3]] CSS codes.

Protocol (aligned with 10.29 §3.1 / p2_layered_detection.py):
  - logical |0bar> = equal superposition of simplex-code codewords
  - per-qubit independent rotation U(theta_i), theta_i ~ U[0, theta_max],
    Pauli type P_i ~ uniform {X, Y, Z}
  - stabilizer projective measurements (X-stabilizers then Z-stabilizers) -> syndrome
  - CSS split minimum-weight recovery (X part from Z-syndrome, Z part from X-syndrome)
  - loss L = 1 - |<0bar|psi_final>|^2, averaged over trials
"""
import numpy as np

def build_code(m):
    """Hamming [[2^m-1, 2^m-1-2m, 3]] = CSS(simplex, simplex^T). H: m x (2^m-1)."""
    n = (1 << m) - 1
    H = np.zeros((m, n), dtype=int)
    for j in range(n):
        v = j + 1                      # column = binary of 1..n
        for i in range(m):
            H[i, j] = (v >> i) & 1
    words = []                         # simplex codewords = rowspace(H), 2^m words
    for mask in range(1 << m):
        w = np.zeros(n, dtype=int)
        for i in range(m):
            if (mask >> i) & 1:
                w ^= H[i]
        words.append(w)
    return n, H, np.array(words)

def logical_zero(words):
    """|0bar> = (1/sqrt(|C|)) sum_{v in C} |v>; qubit j <-> bit j of ket index."""
    n = len(words[0])
    psi = np.zeros(1 << n, dtype=complex)
    for w in words:
        idx = sum(int(w[j]) << j for j in range(n))
        psi[idx] = 1.0 / np.sqrt(len(words))
    return psi

def stabilizer_data(n, H):
    """For each stabilizer generator row: (v_mask scalar, perm array for X^v)."""
    size = 1 << n
    idx = np.arange(size)
    data = []
    for i in range(len(H)):
        v_mask = sum(1 << j for j in range(n) if H[i, j])
        data.append((v_mask, idx ^ v_mask))
    return data

def apply_rot(psi, j, theta, ptype, perm, ph_z):
    """U = cos(t/2) I + i sin(t/2) P_j, P_j from perm[..], ph_z[j] = (-1)^{bit_j}."""
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    if ptype == 'X':
        return c * psi + 1j * s * psi[perm[j]]
    if ptype == 'Z':
        return c * psi + 1j * s * (psi * ph_z[j])
    # Y = i X Z
    return c * psi + 1j * s * (1j * (psi * ph_z[j])[perm[j]])

def measure(psi, v_mask, perm_v, is_x, rng):
    """Projective measurement of X^v or Z^v; returns (new_psi, s) with s in {+1,-1}."""
    idx = np.arange(psi.size)
    if is_x:
        psix = psi[perm_v]
    else:
        ph = np.where(np.bitwise_count(idx & v_mask) & 1, -1.0, 1.0)
        psix = psi * ph
    # projector Pi_s = (I + s P)/2, branch probability p_s = ||Pi_s|psi>||^2
    p_plus = 0.25 * np.linalg.norm(psi + psix) ** 2
    p_minus = 0.25 * np.linalg.norm(psi - psix) ** 2
    s = 1 if rng.random() < p_plus / (p_plus + p_minus) else -1
    p_s = p_plus if s == 1 else p_minus
    out = (psi + s * psix) / (2.0 * np.sqrt(p_s))
    return out, s

def run_sim(n, H, words, theta_max, trials, seed=0):
    rng = np.random.default_rng(seed)
    psi0 = logical_zero(words)
    stab = stabilizer_data(n, H)
    size = 1 << n
    idx = np.arange(size)
    perm = [idx ^ (1 << j) for j in range(n)]          # X_j flip
    ph_z = [np.where((idx >> j) & 1, -1.0, 1.0) for j in range(n)]  # Z_j phase
    L = 0.0
    for _ in range(trials):
        theta = rng.uniform(0, theta_max, n)
        ptype = rng.choice(['X', 'Y', 'Z'], n)
        psi = psi0.copy()
        for j in range(n):
            psi = apply_rot(psi, j, theta[j], ptype[j], perm, ph_z)
        sx_bits = []                                   # Z-part syndrome (from X-meas)
        for v_mask, perm_v in stab:
            psi, s = measure(psi, v_mask, perm_v, is_x=True, rng=rng)
            sx_bits.append(s)
        sz_bits = []                                   # X-part syndrome (from Z-meas)
        for v_mask, perm_v in stab:
            psi, s = measure(psi, v_mask, perm_v, is_x=False, rng=rng)
            sz_bits.append(s)
        sz = sum((1 if s == -1 else 0) << i for i, s in enumerate(sz_bits))
        sx = sum((1 if s == -1 else 0) << i for i, s in enumerate(sx_bits))
        if sz:                                         # X error at bit sz-1 (Hamming col = sz)
            psi = psi[perm[sz - 1]]
        if sx:                                         # Z error at bit sx-1
            psi = psi * ph_z[sx - 1]
        F = abs(np.vdot(psi0, psi)) ** 2
        L += 1.0 - F
    return L / trials

def fit(theta_maxs, losses):
    """log-log linear fit: log L = b log theta + log c."""
    x = np.log(theta_maxs)
    y = np.log(losses)
    b, logc = np.polyfit(x, y, 1)
    c_fixed = [L / t ** 4 for L, t in zip(losses, theta_maxs)]
    return b, np.exp(logc), c_fixed

if __name__ == '__main__':
    theta_maxs = np.array([0.05, 0.1, 0.2, 0.4])
    for m, label, closed in [(3, '[[7,1,3]]', 7 / 9 * 21 / 144),
                             (4, '[[15,7,3]]', 7 / 9 * 105 / 144)]:
        n, H, words = build_code(m)
        for trials in (30, 300):
            losses = [run_sim(n, H, words, t, trials, seed=1000 + trials) for t in theta_maxs]
            b, c, cf = fit(theta_maxs, losses)
            print(f'{label}  trials={trials}')
            print('  L      : ' + ' '.join(f'{L:.3e}' for L in losses))
            print(f'  slope  : {b:.3f}   c(log-log): {c:.4f}   c(L/t^4): '
                  + ' '.join(f'{v:.4f}' for v in cf) + f'   closed-form: {closed:.4f}')
