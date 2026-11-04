#!/usr/bin/env python3        
"""
EDA_VDISP.py                  
Exploratory Data Analysis (EDA) of the VDISP field, by:
  - dataset (SDSS, DESI)
  - mass group (LOW, MEDIUM, HIGH)
  - redshift bin

Reports for each cell:
  N, mean, median, mode (KDE), std, IQR, MAD,
  Q1, Q5, Q25, Q50, Q75, Q95, Q99,
  min, max, skew, kurtosis,
  20-bin histogram.

No corrections. No factors. No significances.
Only descriptive statistics of the filtered raw data.

Usage:
    python3 EDA_VDISP.py

Output:
    - Console: table per cell.
    - JSON: EDA_VDISP.json
    - Histogram PNGs: EDA_VDISP_histograms.png (optional, if matplotlib available)
"""

import numpy as np
import json
import os
import sys
from datetime import datetime
from scipy import stats
from astropy.table import Table

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# =============================================================================
# CONFIGURATION
# =============================================================================

# Common filters (same as pipeline v5)
VDISP_MIN = 150.0
VDISP_MAX_PHYSICAL = 1000.0   # upper physical cut

# Mass groups per dataset (same as pipeline v5)
GROUPS_SDSS = {
    'LOW_MASS':    (150.0, 207.9),
    'MEDIUM_MASS': (207.9, 262.2),
    'HIGH_MASS':   (262.2, 1000.0),
}
GROUPS_DESI = {
    'LOW_MASS':    (150.0, 200.0),
    'MEDIUM_MASS': (200.0, 250.0),
    'HIGH_MASS':   (250.0, 1000.0),
}

# Redshift bins per dataset
BINS_SDSS = [
    ('z01_02', 0.1, 0.2),
    ('z07_08', 0.7, 0.8),
]
BINS_DESI = [
    ('z04_06', 0.4, 0.6),
    ('z08_10', 0.8, 1.0),
]

# Number of histogram bins
N_HIST_BINS = 20


# =============================================================================
# STATISTICS
# =============================================================================

def kde_mode(data, n_points=512):
    """
    Estimates the mode using KDE (kernel density estimation).
    Robust for multimodal or asymmetric distributions.
    """
    if len(data) < 10:
        return float(np.median(data)) if len(data) > 0 else 0.0
    try:
        kde = stats.gaussian_kde(data)
        x_grid = np.linspace(data.min(), data.max(), n_points)
        y_grid = kde(x_grid)
        return float(x_grid[np.argmax(y_grid)])
    except Exception:
        return float(np.median(data))


def compute_statistics(vdisp):
    """
    Returns a dictionary with all descriptive statistics.
    """
    n = len(vdisp)
    if n == 0:
        return None

    vdisp = np.asarray(vdisp, dtype=np.float64)

    mean = float(np.mean(vdisp))
    median = float(np.median(vdisp))
    mode = kde_mode(vdisp)
    std = float(np.std(vdisp, ddof=1)) if n > 1 else 0.0

    q1, q5, q25, q50, q75, q95, q99 = np.percentile(
        vdisp, [1, 5, 25, 50, 75, 95, 99]
    )
    iqr = float(q75 - q25)
    mad = float(np.median(np.abs(vdisp - median)))

    vmin = float(np.min(vdisp))
    vmax = float(np.max(vdisp))

    skew = float(stats.skew(vdisp)) if n > 2 else 0.0
    kurt = float(stats.kurtosis(vdisp)) if n > 3 else 0.0

    # Histogram
    hist_counts, hist_edges = np.histogram(vdisp, bins=N_HIST_BINS)
    hist_centers = 0.5 * (hist_edges[:-1] + hist_edges[1:])

    return {
        'N': int(n),
        'mean': mean,
        'median': median,
        'mode': mode,
        'std': std,
        'iqr': iqr,
        'mad': mad,
        'Q1': float(q1),
        'Q5': float(q5),
        'Q25': float(q25),
        'Q50': float(q50),
        'Q75': float(q75),
        'Q95': float(q95),
        'Q99': float(q99),
        'min': vmin,
        'max': vmax,
        'skew': skew,
        'kurtosis': kurt,
        'hist_counts': hist_counts.tolist(),
        'hist_centers': hist_centers.tolist(),
    }


# =============================================================================
# PRINTING
# =============================================================================

def print_statistics(dataset, group, bin_name, z_min, z_max, stats_dict):
    if stats_dict is None:
        print(f"\n{dataset} / {group} / {bin_name}")
        print("  No data.")
        return

    s = stats_dict
    print(f"\n{'='*70}")
    print(f"{dataset} / {group} / {bin_name}  (z={z_min}-{z_max})")
    print(f"{'='*70}")
    print(f"  N        = {s['N']:,}")
    print(f"  Mean     = {s['mean']:.2f} km/s")
    print(f"  Median   = {s['median']:.2f}")
    print(f"  Mode     = {s['mode']:.2f}  (KDE)")
    print(f"  Std      = {s['std']:.2f}")
    print(f"  IQR      = {s['iqr']:.2f}")
    print(f"  MAD      = {s['mad']:.2f}")
    print(f"  Q1  = {s['Q1']:.1f}  Q5  = {s['Q5']:.1f}  Q25 = {s['Q25']:.1f}")
    print(f"  Q50 = {s['Q50']:.1f}  Q75 = {s['Q75']:.1f}  Q95 = {s['Q95']:.1f}  Q99 = {s['Q99']:.1f}")
    print(f"  Min = {s['min']:.1f}  Max = {s['max']:.1f}")
    print(f"  Skew     = {s['skew']:+.3f}")
    print(f"  Kurtosis = {s['kurtosis']:+.3f}")

    # ASCII histogram
    print(f"  Histogram ({N_HIST_BINS} bins):")
    max_count = max(s['hist_counts']) if s['hist_counts'] else 1
    bar_max = 40
    for c, center in zip(s['hist_counts'], s['hist_centers']):
        n_bar = int(round(bar_max * c / max_count)) if max_count > 0 else 0
        bar = '#' * n_bar
        print(f"    {center:7.1f} | {bar} {c}")


# =============================================================================
# PROCESSING
# =============================================================================

def process_dataset(name, vdisp, z, groups, bins):
    results = {}

    for bin_name, z_min, z_max in bins:
        for group_name, (vmin, vmax) in groups.items():
            mask = (
                (z >= z_min) & (z < z_max) &
                (vdisp >= vmin) & (vdisp < vmax) &
                (vdisp >= VDISP_MIN) &
                (vdisp <= VDISP_MAX_PHYSICAL)
            )
            vdisp_bin = vdisp[mask]
            stats_dict = compute_statistics(vdisp_bin)
            key = f"{group_name}__{bin_name}"
            results[key] = {
                'dataset': name,
                'group': group_name,
                'bin': bin_name,
                'z_min': z_min,
                'z_max': z_max,
                'vdisp_min': vmin,
                'vdisp_max': vmax,
                'stats': stats_dict,
            }
            print_statistics(name, group_name, bin_name, z_min, z_max, stats_dict)

    return results


# =============================================================================
# PLOT (optional)
# =============================================================================

def generate_histograms(results, filename='EDA_VDISP_histograms.png'):
    if not HAS_MPL:
        print("\nmatplotlib not available. Skipping plot.")
        return

    cells = [k for k, v in results.items() if v['stats'] is not None]
    n = len(cells)
    if n == 0:
        return

    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.5 * nrows))
    axes = np.array(axes).flatten()

    for ax, key in zip(axes, cells):
        v = results[key]
        s = v['stats']
        ax.bar(s['hist_centers'], s['hist_counts'],
               width=(s['hist_centers'][1] - s['hist_centers'][0]) if len(s['hist_centers']) > 1 else 1,
               color='steelblue', alpha=0.7, edgecolor='black')
        ax.axvline(s['mean'], color='red', linestyle='--', label=f"mean={s['mean']:.1f}")
        ax.axvline(s['median'], color='green', linestyle='--', label=f"med={s['median']:.1f}")
        ax.axvline(s['mode'], color='orange', linestyle=':', label=f"mode={s['mode']:.1f}")
        ax.set_title(f"{v['dataset']} {v['group']} {v['bin']}\nN={s['N']:,}", fontsize=9)
        ax.set_xlabel('VDISP [km/s]', fontsize=8)
        ax.set_ylabel('Count', fontsize=8)
        ax.legend(fontsize=7)

    for ax in axes[n:]:
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(filename, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"\nHistograms saved to {filename}")


# =============================================================================
# LOADING
# =============================================================================

def load_sdss():
    filename = 'data/sdss_vdisp_calidad.npz'
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found.")
        return None, None
    d = np.load(filename)
    vdisp = d['VDISP'].astype(np.float64)
    z = d['Z'].astype(np.float64)
    print(f"SDSS loaded: {len(vdisp):,} galaxies")
    return vdisp, z


def load_desi():
    filename = 'data/DATASET_LRG_VDISP_FLUXR_FINAL.fits'
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found.")
        return None, None
    t = Table.read(filename)
    vdisp = np.array(t['VDISP'], dtype=np.float64)
    z = np.array(t['Z'], dtype=np.float64)
    print(f"DESI loaded: {len(vdisp):,} galaxies")
    return vdisp, z


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("EDA of VDISP by (dataset, group, redshift bin)")
    print(f"Common filter: {VDISP_MIN} <= VDISP <= {VDISP_MAX_PHYSICAL}")
    print("=" * 70)

    total_results = {
        'metadata': {
            'date': datetime.now().isoformat(),
            'vdisp_min': VDISP_MIN,
            'vdisp_max': VDISP_MAX_PHYSICAL,
            'n_hist_bins': N_HIST_BINS,
            'description': 'Descriptive statistics of VDISP by dataset/group/bin',
        }
    }

    vdisp_sdss, z_sdss = load_sdss()
    if vdisp_sdss is not None:
        total_results['SDSS'] = process_dataset(
            "SDSS", vdisp_sdss, z_sdss, GROUPS_SDSS, BINS_SDSS
        )

    vdisp_desi, z_desi = load_desi()
    if vdisp_desi is not None:
        total_results['DESI'] = process_dataset(
            "DESI", vdisp_desi, z_desi, GROUPS_DESI, BINS_DESI
        )

    # JSON
    with open('EDA_VDISP.json', 'w') as f:
        json.dump(total_results, f, indent=2)
    print(f"\nResults saved to EDA_VDISP.json")

    # Plot
    all_cells = {}
    for ds in ['SDSS', 'DESI']:
        if ds in total_results:
            all_cells.update(total_results[ds])
    generate_histograms(all_cells, 'EDA_VDISP_histograms.png')

    print("\nEDA completed.")


if __name__ == "__main__":
    main()