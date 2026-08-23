import sys, time
sys.path.insert(0, '/tmp/chromobius_src/src')
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/qec-geometry')
import numpy as np
from clorco._make_circuit_params import Params, gen
from clorco.color_code._keyed_constructions import make_named_color_code_constructions
import chromobius
import qecgeo.error_geometry as eg

def make_circuit(d, p, rounds=3):
    params = Params(style='phenom', rounds=rounds, diameter=d, noise_strength=p,
                    noise_model=gen.NoiseModel.uniform_depolarizing(p),
                    debug_out_dir=None, convert_to_cz=False, editable_extras=False)
    return make_named_color_code_constructions()['phenom_color_code'](params)

def unpack_bp(dets_bp, n_det):
    return np.unpackbits(dets_bp, axis=1, bitorder='little')[:, :n_det].astype(np.uint8)

configs = [(3, 0.005, 200000), (5, 0.005, 500000), (7, 0.005, 2000000)]
for d, p, shots in configs:
    t0 = time.time()
    circuit = make_circuit(d, p)
    dem = circuit.detector_error_model(decompose_errors=False)
    decoder = chromobius.compile_decoder_for_dem(dem)
    sampler = circuit.compile_detector_sampler(seed=42)
    dets_bp, obs_bp = sampler.sample(shots, separate_observables=True, bit_packed=True)
    preds_bp = decoder.predict_obs_flips_from_dets_bit_packed(dets_bp)
    le = np.any(preds_bp != obs_bp, axis=1)
    pL = float(le.mean())
    dets = unpack_bp(dets_bp, circuit.num_detectors)
    coords = eg.get_detector_coords(circuit)
    st = eg.analyze_error_structure(dets, coords, le)
    o, e = st['ok'], st['err']
    # 码宽（格坐标）
    xs = [round(c[0]) for c in coords.values()]
    ys = [round(c[1]) for c in coords.values()]
    wx, wy = max(xs) - min(xs), max(ys) - min(ys)
    print(f"d={d} 码宽(格): x={wx} y={wy}  pL={pL:.5f} nA1={e['n']} nA0={o['n']}  t={time.time()-t0:.1f}s", flush=True)
    print(f"   A0: exc_med={o.get('exc_med')} diam_med={o.get('diam_med')} diam_q90={o.get('diam_q90')} "
          f"cross={o.get('cross_rate')} bdry_med={o.get('bdry_med')} cluster_med={o.get('cluster_med')}")
    print(f"   A1: exc_med={e.get('exc_med')} diam_med={e.get('diam_med')} diam_q90={e.get('diam_q90')} "
          f"cross={e.get('cross_rate')} bdry_med={e.get('bdry_med')} cluster_med={e.get('cluster_med')}")
    # 标度律候选量
    if o.get('diam_med') is not None and e.get('diam_med') is not None:
        print(f"   Δdiam_med = {e['diam_med'] - o['diam_med']:.2f}   Δdiam_q90 = {e['diam_q90'] - o['diam_q90']:.2f}")
    print(flush=True)
