#!/usr/bin/env python3
"""Plot both complex weak-readout pointers from the delivered two-mode trajectories."""
from pathlib import Path
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.plotting import panel

def main():
    result=json.loads((ROOT/'results/task_2_4.json').read_text())
    cfg=result['configuration']
    with np.load(ROOT/'results/task_2_4_trajectories.npz',allow_pickle=False) as z:
        t=z['field_t'];e=z['baseline_field_expects'][0]
    row=result['tradeoff']['baseline_size'][0]
    assert row['ratio']==.05 and row['alpha']==2.1
    fig,axes=plt.subplots(1,2,figsize=(9,3.1),layout='constrained')
    colors=['#0072B2','#D55E00']
    for branch,(sign,color) in enumerate(zip([1,-1],colors)):
        label=fr'$s={sign:+d}$'
        axes[0].plot(t,e[branch,1].real,color=color,label=label)
        axes[0].axhline(-sign*.05/(2*2.1),color=color,ls='--',lw=.8)
        axes[1].plot(t,e[branch,1].imag,color=color,label=label,
                     ls='-' if sign==1 else '--')
    axes[1].axhline(cfg['kappa_a']/(4*cfg['g2']),color='black',ls=':',lw=1,label='Leading loss offset')
    for ax in axes:
        ax.set(xlabel='Time (µs)',xlim=(0,1.5));ax.grid();ax.legend(fontsize=8)
    axes[0].set_ylabel(r'$\mathrm{Re}\langle b\rangle$')
    axes[1].set_ylabel(r'$\mathrm{Im}\langle b\rangle$')
    panel(axes[0],'a','Opposite real pointers')
    panel(axes[1],'b','Common imaginary response')
    for ext in ['png','pdf']:
        fig.savefig(ROOT/f'figures/task_2_4_baseline.{ext}',dpi=300)
    plt.close(fig)
if __name__=='__main__':main()
