#!/usr/bin/env python3
"""

CORRECTED ANALYSIS with rigorous scientific factors - FINAL VERSION
Isolates the impact of extreme VDISP with rigorous methodology

SCIENTIFIC SOURCES:
- Correction factors: DESI-SDSS Analysis (Nov 13, 2025) - Equations 6, 7, 8
- ΛCDM null hypothesis: Desjacques et al. 2018, Planck Collaboration 2018
- LRG galaxy bias: Zheng et al. 2009, Tojeiro et al. 2014
- Malmquist bias: Ross et al. 2012
- Faber-Jackson relation: Faber & Jackson 1976
- SDSS samples: Eisenstein et al. 2001, Strauss et al. 2002
- Bispectrum definition: Bernardeau et al. 2002, Jeong & Komatsu 2010
"""

import numpy as np
import json
import sys
from datetime import datetime
from scipy import stats

print("🚀 SDSS HIGH_MASS ANALYSIS: IMPACT OF EXTREME VDISP (FINAL VERSION)")
print("=" * 70)

# --- RIGOROUS CONFIGURATION - BASED ON DESI-SDSS ANALYSIS ---
INPUT_FILE_SDSS = "sdss_vdisp_calidad.npz"
VDISP_CUTOFF = 350.0  # km/s - to isolate extreme galaxies
SAMPLE_SIZE = 500
N_VALIDATION_SAMPLES = 80
l_max = 8
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]

# RIGOROUS CORRECTION FACTORS (DESI-SDSS Analysis, Equations 6, 7, 8)
FACTOR_MASA = 5.263  # Correction for mass evolution (Malmquist bias)
FACTOR_BIAS = 1.493  # Correction for bias evolution: (2.4/2.1)³ (Zheng et al. 2009)
FACTOR_CORRECCION_RIGUROSO = FACTOR_MASA * FACTOR_BIAS  # = 7.856×
H0_TEST_RIGUROSO = 1.1  # ΛCDM - maximum expected evolution (Desjacques et al. 2018)

# Redshift bins for SDSS (consistent with DESI-SDSS analysis)
bins_redshift_sdss = [('z01_02', 0.1, 0.2), ('z07_08', 0.7, 0.8)]

def justificar_parametros_rigurosos():
    """Documents the scientific justification for all parameters"""

    print("\n📚 JUSTIFICATION OF RIGOROUS PARAMETERS:")
    print("=" * 50)
    print("🔬 CORRECTION FACTORS (DESI-SDSS Analysis):")
    print(f"    • Mass factor: {FACTOR_MASA}× (Malmquist bias - Ross et al. 2012)")
    print(f"    • Bias factor: {FACTOR_BIAS}× (bias: 2.1→2.4 - Zheng et al. 2009)")
    print(f"    • Total factor: {FACTOR_CORRECCION_RIGUROSO:.3f}×")
    print(f"🔬 NULL HYPOTHESIS (ΛCDM):")
    print(f"    • H₀ = {H0_TEST_RIGUROSO} (maximum expected evolution - Desjacques et al. 2018)")
    print(f"🔬 SDSS CONFIGURATION:")
    print(f"    • Extreme VDISP threshold: {VDISP_CUTOFF} km/s")
    print(f"    • Redshift bins: {bins_redshift_sdss}")
    print(f"🔬 BISPECTRUM DEFINITION:")
    print(f"    • Scalene configurations: {configs_escalenas}")
    print(f"    • l_max: {l_max} (Bernardeau et al. 2002)")

try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded for fast bispectrum calculation.")
except ImportError:
    print("❌ Rust module not available.")
    sys.exit()

def cargar_datos_sdss():
    """Loads and validates SDSS data with robust error handling"""

    try:
        data_sdss = np.load(INPUT_FILE_SDSS)
        vdisp_sdss = data_sdss['VDISP']
        redshift_sdss = data_sdss['Z']

        print(f"✅ SDSS loaded: {len(vdisp_sdss):,} galaxies")
        print(f"📊 VDISP range: {vdisp_sdss.min():.1f} to {vdisp_sdss.max():.1f} km/s")
        print(f"📊 Z range: {redshift_sdss.min():.3f} to {redshift_sdss.max():.3f}")

        # Apply common quality filter (Strauss et al. 2002)
        VDISP_MIN_CALIDAD = 150.0
        mask_calidad = vdisp_sdss >= VDISP_MIN_CALIDAD
        vdisp_sdss_calidad = vdisp_sdss[mask_calidad]
        redshift_sdss_calidad = redshift_sdss[mask_calidad]

        print(f"🔧 VDISP filter > {VDISP_MIN_CALIDAD} km/s: {len(vdisp_sdss_calidad):,} galaxies")

        return vdisp_sdss_calidad, redshift_sdss_calidad

    except FileNotFoundError:
        print(f"❌ Error: {INPUT_FILE_SDSS} not found.")
        sys.exit()
    except Exception as e:
        print(f"❌ Error loading SDSS data: {e}")
        sys.exit()

def calcular_evolucion_rigurosa(vdisp_data, redshift_data, label, bins_redshift):
    """Calculates evolution with rigorous methodology"""
    print(f"\n--- RIGOROUS CALCULATION: {label} ---")

    galaxies_z_low = None
    galaxies_z_high = None

    # Separate by redshift bins
    for label_z, z_min, z_max in bins_redshift:
        mask = (redshift_data >= z_min) & (redshift_data < z_max)
        vdisp_bin = vdisp_data[mask]

        if len(vdisp_bin) > 0:
            print(f"    📊 {label_z}: {len(vdisp_bin):,} galaxies")

        if len(vdisp_bin) < SAMPLE_SIZE:
            print(f"    ⚠️  {label_z}: Only {len(vdisp_bin):,} galaxies (need {SAMPLE_SIZE})")
            continue

        if 'z01_02' in label_z:
            galaxies_z_low = vdisp_bin
            print(f"    🔵 z={z_min}-{z_max}: {len(vdisp_bin):,} galaxies")
        elif 'z07_08' in label_z:
            galaxies_z_high = vdisp_bin
            print(f"    🔴 z={z_min}-{z_max}: {len(vdisp_bin):,} galaxies")

    if galaxies_z_low is not None and galaxies_z_high is not None:
        n_samples_max = min(N_VALIDATION_SAMPLES,
                            len(galaxies_z_low) // SAMPLE_SIZE,
                            len(galaxies_z_high) // SAMPLE_SIZE)

        if n_samples_max == 0:
             print("    ❌ Insufficient data for non-replacement sampling.")
             return np.nan, 0.0, np.nan

        print(f"    🔄 Generating {n_samples_max} samples of {SAMPLE_SIZE} galaxies...")

        indices_low = np.random.permutation(len(galaxies_z_low))
        indices_high = np.random.permutation(len(galaxies_z_high))
        evolutions = []

        for i in range(n_samples_max):
            start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
            sample_low = galaxies_z_low[indices_low[start:end]].tolist()
            sample_high = galaxies_z_high[indices_high[start:end]].tolist()

            bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_escalenas)
            bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_escalenas)

            if bispectra_high and bispectra_low:
                avg_high = np.mean([abs(b) for b in bispectra_high])
                avg_low = np.mean([abs(b) for b in bispectra_low])
                evol_esc = avg_high / avg_low if avg_low > 0 else np.nan
                evolutions.append(evol_esc)

        evolutions = np.array(evolutions)
        evolutions = evolutions[~np.isnan(evolutions)]

        if len(evolutions) > 1:
            obs_mean = np.mean(evolutions)
            obs_std = np.std(evolutions, ddof=1)
            n_obs = len(evolutions)
            obs_sem = obs_std / np.sqrt(n_obs)

            # APPLY RIGOROUS CORRECTION (DESI-SDSS Analysis)
            evol_corregida = obs_mean * FACTOR_CORRECCION_RIGUROSO

            # T-statistic with rigorous H₀ (Desjacques et al. 2018)
            t = abs(obs_mean - H0_TEST_RIGUROSO) / obs_sem
            p = 2 * (1 - stats.t.cdf(t, n_obs-1))
            sigma = stats.norm.ppf(1 - p/2)
            if np.isinf(sigma): sigma = t

            print(f"    📈 OBS Evolution: {obs_mean:.3f}× ± {obs_sem:.3f}")
            print(f"    🔥 CORR Evolution: {evol_corregida:.3f}×")
            print(f"    🌟 Significance vs ΛCDM: {sigma:.2f}σ")

            return obs_mean, sigma, evol_corregida
        else:
            print("    ❌ No valid evolutions obtained")
            return np.nan, 0.0, np.nan

    print("    ❌ Could not calculate evolution (insufficient data in both bins).")
    return np.nan, 0.0, np.nan

def main():
    # Justify scientific parameters
    justificar_parametros_rigurosos()

    # Load SDSS data (Eisenstein et al. 2001)
    vdisp_sdss_calidad, redshift_sdss_calidad = cargar_datos_sdss()

    # 1. ANALYSIS WITH THE COMPLETE SDSS HIGH_MASS SAMPLE
    CORTE_ALTA_MASA_SDSS = 262.0  # Based on natural SDSS percentiles

    mask_alta_masa = vdisp_sdss_calidad >= CORTE_ALTA_MASA_SDSS
    vdisp_alta_masa = vdisp_sdss_calidad[mask_alta_masa]
    redshift_alta_masa = redshift_sdss_calidad[mask_alta_masa]

    print(f"\n🎯 SDSS HIGH MASS SELECTION:")
    print(f"    • Cutoff: VDISP > {CORTE_ALTA_MASA_SDSS:.1f} km/s")
    print(f"    • High Mass Galaxies: {len(vdisp_alta_masa):,}")
    print(f"    • High Mass VDISP Range: {vdisp_alta_masa.min():.1f} - {vdisp_alta_masa.max():.1f} km/s")

    evol_completa_obs, sig_completa, evol_completa_corr = calcular_evolucion_rigurosa(
        vdisp_alta_masa, redshift_alta_masa,
        "SDSS COMPLETE HIGH_MASS", bins_redshift_sdss
    )

    # 2. ANALYSIS WITH EXTREME VDISP FILTER
    mask_filtrada = vdisp_alta_masa <= VDISP_CUTOFF
    vdisp_filtrado = vdisp_alta_masa[mask_filtrada]
    redshift_filtrado = redshift_alta_masa[mask_filtrada]

    n_filtradas = np.sum(~mask_filtrada)
    print(f"\n🗑️ EXCLUDED GALAXIES (VDISP > {VDISP_CUTOFF:.1f} km/s): {n_filtradas:,} galaxies")
    print(f"    • Remaining: {len(vdisp_filtrado):,} galaxies")

    if n_filtradas > 0:
        print(f"    • Maximum VDISP excluded: {vdisp_alta_masa[~mask_filtrada].max():.1f} km/s")

    # Recalculate evolution with filtered sample
    evol_filtrada_obs, sig_filtrada, evol_filtrada_corr = calcular_evolucion_rigurosa(
        vdisp_filtrado, redshift_filtrado,
        f"SDSS FILTERED HIGH_MASS (VDISP <= {VDISP_CUTOFF:.1f} km/s)",
        bins_redshift_sdss
    )

    # 3. RIGOROUS COMPARISON AND CONCLUSION
    print(f"\n\n🚨 RIGOROUS CONCLUSION: IMPACT OF EXTREME VDISP")
    print("=" * 70)

    if not np.isnan(evol_completa_obs) and not np.isnan(evol_filtrada_obs):
        print(f"📊 OBSERVED RESULTS:")
        print(f"    • COMPLETE SDSS: {evol_completa_obs:.3f}× ({sig_completa:.2f}σ vs ΛCDM)")
        print(f"    • FILTERED SDSS: {evol_filtrada_obs:.3f}× ({sig_filtrada:.2f}σ vs ΛCDM)")

        print(f"\n📊 CORRECTED (RIGOROUS) RESULTS:")
        print(f"    • COMPLETE SDSS: {evol_completa_corr:.3f}×")
        print(f"    • FILTERED SDSS: {evol_filtrada_corr:.3f}×")

        # Calculate percentage impact
        impacto_obs = (evol_completa_obs - evol_filtrada_obs) / evol_filtrada_obs * 100
        impacto_corr = (evol_completa_corr - evol_filtrada_corr) / evol_filtrada_corr * 100

        print(f"\n🎯 IMPACT ANALYSIS:")
        print(f"    • Observed Inflation: {impacto_obs:+.1f}%")
        print(f"    • Corrected Inflation: {impacto_corr:+.1f}%")

        if evol_filtrada_obs > 0 and evol_completa_obs > evol_filtrada_obs:
            print(f"\n    🔍 PRINCIPAL FINDING:")
            print(f"      • VDISP > {VDISP_CUTOFF:.1f} km/s galaxies INFLATE the signal")
            print(f"      • REAL Signal (filtered): {evol_filtrada_corr:.3f}×")
            print(f"      • INFLATED Signal ( complete): {evol_completa_corr:.3f}×")

            # Rigorous comparison with DESI (DESI-SDSS Analysis)
            DESI_HIGH_MASS_CORRECTED = 10.299
            print(f"\n    📊 RIGOROUS SDSS/DESI COMPARISON:")
            print(f"      • Filtered SDSS (corrected): {evol_filtrada_corr:.3f}×")
            print(f"      • DESI High Mass (corrected): ~{DESI_HIGH_MASS_CORRECTED}×")
            print(f"      • SDSS/DESI Ratio: {evol_filtrada_corr/DESI_HIGH_MASS_CORRECTED:.2f}×")

            if abs(evol_filtrada_corr - DESI_HIGH_MASS_CORRECTED) < 2.0:
                print(f"      ✅ HIGH CONSISTENCY between SDSS and DESI")
            else:
                print(f"      ⚠️  Significant SDSS/DESI difference")

        elif evol_filtrada_obs > 0 and evol_completa_obs < evol_filtrada_obs:
            print(f"\n    🔍 UNEXPECTED RESULT:")
            print(f"      • Extreme galaxies SUPPRESS the signal")
            print(f"      • Impact: {abs(impacto_obs):.1f}% reduction")
        else:
            print(f"\n    ⚠️  Ambiguous result - verify data")
    else:
        print("    ❌ Could not calculate both evolutions for comparison")

    # Save RIGOROUS results
    output = {
        'configuracion_rigurosa': {
            'dataset_sdss': INPUT_FILE_SDSS,
            'corte_alta_masa_sdss': CORTE_ALTA_MASA_SDSS,
            'vdisp_cutoff_extremo': VDISP_CUTOFF,
            'factor_correccion_total': FACTOR_CORRECCION_RIGUROSO,
            'factor_masa': FACTOR_MASA,
            'factor_bias': FACTOR_BIAS,
            'h0_test_riguroso': H0_TEST_RIGUROSO,
            'bins_redshift_sdss': bins_redshift_sdss,
            'referencias': {
                'factores_correccion': 'DESI-SDSS Analysis (Nov 13, 2025)',
                'h0_cdm': 'Desjacques et al. 2018',
                'bias_lrg': 'Zheng et al. 2009, Tojeiro et al. 2014',
                'sesgo_malmquist': 'Ross et al. 2012',
                'muestras_sdss': 'Eisenstein et al. 2001, Strauss et al. 2002',
                'definicion_bispectro': 'Bernardeau et al. 2002, Jeong & Komatsu 2010'
            }
        },
        'estadisticas_muestras': {
            'sdss_total_calidad': int(len(vdisp_sdss_calidad)),
            'sdss_alta_masa_completa': int(len(vdisp_alta_masa)),
            'galaxias_excluidas_extremas': int(n_filtradas),
            'sdss_alta_masa_filtrada': int(len(vdisp_filtrado))
        },
        'resultados_rigurosos': {
            'sdss_alta_masa_completa': {
                'evolution_obs': float(evol_completa_obs) if not np.isnan(evol_completa_obs) else None,
                'evolution_corr': float(evol_completa_corr) if not np.isnan(evol_completa_corr) else None,
                'significance_vs_lcdm': float(sig_completa)
            },
            'sdss_alta_masa_filtrada': {
                'evolution_obs': float(evol_filtrada_obs) if not np.isnan(evol_filtrada_obs) else None,
                'evolution_corr': float(evol_filtrada_corr) if not np.isnan(evol_filtrada_corr) else None,
                'significance_vs_lcdm': float(sig_filtrada)
            }
        },
        'analisis_impacto': {
            'impacto_porcentual_obs': float(impacto_obs) if not np.isnan(evol_completa_obs) and not np.isnan(evol_filtrada_obs) else None,
            'impacto_porcentual_corr': float(impacto_corr) if not np.isnan(evol_completa_obs) and not np.isnan(evol_filtrada_obs) else None,
            'galaxias_extremas_inflan_señal': bool(evol_completa_obs > evol_filtrada_obs) if not np.isnan(evol_completa_obs) and not np.isnan(evol_filtrada_obs) else None,
            'consistencia_sdss_desi': bool(abs(evol_filtrada_corr - 10.299) < 2.0) if not np.isnan(evol_filtrada_corr) else None
        },
        'timestamp': datetime.now().isoformat()
    }

    filename = 'ANALISIS_VDISP_EXTREMO_SDSS_RIGUROSO.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n✅ RIGOROUS Results saved in '{filename}'.")

if __name__ == "__main__":
    main()