#!/usr/bin/env python3
"""Audit delivered trajectories and write the final Task 2.4 evidence index.

This reconstructs results from executed outputs; it does not execute new physics.
"""
from pathlib import Path
import hashlib
import json
import tarfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def read(relative):
    return json.loads((ROOT / relative).read_text())

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def merge_diagnostics(data):
    """Connect static rates, executed cycles and the failed depletion prediction.

    These are derived diagnostics of existing executions, not extra simulations
    or an optimization over a newly combined control sequence.
    """
    weak = data['tradeoff']['baseline_size'][0]
    enlarged = data['tradeoff']['amplified_size'][0]
    q_weak = data['weak_readout_reference']['gamma_x_per_us'] / (2 * weak['mean_field_information_rate_per_us'])
    q_enlarged = data['spectral_validation']['primary_result']['gamma_x_per_us'] / (2 * enlarged['mean_field_information_rate_per_us'])
    cost = {'definition': 'Gamma_X/(2*information_rate): symmetric rare-switching plateau estimate only',
            'weak_reference': q_weak, 'enlarged_readout': q_enlarged,
            'weak_over_enlarged': q_weak / q_enlarged,
            'complete_cycle_wrong_population_ratio': data['cycles']['baseline']['metrics']['max_wrong_logical_population'] / data['cycles']['amplified']['metrics']['max_wrong_logical_population']}

    pulse_id = 'pulse_0b35816270623dda'
    pulse = read(f'results/task_2_4_campaign/jobs/{pulse_id}/summary.json')
    design = read('results/task_2_4_campaign/jobs/design_a8c60908f1219c2d/summary.json')
    params = pulse['job']['parameters']
    candidate, = [c for c in design['metrics']['candidates']
                  if all(params[k] == v for k, v in c['parameters'].items())]
    with np.load(ROOT / f'results/task_2_4_campaign/jobs/{pulse_id}/trajectories.npz', allow_pickle=False) as z:
        at_end, = np.flatnonzero(np.isclose(z['t'], params['duration'], rtol=0, atol=1e-12))
        e = z['expects']
        coherent = np.abs(e[:, 1, at_end]) ** 2
        photons = e[:, 3, at_end].real
    if not np.allclose(photons, pulse['metrics']['buffer_population_at_pulse_end'], rtol=1e-12, atol=1e-14):
        raise ValueError('Depletion photon population does not match raw trajectory')
    if np.any(photons - coherent < 0):
        raise ValueError('Negative buffer fluctuation population')
    predicted = candidate['semiclassical_prediction']
    depletion = {'job_id': pulse_id, 'design_job_id': 'design_a8c60908f1219c2d',
        'cutoffs': [params['Na'], params['Nb']], 'pulse_duration_us': params['duration'],
        'classical_information': predicted['information_at_pulse_end'],
        'quantum_information': pulse['metrics']['information_at_pulse_end'],
        'classical_mean_field_photons': predicted['buffer_mean_field_population_at_pulse_end'],
        'quantum_coherent_photons': coherent.tolist(), 'quantum_total_photons': photons.tolist(),
        'quantum_fluctuation_photons': (photons - coherent).tolist(),
        'fluctuation_fraction': ((photons - coherent) / photons).tolist(),
        'quantum_total_over_classical_mean_field': (photons / predicted['buffer_mean_field_population_at_pulse_end']).tolist(),
        'qualification': 'Discovery cutoff; fluctuation energy does not alone prove nonclassical photon statistics'}

    strong = data['tradeoff']['baseline_size'][3]
    strong_pulse = read('results/task_2_4_campaign/jobs/pulse_b1f2b1393d0b0ff1/summary.json')['metrics']
    predicted_p = float(-np.expm1(-strong['spectrum']['gamma_x_per_us'] * strong_pulse['duration']) / 2)
    connection = {'local_static_rate_per_us': strong['spectrum']['gamma_x_per_us'],
        'local_rate_cutoffs': [28, 10], 'cloud_pulse_cutoffs': [32, 12],
        'cloud_job_id': 'pulse_b1f2b1393d0b0ff1',
        'static_two_state_hold_prediction': predicted_p,
        'executed_recovered_population': max(strong_pulse['final_wrong_population']),
        'relative_prediction_difference': predicted_p / max(strong_pulse['final_wrong_population']) - 1,
        'qualification': 'Consistency diagnostic only: different cutoffs and a transient/recovery cycle; not a new validation certificate'}
    return {'switching_per_information': cost, 'depletion_model_failure': depletion,
            'local_rate_cloud_pulse_consistency': connection,
            'selection': {'main_protocol': 'enlarge/read/restore at alpha=2.6, ratio=0.1',
                'secondary_result': 'fixed-size pulse termination and loss of mean-field reset accuracy',
                'optional_tradeoff': 'fast enlargement at ratio=0.25 exceeds original static storage rate',
                'untested_combination': 'enlargement plus optimized depletion tail; no combined performance claim'}}

def build():
    data = read('results/task_2_4.json')
    spectral = read('results/task_2_4_spectral_validation.json')
    if data['spectral_validation'] != spectral:
        raise ValueError('Embedded spectral validation is stale')
    reference_checks = read('reviews/task_2_4_reference_checks.json')
    if not reference_checks['all_checks_pass'] or reference_checks['source_sha256'] != digest(ROOT/'tools/check_task_2_4_reference.py'):
        raise ValueError('Reference derivation checks failed or their source changed')
    cycles = {}
    with np.load(ROOT / 'results/task_2_4_trajectories.npz', allow_pickle=False) as archive:
        for name, cycle in data['cycles'].items():
            t = archive[name + '_t']
            e = archive[name + '_expects']
            m = cycle['metrics']
            read_mask = t <= m['read_end_us'] + 1e-10
            delta = np.real(e[0, 1] - e[1, 1])
            information = float(data['configuration']['kappa_b'] * np.trapezoid(delta[read_mask] ** 2, t[read_mask]))
            wrong = [float(e[0, 6, -1].real), float(e[1, 7, -1].real)]
            if not np.allclose(wrong, m['wrong_logical_population'], rtol=1e-10, atol=1e-13):
                raise ValueError('Logical population mismatch: ' + name)
            if not np.isclose(information, m['mean_field_information_at_read_end'], rtol=1e-10, atol=1e-12):
                raise ValueError('Information integration mismatch: ' + name)
            cycles[name] = dict(m, recomputed_information=information,
                recomputed_wrong_population=wrong,
                final_buffer_population=e[:, 3, -1].real.tolist(),
                parameters={k: cycle['parameters'][k] for k in ('Na', 'Nb', 'ratio', 'alpha_readout', 'ramp', 'read_time', 'idle')})
    campaign = ROOT / 'results/task_2_4_campaign'
    cases = []
    ids = ['pulse_b1f2b1393d0b0ff1', 'pulse_6f787216b4e21a6d', 'pulse_b270049fcd119450']
    for identifier in ids:
        record = read(f'results/task_2_4_campaign/jobs/{identifier}/summary.json')
        if record['execution_status'] != 'completed':
            raise ValueError('Incomplete promoted case: ' + identifier)
        cases.append({'job_id': identifier, 'metrics': record['metrics']})
    validations = []
    for folder in ['independent_validation', 'supplemental_cutoffs']:
        for identifier in ids[:2]:
            path = campaign / folder / (identifier + '.json')
            record = json.loads(path.read_text())
            if record.get('validation_passed') is not True:
                raise ValueError('Validation did not pass: ' + str(path))
            validations.append({'source': str(path.relative_to(ROOT)), 'sha256': digest(path),
                                'validation_passed': True, 'kind': folder})
    paths = [ROOT/'results'/name for name in ['task_2_4.json', 'task_2_4_trajectories.npz',
        'task_2_4_rate_trajectories.npz', 'task_2_4_spectral_validation.json',
        'task_2_4_measurement_validation.json', 'task_2_4_circuit_validation.json']]
    paths += [campaign/'manifest.json', campaign/'status.json', campaign/'source_snapshot.tar.gz']
    paths += sorted(campaign.glob('jobs/*/summary.json'))
    paths += [campaign/'jobs/pulse_0b35816270623dda/trajectories.npz']
    paths += [ROOT/'tools/synthesize_task_2_4.py', ROOT/'tools/plot_task_2_4_model_validation.py']
    paths += [ROOT/'tools/check_task_2_4_reference.py', ROOT/'reviews/task_2_4_reference_checks.json',
              ROOT/'tools/plot_task_2_4_drive_tradeoff.py', ROOT/'tools/plot_task_2_4_protocol_summary.py']
    with tarfile.open(campaign/'source_snapshot.tar.gz', 'r:gz') as frozen:
        source_hashes = read('results/task_2_4_campaign/manifest.json')['source_sha256']
        for name, expected in source_hashes.items():
            actual = hashlib.sha256(frozen.extractfile(name).read()).hexdigest()
            if actual != expected:
                raise ValueError('Archived execution source mismatch: '+name)
    paths += [campaign/'jobs'/identifier/'summary.json' for identifier in ids]
    # Hash only existing source records. Never invent or replace historical execution hashes.
    provenance = {str(p.relative_to(ROOT)): digest(p) for p in paths if p.exists()}
    idle = data['matched_idle_cycle']['wrong_logical_population'][0]
    summary = {'schema_version': 2, 'purpose': 'Final synthesis of executed evidence; no new simulation',
        'frozen_cloud_source_records_verified': len(source_hashes),
        'source_files_sha256': provenance,
        'cycles': cycles, 'static_selected_mode': spectral['primary_result'],
        'independent_reference_checks': reference_checks,
        'integrated_findings': merge_diagnostics(data),
        'comparisons': dict(data['comparison'], matched_clock_idle_wrong_population=idle,
            conservative_wrong_reduction_vs_idle_fraction=1-cycles['amplified']['max_wrong_logical_population']/idle),
        'campaign': {'historical_scheduler': read('results/task_2_4_campaign/status.json'),
                     'promoted_fixed_time_cases': cases, 'independent_and_supplemental_checks': validations},
        'qualifications': ['Ideal cubic model for complete-cycle headlines',
            '2.33x gain is relative to the specified weak reference, not a global optimum',
            'Information is a mean-signal shot-noise reference, not measured single-shot fidelity',
            'Gamma is the selected logical imbalance decay exponent, not a one-way rate',
            'No global spectral dominance proof or rigorous infinite-Fock error bound',
            'Fixed-time waveform comparisons do not establish matched-information superiority',
            'Historical two scheduler timeouts preserved; supplemental checks passed separately',
            'Corrected complete enlargement cycle and full-device robustness remain untested']}
    target = ROOT/'results/task_2_4_final_summary.json'
    target.write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    return target

if __name__ == '__main__':
    print(build())
