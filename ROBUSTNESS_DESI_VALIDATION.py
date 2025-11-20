#!/usr/bin/env python3
"""
CROSS-VALIDATION DESI LRG - RUST-PyO3 - 80 SAMPLES - CUT 150 km/s
"""

import numpy as np
import json
from scipy import stats
from astropy.table import Table
import sys
from datetime import datetime

# IMPORT THE REAL RUST FUNCTION
from cosmic_vorticity import calcular_bispectro_triangular

print("🎯 CROSS-VALIDATION DESI LRG - RUST-PyO3 - 80 SAMPLES")
print("=============================================================================")

# --- CONFIGURATION WITH CUT AT 150 km/s ---
VDISP_CUT_BASE = 150.0  # ✅ CONCEPTUAL CUT
H0_TEST = 1.1
SAMPLE_SIZE = 500
N_VALIDATION_SAMPLES = 80  # ✅ 80 SAMPLES AS ORIGINAL

# CONFIGURATIONS FOR THE RUST BISPECTRUM
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8

# OPTIMIZED REDSHIFT BINS for DESI LRG
bins_redshift_optimizados = [
    ('z04_06', 0.4, 0.6),   # Low bin: good sampling in DESI
    ('z08_10', 0.8, 1.0)    # High bin: good sampling in DESI
]

# OPTIMIZED CUT POINTS
Q_LOW_OPTIMIZED = 220.0   # Percentile ~25% of the complete dataset
Q_HIGH_OPTIMIZED = 303.0  # Percentile ~75% of the complete dataset

def analizar_distribucion_vdisp_filtrada(vdisp_data):
    """Analyzes the VDISP distribution after the >150 km/s filter"""
    print(f"\n📊 ANALYZING VDISP DISTRIBUTION (>{VDISP_CUT_BASE} km/s)...")

    # Apply filter
    vdisp_filtrado = vdisp_data[vdisp_data >= VDISP_CUT_BASE]

    print(f"📈 Statistics after filter:")
    print(f"   • Remaining galaxies: {len(vdisp_filtrado):,}/{len(vdisp_data):,} ({len(vdisp_filtrado)/len(vdisp_data)*100:.1f}%)")
    print(f"   • VDISP range: {vdisp_filtrado.min():.1f} - {vdisp_filtrado.max():.1f} km/s")
    print(f"   • VDISP Mean: {vdisp_filtrado.mean():.1f} ± {vdisp_filtrado.std():.1f} km/s")

    # Percentiles of the filtered dataset
    percentiles = np.percentile(vdisp_filtrado, [0, 25, 50, 75, 100])
    print(f"   • Percentiles: P0={percentiles[0]:.1f}, P25={percentiles[1]:.1f}, P50={percentiles[2]:.1f}, P75={percentiles[3]:.1f}, P100={percentiles[4]:.1f} km/s")

    return vdisp_filtrado, percentiles

def ejecutar_analisis_grupos(vdisp_full, redshift_full, mass_groups, tipo_analisis):
    """Executes the analysis for a set of mass groups using RUST-PyO3"""
    resultados_robustez = {}

    for group_name, (vdisp_min, vdisp_max, label_masa) in mass_groups.items():
        print(f"\n--- GROUP: {label_masa} ({vdisp_min:.1f} - {vdisp_max:.1f} km/s) ---")

        # Calculate group statistics
        mask_grupo = (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)
        n_galaxias = np.sum(mask_grupo)
        print(f"    📊 Galaxies in group: {n_galaxias:,}")

        galaxies_z_low = None
        galaxies_z_high = None

        for label_z, z_min, z_max in bins_redshift_optimizados:
            mask = (redshift_full >= z_min) & (redshift_full < z_max) & mask_grupo
            galaxies_bin = vdisp_full[mask]

            if len(galaxies_bin) < SAMPLE_SIZE:
                print(f"    ⚠️  {label_z}: Only {len(galaxies_bin):,} galaxies (need {SAMPLE_SIZE})")
                continue

            if 'z04_06' in label_z:
                galaxies_z_low = galaxies_bin
                print(f"    🔵 z={z_min}-{z_max}: {len(galaxies_bin):,} galaxies")
            elif 'z08_10' in label_z:
                galaxies_z_high = galaxies_bin
                print(f"    🔴 z={z_min}-{z_max}: {len(galaxies_bin):,} galaxies")

        # EVOLUTION CALCULATION WITH RUST-PyO3
        if galaxies_z_low is not None and galaxies_z_high is not None:

            n_samples_max = min(N_VALIDATION_SAMPLES,
                                len(galaxies_z_low) // SAMPLE_SIZE,
                                len(galaxies_z_high) // SAMPLE_SIZE)

            if n_samples_max > 0:
                print(f"    🔄 Generating {n_samples_max} samples of {SAMPLE_SIZE} galaxies (Rust-PyO3)...")

                indices_low = np.random.permutation(len(galaxies_z_low))
                indices_high = np.random.permutation(len(galaxies_z_high))
                evolutions = []

                for i in range(n_samples_max):
                    start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
                    sample_low = galaxies_z_low[indices_low[start:end]].tolist()
                    sample_high = galaxies_z_high[indices_high[start:end]].tolist()

                    # ✅ USING THE REAL RUST-PyO3 FUNCTION
                    try:
                        bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_escalenas)
                        bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_escalenas)

                        if bispectra_high and bispectra_low:
                            avg_high = np.mean([abs(b) for b in bispectra_high])
                            avg_low = np.mean([abs(b) for b in bispectra_low])
                            evol_esc = avg_high / avg_low if avg_low > 0 else np.nan
                            evolutions.append(evol_esc)

                    except Exception as e:
                        print(f"    ❌ Error in Rust-PyO3 calculation: {e}")
                        continue

                # STATISTICAL ANALYSIS
                evolutions = np.array(evolutions)
                evolutions = evolutions[~np.isnan(evolutions)]

                if len(evolutions) > 1:
                    obs_mean = np.mean(evolutions)
                    obs_std = np.std(evolutions, ddof=1)
                    n_obs = len(evolutions)
                    obs_sem = obs_std / np.sqrt(n_obs)

                    t = abs(obs_mean - H0_TEST) / obs_sem
                    p = 2 * (1 - stats.t.cdf(t, n_obs-1))
                    sigma = stats.norm.ppf(1 - p/2)
                    if np.isinf(sigma): sigma = t

                    resultados_robustez[label_masa] = {
                        'evolution_mean': float(obs_mean),
                        'significance_11': float(sigma),
                        'evolution_std': float(obs_std),
                        'N_samples': n_obs,
                        'vdisp_rango': f"{vdisp_min:.1f}-{vdisp_max:.1f}",
                        'n_galaxias_grupo': int(n_galaxias)
                    }

                    print(f"    📈 RESULTS:")
                    print(f"      • Mean Evolution: {obs_mean:.3f}×")
                    print(f"      • Significance vs {H0_TEST}x: {sigma:.2f}σ")
                    print(f"      • Valid samples: {n_obs}")

                    if sigma >= 2.0:
                        print(f"      🎉 **SIGNIFICANT (>2σ)**")
                else:
                    print("    ❌ Statistical analysis not available.")
            else:
                print("     ❌ Could not get enough samples.")
        else:
            print("    ❌ Not enough galaxies in both redshift bins")

    return resultados_robustez

def main():
    """Main function"""
    print("📥 LOADING COMPLETE DESI LRG DATASET...")
    try:
        tabla = Table.read('DATASET_LRG_VDISP_FLUXR_FINAL.fits')
        vdisp_full = np.array(tabla['VDISP'])
        redshift_full = np.array(tabla['Z'])
        print(f"📊 DESI LRG Loaded: {len(vdisp_full):,} galaxies")
    except FileNotFoundError:
        print("❌ Error: 'DATASET_LRG_VDISP_FLUXR_FINAL.fits' not found.")
        sys.exit()

    # Apply VDISP > 150 km/s filter
    vdisp_filtrado, percentiles = analizar_distribucion_vdisp_filtrada(vdisp_full)
    redshift_filtrado = redshift_full[vdisp_full >= VDISP_CUT_BASE]

    # MASS GROUPS with cut at 150 km/s
    mass_groups_optimized = {
        "VDISP_LOW": (VDISP_CUT_BASE, Q_LOW_OPTIMIZED, 'LOW_MASS'),
        "VDISP_MID": (Q_LOW_OPTIMIZED, Q_HIGH_OPTIMIZED, 'MEDIUM_MASS'),
        "VDISP_HIGH": (Q_HIGH_OPTIMIZED, 500.0, 'HIGH_MASS')
    }

    print(f"\n🎯 EXECUTING ANALYSIS WITH CUT AT {VDISP_CUT_BASE} km/s")
    print("=" * 60)
    print(f"🔧 CUT POINTS: LOW={Q_LOW_OPTIMIZED:.1f} | HIGH={Q_HIGH_OPTIMIZED:.1f}")
    print(f"📊 Redshift Bins: z=0.4-0.6 and z=0.8-1.0")
    print(f"🎯 Samples: {N_VALIDATION_SAMPLES} per group")
    print(f"🔬 Method: Rust-PyO3 (calcular_bispectro_triangular)")

    resultados = ejecutar_analisis_grupos(vdisp_filtrado, redshift_filtrado, mass_groups_optimized, "CORTE_150")

    if resultados:
        print(f"\n🚀 FINAL SUMMARY - CUT {VDISP_CUT_BASE} km/s")
        print("=" * 60)

        for grupo, res in resultados.items():
            sig = res['significance_11']
            evol = res['evolution_mean']
            rango = res['vdisp_rango']
            n_gal = res['n_galaxias_grupo']
            n_samples = res['N_samples']
            print(f"   {grupo:>12} ({rango}): {evol:5.3f}×  |  {sig:5.2f}σ | {n_gal:>8,} galaxies | {n_samples:>2} samples")

        # Save results
        metadata = {
            'corte_vdisp': VDISP_CUT_BASE,
            'observacion': f'Analysis with conceptual cut at {VDISP_CUT_BASE} km/s - Rust-PyO3',
            'bins_redshift': bins_redshift_optimizados,
            'galaxias_totales_filtradas': len(vdisp_filtrado),
            'configuraciones_rust': configs_escalenas,
            'l_max': l_max
        }

        config = {
            'tipo_cortes': 'CORTE_150_RUST',
            'corte_calidad_vdisp': VDISP_CUT_BASE,
            'puntos_corte_masa': {'bajo': Q_LOW_OPTIMIZED, 'alto': Q_HIGH_OPTIMIZED},
            'H0_TEST': H0_TEST,
            'n_muestras': N_VALIDATION_SAMPLES,
            'tamano_muestra': SAMPLE_SIZE,
            'bins_redshift': bins_redshift_optimizados
        }

        output = {
            'metadata': metadata,
            'configuracion': config,
            'resultados': resultados,
            'timestamp': datetime.now().isoformat(),
            'version': 'RUST-PyO3_REAL'
        }

        with open('ROBUSTEZ_DESI_CORTE150_RUST.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Results saved to 'ROBUSTEZ_DESI_CORTE150_RUST.json'")

    print(f"\n✅ ANALYSIS WITH CUT {VDISP_CUT_BASE} km/s COMPLETED (RUST-PyO3)")

if __name__ == "__main__":
    main()