# ROBUSTEZ_MASA_DESI.py                        

#!/usr/bin/env python3
"""                       
ROBUSTEZ_MASA_DESI.py
ROBUSTNESS BY DESI MASS - MASS THRESHOLD CONFIRMATION"""                       
import numpy as np
import json
from scipy import stats

print("🎯 ROBUSTNESS BY DESI MASS - THRESHOLD CONFIRMATION")
print("=" * 60)

# LOAD DESI DATA
print("📥 LOADING DESI DATA...")
data = np.load('lrg_analysis_subset.npz')
proxy_masa = data['PROXY_MASA']  # FIBERFLUX_R
redshift = data['Z']

print(f"📊 DESI LRG DATASET:")
print(f"   • Galaxies: {len(proxy_masa):,}")
print(f"   • Mass proxy: {proxy_masa.min():.3f} - {proxy_masa.max():.3f}")

# LOAD RUST MODULE
try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Rust module loaded")
except ImportError:
    print("❌ Rust module not available")
    exit()

# CONFIGURATION
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8

# 🎯 DEFINE GROUPS BY MASS (TERCILES)
q33 = np.percentile(proxy_masa, 33)
q66 = np.percentile(proxy_masa, 66)

print(f"🔧 DESI MASS THRESHOLDS:")
print(f"   • Q33 (Low mass):  < {q33:.3f}")
print(f"   • Q66 (Mid mass): {q33:.3f} - {q66:.3f}")
print(f"   • High mass:        > {q66:.3f}")

grupos_masa = [
    (proxy_masa < q33, "BAJA_MASA", f"< {q33:.3f}"),
    ((proxy_masa >= q33) & (proxy_masa < q66), "MEDIA_MASA", f"{q33:.3f} - {q66:.3f}"),
    (proxy_masa >= q66, "ALTA_MASA", f"> {q66:.3f}")
]

# REDSHIFT BINS
bins_redshift = [(0.4, 0.6), (0.8, 1.0)]

resultados_robustez = {}

# 🎯 ANALYSIS BY MASS GROUP
for mask_masa, label_masa, rango_masa in grupos_masa:
    print(f"\n📊 GROUP: {label_masa} ({rango_masa})")
    print(f"   • Galaxies in group: {np.sum(mask_masa):,}")

    evoluciones_grupo = []

    for z_min, z_max in bins_redshift:
        mask_z = (redshift >= z_min) & (redshift < z_max)
        mask_total = mask_masa & mask_z
        galaxias_grupo = proxy_masa[mask_total]

        print(f"   • z={z_min}-{z_max}: {len(galaxias_grupo):,} galaxies")

    # 🚀 CALCULATE EVOLUTION BY SAMPLING
    for semilla in range(40):
        np.random.seed(semilla)

        # HIGH-Z SAMPLES (0.8-1.0)
        mask_high = mask_masa & (redshift >= 0.8) & (redshift < 1.0)
        galaxias_high = proxy_masa[mask_high]

        # LOW-Z SAMPLES (0.4-0.6)
        mask_low = mask_masa & (redshift >= 0.4) & (redshift < 0.6)
        galaxias_low = proxy_masa[mask_low]

        if len(galaxias_high) >= 200 and len(galaxias_low) >= 200:
            sample_high = np.random.choice(galaxias_high, size=min(200, len(galaxias_high)), replace=False)
            sample_low = np.random.choice(galaxias_low, size=min(200, len(galaxias_low)), replace=False)

            bispectra_high = calcular_bispectro_triangular(sample_high.tolist(), l_max, configs_escalenas)
            bispectra_low = calcular_bispectro_triangular(sample_low.tolist(), l_max, configs_escalenas)

            if bispectra_high and bispectra_low:
                esc_high = np.mean([abs(b) for b in bispectra_high])
                esc_low = np.mean([abs(b) for b in bispectra_low])

                evol_esc = esc_low / esc_high if esc_high > 0 else 0
                evoluciones_grupo.append(evol_esc)

    # 📊 CALCULATE GROUP SIGNIFICANCE
    if evoluciones_grupo:
        media_evol = np.mean(evoluciones_grupo)
        std_evol = np.std(evoluciones_grupo, ddof=1)
        n_muestras = len(evoluciones_grupo)

        sem_evol = std_evol / np.sqrt(n_muestras)
        t_evol = abs(media_evol - 1.1) / sem_evol
        p_evol = 2 * (1 - stats.t.cdf(t_evol, n_muestras-1))
        sigma_evol = stats.norm.ppf(1 - p_evol/2)

        resultados_robustez[label_masa] = {
            'rango_masa': rango_masa,
            'n_galaxias': int(np.sum(mask_masa)),
            'evolucion_media': float(media_evol),
            'significancia': float(sigma_evol),
            'n_muestras': n_muestras,
            'p_value': float(p_evol)
        }

        print(f"   ✅ Evolution: {media_evol:.1f}×")
        print(f"   📈 Significance: {sigma_evol:.2f}σ")

        if sigma_evol >= 3.0:
            print(f"   🎯 SIGNAL DETECTED")
        else:
            print(f"   🔍 weak signal")

# 📋 COMPARATIVE SUMMARY
print(f"\n📊 DESI MASS ROBUSTNESS SUMMARY:")
print("=" * 50)

for grupo, resultados in resultados_robustez.items():
    sig = resultados['significancia']
    evol = resultados['evolucion_media']
    n_gal = resultados['n_galaxias']

    print(f"   {grupo:>12}: {evol:5.1f}×  |  {sig:5.2f}σ  |  {n_gal:>8,} galaxies")

# 🎯 IDENTIFY THRESHOLD PATTERN
significancias = [r['significancia'] for r in resultados_robustez.values()]
if len(significancias) == 3:
    baja, media, alta = significancias

    print(f"\n🎯 THRESHOLD PATTERN:")
    if alta > media and alta > baja and alta >= 3.0:
        print(f"   ✅ CONFIRMED: Signal is concentrated in HIGH MASS")
        print(f"   🚀 Threshold mechanism operating")
    elif media >= 3.0 and alta >= 3.0:
        print(f"   📈 Signal in mid and high mass")
    else:
        print(f"   🔍 Pattern not clear")

# 💾 SAVE ROBUSTNESS RESULTS
resultados_completos = {
    'umbrales_masa': {
        'q33': float(q33),
        'q66': float(q66)
    },
    'resultados_por_grupo': resultados_robustez,
    'interpretacion': 'DESI LRG mass robustness analysis'
}

with open('ROBUSTEZ_MASA_DESI_LRG.json', 'w') as f:
    json.dump(resultados_completos, f, indent=2)

print(f"\n✅ ROBUSTNESS ANALYSIS COMPLETED")
print(f"   • File: ROBUSTEZ_MASA_DESI_LRG.json")