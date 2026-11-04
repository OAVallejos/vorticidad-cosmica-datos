#!/usr/bin/env python3
"""                           ACSyD_v20_healpix_fkp.py      ============================  V20: Expansion to L_MAX=25 + Robust Jackknife (N_JK=20)          - Dynamic generation of ~860 triangle configurations up to L_MAX=25.
     - Post-processing filter: ℓ_eff ≤ 25 AND |Q| ≤ 5 (Updated Option A).
     - Robust Jackknife with 20 regions (Option C).
     - Q = B_net / (C_l_net)^{1.5}
"""
import numpy as np
import json
import sys
from datetime import datetime
from pathlib import Path
import healpy as hp
import h5py

try:
    from cosmic_vorticity import calcular_bispectro_fkp
    print("✅ Rust Kernel V19/V20 loaded.")
except ImportError:
    print("❌ Rust kernel not available.")
    sys.exit(1)

print("=" * 80)
print("V20: Expansion to L_MAX=25 + Outlier filter (A) + Robust Jackknife (C)")
print("=" * 80)

# =============================================================================
# V20 CONFIGURATION
# =============================================================================
L_MAX = 25          # V20: Expanded from 15 to 25
NSIDE = 64
P0_FKP = 1e4
N_JK = 20           # Option C: Jackknife with 20 regions
VDISP_MIN_CALIDAD = 150.0
H0_TEST = 1.1

# Option A V20: Updated filter thresholds
L_EFF_MAX = 25.0    # V20: Expanded from 15.0 to 25.0 to leverage the new range
Q_ABS_MAX = 5.0     # Kept to suppress cosmic variance outliers

SDSS_CUTS = (207.9, 262.2)
DESI_CUTS = (200.0, 250.0)


def generar_configuraciones_triangulos(l_max: int):
    """
    Dynamically generates all valid triangle configurations up to l_max.
    Applies strict triangle inequality and even parity filter (l1+l2+l3 even).
    For L_MAX=25, this generates ~860 configurations, solving the "small N" problem.
    """
    configs = []
    for l1 in range(2, l_max + 1):
        for l2 in range(l1, l_max + 1):
            for l3 in range(l2, l_max + 1):
                # Strict triangle inequality
                if l3 <= l1 + l2:
                    # Parity filter (l1 + l2 + l3 must be even)
                    if (l1 + l2 + l3) % 2 == 0:
                        configs.append((l1, l2, l3))
    return configs

# Dynamically generate configurations
configs_triangulos = generar_configuraciones_triangulos(L_MAX)

# Safety validation
for cfg in configs_triangulos:
    if max(cfg) > L_MAX:
        raise ValueError(f"Configuration {cfg} exceeds L_MAX={L_MAX}")

PARITY_MASK = np.array([(l1 + l2 + l3) % 2 == 0 for (l1, l2, l3) in configs_triangulos])
L_EFF_ARRAY = np.array([(l1 + l2 + l3) / 3.0 for (l1, l2, l3) in configs_triangulos])
L_EFF_MASK = L_EFF_ARRAY <= L_EFF_MAX

print(f"📐 Total configurations generated: {len(configs_triangulos)}")
print(f"   Configurations with valid parity: {PARITY_MASK.sum()}")
print(f"   Configurations with ℓ_eff ≤ {L_EFF_MAX}: {L_EFF_MASK.sum()}")
print(f"   Initial valid configurations (parity + ℓ_eff): {(PARITY_MASK & L_EFF_MASK).sum()}")
print(f"   🔧 N_JK = {N_JK} (Option C)")

bins_redshift_sdss = [('z01_02', 0.1, 0.2), ('z07_08', 0.7, 0.8)]
bins_redshift_desi = [('z04_06', 0.4, 0.6), ('z08_10', 0.8, 1.0)]


# =============================================================================
# a_lm ADAPTER
# =============================================================================
def alm_healpy_a_kernel(alm_healpy, l_max):
    n_kernel = (l_max + 1) ** 2
    modos_re = np.zeros(n_kernel, dtype=np.float64)
    modos_im = np.zeros(n_kernel, dtype=np.float64)
    for l in range(l_max + 1):
        for m in range(-l, l + 1):
            idx_kernel = l * l + (l + m)
            if m >= 0:
                idx_hp = hp.Alm.getidx(l_max, l, abs(m))
                modos_re[idx_kernel] = np.real(alm_healpy[idx_hp])
                modos_im[idx_kernel] = np.imag(alm_healpy[idx_hp])
            else:
                idx_hp_pos = hp.Alm.getidx(l_max, l, abs(m))
                a_neg = ((-1) ** abs(m)) * np.conj(alm_healpy[idx_hp_pos])
                modos_re[idx_kernel] = np.real(a_neg)
                modos_im[idx_kernel] = np.imag(a_neg)
    return modos_re.tolist(), modos_im.tolist()


# =============================================================================
# FKP FIELD
# =============================================================================
def construir_campo_fkp(ra_data, dec_data, ra_rand, dec_rand, nside, weights_fkp_path, nbar_survey):
    n_pix = hp.nside2npix(nside)
    pix_g = hp.ang2pix(nside, np.radians(90.0 - np.asarray(dec_data, dtype=np.float64)), np.radians(np.asarray(ra_data, dtype=np.float64)))
    pix_r = hp.ang2pix(nside, np.radians(90.0 - np.asarray(dec_rand, dtype=np.float64)), np.radians(np.asarray(ra_rand, dtype=np.float64)))

    n_g = np.zeros(n_pix, dtype=np.float64)
    n_r = np.zeros(n_pix, dtype=np.float64)
    np.add.at(n_g, pix_g, 1.0)
    np.add.at(n_r, pix_r, 1.0)

    N_g, N_r = n_g.sum(), n_r.sum()
    if N_g <= 0 or N_r <= 0:
        raise ValueError(f"N_g={N_g} N_r={N_r} empty")

    alpha = N_g / N_r
    w_fkp_val = 1.0 / (1.0 + nbar_survey * P0_FKP)

    if Path(weights_fkp_path).exists():
        w_map = hp.read_map(str(weights_fkp_path))
    else:
        w_map = (n_g + n_r > 0).astype(np.float64)
    good = w_map > 0

    F = np.where(good, w_map * w_fkp_val * (n_g - alpha * n_r), 0.0)
    return F, alpha


def cargar_randoms(dataset_name, grupo_lower, bin_z):
    path_prod = Path(f"randoms/{dataset_name.lower()}_{grupo_lower}_{bin_z}_produccion.h5")
    path_base = Path(f"randoms/{dataset_name.lower()}_{grupo_lower}_{bin_z}.h5")
    path = path_prod if path_prod.exists() else path_base
    if not path.exists():
        raise FileNotFoundError(f"No randoms at {path}")
    with h5py.File(path, 'r') as f:
        keys = list(f.keys())
        ra_k = next(k for k in keys if k.upper() == 'RA')
        dec_k = next(k for k in keys if k.upper() == 'DEC')
        return f[ra_k][:], f[dec_k][:]


# =============================================================================
# JACKKNIFE
# =============================================================================
def jackknife_regions(nside, n_jk=20):
    npix = hp.nside2npix(nside)
    nside_jk = max(1, int(2 ** np.floor(np.log2(nside / np.sqrt(n_jk)))))
    theta, phi = hp.pix2ang(nside, np.arange(npix))
    pix_jk = hp.ang2pix(nside_jk, theta, phi)
    unique = np.unique(pix_jk)
    if len(unique) > n_jk:
        bins = np.array_split(unique, n_jk)
        mapping = {u: j for j, b in enumerate(bins) for u in b}
        pix_jk = np.array([mapping[u] for u in pix_jk])
    return pix_jk


def jackknife_bispectro_y_Cl(ra, dec, ra_r, dec_r, nside, w_path, nbar, n_jk=20):
    pix_data = hp.ang2pix(nside, np.radians(90.0 - np.asarray(dec, dtype=np.float64)), np.radians(np.asarray(ra, dtype=np.float64)))
    pix_jk = jackknife_regions(nside, n_jk)

    # V19/V20: Calibrated empirical normalization factor
    factor_norm = 1e-4
    n_bar_rust = 1.0

    B_samples, Cl_net_samples = [], []

    for j in range(n_jk):
        mask = pix_jk[pix_data] != j
        if mask.sum() < 100:
            continue
        try:
            F_data, alpha = construir_campo_fkp(ra[mask], dec[mask], ra_r, dec_r, nside, w_path, nbar)
            # V20: lmax is now 25, capturing all modes
            alm_data = hp.map2alm(F_data, lmax=L_MAX)
            re_d, im_d = alm_healpy_a_kernel(alm_data, L_MAX)
            Cl_data = np.asarray(hp.alm2cl(alm_data, lmax=L_MAX), dtype=np.float64)

            F_rand, _ = construir_campo_fkp(ra_r, dec_r, ra_r, dec_r, nside, w_path, nbar)
            alm_rand = hp.map2alm(F_rand, lmax=L_MAX)
            re_r, im_r = alm_healpy_a_kernel(alm_rand, L_MAX)
            Cl_rand = np.asarray(hp.alm2cl(alm_rand, lmax=L_MAX), dtype=np.float64)

            # V20: The ~860 configurations are passed to the Rust kernel
            B_net = calcular_bispectro_fkp(re_d, im_d, re_r, im_r, L_MAX, configs_triangulos, factor_norm, n_bar_rust)

            Cl_net_raw = Cl_data - (alpha ** 2) * Cl_rand
            Cl_net = np.maximum(Cl_net_raw * np.sqrt(factor_norm), 1e-30)

            B_samples.append(B_net)
            Cl_net_samples.append(Cl_net)
        except Exception as e:
            print(f"     [JK ERROR] j={j}: {type(e).__name__}: {e}")
            continue

    if len(B_samples) < 3:
        return None, None, None, None, len(B_samples)

    B_arr, Cl_arr = np.array(B_samples), np.array(Cl_net_samples)
    return (np.nanmean(B_arr, axis=0), np.nanstd(B_arr, axis=0, ddof=1) / np.sqrt(len(B_arr)),
            np.nanmean(Cl_arr, axis=0), np.nanstd(Cl_arr, axis=0, ddof=1) / np.sqrt(len(Cl_arr)),
            len(B_samples))


# =============================================================================
# Q = B / (C1·C2·C3)^{1/2}
# =============================================================================
def calcular_Q(B_mean, Cl_mean):
    Q = np.zeros_like(B_mean)
    for i, (l1, l2, l3) in enumerate(configs_triangulos):
        denom = np.sqrt(Cl_mean[l1] * Cl_mean[l2] * Cl_mean[l3])
        Q[i] = B_mean[i] / denom if denom > 1e-30 else np.nan
    return Q

def propagar_error_Q(B_mean, B_sem, Cl_mean, Cl_sem):
    Q = calcular_Q(B_mean, Cl_mean)
    Q_sem = np.zeros_like(Q)
    for i, (l1, l2, l3) in enumerate(configs_triangulos):
        if np.isnan(Q[i]) or abs(Q[i]) < 1e-30:
            Q_sem[i] = np.nan
            continue
        rel_B = (B_sem[i] / B_mean[i]) ** 2 if abs(B_mean[i]) > 1e-30 else 0
        rel_C = 0.25 * ((Cl_sem[l1]/Cl_mean[l1])**2 + (Cl_sem[l2]/Cl_mean[l2])**2 + (Cl_sem[l3]/Cl_mean[l3])**2)
        Q_sem[i] = abs(Q[i]) * np.sqrt(max(0, rel_B + rel_C))
    return Q, Q_sem


# =============================================================================
# OPTION A: OUTLIER FILTER
# =============================================================================
def aplicar_filtro_outliers(Q_l, Q_h, Qs_l, Qs_h, parity_mask, l_eff_mask, q_abs_max=5.0):
    """
    Applies the Option A filter (V20):
    1. Valid parity (l1+l2+l3 even)
    2. ℓ_eff ≤ 25 (V20: expanded)
    3. |Q| ≤ 5 at both redshifts
    """
    q_mask_l = np.abs(Q_l) <= q_abs_max
    q_mask_h = np.abs(Q_h) <= q_abs_max

    # Combine all masks
    signal_mask = parity_mask & l_eff_mask & q_mask_l & q_mask_h

    return signal_mask


# =============================================================================
# MAIN ANALYSIS
# =============================================================================
def ejecutar_analisis(vdisp_full, redshift_full, ra_full, dec_full, mass_groups, dataset_name, bins_redshift, f_sky):
    resultados = {}
    for group_name, (vdisp_min, vdisp_max, label_masa) in mass_groups.items():
        print(f"\n--- {dataset_name}: {label_masa} ({vdisp_min:.1f}-{vdisp_max:.1f} km/s) ---")
        mask_g = (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)
        v_g = vdisp_full[mask_g]
        z_g = redshift_full[mask_g]
        ra_g = ra_full[mask_g]
        dec_g = dec_full[mask_g]

        limit_up = np.percentile(v_g, 99.5)
        mclean = v_g < limit_up
        v_g, z_g, ra_g, dec_g = v_g[mclean], z_g[mclean], ra_g[mclean], dec_g[mclean]
        print(f"    Galaxies post-cleaning: {len(v_g):,}")

        gal_low = gal_high = None
        ra_low = ra_high = dec_low = dec_high = None
        nbar_low = nbar_high = 0.0
        z_bin_low = z_bin_high = (0, 0)
        bin_low = bin_high = ""

        for label_z, z_min, z_max in bins_redshift:
            mask_z = (z_g >= z_min) & (z_g < z_max)
            gal_bin = v_g[mask_z]
            if len(gal_bin) < 100:
                continue

            grupo_lower = label_masa.lower()
            path_randoms = Path(f"randoms/{dataset_name.lower()}_{grupo_lower}_{label_z}_produccion.h5")
            if not path_randoms.exists():
                continue

            nbar_sv = 1e-4

            if (dataset_name == "SDSS" and 'z01_02' in label_z) or (dataset_name == "DESI" and 'z04_06' in label_z):
                gal_low, ra_low, dec_low = gal_bin, ra_g[mask_z], dec_g[mask_z]
                bin_low, nbar_low, z_bin_low = label_z, nbar_sv, (z_min, z_max)
                print(f"      🔵 {label_z}: {len(gal_bin):,}")
            elif (dataset_name == "SDSS" and 'z07_08' in label_z) or (dataset_name == "DESI" and 'z08_10' in label_z):
                gal_high, ra_high, dec_high = gal_bin, ra_g[mask_z], dec_g[mask_z]
                bin_high, nbar_high, z_bin_high = label_z, nbar_sv, (z_min, z_max)
                print(f"      🔴 {label_z}: {len(gal_bin):,}")

        if gal_low is None or gal_high is None:
            continue

        grupo_lower = label_masa.lower()
        try:
            ra_r_low, dec_r_low = cargar_randoms(dataset_name, grupo_lower, bin_low)
            ra_r_high, dec_r_high = cargar_randoms(dataset_name, grupo_lower, bin_high)
        except Exception as e:
            print(f"    ❌ {e}")
            continue

        w_low = Path(f"weights_fkp/{dataset_name.lower()}_{grupo_lower}_{bin_low}_produccion_weights.fits")
        w_high = Path(f"weights_fkp/{dataset_name.lower()}_{grupo_lower}_{bin_high}_produccion_weights.fits")

        print(f"    🔄 Jackknife LOW ({N_JK} regions)...")
        B_l, Bs_l, Cl_l, Cls_l, n_l = jackknife_bispectro_y_Cl(ra_low, dec_low, ra_r_low, dec_r_low, NSIDE, w_low, nbar_low, N_JK)
        print(f"    🔄 Jackknife HIGH ({N_JK} regions)...")
        B_h, Bs_h, Cl_h, Cls_h, n_h = jackknife_bispectro_y_Cl(ra_high, dec_high, ra_r_high, dec_r_high, NSIDE, w_high, nbar_high, N_JK)

        if B_l is None or B_h is None:
            continue

        Q_l, Qs_l = propagar_error_Q(B_l, Bs_l, Cl_l, Cls_l)
        Q_h, Qs_h = propagar_error_Q(B_h, Bs_h, Cl_h, Cls_h)

        print(f"    [CFG] Q_low  (first 10) = {np.round(Q_l[:10], 4)}")
        print(f"    [CFG] Q_high (first 10) = {np.round(Q_h[:10], 4)}")

        # Option A: Apply outlier filter
        signal_mask = aplicar_filtro_outliers(Q_l, Q_h, Qs_l, Qs_h, PARITY_MASK, L_EFF_MASK, Q_ABS_MAX)
        print(f"    [FILTER A] valid configs: {signal_mask.sum()} / {len(configs_triangulos)}")

        # Show which configurations were filtered (max 10 examples)
        if signal_mask.sum() < len(configs_triangulos):
            filtradas = np.where(~signal_mask)[0]
            print(f"    [FILTER A] Examples of filtered configurations:")
            for idx in filtradas[:10]:
                cfg = configs_triangulos[idx]
                l_eff = L_EFF_ARRAY[idx]
                q_l = Q_l[idx]
                q_h = Q_h[idx]
                razon = []
                if not PARITY_MASK[idx]:
                    razon.append("odd parity")
                if not L_EFF_MASK[idx]:
                    razon.append(f"ℓ_eff={l_eff:.1f}>{L_EFF_MAX}")
                if abs(q_l) > Q_ABS_MAX:
                    razon.append(f"|Q_low|={abs(q_l):.2f}>{Q_ABS_MAX}")
                if abs(q_h) > Q_ABS_MAX:
                    razon.append(f"|Q_high|={abs(q_h):.2f}>{Q_ABS_MAX}")
                print(f"      idx={idx:3d} {cfg} ℓ_eff={l_eff:.1f} Q=[{q_l:.2f}, {q_h:.2f}] → {', '.join(razon)}")
            if len(filtradas) > 10:
                print(f"      ... and {len(filtradas) - 10} more")

        if signal_mask.sum() == 0:
            print(f"    ⚠️  No valid configurations after filter")
            continue

        evol = Q_h[signal_mask] / Q_l[signal_mask]
        err_ratio = np.sqrt((Qs_h[signal_mask]/Q_h[signal_mask])**2 + (Qs_l[signal_mask]/Q_l[signal_mask])**2)
        evol_err = np.abs(evol) * err_ratio
        sigma_per = np.abs(evol - H0_TEST) / evol_err
        valid_sigma = sigma_per[np.isfinite(sigma_per)]
        sigma = float(np.nanmax(valid_sigma)) if len(valid_sigma) else 0.0
        sigma_comb = float(np.sqrt(np.nansum(sigma_per[np.isfinite(sigma_per)]**2))) if len(valid_sigma) else 0.0

        resultados[label_masa] = {
            'evolution_Q_mean': float(np.nanmean(evol)),
            'evolution_Q_sem': float(np.nanmean(evol_err)),
            'significance_max': sigma,
            'significance_combined': sigma_comb,
            'N_jk_valid': n_l,
            'N_configs_valid': int(signal_mask.sum()),
            'N_configs_total': len(configs_triangulos),
            'N_configs_filtradas': int((~signal_mask).sum()),
            'Q_low_array': [float(x) if np.isfinite(x) else 0.0 for x in Q_l],
            'Q_high_array': [float(x) if np.isfinite(x) else 0.0 for x in Q_h],
            'filtro_aplicado': {
                'l_eff_max': L_EFF_MAX,
                'q_abs_max': Q_ABS_MAX,
                'n_jk': N_JK
            }
        }
        print(f"    📈 Q Evolution: {resultados[label_masa]['evolution_Q_mean']:.3f}× ± {resultados[label_masa]['evolution_Q_sem']:.3f} | σ_max: {sigma:.2f} | σ_comb: {sigma_comb:.2f}")

    return resultados


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("📥 Loading datasets...")
    try:
        d_sdss = np.load('data/sdss_vdisp_calidad.npz')
        print(f"✅ SDSS: {len(d_sdss['VDISP']):,}")
    except Exception as e:
        print(f"❌ SDSS: {e}"); return

    try:
        from astropy.table import Table
        t_desi = Table.read('data/DATASET_LRG_VDISP_FLUXR_FINAL.fits')
        print(f"✅ DESI: {len(t_desi):,}")
    except Exception as e:
        print(f"❌ DESI: {e}"); return

    print("\n🔄 SDSS V20...")
    mg_sdss = {"LOW": (VDISP_MIN_CALIDAD, SDSS_CUTS[0], 'BAJA_MASA'), "MID": (SDSS_CUTS[0], SDSS_CUTS[1], 'MEDIA_MASA'), "HIGH": (SDSS_CUTS[1], 800.0, 'ALTA_MASA')}
    res_sdss = ejecutar_analisis(d_sdss['VDISP'], d_sdss['Z'], d_sdss['RA'], d_sdss['DEC'], mg_sdss, "SDSS", bins_redshift_sdss, 0.25)

    print("\n🔄 DESI V20...")
    mg_desi = {"LOW": (VDISP_MIN_CALIDAD, DESI_CUTS[0], 'MEDIA_MASA'), "MID": (DESI_CUTS[0], DESI_CUTS[1], 'MEDIA_MASA'), "HIGH": (DESI_CUTS[1], 480.0, 'ALTA_MASA')}
    res_desi = ejecutar_analisis(np.array(t_desi['VDISP']), np.array(t_desi['Z']), np.array(t_desi['RA']), np.array(t_desi['DEC']), mg_desi, "DESI", bins_redshift_desi, 0.34)

    print("\n" + "="*80)
    print("V20 SUMMARY: REDUCED Q WITH FILTER (A) + ROBUST JACKKNIFE (C) + L_MAX=25")
    print("="*80)
    for name, res in [("SDSS", res_sdss), ("DESI", res_desi)]:
        print(f"\n {name}:")
        if not res:
            print("    (no results)")
            continue
        for grupo, r in res.items():
            print(f"    {grupo:>12}: Q_evol = {r['evolution_Q_mean']:6.3f}× ± {r['evolution_Q_sem']:.3f} | "
                  f"σ_max={r['significance_max']:5.2f} | σ_comb={r['significance_combined']:5.2f} | "
                  f"N_cfg={r['N_configs_valid']}/{r['N_configs_total']} (filtered: {r['N_configs_filtradas']})")

    out = {
        'version': 'V20',
        'metrica': 'Q = B_net / (C_l_net)^{1.5} (Empirical normalization factor_norm=1e-4)',
        'L_MAX': L_MAX,
        'N_configs': len(configs_triangulos),
        'configs': [list(c) for c in configs_triangulos],
        'resultados_sdss': res_sdss,
        'resultados_desi': res_desi,
        'filtro_config': {
            'opcion_A': {
                'l_eff_max': L_EFF_MAX,
                'q_abs_max': Q_ABS_MAX,
                'descripcion': 'Filters configurations with ℓ_eff > 25 OR |Q| > 5'
            },
            'opcion_C': {
                'n_jk': N_JK,
                'descripcion': 'Jackknife with 20 regions to reduce statistical error'
            }
        },
        'timestamp': datetime.now().isoformat()
    }
    with open('ROBUSTEZ_V20_Q_REDUCIDO.json', 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\n✅ ROBUSTEZ_V20_Q_REDUCIDO.json saved")

if __name__ == "__main__":
    main()