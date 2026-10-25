#!/usr/bin/env python3
"""Reproduce the fixed-time three-protocol synthesis from executed campaign data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

CASES=[('pulse_b1f2b1393d0b0ff1','Constant'),
       ('pulse_6f787216b4e21a6d','Raised\ncosine'),
       ('pulse_b270049fcd119450','Gaussian')]


def main(campaign,stem):
    import matplotlib.pyplot as plt
    import numpy as np
    from src.plotting import panel
    records=[]
    for identifier,label in CASES:
        path=campaign/'jobs'/identifier/'summary.json'
        result=json.loads(path.read_text())
        if result.get('execution_status')!='completed':
            raise ValueError('Cannot plot an incomplete case: '+identifier)
        m=result['metrics']
        if (m['Na'],m['Nb'])!=(32,12) or m['duration']!=4 or m['idle']!=2 or m['ratio']!=.5:
            raise ValueError('The compared cases must share cutoffs, pulse length, recovery and peak drive')
        records.append((identifier,label,m,hashlib.sha256(path.read_bytes()).hexdigest()))
    physics=('alpha','g2','control_g2','kappa_a','kappa_b','phase','order','efficiency','drive_scale')
    if any(any(m[k]!=records[0][2][k] for k in physics) for _,_,m,_ in records):
        raise ValueError('The compared cases do not share physical assumptions')
    metrics=[np.array([m['snr_squared_at_pulse_end'] for _,_,m,_ in records]),
             100*np.array([max(m['final_wrong_population']) for _,_,m,_ in records]),
             np.array([max(m['buffer_population_at_pulse_end']) for _,_,m,_ in records])]
    fig,axes=plt.subplots(1,3,figsize=(9.5,3.25),layout='constrained')
    colors=['#0072B2','#D55E00','#009E73']
    for ax,values in zip(axes,metrics):
        for index,(value,color) in enumerate(zip(values,colors)):
            ax.scatter(index,value,s=39,color=color,zorder=3)
            text=f'{value:.3g}' if ax is axes[2] else f'{value:.4g}'
            ax.annotate(text,(index,value),xytext=(0,8),textcoords='offset points',
                         ha='center',va='bottom',fontsize=8)
        ax.set(xticks=range(3),xticklabels=[row[1] for row in records],xlim=(-.45,2.45))
        ax.grid(axis='y')
    axes[0].set_ylabel(r'Shot-noise reference $\mathrm{SNR}^2$')
    axes[0].set_ylim(0,18)
    panel(axes[0],'a','Signal collected by 4 µs')
    axes[1].set_ylabel('Wrong logical population (%)')
    axes[1].set_ylim(0,.225)
    panel(axes[1],'b','After 2 µs of recovery')
    axes[2].set(yscale='log',ylim=(4e-5,.085),ylabel='Mean buffer photon number')
    panel(axes[2],'c','Buffer left at pulse end')
    fig.suptitle(r'Fixed pulse length and peak drive: $T=4$ µs, $\epsilon_{\rm peak}=0.5g_2$',fontsize=11)
    stem.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(stem.with_suffix('.png'),dpi=300)
    fig.savefig(stem.with_suffix('.pdf'))
    plt.close(fig)
    evidence={'cases':[{'job_id':identifier,'label':label.replace('\n',' '),
        'summary_sha256':digest,'information':m['information_at_pulse_end'],
        'snr_squared':m['snr_squared_at_pulse_end'],
        'max_recovered_wrong_population':max(m['final_wrong_population']),
        'max_buffer_population_at_turnoff':max(m['buffer_population_at_pulse_end'])}
        for identifier,label,m,digest in records],
        'interpretation':'Same duration and peak-drive tradeoff, not a matched-SNR superiority claim',
        'measurement_convention':'SNR_squared=4I for a unit-vacuum-noise conditional-mean reference; no measured single-shot fidelity'}
    print(json.dumps(evidence,indent=2,allow_nan=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,default=ROOT/'results/task_2_4_campaign')
    parser.add_argument('--output-stem',type=Path,default=ROOT/'figures/task_2_4_campaign_synthesis')
    args=parser.parse_args()
    main(args.campaign,args.output_stem)
