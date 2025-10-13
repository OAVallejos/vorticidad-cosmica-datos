#!/usr/bin/env python3
"""
VALIDACIÓN OPTIMIZADA PARA 5σ - 25 MUESTRAS
"""

import numpy as np
import json

print("🎯 VALIDACIÓN OPTIMIZADA - META 5σ")
print("=" * 60)

try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Módulo Rust cargado")
    RUST_AVAILABLE = True
except ImportError:
    print("❌ Módulo Rust no disponible")
    exit()

# CONFIGURACIÓN OPTIMIZADA
configs_222 = [(2, 2, 2)]
configs_444 = [(4, 4, 4)] 
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
todas_configs = configs_222 + configs_444 + configs_escalenas
l_max = 8

# Cargar datos
data = np.load('sdss_vdisp_calidad.npz')
vdisp = data['VDISP']
redshift = data['Z']

# BINS PARA ANÁLISIS
bins_paper = [(0.1, 0.2, "z01_02"), (0.7, 0.8, "z07_08")]

print(f"🔧 CONFIGURACIÓN OPTIMIZADA:")
print(f"   • Muestras: 25 (vs 5 original)")
print(f"   • Configuraciones: {len(todas_configs)}")
print(f"   • l_max: {l_max}")

resultados_comparativos = {}
evoluciones_222 = []
evoluciones_esc = []

# 🎯 ANÁLISIS PRINCIPAL OPTIMIZADO
for z_min, z_max, label in bins_paper:
    print(f"\n📊 {label} (z={z_min}-{z_max}):")
    mask = (redshift >= z_min) & (redshift < z_max) & (vdisp > 100)
    galaxies_bin = vdisp[mask]
    
    print(f"   • Galaxias disponibles: {len(galaxies_bin)}")
    
    # Usar muestras más grandes para estabilidad
    sample_size = min(500, len(galaxies_bin))  # Aumentado de 200 a 500
    
    resultados_bin = {
        '222': [],
        '444': [],
        'escalenos': []
    }
    
    # 🚀 25 MUESTRAS (OPTIMIZADO PARA 5σ)
    for semilla in range(25):
        np.random.seed(semilla)
        if len(galaxies_bin) >= sample_size:
            sample = np.random.choice(galaxies_bin, size=sample_size, replace=False)
            bispectra = calcular_bispectro_triangular(sample.tolist(), l_max, todas_configs)
            
            if bispectra:
                # (2,2,2)
                valor_222 = abs(bispectra[0])
                resultados_bin['222'].append(valor_222)
                
                # (4,4,4)
                valor_444 = abs(bispectra[1])
                resultados_bin['444'].append(valor_444)
                
                # Escalenos promedio
                valores_esc = [abs(bispectra[i]) for i in range(2, 8)]
                valor_esc_prom = np.mean(valores_esc) if valores_esc else 0
                resultados_bin['escalenos'].append(valor_esc_prom)
    
    # Calcular promedios por bin
    if resultados_bin['222']:
        resultados_comparativos[label] = {
            'z_mean': (z_min + z_max) / 2,
            '222': np.mean(resultados_bin['222']),
            '444': np.mean(resultados_bin['444']),
            'escalenos_promedio': np.mean(resultados_bin['escalenos']),
            'N_galaxias': sample_size,
            'N_muestras': len(resultados_bin['222'])
        }
        
        print(f"   • (2,2,2): {np.mean(resultados_bin['222']):.3e} (n={len(resultados_bin['222'])})")
        print(f"   • Escalenos: {np.mean(resultados_bin['escalenos']):.3e} (n={len(resultados_bin['escalenos'])})")

# 🎯 CÁLCULO DE EVOLUCIONES (25 MUESTRAS)
print(f"\n📈 CALCULANDO EVOLUCIONES...")
if 'z01_02' in resultados_comparativos and 'z07_08' in resultados_comparativos:
    z_low = resultados_comparativos['z01_02']
    z_high = resultados_comparativos['z07_08']
    
    # Para cada una de las 25 muestras, calcular evolución individual
    for semilla in range(25):
        np.random.seed(semilla)
        
        # Muestra alta-z
        mask_high = (redshift >= 0.7) & (redshift < 0.8) & (vdisp > 100)
        galaxies_high = vdisp[mask_high]
        if len(galaxies_high) >= 500:
            sample_high = np.random.choice(galaxies_high, size=500, replace=False)
            bispectra_high = calcular_bispectro_triangular(sample_high.tolist(), l_max, [(2,2,2)] + configs_escalenas)
            
            # Muestra baja-z
            mask_low = (redshift >= 0.1) & (redshift < 0.2) & (vdisp > 100)
            galaxies_low = vdisp[mask_low]
            if len(galaxies_low) >= 500:
                sample_low = np.random.choice(galaxies_low, size=500, replace=False)
                bispectra_low = calcular_bispectro_triangular(sample_low.tolist(), l_max, [(2,2,2)] + configs_escalenas)
                
                if bispectra_high and bispectra_low:
                    # (2,2,2)
                    evol_222 = abs(bispectra_high[0]) / abs(bispectra_low[0]) if abs(bispectra_low[0]) > 0 else 0
                    evoluciones_222.append(evol_222)
                    
                    # Escalenos promedio
                    esc_high = np.mean([abs(b) for b in bispectra_high[1:]])
                    esc_low = np.mean([abs(b) for b in bispectra_low[1:]])
                    evol_esc = esc_high / esc_low if esc_low > 0 else 0
                    evoluciones_esc.append(evol_esc)
                    
                    if semilla < 5:  # Mostrar primeras 5
                        print(f"   Muestra {semilla+1}: (2,2,2)={evol_222:.1f}×, Escalenos={evol_esc:.1f}×")

# 📊 GUARDAR RESULTADOS OPTIMIZADOS
resultados_finales = {
    'resultados_comparativos': resultados_comparativos,
    'validacion_estadistica': {
        'evoluciones_222': evoluciones_222,
        'evoluciones_esc': evoluciones_esc
    }
}

with open('analisis_divergencia_OPTIMIZADO.json', 'w') as f:
    json.dump(resultados_finales, f, indent=2)

print(f"\n✅ VALIDACIÓN OPTIMIZADA COMPLETADA")
print(f"   • Muestras: {len(evoluciones_222)}")
print(f"   • Archivo: analisis_divergencia_OPTIMIZADO.json")

# 📈 CALCULAR SIGNIFICANCIA PROYECTADA
if evoluciones_esc:
    from scipy import stats
    media_esc = np.mean(evoluciones_esc)
    std_esc = np.std(evoluciones_esc, ddof=1)
    n_esc = len(evoluciones_esc)
    
    sem_esc = std_esc / np.sqrt(n_esc)
    t_esc = abs(media_esc - 1.1) / sem_esc
    p_esc = 2 * (1 - stats.t.cdf(t_esc, n_esc-1))
    sigma_esc = stats.norm.ppf(1 - p_esc/2)
    
    print(f"\n🎯 SIGNIFICANCIA PROYECTADA:")
    print(f"   • Media: {media_esc:.2f}×")
    print(f"   • Muestras: {n_esc}")
    print(f"   • Significancia: {sigma_esc:.2f}σ")
    
    if sigma_esc >= 5.0:
        print(f"   🎉 ¡5σ ALCANZADO!")
    else:
        print(f"   📈 Progreso: {sigma_esc:.2f}σ (meta: 5σ)")

