#!/usr/bin/env python3      

"""                             

DIAGNOSIS OF ZERO VALUES IN CONFIGURATIONS        
Analyzes why some configurations yield zero bispectrum              

"""

import numpy as np

def verificar_condiciones_triangulo(l1, l2, l3):
    """Verifies all triangle conditions"""
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
    """Analyzes configurations that yield zero in the data"""

    print("🔍 DIAGNOSIS OF ZERO-VALUE CONFIGURATIONS")
    print("=" * 60)

    # Problematic configurations from your data
    configs_problematicas = [
        (3, 5, 7),  # Always zero
        (3, 3, 3),  # Always zero
        (5, 5, 5)   # Always zero
    ]

    configs_normales = [
        (1, 2, 3), (2, 2, 2), (4, 4, 4)  # These do work
    ]

    print("\n📋 ANALYSIS OF TRIANGLE CONDITIONS:")
    print("-" * 50)

    for config in configs_problematicas + configs_normales:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)

        print(f"\nConfiguration {config}:")
        print(f"  Valid: {valido}")
        for cond, resultado in condiciones.items():
            print(f"  {cond}: {resultado}")

        # Verify sum of possible magnetic moments
        print(f"  Sum l1+l2+l3: {l1 + l2 + l3} (even: {(l1+l2+l3) % 2 == 0})")

        # Show some possible magnetic moments
        print(f"  Example m1,m2,m3: m1=0, m2=0, m3=0 → m1+m2+m3={0+0+0}")

def diagnosticar_implementacion():
    """Diagnoses the bispectrum implementation"""

    print("\n🔧 IMPLEMENTATION DIAGNOSIS:")
    print("-" * 50)

    # Test with simple data
    l_max = 7
    total_modos = (l_max + 1) ** 2

    # Create alm modes with simple structure
    modos_alm = [0.0] * total_modos

    # Activate only some modes
    for l in range(l_max + 1):
        idx = l * (2 * l_max + 1) + (0 + l)  # m=0
        if idx < len(modos_alm):
            modos_alm[idx] = 1.0e-6

    print("Activated alm modes (m=0):")
    for l in range(l_max + 1):
        idx = l * (2 * l_max + 1) + (0 + l)
        if idx < len(modos_alm):
            print(f"  l={l}, m=0: idx={idx}, value={modos_alm[idx]:.2e}")

def sugerir_configuraciones_alternativas():
    """Suggests configurations that should work better"""

    print("\n💡 RECOMMENDED ALTERNATIVE CONFIGURATIONS:")
    print("-" * 50)

    # Configurations that always meet conditions
    configs_robustas = [
        # Robust scalene triangles
        (1, 2, 3), (1, 3, 4), (2, 3, 5),
        (1, 4, 5), (2, 4, 6), (3, 4, 7),
        (1, 5, 6), (2, 5, 7), (3, 6, 7),

        # Robust equilateral triangles
        (2, 2, 2), (4, 4, 4), (6, 6, 6),
        (3, 3, 3), (5, 5, 5), (7, 7, 7)  # These should work
    ]

    print("Configurations that should avoid zeros:")
    for config in configs_robustas:
        l1, l2, l3 = config
        valido, _ = verificar_condiciones_triangulo(l1, l2, l3)
        if valido:
            print(f"  ✅ {config}")

def analizar_patron_ceros():
    """Analyzes the zero pattern in existing data"""

    print("\n📊 ANALYSIS OF ZERO PATTERN IN DATA:")
    print("-" * 50)

    # Data from your results
    configs_con_cero = [
        (3, 5, 7), (3, 3, 3), (5, 5, 5)
    ]

    configs_sin_cero = [
        (1, 2, 3), (1, 3, 4), (2, 3, 5),
        (1, 4, 5), (2, 4, 6), (2, 2, 2),
        (4, 4, 4)
    ]

    print("Configurations that YIELD ZERO:")
    for config in configs_con_cero:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)
        print(f"  {config}: valid={valido}, sum={l1+l2+l3}, even={((l1+l2+l3) % 2 == 0)}")

    print("\nConfigurations that WORK:")
    for config in configs_sin_cero:
        l1, l2, l3 = config
        valido, condiciones = verificar_condiciones_triangulo(l1, l2, l3)
        print(f"  {config}: valid={valido}, sum={l1+l2+l3}, even={((l1+l2+l3) % 2 == 0)}")

if __name__ == "__main__":
    analizar_configuraciones_cero()
    diagnosticar_implementacion()
    sugerir_configuraciones_alternativas()
    analizar_patron_ceros()

    print("\n🎯 IMMEDIATE RECOMMENDATIONS:")
    print("=" * 50)
    print("1. AVOID these problematic configurations:")
    print("    - (3, 5, 7) → Odd sum (15)")
    print("    - (3, 3, 3) → Odd sum (9)")
    print("    - (5, 5, 5) → Odd sum (15)")
    print("\n2. USE these alternative configurations:")
    print("    - (3, 4, 7) → Even sum (14)")
    print("    - (3, 3, 4) → Even sum (10)")
    print("    - (5, 5, 6) → Even sum (16)")
    print("\n3. The key condition: l1 + l2 + l3 must be EVEN")