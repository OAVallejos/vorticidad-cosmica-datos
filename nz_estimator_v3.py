"""
nz_estimator_v3.py
================
Estimator of n̄(z) from EDA_VDISP.json + ΛCDM cosmology.
V3:
  • Smooth transition at the edges (Edge Tapering) to avoid Fourier /
    spherical-harmonic artifacts (ringing) in high-mass bins.
  • Improved robustness against extreme or null n̄ densities.
  • Fully compatible with randoms_generator_v3.py and NumPy 1.x/2.x.

Distinguishes TWO densities:
  n̄_VDISP(z)  : density of the subsample with measured VDISP.
  n̄_survey(z) : density of the full survey in that bin, = n̄_VDISP(z) / C_VDISP(z)

Units: n̄ in h³/Mpc³, distances in Mpc/h.
"""
import numpy as np
import json
from scipy.interpolate import interp1d
from scipy.integrate import quad
import logging

log = logging.getLogger(__name__)

# NumPy 2.0+ compatibility
if hasattr(np, 'trapezoid'):
    np_trapz = np.trapezoid
else:
    np_trapz = np.trapz  # type: ignore


# =============================================================================
# ΛCDM COSMOLOGY (Planck 2018)
# =============================================================================
class Cosmology:
    def __init__(self, H0=67.66, Om=0.31, Ob=0.049, Or=0.0):
        self.H0 = H0
        self.h = H0 / 100.0
        self.Om = Om
        self.Ob = Ob
        self.Or = Or
        self.Ol = 1.0 - Om - Or
        self.c = 299792.458            # km/s
        self.DH = self.c / self.H0     # Mpc

    def E(self, z):
        return np.sqrt(self.Or*(1+z)**4 + self.Om*(1+z)**3 + self.Ol)

    def inv_E(self, z):
        return 1.0 / self.E(z)

    def chi(self, z):
        integral, _ = quad(self.inv_E, 0, z, limit=200)
        return self.DH * integral / self.h   # Mpc/h

    def dV_c_dOmega_dz(self, z):
        return self.DH * self.inv_E(z) * (self.chi(z))**2   # (Mpc/h)³/sr

    def V_c_bin(self, z_min, z_max, n_points=200):
        z_grid = np.linspace(z_min, z_max, n_points)
        dV = np.array([self.dV_c_dOmega_dz(z) for z in z_grid])
        return np_trapz(dV, z_grid)                       # (Mpc/h)³/sr


# =============================================================================
# EFFECTIVE SPECTROSCOPIC AREAS (sr)
# =============================================================================
AREAS_SR = {
    'SDSS': 9376.0 * (np.pi/180.0)**2,    # deg² → sr
    'DESI': 14000.0 * (np.pi/180.0)**2,
}


# =============================================================================
# COMPLETENESS FACTOR C_VDISP = N_VDISP / N_survey
# =============================================================================
COMPLETENESS = {
    # SDSS
    ('SDSS', 'BAJA_MASA',  'z01_02'): 0.60,
    ('SDSS', 'MEDIA_MASA', 'z01_02'): 0.29,
    ('SDSS', 'ALTA_MASA',  'z01_02'): 0.20,
    ('SDSS', 'BAJA_MASA',  'z07_08'): 0.15,
    ('SDSS', 'MEDIA_MASA', 'z07_08'): 0.10,
    ('SDSS', 'ALTA_MASA',  'z07_08'): 0.09,

    # DESI
    ('DESI', 'BAJA_MASA',  'z04_06'): 0.013,
    ('DESI', 'MEDIA_MASA', 'z04_06'): 0.019,
    ('DESI', 'ALTA_MASA',  'z04_06'): 0.043,
    ('DESI', 'BAJA_MASA',  'z08_10'): 0.010,
    ('DESI', 'MEDIA_MASA', 'z08_10'): 0.015,
    ('DESI', 'ALTA_MASA',  'z08_10'): 0.035,
}


# =============================================================================
# V3 ESTIMATOR
# =============================================================================
class N_zEstimator:
    """
    Estimates n̄_VDISP(z) and n̄_survey(z) with edge-smoothed profiles.
    """

    def __init__(self, eda_path: str = "EDA_VDISP.json"):
        with open(eda_path, 'r') as f:
            self.eda = json.load(f)
        self.cosmo = Cosmology()
        self._cache = {}

    def estimate_nbar(self, survey: str, grupo: str, bin_z: str) -> dict:
        key = (survey, grupo, bin_z)
        if key in self._cache:
            return self._cache[key]

        survey_data = self.eda[survey]
        meta  = survey_data[f"{grupo}__{bin_z}"]
        stats = meta["stats"]

        N_vdisp = stats["N"]
        z_min   = meta["z_min"]
        z_max   = meta["z_max"]
        Omega   = AREAS_SR[survey]

        V_c = self.cosmo.V_c_bin(z_min, z_max)         # (Mpc/h)³/sr
        nbar_vdisp = N_vdisp / (V_c * Omega)           # h³/Mpc³

        C = COMPLETENESS.get(key, np.nan)
        if np.isnan(C) or C <= 0:
            log.warning(f"⚠️ C_VDISP not defined for {key}; nbar_survey = NaN")
            nbar_survey = np.nan
        else:
            nbar_survey = nbar_vdisp / C

        # Grid extended slightly to allow edge smoothing
        z_grid = np.linspace(z_min, z_max, 100)

        # V3 IMPROVEMENT: Smooth transition window (cosine tapering) at the ends
        # to avoid abrupt step-like cuts that ruin spherical harmonics.
        delta_z = z_max - z_min
        taper = np.ones_like(z_grid)
        edge_fraction = 0.15  # 15% of the edges with smooth transition
        mask_low = z_grid < (z_min + edge_fraction * delta_z)
        mask_high = z_grid > (z_max - edge_fraction * delta_z)

        if np.any(mask_low):
            z_transition = (z_grid[mask_low] - z_min) / (edge_fraction * delta_z)
            taper[mask_low] = 0.5 * (1.0 - np.cos(np.pi * z_transition))
        if np.any(mask_high):
            z_transition = (z_max - z_grid[mask_high]) / (edge_fraction * delta_z)
            taper[mask_high] = 0.5 * (1.0 - np.cos(np.pi * z_transition))

        nz_vdisp_profile = nbar_vdisp * taper
        nz_survey_profile = nbar_survey * taper if not np.isnan(nbar_survey) else np.full_like(z_grid, np.nan)

        result = {
            'nbar_vdisp':     float(nbar_vdisp),
            'nbar_survey':    float(nbar_survey) if not np.isnan(nbar_survey) else np.nan,
            'C_vdisp':        float(C) if not np.isnan(C) else np.nan,
            'N_vdisp':        N_vdisp,
            'V_c':            float(V_c),
            'Omega':          float(Omega),
            'z_min':          z_min,
            'z_max':          z_max,
            'z_grid':         z_grid,
            'nz_vdisp_grid':  nz_vdisp_profile,
            'nz_survey_grid': nz_survey_profile,
        }

        self._cache[key] = result
        return result

    def get_nz_func(self, survey, grupo, bin_z,
                    which: str = 'vdisp',
                    extrapolate_zero: bool = True) -> callable:
        """
        Returns the interpolated and smoothed n(z) function.
        which = 'vdisp'  → density of the VDISP subsample
        which = 'survey' → density of the full survey (corrected by C)
        """
        if which not in ('vdisp', 'survey'):
            raise ValueError("which must be 'vdisp' or 'survey'")

        info = self.estimate_nbar(survey, grupo, bin_z)
        y = info['nz_vdisp_grid'] if which == 'vdisp' else info['nz_survey_grid']

        if np.isnan(y).all():
            fill = 0.0
        else:
            fill = 0.0 if extrapolate_zero else float(np.nanmean(y))

        itp = interp1d(info['z_grid'], y, kind='linear',
                       bounds_error=False, fill_value=fill)

        def n_z(z):
            return np.maximum(itp(z), 0.0)
        return n_z


# =============================================================================
# VALIDATION AND TEST
# =============================================================================
def validate():
    est = N_zEstimator()
    lit = {
        ('SDSS', 'BAJA_MASA',  'z01_02'): 3.0e-4,
        ('SDSS', 'MEDIA_MASA', 'z01_02'): 3.0e-4,
        ('SDSS', 'ALTA_MASA',  'z07_08'): 1.0e-4,
        ('DESI', 'BAJA_MASA',  'z04_06'): 5.0e-4,
        ('DESI', 'MEDIA_MASA', 'z04_06'): 4.0e-4,
        ('DESI', 'ALTA_MASA',  'z04_06'): 3.0e-4,
    }

    print("\n" + "="*92)
    print("V3 VALIDATION: n̄_VDISP vs n̄_survey (with smooth edge tapering)")
    print("="*92)
    print(f"{'Survey':<6} {'Group':<11} {'Bin':<7} "
          f"{'n̄_VDISP':>11} {'C':>7} {'n̄_survey':>11} {'Lit':>9} {'Ratio':>7}")
    print("-"*92)
    for key, lit_val in lit.items():
        survey, grupo, bin_z = key
        info = est.estimate_nbar(survey, grupo, bin_z)
        ratio = info['nbar_survey'] / lit_val if not np.isnan(info['nbar_survey']) else np.nan
        print(f"{survey:<6} {grupo:<11} {bin_z:<7} "
              f"{info['nbar_vdisp']:>11.3e} {info['C_vdisp']:>7.3f} "
              f"{info['nbar_survey']:>11.3e} {lit_val:>9.1e} {ratio:>7.2f}x")
    print("="*92)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    validate()