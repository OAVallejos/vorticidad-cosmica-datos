#!/usr/bin/env python3
"""
triangle_analysis_v20.py
Analysis separated by triangle type (Equilateral, Squeezed, Scalene) V20.
L_MAX=25, ~860 total configurations, ~500 valid after filtering.
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

# =============================================================================
# CONFIGURATION
# =============================================================================
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['mathtext.fontset'] = 'dejavusans'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def classify_triangle(l1, l2, l3):
    if l1 == l2 == l3:
        return 'Equilateral'
    elif l1 < l2 and l2 == l3:
        return 'Squeezed'
    else:
        return 'Scalene'

def apply_filter_mask(configs, Q_low, Q_high, l_eff_max, q_abs_max=5.0):
    mask = []
    for i, (l1, l2, l3) in enumerate(configs):
        l_eff = (l1 + l2 + l3) / 3.0
        parity_ok = (l1 + l2 + l3) % 2 == 0
        l_eff_ok = l_eff <= l_eff_max
        q_ok = (abs(Q_low[i]) <= q_abs_max) and (abs(Q_high[i]) <= q_abs_max)
        mask.append(parity_ok and l_eff_ok and q_ok)
    return np.array(mask)

# =============================================================================
# MAIN ANALYSIS
# =============================================================================
def main():
    json_file = 'ROBUSTEZ_V20_Q_REDUCIDO.json'
    print(f"📥 Loading {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)

    configs = [tuple(c) for c in data['configs']]
    l_eff_array = np.array([(l1 + l2 + l3) / 3.0 for l1, l2, l3 in configs])

    # V20: Read filter parameters dynamically from JSON
    l_eff_max = data['filtro_config']['opcion_A']['l_eff_max']
    q_abs_max = data['filtro_config']['opcion_A']['q_abs_max']

    types = [classify_triangle(*c) for c in configs]

    print("\n" + "="*80)
    print(f"ANALYSIS BY TRIANGLE TYPE V20 - DESI HIGH MASS (L_MAX={data['L_MAX']})")
    print("="*80)

    # =========================================================================
    # FIGURE 1: EVOLUTION SEPARATED BY TYPE
    # =========================================================================
    print("\n🎨 Generating Figure 1: Evolution by triangle type...")
    fig1, axes1 = plt.subplots(1, 3, figsize=(18, 6))

    types_to_analyze = ['Equilateral', 'Squeezed', 'Scalene']
    colors = {'Equilateral': '#d62728', 'Squeezed': '#1f77b4', 'Scalene': '#2ca02c'}

    results_by_type = {}

    for idx, triangle_type in enumerate(types_to_analyze):
        ax = axes1[idx]

        # Keep JSON keys in Spanish to match the output file
        res = data['resultados_desi']['ALTA_MASA']
        Q_low = np.array(res['Q_low_array'])
        Q_high = np.array(res['Q_high_array'])

        valid_mask = apply_filter_mask(configs, Q_low, Q_high, l_eff_max, q_abs_max)
        type_mask = np.array([t == triangle_type for t in types])
        final_mask = valid_mask & type_mask

        l_eff_valid = l_eff_array[final_mask]
        q_low_valid = Q_low[final_mask]
        q_high_valid = Q_high[final_mask]

        ratio_mask = np.abs(q_low_valid) > 0.5
        l_eff_ratio = l_eff_valid[ratio_mask]
        ratio = q_high_valid[ratio_mask] / q_low_valid[ratio_mask]

        ax.scatter(l_eff_ratio, ratio,
                  color=colors[triangle_type], marker='o', s=60, alpha=0.7,
                  edgecolors='black', linewidth=0.5, zorder=5)

        ax.axhline(1.0, color='black', linestyle='--', linewidth=1.5, alpha=0.7, label='No evolution')
        ax.axhline(0.0, color='gray', linestyle=':', linewidth=1.0, alpha=0.5)

        if len(ratio) > 0:
            mean_ratio = np.mean(ratio)
            std_ratio = np.std(ratio)
            median_ratio = np.median(ratio)

            ax.axhline(mean_ratio, color=colors[triangle_type], linestyle='-', linewidth=1.0, alpha=0.5,
                      label=f'Mean: {mean_ratio:.2f}±{std_ratio:.2f}')

            results_by_type[triangle_type] = {
                'N': len(ratio),
                'mean': mean_ratio,
                'std': std_ratio,
                'median': median_ratio,
                'min': np.min(ratio),
                'max': np.max(ratio)
            }

        # V20: Update X-axis limits
        ax.set_xlim(0, 26)
        ax.set_ylim(-2, 4)
        ax.set_xlabel(r'$\ell_{\mathrm{eff}}$', fontsize=12)
        ax.set_ylabel(r'$Q_{\mathrm{high}} / Q_{\mathrm{low}}$', fontsize=12)
        ax.set_title(f'{triangle_type}\n(N={len(ratio)} configs)', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

    fig1.suptitle(f'DESI High Mass V20: Evolution by Triangle Type (L_MAX={data["L_MAX"]})',
                  fontsize=16, fontweight='bold', y=1.02)

    filename1 = 'DESI_HighMass_Evolution_By_Type_V20.png'
    fig1.savefig(filename1, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {filename1}")

    # =========================================================================
    # FIGURE 2: PARITY SEPARATED BY TYPE
    # =========================================================================
    print("\n🎨 Generating Figure 2: Parity by triangle type...")
    fig2, axes2 = plt.subplots(1, 3, figsize=(18, 6))

    for idx, triangle_type in enumerate(types_to_analyze):
        ax = axes2[idx]

        res = data['resultados_desi']['ALTA_MASA']
        Q_low = np.array(res['Q_low_array'])
        Q_high = np.array(res['Q_high_array'])

        valid_mask = apply_filter_mask(configs, Q_low, Q_high, l_eff_max, q_abs_max)
        type_mask = np.array([t == triangle_type for t in types])
        final_mask = valid_mask & type_mask

        q_low_valid = Q_low[final_mask]
        q_high_valid = Q_high[final_mask]

        ax.scatter(q_low_valid, q_high_valid,
                  color=colors[triangle_type], marker='o', s=60, alpha=0.7,
                  edgecolors='black', linewidth=0.5, zorder=5)

        min_q = min(np.min(q_low_valid), np.min(q_high_valid))
        max_q = max(np.max(q_low_valid), np.max(q_high_valid))
        ax.plot([min_q, max_q], [min_q, max_q], 'k--', linewidth=1.5, alpha=0.7, label='Q_high = Q_low')

        if len(q_low_valid) > 3:
            slope, intercept, r_value, p_value, std_err = stats.linregress(q_low_valid, q_high_valid)
            x_fit = np.array([min_q, max_q])
            y_fit = slope * x_fit + intercept
            ax.plot(x_fit, y_fit, color=colors[triangle_type], linewidth=2.0, alpha=0.8,
                   label=f'Fit: y={slope:.3f}x+{intercept:.3f}\nR²={r_value**2:.3f}')

        limit = max(abs(min_q), abs(max_q)) + 1
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel(r'$Q_{\mathrm{low}}$', fontsize=12)
        ax.set_ylabel(r'$Q_{\mathrm{high}}$', fontsize=12)
        ax.set_title(f'{triangle_type}\n(N={len(q_low_valid)} configs)', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

    fig2.suptitle(f'DESI High Mass V20: Parity by Triangle Type (L_MAX={data["L_MAX"]})',
                  fontsize=16, fontweight='bold', y=1.02)

    filename2 = 'DESI_HighMass_Parity_By_Type_V20.png'
    fig2.savefig(filename2, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {filename2}")

    # =========================================================================
    # STATISTICAL SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("STATISTICAL SUMMARY BY TRIANGLE TYPE (V20)")
    print("="*80)
    print(f"\n{'Type':<12} {'N':<6} {'Mean':<10} {'Std':<10} {'Median':<10} {'Min':<10} {'Max':<10}")
    print("-"*70)
    for triangle_type in types_to_analyze:
        if triangle_type in results_by_type:
            r = results_by_type[triangle_type]
            print(f"{triangle_type:<12} {r['N']:<6} {r['mean']:<10.3f} {r['std']:<10.3f} "
                  f"{r['median']:<10.3f} {r['min']:<10.3f} {r['max']:<10.3f}")

    print("\n" + "="*80)
    print("PHYSICAL INTERPRETATION")
    print("="*80)
    print("""
• Equilateral (l1=l2=l3): Sensitive to primordial non-Gaussianity
  - If mean ≈ 1: No evolution (consistent with standard inflation)
  - If mean ≠ 1: Possible signal of non-standard physics

• Squeezed (l1 << l2=l3): Sensitive to bias and structure evolution
  - Deviations from 1 indicate bias evolution with redshift
  - Expected: mean > 1 (structure growth)

• Scalene (l1≠l2≠l3): Sensitive to non-linear interactions
  - Greater dispersion expected
  - Information on mode couplings
""")

    print("\n🎉 Triangle type analysis V20 completed!")

if __name__ == "__main__":
    main()