# ANALISIS_RUIDO_MUESTRA_DESI_ALTAm.py

#!/usr/bin/env python3
"""
ANÁLISIS DE ROBUSTEZ: RUIDO DE MUESTREO EN ALTA MASA (H0=1.1x)
"""
import numpy as np
import json
from scipy import stats

print("🎯 ANÁLISIS DE RUIDO DE MUESTREO (ALTA MASA)")
print("=" * 60)

# CARGAR DATOS (ASUME LOS MISMOS DATOS LRG)
data = np.load('lrg_analysis_subset.npz')
proxy_masa = data['PROXY_MASA']
redshift = data['Z']

# CARGAR MÓDULO RUST
try:
    from cosmic_vorticity import calcular_bispectro_triangular
    # print("✅ Módulo Rust cargado")
except ImportError:
    print("❌ Módulo Rust no disponible")
    exit()

# CONFIGURACIÓN ESPECÍFICA
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8
N_ITERACIONES = 40  # Usamos las iteraciones más altas para estabilidad

# 1. DEFINIR UMBRALES DE ALTA MASA (Q66)
q66 = np.percentile(proxy_masa, 66)
mask_alta_masa = proxy_masa >= q66

print(f"🔧 CONFIGURACIÓN ALTA MASA:")
print(f"   • Umbral (Q66): > {q66:.3f}")
print(f"   • Galaxias en grupo: {np.sum(mask_alta_masa):,}")
print(f"   • Muestras (N): {N_ITERACIONES}")

# Definir las máscaras de redshift para Alta Masa
mask_high_z = mask_alta_masa & (redshift >= 0.8) & (redshift < 1.0)
mask_low_z = mask_alta_masa & (redshift >= 0.4) & (redshift < 0.6)
galaxias_high = proxy_masa[mask_high_z]
galaxias_low = proxy_masa[mask_low_z]

print(f"   • Alta-z (0.8-1.0): {len(galaxias_high):,} galaxias") # Este es el cuello de botella
print(f"   • Baja-z (0.4-0.6): {len(galaxias_low):,} galaxias")

# 2. RANGO DE TAMAÑOS DE SUBLOTE (SAMPLE SIZE) PARA PROBAR EL RUIDO
# Probaremos el tamaño máximo (200) y uno más pequeño (100)
TAMAÑOS_MUESTRA = [100, 200]
resultados_ruido = {}

print("\n📊 TEST DE SENSIBILIDAD AL TAMAÑO DE LA MUESTRA:")

for sample_size in TAMAÑOS_MUESTRA:
    print(f"\n   -> PROBANDO SAMPLE SIZE = {sample_size}")
    evoluciones_test = []

    if len(galaxias_high) < sample_size or len(galaxias_low) < sample_size:
        print(f"      ❌ Tamaño de muestra {sample_size} es demasiado grande para un bin. Saltando.")
        continue

    for semilla in range(N_ITERACIONES):
        np.random.seed(semilla)
        
        # MUESTREO
        sample_high = np.random.choice(galaxias_high, size=sample_size, replace=False)
        sample_low = np.random.choice(galaxias_low, size=sample_size, replace=False)

        # CÁLCULO DE BISPECTRO
        bispectra_high = calcular_bispectro_triangular(sample_high.tolist(), l_max, configs_escalenas)
        bispectra_low = calcular_bispectro_triangular(sample_low.tolist(), l_max, configs_escalenas)

        if bispectra_high and bispectra_low:
            esc_high = np.mean([abs(b) for b in bispectra_high])
            esc_low = np.mean([abs(b) for b in bispectra_low])

            evol_esc = esc_low / esc_high if esc_high > 0 else 0
            evoluciones_test.append(evol_esc)

    # 3. CÁLCULO DE SIGNIFICANCIA (H0 = 1.1x)
    if evoluciones_test:
        media_evol = np.mean(evoluciones_test)
        std_evol = np.std(evoluciones_test, ddof=1)
        n_muestras = len(evoluciones_test)

        sem_evol = std_evol / np.sqrt(n_muestras)
        t_evol = abs(media_evol - 1.1) / sem_evol  # Usando H0 = 1.1x
        p_evol = 2 * (1 - stats.t.cdf(t_evol, n_muestras-1))
        sigma_evol = stats.norm.ppf(1 - p_evol/2)

        resultados_ruido[sample_size] = {
            'evolucion_media': float(media_evol),
            'significancia': float(sigma_evol),
            'std_evol': float(std_evol)
        }

        print(f"      ✅ Evolución media: {media_evol:.2f}×")
        print(f"      📈 Significancia (vs 1.1x): {sigma_evol:.2f}σ")
        print(f"      • Desviación Std: {std_evol:.1f}")

# 4. INTERPRETACIÓN DE SENSIBILIDAD
if 100 in resultados_ruido and 200 in resultados_ruido:
    sig_100 = resultados_ruido[100]['significancia']
    sig_200 = resultados_ruido[200]['significancia']
    
    print("\n🔬 INTERPRETACIÓN DE SENSIBILIDAD:")
    if sig_200 > sig_100:
        print(f"   ✅ Confirmación de Ruido de Muestreo: La significancia AUMENTA ({sig_100:.2f}σ -> {sig_200:.2f}σ)")
        print(f"   Esto sugiere que el resultado de Alta Masa está LIMITADO por la estadística de la muestra (N_galaxias).")
    else:
        print(f"   🔍 La significancia no aumentó significativamente o disminuyó, lo cual es inusual.")

print(f"\n✅ ANÁLISIS DE RUIDO COMPLETADO")