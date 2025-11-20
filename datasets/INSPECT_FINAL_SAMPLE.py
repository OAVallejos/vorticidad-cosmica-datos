#!/usr/bin/env python3
"""
Verifies the existence and content of the LRG dataset with REAL VDISP.
NOW COMPATIBLE WITH: DATASET_LRG_VDISP_FLUXR_FINAL.fits
"""

import os
import numpy as np
from astropy.table import Table

def calculate_table_size(table):
    """Calculates the approximate in-memory size of a table"""
    total_size = 0
    for colname in table.colnames:
        col = table[colname]
        if hasattr(col, 'nbytes'):
            total_size += col.nbytes
        else:
            # Conservative estimate for columns without nbytes
            total_size += len(col) * 8  # Assumes 8 bytes per element
    return total_size

def inspect_catalog():
    """Loads and inspects the final dataset."""
    final_file = "DATASET_LRG_VDISP_FLUXR_FINAL.fits"

    if not os.path.exists(final_file):
        print(f"❌ ERROR: The final file '{final_file}' does not exist.")
        print("Make sure you have run COMBINAR_DATASET_DESI_LUM_FINAL.py first.")
        return

    print(f"✅ File found: {final_file}")

    try:
        # Load the FITS file
        tabla = Table.read(final_file)

        print(f"📊 TOTAL LRG GALAXIES WITH REAL VDISP: {len(tabla):,}")
        print(f"\n📋 AVAILABLE COLUMNS ({len(tabla.colnames)}):")
        for i, col in enumerate(tabla.colnames):
            print(f"   {i+1:2d}. {col}")

        # Show complete statistics
        print(f"\n📈 COMPLETE DATASET STATISTICS:")
        print(f"   • VDISP: {tabla['VDISP'].min():.1f} - {tabla['VDISP'].max():.1f} km/s")
        print(f"   • Mean VDISP: {tabla['VDISP'].mean():.1f} ± {tabla['VDISP'].std():.1f} km/s")
        print(f"   • Redshift (Z): {tabla['Z'].min():.3f} - {tabla['Z'].max():.3f}")
        print(f"   • Mean Redshift: {tabla['Z'].mean():.3f} ± {tabla['Z'].std():.3f}")
        print(f"   • FLUX_R: {tabla['FLUX_R'].min():.2f} - {tabla['FLUX_R'].max():.2f}")
        print(f"   • Median FLUX_R: {np.median(tabla['FLUX_R']):.2f}")

        # Calculate luminosity proxy if necessary for analysis
        print(f"\n🔧 CALCULATING LUMINOSITY PROXY...")
        tabla['PROXY_L'] = tabla['VDISP']**2 * tabla['FLUX_R']
        print(f"   • PROXY_L = VDISP² × FLUX_R (luminosity proxy)")
        print(f"   • PROXY_L range: {tabla['PROXY_L'].min():.2e} - {tabla['PROXY_L'].max():.2e}")

        print(f"\n⭐ SAMPLE OF 5 GALAXIES (key columns):")
        sample_columns = ['TARGETID', 'RA', 'DEC', 'Z', 'VDISP', 'FLUX_R', 'PROXY_L']
        print(tabla[sample_columns][:5])

        # Additional dataset information
        print(f"\n💾 ADDITIONAL INFORMATION:")
        size_mb = calculate_table_size(tabla) / 1024 / 1024
        print(f"   • Approximate memory: {size_mb:.1f} MB")
        print(f"   • Unique objects (TARGETID): {len(np.unique(tabla['TARGETID'])):,}")
        print(f"   • Cosmic range covered: z = {tabla['Z'].min():.3f} - {tabla['Z'].max():.3f}")

        # Luminosity proxy statistics
        print(f"\n🎯 PROXY_L STATISTICS:")
        print(f"   • VDISP vs FLUX_R correlation: {np.corrcoef(tabla['VDISP'], tabla['FLUX_R'])[0,1]:.3f}")
        print(f"   • VDISP vs Z correlation: {np.corrcoef(tabla['VDISP'], tabla['Z'])[0,1]:.3f}")
        print(f"   • PROXY_L vs Z correlation: {np.corrcoef(tabla['PROXY_L'], tabla['Z'])[0,1]:.3f}")

    except Exception as e:
        print(f"❌ ERROR reading or inspecting the file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_catalog()