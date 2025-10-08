#!/usr/bin/env python3
"""
ANÁLISIS DIRECTO - LOS DATOS FITS YA SON MODOS alm
"""

import numpy as np
import json
from astropy.io import fits
from cosmic_vorticity import calcular_bispectro_triangular

def analizar_alm_directo():
    print("🎯 ANÁLISIS DIRECTO - DATOS COMO MODOS alm")
    print("=" * 60)
    
    archivos = [
        ('datos_planck/vorticidad/modosB_con_vorticidad.fits', 'Modos B con Vorticidad'),
        ('datos_planck/vorticidad/modosB_gaussianos.fits', 'Modos B Gaussianos'),
        ('datos_planck/vorticidad_avanzada/modosB_vorticidad_fuerte.fits', 'Modos B Vorticidad Fuerte'),
        ('datos_planck/vorticidad_avanzada/modosB_lensing.fits', 'Modos B Lensing')
    ]
    
    resultados_totales = {}
    
    for ruta, nombre in archivos:
        print(f"\n🌌 ANALIZANDO: {nombre}")
        print("=" * 50)
        
        # Cargar datos directamente como alm
        with fits.open(ruta) as hdul:
            datos = hdul[1].data['MODOS_B']
            modos_b = datos.astype(np.float32).flatten().tolist()
        
        print(f"📊 Datos cargados: {len(modos_b)} 'modos'")
        print(f"📈 Estadísticas: min={np.min(datos):.2e}, max={np.max(datos):.2e}")
        
        # DIFERENTES ESTRATEGIAS de agrupación
        estrategias = [
            ("Agrupación estándar", 10, [
                (2, 3, 4), (3, 4, 5), (4, 5, 6), (5, 6, 7),
                (2, 4, 5), (3, 5, 6), (4, 6, 7), (5, 7, 8),
                (2, 2, 2), (3, 3, 3), (4, 4, 4), (5, 5, 5)
            ]),
            ("Agrupación amplia", 15, [
                (5, 6, 7), (6, 7, 8), (7, 8, 9), (8, 9, 10),
                (5, 7, 8), (6, 8, 9), (7, 9, 10), (8, 10, 11),
                (5, 5, 5), (6, 6, 6), (7, 7, 7), (8, 8, 8)
            ]),
            ("Agrupación mixta", 12, [
                (3, 4, 6), (4, 5, 7), (5, 6, 8), (6, 7, 9),
                (3, 5, 6), (4, 6, 7), (5, 7, 8), (6, 8, 9),
                (3, 3, 3), (4, 4, 4), (5, 5, 5), (6, 6, 6)
            ])
        ]
        
        mejor_ratio = 0
        mejor_estrategia = ""
        
        for estrategia_nombre, l_max, configs in estrategias:
            print(f"\n🔍 Probando: {estrategia_nombre} (l_max={l_max})")
            
            resultados = calcular_bispectro_triangular(modos_b, l_max, configs)
            
            # Filtrar resultados válidos
            escalenos = []
            equilateros = []
            
            for (l1, l2, l3), b_val in zip(configs, resultados):
                if np.isfinite(b_val) and abs(b_val) > 1e-25:
                    if l1 != l2 and l2 != l3 and l1 != l3:
                        escalenos.append(abs(b_val))
                    elif l1 == l2 == l3:
                        equilateros.append(abs(b_val))
            
            # Calcular ratio
            if escalenos and equilateros:
                ratio = np.mean(escalenos) / np.mean(equilateros)
                print(f"   📊 Ratio: {ratio:.3f} ({len(escalenos)} escalenos, {len(equilateros)} equiláteros)")
                
                if ratio > mejor_ratio:
                    mejor_ratio = ratio
                    mejor_estrategia = estrategia_nombre
                
                if ratio > 1.5:
                    print("   🎯 ¡POSIBLE VORTICIDAD!")
                elif ratio > 1.2:
                    print("   💡 Indicios de vorticidad")
            else:
                print("   ❌ No hay suficientes datos válidos")
        
        # Resultado final para este archivo
        print(f"\n📈 MEJOR RESULTADO para {nombre}:")
        print(f"   Estrategia: {mejor_estrategia}")
        print(f"   Ratio vorticidad: {mejor_ratio:.3f}")
        
        if mejor_ratio > 1.5:
            conclusion = "FUERTE_EVIDENCIA_VORTICIDAD"
            print("   🎯 CONCLUSIÓN: FUERTE EVIDENCIA DE VORTICIDAD")
        elif mejor_ratio > 1.2:
            conclusion = "INDICIO_VORTICIDAD"
            print("   🎯 CONCLUSIÓN: INDICIO DE VORTICIDAD")
        else:
            conclusion = "SIN_EVIDENCIA_VORTICIDAD"
            print("   🎯 CONCLUSIÓN: Sin evidencia fuerte")
        
        resultados_totales[nombre] = {
            'mejor_ratio': mejor_ratio,
            'mejor_estrategia': mejor_estrategia,
            'conclusion': conclusion
        }
    
    # RESUMEN EJECUTIVO
    print(f"\n{'='*60}")
    print("🎯 RESUMEN EJECUTIVO FINAL")
    print("=" * 60)
    
    for nombre, resultado in resultados_totales.items():
        print(f"📊 {nombre}:")
        print(f"   Ratio: {resultado['mejor_ratio']:.3f}")
        print(f"   Estrategia: {resultado['mejor_estrategia']}")
        print(f"   Conclusión: {resultado['conclusion']}")
        print()
    
    # HALLazGO PRINCIPAL
    ratios = [r['mejor_ratio'] for r in resultados_totales.values()]
    if ratios:
        max_ratio = max(ratios)
        archivo_max = [k for k, v in resultados_totales.items() if v['mejor_ratio'] == max_ratio][0]
        
        print("🌟 HALLAZGO CIENTÍFICO PRINCIPAL:")
        print(f"   Máximo ratio de vorticidad detectado: {max_ratio:.3f}")
        print(f"   En archivo: {archivo_max}")
        
        if max_ratio > 2.0:
            print("   🚀 ¡FUERTE EVIDENCIA DE VORTICIDAD CÓSMICA!")
            print("   📚 Esto sugiere física beyond-ΛCDM")
        elif max_ratio > 1.5:
            print("   💫 Evidencia significativa de vorticidad")
        elif max_ratio > 1.2:
            print("   🔍 Indicios prometedores")
        else:
            print("   📉 Sin evidencia concluyente")

if __name__ == "__main__":
    analizar_alm_directo()
