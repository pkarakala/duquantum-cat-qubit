// Teachable wrong builds for level 6. Detectors name the mistake; they do not block the tree.

import { isHermitianSymbolic, operatorTerms, type ExprTree, type Mode, type OpTerm } from './expr.js';

export type WrongKey =
  | 'drive_on_memory_not_buffer'
  | 'no_dissipation'
  | 'wrong_conversion'
  | 'missing_hc';

export interface Finding {
  key: WrongKey;
  misconception?: 'M3';
  message: string;
}

export interface DetectInput {
  H: ExprTree;
  jumps?: ExprTree[];
  modes?: Mode;
}

export function detect(input: ExprTree | DetectInput): Finding[] {
  const program = isProgram(input) ? input : { H: input, jumps: [] as ExprTree[] };
  const jumps = program.jumps ?? [];
  const findings: Finding[] = [];
  let terms: OpTerm[] = [];
  try {
    terms = operatorTerms(program.H);
  } catch {
    terms = [];
  }
  const memory = hasQuadrature(terms, 'a', 'ad');
  const buffer = hasQuadrature(terms, 'b', 'bd');
  if (memory && !buffer) {
    findings.push({
      key: 'drive_on_memory_not_buffer',
      message: "this pushes along the ridge between the wells, so it can't make a cat",
    });
  }
  const modes = program.modes ?? inferModes(program.H, jumps);
  const dissipated =
    modes === 'two' ? jumps.some((jump) => hasSym(jump, 'b')) : jumps.some(hasA2);
  if (!dissipated) {
    findings.push({
      key: 'no_dissipation',
      misconception: 'M3',
      message:
        'nothing dissipates: add √κ_b·b so the buffer can dump pairs, or √κ₂·a² for pair loss. Engineered two-photon loss creates the cat.',
    });
  }
  if (hasOps(terms, ['a', 'bd', 'bd']) || hasOps(terms, ['ad', 'b', 'b'])) {
    findings.push({
      key: 'wrong_conversion',
      message:
        'this is a·b†², not a²·b†: one memory photon in and two buffer photons out, instead of two memory photons for one buffer photon',
    });
  }
  if (!isHermitianSymbolic(program.H)) {
    findings.push({
      key: 'missing_hc',
      message: 'the h.c. term is missing, so H is not Hermitian',
    });
  }
  return findings;
}

function isProgram(input: ExprTree | DetectInput): input is DetectInput {
  return !!input && typeof input === 'object' && 'H' in input && !('op' in input);
}

function inferModes(H: ExprTree, jumps: ExprTree[]): Mode {
  const buffer = [H, ...jumps].some((tree) => hasSym(tree, 'b') || hasSym(tree, 'bd'));
  return buffer ? 'two' : 'one';
}

function hasQuadrature(terms: OpTerm[], left: OpTerm['ops'][number], right: OpTerm['ops'][number]): boolean {
  const singles = terms.filter((term) => term.ops.length === 1 && Math.hypot(term.re, term.im) > 1e-9);
  return singles.some((term) => {
    if (term.ops[0] !== left) return false;
    return singles.some(
      (other) =>
        other.ops[0] === right &&
        sameList(term.params, other.params) &&
        sameList(term.sqrts, other.sqrts) &&
        Math.abs(term.re - other.re) < 1e-9 &&
        Math.abs(term.im - other.im) < 1e-9,
    );
  });
}

function hasOps(terms: OpTerm[], ops: string[]): boolean {
  return terms.some(
    (term) =>
      term.ops.length === ops.length &&
      term.ops.every((op, index) => op === ops[index]) &&
      Math.hypot(term.re, term.im) > 1e-9,
  );
}

function sameList(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((item, index) => item === right[index]);
}

function walk(tree: ExprTree, visit: (node: ExprTree) => void): void {
  visit(tree);
  if (tree.op === 'add' || tree.op === 'mul') tree.args.forEach((arg) => walk(arg, visit));
  else if (tree.op === 'pow') walk(tree.base, visit);
  else if (tree.op === 'dag' || tree.op === 'sqrt') walk(tree.arg, visit);
}

function hasSym(tree: ExprTree, name: string): boolean {
  let found = false;
  walk(tree, (node) => {
    if (node.op === 'sym' && node.name === name) found = true;
  });
  return found;
}

function hasA2(tree: ExprTree): boolean {
  let found = false;
  walk(tree, (node) => {
    if (node.op === 'pow' && node.exp >= 2 && node.base.op === 'sym' && node.base.name === 'a') found = true;
    if (node.op === 'mul') {
      const count = node.args.filter((arg) => arg.op === 'sym' && arg.name === 'a').length;
      if (count >= 2) found = true;
    }
  });
  return found;
}
