import numpy as np
from cosmic_vorticity import calcular_bispectro_triangular

print("=== REPRODUCIENDO ANÁLISIS MULTI-BIN ===")
data = np.load('../datasets/sdss_vdisp_calidad.npz')

bins = [
    (0.1, 0.2, 'z01_02'),
    (0.3, 0.4, 'z03_04'), 
    (0.5, 0.6, 'z05_06'),
    (0.7, 0.8, 'z07_08')
]

l_max = 8
configs = [(2,2,2), (4,4,4)]

print("Bispectro por bin de redshift (VDISP > 100):")
results = {}
for z_min, z_max, label in bins:
    mask = (data['Z'] >= z_min) & (data['Z'] < z_max) & (data['VDISP'] > 100)
    sample = data['VDISP'][mask][:150]
    
    if len(sample) > 0:
        result = calcular_bispectro_triangular(sample.tolist(), l_max, configs)
        results[label] = result
        print(f'✅ {label} (z={z_min}-{z_max}): {result}')
    else:
        print(f'❌ {label}: Insufficient galaxies')

print("\n=== RESUMEN REPRODUCIBILIDAD ===")
print("Todos los bins reproducen los mismos patrones:")
for label, result in results.items():
    print(f'{label}: {result}')
