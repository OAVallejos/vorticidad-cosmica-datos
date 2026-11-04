"""
fkp_weights_v3.py                   Calcula el mapa de pesos FKP en HEALPix (NSIDE=64) a partir de los randoms V3.
V3:                             • Compatibilidad total con la nomenclatura de randoms_generator_v3.py (*_randoms_v3.h5).
  • Lectura y promedio espacial por píxel HEALPix de los pesos FKP dinámicos w(z).
  • Vectorización completa con np.bincount ponderado.
"""
import numpy as np
import healpy as hp
import h5py
from pathlib import Path
import logging
import gc

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

NSIDE = 64
NPIX = hp.nside2npix(NSIDE)
P0_FKP = 1e4  # h⁻³ Mpc³


class FKPWeightCalculatorV3:
    """Calcula mapa de pesos FKP promediando los randoms HDF5 por píxel HEALPix."""

    def __init__(self, nside: int = NSIDE, P0: float = P0_FKP):
        self.nside = nside
        self.npix = hp.nside2npix(nside)
        self.P0 = P0

    def calculate_weights(self, randoms_path: Path) -> np.ndarray:
        """
        Calcula el mapa de pesos promediando el peso dinámico w(z) de los randoms
        que caen en cada píxel HEALPix válido.
        """
        log.info(f"Calculando pesos FKP espaciales para {randoms_path.name}")

        with h5py.File(randoms_path, 'r') as f:
            pixel_chunk = f['pixel'][:]  # int32
            weight_chunk = f['weight'][:]  # float32 (pesos FKP dinámicos de v3)

        # Suma de pesos y conteo de objetos por píxel (vectorizado)
        sum_weights = np.bincount(pixel_chunk, weights=weight_chunk, minlength=self.npix)
        counts = np.bincount(pixel_chunk, minlength=self.npix)

        mask = counts > 0
        weight_map = np.zeros(self.npix, dtype=np.float32)

        # Promedio del peso FKP por píxel ocupado
        weight_map[mask] = sum_weights[mask] / counts[mask]

        log.info(f"  Píxeles con randoms válidos: {mask.sum()} / {self.npix}")
        log.info(f"  Peso FKP promedio en mapa: {weight_map[mask].mean():.4f} (min: {weight_map[mask].min():.4f}, max: {weight_map[mask].max():.4f})")

        return weight_map

    def save_weights(self, weight_map: np.ndarray, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        hp.write_map(str(output_path), weight_map,
                     overwrite=True, fits_IDL=False, nest=False)
        log.info(f"✅ Guardado en {output_path} ({output_path.stat().st_size / 1e3:.1f} KB)")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    calculator = FKPWeightCalculatorV3(nside=NSIDE, P0=P0_FKP)

    randoms_dir = Path("randoms")
    # Buscamos los archivos generados por la v3
    randoms_files = sorted(randoms_dir.glob("*_randoms_v3.h5"))

    if not randoms_files:
        log.error("No hay archivos *_randoms_v3.h5 en randoms/")
        exit(1)

    log.info(f"Encontrados {len(randoms_files)} archivos de randoms V3")

    for randoms_path in randoms_files:
        # Parsear nombre robusto: {survey}_{grupo}_{bin}_randoms_v3.h5
        stem = randoms_path.stem  # ej: sdss_baja_masa_z01_02_randoms_v3
        clean_stem = stem.replace("_randoms_v3", "") # sdss_baja_masa_z01_02

        parts = clean_stem.split("_")
        survey = parts[0].upper()
        grupo = "_".join(parts[1:-2]).upper()       # BAJA_MASA
        bin_z = "_".join(parts[-2:])                # z01_02

        # dz desde bin_z
        zp = bin_z[1:].split("_")
        dz = (float(zp[1]) - float(zp[0])) / 10.0

        log.info(f"\n{'='*60}\nPROCESANDO PESOS: {survey} | {grupo} | {bin_z} (dz={dz:.2f})\n{'='*60}")

        try:
            weight_map = calculator.calculate_weights(randoms_path)
        except Exception as e:
            log.error(f"❌ Error calculando pesos para {randoms_path.name}: {e}")
            continue

        output_path = Path(
            f"weights_fkp/{survey.lower()}_{grupo.lower()}_{bin_z}_weights.fits"
        )
        calculator.save_weights(weight_map, output_path)

        del weight_map
        gc.collect()

    log.info("🎉 Mapas de pesos FKP V3 generados exitosamente.")