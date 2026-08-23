import numpy as np
from galpy.potential import Potential, MWPotential2014, vcirc
from galpy.orbit import Orbit

VO, RO = 220.0, 8.0
T_NAT = 0.03556  # Gyr per natural time unit (ro/vo)
G = 4.30091e-6   # (km/s)^2 kpc/Msun
A0_SI = 1.2e-10  # m/s^2
A0 = A0_SI/3.2408e-14   # -> (km/s)^2/kpc  = 3702.8
M_BARY = 7.24e10        # Msun (MWPotential2014 bulge+disk)
AMP = G*M_BARY/(VO**2*RO)   # natural units
A0_NAT = A0*RO/VO**2        # natural units

class MilgromA2(Potential):
    """8.18 interpolation: g_M = sqrt(g_N^2 + g_N*a0), spherical baryonic mass."""
    def __init__(self, amp=AMP, a0=A0_NAT):
        Potential.__init__(self, amp=amp, ro=RO, vo=VO)
        self._a0 = a0
    def _Rforce(self, R, z, phi=0.0, t=0.0):
        if R <= 0:
            return 0.0
        r2 = R*R + z*z
        r = np.sqrt(r2)
        gN = self._amp/r2
        gM = np.sqrt(gN*gN + gN*self._a0)
        return -gM*R/r
    def _zforce(self, R, z, phi=0.0, t=0.0):
        if R <= 0:
            return 0.0
        r2 = R*R + z*z
        r = np.sqrt(r2)
        gN = self._amp/r2
        gM = np.sqrt(gN*gN + gN*self._a0)
        return -gM*z/r

POT_M = MilgromA2()
POT_L = MWPotential2014

def apo_of(vT, peri, pot, ts_apo):
    o = Orbit([peri, 0.0, vT, 0.0, 0.0, 0.0])
    o.integrate(ts_apo, pot, method="odeint")
    return np.max(o.R(ts_apo))

def find_vT(peri, apo_target, pot):
    vc = vcirc(pot, peri, use_physical=False)  # natural units
    lo, hi = 0.3*vc, 1.3*vc
    ts_apo = np.linspace(0.0, 90.0, 1200)  # 3.2 Gyr
    f_lo = apo_of(lo, peri, pot, ts_apo)
    f_hi = apo_of(hi, peri, pot, ts_apo)
    # safety: if target outside bracket, widen
    for _ in range(4):
        if f_lo > apo_target:
            lo *= 0.8; f_lo = apo_of(lo, peri, pot, ts_apo)
        if f_hi < apo_target:
            hi *= 1.2; f_hi = apo_of(hi, peri, pot, ts_apo)
    for _ in range(12):
        mid = 0.5*(lo+hi)
        f_mid = apo_of(mid, peri, pot, ts_apo)
        if f_mid < apo_target:
            lo = mid
        else:
            hi = mid
    return 0.5*(lo+hi)

def run_orbit(name, peri, apo, pot):
    vT = find_vT(peri, apo, pot)
    o = Orbit([peri, 0.0, vT, 0.0, 0.0, 0.0])
    ts = np.linspace(0.0, 6.0/T_NAT, 6001)  # 6 Gyr
    o.integrate(ts, pot, method="odeint")
    R = o.R(ts); vR = o.vR(ts); phi = o.phi(ts)
    cross = np.where((vR[:-1] < 0) & (vR[1:] >= 0))[0]
    idx = cross + 1
    if len(idx) < 4:
        return (name, None)
    dphi = np.diff(phi[idx])
    dphi = (dphi + np.pi) % (2*np.pi) - np.pi   # precession per orbit (rad), retrograde < 0
    T_orb = np.diff(ts[idx])*T_NAT
    prec_orb = np.degrees(dphi)
    return (name, dict(vT=vT*VO, peri=peri, apo=apo,
                       prec_orbit=float(np.mean(prec_orb)),
                       prec_std=float(np.std(prec_orb)),
                       prec_Gyr=float(np.mean(prec_orb/T_orb)),
                       T_orb=float(np.mean(T_orb)),
                       n_orbits=len(idx)-1))

ORBITS = [
    ("GD-1", 13.8, 22.3),
    ("Pal5", 9.5, 19.5),
    ("Helmi", 14.0, 28.0),
]

print("=== MOND (a^2=a_N^2+a_N*a0, M_bary=7.24e10 Msun, r_t=9.17 kpc) ===")
for name, peri, apo in ORBITS:
    res = run_orbit(name, peri, apo, POT_M)
    if res[1] is None:
        print(f"{name}: FAILED")
    else:
        d = res[1]
        print(f"{name}: vT={d['vT']:.1f} km/s  peri={d['peri']:.1f} apo={d['apo']:.1f} kpc  "
              f"T={d['T_orb']:.3f} Gyr  precession={d['prec_orbit']:+.2f} deg/orbit "
              f"({d['prec_Gyr']:+.1f} deg/Gyr, std={d['prec_std']:.2f}, n={d['n_orbits']})")

print("=== LCDM (MWPotential2014) ===")
for name, peri, apo in ORBITS:
    res = run_orbit(name, peri, apo, POT_L)
    if res[1] is None:
        print(f"{name}: FAILED")
    else:
        d = res[1]
        print(f"{name}: vT={d['vT']:.1f} km/s  peri={d['peri']:.1f} apo={d['apo']:.1f} kpc  "
              f"T={d['T_orb']:.3f} Gyr  precession={d['prec_orbit']:+.2f} deg/orbit "
              f"({d['prec_Gyr']:+.1f} deg/Gyr, std={d['prec_std']:.2f}, n={d['n_orbits']})")
