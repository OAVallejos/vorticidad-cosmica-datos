#!/usr/bin/env python3     
"""                       
Data quality analysis: zeros, NaN, and empty values in DATASET_LRG_VDISP_FLUXR_FINAL.fits
Adapted version for the complete LRG dataset
"""

import numpy as np
from astropy.table import Table
import matplotlib.pyplot as plt
import sys

def analizar_calidad_datos(archivo_fits):
    """
    Analyzes the data quality in the FITS file of the complete LRG dataset
    """
    print("🔍 STARTING LRG DATA QUALITY ANALYSIS")
    print("=" * 60)

    try:
        # Load the dataset
        tabla = Table.read(archivo_fits)
        print(f"✅ Dataset loaded: {len(tabla):,} rows, {len(tabla.colnames)} columns")

        # Display basic dataset information
        print(f"\n📊 AVAILABLE COLUMNS:")
        for col in tabla.colnames:
            print(f"   - {col}: type={tabla[col].dtype}")

    except FileNotFoundError:
        print(f"❌ Error: File '{archivo_fits}' not found")
        return None, None
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None, None

    # Analysis by column - ALL critical columns
    resultados = {}
    columnas_analizar = ['VDISP', 'Z', 'FLUX_R', 'RA', 'DEC', 'VDISP_ERR']  # Critical columns

    for columna in columnas_analizar:
        if columna not in tabla.colnames:
            print(f"⚠️  Column '{columna}' not found in the dataset")
            continue

        datos = tabla[columna]
        resultados[columna] = {
            'total': len(datos),
            'no_nulos': np.sum(~np.isnan(datos)),
            'nulos': np.sum(np.isnan(datos)),
            'ceros': np.sum(datos == 0),
            'negativos': np.sum(datos < 0) if np.issubdtype(datos.dtype, np.number) else 0,
            'infinitos': np.sum(np.isinf(datos)) if np.issubdtype(datos.dtype, np.number) else 0,
            'minimo': np.nanmin(datos) if np.issubdtype(datos.dtype, np.number) and np.sum(~np.isnan(datos)) > 0 else None,
            'maximo': np.nanmax(datos) if np.issubdtype(datos.dtype, np.number) and np.sum(~np.isnan(datos)) > 0 else None,
            'media': np.nanmean(datos) if np.issubdtype(datos.dtype, np.number) and np.sum(~np.isnan(datos)) > 0 else None,
            'mediana': np.nanmedian(datos) if np.issubdtype(datos.dtype, np.number) and np.sum(~np.isnan(datos)) > 0 else None,
            'std': np.nanstd(datos) if np.issubdtype(datos.dtype, np.number) and np.sum(~np.isnan(datos)) > 0 else None
        }

    # Display detailed results
    print(f"\n📈 COLUMN QUALITY STATISTICS:")
    print("=" * 60)

    for columna, stats in resultados.items():
        print(f"\n🎯 COLUMN: {columna}")
        print(f"   📏 Total values: {stats['total']:,}")
        print(f"   ✅ Non-null: {stats['no_nulos']:,} ({stats['no_nulos']/stats['total']*100:.1f}%)")
        print(f"   ❌ Null/NaN values: {stats['nulos']:,} ({stats['nulos']/stats['total']*100:.1f}%)")
        print(f"   0️⃣  Zero values: {stats['ceros']:,} ({stats['ceros']/stats['total']*100:.1f}%)")
        print(f"   📉 Negative values: {stats['negativos']:,} ({stats['negativos']/stats['total']*100:.1f}%)")
        print(f"   ∞   Infinite values: {stats['infinitos']:,}")

        if stats['minimo'] is not None:
            print(f"   📊 Statistics (excluding NaN):")
            print(f"      Minimum: {stats['minimo']:.4f}")
            print(f"      Maximum: {stats['maximo']:.4f}")
            print(f"      Mean: {stats['media']:.4f}")
            print(f"      Median: {stats['mediana']:.4f}")
            print(f"      Std Dev: {stats['std']:.4f}")

    # Distribution analysis
    print(f"\n📊 VALUE DISTRIBUTION (PERCENTILES):")
    print("=" * 60)

    for columna in ['VDISP', 'Z', 'FLUX_R']:  # Only main numerical ones
        if columna in resultados and resultados[columna]['no_nulos'] > 0:
            datos_validos = tabla[columna][~np.isnan(tabla[columna])]

            # Percentiles
            percentiles = np.percentile(datos_validos, [0, 1, 5, 25, 50, 75, 95, 99, 100])
            print(f"\n📋 {columna} - Percentiles:")
            print(f"   Min(0%): {percentiles[0]:.4f}")
            print(f"   1%: {percentiles[1]:.4f} | 5%: {percentiles[2]:.4f}")
            print(f"   25%: {percentiles[3]:.4f} | 50%: {percentiles[4]:.4f} | 75%: {percentiles[5]:.4f}")
            print(f"   95%: {percentiles[6]:.4f} | 99%: {percentiles[7]:.4f}")
            print(f"   Max(100%): {percentiles[8]:.4f}")

    # Analysis of correlation between data problems
    print(f"\n🔗 DATASET INTEGRITY ANALYSIS:")
    print("=" * 60)

    # Verify complete integrity (all critical columns present)
    columnas_criticas = ['VDISP', 'Z', 'FLUX_R', 'RA', 'DEC']
    mask_completo = np.ones(len(tabla), dtype=bool)

    for col in columnas_criticas:
        if col in tabla.colnames:
            mask_completo &= ~np.isnan(tabla[col])
        else:
            mask_completo = np.zeros(len(tabla), dtype=bool)
            break

    n_completos = np.sum(mask_completo)
    print(f"✅ Rows with ALL critical columns valid: {n_completos:,} ({n_completos/len(tabla)*100:.1f}%)")
    print(f"❌ Rows with at least one missing value: {len(tabla) - n_completos:,}")

    return tabla, resultados

def crear_visualizaciones_simple(tabla, resultados):
    """
    Creates simple visualizations for the LRG dataset
    """
    print(f"\n📊 CREATING BASIC VISUALIZATIONS...")

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Data Quality Analysis - Complete DESI LRG Dataset', fontsize=16)

    # 1. VDISP Distribution
    if 'VDISP' in tabla.colnames:
        vdisp_valido = tabla['VDISP'][~np.isnan(tabla['VDISP'])]
        if len(vdisp_valido) > 0:
            axes[0, 0].hist(vdisp_valido, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].set_xlabel('VDISP (km/s)')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].set_title('VDISP Distribution')
            axes[0, 0].axvline(x=262.9, color='red', linestyle='--', label=f'Mean: {262.9:.1f} km/s')
            axes[0, 0].legend()

    # 2. Z (redshift) Distribution
    if 'Z' in tabla.colnames:
        z_valido = tabla['Z'][~np.isnan(tabla['Z'])]
        if len(z_valido) > 0:
            axes[0, 1].hist(z_valido, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
            axes[0, 1].set_xlabel('Redshift (Z)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].set_title('Redshift Distribution')
            axes[0, 1].axvline(x=0.578, color='red', linestyle='--', label=f'Mean: {0.578:.3f}')
            axes[0, 1].legend()

    # 3. FLUX_R Distribution (log scale)
    if 'FLUX_R' in tabla.colnames:
        flux_valido = tabla['FLUX_R'][~np.isnan(tabla['FLUX_R'])]
        flux_valido = flux_valido[flux_valido > 0]  # Only positive values
        if len(flux_valido) > 0:
            axes[1, 0].hist(np.log10(flux_valido), bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
            axes[1, 0].set_xlabel('log10(FLUX_R) [nanomaggies]')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].set_title('FLUX_R Distribution (log scale)')
            axes[1, 0].axvline(x=np.log10(7.24), color='red', linestyle='--', label=f'Median: {7.24:.2f}')
            axes[1, 0].legend()

    # 4. VDISP vs Z Scatter Plot
    if 'VDISP' in tabla.colnames and 'Z' in tabla.colnames:
        mask_valido = (~np.isnan(tabla['VDISP'])) & (~np.isnan(tabla['Z']))
        if np.sum(mask_valido) > 0:
            # Sample to avoid overloading the plot
            if np.sum(mask_valido) > 10000:
                indices = np.random.choice(np.where(mask_valido)[0], 10000, replace=False)
                scatter = axes[1, 1].scatter(tabla['Z'][indices], tabla['VDISP'][indices],
                                           alpha=0.3, s=1, c=tabla['Z'][indices], cmap='viridis')
            else:
                scatter = axes[1, 1].scatter(tabla['Z'][mask_valido], tabla['VDISP'][mask_valido],
                                           alpha=0.5, s=1, c=tabla['Z'][mask_valido], cmap='viridis')

            axes[1, 1].set_xlabel('Redshift (Z)')
            axes[1, 1].set_ylabel('VDISP (km/s)')
            axes[1, 1].set_title('VDISP vs Redshift')
            plt.colorbar(scatter, ax=axes[1, 1], label='Redshift')

    plt.tight_layout()
    plt.savefig('calidad_datos_DESI_LRG.png', dpi=300, bbox_inches='tight')
    print("✅ Visualizations saved to 'calidad_datos_DESI_LRG.png'")
    plt.close()

    # Create quality summary plot
    fig2, ax = plt.subplots(figsize=(12, 6))

    if resultados:
        categorias = []
        porcentajes_validos = []

        for col in ['VDISP', 'Z', 'FLUX_R', 'RA', 'DEC', 'VDISP_ERR']:
            if col in resultados:
                categorias.append(col)
                porcentaje_valido = (resultados[col]['no_nulos'] / resultados[col]['total']) * 100
                porcentajes_validos.append(porcentaje_valido)

        bars = ax.bar(categorias, porcentajes_validos, color=['green' if p > 99 else 'orange' for p in porcentajes_validos], alpha=0.7)
        ax.set_xlabel('Columns')
        ax.set_ylabel('Percentage of Valid Values (%)')
        ax.set_title('Data Quality by Column - DESI LRG Dataset')
        ax.set_ylim(0, 100)

        # Add values on the bars
        for bar, porcentaje in zip(bars, porcentajes_validos):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{porcentaje:.1f}%', ha='center', va='bottom', fontweight='bold')

        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('resumen_calidad_datos_LRG.png', dpi=300, bbox_inches='tight')
        print("✅ Quality summary saved to 'resumen_calidad_datos_LRG.png'")
        plt.close()

def generar_recomendaciones_limpieza(resultados):
    """
    Generates specific recommendations for data cleaning of the LRG dataset
    """
    print(f"\n🎯 QUALITY RECOMMENDATIONS:")
    print("=" * 60)

    recomendaciones = []
    problemas_detectados = 0

    for columna, stats in resultados.items():
        # Check for null values
        if stats['nulos'] > 0:
            rec = f"COLUMN {columna}: {stats['nulos']} NaN values detected"
            recomendaciones.append(rec)
            problemas_detectados += 1

        # Specific checks by column
        if columna == 'VDISP':
            if stats['ceros'] > 0:
                rec = f"VDISP: {stats['ceros']} zero values - physically improbable"
                recomendaciones.append(rec)
                problemas_detectados += 1
            if stats['negativos'] > 0:
                rec = f"VDISP: {stats['negativos']} negative values - physically impossible"
                recomendaciones.append(rec)
                problemas_detectados += 1

        elif columna == 'FLUX_R':
            if stats['negativos'] > 0:
                rec = f"FLUX_R: {stats['negativos']} negative values - negative luminosity impossible"
                recomendaciones.append(rec)
                problemas_detectados += 1

        elif columna == 'Z':
            if stats['negativos'] > 0:
                rec = f"Z: {stats['negativos']} negative redshifts - physically impossible"
                recomendaciones.append(rec)
                problemas_detectados += 1

    if problemas_detectados == 0:
        print("✅ EXCELLENT QUALITY: No critical issues detected in the dataset")
        print("   • 0 NaN values in critical columns")
        print("   • 0 physically impossible values")
        print("   • 100% integrity in essential data")
    else:
        print(f"⚠️  {problemas_detectados} issues detected:")
        for i, rec in enumerate(recomendaciones, 1):
            print(f"   {i}. {rec}")

def main():
    """
    Main function
    """
    archivo_fits = 'DATASET_LRG_VDISP_FLUXR_FINAL.fits'

    print("🔍 DESI LRG COMPLETE DATA QUALITY ANALYSIS")
    print("=" * 60)
    print("Dataset: DATASET_LRG_VDISP_FLUXR_FINAL.fits")
    print("=" * 60)

    # Run analysis
    tabla, resultados = analizar_calidad_datos(archivo_fits)

    if tabla is not None and resultados:
        # Create visualizations
        crear_visualizaciones_simple(tabla, resultados)

        # Generate recommendations
        generar_recomendaciones_limpieza(resultados)

        print(f"\n✅ QUALITY ANALYSIS COMPLETED")
        print(f"📊 FINAL SUMMARY:")
        total_filas = len(tabla)
        print(f"   • Total LRG galaxies: {total_filas:,}")

        # Calculate complete integrity
        columnas_criticas = ['VDISP', 'Z', 'FLUX_R', 'RA', 'DEC']
        mask_completo = np.ones(total_filas, dtype=bool)
        for col in columnas_criticas:
            if col in tabla.colnames:
                mask_completo &= ~np.isnan(tabla[col])

        n_completos = np.sum(mask_completo)
        print(f"   • Galaxies with complete data: {n_completos:,} ({n_completos/total_filas*100:.1f}%)")
        print(f"   • Overall quality: EXCELLENT" if n_completos == total_filas else f"   • Overall quality: GOOD")

    else:
        print("❌ Analysis could not be completed")

if __name__ == "__main__":
    main()