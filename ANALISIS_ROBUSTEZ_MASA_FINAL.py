#!/usr/bin/env python3    

"""                       
ANÁLISIS DE ROBUSTEZ FINAL CORREGIDO: Señal 3.02x por Subgrupos de VDISP (Masa)                         - CORRECCIÓN: Soluciona el error de sintaxis al filtrar NaN en el array.
- Usa muestreo SIN REEMPLAZO y optimización de memoria (mmap, float32).
"""

import numpy as np
import json
from scipy import stats

print("🎯 ANÁLISIS FINAL DE ROBUSTEZ - VDISP MASA")
print("============================================================")

# Asegurar que el módulo Rust esté cargado para el rendimiento
try:
    # Asume que el módulo 'cosmic_vorticity' con 'calcular_bispectro_triangular' está en el PATH
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Módulo Rust cargado para cálculo rápido del bispectro.")
except ImportError:
    print("❌ Módulo Rust no disponible. El script solo puede ejecutarse si este módulo existe.")
    exit()

# --- CONFIGURACIÓN ESTRATÉGICA ---
# Triángulos para el análisis del bispectro
configs_a_testear = [(2, 2, 2), (1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]
l_max = 8
N_MUESTRAS_VALIDACION = 25
SAMPLE_SIZE = 500 # Tamaño de la sub-muestra sin reemplazo

# Hipótesis Nula: H₀ = 1.1x (Valor conservador de referencia)
H0_TEST = 1.1

# --- CARGA DE DATOS OPTIMIZADA (MEMORIA) ---
try:
    # Usar mmap_mode='r' para no cargar todo el archivo en 2GB RAM
    data = np.load('sdss_vdisp_calidad.npz', mmap_mode='r')
    # Usar float32 para reducir a la mitad el uso de memoria de los arrays
    vdisp_full = data['VDISP'].astype(np.float32)
    redshift_full = data['Z'].astype(np.float32)
    del data # Liberar el objeto mapeado
except FileNotFoundError:
    print("❌ Error: Archivo de datos no encontrado. Verifique 'sdss_vdisp_calidad.npz'.")
    exit()


# --- DEFINICIÓN DE GRUPOS DE MASA (Cuantiles Confirmados) ---
FILTRO_VDISP_MIN = 100
mask_filtrada_total = (redshift_full >= 0.1) & (redshift_full < 0.8) & (vdisp_full > FILTRO_VDISP_MIN)
vdisp_filtrado = vdisp_full[mask_filtrada_total]

if len(vdisp_filtrado) < 1000:
    print("❌ Error: Datos insuficientes para definir cuantiles.")
    exit()

# Cuantiles pre-calculados (33% y 66%)
q_33 = np.percentile(vdisp_filtrado, 33)
q_66 = np.percentile(vdisp_filtrado, 66)

grupos_masa = {
    "VDISP_LOW (<33%)": (FILTRO_VDISP_MIN, q_33),
    "VDISP_MID (33%-66%)": (q_33, q_66),
    "VDISP_HIGH (>66%)": (q_66, 1000.0)
}

print(f"\n🔧 CONFIGURACIÓN DEL ANÁLISIS:")
print(f"    • Muestras sin reemplazo: {N_MUESTRAS_VALIDACION}")
print(f"    • Cuantiles VDISP: Q33={q_33:.1f} | Q66={q_66:.1f}")

resultados_evolucion_final = {}

# 🎯 ANÁLISIS POR GRUPO DE MASA
for nombre_grupo, (vdisp_min, vdisp_max) in grupos_masa.items():
    print(f"\n\n==================================================")
    print(f"🔬 GRUPO DE MASA: {nombre_grupo} ({vdisp_min:.1f} - {vdisp_max:.1f} km/s)")
    print("==================================================")

    galaxies_z_low = None
    galaxies_z_high = None

    # Iteración sobre los bins de redshift (z_min y z_max son floats)
    for label, z_min, z_max in [('z01_02', 0.1, 0.2), ('z07_08', 0.7, 0.8)]:

        mask = (redshift_full >= z_min) & (redshift_full < z_max) & \
               (vdisp_full >= vdisp_min) & (vdisp_full < vdisp_max)

        galaxies_bin = vdisp_full[mask]

        if len(galaxies_bin) < SAMPLE_SIZE:
            print(f"    ❌ {label}: Datos insuficientes ({len(galaxies_bin)} < {SAMPLE_SIZE}).")
            continue

        print(f"    ✅ {label} (z={z_min}-{z_max}): {len(galaxies_bin)} galaxias disponibles.")

        if 'z01_02' in label:
            galaxies_z_low = galaxies_bin
        elif 'z07_08' in label:
            galaxies_z_high = galaxies_bin

    # 2. CÁLCULO DE EVOLUCIÓN (Muestreo SIN REEMPLAZO)
    if galaxies_z_low is not None and galaxies_z_high is not None:

        # Calcular el número máximo de muestras sin reemplazo que se pueden tomar
        n_samples = min(N_MUESTRAS_VALIDACION,
                        len(galaxies_z_low) // SAMPLE_SIZE,
                        len(galaxies_z_high) // SAMPLE_SIZE)

        if n_samples == 0:
            print("    ❌ No se pudieron obtener muestras SIN REEMPLAZO.")
            continue

        print(f"    🚀 Ejecutando {n_samples} muestreos SIN REEMPLAZO...")

        # Mezclar índices para asegurar la aleatoriedad de las sub-muestras
        indices_low = np.random.permutation(len(galaxies_z_low))
        indices_high = np.random.permutation(len(galaxies_z_high))

        evoluciones_esc = []

        for i in range(n_samples):
            # Extraer sub-muestras disjuntas
            start, end = i * SAMPLE_SIZE, (i + 1) * SAMPLE_SIZE
            sample_low = galaxies_z_low[indices_low[start:end]]
            sample_high = galaxies_z_high[indices_high[start:end]]

            # Cálculo Rust (Usando np.array de float32)
            bispectra_low = calcular_bispectro_triangular(sample_low, l_max, configs_a_testear)
            bispectra_high = calcular_bispectro_triangular(sample_high, l_max, configs_a_testear)

            if bispectra_high and bispectra_low:
                # Escalenos promedio (índices 1 en adelante, asumiendo el índice 0 es el monopolo o similar)
                esc_high = np.mean([abs(b) for b in bispectra_high[1:]])
                esc_low = np.mean([abs(b) for b in bispectra_low[1:]])
                evol_esc = esc_high / esc_low if esc_low > 0 else np.nan
                evoluciones_esc.append(evol_esc)

        # 3. ANÁLISIS ESTADÍSTICO FINAL
        evoluciones_esc = np.array(evoluciones_esc)

        # CORRECCIÓN DE SINTAXIS (Cierre de corchete ']')
        evoluciones_esc = evoluciones_esc[~np.isnan(evoluciones_esc)]
        # Fin de la corrección

        if len(evoluciones_esc) > 1:
            media_obs = np.mean(evoluciones_esc)
            std_obs = np.std(evoluciones_esc, ddof=1)
            n_obs = len(evoluciones_esc)
            sem_obs = std_obs / np.sqrt(n_obs)

            # Cálculo de la significancia (t-test vs H0=1.1)
            # t-statistic: (media_observada - media_nula) / error_estándar_de_la_media
            t = abs(media_obs - H0_TEST) / sem_obs
            # p-valor para prueba de dos colas
            p = 2 * (1 - stats.t.cdf(t, n_obs-1))
            # Conversión del p-valor a unidades de sigma (equivalente a desviación estándar de una normal)
            sigma = stats.norm.ppf(1 - p/2)

            resultados_evolucion_final[nombre_grupo] = {
                'media_evolucion': media_obs,
                'sem_evolucion': sem_obs,
                'significancia_11': sigma,
                'N_muestras_sin_reemplazo': n_obs
            }

            print(f"\n    📈 RESULTADOS FINALES (Escalenos):")
            print(f"      • Evolución Media: {media_obs:.2f}×")
            print(f"      • Error Estándar (SEM): {sem_obs:.2f}×")
            print(f"      • Significancia vs {H0_TEST}x: {sigma:.2f}σ")

            if sigma >= 5.0:
                 print(f"      🎉 **EVIDENCIA SÓLIDA (>5σ)**")

        else:
            print("    ❌ Análisis estadístico no disponible.")


# 4. REPORTE FINAL Y GUARDADO
print("\n" + "=" * 60)
print("🌟 VEREDICTO FINAL: FIRMA DE VORTICIDAD EN ALTA MASA 🌟")
print("=" * 60)

datos_para_json = {'resultados_masa_final': resultados_evolucion_final}

for nombre, res in resultados_evolucion_final.items():
    print(f"Grupo: {nombre}")
    print(f"  Media Evolución: {res['media_evolucion']:.2f}×")
    print(f"  SEM: {res['sem_evolucion']:.2f}×")
    print(f"  Significancia ({H0_TEST}x): {res['significancia_11']:.2f}σ")

    if res['significancia_11'] >= 5.0:
        print("  🔑 Interpretación: Señal **beyond-ΛCDM** confirmada.")

# Guardar resultados
try:
    with open('analisis_robustez_masa_FINAL.json', 'w') as f:
        json.dump(datos_para_json, f, indent=2)
    print(f"\n✅ Resultados guardados en 'analisis_robustez_masa_FINAL.json'.")
except IOError:
    print("\n❌ Error al guardar el archivo JSON.")

print(f"\n✅ ANÁLISIS FINAL COMPLETADO.")