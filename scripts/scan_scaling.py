import sys, time
sys.path.insert(0, '/tmp/chromobius_src/src')
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/qec-geometry')
import numpy as np
import stim
import pymatching
from clorco._make_circuit_params import Params, gen
from clorco.color_code._keyed_constructions import make_named_color_code_constructions
import chromobius
import qecgeo.error_geometry as eg

def make_circuit(d, p, rounds=3):
    params = Params(
        style='phenom', rounds=rounds, diameter=d,
        noise_strength=p,
        noise_model=gen.NoiseModel.uniform_depolarizing(p),
        debug_out_dir=None, convert_to_cz=False, editable_extras=False,
    )
    return make_named_color_code_constructions()['phenom_color_code'](params)

def unpack_bp(dets_bp, n_det):
    return np.unpackbits(dets_bp, axis=1, bitorder='little')[:, :n_det].astype(np.uint8)

# p=0.005 低噪声（标度律标准），shots 按码距分配保证 A1 样本量
configs = [(3, 0.005, 120000), (5, 0.005, 300000), (7, 0.005, 2000000)]
results = []
for d, p, shots in configs:
    t0 = time.time()
    circuit = make_circuit(d, p)
    dem = circuit.detector_error_model(decompose_errors=False)
    matching = pymatching.Matching.from_detector_error_model(dem)
    decoder = chromobius.compile_decoder_for_dem(dem)
    sampler = circuit.compile_detector_sampler(seed=42)
    dets_bp, obs_bp = sampler.sample(shots, separate_observables=True, bit_packed=True)
    preds_bp = decoder.predict_obs_flips_from_dets_bit_packed(dets_bp)
    le = np.any(preds_bp != obs_bp, axis=1)
    pL = float(le.mean())
    n_A1 = int(le.sum())
    dets = unpack_bp(dets_bp, circuit.num_detectors)
    coords = eg.get_detector_coords(circuit)
    st = eg.analyze_error_structure(dets, coords, le)
    # A0 抽样上限 30000（中位数统计足够）；A1 全量
    st2 = eg.analyze_edges(dets, matching, coords, le, max_ok_samples=30000)
    a0td = st2['ok'].get('total_dist_med')
    a1td = st2['err'].get('total_dist_med')
    a0q90 = st2['ok'].get('total_dist_q90')
    a1q90 = st2['err'].get('total_dist_q90')
    cr0 = st['ok'].get('cross_rate', 0)
    cr1 = st['err'].get('cross_rate', 0)
    cl0 = st['ok'].get('cluster', 0)
    cl1 = st['err'].get('cluster', 0)
    row = dict(d=d, p=p, pL=pL, n_A1=n_A1, unpaired=st2.get('unpaired', 0),
               A0_td=a0td, A1_td=a1td,
               delta=(a1td - a0td) if a0td is not None and a1td is not None else None,
               A0_q90=a0q90, A1_q90=a1q90,
               delta_q90=(a1q90 - a0q90) if a1q90 is not None and a0q90 is not None else None,
               cross_lift=(cr1 / cr0) if cr0 and cr0 > 0 else None,
               cluster_lift=(cl1 / cl0) if cl0 and cl0 > 0 else None,
               t_sec=round(time.time() - t0, 1))
    results.append(row)
    print(row, flush=True)

print("\n=== 色码标度律 (p=0.005) ===")
for r in results:
    print(f"d={r['d']}: A1_td(med)={r['A1_td']}, A0_td(med)={r['A0_td']}, Δ_med={r['delta']}, "
          f"Δ_q90={r['delta_q90']}, pL={r['pL']:.5f}, nA1={r['n_A1']}, unpaired={r['unpaired']}, "
          f"cross_lift={r['cross_lift']:.2f}, cluster_lift={r['cluster_lift']:.2f}")
