#!/usr/bin/env python3
"""Show the selected controls and counted signal from saved cycle results."""
from pathlib import Path
import json
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.plotting import panel


def main():
    result = json.loads((ROOT/'results/task_2_4.json').read_text())
    with np.load(ROOT/'results/task_2_4_trajectories.npz', allow_pickle=False) as z:
        traces = {name: (z[name+'_t'], z[name+'_information'])
                  for name in ['baseline', 'amplified']}
    p = result['cycles']['amplified']['parameters']
    t = traces['amplified'][0]
    def smooth(u):
        u = np.clip(u, 0, 1)
        return u**3 * (10 - 15*u + 6*u*u)
    alpha = p['alpha_storage'] + (p['alpha_readout']-p['alpha_storage']) * (
        smooth(t/p['ramp']) - smooth((t-p['ramp']-p['read_time'])/p['ramp']))
    drive = np.where((t >= p['ramp']) & (t < p['ramp']+p['read_time']), p['ratio'], 0.)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.1), layout='constrained')
    axes[0].plot(t, alpha, color='#333333', label='Target cat amplitude')
    axes[0].set(xlim=(0, t[-1]), ylim=(2.05, 2.67),
                xlabel='Cycle time (µs)', ylabel=r'Target amplitude $\alpha(t)$')
    drive_axis = axes[0].twinx()
    drive_axis.step(t, drive, where='post', color='#D55E00')
    drive_axis.set(ylim=(-.01, .13), ylabel=r'Readout drive $\epsilon_Z/g_2$')
    drive_axis.tick_params(axis='y', colors='#D55E00')
    drive_axis.yaxis.label.set_color('#D55E00')
    for name, label, color in [('baseline', 'Weak reference', '#0072B2'),
                                ('amplified', 'Enlargement cycle', '#D55E00')]:
        time, info = traces[name]
        m = result['cycles'][name]['metrics']
        mask = time <= m['read_end_us'] + 1e-10
        assert np.isclose(time[mask][-1], m['read_end_us'])
        final = info[mask][-1]
        assert np.isclose(final, m['mean_field_information_at_read_end'])
        axes[1].plot(time[mask], info[mask], color=color, label=label)
        axes[1].plot([time[mask][-1], time[-1]], [final, final], '--', color=color)
        axes[1].scatter(time[-1], final, color=color, s=22, zorder=3)
        axes[1].annotate(f'{time[-1]:.2f} µs', (time[-1], final),
                          xytext=(-3, 9), textcoords='offset points', ha='right', fontsize=8)
    axes[1].set(xlim=(0, 116), ylim=(0, 1.18), xlabel='Cycle time (µs)',
                ylabel=r'Counted information $\mathcal{I}$')
    axes[1].legend(loc='lower right', fontsize=8)
    for ax in axes:
        ax.grid()
    panel(axes[0], 'a', 'Enlarge, read, restore')
    panel(axes[1], 'b', 'Same signal target; complete-cycle time')
    for suffix in ['png', 'pdf']:
        fig.savefig(ROOT/f'figures/task_2_4_protocol_summary.{suffix}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    main()
