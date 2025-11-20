#!/usr/bin/env python3
"""
FINAL SOLUTION: LRG DATASET WITH REAL VDISP FROM DESI DR1 FASTSPECFIT AND LUMINOSITY (FLUX_R).
*** NOW DOWNLOADING AND PROCESSING THE COMPLETE SET OF 24 FILES ***
*** WITH IMMEDIATE DELETION OF RAW FILES TO SAVE SPACE ***
"""

import requests
import os
import subprocess
import re
from astropy.io import fits
import numpy as np
from astropy.table import Table, vstack, join

# Base URL
BASE_URL = "https://data.desi.lbl.gov/public/dr1/vac/dr1/fastspecfit/iron/v3.0/catalogs/"

def get_complete_healpix_list():
    """Gets the complete list of Healpix files"""
    print("🎯 GETTING COMPLETE LIST OF HEALPIX FILES")
    print("=" * 65)

    try:
        # Use cURL's ls -l to get the list, size, and name
        result = subprocess.run(['curl', '-s', BASE_URL], capture_output=True, text=True, timeout=60)
        healpix_files = []
        for line in result.stdout.split('\n'):
            # Look for links to .fits files containing the LRG patterns
            if any(pattern in line for pattern in ['main-dark-nside1-hp', 'main-bright-nside1-hp']) and '.fits' in line:
                match = re.search(r'>([^<]+\.fits)<', line)
                if match:
                    file_name = match.group(1)
                    size_match = re.search(r'(\d+(?:\.\d+)?[KMG]B)', line)
                    size = size_match.group(1) if size_match else "unknown size"
                    healpix_files.append((file_name, size))

        if healpix_files:
            print(f"📋 FOUND {len(healpix_files)} HEALPIX FILES ON THE SERVER:")
            healpix_files.sort(key=lambda x: x[0], reverse=False) # Sort for better visualization
            for file_name, size in healpix_files[:5]:
                print(f"    • {file_name} ({size})")
            if len(healpix_files) > 5:
                print("    • ... (omitting the rest)")

            return [a[0] for a in healpix_files], BASE_URL
        else:
            print("❌ No Healpix files found")

    except Exception as e:
        print(f"❌ Error getting list: {e}")

    return [], BASE_URL

def process_lrg_file(file_path):
    """
    Reads HDUs and joins data. Includes FLUX_R from the METADATA HDU.
    Saves as a temporary file with the prefix 'temp_lrg_'.
    """
    base_name = os.path.basename(file_path)
    print(f"\n🔍 Processing: {base_name}")

    try:
        with fits.open(file_path) as hdul:

            # --- 1. Read and extract SPECPHOT data (VDISP) ---
            if 'SPECPHOT' not in hdul:
                print(f"    ❌ SPECPHOT HDU not found")
                return None

            table_specphot = Table.read(hdul['SPECPHOT'])
            cols_specphot_req = ['TARGETID', 'VDISP', 'VDISP_IVAR']

            if not all(col in table_specphot.colnames for col in cols_specphot_req):
                missing = [col for col in cols_specphot_req if col not in table_specphot.colnames]
                print(f"    ❌ SPECPHOT HDU is incomplete. Missing: {missing}")
                return None

            table_specphot = table_specphot[cols_specphot_req]

            # --- 2. Read and extract METADATA data (Z, RA, DEC, DESI_TARGET, FLUX_R) ---
            if 'METADATA' not in hdul:
                print(f"    ❌ METADATA HDU not found")
                return None

            table_targets = Table.read(hdul['METADATA'])
            # ADDING FLUX_R, which is the luminosity in the r-band (nanomaggies)
            cols_targets_req = ['TARGETID', 'RA', 'DEC', 'DESI_TARGET', 'Z', 'FLUX_R']

            if not all(col in table_targets.colnames for col in cols_targets_req):
                missing = [col for col in cols_targets_req if col not in table_targets.colnames]
                print(f"    ❌ METADATA HDU is incomplete. Missing: {missing}")
                return None

            table_targets = table_targets[cols_targets_req]

            # --- 3. Join the tables by TARGETID ---
            complete_data = join(table_specphot, table_targets, keys='TARGETID', join_type='inner')

            n_total = len(complete_data)
            print(f"    • Total objects joined: {n_total:,}")

            # --- 4. Filter LRG galaxies and VDISP quality ---
            LRG_BIT = 0
            lrg_mask = 2 ** LRG_BIT

            is_lrg = (complete_data['DESI_TARGET'] & lrg_mask) != 0
            data_lrg = complete_data[is_lrg]
            n_lrg = len(data_lrg)

            if n_lrg == 0:
                print(f"    ⚠️ No LRG galaxies found")
                return None

            print(f"    ✅ {n_lrg:,} LRG galaxies found")

            # VDISP error calculation (handling IVAR = 0)
            ivar = np.array(data_lrg['VDISP_IVAR'])
            # RuntimeWarning: divide by zero encountered in divide is expected here, already handled with np.nan
            with np.errstate(divide='ignore', invalid='ignore'):
                data_lrg['VDISP_ERR'] = np.where(ivar > 0, 1.0 / np.sqrt(ivar), np.nan)

            # Quality filter (VDISP and error)
            valid_mask = (
                (data_lrg['VDISP'] > 50) &
                (data_lrg['VDISP'] < 500) &
                (~np.isnan(data_lrg['VDISP_ERR'])) &
                (data_lrg['VDISP_ERR'] > 0) &
                (data_lrg['VDISP_ERR'] < 100)
            )

            filtered_table = data_lrg[valid_mask]
            n_valid = len(filtered_table)

            print(f"    📊 {n_valid:,} LRG with valid VDISP, error, and FLUX_R")

            if n_valid == 0:
                return None

            # --- 5. Save as a temporary file ---
            output_temp_name = f"temp_lrg_{base_name}"
            filtered_table.write(output_temp_name, overwrite=True)
            print(f"    💾 Temporary saved: {output_temp_name}")

            return filtered_table

    except Exception as e:
        print(f"    ❌ Error processing file: {type(e).__name__}: {e}")
        return None

def main():
    print("🚀 BUILDING LRG DATASET WITH REAL VDISP AND LUMINOSITY (FLUX_R)")
    print("=" * 75)
    print("💡 STRATEGY: Download → Process → Delete (to save space)")
    print("=" * 75)

    healpix_files, base_url = get_complete_healpix_list()

    if not healpix_files:
        print("❌ Critical files not found")
        return

    os.makedirs('lrg_completo', exist_ok=True) # Temporary folder for downloads
    successfully_processed_files = []

    # Loop to download, process, and delete (SEQUENTIALLY)
    for i, file_name in enumerate(sorted(healpix_files)):
        file_path = f"lrg_completo/{file_name}"
        url = base_url + file_name

        print(f"\n--- 🔄 Starting batch {i+1}/{len(healpix_files)}: {file_name} ---")

        # 1. DOWNLOAD THE SINGLE FILE
        if not os.path.exists(file_path):
            print(f"📥 Downloading {file_name}...")
            try:
                # Get file size for feedback
                response = requests.head(url, timeout=15)
                size_bytes = int(response.headers.get('content-length', 0))
                size_mb = size_bytes / 1024 / 1024
                print(f"    • Size: {size_mb:.1f} MB")

                # Robust download with wget
                subprocess.run([
                    'wget', '--progress=bar:force',
                    '--timeout=900', '--tries=5',
                    '-O', file_path, url
                ], check=True, timeout=1800)
                print(f"✅ Downloaded: {file_name}")
            except Exception as e:
                print(f"❌ Error downloading {file_name}: {type(e).__name__}: {e}")
                continue # Skip to the next file if download fails
        else:
            print(f"✅ Already exists: {file_name} (continuing with processing)")

        # 2. PROCESS THE FILE (Creates temp_lrg_*.fits)
        filtered_table = process_lrg_file(file_path)

        # 3. DELETE THE RAW FILE IMMEDIATELY
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted raw file: {file_path} to free up space.")
                if filtered_table is not None:
                    # If the original was processed and deleted successfully, it's considered a success
                    successfully_processed_files.append(file_name)
            except Exception as e:
                print(f"⚠️ Error deleting {file_path}: {e}")
                # This should not stop the process, but requires attention.
        else:
            print(f"⚠️ File {file_path} no longer exists (perhaps processing failed).")

    # Clean up temporary folder if empty
    try:
        if os.path.exists('lrg_completo') and not os.listdir('lrg_completo'):
            os.rmdir('lrg_completo')
            print(f"🗑️ Temporary folder 'lrg_completo' deleted (it was empty).")
    except Exception as e:
        print(f"⚠️ Could not delete temporary folder: {e}")

    print(f"\n" + "="*75)
    print(f"✅ PROCESSING COMPLETE. {len(successfully_processed_files)} temporary files generated.")
    print("📊 Generated temporary files:")
    for file_name in successfully_processed_files:
        print(f"    • temp_lrg_{file_name}")
    print("🎯 NEXT STEP: Run COMBINAR_DATASET_DESI_LUM_FINAL.py to merge all *temporary* files.")
    print("="*75)

if __name__ == "__main__":
    main()