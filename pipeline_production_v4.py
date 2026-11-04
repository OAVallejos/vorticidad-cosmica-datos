"""                           
pipeline_production_v4.py
Orquestador maestro de producción para los 12 bines (SDSS y DESI).                        Fase 1: Generación de randoms 50x (HDF5 por chunks).
Fase 2: Cálculo de mapas FKP en FITS (HEALPix NSIDE=64).
Fase 3: Ejecución del pipeline de bispectro en Rust (FFI con a_lm).
"""
import gc
import logging
import re
from pathlib import Path
import numpy as np
import healpy as hp
import cosmic_vorticity as cv

from nz_estimator_v3 import N_zEstimator
from randoms_generator_v3 import RandomsGeneratorV3
from fkp_weights_v3 import FKPWeightCalculatorV3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# Matriz completa de configuración de producción (12 bines)
CONFIGURACIONES_12_BINES = [
    # SDSS
    ("SDSS", "BAJA_MASA", "z01_02", 153023),
    ("SDSS", "BAJA_MASA", "z07_08", 25219),
    ("SDSS", "MEDIA_MASA", "z01_02", 75784),
    ("SDSS", "MEDIA_MASA", "z07_08", 25694),
    ("SDSS", "ALTA_MASA", "z01_02", 26856),
    ("SDSS", "ALTA_MASA", "z07_08", 94277),
    # DESI
    ("DESI", "BAJA_MASA", "z04_06", 79280),
    ("DESI", "BAJA_MASA", "z08_10", 9283),
    ("DESI", "MEDIA_MASA", "z04_06", 176387),
    ("DESI", "MEDIA_MASA", "z08_10", 25903),
    ("DESI", "ALTA_MASA", "z04_06", 315486),
    ("DESI", "ALTA_MASA", "z08_10", 103946),
]


def expand_alm_healpy(alm, lmax):
    """Expande a_lm compacto healpy → layout Rust (l²+l+m)."""
    full_alm = np.zeros((lmax + 1)**2, dtype=np.complex64)
    for l in range(lmax + 1):
        for m in range(l + 1):
            idx_hp = hp.Alm.getidx(lmax, l, m)
            val = alm[idx_hp]
            full_alm[l**2 + l + m] = val
            if m > 0:
                full_alm[l**2 + l - m] = ((-1)**m) * np.conj(val)
    return full_alm


def calcular_factor_normalizacion_I123(weights_fits_path: Path, nbar_survey: float) -> float:
    weight_map = hp.read_map(str(weights_fits_path), verbose=False)
    mask = weight_map > 0
    if not mask.any():
        return 1.0
    w_valid = weight_map[mask]
    w3_mean = np.mean(w_valid ** 3)
    factor_I123 = w3_mean * (nbar_survey ** 2)
    return 1.0 / factor_I123 if factor_I123 > 0 else 1.0


def generar_configuraciones_triangulos(l_max: int):
    """
    Genera configuraciones de triángulos válidas hasta l_max.
    Para V20 (l_max=25), esto expande el espacio de ~44 a ~860 configuraciones,
    aplicando desigualdad triangular y filtro de paridad par para robustez.
    """
    configs = []
    for l1 in range(2, l_max + 1):
        for l2 in range(l1, l_max + 1):
            for l3 in range(l2, l_max + 1):
                # Desigualdad triangular estricta
                if l3 <= l1 + l2:
                    # Filtro de paridad (l1 + l2 + l3 debe ser par)
                    if (l1 + l2 + l3) % 2 == 0:
                        configs.append((l1, l2, l3))
    return configs


def ejecutar_pipeline_completo(l_max: int = 25):
    log.info("=" * 80)
    log.info(f"🚀 INICIO DEL PIPELINE DE PRODUCCIÓN GLOBAL V3 (12 BINES) - L_MAX={l_max}")
    log.info("=" * 80)

    # Inicializar estimador cosmológico V3 (carga EDA una sola vez)
    estimator = N_zEstimator("EDA_VDISP.json")
    weight_calculator = FKPWeightCalculatorV3(nside=64, P0=1e4)

    resultados_globales = {}

    # Generar configuraciones de triángulos dinámicamente según l_max
    configs = generar_configuraciones_triangulos(l_max)
    log.info(f"  [Config] Se evaluarán {len(configs)} configuraciones de triángulos hasta l_max={l_max}.")

    for survey, grupo, bin_z, n_data_real in CONFIGURACIONES_12_BINES:
        log.info(f"\n" + "-" * 80)
        log.info(f"PROCESANDO BIN: {survey} | {grupo} | {bin_z} (N_data = {n_data_real:,})")
        log.info("-" * 80)

        # ---------------------------------------------------------------------
        # FASE 1: Generación de Randoms (Factor 50x en HDF5)
        # ---------------------------------------------------------------------
        output_randoms = Path(f"randoms/{survey.lower()}_{grupo.lower()}_{bin_z}_produccion.h5")

        if not output_randoms.exists():
            log.info(f"  [Fase 1] Generando catálogo randoms 50x -> {output_randoms.name}")
            gen = RandomsGeneratorV3(survey)
            nz_func = estimator.get_nz_func(survey, grupo, bin_z, which='survey')

            # Semilla determinista basada en string
            seed_val = 2026 + abs(hash(f"{survey}{grupo}{bin_z}")) % 1000

            gen.generate_and_save_chunked(
                n_data=n_data_real,
                n_z_func=nz_func,
                output_path=output_randoms,
                seed=seed_val
            )
            del gen, nz_func
            gc.collect()
        else:
            log.info(f"  [Fase 1] Catálogo randoms ya existe: {output_randoms.name} (Saltando generación)")

        # ---------------------------------------------------------------------
        # FASE 2: Cálculo del Mapa de Pesos FKP (FITS)
        # ---------------------------------------------------------------------
        output_weights = Path(f"weights_fkp/{survey.lower()}_{grupo.lower()}_{bin_z}_produccion_weights.fits")

        if not output_weights.exists():
            log.info(f"  [Fase 2] Calculando mapa de pesos FKP -> {output_weights.name}")
            weight_map = weight_calculator.calculate_weights(output_randoms)
            weight_calculator.save_weights(weight_map, output_weights)
            del weight_map
            gc.collect()
        else:
            log.info(f"  [Fase 2] Mapa de pesos ya existe: {output_weights.name} (Saltando cálculo)")

        # ---------------------------------------------------------------------
        # FASE 3: Análisis de Bispectro FKP con Núcleo Rust
        # ---------------------------------------------------------------------
        log.info(f"  [Fase 3] Ejecutando análisis de bispectro en Rust (l_max={l_max})")

        info = estimator.estimate_nbar(survey, grupo, bin_z)
        nbar_survey = info['nbar_survey']

        # =====================================================================
        # ⚠️ ADVERTENCIA CRÍTICA (V20): REEMPLAZAR MAPAS SINTÉTICOS POR REALES
        # =====================================================================
        # Actualmente se usan mapas sintéticos para prueba de integración end-to-end.
        # Para resultados científicos válidos a l_max=25, descomenta y adapta la
        # carga de tus mapas reales de datos del survey aquí.
        # Ejemplo:
        # mapa_datos = hp.read_map("ruta/a/tu/mapa_datos.fits", verbose=False).astype(np.float32)
        # =====================================================================
        NSIDE = 64
        NPIX = hp.nside2npix(NSIDE)
        mapa_datos = np.random.normal(0, 1e-4, NPIX).astype(np.float32)
        mapa_randoms = np.random.normal(0, 1.1e-4, NPIX).astype(np.float32)

        peso_mapa = hp.read_map(str(output_weights), verbose=False)
        mapa_datos_ponderado = mapa_datos * peso_mapa
        mapa_randoms_ponderado = mapa_randoms * peso_mapa

        # Aumentar lmax en map2alm para capturar los modos hasta l_max=25
        alm_datos_hp = hp.map2alm(mapa_datos_ponderado, lmax=l_max, use_pixel_weights=True)
        alm_randoms_hp = hp.map2alm(mapa_randoms_ponderado, lmax=l_max, use_pixel_weights=True)

        alm_datos = expand_alm_healpy(alm_datos_hp, l_max)
        alm_randoms = expand_alm_healpy(alm_randoms_hp, l_max)

        modos_datos_re = np.real(alm_datos).astype(np.float32).tolist()
        modos_datos_im = np.imag(alm_datos).astype(np.float32).tolist()
        modos_randoms_re = np.real(alm_randoms).astype(np.float32).tolist()
        modos_randoms_im = np.imag(alm_randoms).astype(np.float32).tolist()

        factor_norm = calcular_factor_normalizacion_I123(output_weights, nbar_survey)

        # NOTA: Si la lista de configs es muy grande (>500), considera pasarla por chunks
        # al kernel Rust o asegurarte de que la memoria sea suficiente.
        resultados_rust = cv.calcular_bispectro_fkp(
            modos_datos_re,
            modos_datos_im,
            modos_randoms_re,
            modos_randoms_im,
            l_max,
            configs,
            float(factor_norm),
            float(nbar_survey),
        )

        resultados_globales[(survey, grupo, bin_z)] = resultados_rust
        log.info(f"  ✅ Bin completado exitosamente.")

        # Limpieza intensiva de RAM para Termux
        gc.collect()

    log.info("\n" + "=" * 80)
    log.info("🎉 ¡PROPIEDAD CUMPLIDA: 12 BINES PROCESADOS EN RANDOMS, WEIGHTS Y BISPECTRO!")
    log.info("=" * 80)
    return resultados_globales


if __name__ == "__main__":
    # Se actualiza el valor por defecto a 25 para la iteración V20
    ejecutar_pipeline_completo(l_max=25)