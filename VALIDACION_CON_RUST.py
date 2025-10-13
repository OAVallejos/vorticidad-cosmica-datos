#!/usr/bin/env python3
"""
VALIDACIÓN USANDO CÓDIGO RUST EXISTENTE - SIN DEPENDENCIAS EXTERNAS
"""

import numpy as np
import json

print("🎯 VALIDACIÓN USANDO MÓDULO RUST EXISTENTE")
print("=" * 60)

try:
    from cosmic_vorticity import calcular_bispectro_triangular
    print("✅ Módulo Rust cargado correctamente")
    RUST_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error cargando módulo Rust: {e}")
    print("   Compila primero: cd rust_final && cargo build --release")
    RUST_AVAILABLE = False
    exit()

# CONFIGURACIONES PARA COMPARAR (2,2,2) vs ESCALENOS
configs_222 = [(2, 2, 2)]
configs_444 = [(4, 4, 4)] 
configs_escalenas = [(1, 2, 3), (1, 3, 4), (2, 3, 5), (1, 4, 5), (2, 4, 6), (3, 4, 7)]

todas_configs = configs_222 + configs_444 + configs_escalenas
l_max = 8

# Cargar datos
data = np.load('sdss_vdisp_calidad.npz')
vdisp = data['VDISP']
redshift = data['Z']

bins_paper = [(0.1, 0.2, "z01_02"), (0.7, 0.8, "z07_08")]

print("\n🔍 COMPARANDO (2,2,2) vs CONFIGURACIONES ESCALENAS")
print("=" * 60)

resultados_comparativos = {}

for z_min, z_max, label in bins_paper:
    print(f"\n📊 {label} (z={z_min}-{z_max}):")
    mask = (redshift >= z_min) & (redshift < z_max) & (vdisp > 100)
    sample = vdisp[mask][:200]
    
    if len(sample) >= 100:
        bispectra = calcular_bispectro_triangular(sample.tolist(), l_max, todas_configs)
        
        # Extraer valores
        valor_222 = abs(bispectra[0])  # Primera configuración
        valor_444 = abs(bispectra[1])  # Segunda configuración
        valores_escalenos = [abs(bispectra[i]) for i in range(2, 8)]  # Resto son escalenos
        
        media_escalenos = np.mean(valores_escalenos) if valores_escalenos else 0
        
        resultados_comparativos[label] = {
            'z_mean': (z_min + z_max) / 2,
            '222': valor_222,
            '444': valor_444,
            'escalenos_promedio': media_escalenos,
            'N_galaxias': len(sample)
        }
        
        print(f"   (2,2,2): {valor_222:.3e}")
        print(f"   (4,4,4): {valor_444:.3e}")
        print(f"   Escalenos (prom): {media_escalenos:.3e}")

# ANÁLISIS DE LA DIVERGENCIA
print("\n🚨 ANÁLISIS DE DIVERGENCIA")
print("=" * 60)

if 'z01_02' in resultados_comparativos and 'z07_08' in resultados_comparativos:
    z_low = resultados_comparativos['z01_02']
    z_high = resultados_comparativos['z07_08']
    
    # Calcular evoluciones
    evol_222 = z_high['222'] / z_low['222'] if z_low['222'] > 0 else 0
    evol_444 = z_high['444'] / z_low['444'] if z_low['444'] > 0 else 0
    evol_esc = z_high['escalenos_promedio'] / z_low['escalenos_promedio'] if z_low['escalenos_promedio'] > 0 else 0
    
    print("EVOLUCIONES (z=0.7 vs z=0.1):")
    print(f"   (2,2,2): {evol_222:.1f}×")
    print(f"   (4,4,4): {evol_444:.1f}×")
    print(f"   Escalenos: {evol_esc:.1f}×")
    
    print("\n🔍 PATRÓN DETECTADO:")
    if evol_222 > 10 and evol_esc < 1.5:
        print("   🚨 (2,2,2) ES UN OUTLIER")
        print("   - Muestra evolución extrema (>10×)")
        print("   - Inconsistente con escalenos (<1.5×)")
        print("   - Posible artefacto específico de (2,2,2)")
    elif evol_222 > 2 and evol_444 > 2 and evol_esc > 1.5:
        print("   📈 PATRÓN CONSISTENTE")
        print("   - Todas las configuraciones muestran evolución")
        print("   - Posible señal física real")
    else:
        print("   📊 PATRÓN MIXTO")
        print("   - Necesita más investigación")

# VALIDACIÓN CON MÚLTIPLES MUESTRAS
print("\n📊 VALIDACIÓN ESTADÍSTICA ROBUSTA")
print("=" * 60)

z_min, z_max = 0.7, 0.8
mask = (redshift >= z_min) & (redshift < z_max) & (vdisp > 100)
galaxies_bin = vdisp[mask]

evoluciones_222 = []
evoluciones_esc = []

for semilla in range(5):
    np.random.seed(semilla)
    if len(galaxies_bin) >= 200:
        # Muestra de z=0.7-0.8
        sample_high = np.random.choice(galaxies_bin, size=200, replace=False)
        bispectra_high = calcular_bispectro_triangular(sample_high.tolist(), l_max, [(2,2,2)] + configs_escalenas)
        
        # Muestra de z=0.1-0.2 para referencia
        mask_low = (redshift >= 0.1) & (redshift < 0.2) & (vdisp > 100)
        galaxies_low = vdisp[mask_low]
        if len(galaxies_low) >= 200:
            sample_low = np.random.choice(galaxies_low, size=200, replace=False)
            bispectra_low = calcular_bispectro_triangular(sample_low.tolist(), l_max, [(2,2,2)] + configs_escalenas)
            
            if bispectra_high and bispectra_low:
                # (2,2,2)
                evol_222 = abs(bispectra_high[0]) / abs(bispectra_low[0]) if abs(bispectra_low[0]) > 0 else 0
                # Escalenos promedio
                esc_high = np.mean([abs(b) for b in bispectra_high[1:]])
                esc_low = np.mean([abs(b) for b in bispectra_low[1:]])
                evol_esc = esc_high / esc_low if esc_low > 0 else 0
                
                evoluciones_222.append(evol_222)
                evoluciones_esc.append(evol_esc)
                
                print(f"Muestra {semilla+1}: (2,2,2)={evol_222:.1f}×, Escalenos={evol_esc:.1f}×")

if evoluciones_222 and evoluciones_esc:
    print(f"\n📈 ESTADÍSTICAS CONSOLIDADAS:")
    print(f"(2,2,2): {np.mean(evoluciones_222):.1f}× ± {np.std(evoluciones_222):.1f}")
    print(f"Escalenos: {np.mean(evoluciones_esc):.1f}× ± {np.std(evoluciones_esc):.1f}")
    
    # Test de consistencia
    diff = abs(np.mean(evoluciones_222) - np.mean(evoluciones_esc))
    if diff > 5:
        print("🚨 ALTA INCONSISTENCIA - (2,2,2) probablemente es artefacto")
    elif diff > 2:
        print("⚠️  Inconsistencia moderada - necesita investigación")
    else:
        print("✅ Consistencia aceptable")

print("\n🎯 CONCLUSIÓN FINAL:")
print("=" * 60)
if evoluciones_222 and np.mean(evoluciones_222) > 10 and np.mean(evoluciones_esc) < 2:
    print("❌ EL RESULTADO DE 77.3× EN (2,2,2) ES PROBABLEMENTE UN ARTEFACTO")
    print("   - Inconsistente con configuraciones escalenas")
    print("   - Alta variabilidad entre muestras")
    print("   - No se debe reportar como descubrimiento")
else:
    print("✅ EL RESULTADO PARECE ROBUSTO")
    print("   - Consistencia entre configuraciones")
    print("   - Puede proceder con cautela")

# Guardar resultados para análisis posterior
with open('analisis_divergencia.json', 'w') as f:
    json.dump({
        'resultados_comparativos': resultados_comparativos,
        'validacion_estadistica': {
            'evoluciones_222': evoluciones_222,
            'evoluciones_esc': evoluciones_esc
        }
    }, f, indent=2)

print(f"\n💾 Resultados guardados: analisis_divergencia.json")
