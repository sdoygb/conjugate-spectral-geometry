import numpy as np
from scipy.integrate import solve_ivp

# ============================================================
# Parameters from 0.14 §5.3
# ============================================================
lambda1_eff = 391.05        # rad^-2
lambda2_eff = 59324.3       # rad^-2  (from Delta_lambda = 58933.25 = 59324.3 - 391.05)
I5 = 3.43e12                # inertia at s=0 (N5)
N5 = 1.2e8
N6 = 1.35e8                 # N6 = N5 * 9/8
N7_M7_Neff = 2.7e8          # N_eff at N7 saturation (N5 * 2.25)

s6 = np.log(N6 / N5)        # = ln(9/8) = 0.11778
s7 = np.log(N7_M7_Neff / N5)  # = ln(2.25) = 0.81093

print(f"s6 = {s6:.6f}")
print(f"s7 = {s7:.6f}")

def I_of(s):
    return I5 * np.exp(s)

def dI_ds(s):
    return I5 * np.exp(s)   # I'(s) = I(s) for I = I5 * e^s

def dV_ds(s):
    return lambda2_eff - lambda1_eff * np.exp(-s)

def V_of(s):
    return lambda2_eff * s + lambda1_eff * np.exp(-s)

print(f"\nV(0)  = {V_of(0):.2f}")
print(f"V(s6) = {V_of(s6):.2f}")
print(f"V(s7) = {V_of(s7):.2f}")
print(f"dV/ds at s=0  = {dV_ds(0):.2f}")
print(f"dV/ds at s=s6 = {dV_ds(s6):.2f}")
print(f"dV/ds at s=s7 = {dV_ds(s7):.2f}")

# ============================================================
# Energy conservation approach
# E = (1/2) * I(s) * (s')^2 + V(s) = const
# s' = sqrt(2*(E - V(s)) / I(s))
# We need initial condition: s'(0) at s=0
# 
# From article: "current at beginning of phase III at N5 level"
# We need to know the initial velocity. Let's try several values.
# 
# Actually, let's use the fact that the system has been evolving
# from N1 to N5. But we don't have exact s'(0).
#
# Let's instead integrate the ODE directly with reasonable IC.
# ============================================================

# Try the initial velocity that makes the system just reach N7
# E = V(s7)  → at N7, velocity approaches 0
E_just_N7 = V_of(s7)
s0_dot_just_N7 = np.sqrt(2 * (E_just_N7 - V_of(0)) / I5)
print(f"\nIf just reaching N7 (E=V(s7)):")
print(f"  s'(0) = {s0_dot_just_N7:.6e}")

# Try 2x that energy
E_2x = V_of(0) + 2 * (E_just_N7 - V_of(0))
s0_dot_2x = np.sqrt(2 * (E_2x - V_of(0)) / I5)
print(f"  s'(0) = {s0_dot_2x:.6e} (2x E_diff)")

# ============================================================
# Direct ODE integration of equation (0.14.7):
# I(s) * s'' + (1/2)*I'(s)*(s')^2 + dV/ds = 0
# → s'' = -[(1/2)*I'(s)*(s')^2 + dV/ds] / I(s)
# State vector: y = [s, s']
# ============================================================

def ode(tau, y):
    s, sdot = y
    I = I_of(s)
    Ip = dI_ds(s)
    Vp = dV_ds(s)
    sddot = -(0.5 * Ip * sdot**2 + Vp) / I
    return [sdot, sddot]

# Event: s reaches s6
def event_s6(tau, y):
    return y[0] - s6
event_s6.terminal = True
event_s6.direction = 1

def event_s7(tau, y):
    return y[0] - s7
event_s7.terminal = True
event_s7.direction = 1

# ============================================================
# Scenario 1: Just reach N7 (most conservative)
# ============================================================
print("\n" + "="*70)
print("SCENARIO 1: Just reaching N7 (E = V(s7), s'(s7) → 0)")
print("="*70)

# Actually this doesn't make sense — if E = V(s7), s'(s7) = 0
# but s increases from 0, so E must be > V(s7) to have finite speed at N7.
# E = V(s7) means infinite time to reach N7 (approaches asymptotically).
# So let's use a different approach: use the "current speed" estimate.

# From the article text: "our universe has undergone such a long expansion phase
# (about 13.8 Gyr) to reach the beginning of the current phase III"
# This suggests the age ~ 13.8 Gyr corresponds to reaching N5.
# 
# But we need s'(0). Let's use an alternative:
# The article mentions in §5.3.1 that dη/dτ = 1/sqrt(lambda1_eff).
# 
# Let me try to estimate from the age of universe.
# Actually, we don't have a direct τ-to-time conversion.
#
# Let's just report the answer in τ-units first,
# then also try to convert using the Hubble time.

# ============================================================
# Let's use a reasonable benchmark: s'(0) such that the system
# has climbed from some reference point.
#
# Better: the article says ℐ5 ≈ 3.43e12 is huge, evolution is very slow.
# Let's just use energy conservation to compute Δτ.
# ============================================================

# Energy integral: τ = ∫ ds / s'(s) = ∫ ds * sqrt(I(s) / (2*(E - V(s))))
# Use scipy quad for precise integration.

from scipy.integrate import quad

def tau_to_s(s_end, E, s_start=0):
    """Compute τ to go from s_start to s_end."""
    integrand = lambda s: np.sqrt(I_of(s) / (2.0 * (E - V_of(s))))
    result, error = quad(integrand, s_start, s_end)
    return result

# We need E. Let's try a physically reasonable value.
# The article says the system "reaches" N5 at current epoch.
# If phase III just started, s'(0) should be positive but small.
#
# Let me try: assume the kinetic energy at s=0 equals some fraction
# of the potential difference V(s7)-V(0).
# Try multiple values.

dV_total = V_of(s7) - V_of(0)
print(f"\nΔV from N5 to N7 = {dV_total:.2f}")

# Scenario A: KE at s=0 = 10% of ΔV_total
ke_fracs = [0.01, 0.1, 0.5, 1.0, 2.0, 10.0]
print(f"\n{'KE frac':>10} {'E':>15} {'s\\'(0)':>12} {'τ(N5→N6)':>15} {'τ(N5→N7)':>15} {'τ(N6→N7)':>15}")
print("-" * 90)

for frac in ke_fracs:
    KE0 = frac * dV_total
    E = V_of(0) + KE0
    s0_dot = np.sqrt(2 * KE0 / I5)
    tau6 = tau_to_s(s6, E)
    tau7 = tau_to_s(s7, E)
    print(f"{frac:>10.2f} {E:>15.2f} {s0_dot:>12.4e} {tau6:>15.4e} {tau7:>15.4e} {tau7-tau6:>15.4e}")

# ============================================================
# Now let's try to convert τ to physical time.
# dη/dτ = 1/sqrt(lambda1_eff)  →  dτ/dη = sqrt(lambda1_eff)
# But we need η-to-t conversion.
# 
# From §5.3.1: Γ = 3H * dη/dτ = 3H / sqrt(lambda1_eff)
# and H = c * sqrt(Λ_res/3), t_H = 1/H ≈ 1.42e10 yr
#
# But Γ is damping for the Ψ-equation, not directly the s-evolution.
#
# The relation between outer time τ and physical time t:
# We need to check article 0.13 more carefully.
# 
# For now, let's just give the answer in τ-units and note the conversion.
# ============================================================

print("\n" + "="*70)
print("CONVERSION TO PHYSICAL TIME")
print("="*70)

# From §5.2: t_H = sqrt(3/Λ_res)/c ≈ 1.42e10 yr
# dη/dτ = 1/sqrt(lambda1_eff) = 1/sqrt(391.05) ≈ 0.05057
# But η vs t relationship is not directly given.
# 
# In conformal time: dt = a(η) dη / c... but this is the η of causal field.
#
# Let's just use: if the system took ~ t_H to evolve to N5,
# then τ(N1→N5) ~ some value, and we can estimate τ-time scaling.
#
# Actually this is too speculative. Let's just report in τ-units.

# ============================================================
# Try the ODE integration approach to verify
# ============================================================
print("\n" + "="*70)
print("ODE VERIFICATION (KE frac = 0.1)")
print("="*70)

frac = 0.1
KE0 = frac * dV_total
E = V_of(0) + KE0
s0_dot = np.sqrt(2 * KE0 / I5)

t_span = (0, 2e12)
y0 = [0.0, s0_dot]

sol = solve_ivp(ode, t_span, y0, events=[event_s6, event_s7], 
                method='RK45', rtol=1e-10, atol=1e-14, max_step=1e9)

print(f"Final t = {sol.t[-1]:.4e}")
print(f"Final s = {sol.y[0][-1]:.6f}")
print(f"Final s' = {sol.y[1][-1]:.6e}")

if len(sol.t_events[0]) > 0:
    print(f"τ to N6 = {sol.t_events[0][0]:.4e}")
if len(sol.t_events[1]) > 0:
    print(f"τ to N7 = {sol.t_events[1][0]:.4e}")

# Verify energy conservation
E_final = 0.5 * I_of(sol.y[0][-1]) * sol.y[1][-1]**2 + V_of(sol.y[0][-1])
print(f"E_initial = {E:.6f}")
print(f"E_final   = {E_final:.6f}")
print(f"Relative error = {abs(E_final - E) / E:.2e}")
