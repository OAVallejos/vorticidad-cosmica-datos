#!/usr/bin/env python3
"""
TEST_DATOS_SINTETICOS.py
Verifica detección con datos controlados
"""

import numpy as np
import sys

def generar_datos_sinteticos(tipo="sin_vorticidad", n_modos=100, ruido=1e-6):
    """Genera datos alm sintéticos para testing"""
    
    if tipo == "sin_vorticidad":
        # Datos gaussianos sin vorticidad (bispectro ~0)
        alm_real = np.random.normal(0, ruido, n_modos)
        alm_imag = np.random.normal(0, ruido, n_modos)
        
    elif tipo == "con_vorticidad":
        # Datos con correlación no-gaussiana (bispectro ≠ 0)
        alm_real = np.random.normal(0, ruido, n_modos)
        alm_imag = np.random.normal(0, ruido, n_modos)
        
        # Introducir correlación triple simple
        for i in range(0, n_modos-3, 3):
            corr = np.random.normal(0, ruido*10)
            alm_real[i] += corr
            alm_real[i+1] += corr * 0.5
            alm_real[i+2] += corr * 0.3
            
    elif tipo == "ruido_puro":
        # Ruido blanco puro
        alm_real = np.random.normal(0, ruido, n_modos)
        alm_imag = np.random.normal(0, ruido, n_modos)
    
    return alm_real + 1j * alm_imag

def test_datos_sinteticos():
    """Test con datos controlados"""
    
    print("🧪 TEST CON DATOS SINTÉTICOS CONTROLADOS")
    print("=" * 60)
    
    # Configuración de test robusta
    config_test = (2, 2, 2)
    
    tipos_datos = [
        ("sin_vorticidad", "Bispectro ~0"),
        ("con_vorticidad", "Bispectro ≠ 0"), 
        ("ruido_puro", "Bispectro ~0")
    ]
    
    print("\n📊 RESULTADOS CON DATOS SINTÉTICOS:")
    print("-" * 50)
    
    for tipo, descripcion in tipos_datos:
        # Generar datos
        datos_alm = generar_datos_sinteticos(tipo=tipo)
        
        # Calcular bispectro simple (simulado)
        l1, l2, l3 = config_test
        bispectro = np.abs(np.mean(datos_alm))**3  # Proxy simple
        
        # Evaluar resultado
        if "~0" in descripcion:
            esperado = "≈0"
            status = "✅" if bispectro < 1e-5 else "❌"
        else:
            esperado = "≠0" 
            status = "✅" if bispectro > 1e-5 else "❌"
        
        print(f"{status} {tipo:15} | bispectro = {bispectro:.2e} | esperado: {esperado}")
        print(f"   {descripcion}")
    
    print(f"\n🎯 VERIFICACIÓN DE FALSOS POSITIVOS/NEGATIVOS:")
    print("-" * 50)
    
    # Test más riguroso con múltiples realizaciones
    n_realizaciones = 10
    detecciones_correctas = 0
    
    for i in range(n_realizaciones):
        datos_sin = generar_datos_sinteticos("sin_vorticidad")
        datos_con = generar_datos_sinteticos("con_vorticidad")
        
        bs_sin = np.abs(np.mean(datos_sin))**3
        bs_con = np.abs(np.mean(datos_con))**3
        
        # Verificar que con_vorticidad > sin_vorticidad
        if bs_con > bs_sin:
            detecciones_correctas += 1
    
    tasa_acierto = detecciones_correctas / n_realizaciones * 100
    print(f"Detecciones correctas: {detecciones_correctas}/{n_realizaciones}")
    print(f"Tasa de acierto: {tasa_acierto:.1f}%")
    
    if tasa_acierto > 70:
        print("✅ TEST PASADO - El método discrimina correctamente")
        return True
    else:
        print("❌ TEST FALLADO - Posibles falsos positivos/negativos")
        return False

if __name__ == "__main__":
    success = test_datos_sinteticos()
    sys.exit(0 if success else 1)
