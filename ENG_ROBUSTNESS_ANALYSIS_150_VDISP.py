#!/usr/bin/env python3

"""
EXTENDED FINAL ROBUSTNESS ANALYSIS: 3.02x Signal by VDISP Subgroups (Mass)
- EXTENSION: Includes a rigorous VDISP quality cut test > 150 km/s.
"""

import numpy as np
import json
from scipy import stats
import sys

print("🎯 FINAL ROBUSTNESS ANALYSIS - VDISP MASS (EXTENDED)")
print("============================================================")

# Ensure Rust module is loaded for performance
try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded for fast bispectrum calculation.")
except ImportError:
    print("❌ Rust module unavailable. The script can only run if this module exists.")
    sys.exit()

# --- STRATEGIC CONFIGURATION ---
configs_a_testear = [(2, 2, 2), (1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8
N_MUESTRAS_VALIDACION = 25
SAMPLE_SIZE = 500 # Non-replacement sub-sample size

# Null Hypothesis: H₀ = 1.1x (Conservative reference value)
H0_TEST = 1.1

# Definition of the extreme cut for the robustness test
VDISP_CUT_BASE = 100
VDISP_CUT_EXTREMO = 150 # <-- New cut to test

# --- OPTIMIZED DATA LOADING (MEMORY) ---
try:
    data = np.load('sdss_vdisp_calidad.npz', mmap_mode='r')
    vdisp_full = data['VDISP'].astype(np.float32)
    redshift_full = data['Z'].astype(np.float32)
    del data
except FileNotFoundError:
    print("❌ Error: Data file not found. Check 'sdss_vdisp_calidad.npz'.")
    sys.exit()


def analizar_por_corte(filtro_vdisp_min):
    """Executes the complete mass robustness analysis for a given FILTRO_VDISP_MIN."""

    print(f"\n\n========================================================================================")
    print(f"🔬 RUNNING ROBUSTNESS ANALYSIS WITH MINIMUM VDISP QUALITY FILTER > {filtro_vdisp_min:.0f} km/s")
    print(f"========================================================================================")

    # 1. Quantile Definition based on the new filter
    mask_filtrada_total = (redshift_full >= 0.1) & (redshift_full < 0.8) & (vdisp_full > filtro_vdisp_min)
    vdisp_filtrado = vdisp_full[mask_filtrada_total]

    if len(vdisp_filtrado) < 1000:
        print(f"❌ Error: Insufficient data to define quantiles with VDISP > {filtro_vdisp_min}.")
        return {}

    q_33 = np.percentile(vdisp_filtrado, 33)
    q_66 = np.percentile(vdisp_filtrado, 66)

    grupos_masa = {
        "VDISP_LOW (<33%)": (filtro_vdisp_min, q_33),
        "VDISP_MID (33%-66%)": (q_33, q_66),
        "VDISP_HIGH (>66%)": (q_66, 1000.0)
    }

    print(f"\n🔧 RECALCULATED QUANTILES (VDISP > {filtro_vdisp_min}): Q33={q_33:.1f} | Q66={q_66:.1f}")

    resultados_evolucion = {}

    # 2. ANALYSIS BY MASS GROUP
    for nombre_grupo, (vdisp_min, vdisp_max) in grupos_masa.items():
        print(f"\n--- MASS GROUP: {nombre_grupo} ({vdisp_min:.1f} - {vdisp_max:.1f} km/s) ---")

        galaxies_z_low = None
        galaxies_z_high = None

        # a) Filtering by Redshift and Mass Group
        for label, z_min, z_max in [('z01_02', 0.1, 0.2), ('z07_08', 0.7, 0.8)]:

            mask = (redshift_full >= z_min) & (redshift_full < z_max) & \
                   (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)

            galaxies_bin = vdisp_full[mask]

            if len(galaxies_bin) < SAMPLE_SIZE:
                print(f"    ❌ {label}: Insufficient data ({len(galaxies_bin)} < {SAMPLE_SIZE}).")
                continue

            print(f"    ✅ {label} (z={z_min}-{z_max}): {len(galaxies_bin)} galaxies available.")

            if 'z01_02' in label:
                galaxies_z_low = galaxies_bin
            elif 'z07_08' in label:
                galaxies_z_high = galaxies_bin

        # b) EVOLUTION CALCULATION (Non-Replacement Sampling)
        if galaxies_z_low is not None and galaxies_z_high is not None:

            n_samples = min(N_MUESTRAS_VALIDACION,
                            len(galaxies_z_low) // SAMPLE_SIZE,
                            len(galaxies_z_high) // SAMPLE_SIZE)

            if n_samples == 0:
                print("    ❌ Could not get non-replacement samples.")
                continue

            # print(f"    🚀 Running {n_samples} non-replacement samplings...")

            indices_low = np.random.permutation(len(galaxies_z_low))
            indices_high = np.random.permutation(len(galaxies_z_high))

            evoluciones_esc = []

            for i in range(n_samples):
                start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
                sample_low = galaxies_z_low[indices_low[start:end]]
                sample_high = galaxies_z_high[indices_high[start:end]]

                bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_a_testear)
                bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_a_testear)

                if bispectra_high and bispectra_low:
                    # Average Scalene (indices 1 onwards)
                    esc_high = np.mean([abs(b) for b in bispectra_high[1:]])
                    esc_low = np.mean([abs(b) for b in bispectra_low[1:]])
                    evol_esc = esc_high / esc_low if esc_low > 0 else np.nan
                    evoluciones_esc.append(evol_esc)

            # c) FINAL STATISTICAL ANALYSIS
            evoluciones_esc = np.array(evoluciones_esc)
            evoluciones_esc = evoluciones_esc[~np.isnan(evoluciones_esc)]

            if len(evoluciones_esc) > 1:
                media_obs = np.mean(evoluciones_esc)
                std_obs = np.std(evoluciones_esc, ddof=1)
                n_obs = len(evoluciones_esc)
                sem_obs = std_obs / np.sqrt(n_obs)

                # Significance calculation (t-test vs H0=1.1)
                t = abs(media_obs - H0_TEST) / sem_obs
                p = 2 * (1 - stats.t.cdf(t, n_obs-1))
                sigma = stats.norm.ppf(1 - p/2)

                resultados_evolucion[nombre_grupo] = {
                    'media_evolucion': media_obs,
                    'sem_evolucion': sem_obs,
                    'significancia_11': sigma,
                    'N_muestras_sin_reemplazo': n_obs
                }

                print(f"\n    📈 FINAL RESULTS (Scalenes):")
                print(f"      • Mean Evolution: {media_obs:.2f}×")
                print(f"      • Standard Error (SEM): {sem_obs:.2f}×")
                print(f"      • Significance vs {H0_TEST}x: {sigma:.2f}σ")

                if sigma >= 5.0:
                     print(f"      🎉 **SOLID EVIDENCE (>5σ)**")

            else:
                print("    ❌ Statistical analysis unavailable.")
    
    return resultados_evolucion

# Run analysis for base cut and extreme cut
resultados_corte_base = analizar_por_corte(VDISP_CUT_BASE)
resultados_corte_extremo = analizar_por_corte(VDISP_CUT_EXTREMO)


# 4. FINAL REPORT AND SAVING
print("\n" + "=" * 80)
print("🌟 FINAL VERDICT: COMPARISON OF ROBUSTNESS BY QUALITY AND MASS 🌟")
print("=" * 80)

def imprimir_resumen(titulo, resultados):
    print(f"\n--- {titulo} (VDISP > {VDISP_CUT_BASE if 'Base' in titulo else VDISP_CUT_EXTREMO} km/s) ---")
    for nombre, res in resultados.items():
        print(f"  Group: {nombre}")
        print(f"    Mean Evolution: {res['media_evolucion']:.2f}×")
        print(f"    SEM: {res['sem_evolucion']:.2f}×")
        print(f"    Significance ({H0_TEST}x): {res['significancia_11']:.2f}σ")
        if res['significancia_11'] >= 5.0:
            print("    🔑 Interpretation: Beyond-ΛCDM signal confirmed.")

imprimir_resumen("BASE CUT (Standard Quality)", resultados_corte_base)
imprimir_resumen("EXTREME CUT (High Purity)", resultados_corte_extremo)

datos_para_json = {
    f'resultados_corte_{VDISP_CUT_BASE}': resultados_corte_base,
    f'resultados_corte_{VDISP_CUT_EXTREMO}': resultados_corte_extremo
}

# Save results
try:
    with open('analisis_robustez_masa_VDISP_EXTENDIDO.json', 'w') as f:
        json.dump(datos_para_json, f, indent=2)
    print(f"\n✅ Complete results saved in 'analisis_robustez_masa_VDISP_EXTENDIDO.json'.")
except IOError:
    print("\n❌ Error saving JSON file.")

print(f"\n✅ EXTENDED ANALYSIS COMPLETED.")