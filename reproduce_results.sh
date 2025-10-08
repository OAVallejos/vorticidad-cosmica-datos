#!/bin/bash
echo "=== REPRODUCIBILITY SCRIPT - Cosmic Vorticity Paper ==="

# 1. Verificar datos
echo "1. Verificando datasets..."
python3 -c "
import numpy as np
data = np.load('datasets/sdss_vdisp_calidad.npz')
print(f'✅ Dataset cargado: {len(data[\"VDISP\"]):,} galaxias')
print(f'   VDISP: {data[\"VDISP\"].min():.1f}-{data[\"VDISP\"].max():.1f} km/s')
print(f'   Redshift: {data[\"Z\"].min():.3f}-{data[\"Z\"].max():.3f}')
"

# 2. Reproducir análisis multi-bin
echo "2. Reproduciendo análisis multi-bin..."
python3 code/reproduce_multi_bin.py

# 3. Verificar bispectro
echo "3. Probando bispectro..."
python3 code/test_bispectro.py

echo "=== REPRODUCIBILIDAD COMPLETADA ==="
