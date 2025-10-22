import numpy as np
import os

# --- DOWNLOAD CONFIGURATION ---
NUM_PARTES = 4
NOMBRE_BASE = 'lrg_analysis_features_part_'

print("Starting reconstruction from downloaded .npy files...")
print("-" * 30)

# 1. LOAD AND JOIN THE PARTS OF THE LARGE ARRAY ('PROXY_MASA')
partes_cargadas = []
for i in range(NUM_PARTES):
    filename = f'{NOMBRE_BASE}{i+1}_of_{NUM_PARTES}.npy'

    try:
        parte = np.load(filename)
        partes_cargadas.append(parte)
        print(f"✅ Part {i+1} of PROXY_MASA loaded. Shape: {parte.shape}")
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {filename}")
        print("Make sure all .npy files are in the same folder as this script.")
        exit()

# Concatenate to reconstruct the mass array
PROXY_MASA_RECONSTRUIDO = np.concatenate(partes_cargadas, axis=0)

# 2. LOAD THE SMALL ARRAYS
TARGETID = np.load('TARGETID.npy')
RA = np.load('RA.npy')
DEC = np.load('DEC.npy')
Z = np.load('Z.npy')
WEIGHT_ZFAIL = np.load('WEIGHT_ZFAIL.npy')

# 3. SAVE THE FINAL FILE (Original .npz format)
NOMBRE_FINAL = 'lrg_analysis_subset.npz'

# We use savez_compressed to recreate the original structure (.npz)
np.savez_compressed(
    NOMBRE_FINAL,
    TARGETID=TARGETID,
    RA=RA,
    DEC=DEC,
    Z=Z,
    PROXY_MASA=PROXY_MASA_RECONSTRUIDO,  # We use the reconstructed array
    WEIGHT_ZFAIL=WEIGHT_ZFAIL
)

print("-" * 30)
print("⭐ Data reconstruction completed!")
print(f"The final file '{NOMBRE_FINAL}' has been saved.")
print(f"Reconstructed PROXY_MASA shape: {PROXY_MASA_RECONSTRUIDO.shape}")