#!/usr/bin/env python3
"""Plot the fixed-cat-size trade-off from the executed Task 2.4 sweep."""
from pathlib import Path
import json
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.plotting import panel


def main():
    results = json.loads((ROOT/'results/task_2_4.json').read_text())
    rows = results['tradeoff']['baseline_size']
    assert all(row['alpha'] == 2.1 for row in rows)
    drive = np.array([row['ratio'] for row in rows])
    contrast = [row['contrast_3_4us'] for row in rows]
    rates = [row['spectrum']['gamma_x_per_us'] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), layout='constrained')
    axes[0].plot(drive, contrast, 'o-', color='#0072B2', label='Full two-mode model')
    guide = np.r_[0, drive]
    axes[0].plot(guide, guide/2.1, '--', color='#555555', lw=1,
                 label='Weak-drive prediction')
    axes[0].set(ylabel=r'Real buffer-field separation $C_b$', ylim=(0, .51))
    axes[1].semilogy(drive, rates, 'o-', color='#0072B2')
    axes[1].axhline(results['storage_reference']['gamma_x_per_us'], color='#555555',
                    ls='--', lw=1, label='Undriven storage')
    axes[1].set(ylabel=r'Logical relaxation $\Gamma_X$ (µs$^{-1}$)', ylim=(1e-7, 2e-2))
    for ax in axes:
        ax.set(xlabel=r'Memory-drive strength $\epsilon_Z/g_2$', xlim=(0, 1.04))
        ax.grid()
        ax.legend(fontsize=8)
    panel(axes[0], 'a', 'A stronger drive increases contrast')
    panel(axes[1], 'b', 'It also increases the switching rate')
    for suffix in ['png', 'pdf']:
        fig.savefig(ROOT/f'figures/task_2_4_drive_tradeoff.{suffix}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
