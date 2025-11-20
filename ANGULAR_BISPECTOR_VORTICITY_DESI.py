#!/usr/bin/env python3
"""

RIGOROUS calculation of the angular bispectrum using a scientific Rust library

SCIENTIFIC SOURCES:
- Angular bispectrum definition: Komatsu et al. (2005), Spergel & Goldberg (1999)
- Wigner-3j implementation: Bucher et al. (2010), Planck Collaboration (2020)
- Gaussianity tests: D'Agostino (1971), Anderson & Darling (1954)
- Multipole configurations: Fergusson & Shellard (2009)
"""

import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
import json
from scipy import stats

# PRINCIPAL DATASET
N_GALAXIAS_DESI = 1470000  # DESI Collaboration (2021)

def justificar_metodologia_bispectro_riguroso():
    """Documents the scientific justification of the methodology"""

    print("\n📚 RIGOROUS METHODOLOGICAL JUSTIFICATION:")
    print("=" * 50)
    print("🔬 ANGULAR BISPECTRUM - DEFINITION:")
    print("   • B(ℓ₁,ℓ₂,ℓ₃) = ∑ₘ₁ₘ₂ₘ₃ 𝒢ˡ¹ˡ²ˡ³ₘ₁ₘ₂ₘ₃ aₗ₁ₘ₁ aₗ₂ₘ₂ aₗ₃ₘ₃")
    print("   • Gaunt symbol 𝒢 includes Wigner-3j - Komatsu et al. (2005)")
    print("   • Rust implementation using wigners::wigner_3j")
    print("🔬 MULTIPOLE CONFIGURATIONS:")
    print("   • Equilateral: tests isotropy - Fergusson & Shellard (2009)")
    print("   • Scalene: tests rotational anisotropies")
    print("🔬 GAUSSIANITY TESTS:")
    print("   • D'Agostino (1971): Skewness and kurtosis")
    print("   • Anderson-Darling (1954): Normality test")

def convertir_mapa_a_modos_rust(mapa_delta, lmax):
    """
    Converts HEALPix map to a format compatible with the Rust library
    Based on: HEALPix standard for alm coefficients
    """
    # Calculate alm coefficients
    alm = hp.map2alm(mapa_delta, lmax=lmax)

    # Convert to flat format for Rust
    modos_b = []
    for l in range(lmax + 1):
        for m in range(-l, l + 1):
            idx = hp.Alm.getidx(lmax, l, abs(m))
            if m < 0:
                # Imaginary part for m < 0
                valor = -np.imag(alm[idx])
            elif m > 0:
                # Real part for m > 0
                valor = np.real(alm[idx])
            else:
                # m = 0 is purely real
                valor = np.real(alm[idx])
            modos_b.append(valor)

    return np.array(modos_b, dtype=np.float32)

def definir_umbrales_significancia_rigurosos():
    """Defines significance thresholds based on literature"""

    print("\n🔬 RIGOROUS SIGNIFICANCE THRESHOLDS:")
    print("=" * 50)

    # Based on ΛCDM simulations (Planck Collaboration 2020)
    UMBRAL_BISPECTRO = 1e-10  # Expected noise level in ΛCDM
    UMBRAL_SKEWNESS = 0.3     # D'Agostino (1971)
    UMBRAL_KURTOSIS = 0.5     # D'Agostino (1971)
    UMBRAL_ANDERSON = 0.75    # Anderson-Darling (1954) - 1% level

    print("🔬 BASED ON ΛCDM SIMULATIONS:")
    print(f"   • |Bispectrum| > {UMBRAL_BISPECTRO:.1e}: Significant")
    print(f"   • Skewness > {UMBRAL_SKEWNESS}: Detectable non-Gaussianity")
    print(f"   • Kurtosis > {UMBRAL_KURTOSIS}: Significant heavy tails")
    print(f"   • Anderson-Darling > {UMBRAL_ANDERSON}: Rejection of Gaussianity (1%)")

    return {
        'umbral_bispectro': UMBRAL_BISPECTRO,
        'umbral_skewness': UMBRAL_SKEWNESS,
        'umbral_kurtosis': UMBRAL_KURTOSIS,
        'umbral_anderson': UMBRAL_ANDERSON
    }

def calcular_bispectro_angular_riguroso():
    print("🔺 RIGOROUS ANGULAR BISPECTRUM CALCULATION - DESI")
    print("=" * 60)
    print(f"📊 DATASET: DESI LRG - {N_GALAXIAS_DESI:,} galaxies")

    # Justify methodology
    justificar_metodologia_bispectro_riguroso()
    umbrales = definir_umbrales_significancia_rigurosos()

    # Load δ map
    try:
        mapa_delta = hp.read_map('mapas_healpix/mapa_delta_densidad.fits')
        nside = hp.get_nside(mapa_delta)
        npix = hp.nside2npix(nside)
        print(f"✅ δ map loaded: Nside={nside}, {npix:,} pixels")
    except:
        print("❌ Could not load δ map")
        return

    # RIGOROUS bispectrum configuration
    lmax = 100  # Maximum multipole
    print(f"🔧 Configuring bispectrum up to ℓ={lmax}")

    # SPECIFIC configurations for vorticity detection
    configuraciones = [
        (10, 10, 10, 'equilateral_pequeno'),
        (20, 20, 20, 'equilateral_medio'),
        (30, 30, 30, 'equilateral_grande'),
        (10, 20, 30, 'escaleno_1'),
        (15, 25, 35, 'escaleno_2'),
        (12, 24, 36, 'escaleno_3'),
        (8, 16, 24, 'escaleno_4'),
        (25, 30, 35, 'escaleno_5')
    ]

    resultados_bispectro = {}

    # ✅ CORRECTION: Flag to track method used
    rust_available = False

    # ✅ USE RUST LIBRARY FOR RIGOROUS CALCULATION
    try:
        from cosmic_vorticity import calcular_bispectro_angular_galaxias
        rust_available = True  # ✅ CORRECTION: Flag updated

        print(f"\n📊 CALCULATING RIGOROUS BISPECTRUM...")
        print("   • Method: Rust library with Wigner-3j")
        print("   • Reference: Komatsu et al. (2005), Bucher et al. (2010)")

        # Convert map to Rust format
        modos_b = convertir_mapa_a_modos_rust(mapa_delta, lmax)
        configuraciones_rust = [(l1, l2, l3) for l1, l2, l3, _ in configuraciones]

        # ✅ RIGOROUS CALCULATION WITH RUST
        # NOTE: This line requires a non-existent external Rust library 'cosmic_vorticity'
        # The translation assumes the Python side of the interaction is correct.
        resultados_rust = calcular_bispectro_angular_galaxias(
            modos_b.tolist(), lmax, configuraciones_rust
        )

        # Process results
        for i, ((l1, l2, l3, tipo), bispectrum_val) in enumerate(zip(configuraciones, resultados_rust)):
            magnitud = abs(bispectrum_val)
            significativo = magnitud > umbrales['umbral_bispectro']

            resultados_bispectro[f"{tipo}_l{l1}_{l2}_{l3}"] = {
                'multipolos': (int(l1), int(l2), int(l3)),
                'bispectrum': float(bispectrum_val),
                'magnitud_absoluta': float(magnitud),
                'tipo': tipo,
                'significativo': bool(significativo),
                'referencia_calculo': 'Komatsu et al. (2005) - Rust implementation with Wigner-3j'
            }

            status = "🎯 SIGNIFICANT" if significativo else "⚪ NON-SIGNIFICANT"
            print(f"   • {tipo:>20} ℓ=({l1:2d},{l2:2d},{l3:2d}): {magnitud:.2e} - {status}")

    except ImportError:
        rust_available = False  # ✅ CORRECTION: Flag updated
        print("❌ Rust library not available - using simplified Python estimator")
        print("   ⚠️  WARNING: Python method is an approximation, not rigorous calculation")

        # Calculate alm for fallback Python method
        alm = hp.map2alm(mapa_delta, lmax=lmax)

        for l1, l2, l3, tipo in configuraciones:
            try:
                # Simplified estimation (NON-RIGOROUS - for reference only)
                # This simplistic estimation using direct summation of alm is incorrect for the bispectrum,
                # which requires the Wigner 3j symbol (Gaunt coefficient).
                # It is included here only to mirror the original Python's fallback logic.
                cg_factor = 1.0 / np.sqrt((2*l1 + 1) * (2*l2 + 1) * (2*l3 + 1))
                # Note: This is NOT the correct way to compute the bispectrum B_{l1 l2 l3}
                # It is only a placeholder for the missing Rust function.
                bispectrum_val = np.real(
                    np.sum(alm[l1] * alm[l2] * alm[l3]) * cg_factor
                )
                magnitud = abs(bispectrum_val)
                significativo = magnitud > umbrales['umbral_bispectro']

                resultados_bispectro[f"{tipo}_l{l1}_{l2}_{l3}"] = {
                    'multipolos': (int(l1), int(l2), int(l3)),
                    'bispectrum': float(bispectrum_val),
                    'magnitud_absoluta': float(magnitud),
                    'tipo': tipo,
                    'significativo': bool(significativo),
                    'referencia_calculo': 'Python APPROXIMATION - NON-RIGOROUS'
                }

                status = "🎯 SIGNIFICANT" if significativo else "⚪ NON-SIGNIFICANT"
                print(f"   • {tipo:>20} ℓ=({l1:2d},{l2:2d},{l3:2d}): {magnitud:.2e} - {status}")

            except Exception as e:
                print(f"   ⚠️  Config ({l1},{l2},{l3}): Error - {e}")

    # RIGOROUS non-Gaussianity analysis
    print(f"\n🔍 RIGOROUS NON-GAUSSIANITY ANALYSIS...")
    print("   • Tests: D'Agostino (1971), Anderson-Darling (1954)")

    # Filter pixels with valid data
    delta_valores = mapa_delta[mapa_delta != 0]
    n_pixeles_validos = len(delta_valores)

    print(f"   • Valid pixels: {n_pixeles_validos:,}")

    if n_pixeles_validos > 0:
        # RIGOROUS statistical moments
        skewness = stats.skew(delta_valores)
        kurtosis = stats.kurtosis(delta_valores)

        # Rigorous Gaussianity tests
        normal_test = stats.normaltest(delta_valores)  # D'Agostino
        anderson_test = stats.anderson(delta_valores, dist='norm')

        # Evaluate significance
        skew_significativo = abs(skewness) > umbrales['umbral_skewness']
        kurt_significativo = abs(kurtosis) > umbrales['umbral_kurtosis']
        # The 1% critical value for the Anderson-Darling test is often around 1.035,
        # but the prompt specifies 0.75, which corresponds to a much higher p-value.
        # We use the prompt's specified value for consistency.
        anderson_significativo = anderson_test.statistic > umbrales['umbral_anderson']

        print(f"   • Skewness (γ₁): {skewness:.3f} (threshold: {umbrales['umbral_skewness']}) - {'🎯' if skew_significativo else '⚪'}")
        print(f"   • Kurtosis (γ₂): {kurtosis:.3f} (threshold: {umbrales['umbral_kurtosis']}) - {'🎯' if kurt_significativo else '⚪'}")
        print(f"   • D'Agostino Test: p = {normal_test.pvalue:.3e}")
        print(f"   • Anderson-Darling Test: {anderson_test.statistic:.3f} (threshold: {umbrales['umbral_anderson']}) - {'🎯' if anderson_significativo else '⚪'}")

    else:
        skewness = kurtosis = normal_test = anderson_test = None
        skew_significativo = kurt_significativo = anderson_significativo = False

    # Analysis of significant configurations
    configs_significativas = [k for k, v in resultados_bispectro.items() if v['significativo']]
    proporcion_significativas = len(configs_significativas) / len(resultados_bispectro) if len(resultados_bispectro) > 0 else 0

    print(f"\n📈 RIGOROUS BISPECTRUM SUMMARY:")
    print(f"   • Total configurations: {len(resultados_bispectro)}")
    print(f"   • Significant configurations: {len(configs_significativas)}")
    print(f"   • Significant proportion: {proporcion_significativas:.1%}")

    # RIGOROUS Visualization
    visualizar_bispectro_riguroso(mapa_delta, resultados_bispectro, delta_valores, umbrales, rust_available)

    # Prepare RIGOROUS results
    resultados = {
        'metadatos_rigor': {
            'version': 'bispectro_angular_riguroso_v3.1',
            'dataset': 'DESI LRG',
            'n_galaxias': N_GALAXIAS_DESI,
            'lmax_analizado': lmax,
            'nside_mapa': int(nside) if 'nside' in locals() else None,
            'metodologia_rust': rust_available,  # ✅ CORRECTION: Use real flag
            'timestamp': str(np.datetime64('now')),
            'referencias_principales': [
                'Komatsu et al. (2005)',
                'Bucher et al. (2010)',
                'D\'Agostino (1971)',
                'Anderson & Darling (1954)',
                'DESI Collaboration (2021)'
            ]
        },
        'configuraciones_bispectro': resultados_bispectro,
        'estadisticas_orden_superior': {
            'skewness': float(skewness) if skewness is not None else None,
            'kurtosis': float(kurtosis) if kurtosis is not None else None,
            'pvalue_normalidad_dagostino': float(normal_test.pvalue) if normal_test is not None else None,
            'estadistico_anderson': float(anderson_test.statistic) if anderson_test is not None else None,
            'skewness_significativo': bool(skew_significativo),
            'kurtosis_significativo': bool(kurt_significativo),
            'anderson_significativo': bool(anderson_significativo),
            'referencia_tests': 'D\'Agostino (1971), Anderson-Darling (1954)'
        },
        'analisis_significancia': {
            'total_configuraciones': len(resultados_bispectro),
            'configuraciones_significativas': len(configs_significativas),
            'proporcion_significativas': float(proporcion_significativas),
            'evidencia_no_gaussiana_bispectro': bool(len(configs_significativas) > len(resultados_bispectro) * 0.5),
            'umbral_bispectro_usado': float(umbrales['umbral_bispectro'])
        }
    }

    # Rigorous Interpretation
    gaussianidad_rechazada = bool(
        (normal_test and normal_test.pvalue < 0.01) or
        (anderson_test and anderson_test.statistic > umbrales['umbral_anderson'])
    )

    bispectro_no_nulo = len(configs_significativas) > 0

    compatible_vorticidad = bool(
        skew_significativo and
        len(configs_significativas) > 2 and
        proporcion_significativas > 0.3
    )

    if len(configs_significativas) > 4 and gaussianidad_rechazada:
        nivel_confianza = 'ALTO'
    elif len(configs_significativas) > 2:
        nivel_confianza = 'MODERADO'
    else:
        nivel_confianza = 'BAJO'

    # ✅ CORRECTION: Use real flag to determine method
    metodo_calculo = 'Rust with Wigner-3j' if rust_available else 'Python approximate'

    resultados['interpretacion_rigurosa'] = {
        'gaussianidad_rechazada': gaussianidad_rechazada,
        'bispectro_no_nulo': bispectro_no_nulo,
        'compatible_vorticidad': compatible_vorticidad,
        'nivel_confianza': nivel_confianza,
        'configuraciones_escaleno_significativas': len([k for k in configs_significativas if 'escaleno' in k]),
        'metodo_calculo': metodo_calculo  # ✅ CORRECTION: Use correct variable
    }

    with open('mapas_healpix/resultados_bispectro_angular_riguroso.json', 'w') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n💾 RIGOROUS Bispectrum results saved")

    return resultados

def visualizar_bispectro_riguroso(mapa_delta, resultados_bispectro, delta_valores, umbrales, rust_available):
    """RIGOROUS Visualization of the bispectrum analysis"""

    fig = plt.figure(figsize=(18, 12))

    # 1. δ Map
    plt.subplot(2, 3, 1)
    hp.mollview(mapa_delta, title=f"δ Field - DESI LRG (Nside={hp.get_nside(mapa_delta)})",
                unit="δ", cmap='RdBu_r', sub=(2,3,1))

    # 2. Bispectrum values with significance
    plt.subplot(2, 3, 2)
    configs = list(resultados_bispectro.keys())
    bispect_vals = [res['magnitud_absoluta'] for res in resultados_bispectro.values()]
    colores = ['red' if res['significativo'] else 'gray' for res in resultados_bispectro.values()]

    bars = plt.bar(range(len(configs)), bispect_vals, color=colores, alpha=0.7)
    plt.xticks(range(len(configs)), [f"C{i+1}" for i in range(len(configs))], rotation=45, fontsize=8)
    plt.ylabel('|B(ℓ₁,ℓ₂,ℓ₃)|')

    # ✅ CORRECTION: Indicate the real method used
    metodo = 'Rust + Wigner-3j' if rust_available else 'Python (approx)'
    plt.title(f'Angular Bispectrum DESI\n{metodo} - RED > ΛCDM Threshold')

    plt.yscale('log')
    plt.grid(True, alpha=0.3)

    # Threshold line
    plt.axhline(y=umbrales['umbral_bispectro'], color='red', linestyle='--',
                label=f'Threshold: {umbrales["umbral_bispectro"]:.1e}')

    for bar, val, sig in zip(bars, bispect_vals, colores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1,
                 f'{val:.1e}', ha='center', va='bottom', fontsize=7,
                 color='red' if sig == 'red' else 'gray')

    plt.legend()

    # 3. δ Distribution with Gaussian reference
    plt.subplot(2, 3, 3)
    if len(delta_valores) > 0:
        n, bins, patches = plt.hist(delta_valores, bins=50, density=True, alpha=0.7, color='green')

        # Reference Gaussian Distribution
        x = np.linspace(delta_valores.min(), delta_valores.max(), 100)
        gaussian_ref = stats.norm.pdf(x, delta_valores.mean(), delta_valores.std())
        plt.plot(x, gaussian_ref, 'r--', linewidth=2, label='ΛCDM Gaussian')

        plt.xlabel('δ')
        plt.ylabel('Probability Density')
        plt.title('δ Distribution vs Gaussian Reference')
        plt.legend()
        plt.grid(True, alpha=0.3)

    # 4. QQ-plot for Gaussianity
    plt.subplot(2, 3, 4)
    if len(delta_valores) > 0:
        stats.probplot(delta_valores, dist="norm", plot=plt)
        plt.title('QQ-plot: δ vs Normal Distribution')

    # 5. Statistical summary with thresholds
    plt.subplot(2, 3, 5)
    if len(delta_valores) > 0:
        stats_vals = [stats.skew(delta_valores), stats.kurtosis(delta_valores)]
        stats_labels = ['Skewness', 'Kurtosis']
        colors_stats = ['red', 'blue']

        bars_stats = plt.bar(stats_labels, stats_vals, color=colors_stats, alpha=0.7)
        plt.ylabel('Value')
        plt.title('DESI Non-Gaussianity Statistics')

        # Significance thresholds
        plt.axhline(y=umbrales['umbral_skewness'], color='red', linestyle='--',
                    alpha=0.5, label=f'Skew threshold={umbrales["umbral_skewness"]}')
        plt.axhline(y=umbrales['umbral_kurtosis'], color='purple', linestyle='--',
                    alpha=0.5, label=f'Kurt threshold={umbrales["umbral_kurtosis"]}')

        for bar, val in zip(bars_stats, stats_vals):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                     f'{val:.2f}', ha='center', va='bottom')
        plt.legend()

    # 6. Dataset and results information
    plt.subplot(2, 3, 6)
    plt.axis('off')

    configs_significativas = [k for k, v in resultados_bispectro.items() if v['significativo']]
    proporcion = len(configs_significativas) / len(resultados_bispectro) if len(resultados_bispectro) > 0 else 0

    # ✅ CORRECTION: Use real flag
    metodo_usado = 'Rust + Wigner-3j' if rust_available else 'Python (approx)'

    info_text = f"""DESI LRG DATASET
Total: {N_GALAXIAS_DESI:,} galaxies

METHOD: {metodo_usado}
Configurations: {len(resultados_bispectro)}
Significant: {len(configs_significativas)}
Proportion: {proporcion:.1%}

RIGOROUS THRESHOLDS:
|Bispectrum| > {umbrales['umbral_bispectro']:.1e}
Skewness > {umbrales['umbral_skewness']}
Kurtosis > {umbrales['umbral_kurtosis']}

REFERENCES:
Komatsu et al. (2005)
Bucher et al. (2010)
DESI Collab. (2021)"""

    plt.text(0.1, 0.9, info_text, transform=plt.gca().transAxes, fontsize=9,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig('mapas_healpix/analisis_bispectro_angular_riguroso_desi.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ RIGOROUS bispectrum visualization saved")

if __name__ == "__main__":
    resultados = calcular_bispectro_angular_riguroso()

    if resultados is not None:
        print(f"\n✅ RIGOROUS BISPECTRUM ANALYSIS COMPLETED - DESI")

        # Final RIGOROUS interpretation
        interp = resultados['interpretacion_rigurosa']
        analisis = resultados['analisis_significancia']
        stats = resultados['estadisticas_orden_superior']

        print(f"\n🎯 FINAL RIGOROUS INTERPRETATION:")
        print(f"   • Calculation Method: {interp['metodo_calculo']}")  # ✅ Now it will be correct
        print(f"   • Confidence Level: {interp['nivel_confianza']}")
        print(f"   • Significant Configurations: {analisis['configuraciones_significativas']}/{analisis['total_configuraciones']}")
        print(f"   • Gaussianity Rejected: {interp['gaussianidad_rechazada']}")
        print(f"   • Non-null Bispectrum: {interp['bispectro_no_nulo']}")
        print(f"   • Compatible with Vorticity: {interp['compatible_vorticidad']}")

        if interp['nivel_confianza'] == 'ALTO':
            print(f"\n🎉 **SOLID CONFIRMATION OF NON-GAUSSIANITY**")
            print(f"   → Angular bispectrum shows non-Gaussian signatures")
            print(f"   → Compatible with primordial cosmic vorticity")
            print(f"   → Consistent with previous spectral analysis")

            # Linkage with previous analyses
            print(f"\n🔗 LINKAGE WITH PREVIOUS RIGOROUS ANALYSES:")
            print(f"   • DESI Dataset: {N_GALAXIAS_DESI:,} LRG galaxies")
            print(f"   • Spectral: Skewness {stats['skewness']:.3f}, Kurtosis {stats['kurtosis']:.3f}")
            print(f"   • 3D Bispectrum: 10.299× corrected evolution")
            print(f"   • Faber-Jackson: Broken ($R^2 = 0.002$)")
            print(f"   • $M_c$ confirmed: $200.0\ \mathrm{km/s}$")

        elif interp['nivel_confianza'] == 'MODERADO':
            print(f"\n📈 Moderate evidence of non-Gaussianity")
            print(f"   → Additional analyses are required")
        else:
            print(f"\n⚪ Limited evidence of non-Gaussianity")

    else:
        print("❌ Error in the rigorous bispectrum analysis")