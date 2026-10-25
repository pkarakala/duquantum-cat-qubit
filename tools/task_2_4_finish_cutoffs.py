#!/usr/bin/env python3
"""Supplement timed-out QuTiP joint cutoffs using the validated Dynamiqs backend.

This combines a cutoff increase with an integrator change. It is not a new
same-cutoff solver certificate, and it never replaces original timeout records.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from tools.task_2_4_independent_check import (atomic_json, jax_envelope,
                                             verify_frozen_sources)


def finish_cutoff(output, reference_id, Na, Nb):
    verify_frozen_sources(output)
    manifest=json.loads((output/'manifest.json').read_text())
    job=next(j for j in manifest['jobs'] if j['id']==reference_id)
    reference_folder=output/'jobs'/reference_id
    reference=json.loads((reference_folder/'summary.json').read_text())
    if reference.get('execution_status')!='completed' or reference.get('job')!=job:
        raise ValueError('Reference is not a completed matching campaign case')
    p=reference['metrics']
    if (p['Na'],p['Nb'])!=(32,12) or (Na,Nb)!=(40,14):
        raise ValueError('This supplement requires a 32x12 reference and 40x14 target')
    if p['order']!='cubic' or p['phase']!=0.:
        raise ValueError('Supplement restricted to real-drive cubic finalists')
    import inspect
    import dynamiqs as dq
    import jax
    import jax.numpy as jnp
    import numpy as np
    import scipy
    from src.circuit import rotating_model, buffer_drive
    from src.readout_pulses import pulse_envelope
    from tasks.task_2_4 import observables, sparse_qarray
    dq.set_precision('double')
    dq.set_progress_meter(False)
    with np.load(reference_folder/'trajectories.npz') as data:
        t,expected=data['t'],data['expects']
    if expected.shape!=(2,10,len(t)) or not np.isfinite(t).all() or np.any(np.diff(t)<=0):
        raise ValueError('Invalid reference grid or observables')
    boundaries=np.asarray(p['stage_boundaries_us'])
    if any(np.min(abs(t-point))>1e-12 for point in boundaries):
        raise ValueError('Reference grid omits a stage boundary')
    profile_args=(p['duration'],p['profile'],p['edge_fraction'],p['hold_ratio'],
                  p['tail_ratio'],p['knots'])
    def envelope(time_value):
        return jax_envelope(time_value,*profile_args,jnp)
    delta=1e-10*max(1.,p['duration'])
    probe=np.unique(np.r_[t,np.linspace(0.,t[-1],4001),boundaries,
                          boundaries-delta,boundaries+delta])
    profile_error=float(np.max(abs(np.asarray(envelope(jnp.asarray(probe)))
                                   -pulse_envelope(probe,*profile_args))))
    if profile_error>1e-13:
        raise RuntimeError('Traceable waveform differs from reference pulse')
    a,b,ops=observables(Na,Nb,p['alpha'])
    H,_=rotating_model(Na,Nb,p['alpha'],p['g2'],0.,p['order'])
    H=sparse_qarray(H,Na,Nb)
    H+=(buffer_drive(p['alpha'],p['g2'],p['order'])
        -buffer_drive(p['alpha'],p['control_g2'],p['order']))*(b+b.dag())
    epsilon=p['ratio']*p['control_g2']*p['drive_scale']
    H+=dq.modulated(lambda time_value:epsilon*envelope(time_value),a+a.dag(),
                     discontinuity_ts=jnp.asarray(boundaries))
    jumps=[np.sqrt(p['kappa_b'])*b]
    if p['kappa_a']:
        jumps.append(np.sqrt(p['kappa_a'])*a)
    initial=[dq.tensor(dq.coherent(Na,sign*p['alpha']),dq.fock(Nb,0)) for sign in (1,-1)]
    started=time.monotonic()
    result=dq.mesolve(H,jumps,initial,jnp.asarray(t),exp_ops=ops,save_states=False,
                       method=dq.method.Tsit5(rtol=1e-10,atol=1e-12,max_steps=5000000))
    actual=np.asarray(result.expects)
    final=np.asarray(result.states.to_jax())[...,-1,:,:]
    errors=np.max(abs(actual-expected),axis=(0,2))
    physical_indices=[0,1,2,3,6,7,8,9]
    # Boundary projectors refer to different Fock levels and are not errors.
    names=p['observable_order']
    physical_errors={names[i]:float(errors[i]) for i in physical_indices}
    scale=p['ratio']/(2*p['alpha'])
    if scale<=0:
        raise ValueError('A nonzero nominal readout field is required for the convergence scale')
    buffer_error_fraction=float(errors[1]/scale)
    wrong_difference=float(np.max(abs(actual[:,6:8]-expected[:,6:8])))
    leakage_difference=float(np.max(abs(actual[:,8]-expected[:,8])))
    health={'max_trace_error':float(np.max(abs(actual[:,9]-1.))),
            'final_min_eigenvalue':float(np.linalg.eigvalsh(final).min()),
            'final_hermiticity_error':float(np.max(abs(final-final.conj().swapaxes(-1,-2))))}
    thresholds={'buffer_field_fraction':1e-3,'wrong_population_absolute':1e-6,
                'leakage_absolute':1e-6,'trace_absolute':1e-9,
                'final_eigenvalue_floor':-1e-7,'hermiticity_absolute':1e-10,
                'target_boundary_population':1e-3,'waveform_absolute':1e-13}
    checks={'buffer_field_converged':buffer_error_fraction<thresholds['buffer_field_fraction'],
            'wrong_population_converged':wrong_difference<thresholds['wrong_population_absolute'],
            'leakage_converged':leakage_difference<thresholds['leakage_absolute'],
            'trace_preserved':health['max_trace_error']<thresholds['trace_absolute'],
            'final_state_numerically_positive':health['final_min_eigenvalue']>thresholds['final_eigenvalue_floor'],
            'final_state_hermitian':health['final_hermiticity_error']<thresholds['hermiticity_absolute'],
            'target_boundaries_small':bool(np.max(actual[:,4:6].real)<thresholds['target_boundary_population']),
            'waveforms_match':profile_error<=thresholds['waveform_absolute']}
    summary={'execution_status':'completed','validation_passed':all(checks.values()),
        'comparison_kind':'Combined joint-cutoff and integration-backend comparison; not same-cutoff solver validation',
        'reference_job_id':reference_id,'reference_cutoffs':[32,12],'target_cutoffs':[Na,Nb],
        'original_timeout_records_preserved':True,
        'reference_parameters':p,'observable_order':names,
        'compared_observable_indices':physical_indices,
        'excluded_boundary_observable_indices':[4,5],
        'max_absolute_physical_observable_differences':physical_errors,
        'max_buffer_field_difference_fraction':buffer_error_fraction,
        'max_wrong_population_absolute_difference':wrong_difference,
        'max_leakage_absolute_difference':leakage_difference,
        'final_wrong_population':[float(actual[i,6+i,-1].real) for i in (0,1)],
        'reference_final_wrong_population':[float(expected[i,6+i,-1].real) for i in (0,1)],
        'final_leakage':actual[:,8,-1].real.tolist(),
        'reference_final_leakage':expected[:,8,-1].real.tolist(),
        'target_max_top2_a':float(actual[:,4].real.max()),
        'target_max_top_b':float(actual[:,5].real.max()),
        'reference_max_top2_a':float(expected[:,4].real.max()),
        'reference_max_top_b':float(expected[:,5].real.max()),
        'waveform_max_absolute_error':profile_error,
        'state_health':health,'checks':checks,'thresholds':thresholds,
        'wall_s':time.monotonic()-started,
        'solver':'Dynamiqs Tsit5(rtol=1e-10,atol=1e-12)',
        'versions':{'python':platform.python_version(),'dynamiqs':dq.__version__,
                    'jax':jax.__version__,'scipy':scipy.__version__},
        'frozen_source_sha256':manifest['source_sha256'],
        'supplement_source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(),ROOT/'tools/task_2_4_independent_check.py')},
        'profile_function_sha256':hashlib.sha256(inspect.getsource(pulse_envelope).encode()).hexdigest(),
        'scope':'Joint-cutoff evidence for selected pulse, not a global circuit/fidelity certificate'}
    destination=output/'supplemental_cutoffs'
    destination.mkdir(parents=True,exist_ok=True)
    temporary=destination/(reference_id+f'.{os.getpid()}.tmp.npz')
    np.savez_compressed(temporary,t=t,dynamiqs_40_14_expects=actual,
                        qutip_32_12_expects=expected,envelope=np.asarray(envelope(jnp.asarray(t))))
    temporary.replace(destination/(reference_id+'.npz'))
    atomic_json(destination/(reference_id+'.json'),summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',required=True)
    parser.add_argument('--Na',type=int,default=40)
    parser.add_argument('--Nb',type=int,default=14)
    parser.add_argument('--cpus',default='')
    args=parser.parse_args()
    if args.cpus and hasattr(os,'sched_setaffinity'):
        requested=set(map(int,args.cpus.split(',')))
        if not requested.issubset(os.sched_getaffinity(0)):
            raise ValueError('Requested supplemental CPUs unavailable')
        os.sched_setaffinity(0,requested)
    for variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[variable]='1'
    os.environ['MPLBACKEND']='Agg'
    output=args.output.resolve()
    folder=output/'supplemental_cutoffs'
    status_path=folder/(args.reference+'.status.json')
    atomic_json(status_path,{'status':'running','reference_job_id':args.reference,
                             'pid':os.getpid(),'started_unix':time.time()})
    try:
        summary=finish_cutoff(output,args.reference,args.Na,args.Nb)
    except Exception as error:
        atomic_json(status_path,{'status':'failed','error':str(error),'traceback':traceback.format_exc()})
        raise
    atomic_json(status_path,{'status':'completed','validation_passed':summary['validation_passed'],
                             'wall_s':summary['wall_s']})
    print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
    if not summary['validation_passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
