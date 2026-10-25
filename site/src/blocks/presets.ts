// Presets the level-6 canvas and the tutor's wrong-build demos load.
// The correct two-mode machine is H = g₂(a²b† + a†²b) − ε_d(b + b†),
// with jumps √κ_b·b and √κ_a·a. α² = ε_d/g₂ is fixed by that balance.

import { add, mul, num, param, pow, sqrt, sym, type ExprTree, type Mode } from './expr.js';

export interface Preset {
  H: ExprTree;
  jumps: ExprTree[];
  modes: Mode;
}

export const H2PH_PYTHON =
  'g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())';

const coupling = mul(
  param('g2'),
  add(mul(pow(sym('a'), 2), sym('bd')), mul(pow(sym('ad'), 2), sym('b'))),
);

const bufferDrive = mul(num(-1), param('eps_d'), add(sym('b'), sym('bd')));

export const h2phH: ExprTree = add(coupling, bufferDrive);

export const h2phJumps: ExprTree[] = [
  mul(sqrt(param('kappa_b')), sym('b')),
  mul(sqrt(param('kappa_a')), sym('a')),
];

export const oneModeCatJump: ExprTree = mul(
  sqrt(param('kappa2')),
  add(pow(sym('a'), 2), mul(num(-1), pow(param('alpha'), 2), sym('I'))),
);

const memoryDrive = mul(num(-1), param('eps_z'), add(sym('a'), sym('ad')));

const wrongConversionBody = mul(
  param('g2'),
  add(mul(sym('a'), pow(sym('bd'), 2)), mul(sym('ad'), pow(sym('b'), 2))),
);

export const PRESET_NAMES = [
  'empty',
  'h2ph_correct',
  'one_mode_cat',
  'wrong_drive_on_memory',
  'wrong_no_dissipation',
  'wrong_conversion',
  'wrong_missing_hc',
  'readout_z',
  'state_prep_x',
  'kerr',
] as const;

export type PresetName = (typeof PRESET_NAMES)[number];

const PRESETS: Record<PresetName, Preset> = {
  empty: { H: num(0), jumps: [], modes: 'one' },
  h2ph_correct: { H: h2phH, jumps: h2phJumps, modes: 'two' },
  one_mode_cat: { H: num(0), jumps: [oneModeCatJump], modes: 'one' },
  wrong_drive_on_memory: {
    // ε(a+a†) pushes along Im, the ridge between the wells. It cannot select +α.
    H: add(coupling, memoryDrive),
    jumps: h2phJumps,
    modes: 'two',
  },
  wrong_no_dissipation: {
    H: h2phH,
    jumps: [mul(sqrt(param('kappa_a')), sym('a'))],
    modes: 'two',
  },
  wrong_conversion: {
    // a·b†² converts one memory photon into two buffer photons. The hardware term is a²·b†.
    H: add(wrongConversionBody, bufferDrive),
    jumps: h2phJumps,
    modes: 'two',
  },
  wrong_missing_hc: {
    H: add(mul(param('g2'), mul(pow(sym('a'), 2), sym('bd'))), bufferDrive),
    jumps: h2phJumps,
    modes: 'two',
  },
  readout_z: {
    // Level 7. ε_Z(a+a†) is a Z_L rotation on top of the cat Hamiltonian, not a preparation drive.
    H: add(h2phH, mul(param('eps_z'), add(sym('a'), sym('ad')))),
    jumps: h2phJumps,
    modes: 'two',
  },
  state_prep_x: {
    // i(a†−a) pushes along Re, so it can fall into the +α well.
    H: mul(num(0, 1), param('eps_x'), add(sym('ad'), mul(num(-1), sym('a')))),
    jumps: [oneModeCatJump],
    modes: 'one',
  },
  kerr: {
    H: mul(param('K'), sym('n_a')),
    jumps: [oneModeCatJump],
    modes: 'one',
  },
};

export function getPreset(name: string): Preset {
  if (!isPresetName(name)) {
    throw new Error(`unknown preset "${name}". Known: ${PRESET_NAMES.join(', ')}`);
  }
  return PRESETS[name];
}

export function isPresetName(name: string): name is PresetName {
  return (PRESET_NAMES as readonly string[]).includes(name);
}
