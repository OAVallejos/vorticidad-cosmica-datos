#!/usr/bin/env python3      

""" 
REAL_RUST_DIAGNOSIS.py                  
Complete diagnosis of Rust module
"""                                                 import numpy as np
import inspect

print("🔍 COMPLETE DIAGNOSIS OF RUST MODULE")
print("=" * 60)

try:
    import cosmic_vorticity
    print("✅ Module 'cosmic_vorticity' imported")

    # Verify what is actually in the module
    print("\n📋 MODULE CONTENT:")
    for name in dir(cosmic_vorticity):
        if not name.startswith('_'):  # Only public elements
            obj = getattr(cosmic_vorticity, name)
            print(f"  - {name}: {type(obj)}")

    # Verify specific functions
    print("\n🔧 VERIFYING SPECIFIC FUNCTIONS:")

    if hasattr(cosmic_vorticity, 'calcular_bispectro_triangular'):
        print("✅ calcular_bispectro_triangular - EXISTS")
        # Test the function
        try:
            test_data = [100.0, 200.0, 150.0]
            result = cosmic_vorticity.calcular_bispectro_triangular(test_data, 4, [(2,2,2)])
            print(f"  Test result: {result}")
        except Exception as e:
            print(f"  ❌ Execution error: {e}")
    else:
        print("❌ calcular_bispectro_triangular - DOES NOT EXIST")

    # Verify classes
    print("\n🏗️ VERIFYING CLASSES:")
    classes_to_check = ['CosmologicalParameters', 'VectorFieldParameters', 'CosmicVorticitySystem']

    for class_name in classes_to_check:
        if hasattr(cosmic_vorticity, class_name):
            print(f"✅ {class_name} - EXISTS")
            cls = getattr(cosmic_vorticity, class_name)

            # Attempt to view signature
            try:
                sig = inspect.signature(cls.__init__)
                print(f"  Signature: {sig}")
            except:
                print("  Cannot obtain signature")

            # Attempt to create instance
            try:
                if class_name == 'CosmologicalParameters':
                    instance = cls(h0=67.4, omega_m=0.315, omega_b=0.049,
                                 omega_r=9.2e-5, omega_lambda=0.685,
                                 sigma_8=0.811, n_s=0.965, tau=0.054)
                elif class_name == 'VectorFieldParameters':
                    instance = cls(m_a=1e-28, lambda_a=1e-45, alpha=3e-18,
                                 beta=8e-42, gamma_2=1.4e-3, v=6.3e-3, m_phi=7.2e-33)
                elif class_name == 'CosmicVorticitySystem':
                    # We need instances first
                    cosmo = cosmic_vorticity.CosmologicalParameters(h0=67.4, omega_m=0.315, omega_b=0.049,
                                                                    omega_r=9.2e-5, omega_lambda=0.685,
                                                                    sigma_8=0.811, n_s=0.965, tau=0.054)
                    vector = cosmic_vorticity.VectorFieldParameters(m_a=1e-28, lambda_a=1e-45, alpha=3e-18,
                                                                    beta=8e-42, gamma_2=1.4e-3, v=6.3e-3, m_phi=7.2e-33)
                    instance = cls(cosmo, vector, 1000.0)

                print(f"  ✅ Instance created: {instance}")

                # Verify methods
                if hasattr(instance, 'calculate_log_likelihood'):
                    print("  ✅ calculate_log_likelihood - EXISTS")
                else:
                    print("  ❌ calculate_log_likelihood - DOES NOT EXIST")

            except Exception as e:
                print(f"  ❌ Error creating instance: {e}")
        else:
            print(f"❌ {class_name} - DOES NOT EXIST")

except ImportError as e:
    print(f"❌ Cannot import cosmic_vorticity: {e}")
    print("\n💡 SOLUTION: Verify that:")
    print("  1. Rust is installed: rustc --version")
    print("  2. Maturin is installed: pip install maturin")
    print("  3. The module is compiled: cargo build --release")
    print("  4. Bindings are installed: maturin develop")

print("\n🔎 VERIFYING RUST FILES:")
import os
rust_files = [f for f in os.listdir('.') if f.endswith('.rs') or f == 'Cargo.toml']
for f in rust_files:
    print(f"  📄 {f}")

print("\n🎯 DIAGNOSIS COMPLETED")