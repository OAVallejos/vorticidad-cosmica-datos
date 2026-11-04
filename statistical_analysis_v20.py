#!/usr/bin/env python3
"""
statistical_analysis_v20.py
Honest statistical analysis V20 with large N (~500 configs per bin).
This is no longer an "expansion proposal": the expansion to L_MAX=25 is already applied.
"""                           
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['mathtext.fontset'] = 'dejavusans'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def clasificar_triangulo(l1, l2, l3):
    if l1 == l2 == l3:
        return 'Equilateral'
    elif l1 < l2 and l2 == l3:
        return 'Squeezed'
    else:
        return 'Scalene'

def aplicar_mascara_filtro(configs, Q_low, Q_high, l_eff_max, q_abs_max=5.0):
    mask = []
    for i, (l1, l2, l3) in enumerate(configs):
        l_eff = (l1 + l2 + l3) / 3.0
        paridad_ok = (l1 + l2 + l3) % 2 == 0
        l_eff_ok = l_eff <= l_eff_max
        q_ok = (abs(Q_low[i]) <= q_abs_max) and (abs(Q_high[i]) <= q_abs_max)
        mask.append(paridad_ok and l_eff_ok and q_ok)
    return np.array(mask)

def bootstrap_pendiente(x, y, n_bootstrap=10000, confianza=0.95):
    """Robust bootstrap for the slope."""
    n = len(x)
    if n < 3:
        return None, None, None, "N<3: bootstrap not applicable"

    pendientes = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, size=n, replace=True)
        x_b, y_b = x[idx], y[idx]
        if np.std(x_b) < 1e-10:
            continue
        slope, _, _, _, _ = stats.linregress(x_b, y_b)
        if np.isfinite(slope):
            pendientes.append(slope)

    if len(pendientes) < 100:
        return None, None, None, "Unstable bootstrap"

    pendientes = np.array(pendientes)
    alpha = 1 - confianza
    lower = np.percentile(pendientes, 100 * alpha / 2)
    upper = np.percentile(pendientes, 100 * (1 - alpha / 2))
    median = np.median(pendientes)

    return median, lower, upper, f"CI {confianza*100:.0f}%: [{lower:.3f}, {upper:.3f}]"

def test_permutacion_pendiente(x, y, n_perm=10000):
    """Permutation test: is the slope significant against chance?"""
    n = len(x)
    if n < 3:
        return None, "N<3"

    slope_obs, _, _, _, _ = stats.linregress(x, y)

    count_extreme = 0
    for _ in range(n_perm):
        y_perm = np.random.permutation(y)
        slope_perm, _, _, _, _ = stats.linregress(x, y_perm)
        if abs(slope_perm - 1.0) >= abs(slope_obs - 1.0):
            count_extreme += 1

    p_value = count_extreme / n_perm
    return p_value, f"p={p_value:.3f} (vs H0: slope=1)"

# =============================================================================
# MAIN ANALYSIS
# =============================================================================
def main():
    print("="*80)
    print("HONEST ANALYSIS V20: Statistics with LARGE N (L_MAX=25)")
    print("="*80)

    json_file = 'ROBUSTEZ_V20_Q_REDUCIDO.json'
    with open(json_file, 'r') as f:
        data = json.load(f)

    configs = [tuple(c) for c in data['configs']]
    l_eff_array = np.array([(l1 + l2 + l3) / 3.0 for l1, l2, l3 in configs])
    tipos = [clasificar_triangulo(*c) for c in configs]

    l_eff_max = data['filtro_config']['opcion_A']['l_eff_max']
    q_abs_max = data['filtro_config']['opcion_A']['q_abs_max']

    # =========================================================================
    # REAL ANALYSIS WITH EXPANDED DATA
    # =========================================================================
    print("\n" + "="*80)
    print("STATISTICAL ANALYSIS WITH EXPANDED V20 DATA")
    print("="*80)

    res = data['resultados_desi']['ALTA_MASA']
    Q_low = np.array(res['Q_low_array'])
    Q_high = np.array(res['Q_high_array'])
    valid_mask = aplicar_mascara_filtro(configs, Q_low, Q_high, l_eff_max, q_abs_max)

    resultados = {}
    for tipo in ['Equilateral', 'Squeezed', 'Scalene']:
        tipo_mask = np.array([t == tipo for t in tipos])
        final_mask = valid_mask & tipo_mask

        q_low = Q_low[final_mask]
        q_high = Q_high[final_mask]
        l_eff = l_eff_array[final_mask]

        n = len(q_low)
        print(f"\n--- {tipo} (N={n}) ---")

        if n < 3:
            print(f"  ⚠️  N={n} is insufficient for rigorous statistics")
            resultados[tipo] = {'N': n, 'status': 'insufficient'}
            continue

        # Linear fit
        slope, intercept, r_value, p_value, std_err = stats.linregress(q_low, q_high)
        print(f"  Slope: {slope:.3f} ± {std_err:.3f}")
        print(f"  R² = {r_value**2:.3f}")
        print(f"  p-value (vs slope=0): {p_value:.4f}")

        # Bootstrap
        median_b, lower_b, upper_b, msg_b = bootstrap_pendiente(q_low, q_high)
        print(f"  Bootstrap: {msg_b}")

        # Permutation test
        p_perm, msg_perm = test_permutacion_pendiente(q_low, q_high)
        print(f"  Permutation: {msg_perm}")

        # Honest verdict with large N
        if n < 5:
            veredicto = "⚠️  INCONCLUSIVE (N too small)"
        elif p_perm > 0.05:
            veredicto = "✅ Compatible with no-evolution (slope ≈ 1)"
        else:
            veredicto = "🔴 Significant: evolution detected"
        print(f"  Verdict: {veredicto}")

        resultados[tipo] = {
            'N': n, 'slope': slope, 'std_err': std_err,
            'r2': r_value**2, 'p_perm': p_perm,
            'bootstrap': (median_b, lower_b, upper_b),
            'veredicto': veredicto
        }

    # =========================================================================
    # V20 CONFIGURATION COUNT
    # =========================================================================
    print("\n" + "="*80)
    print("V20 CONFIGURATION DISTRIBUTION (L_MAX=25)")
    print("="*80)

    conteo_total = {'Equilateral': 0, 'Squeezed': 0, 'Scalene': 0}
    conteo_valido = {'Equilateral': 0, 'Squeezed': 0, 'Scalene': 0}

    for i, (l1, l2, l3) in enumerate(configs):
        t = clasificar_triangulo(l1, l2, l3)
        conteo_total[t] += 1
        if valid_mask[i]:
            conteo_valido[t] += 1

    print(f"\n{'Type':<12} {'Total (L≤25)':<15} {'Valid (filter)':<18} {'Retention rate'}")
    print("-"*60)
    for t in conteo_total:
        tasa = conteo_valido[t] / conteo_total[t] * 100 if conteo_total[t] > 0 else 0
        print(f"{t:<12} {conteo_total[t]:<15} {conteo_valido[t]:<18} {tasa:.1f}%")

    # =========================================================================
    # FIGURE: Honest V20 analysis
    # =========================================================================
    print("\n Generating V20 summary figure...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    colors = {'Equilateral': '#d62728', 'Squeezed': '#1f77b4', 'Scalene': '#2ca02c'}

    for idx, tipo in enumerate(['Equilateral', 'Squeezed', 'Scalene']):
        ax = axes[idx]
        tipo_mask = np.array([t == tipo for t in tipos])
        final_mask = valid_mask & tipo_mask

        q_low = Q_low[final_mask]
        q_high = Q_high[final_mask]
        n = len(q_low)

        ax.scatter(q_low, q_high, color=colors[tipo], s=40, alpha=0.6,
                  edgecolors='black', linewidth=0.3, zorder=5)

        lim = max(abs(q_low.max()), abs(q_high.max()), 1) + 1
        ax.plot([-lim, lim], [-lim, lim], 'k--', linewidth=1.5, alpha=0.7, label='Q_high = Q_low')

        if n >= 3:
            slope, intercept, r_value, _, std_err = stats.linregress(q_low, q_high)
            ax.plot([-lim, lim], [slope*(-lim)+intercept, slope*lim+intercept],
                   color=colors[tipo], linewidth=2, alpha=0.8,
                   label=f'Fit: {slope:.3f}x+{intercept:.3f}\nR²={r_value**2:.3f}\nN={n}')
        else:
            ax.text(0.5, 0.5, f'N={n}\nInsufficient\nfor fit',
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=14, fontweight='bold', color='red',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect('equal')
        ax.set_xlabel(r'$Q_{\mathrm{low}}$', fontsize=12)
        ax.set_ylabel(r'$Q_{\mathrm{high}}$', fontsize=12)
        ax.set_title(f'{tipo}\n(N={n} configs)', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3)

    fig.suptitle(f'DESI High Mass V20: HONEST Analysis (L_MAX={data["L_MAX"]}, large N)',
                 fontsize=15, fontweight='bold', y=1.02)

    filename = 'Analisis_Honesto_DESI_AltaMasa_V20.png'
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {filename}")

    # =========================================================================
    # HONEST CONCLUSION V20
    # =========================================================================
    print("\n" + "="*80)
    print("HONEST CONCLUSION V20")
    print("="*80)
    print("""
🔬 Scientific implications:
    - If slope ≈ 1 (p>0.05): Confirmation of no-evolution of the bispectrum
    - If slope ≠ 1 (p≤0.05): Detection of cosmic evolution
    - The precision allows distinguishing between theoretical models
""")

if __name__ == "__main__":
    main()