#!/usr/bin/env python3
"""
TEST_ESTABILIDAD_NUMERICA.py
Verifica estabilidad con diferentes precisiones numéricas
"""

import numpy as np
import sys

def test_estabilidad_numerica():
    """Test con diferentes precisiones numéricas"""
    
    print("🧪 TEST DE ESTABILIDAD NUMÉRICA")
    print("=" * 60)
    
    # Configuración de test
    config_test = (2, 2, 2)
    
    # Diferentes precisiones a probar
    precisiones = [
        ("float32", np.float32),
        ("float64", np.float64), 
    ]
    
    print("\n📊 COMPARACIÓN DE PRECISIONES:")
    print("-" * 50)
    
    resultados = {}
    
    for nombre, dtype in precisiones:
        # Generar datos con diferente precisión
        np.random.seed(42)  # Misma semilla para comparación justa
        
        if dtype == np.float32:
            datos_real = np.random.normal(0, 1e-6, 100).astype(np.float32)
            datos_imag = np.random.normal(0, 1e-6, 100).astype(np.float32)
        else:
            datos_real = np.random.normal(0, 1e-6, 100).astype(np.float64)
            datos_imag = np.random.normal(0, 1e-6, 100).astype(np.float64)
            
        datos_alm = datos_real + 1j * datos_imag
        
        # Calcular métricas de estabilidad
        bispectro = np.abs(np.mean(datos_alm))**3
        varianza = np.var(datos_alm)
        condicionamiento = np.max(np.abs(datos_alm)) / np.min(np.abs(datos_alm[np.abs(datos_alm) > 0]))
        
        resultados[nombre] = {
            'bispectro': bispectro,
            'varianza': varianza, 
            'condicionamiento': condicionamiento,
            'dtype': dtype
        }
        
        print(f"📐 {nombre:8} | Bispectro = {bispectro:.2e}")
        print(f"   Varianza: {varianza:.2e} | Condicionamiento: {condicionamiento:.2e}")
    
    # Comparar resultados entre precisiones
    print(f"\n🔍 COMPARACIÓN ENTRE PRECISIONES:")
    print("-" * 50)
    
    bs_32 = resultados['float32']['bispectro']
    bs_64 = resultados['float64']['bispectro']
    
    diferencia_relativa = np.abs(bs_64 - bs_32) / np.abs(bs_64)
    
    print(f"Bispectro float32: {bs_32:.2e}")
    print(f"Bispectro float64: {bs_64:.2e}")
    print(f"Diferencia relativa: {diferencia_relativa:.2e}")
    
    # Test de underflow/overflow
    print(f"\n⚠️  TEST DE UNDERFLOW/OVERFLOW:")
    print("-" * 50)
    
    # Probar con valores extremos
    valores_extremos = [1e-20, 1e-10, 1e0, 1e10, 1e20]
    
    for valor in valores_extremos:
        try:
            test_data = np.array([valor], dtype=np.float64)
            bispectro_test = np.abs(test_data[0])**3
            print(f"✅ Valor {valor:.0e} -> Bispectro {bispectro_test:.0e}")
        except Exception as e:
            print(f"❌ Valor {valor:.0e} -> Error: {e}")
    
    # Criterio de aceptación
    umbral_diferencia = 1e-4  # 0.01% de diferencia
    
    if diferencia_relativa < umbral_diferencia:
        print(f"\n🎯 RESULTADO: ESTABILIDAD NUMÉRICA ✅")
        print(f"Las precisiones dan resultados consistentes (diferencia: {diferencia_relativa:.2e})")
        return True
    else:
        print(f"\n🎯 RESULTADO: INESTABILIDAD NUMÉRICA ❌")
        print(f"Grandes diferencias entre precisiones (diferencia: {diferencia_relativa:.2e})")
        return False

def test_sensibilidad_ruido():
    """Test de sensibilidad al nivel de ruido"""
    
    print(f"\n📈 TEST DE SENSIBILIDAD AL RUIDO:")
    print("-" * 50)
    
    niveles_ruido = [1e-10, 1e-8, 1e-6, 1e-4, 1e-2]
    
    for ruido in niveles_ruido:
        datos = np.random.normal(0, ruido, 100) + 1j * np.random.normal(0, ruido, 100)
        bispectro = np.abs(np.mean(datos))**3
        
        print(f"Ruido {ruido:.0e} -> Bispectro {bispectro:.2e}")
        
        # Verificar que no hay NaN o infinitos
        if np.isnan(bispectro) or np.isinf(bispectro):
            print(f"❌ PROBLEMA: Valor numérico inválido con ruido {ruido:.0e}")
            return False
    
    print("✅ Todos los niveles de ruido producen valores válidos")
    return True

if __name__ == "__main__":
    success1 = test_estabilidad_numerica()
    success2 = test_sensibilidad_ruido()
    
    sys.exit(0 if (success1 and success2) else 1)
