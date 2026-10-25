#!/usr/bin/env python3
"""Bounded independent Dynamiqs checks of completed QuTiP campaign finalists.

This tool lives outside the running campaign's src/tasks source-hash set.
It never modifies that source or claims that pending cases passed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def control_signature(parameters):
    return json.dumps({k:v for k,v in parameters.items()
                       if k not in ('Na', 'Nb', 'step', 'rtol', 'atol')}, sort_keys=True)


def verify_frozen_sources(output):
    manifest = json.loads((output/'manifest.json').read_text())
    changed = [name for name, digest in manifest['source_sha256'].items()
               if not (ROOT/name).is_file()
               or hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest]
    if changed:
        raise RuntimeError('Frozen campaign source changed: '+', '.join(changed))


def completed_references(output, max_cases):
    """One selected constant and one selected shape, at the production cutoff."""
    manifest = json.loads((output/'manifest.json').read_text())
    frozen = manifest.get('finalists_frozen')
    if not frozen:
        return [], ['finalist selection has not finished']
    by_id = {j['id']:j for j in manifest['jobs']}
    selected = [by_id[i] for i in frozen['discovery_ids']]
    targets = []
    for shaped in (False, True):
        match = next((j for j in selected
                      if (j['parameters'].get('profile','constant') != 'constant') == shaped), None)
        if match is not None:
            targets.append(match)
    references, pending = [], []
    for target in targets[:max_cases]:
        found = None
        for item in manifest['jobs']:
            p = item['parameters']
            if (item['kind'] != 'pulse' or p.get('Na') != 32 or p.get('Nb') != 12
                    or p.get('order','cubic') != 'cubic' or p.get('phase',0.) != 0.
                    or control_signature(p) != control_signature(target['parameters'])):
                continue
            folder = output/'jobs'/item['id']
            if not (folder/'summary.json').exists() or not (folder/'trajectories.npz').exists():
                continue
            record = json.loads((folder/'summary.json').read_text())
            if record.get('execution_status') == 'completed' and record.get('job') == item:
                found = dict(item, reference_folder=str(folder))
                break
        if found is None:
            pending.append('production reference pending: '+target['id'])
        else:
            references.append(found)
    if len(targets) < min(2, max_cases):
        pending.append('selection did not produce both a constant and a shaped finalist')
    return references, pending


def jax_envelope(t, duration, profile, edge_fraction, hold_ratio, tail_ratio, knots, jnp):
    """Independent traceable construction, checked against the QuTiP profile."""
    u = t/duration
    inside = (u >= 0) & (u < 1)
    if profile == 'constant':
        return jnp.where(inside, 1., 0.)
    edge = .5*(1-jnp.cos(jnp.pi*jnp.clip(u/edge_fraction,0,1)))
    edge *= .5*(1-jnp.cos(jnp.pi*jnp.clip((1-u)/edge_fraction,0,1)))
    if profile == 'raised_cosine':
        value = edge
    elif profile == 'gaussian':
        value = edge*jnp.exp(-.5*((u-.5)/.20)**2)
    elif profile == 'build_hold_deplete':
        first = .5*(1-jnp.cos(jnp.pi*jnp.clip((u-knots[0])/edge_fraction+.5,0,1)))
        second = .5*(1-jnp.cos(jnp.pi*jnp.clip((u-knots[1])/edge_fraction+.5,0,1)))
        value = edge*(1+(hold_ratio-1)*first+(tail_ratio-hold_ratio)*second)
    else:
        raise ValueError('Unknown reference pulse profile: '+profile)
    return jnp.where(inside,value,0.)


def check_reference(item, destination):
    # CPU affinity and thread caps must already be set before these imports.
    import inspect
    import dynamiqs as dq
    import jax
    import jax.numpy as jnp
    import numpy as np
    import qutip
    import scipy
    from src.circuit import rotating_model, buffer_drive
    from src.readout_pulses import pulse_envelope
    from src.readout_measurement import optimized_quadrature_information
    from tasks.task_2_4 import observables, sparse_qarray

    dq.set_precision('double')
    dq.set_progress_meter(False)
    folder = Path(item['reference_folder'])
    reference = json.loads((folder/'summary.json').read_text())
    p = reference['metrics']
    with np.load(folder/'trajectories.npz') as archive:
        t, expected = archive['t'], archive['expects']
    Na, Nb, alpha = p['Na'],p['Nb'],p['alpha']
    if (Na,Nb) != (32,12) or p['order'] != 'cubic' or p['phase'] != 0.:
        raise ValueError('This certificate is restricted to production-cutoff real cubic pulses')
    if expected.shape != (2,10,len(t)) or np.any(np.diff(t)<=0):
        raise ValueError('Reference trajectory shape or time grid is invalid')
    boundary = np.asarray(p['stage_boundaries_us'])
    if any(np.min(abs(t-point)) > 1e-12 for point in boundary):
        raise ValueError('Reference grid omits a stage boundary')
    profile_args = (p['duration'],p['profile'],p['edge_fraction'],p['hold_ratio'],
                    p['tail_ratio'],p['knots'])
    def envelope(time_value):
        return jax_envelope(time_value,*profile_args,jnp)
    # Include points immediately on either side of every waveform boundary.
    delta = 1e-10*max(1.,p['duration'])
    probe = np.unique(np.r_[t,np.linspace(0.,t[-1],4001),boundary,
                            boundary-delta,boundary+delta])
    profile_error = float(np.max(abs(np.asarray(envelope(jnp.asarray(probe)))
                                     -pulse_envelope(probe,*profile_args))))
    if profile_error > 1e-13:
        raise RuntimeError('Independent traceable profile does not match the reference waveform')
    a,b,ops = observables(Na,Nb,alpha)
    H,_ = rotating_model(Na,Nb,alpha,p['g2'],0.,p['order'])
    H = sparse_qarray(H,Na,Nb)
    H += (buffer_drive(alpha,p['g2'],p['order'])
          -buffer_drive(alpha,p['control_g2'],p['order']))*(b+b.dag())
    epsilon = p['ratio']*p['control_g2']*p['drive_scale']
    H += dq.modulated(lambda time_value: epsilon*envelope(time_value),a+a.dag(),
                       discontinuity_ts=jnp.asarray(boundary))
    jumps = [np.sqrt(p['kappa_b'])*b]
    if p['kappa_a']:
        jumps.append(np.sqrt(p['kappa_a'])*a)
    initial = [dq.tensor(dq.coherent(Na,sign*alpha),dq.fock(Nb,0)) for sign in (1,-1)]
    started = time.monotonic()
    result = dq.mesolve(H,jumps,initial,jnp.asarray(t),exp_ops=ops,save_states=False,
                        method=dq.method.Tsit5(rtol=1e-10,atol=1e-12,max_steps=5000000))
    actual = np.asarray(result.expects)
    final = np.asarray(result.states.to_jax())[...,-1,:,:]
    errors = np.max(abs(actual-expected),axis=(0,2))
    wrong = np.asarray([actual[i,6+i,-1].real for i in (0,1)])
    qwrong = np.asarray([expected[i,6+i,-1].real for i in (0,1)])
    mask = t <= p['duration']
    info = optimized_quadrature_information(t[mask],actual[0,1,mask]-actual[1,1,mask],
                                             p['kappa_b'],efficiency=p['efficiency'])
    thresholds = [2e-7,2e-7,2e-6,2e-6,1e-7,1e-7,1e-7,1e-7,1e-7,1e-9]
    health = {'max_trace_error':float(np.max(abs(actual[:,9]-1))),
              'final_min_eigenvalue':float(np.linalg.eigvalsh(final).min()),
              'final_hermiticity_error':float(np.max(abs(final-final.conj().swapaxes(-1,-2))))}
    checks = {'waveforms_match':profile_error<=1e-13,
              'all_observables_agree':bool(np.all(errors<=thresholds)),
              'trace_preserved':health['max_trace_error']<1e-9,
              'final_state_numerically_positive':health['final_min_eigenvalue']>-1e-7,
              'final_state_hermitian':health['final_hermiticity_error']<1e-10}
    metadata = {'job_id':item['id'],'reference_job':reference['job'],
        'execution_status':'completed','validation_passed':all(checks.values()),'checks':checks,
        'reference_parameters':p,'solver':'Dynamiqs Tsit5(rtol=1e-10,atol=1e-12)',
        'comparison':'Both independent codeword evolutions, identical saved grid and stage boundaries',
        'observable_order':p['observable_order'],
        'max_absolute_error_by_observable':errors.tolist(),
        'absolute_tolerance_by_observable':thresholds,'waveform_max_absolute_error':profile_error,
        'final_wrong_population':wrong.tolist(),'reference_final_wrong_population':qwrong.tolist(),
        'final_wrong_population_max_error':float(np.max(abs(wrong-qwrong))),
        'final_leakage':actual[:,8,-1].real.tolist(),
        'final_leakage_max_error':float(np.max(abs(actual[:,8,-1]-expected[:,8,-1]))),
        'information_at_pulse_end':info['optimal_fixed_quadrature_information'],
        'information_absolute_difference':float(abs(info['optimal_fixed_quadrature_information']-p['information_at_pulse_end'])),
        'state_health':health,'wall_s':time.monotonic()-started,
        'versions':{'python':platform.python_version(),'dynamiqs':dq.__version__,
                    'jax':jax.__version__,'qutip':qutip.__version__,'scipy':scipy.__version__},
        'source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(),ROOT/'src/circuit.py',ROOT/'src/readout_pulses.py',
                         ROOT/'tasks/task_2_4.py')},
        'profile_function_sha256':hashlib.sha256(inspect.getsource(pulse_envelope).encode()).hexdigest(),
        'scope':'Independent integration check only; does not certify Fock convergence or single-shot fidelity'}
    destination.mkdir(parents=True,exist_ok=True)
    temporary = destination/(item['id']+'.tmp.npz')
    np.savez_compressed(temporary,t=t,dynamiqs_expects=actual,qutip_expects=expected,
                        envelope=np.asarray(envelope(jnp.asarray(t))))
    temporary.replace(destination/(item['id']+'.npz'))
    atomic_json(destination/(item['id']+'.json'),metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--wait-seconds',type=float,default=900.)
    parser.add_argument('--max-cases',type=int,default=2)
    parser.add_argument('--cpus',default='14,15')
    args = parser.parse_args()
    if args.wait_seconds<0 or not 1<=args.max_cases<=2:
        raise ValueError('Nonnegative wait and one or two cases required')
    if hasattr(os,'sched_setaffinity') and args.cpus:
        wanted = set(map(int,args.cpus.split(',')))
        if not wanted.issubset(os.sched_getaffinity(0)):
            raise ValueError('Requested independent-validation CPUs are unavailable')
        os.sched_setaffinity(0,wanted)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    os.environ['MPLBACKEND']='Agg'
    output=args.output.resolve()
    destination=output/'independent_validation'
    verify_frozen_sources(output)
    deadline=time.monotonic()+args.wait_seconds
    selected,pending=[],[]
    while True:
        selected,pending=completed_references(output,args.max_cases)
        atomic_json(destination/'status.json',{'status':'waiting_for_references','pending':pending,
            'available_job_ids':[j['id'] for j in selected],'remaining_wait_s':max(0,deadline-time.monotonic())})
        if not pending or time.monotonic()>=deadline:
            break
        time.sleep(min(15.,max(0,deadline-time.monotonic())))
    results=[]
    for item in selected:
        atomic_json(destination/'status.json',{'status':'running','active_job_id':item['id'],
            'completed_job_ids':[r['job_id'] for r in results],'pending':pending})
        try:
            result=check_reference(item,destination)
            results.append(result)
            print(item['id'],'validation_passed=',result['validation_passed'],flush=True)
        except Exception as error:
            import traceback
            atomic_json(destination/(item['id']+'.error.json'),{'status':'failed',
                'error':str(error),'traceback':traceback.format_exc()})
            results.append({'job_id':item['id'],'validation_passed':False,'execution_status':'failed'})
    status={'status':'completed' if not pending and len(results)==args.max_cases else 'incomplete',
            'case_count':len(results),'requested_cases':args.max_cases,'pending':pending,
            'case_results':[{'job_id':r['job_id'],'execution_status':r['execution_status'],
                             'validation_passed':r['validation_passed']} for r in results],
            'all_requested_cases_validated':not pending and len(results)==args.max_cases
                and all(r['validation_passed'] for r in results)}
    atomic_json(destination/'status.json',status)
    print(json.dumps(status,indent=2),flush=True)
    if results and any(not r['validation_passed'] for r in results):
        raise SystemExit(1)
    if not status['all_requested_cases_validated']:
        raise SystemExit(2)


if __name__=='__main__':
    main()
