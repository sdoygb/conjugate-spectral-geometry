"""Full-noise state-vector simulation of [[7,1,3]] / [[15,7,3]], recovery-channel version.

Protocol (reconstructed from 10.29 §3.1):
  - logical |0bar> = equal superposition of simplex codewords
  - per-qubit independent rotation U(theta_i), theta_i ~ U[0, theta_max],
    Pauli type P_i ~ uniform {X, Y, Z}
  - recovery-channel fidelity: F = sum_s |<0bar| R_s Pi_s |psi>|^2 over all syndromes s
    (equivalent to infinite measurement trials; single-shot measurement would
    sample the s ~ theta^2 detection path only ~0.3% of trials at theta_max=0.05)
  - loss L = 1 - F, averaged over injection trials

Precomputed matrix V (256 x 2^n) with columns v_s = Pi_s R_s^dag |0bar>:
  F = ||V^dag psi||^2.
"""
import numpy as np

def build_code(m):
    n = (1 << m) - 1
    H = np.zeros((m, n), dtype=int)
    for j in range(n):
        v = j + 1
        for i in range(m):
            H[i, j] = (v >> i) & 1
    words = []
    for mask in range(1 << m):
        w = np.zeros(n, dtype=int)
        for i in range(m):
            if (mask >> i) & 1:
                w ^= H[i]
        words.append(w)
    return n, H, np.array(words)

def logical_zero(words):
    n = len(words[0])
    psi = np.zeros(1 << n, dtype=complex)
    for w in words:
        idx = sum(int(w[j]) << j for j in range(n))
        psi[idx] = 1.0 / np.sqrt(len(words))
    return psi

def recovery_channel_matrix(n, m, H, words):
    """Columns v_s = Pi_s R_s^dag |0bar>, s = sx | (sz << m). Returns (V, perm, ph_z)."""
    psi0 = logical_zero(words)
    size = 1 << n
    idx = np.arange(size)
    perm = [idx ^ (1 << j) for j in range(n)]
    ph_z = [np.where((idx >> j) & 1, -1.0, 1.0) for j in range(n)]
    xmask = [sum(1 << j for j in range(n) if H[i, j]) for i in range(m)]
    xperm = [idx ^ xmask[i] for i in range(m)]
    xph = [np.where(np.bitwise_count(idx & xmask[i]) & 1, -1.0, 1.0) for i in range(m)]
    V = np.zeros(((1 << m) ** 2, size), dtype=complex)
    for sx in range(1 << m):
        for sz in range(1 << m):
            v = psi0.copy()
            if sx:                                    # R^dag Z part: Z_{sx-1}
                v = v * ph_z[sx - 1]
            if sz:                                    # R^dag X part: X_{sz-1}
                v = v[perm[sz - 1]]
            for i in range(m):                        # X-stabilizer projection (sx bits)
                s = -1.0 if (sx >> i) & 1 else 1.0
                v = (v + s * v[xperm[i]]) / 2.0
            for i in range(m):                        # Z-stabilizer projection (sz bits)
                s = -1.0 if (sz >> i) & 1 else 1.0
                v = (v + s * v * xph[i]) / 2.0
            V[sx + (sz << m)] = v
    return V, perm, ph_z

def run_sim2(n, psi0, V, perm, ph_z, theta_max, trials, seed=0):
    rng = np.random.default_rng(seed)
    L = 0.0
    for _ in range(trials):
        theta = rng.uniform(0, theta_max, n)
        ptype = rng.choice(['X', 'Y', 'Z'], n)
        psi = psi0.copy()
        for j in range(n):
            c, s = np.cos(theta[j] / 2), np.sin(theta[j] / 2)
            if ptype[j] == 'X':
                psi = c * psi + 1j * s * psi[perm[j]]
            elif ptype[j] == 'Z':
                psi = c * psi + 1j * s * (psi * ph_z[j])
            else:
                psi = c * psi - s * (psi * ph_z[j])[perm[j]]   # i*s*Y = -s*XZ
        F = np.linalg.norm(V @ psi) ** 2
        L += 1.0 - F
    return L / trials

def fit(theta_maxs, losses):
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
        psi0 = logical_zero(words)
        V, perm, ph_z = recovery_channel_matrix(n, m, H, words)
        print(f'{label}: V shape {V.shape}, memory {V.nbytes/1e6:.0f} MB')
        for trials in (30, 300):
            losses = [run_sim2(n, psi0, V, perm, ph_z, t, trials, seed=1000 + trials) for t in theta_maxs]
            b, c, cf = fit(theta_maxs, losses)
            print(f'  trials={trials}')
            print('    L      : ' + ' '.join(f'{L:.4e}' for L in losses))
            print(f'    slope  : {b:.3f}   c(log-log): {c:.4f}   c(L/t^4): '
                  + ' '.join(f'{v:.4f}' for v in cf) + f'   closed-form: {closed:.4f}')
