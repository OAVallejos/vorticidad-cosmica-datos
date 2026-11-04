#!/usr/bin/env python3        
"""
plot_evolucion_v20ac.py
V20 Cosmic Evolution Analysis: Q_high / Q_low and Parity Plots
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
plt.rcParams['axes.labelsize'] = 11
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

    # V20: Read filter parameters dynamically
    l_eff_max = data['filtro_config']['opcion_A']['l_eff_max']
    q_abs_max = data['filtro_config']['opcion_A']['q_abs_max']

    surveys = ['resultados_sdss', 'resultados_desi']
    survey_titles = ['SDSS', 'DESI']
    colors = {'Equilateral': '#d62728', 'Squeezed': '#1f77b4', 'Scalene': '#2ca02c'}
    markers = {'Equilateral': 'D', 'Squeezed': 's', 'Scalene': 'o'}

    # =========================================================================
    # FIGURE 1: EVOLUTION RATIO (Q_high / Q_low) vs l_eff
    # =========================================================================
    print("🎨 Generating Figure 1: Evolution Ratio...")
    fig1 = plt.figure(figsize=(14, 9))
    gs1 = gridspec.GridSpec(3, 2, figure=fig1, hspace=0.35, wspace=0.15)

    for col, (survey_key, survey_name) in enumerate(zip(surveys, survey_titles)):
        resultados = data[survey_key]
        mass_keys = list(resultados.keys())

        for row, mass_key in enumerate(mass_keys):
            if row >= 3:
                continue

            res = resultados[mass_key]
            Q_low = np.array(res['Q_low_array'])
            Q_high = np.array(res['Q_high_array'])

            valid_mask = aplicar_mascara_filtro(configs, Q_low, Q_high, l_eff_max, q_abs_max)
            # Crucial filter to avoid mathematical explosion when Q_low ≈ 0
            ratio_mask = valid_mask & (np.abs(Q_low) > 0.5)

            ax = fig1.add_subplot(gs1[row, col])

            for tipo in ['Equilateral', 'Squeezed', 'Scalene']:
                tipo_mask = np.array([clasificar_triangulo(*c) == tipo for c in configs])
                final_mask = ratio_mask & tipo_mask

                l_eff_valid = l_eff_array[final_mask]
                q_low_valid = Q_low[final_mask]
                q_high_valid = Q_high[final_mask]

                ratio = q_high_valid / q_low_valid
                label = f'{tipo}' if (row == 0 and col == 0) else None

                ax.scatter(l_eff_valid, ratio, color=colors[tipo], marker=markers[tipo],
                          s=45, alpha=0.8, label=label, edgecolors='white', linewidth=0.5, zorder=5)

            ax.axhline(1.0, color='black', linestyle='--', linewidth=1.5, alpha=0.7,
                      label='No Evolution (Q_h = Q_l)' if (row == 0 and col == 0) else None)
            ax.axhline(0.0, color='gray', linestyle=':', linewidth=1.0, alpha=0.5)

            # V20: Update X-axis limits
            ax.set_xlim(0, 26)
            ax.set_ylim(-2, 4)
            ax.set_title(f"{survey_name} - {mass_key.replace('_', ' ').title()}\n(N={ratio_mask.sum()} configs with |Q_low|>0.5)",
                        fontsize=11, fontweight='bold')

            if row == 2:
                ax.set_xlabel(r'$\ell_{\mathrm{eff}}$', fontsize=12)
            if col == 0:
                ax.set_ylabel(r'$Q_{\mathrm{high}} / Q_{\mathrm{low}}$', fontsize=12)

            if row == 0 and col == 0:
                ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

    fig1.suptitle(f'V20: Cosmic Evolution Ratio (L_MAX={data["L_MAX"]})',
                  fontsize=15, fontweight='bold', y=0.98)
    fig1.savefig('Evolucion_Ratio_V20_AC.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: Evolucion_Ratio_V20_AC.png")

    # =========================================================================
    # FIGURE 2: PARITY PLOT (Q_high vs Q_low)
    # =========================================================================
    print("🎨 Generating Figure 2: Parity Plot...")
    fig2 = plt.figure(figsize=(14, 9))
    gs2 = gridspec.GridSpec(3, 2, figure=fig2, hspace=0.35, wspace=0.15)

    for col, (survey_key, survey_name) in enumerate(zip(surveys, survey_titles)):
        resultados = data[survey_key]
        mass_keys = list(resultados.keys())

        for row, mass_key in enumerate(mass_keys):
            if row >= 3:
                continue

            res = resultados[mass_key]
            Q_low = np.array(res['Q_low_array'])
            Q_high = np.array(res['Q_high_array'])

            valid_mask = aplicar_mascara_filtro(configs, Q_low, Q_high, l_eff_max, q_abs_max)
            ax = fig2.add_subplot(gs2[row, col])

            for tipo in ['Equilateral', 'Squeezed', 'Scalene']:
                tipo_mask = np.array([clasificar_triangulo(*c) == tipo for c in configs])
                final_mask = valid_mask & tipo_mask

                q_low_valid = Q_low[final_mask]
                q_high_valid = Q_high[final_mask]

                label = f'{tipo}' if (row == 0 and col == 0) else None
                ax.scatter(q_low_valid, q_high_valid, color=colors[tipo], marker=markers[tipo],
                          s=45, alpha=0.8, label=label, edgecolors='white', linewidth=0.5, zorder=5)

            min_q = min(np.min(Q_low[valid_mask]), np.min(Q_high[valid_mask]))
            max_q = max(np.max(Q_low[valid_mask]), np.max(Q_high[valid_mask]))
            ax.plot([min_q, max_q], [min_q, max_q], 'k--', linewidth=1.5, alpha=0.7,
                   label='Q_high = Q_low' if (row == 0 and col == 0) else None)

            limit = max(abs(min_q), abs(max_q)) + 1
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            ax.set_aspect('equal', adjustable='box')

            ax.set_title(f"{survey_name} - {mass_key.replace('_', ' ').title()}\n(N={valid_mask.sum()} valid configs)",
                        fontsize=11, fontweight='bold')

            if row == 2:
                ax.set_xlabel(r'$Q_{\mathrm{low}}$ (low z)', fontsize=12)
            if col == 0:
                ax.set_ylabel(r'$Q_{\mathrm{high}}$ (high z)', fontsize=12)

            if row == 0 and col == 0:
                ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

    fig2.suptitle(f'V20: Parity Plot (Robust Evolution Detection)',
                  fontsize=15, fontweight='bold', y=0.98)
    fig2.savefig('Evolucion_Parity_V20_AC.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: Evolucion_Parity_V20_AC.png")
    print("\n🎉 V20 evolution analysis completed successfully!")

if __name__ == "__main__":
    main()