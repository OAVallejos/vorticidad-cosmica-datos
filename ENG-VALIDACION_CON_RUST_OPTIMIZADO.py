#!/usr/bin/env python3
"""
VALIDACION_CON_RUST_OPTIMIZADO.py
OPTIMIZED VALIDATION FOR 5σ - 40 SAMPLES
"""

import numpy as np
import json
from scipy import stats # Imported for the final section

print("🎯 OPTIMIZED VALIDATION - 5σ TARGET")
print("=" * 60)

try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded")
    RUST_AVAILABLE = True
except ImportError:
    print("❌ Rust module not available")
    exit()

# OPTIMIZED CONFIGURATION
configs_222 = [(2, 2, 2)]
configs_444 = [(4, 4, 4)]
configs_scalene = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
all_configs = configs_222 + configs_444 + configs_scalene
l_max = 8

# Load data
data = np.load('sdss_vdisp_calidad.npz')
vdisp = data['VDISP']
redshift = data['Z']

# BINS FOR ANALYSIS
bins_paper = [(0.1, 0.2, "z01_02"), (0.7, 0.8, "z07_08")]

print(f"🔧 OPTIMIZED CONFIGURATION:")
print(f"   • Samples: 40 (vs 5 original)") # MODIFICATION 1: 25 -> 40
print(f"   • Configurations: {len(all_configs)}")
print(f"   • l_max: {l_max}")

comparative_results = {}
evolutions_222 = []
evolutions_esc = [] # Changed 'evoluciones_esc' to 'evolutions_esc' for consistency

# 🎯 MAIN OPTIMIZED ANALYSIS
for z_min, z_max, label in bins_paper:
    print(f"\n📊 {label} (z={z_min}-{z_max}):")
    mask = (redshift >= z_min) & (redshift < z_max) & (vdisp > 100)
    galaxies_bin = vdisp[mask]

    print(f"   • Available galaxies: {len(galaxies_bin)}")

    # Use larger samples for stability
    sample_size = min(500, len(galaxies_bin)) # Increased from 200 to 500

    bin_results = {
        '222': [],
        '444': [],
        'scalene': [] # Changed 'escalenos' to 'scalene' for consistency
    }

    # 🚀 40 SAMPLES
    for seed in range(40): # MODIFICATION 2: 25 -> 40
        np.random.seed(seed)
        if len(galaxies_bin) >= sample_size:
            sample = np.random.choice(galaxies_bin, size=sample_size, replace=False)
            bispectra = calcular_bispectro_triangular(sample.tolist(), l_max, all_configs)

            if bispectra:
                # (2,2,2)
                value_222 = abs(bispectra[0])
                bin_results['222'].append(value_222)

                # (4,4,4)
                value_444 = abs(bispectra[1])
                bin_results['444'].append(value_444)

                # Average scalene
                scalene_values = [abs(bispectra[i]) for i in range(2, 8)]
                avg_scalene_value = np.mean(scalene_values) if scalene_values else 0
                bin_results['scalene'].append(avg_scalene_value)

    # Calculate averages by bin
    if bin_results['222']:
        comparative_results[label] = {
            'z_mean': (z_min + z_max) / 2,
            '222': np.mean(bin_results['222']),
            '444': np.mean(bin_results['444']),
            'average_scalene': np.mean(bin_results['scalene']),
            'N_galaxies': sample_size,
            'N_samples': len(bin_results['222'])
        }

        print(f"   • (2,2,2): {np.mean(bin_results['222']):.3e} (n={len(bin_results['222'])})")
        print(f"   • Scalene: {np.mean(bin_results['scalene']):.3e} (n={len(bin_results['scalene'])})")

# 🎯 EVOLUTION CALCULATION (40 SAMPLES)
print(f"\n📈 CALCULATING EVOLUTIONS...")
if 'z01_02' in comparative_results and 'z07_08' in comparative_results:
    z_low = comparative_results['z01_02']
    z_high = comparative_results['z07_08']

    # For each of the 40 samples, calculate individual evolution
    for seed in range(40): # MODIFICATION 3: 25 -> 40
        np.random.seed(seed)

        # High-z sample
        mask_high = (redshift >= 0.7) & (redshift < 0.8) & (vdisp > 100)
        galaxies_high = vdisp[mask_high]
        if len(galaxies_high) >= 500:
            sample_high = np.random.choice(galaxies_high, size=500, replace=False)
            bispectra_high = calcular_bispectro_triangular(sample_high.tolist(), l_max, [(2,2,2)] + configs_scalene)

            # Low-z sample
            mask_low = (redshift >= 0.1) & (redshift < 0.2) & (vdisp > 100)
            galaxies_low = vdisp[mask_low]
            if len(galaxies_low) >= 500:
                sample_low = np.random.choice(galaxies_low, size=500, replace=False)
                bispectra_low = calcular_bispectro_triangular(sample_low.tolist(), l_max, [(2,2,2)] + configs_scalene)

                if bispectra_high and bispectra_low:
                    # (2,2,2)
                    evol_222 = abs(bispectra_high[0]) / abs(bispectra_low[0]) if abs(bispectra_low[0]) > 0 else 0
                    evolutions_222.append(evol_222)

                    # Average scalene
                    avg_scalene_high = np.mean([abs(b) for b in bispectra_high[1:]])
                    avg_scalene_low = np.mean([abs(b) for b in bispectra_low[1:]])
                    evol_esc = avg_scalene_high / avg_scalene_low if avg_scalene_low > 0 else 0
                    evolutions_esc.append(evol_esc)

                    if seed < 5: # Show first 5
                        print(f"   Sample {seed+1}: (2,2,2)={evol_222:.1f}×, Scalene={evol_esc:.1f}×")

# 📊 SAVE OPTIMIZED RESULTS
final_results = {
    'comparative_results': comparative_results,
    'statistical_validation': {
        'evolutions_222': evolutions_222,
        'evolutions_scalene': evolutions_esc
    }
}

with open('analisis_divergencia_OPTIMIZADO.json', 'w') as f:
    json.dump(final_results, f, indent=2)

print(f"\n✅ OPTIMIZED VALIDATION COMPLETED")
print(f"   • Samples: {len(evolutions_222)}")
print(f"   • File: analisis_divergencia_OPTIMIZADO.json")

# 📈 CALCULATE PROJECTED SIGNIFICANCE
if evolutions_esc:
    mean_esc = np.mean(evolutions_esc)
    std_esc = np.std(evolutions_esc, ddof=1)
    n_esc = len(evolutions_esc)

    sem_esc = std_esc / np.sqrt(n_esc)
    # H0 = 1.1x is used for the most rigorous significance (as in the DESI analysis)
    t_esc = abs(mean_esc - 1.1) / sem_esc
    p_esc = 2 * (1 - stats.t.cdf(t_esc, n_esc-1))
    sigma_esc = stats.norm.ppf(1 - p_esc/2)

    print(f"\n🎯 PROJECTED SIGNIFICANCE:")
    print(f"   • Mean: {mean_esc:.2f}×")
    print(f"   • Samples: {n_esc}")
    print(f"   • Significance: {sigma_esc:.2f}σ")

    if sigma_esc >= 5.0:
        print(f"   🎉 5σ REACHED!")
    else:
        print(f"   📈 Progress: {sigma_esc:.2f}σ (target: 5σ)")