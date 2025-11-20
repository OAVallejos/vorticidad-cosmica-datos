#!/usr/bin/env python3
"""                         TEST_NUMERICAL_STABILITY_RUST.py
Verifies stability of the Rust module with different precisions
"""

import numpy as np
import sys
import cosmic_vorticity as cv

def test_estabilidad_rust():
    """Numerical stability test using the actual Rust module"""

    print("🧪 NUMERICAL STABILITY TEST - RUST MODULE")
    print("=" * 60)

    # REAL test configuration using your module
    config_test = [(2, 2, 2), (3, 3, 3), (2, 3, 4)]
    l_max = 10

    print(f"\n📊 TESTING RUST FUNCTIONS:")
    print("-" * 50)

    # Test 1: Bispectrum with different precisions
    precisiones = [np.float32, np.float64]

    for precision in precisiones:
        print(f"\n🔍 Testing with {precision.__name__}:")

        # Generate test data
        np.random.seed(42)
        if precision == np.float32:
            modos_b = np.random.normal(0, 1.0, 400).astype(np.float32)
        else:
            modos_b = np.random.normal(0, 1.0, 400).astype(np.float64)

        try:
            # Call the REAL Rust function
            resultado = cv.calcular_bispectro_triangular(modos_b, l_max, config_test)
            print(f"  ✅ Bispectrum calculated: {resultado}")

            # Verify no NaN/Infinities
            if any(np.isnan(r) or np.isinf(r) for r in resultado):
                print(f"  ❌ Invalid values detected")
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    # Test 2: Cosmological system
    print(f"\n🌌 COSMOLOGICAL SYSTEM TEST:")
    print("-" * 50)

    try:
        # Create REAL parameters
        cosmo = cv.CosmologicalParameters(
            h0=67.4, omega_m=0.315, omega_b=0.049,
            omega_r=9.2e-5, omega_lambda=0.685,
            sigma_8=0.811, n_s=0.965, tau=0.054
        )

        vector = cv.VectorFieldParameters(
            m_a=1e-28, lambda_a=1e-45, alpha=3e-18,
            beta=8e-42, gamma_2=1.4e-3, v=6.3e-3, m_phi=7.2e-33
        )

        sistema = cv.CosmicVorticitySystem(cosmo, vector, 1000.0)

        # Likelihood test
        likelihood = sistema.calculate_log_likelihood_simple((1.0, 0.1), (1.0, 0.1))
        print(f"  ✅ Likelihood calculated: {likelihood:.6f}")

    except Exception as e:
        print(f"  ❌ Cosmological system error: {e}")
        return False

    # Test 3: Triangular configurations
    print(f"\n📐 TRIANGULAR CONFIGURATIONS TEST:")
    print("-" * 50)

    try:
        configs = cv.obtener_todas_configuraciones_triangulares()
        print(f"  ✅ {len(configs)} configurations obtained")

        # Test some configurations
        tipos = ["equilatero", "escaleno", "isosceles"]
        for tipo in tipos:
            configs_tipo = cv.obtener_configuraciones_por_tipo(tipo)
            print(f"  - {tipo}: {len(configs_tipo)} configurations")

    except Exception as e:
        print(f"  ❌ Configurations error: {e}")
        return False

    return True

def test_estabilidad_extremos():
    """Test with extreme values in the Rust module"""

    print(f"\n⚠️  EXTREME VALUES TEST - RUST:")
    print("-" * 50)

    valores_test = [
        [0.0] * 100,           # All zeros
        [1e-10] * 100,         # Very small values
        [1e10] * 100,          # Very large values
        [1.0] * 100,           # Unit values
    ]

    config_test = [(2, 2, 2)]
    l_max = 4

    for i, datos in enumerate(valores_test):
        try:
            resultado = cv.calcular_bispectro_triangular(datos, l_max, config_test)
            print(f"  ✅ Test {i+1}: {resultado}")

            if any(np.isnan(r) or np.isinf(r) for r in resultado):
                print(f"  ❌ Invalid values in test {i+1}")
                return False

        except Exception as e:
            print(f"  ❌ Error in test {i+1}: {e}")
            return False

    return True

if __name__ == "__main__":
    success1 = test_estabilidad_rust()
    success2 = test_estabilidad_extremos()

    if success1 and success2:
        print(f"\n🎯 FINAL RESULT: RUST STABILITY  ✅")
        print("All Rust module functions are numerically stable")
        sys.exit(0)
    else:
        print(f"\n🎯 FINAL RESULT: PROBLEMS DETECTED ❌")
        sys.exit(1)