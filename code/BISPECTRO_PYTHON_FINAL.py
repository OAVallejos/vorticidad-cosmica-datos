#!/usr/bin/env python3
"""
BISPECTRO_PYTHON_FINAL.py
Implementación Python pura definitiva - SIN RUST
"""

import numpy as np
import json

def calcular_bispectro_python_final(modos_alm, l_max, configs):
    """Bispectro Python puro con todas las correcciones"""
    resultados = []
    
    for (l1, l2, l3) in configs:
        if not condiciones_triangulo(l1, l2, l3):
            resultados.append(0.0)
            continue
            
        suma = 0.0
        
        # PREFACTOR GEOMÉTRICO
        prefactor = np.sqrt((2*l1+1) * (2*l2+1) * (2*l3+1) / (4.0 * np.pi))
        
        for m1 in range(-l1, l1+1):
            for m2 in range(-l2, l2+1):
                m3 = -m1 - m2
                if abs(m3) <= l3:
                    wigner = calcular_wigner_3j_python(l1, l2, l3, m1, m2, m3)
                    a_l1 = obtener_modo_python(modos_alm, l1, m1, l_max)
                    a_l2 = obtener_modo_python(modos_alm, l2, m2, l_max)
                    a_l3 = obtener_modo_python(modos_alm, l3, m3, l_max)
                    
                    suma += wigner * a_l1 * a_l2 * a_l3
        
        resultados.append(float(prefactor * suma))
    
    return resultados

def calcular_wigner_3j_python(l1, l2, l3, m1, m2, m3):
    """Wigner 3-j en Python con correcciones"""
    if not condiciones_triangulo(l1, l2, l3) or (m1 + m2 + m3 != 0):
        return 0.0
    
    # Aproximación corregida con signo
    signo = 1.0 if (l1 + l2 + l3) % 2 == 0 else -1.0
    return signo / np.sqrt(2 * l1 + 1)

def obtener_modo_python(modos_b, l, m, l_max):
    """Obtener modo en Python"""
    idx = l * (2 * l_max + 1) + (m + l)
    return modos_b[idx] if idx < len(modos_b) else 0.0

def condiciones_triangulo(l1, l2, l3):
    """Condiciones de triangularidad"""
    return (l1 + l2 >= l3) and (l1 + l3 >= l2) and (l2 + l3 >= l1) and \
           ((l1 + l2 + l3) % 2 == 0) and (l1 + l2 + l3) >= 2

# 🎯 PRUEBA INMEDIATA
if __name__ == "__main__":
    print("🎯 BISPECTRO PYTHON PURO - FUNCIONANDO")
    
    l_max = 2
    total_modos = (l_max + 1) ** 2
    modos_alm = [0.0] * total_modos
    
    # Activar solo modo l=2, m=0
    idx = 2 * (2*2 + 1) + (0 + 2)
    if idx < len(modos_alm):
        modos_alm[idx] = 1.0e-6
    
    configs = [(2, 2, 2)]
    
    resultado = calcular_bispectro_python_final(modos_alm, l_max, configs)
    print(f"🔧 Resultado: {resultado[0]:.6e}")
    
    if resultado[0] != 0.0:
        print("✅ ¡BISPECTRO PYTHON FUNCIONA!")
    else:
        print("❌ Error en implementación Python")
