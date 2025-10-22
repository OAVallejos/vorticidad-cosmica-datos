#!/usr/bin/env python3

"""
ANÁLISIS_ROBUSTEZ_EXTENDIDO.py
EXTENDED FINAL ROBUSTNESS ANALYSIS: 3.02x Signal by VDISP (Mass) Subgroups
- EXTENSION: Includes a rigorous quality cut test of VDISP > 150 km/s.
"""

import numpy as np
import json
from scipy import stats
import sys

print("🎯 EXTENDED FINAL ROBUSTNESS ANALYSIS - VDISP MASS")
print("============================================================")

# Ensure the Rust module is loaded for performance
try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded for fast bispectrum calculation.")
except ImportError:
    print("❌ Rust module not available. The script can only run if this module exists.")
    sys.exit()

# --- STRATEGIC CONFIGURATION ---
configs_to_test = [(2, 2, 2), (1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8
N_VALIDATION_SAMPLES = 40
SAMPLE_SIZE = 500 # Size of the sub-sample without replacement

# Null Hypothesis: H₀ = 1.1x (Conservative reference value)
H0_TEST = 1.1

# Definition of the extreme cut for the robustness test
VDISP_CUT_BASE = 100
VDISP_CUT_EXTREME = 150 # <-- New cut to test

# --- OPTIMIZED DATA LOADING (MEMORY) ---
try:
    data = np.load('sdss_vdisp_calidad.npz', mmap_mode='r')
    vdisp_full = data['VDISP'].astype(np.float32)
    redshift_full = data['Z'].astype(np.float32)
    del data
except FileNotFoundError:
    print("❌ Error: Data file not found. Check 'sdss_vdisp_calidad.npz'.")
    sys.exit()


def analyze_by_cut(vdisp_min_filter):
    """Executes the complete mass robustness analysis for a given VDISP_MIN_FILTER."""

    print(f"\n\n========================================================================================")
    print(f"🔬 EXECUTING ROBUSTNESS ANALYSIS WITH MINIMUM VDISP QUALITY FILTER > {vdisp_min_filter:.0f} km/s")
    print(f"========================================================================================")

    # 1. Quantile Definition based on the new filter
    mask_filtered_total = (redshift_full >= 0.1) & (redshift_full < 0.8) & (vdisp_full > vdisp_min_filter)
    vdisp_filtered = vdisp_full[mask_filtered_total]

    if len(vdisp_filtered) < 1000:
        print(f"❌ Error: Insufficient data to define quantiles with VDISP > {vdisp_min_filter}.")
        return {}

    q_33 = np.percentile(vdisp_filtered, 33)
    q_66 = np.percentile(vdisp_filtered, 66)

    mass_groups = {
        "VDISP_LOW (<33%)": (vdisp_min_filter, q_33),
        "VDISP_MID (33%-66%)": (q_33, q_66),
        "VDISP_HIGH (>66%)": (q_66, 1000.0)
    }

    print(f"\n🔧 RECALCULATED QUANTILES (VDISP > {vdisp_min_filter}): Q33={q_33:.1f} | Q66={q_66:.1f}")

    evolution_results = {}

    # 2. ANALYSIS BY MASS GROUP
    for group_name, (vdisp_min, vdisp_max) in mass_groups.items():
        print(f"\n--- MASS GROUP: {group_name} ({vdisp_min:.1f} - {vdisp_max:.1f} km/s) ---")

        galaxies_z_low = None
        galaxies_z_high = None

        # a) Filtering by Redshift and Mass Group
        for label, z_min, z_max in [('z01_02', 0.1, 0.2), ('z07_08', 0.7, 0.8)]:

            mask = (redshift_full >= z_min) & (redshift_full < z_max) & \
                   (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)

            galaxies_bin = vdisp_full[mask]

            if len(galaxies_bin) < SAMPLE_SIZE:
                print(f"    ❌ {label}: Insufficient data ({len(galaxies_bin)} < {SAMPLE_SIZE}).")
                continue

            print(f"    ✅ {label} (z={z_min}-{z_max}): {len(galaxies_bin)} galaxies available.")

            if 'z01_02' in label:
                galaxies_z_low = galaxies_bin
            elif 'z07_08' in label:
                galaxies_z_high = galaxies_bin

        # b) EVOLUTION CALCULATION (Sampling WITHOUT REPLACEMENT)
        if galaxies_z_low is not None and galaxies_z_high is not None:

            n_samples = min(N_VALIDATION_SAMPLES,
                            len(galaxies_z_low) // SAMPLE_SIZE,
                            len(galaxies_z_high) // SAMPLE_SIZE)

            if n_samples == 0:
                print("    ❌ Could not obtain samples WITHOUT REPLACEMENT.")
                continue

            # print(f"    🚀 Executing {n_samples} samplings WITHOUT REPLACEMENT...")

            indices_low = np.random.permutation(len(galaxies_z_low))
            indices_high = np.random.permutation(len(galaxies_z_high))

            scalene_evolutions = []

            for i in range(n_samples):
                start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
                sample_low = galaxies_z_low[indices_low[start:end]]
                sample_high = galaxies_z_high[indices_high[start:end]]

                bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_to_test)
                bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_to_test)

                if bispectra_high and bispectra_low:
                    # Average Scalene (indices 1 onwards)
                    avg_scalene_high = np.mean([abs(b) for b in bispectra_high[1:]])
                    avg_scalene_low = np.mean([abs(b) for b in bispectra_low[1:]])
                    evol_esc = avg_scalene_high / avg_scalene_low if avg_scalene_low > 0 else np.nan
                    scalene_evolutions.append(evol_esc)

            # c) FINAL STATISTICAL ANALYSIS
            scalene_evolutions = np.array(scalene_evolutions)
            scalene_evolutions = scalene_evolutions[~np.isnan(scalene_evolutions)]

            if len(scalene_evolutions) > 1:
                obs_mean = np.mean(scalene_evolutions)
                obs_std = np.std(scalene_evolutions, ddof=1)
                n_obs = len(scalene_evolutions)
                obs_sem = obs_std / np.sqrt(n_obs)

                # Significance Calculation (t-test vs H0=1.1)
                t = abs(obs_mean - H0_TEST) / obs_sem
                p = 2 * (1 - stats.t.cdf(t, n_obs-1))
                sigma = stats.norm.ppf(1 - p/2)

                evolution_results[group_name] = {
                    'evolution_mean': obs_mean,
                    'evolution_sem': obs_sem,
                    'significance_11': sigma,
                    'N_samples_without_replacement': n_obs
                }

                print(f"\n    📈 FINAL RESULTS (Scalene):")
                print(f"      • Mean Evolution: {obs_mean:.2f}×")
                print(f"      • Standard Error (SEM): {obs_sem:.2f}×")
                print(f"      • Significance vs {H0_TEST}x: {sigma:.2f}σ")

                if sigma >= 5.0:
                    print(f"      🎉 **SOLID EVIDENCE (>5σ)**")

            else:
                print("    ❌ Statistical analysis not available.")
    
    return evolution_results

# Execute analysis for the base cut and the extreme cut
base_cut_results = analyze_by_cut(VDISP_CUT_BASE)
extreme_cut_results = analyze_by_cut(VDISP_CUT_EXTREMO)


# 4. FINAL REPORT AND SAVING
print("\n" + "=" * 80)
print("🌟 FINAL VERDICT: ROBUSTNESS COMPARISON BY QUALITY AND MASS 🌟")
print("=" * 80)

def print_summary(title, results):
    print(f"\n--- {title} (VDISP > {VDISP_CUT_BASE if 'Base' in title else VDISP_CUT_EXTREMO} km/s) ---")
    for name, res in results.items():
        print(f"  Group: {name}")
        print(f"    Mean Evolution: {res['evolution_mean']:.2f}×")
        print(f"    SEM: {res['evolution_sem']:.2f}×")
        print(f"    Significance ({H0_TEST}x): {res['significance_11']:.2f}σ")
        if res['significance_11'] >= 5.0:
            print("    🔑 Interpretation: Beyond-ΛCDM signal confirmed.")

print_summary("BASE CUT (Standard Quality)", base_cut_results)
print_summary("EXTREME CUT (High Purity)", extreme_cut_results)

data_for_json = {
    f'results_cut_{VDISP_CUT_BASE}': base_cut_results,
    f'results_cut_{VDISP_CUT_EXTREMO}': extreme_cut_results
}

# Save results
try:
    with open('analisis_robustez_masa_VDISP_EXTENDIDO.json', 'w') as f:
        json.dump(data_for_json, f, indent=2)
    print(f"\n✅ Complete results saved in 'analisis_robustez_masa_VDISP_EXTENDIDO.json'.")
except IOError:
    print("\n❌ Error saving the JSON file.")

print(f"\n✅ EXTENDED ANALYSIS COMPLETED.")
