"""功率谱统计量（移植官方基线实现，参数化 bin 结构）。"""

import numpy as np

PIXEL_ARCMIN = 2.0
SIGMA_NOISE = 0.4 / (2 * 30.0 * PIXEL_ARCMIN**2) ** 0.5  # 0.0258，与官方一致


def power_spectrum(x, pixsize_radian, kedge):
    """功率谱（含实 FFT 对称修正），返回 (k_avg, P(k))。

    移植自 wl_challenge/baseline_official.py，保证与官方基线逐位一致。
    """
    xk = np.fft.rfft2(x)
    xk2 = (xk * xk.conj()).real
    Nmesh = x.shape
    k = np.zeros((Nmesh[0], Nmesh[1] // 2 + 1))
    k += np.fft.fftfreq(Nmesh[0], d=pixsize_radian).reshape(-1, 1) ** 2
    k += np.fft.rfftfreq(Nmesh[1], d=pixsize_radian).reshape(1, -1) ** 2
    k = k**0.5 * 2 * np.pi
    index = np.searchsorted(kedge, k)
    power = np.bincount(index.flatten(), weights=xk2.flatten(), minlength=len(kedge) + 1)
    Nmode = np.bincount(index.flatten(), minlength=len(kedge) + 1)
    power_k = np.bincount(index.flatten(), weights=k.flatten(), minlength=len(kedge) + 1)
    if Nmesh[1] % 2 == 0:
        power += np.bincount(
            index[..., 1:-1].flatten(),
            weights=xk2[..., 1:-1].flatten(),
            minlength=len(kedge) + 1,
        )
        Nmode += np.bincount(index[..., 1:-1].flatten(), minlength=len(kedge) + 1)
        power_k += np.bincount(
            index[..., 1:-1].flatten(),
            weights=k[..., 1:-1].flatten(),
            minlength=len(kedge) + 1,
        )
    else:
        power += np.bincount(
            index[..., 1:].flatten(),
            weights=xk2[..., 1:].flatten(),
            minlength=len(kedge) + 1,
        )
        Nmode += np.bincount(index[..., 1:].flatten(), minlength=len(kedge) + 1)
        power_k += np.bincount(
            index[..., 1:].flatten(),
            weights=k[..., 1:].flatten(),
            minlength=len(kedge) + 1,
        )
    nz = Nmode > 0
    k_avg = np.zeros(len(kedge) + 1)
    P = np.zeros(len(kedge) + 1)
    k_avg[nz] = power_k[nz] / Nmode[nz]
    P[nz] = power[nz] / Nmode[nz]
    return k_avg[1:-1], P[1:-1]  # 去掉 DC 和越界 bin


def unpack_masked(kappa_flat, mask):
    """把 (..., 132019) 压缩像素解压为 (..., 1424, 176) 图。"""
    full = np.zeros(kappa_flat.shape[:-1] + mask.shape, np.float64)
    full[..., mask] = kappa_flat
    return full


def add_shape_noise(imgs, rng, sigma=SIGMA_NOISE):
    """形状噪声：高斯白噪声 × 掩模（与官方一致）。"""
    return imgs + rng.normal(0.0, sigma, imgs.shape)


def logPS(imgs, kedge, pixsize_radian):
    """批量功率谱：输入 (..., ny, nx) 图，输出 (..., nbin) log10 P。"""
    flat = imgs.reshape(-1, *imgs.shape[-2:])
    out = np.zeros((len(flat), len(kedge) - 2), np.float32)
    for j, im in enumerate(flat):
        _, P = power_spectrum(im, pixsize_radian, kedge)
        out[j] = np.log10(P + 1e-30)
    return out.reshape(imgs.shape[:-2] + (len(kedge) - 2,))
