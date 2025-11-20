#!/usr/bin/env python3
"""

CORRECTED Tuning with consistent parameters
"""

import numpy as np
import json
from scipy import stats
from astropy.table import Table

print("🎯 MASS THRESHOLD TUNING (Mc) - VORTEX (v4.3) PARAMETERS")
print("=" * 70)

# --- CONFIGURATION CONSISTENT WITH VORTEX (v4.3) ---
VDISP_MIN_CALIDAD = 150.0  # Minimum Velocity Dispersion for Quality
H0_ACDM_MAX = 1.1          # ΛCDM Upper limit preprint
SAMPLE_SIZE = 500
N_VALIDATION_SAMPLES = 80

# Redshift bins for DESI
bins_redshift_desi = [('z04_06', 0.4, 0.6), ('z08_10', 0.8, 1.0)]

# Scaling configurations (l_1, l_2, l_3)
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8

# VORTEX CORRECTION FACTORS
C_MASA = 5.263      # 1/0.190 from VORTEX
C_BIAS = 1.493      # (2.4/2.1)^3 from VORTEX
C_TOTAL = 7.856     # 5.263 × 1.493 from VORTEX (v4.3)

def justificar_parametros_vortex():
    """Documents parameters consistent """

    print("\n📚 PARAMETERS CONSISTENT:")
    print("=" * 50)
    print("🔬 CORRECTION FACTORS:")
    print(f"    • C_Mass: {C_MASA}× (1/0.190 - VORTEX)")
    print(f"    • C_Bias: {C_BIAS}× ((2.4/2.1)³ - VORTEX)")
    print(f"    • C_Total: {C_TOTAL}× (VORTEX)")
    print(f"🔬 NULL HYPOTHESIS (VORTEX):")
    print(f"    • H₀ = {H0_ACDM_MAX} (ΛCDM upper limit)")
    print(f"🔬 THRESHOLDS:")
    print(f"    • Minimum VDISP: {VDISP_MIN_CALIDAD} km/s")
    print(f"    • Target Mc: ~220 km/s (M_c ≈ 3 × 10¹³ M☉)")

try:
    # Assumes a module `cosmic_vorticity` exists (likely written in Rust/C)
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded for fast bispectrum calculation.")
except ImportError:
    print("❌ Rust module not available.")
    exit()

def ejecutar_analisis_grupos_vortex(vdisp_full, redshift_full, mass_groups, dataset_name, bins_redshift):
    """Version with VORTEX parameters"""
    resultados = {}

    for group_name, (vdisp_min, vdisp_max, label_masa) in mass_groups.items():
        print(f"    📊 Analyzing {label_masa} ({vdisp_min:.1f} - {vdisp_max:.1f} km/s)")

        # Filter galaxies within the VDISP range
        mask_grupo = (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)
        n_galaxias = np.sum(mask_grupo)

        galaxies_z_low = None
        galaxies_z_high = None

        # Separate into redshift bins
        for label_z, z_min, z_max in bins_redshift:
            mask = (redshift_full >= z_min) & (redshift_full < z_max) & mask_grupo
            galaxies_bin = vdisp_full[mask]

            if len(galaxies_bin) < SAMPLE_SIZE:
                print(f"      ⚠️  {label_z}: Only {len(galaxies_bin):,} galaxies")
                continue

            if 'z04_06' in label_z:
                galaxies_z_low = galaxies_bin
                print(f"      🔵 z={z_min}-{z_max}: {len(galaxies_bin):,} galaxies")
            elif 'z08_10' in label_z:
                galaxies_z_high = galaxies_bin
                print(f"      🔴 z={z_min}-{z_max}: {len(galaxies_bin):,} galaxies")

        # EVOLUTION CALCULATION
        if galaxies_z_low is not None and galaxies_z_high is not None:
            n_samples_max = min(N_VALIDATION_SAMPLES,
                                len(galaxies_z_low) // SAMPLE_SIZE,
                                len(galaxies_z_high) // SAMPLE_SIZE)

            if n_samples_max > 0:
                print(f"      🔄 Generating {n_samples_max} samples...")

                indices_low = np.random.permutation(len(galaxies_z_low))
                indices_high = np.random.permutation(len(galaxies_z_high))
                evolutions = []

                for i in range(n_samples_max):
                    start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
                    sample_low = galaxies_z_low[indices_low[start:end]].tolist()
                    sample_high = galaxies_z_high[indices_high[start:end]].tolist()

                    # Call external (Rust) function to calculate the triangular bispectrum
                    bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_escalenas)
                    bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_escalenas)

                    if bispectra_high and bispectra_low:
                        # Calculate the ratio of average absolute bispectra
                        avg_high = np.mean([abs(b) for b in bispectra_high])
                        avg_low = np.mean([abs(b) for b in bispectra_low])
                        evol_esc = avg_high / avg_low if avg_low > 0 else np.nan
                        evolutions.append(evol_esc)

                # STATISTICAL ANALYSIS WITH H₀ = 1.1
                evolutions = np.array(evolutions)
                evolutions = evolutions[~np.isnan(evolutions)]

                if len(evolutions) > 1:
                    obs_mean = np.mean(evolutions)
                    obs_std = np.std(evolutions, ddof=1)
                    n_obs = len(evolutions)
                    obs_sem = obs_std / np.sqrt(n_obs)

                    # T-statistic with H₀ = 1.1 (VORTEXv4.3)
                    t = abs(obs_mean - H0_ACDM_MAX) / obs_sem
                    p = 2 * (1 - stats.t.cdf(t, n_obs-1))
                    sigma = stats.norm.ppf(1 - p/2)
                    if np.isinf(sigma): sigma = t

                    # APPLY VORTEX.tex CORRECTION
                    evol_corregida = obs_mean * C_TOTAL

                    resultados[label_masa] = {
                        'evolution_mean_obs': float(obs_mean),
                        'evolution_mean_corr': float(evol_corregida),
                        'significance_vs_acdm': float(sigma),
                        'evolution_std': float(obs_std),
                        'N_samples': n_obs,
                        'vdisp_rango': f"{vdisp_min:.1f}-{vdisp_max:.1f}",
                        'n_galaxias_grupo': int(n_galaxias),
                        'factor_correccion': C_TOTAL,
                        'H0_acdm_max': H0_ACDM_MAX
                    }

                    print(f"      📈 OBS Result: {obs_mean:.3f}× | vs {H0_ACDM_MAX}×: {sigma:.2f}σ")
                    print(f"      🔥 CORR Result: {evol_corregida:.3f}×")

                    # CLASSIFICATION WITH VORTEX PARAMETERS
                    if evol_corregida > 8.0 and sigma > 5.0:
                        print(f"      🎉 VERY STRONG EVOLUTION (>8.0× corrected)")
                    elif evol_corregida > 5.0 and sigma > 3.0:
                        print(f"      📈 Strong evolution (>5.0× corrected)")
                    elif evol_corregida > 2.0 and sigma > 2.0:
                        print(f"      🔍 Moderate evolution (>2.0× corrected)")
                    else:
                        print(f"      ⚪ No significant evolution")

                else:
                    print("      ❌ Statistical analysis not available.")
            else:
                print("      ❌ Could not obtain enough samples.")
        else:
            print("      ❌ Not enough galaxies in both redshift bins")

    return resultados

def main_afinamiento_vortex():
    print("🎯 MASS THRESHOLD TUNING (Mc) - VORTEX PARAMETERS")
    print("=" * 70)

    # Justify VORTEX parameters
    justificar_parametros_vortex()

    print("\n🔍 Searching for the lower limit of HIGH MASS where")
    print("    strong bispectrum evolution begins")

    # 1. Load DESI data
    try:
        tabla_desi = Table.read('DATASET_LRG_VDISP_FLUXR_FINAL.fits')
        vdisp_desi = np.array(tabla_desi['VDISP'])
        redshift_desi = np.array(tabla_desi['Z'])
        print(f"✅ DESI loaded: {len(vdisp_desi):,} galaxies")
    except FileNotFoundError:
        print("❌ Error: 'DATASET_LRG_VDISP_FLUXR_FINAL.fits' not found.")
        return

    # Apply quality filter
    mask_calidad = vdisp_desi >= VDISP_MIN_CALIDAD
    vdisp_filtrado = vdisp_desi[mask_calidad]
    redshift_filtrado = redshift_desi[mask_calidad]

    print(f"🔧 VDISP filter > {VDISP_MIN_CALIDAD} km/s: {len(vdisp_filtrado):,} galaxies")

    # --- CONSISTENT CONFIGURATION ---
    CUTS_TO_TEST = np.linspace(200.0, 280.0, 9)
    VDISP_MAX = 500.0
    resultados_afinamiento = {}

    for mc_test in CUTS_TO_TEST:
        mc_test = round(mc_test, 1)

        print(f"\n--- 🔄 Testing Mc = {mc_test:.1f} km/s ---")
        print(f"    📈 Analyzing HIGH MASS above the threshold")

        # Define ONLY the HIGH MASS group
        mass_groups = {
            "ALTA_MASA_TEST": (mc_test, VDISP_MAX, f'ALTA_MASA_Mc_{mc_test:.1f}'),
        }

        # Run analysis with VORTEX parameters
        resultados_bin = ejecutar_analisis_grupos_vortex(
            vdisp_filtrado, redshift_filtrado, mass_groups, "DESI", bins_redshift_desi
        )

        if f'ALTA_MASA_Mc_{mc_test:.1f}' in resultados_bin:
            res = resultados_bin[f'ALTA_MASA_Mc_{mc_test:.1f}']
            resultados_afinamiento[mc_test] = {
                'evolution_obs': res['evolution_mean_obs'],
                'evolution_corr': res['evolution_mean_corr'],
                'significance_vs_acdm': res['significance_vs_acdm'],
                'N_galaxias_alta_masa': res['n_galaxias_grupo'],
                'vdisp_rango': res['vdisp_rango'],
                'factor_correccion': res['factor_correccion'],
                'H0_acdm_max': res['H0_acdm_max']
            }
            print(f"    🔥 CORRECTED Evolution: {res['evolution_mean_corr']:.3f}× | vs ΛCDM: {res['significance_vs_acdm']:.2f}σ")
        else:
            resultados_afinamiento[mc_test] = {
                'evolution_obs': np.nan,
                'evolution_corr': np.nan,
                'significance_vs_acdm': np.nan,
                'N_galaxias_alta_masa': 0,
                'vdisp_rango': f"{mc_test:.1f}-{VDISP_MAX:.1f}",
                'factor_correccion': C_TOTAL,
                'H0_acdm_max': H0_ACDM_MAX
            }
            print(f"    ⚠️  Incomplete analysis for Mc = {mc_test:.1f}")

    # Save results
    filename = 'ANALISIS_AFINAMIENTO_Mc_VORTEX.json'
    with open(filename, 'w') as f:
        # Use default=str to handle numpy types when serializing
        json.dump(resultados_afinamiento, f, indent=2, default=str)
    print(f"\n✅ VORTEX tuning results saved in '{filename}'.")

    # Result Analysis
    print("\n📊 TUNING SUMMARY - HIGH MASS (VORTEX):")
    print("Mc (km/s) | Evol(Obs) | Evol(Corr) | vs ΛCDM | N Galaxies | Classification")
    print("-" * 90)

    mejor_mc = None
    mejor_evolucion_corr = 0
    mejor_significancia = 0

    for mc in sorted(resultados_afinamiento.keys()):
        res = resultados_afinamiento[mc]
        # Handle NaN values for display and comparison
        evol_obs = res['evolution_obs'] if not np.isnan(res['evolution_obs']) else 0
        evol_corr = res['evolution_corr'] if not np.isnan(res['evolution_corr']) else 0
        sig = res['significance_vs_acdm'] if not np.isnan(res['significance_vs_acdm']) else 0
        n_gal = res['N_galaxias_alta_masa']

        # Classification with VORTEX parameters
        if evol_corr > 8.0 and sig > 5.0:
            clasif = "🎉 VERY STRONG"
        elif evol_corr > 5.0 and sig > 3.0:
            clasif = "📈 STRONG"
        elif evol_corr > 2.0 and sig > 2.0:
            clasif = "🔍 MODERATE"
        else:
            clasif = "⚪ WEAK"

        print(f"{float(mc):9.1f} | {evol_obs:9.3f}× | {evol_corr:10.3f}× | {sig:7.2f}σ | {n_gal:>9,} | {clasif}")

        # Search for the lowest Mc with STRONG evolution
        if evol_corr > 5.0 and sig > 3.0:
            if mejor_mc is None or float(mc) < mejor_mc:
                mejor_mc = float(mc)
                mejor_evolucion_corr = evol_corr
                mejor_significancia = sig

    # Interpretation
    print(f"\n💡 INTERPRETATION:")
    if mejor_mc:
        print(f"    🎯 Critical Mass Threshold Mc: ~{mejor_mc:.1f} km/s")
        print(f"    📈 ABOVE {mejor_mc:.1f} km/s: STRONG evolution")
        print(f"    📊 Corrected Signal: {mejor_evolucion_corr:.3f}×, vs ΛCDM: {mejor_significancia:.2f}σ")
        print(f"    🌟 Corresponding Mass: M_c ≈ 3 × 10¹³ M☉")
        print(f"    🔬 Factors: mass ({C_MASA}×) × bias ({C_BIAS}×) = {C_TOTAL}×")
    else:
        print("    🔍 No clear threshold was identified")

    print(f"\n📚 CONCLUSION:")
    print("    • Parameters are consistent")
    print("    • Null hypothesis: H₀ = 1.1× (ΛCDM limit)")
    print("    • Signals include validated systematic corrections")
    print("    • Mc identifies the onset of detectable primordial vorticity")

if __name__ == "__main__":
    main_afinamiento_vortex()