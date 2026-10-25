#!/usr/bin/env python3
"""Plot the executed mean-field prediction and its full quantum check."""
from pathlib import Path
import json
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.plotting import panel


def main():
    summary = json.loads((ROOT / 'results/task_2_4_final_summary.json').read_text())
    d = summary['integrated_findings']['depletion_model_failure']
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), layout='constrained')
    colors = ['#0072B2', '#D55E00', '#009E73']
    information = [d['classical_information'], d['quantum_information']]
    axes[0].bar(range(2), information, color=colors[:2], width=.48)
    for x, value in enumerate(information):
        axes[0].annotate(f'{value:.4f}', (x, value), xytext=(0, 7),
                         textcoords='offset points', ha='center', fontsize=9)
    axes[0].set(xticks=range(2), xticklabels=['Classical', 'Quantum'],
                ylim=(0, 1.8), ylabel=r'Collected information $\mathcal{I}$')
    photons = [d['classical_mean_field_photons'][0],
               d['quantum_coherent_photons'][0], d['quantum_total_photons'][0]]
    for x, (value, color) in enumerate(zip(photons, colors)):
        axes[1].scatter(x, value, color=color, s=42, zorder=3)
        axes[1].annotate(f'{value:.3g}', (x, value), xytext=(0, 8),
                         textcoords='offset points', ha='center', fontsize=9)
    axes[1].set(xticks=range(3),
        xticklabels=['Classical\n'+r'$|B|^2$', 'Quantum\n'+r'$|\langle b\rangle|^2$',
                     'Quantum\n'+r'$\langle n_b\rangle$'],
        xlim=(-.5, 2.5), yscale='log', ylim=(7e-6, 1.2e-2),
        ylabel='Buffer photons at pulse end')
    for ax in axes:
        ax.grid(axis='y')
        ax.set_axisbelow(True)
    panel(axes[0], 'a', 'Mean-signal prediction: 3.0% difference')
    panel(axes[1], 'b', 'Total energy: 35 times the prediction')
    fig.suptitle('Same 2-µs depletion candidate; full quantum check at 24 × 8', fontsize=11)
    for suffix in ['png', 'pdf']:
        fig.savefig(ROOT / f'figures/task_2_4_model_validation.{suffix}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
