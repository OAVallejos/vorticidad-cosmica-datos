#!/usr/bin/env python3
"""
plot_v20_ac.py
Generates publication-quality plots for the V20 results (L_MAX=25, Filter A + Jackknife C)
"""
import json                   
import numpy as np
import matplotlib             
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# =============================================================================
# STYLE CONFIGURATION
# =============================================================================
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans', 'sans-serif']
plt.rcParams['mathtext.fontset'] = 'dejavusans'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9

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

# =============================================================================
# MAIN FUNCTION
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

    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.15)

    surveys = ['resultados_sdss', 'resultados_desi']
    survey_titles = ['SDSS', 'DESI']
    mass_bins = ['BAJA_MASA', 'MEDIA_MASA', 'ALTA_MASA']
    mass_labels = ['Low Mass', 'Medium Mass', 'High Mass']

    colors = {'Equilateral': '#d62728', 'Squeezed': '#1f77b4', 'Scalene': '#2ca02c'}
    markers = {'Equilateral': 'D', 'Squeezed': 's', 'Scalene': 'o'}

    for col, (survey_key, survey_name) in enumerate(zip(surveys, survey_titles)):
        resultados = data[survey_key]

        plot_results = {}
        if survey_name == 'DESI':
            keys = list(resultados.keys())
            if len(keys) == 2 and 'MEDIA_MASA' in keys:
                plot_results['BAJA_MASA'] = resultados[keys[0]]
                plot_results['MEDIA_MASA'] = resultados[keys[1]]
                if 'ALTA_MASA' in resultados:
                    plot_results['ALTA_MASA'] = resultados['ALTA_MASA']
            else:
                plot_results = resultados
        else:
            plot_results = resultados

        for row, (mass_key, mass_label) in enumerate(zip(mass_bins, mass_labels)):
            if mass_key not in plot_results:
                continue

            res = plot_results[mass_key]
            Q_low = np.array(res['Q_low_array'])
            Q_high = np.array(res['Q_high_array'])

            valid_mask = aplicar_mascara_filtro(configs, Q_low, Q_high, l_eff_max, q_abs_max)
            ax = fig.add_subplot(gs[row, col])

            for tipo in ['Equilateral', 'Squeezed', 'Scalene']:
                tipo_mask = np.array([clasificar_triangulo(*c) == tipo for c in configs])
                final_mask = valid_mask & tipo_mask

                l_eff_valid = l_eff_array[final_mask]
                q_low_valid = Q_low[final_mask]
                q_high_valid = Q_high[final_mask]

                label_low = f'{tipo} (Low-z)' if (row == 0 and col == 0) else None
                label_high = f'{tipo} (High-z)' if (row == 0 and col == 0) else None

                ax.scatter(l_eff_valid, q_low_valid, color=colors[tipo], marker=markers[tipo],
                          s=50, alpha=0.6, label=label_low, edgecolors='white', linewidth=0.5, zorder=5)
                ax.scatter(l_eff_valid, q_high_valid, color=colors[tipo], marker=markers[tipo],
                          s=50, alpha=0.9, label=label_high, edgecolors='black', linewidth=0.5, zorder=5)

            ax.axhline(0, color='gray', linestyle='--', linewidth=1.2, alpha=0.7,
                      label='Q = 0 (Gaussian Field)' if (row == 0 and col == 0) else None)
            ax.axhline(q_abs_max, color='red', linestyle=':', linewidth=1, alpha=0.6,
                      label=f'Filter Threshold |Q|={q_abs_max}' if (row == 0 and col == 0) else None)
            ax.axhline(-q_abs_max, color='red', linestyle=':', linewidth=1, alpha=0.6)

            # V20: Update X-axis limits to cover up to l_eff ~ 25
            ax.set_xlim(0, 26)
            ax.set_ylim(-6, 6)
            ax.set_title(f"{survey_name} - {mass_label}\n(N={valid_mask.sum()} valid configs)",
                        fontsize=11, fontweight='bold')

            if row == 2:
                ax.set_xlabel(r'$\ell_{\mathrm{eff}} = (\ell_1 + \ell_2 + \ell_3)/3$', fontsize=12)
            if col == 0:
                ax.set_ylabel(r'$Q = B_{\mathrm{net}} / (C_{\ell}^{\mathrm{net}})^{1.5}$', fontsize=12)

            if row == 0 and col == 0:
                ax.legend(loc='upper right', fontsize=8, ncol=1, framealpha=0.9)

    fig.suptitle(f'V20: Reduced Q Statistic (L_MAX={data["L_MAX"]}, Valid Configurations after Filter)',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.savefig('Q_reducido_V20_AC_limpio.png', dpi=300, bbox_inches='tight')
    plt.savefig('Q_reducido_V20_AC_limpio.pdf', bbox_inches='tight')
    print("✅ Plots saved successfully:")
    print("   - Q_reducido_V20_AC_limpio.png")
    print("   - Q_reducido_V20_AC_limpio.pdf")

if __name__ == "__main__":
    main()