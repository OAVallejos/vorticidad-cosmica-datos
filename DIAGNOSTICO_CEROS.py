#!/usr/bin/env python3
"""
DIAGNÓSTICO DE VALORES CERO EN CONFIGURACIONES
Analiza por qué algunas configuraciones dan bispectro cero
"""

import numpy as np

def verificar_condiciones_triangulo(l1, l2, l3):
    """Verifica todas las condiciones de triangularidad"""
    condiciones = {
        'suma_l1_l2 >= l3': l1 + l2 >= l3,
        'suma_l1_l3 >= l2': l1 + l3 >= l2,
        'suma_l2_l3 >= l1': l2 + l3 >= l1,
        'suma_par': (l1 + l2 + l3) % 2 == 0,
        'suma_total >= 2': (l1 + l2 + l3) >= 2,
        'l1_l2_l3 >= 0': l1 >= 0 and l2 >= 0 and l3 >= 0
    }
    return all(condiciones.values()), condiciones

def analizar_configuraciones_cero():
    """Analiza configuraciones que dan cero en los datos"""
    
    print("🔍 DIAGNÓSTICO DE CONFIGURACIONES CON VALOR CERO")
    print("=" * 60)
    
    # Configuraciones problemáticas de tus datos
    configs_problematicas = [
        (3, 5, 7),  # Siempre cero
        (3, 3, 3),  # Siempre cero  
        (5, 5, 5)   # Siempre cero
    ]
    
    configs_normales = [
        (1, 2, 3), (2, 2, 2), (4, 4, 4)  # Estas sí funcionan
    ]
    
    print("\n📋 ANÁLISIS DE CONDICIONES DE TRIÁNGULO:")
    print("-" * 50)
    
    for config in configs_problematicas + configs_normales:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)
        
        print(f"\nConfiguración {config}:")
        print(f"  Válida: {valido}")
        for cond, resultado in condiciones.items():
            print(f"  {cond}: {resultado}")
        
        # Verificar suma de momentos magnéticos posibles
        print(f"  Suma l1+l2+l3: {l1 + l2 + l3} (par: {(l1+l2+l3) % 2 == 0})")
        
        # Mostrar algunos momentos magnéticos posibles
        print(f"  Ejemplo m1,m2,m3: m1=0, m2=0, m3=0 → m1+m2+m3={0+0+0}")

def diagnosticar_implementacion():
    """Diagnostica la implementación del bispectro"""
    
    print("\n🔧 DIAGNÓSTICO DE IMPLEMENTACIÓN:")
    print("-" * 50)
    
    # Test con datos simples
    l_max = 7
    total_modos = (l_max + 1) ** 2
    
    # Crear modos alm con estructura simple
    modos_alm = [0.0] * total_modos
    
    # Activar solo algunos modos
    for l in range(l_max + 1):
        idx = l * (2 * l_max + 1) + (0 + l)  # m=0
        if idx < len(modos_alm):
            modos_alm[idx] = 1.0e-6
    
    print("Modos alm activados (m=0):")
    for l in range(l_max + 1):
        idx = l * (2 * l_max + 1) + (0 + l)
        if idx < len(modos_alm):
            print(f"  l={l}, m=0: idx={idx}, valor={modos_alm[idx]:.2e}")

def sugerir_configuraciones_alternativas():
    """Sugiere configuraciones que deberían funcionar mejor"""
    
    print("\n💡 CONFIGURACIONES ALTERNATIVAS RECOMENDADAS:")
    print("-" * 50)
    
    # Configuraciones que siempre cumplen condiciones
    configs_robustas = [
        # Triángulos escalenos robustos
        (1, 2, 3), (1, 3, 4), (2, 3, 5), 
        (1, 4, 5), (2, 4, 6), (3, 4, 7),
        (1, 5, 6), (2, 5, 7), (3, 6, 7),
        
        # Equiláteros robustos
        (2, 2, 2), (4, 4, 4), (6, 6, 6),
        (3, 3, 3), (5, 5, 5), (7, 7, 7)  # Estos deberían funcionar
    ]
    
    print("Configuraciones que deberían evitar ceros:")
    for config in configs_robustas:
        l1, l2, l3 = config
        valido, _ = verificar_condiciones_triangulo(l1, l2, l3)
        if valido:
            print(f"  ✅ {config}")

def analizar_patron_ceros():
    """Analiza el patrón de ceros en los datos existentes"""
    
    print("\n📊 ANÁLISIS DE PATRÓN DE CEROS EN DATOS:")
    print("-" * 50)
    
    # Datos de tus resultados
    configs_con_cero = [
        (3, 5, 7), (3, 3, 3), (5, 5, 5)
    ]
    
    configs_sin_cero = [
        (1, 2, 3), (1, 3, 4), (2, 3, 5),
        (1, 4, 5), (2, 4, 6), (2, 2, 2),
        (4, 4, 4)
    ]
    
    print("Configuraciones que DAN CERO:")
    for config in configs_con_cero:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)
        print(f"  {config}: válido={valido}, suma={l1+l2+l3}, par={((l1+l2+l3) % 2 == 0)}")
    
    print("\nConfiguraciones que FUNCIONAN:")
    for config in configs_sin_cero:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)
        print(f"  {config}: válido={valido}, suma={l1+l2+l3}, par={((l1+l2+l3) % 2 == 0)}")

if __name__ == "__main__":
    analizar_configuraciones_cero()
    diagnosticar_implementacion()
    sugerir_configuraciones_alternativas()
    analizar_patron_ceros()
    
    print("\n🎯 RECOMENDACIONES INMEDIATAS:")
    print("=" * 50)
    print("1. EVITAR estas configuraciones problemáticas:")
    print("   - (3, 5, 7) → Suma impar (15)")
    print("   - (3, 3, 3) → Suma impar (9)") 
    print("   - (5, 5, 5) → Suma impar (15)")
    print("\n2. USAR estas configuraciones alternativas:")
    print("   - (3, 4, 7) → Suma par (14)")
    print("   - (3, 3, 4) → Suma par (10)")
    print("   - (5, 5, 6) → Suma par (16)")
    print("\n3. La condición clave: l1 + l2 + l3 debe ser PAR")
