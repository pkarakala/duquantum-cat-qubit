// ExprTree (CONTRACT §4): the only thing a learner Hamiltonian is allowed to be.
// Pretty-printing is a pure function of the tree. Nothing here is eval'd.

export const PARAM_NAMES = [
  'g2',
  'eps_d',
  'kappa_b',
  'kappa_a',
  'kappa2',
  'alpha',
  'eps_z',
  'eps_x',
  'K',
  'chi',
] as const;

export const SYM_NAMES = ['a', 'ad', 'b', 'bd', 'I', 'n_a'] as const;

export type Mode = 'one' | 'two';
export type Role = 'H' | 'jump';
export type ParamName = (typeof PARAM_NAMES)[number];
export type SymName = (typeof SYM_NAMES)[number];

export interface NumNode {
  op: 'num';
  value: number;
  imag?: number;
}
export interface ParamNode {
  op: 'param';
  name: string;
}
export interface SymNode {
  op: 'sym';
  name: string;
}
export interface AddNode {
  op: 'add';
  args: ExprTree[];
}
export interface MulNode {
  op: 'mul';
  args: ExprTree[];
}
export interface PowNode {
  op: 'pow';
  base: ExprTree;
  exp: number;
}
export interface DagNode {
  op: 'dag';
  arg: ExprTree;
}
export interface SqrtNode {
  op: 'sqrt';
  arg: ExprTree;
}
export type ExprTree =
  | NumNode
  | ParamNode
  | SymNode
  | AddNode
  | MulNode
  | PowNode
  | DagNode
  | SqrtNode;

export interface Validation {
  ok: boolean;
  errors: string[];
}

const PARAMS = new Set<string>(PARAM_NAMES);
const SYMS = new Set<string>(SYM_NAMES);
const MAX_DEPTH = 8;
const MAX_NODES = 64;

export function sym(name: string): SymNode {
  return { op: 'sym', name };
}
export function param(name: string): ParamNode {
  return { op: 'param', name };
}
export function num(value: number, imag = 0): NumNode {
  if (imag === 0) return { op: 'num', value };
  return { op: 'num', value, imag };
}
export function add(...args: ExprTree[]): AddNode {
  return { op: 'add', args };
}
export function mul(...args: ExprTree[]): MulNode {
  return { op: 'mul', args };
}
export function pow(base: ExprTree, exp: number): PowNode {
  return { op: 'pow', base, exp };
}
export function sqrt(arg: ExprTree): SqrtNode {
  return { op: 'sqrt', arg };
}
export function dag(arg: ExprTree): DagNode {
  return { op: 'dag', arg };
}

export function validate(tree: ExprTree, modes: Mode, role: Role = 'H'): Validation {
  const errors: string[] = [];
  const counted = inspect(tree, modes, errors);
  if (counted.depth > MAX_DEPTH) {
    errors.push(`expression depth ${counted.depth} exceeds ${MAX_DEPTH}`);
  }
  if (counted.nodes > MAX_NODES) {
    errors.push(`expression has ${counted.nodes} nodes; limit is ${MAX_NODES}`);
  }
  if (role === 'jump') {
    for (const message of jumpCoeffErrors(tree)) errors.push(message);
  }
  if (errors.length === 0 && role === 'H') {
    if (!isHermitianSymbolic(tree)) errors.push('H is not Hermitian');
    else if (!isHermitianNumeric(tree)) {
      errors.push('H failed the numeric Hermitian check at cutoff N=8 (tolerance 1e-9)');
    }
  }
  return { ok: errors.length === 0, errors: dedupe(errors) };
}

export function validateProgram(
  program: { H: ExprTree; jumps: ExprTree[] },
  modes: Mode,
): Validation {
  const errors: string[] = [];
  for (const message of validate(program.H, modes, 'H').errors) errors.push(`H: ${message}`);
  program.jumps.forEach((jump, index) => {
    for (const message of validate(jump, modes, 'jump').errors) {
      errors.push(`jump ${index + 1}: ${message}`);
    }
  });
  return { ok: errors.length === 0, errors };
}

function dedupe(errors: string[]): string[] {
  const seen = new Set<string>();
  return errors.filter((error) => (seen.has(error) ? false : (seen.add(error), true)));
}

function isRecord(value: unknown): value is { op?: unknown } {
  return !!value && typeof value === 'object';
}

function inspect(tree: ExprTree, modes: Mode, errors: string[]): { depth: number; nodes: number } {
  if (!isRecord(tree) || typeof tree.op !== 'string') {
    errors.push('expression is not an ExprTree');
    return { depth: 1, nodes: 1 };
  }
  switch (tree.op) {
    case 'num': {
      const node = tree as NumNode;
      if (typeof node.value !== 'number' || !Number.isFinite(node.value)) {
        errors.push('number value must be a finite real');
      }
      if (node.imag !== undefined && (typeof node.imag !== 'number' || !Number.isFinite(node.imag))) {
        errors.push('number imag must be a finite real');
      }
      return { depth: 1, nodes: 1 };
    }
    case 'param': {
      const name = (tree as ParamNode).name;
      if (!PARAMS.has(name)) errors.push(`unknown param "${name}"`);
      return { depth: 1, nodes: 1 };
    }
    case 'sym': {
      const name = (tree as SymNode).name;
      if (!SYMS.has(name)) errors.push(`unknown symbol "${name}"`);
      else if ((name === 'b' || name === 'bd') && modes !== 'two') {
        errors.push(`symbol "${name}" is only allowed in two-mode`);
      }
      return { depth: 1, nodes: 1 };
    }
    case 'add':
    case 'mul': {
      const args = (tree as AddNode).args;
      if (!Array.isArray(args) || args.length === 0) {
        errors.push(`${tree.op} has no arguments`);
        return { depth: 1, nodes: 1 };
      }
      let nodes = 1;
      let depth = 1;
      for (const arg of args) {
        const child = inspect(arg, modes, errors);
        nodes += child.nodes;
        depth = Math.max(depth, 1 + child.depth);
      }
      return { depth, nodes };
    }
    case 'pow': {
      const node = tree as PowNode;
      if (!Number.isInteger(node.exp) || node.exp < 0 || node.exp > 4) {
        errors.push(`power exponent ${String(node.exp)} is outside 0–4`);
      }
      const child = inspect(node.base, modes, errors);
      return { depth: 1 + child.depth, nodes: 1 + child.nodes };
    }
    case 'dag': {
      const child = inspect((tree as DagNode).arg, modes, errors);
      return { depth: 1 + child.depth, nodes: 1 + child.nodes };
    }
    case 'sqrt': {
      const arg = (tree as SqrtNode).arg;
      if (!isRecord(arg) || (arg.op !== 'param' && arg.op !== 'num')) {
        errors.push('sqrt applies only to a param or a number');
        if (isRecord(arg) && typeof arg.op === 'string') {
          const child = inspect(arg as ExprTree, modes, errors);
          return { depth: 1 + child.depth, nodes: 1 + child.nodes };
        }
        return { depth: 2, nodes: 2 };
      }
      const child = inspect(arg as ExprTree, modes, errors);
      return { depth: 1 + child.depth, nodes: 1 + child.nodes };
    }
    default:
      errors.push(`unknown op "${tree.op}"`);
      return { depth: 1, nodes: 1 };
  }
}

function jumpCoeffErrors(tree: ExprTree): string[] {
  if (!isRecord(tree) || typeof tree.op !== 'string') return [];
  const terms = tree.op === 'add' ? (tree as AddNode).args : [tree];
  const errors: string[] = [];
  for (const term of terms) {
    const factors = isRecord(term) && term.op === 'mul' ? (term as MulNode).args : [term];
    let sawSqrt = false;
    let bare = false;
    for (const factor of factors) {
      if (!isRecord(factor)) continue;
      if (factor.op === 'sqrt') sawSqrt = true;
      else if (factor.op === 'param') bare = true;
      else if (factor.op === 'num') {
        const value = (factor as NumNode).value;
        const imag = (factor as NumNode).imag ?? 0;
        const sign = imag === 0 && (value === 1 || value === -1);
        const unit = value === 0 && (imag === 1 || imag === -1);
        if (!sign && !unit) bare = true;
      }
    }
    if (!sawSqrt || bare) errors.push('jump coefficient must be wrapped in sqrt');
  }
  return errors;
}

type Op = 'a' | 'ad' | 'b' | 'bd';

export interface OpTerm {
  re: number;
  im: number;
  params: string[];
  sqrts: string[];
  ops: Op[];
}

const TERM_CAP = 4096;

export function operatorTerms(tree: ExprTree): OpTerm[] {
  return termsOf(tree);
}

export function isHermitianSymbolic(tree: ExprTree): boolean {
  try {
    const terms = termsOf(tree);
    return mapsEqual(termMap(terms), termMap(terms.map(dagTerm)));
  } catch {
    return false;
  }
}

function termsOf(tree: ExprTree): OpTerm[] {
  if (!isRecord(tree) || typeof tree.op !== 'string') throw new Error('not a tree');
  switch (tree.op) {
    case 'num':
      return [term((tree as NumNode).value, (tree as NumNode).imag ?? 0, [], [], [])];
    case 'param':
      return [term(1, 0, [(tree as ParamNode).name], [], [])];
    case 'sym':
      return symTerms((tree as SymNode).name);
    case 'add':
      return (tree as AddNode).args.flatMap(termsOf);
    case 'mul':
      return (tree as MulNode).args.reduce((acc, arg) => convolve(acc, termsOf(arg)), [term(1, 0, [], [], [])]);
    case 'pow': {
      const node = tree as PowNode;
      if (!Number.isInteger(node.exp) || node.exp < 0) throw new Error('bad power');
      if (node.exp === 0) return [term(1, 0, [], [], [])];
      let acc = termsOf(node.base);
      for (let i = 1; i < node.exp; i++) acc = convolve(acc, termsOf(node.base));
      return acc;
    }
    case 'sqrt': {
      const arg = (tree as SqrtNode).arg;
      if (arg.op === 'param') return [term(1, 0, [], [arg.name], [])];
      if (arg.op === 'num') {
        const root = sqrtComplex(arg.value, arg.imag ?? 0);
        return [term(root.re, root.im, [], [], [])];
      }
      throw new Error('sqrt');
    }
    case 'dag':
      return termsOf((tree as DagNode).arg).map(dagTerm);
    default:
      throw new Error('op');
  }
}

function term(re: number, im: number, params: string[], sqrts: string[], ops: Op[]): OpTerm {
  return { re, im, params, sqrts, ops };
}

function symTerms(name: string): OpTerm[] {
  switch (name) {
    case 'a':
      return [term(1, 0, [], [], ['a'])];
    case 'ad':
      return [term(1, 0, [], [], ['ad'])];
    case 'b':
      return [term(1, 0, [], [], ['b'])];
    case 'bd':
      return [term(1, 0, [], [], ['bd'])];
    case 'I':
      return [term(1, 0, [], [], [])];
    case 'n_a':
      // n = a†a is Hermitian because (a†a)† = a†a. Keep that order.
      return [term(1, 0, [], [], ['ad', 'a'])];
    default:
      throw new Error(name);
  }
}

function convolve(left: OpTerm[], right: OpTerm[]): OpTerm[] {
  if (left.length * right.length > TERM_CAP) throw new Error('term cap');
  const out: OpTerm[] = [];
  for (const a of left) {
    for (const b of right) {
      out.push(
        term(
          a.re * b.re - a.im * b.im,
          a.re * b.im + a.im * b.re,
          [...a.params, ...b.params].sort(),
          [...a.sqrts, ...b.sqrts].sort(),
          canon([...a.ops, ...b.ops]),
        ),
      );
    }
  }
  return out;
}

function canon(ops: Op[]): Op[] {
  // a-mode commutes with b-mode. Order inside one mode is the operator order.
  const memory: Op[] = [];
  const buffer: Op[] = [];
  for (const op of ops) {
    if (op === 'a' || op === 'ad') memory.push(op);
    else buffer.push(op);
  }
  return [...memory, ...buffer];
}

function dagTerm(value: OpTerm): OpTerm {
  const ops = value.ops
    .slice()
    .reverse()
    .map((op) => (op === 'a' ? 'ad' : op === 'ad' ? 'a' : op === 'b' ? 'bd' : 'b')) as Op[];
  return term(value.re, -value.im, value.params, value.sqrts, canon(ops));
}

function termKey(value: OpTerm): string {
  return `${value.params.join(',')}|${value.sqrts.join(',')}|${value.ops.join('.')}`;
}

function termMap(terms: OpTerm[]): Map<string, { re: number; im: number }> {
  const map = new Map<string, { re: number; im: number }>();
  for (const value of terms) {
    if (Math.hypot(value.re, value.im) < 1e-15) continue;
    const key = termKey(value);
    const prev = map.get(key) ?? { re: 0, im: 0 };
    map.set(key, { re: prev.re + value.re, im: prev.im + value.im });
  }
  for (const [key, coeff] of map) {
    if (Math.hypot(coeff.re, coeff.im) < 1e-12) map.delete(key);
  }
  return map;
}

function mapsEqual(
  left: Map<string, { re: number; im: number }>,
  right: Map<string, { re: number; im: number }>,
): boolean {
  if (left.size !== right.size) return false;
  for (const [key, coeff] of left) {
    const other = right.get(key);
    if (!other) return false;
    if (Math.abs(coeff.re - other.re) > 1e-9 || Math.abs(coeff.im - other.im) > 1e-9) return false;
  }
  return true;
}

function sqrtComplex(re: number, imag: number): { re: number; im: number } {
  if (imag === 0) {
    if (re >= 0) return { re: Math.sqrt(re), im: 0 };
    return { re: 0, im: Math.sqrt(-re) };
  }
  const radius = Math.hypot(re, imag);
  return {
    re: Math.sqrt((radius + re) / 2),
    im: Math.sign(imag) * Math.sqrt((radius - re) / 2),
  };
}

interface Mat {
  n: number;
  re: Float64Array;
  im: Float64Array;
}

export function isHermitianNumeric(tree: ExprTree): boolean {
  try {
    const two = containsBuffer(tree);
    const cutoff = two ? 4 : 8;
    const buffer = two ? 3 : 1;
    const matrix = buildMat(tree, cutoff, buffer);
    const dagger = matDag(matrix);
    let max = 0;
    for (let i = 0; i < matrix.re.length; i++) {
      max = Math.max(max, Math.abs(matrix.re[i] - dagger.re[i]), Math.abs(matrix.im[i] - dagger.im[i]));
    }
    return max < 1e-9;
  } catch {
    return false;
  }
}

function containsBuffer(tree: ExprTree): boolean {
  if (!isRecord(tree) || typeof tree.op !== 'string') return false;
  if (tree.op === 'sym') return (tree as SymNode).name === 'b' || (tree as SymNode).name === 'bd';
  if (tree.op === 'add' || tree.op === 'mul') return (tree as AddNode).args.some(containsBuffer);
  if (tree.op === 'pow') return containsBuffer((tree as PowNode).base);
  if (tree.op === 'dag' || tree.op === 'sqrt') return containsBuffer((tree as DagNode).arg);
  return false;
}

function zeros(n: number): Mat {
  return { n, re: new Float64Array(n * n), im: new Float64Array(n * n) };
}

function eye(n: number): Mat {
  const matrix = zeros(n);
  for (let i = 0; i < n; i++) matrix.re[i * n + i] = 1;
  return matrix;
}

function matAdd(left: Mat, right: Mat): Mat {
  const out = zeros(left.n);
  for (let i = 0; i < out.re.length; i++) {
    out.re[i] = left.re[i] + right.re[i];
    out.im[i] = left.im[i] + right.im[i];
  }
  return out;
}

function matScale(matrix: Mat, re: number, imag: number): Mat {
  const out = zeros(matrix.n);
  for (let i = 0; i < out.re.length; i++) {
    out.re[i] = matrix.re[i] * re - matrix.im[i] * imag;
    out.im[i] = matrix.re[i] * imag + matrix.im[i] * re;
  }
  return out;
}

function matMul(left: Mat, right: Mat): Mat {
  const n = left.n;
  const out = zeros(n);
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < n; k++) {
      let re = 0;
      let imag = 0;
      for (let j = 0; j < n; j++) {
        const ar = left.re[i * n + j];
        const ai = left.im[i * n + j];
        const br = right.re[j * n + k];
        const bi = right.im[j * n + k];
        re += ar * br - ai * bi;
        imag += ar * bi + ai * br;
      }
      out.re[i * n + k] = re;
      out.im[i * n + k] = imag;
    }
  }
  return out;
}

function matDag(matrix: Mat): Mat {
  const n = matrix.n;
  const out = zeros(n);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      out.re[i * n + j] = matrix.re[j * n + i];
      out.im[i * n + j] = -matrix.im[j * n + i];
    }
  }
  return out;
}

function matA(memory: number, buffer: number): Mat {
  const n = memory * buffer;
  const matrix = zeros(n);
  for (let na = 1; na < memory; na++) {
    const amp = Math.sqrt(na);
    for (let nb = 0; nb < buffer; nb++) {
      const col = na * buffer + nb;
      const row = (na - 1) * buffer + nb;
      matrix.re[row * n + col] = amp;
    }
  }
  return matrix;
}

function matB(memory: number, buffer: number): Mat {
  const n = memory * buffer;
  const matrix = zeros(n);
  for (let nb = 1; nb < buffer; nb++) {
    const amp = Math.sqrt(nb);
    for (let na = 0; na < memory; na++) {
      const col = na * buffer + nb;
      const row = na * buffer + (nb - 1);
      matrix.re[row * n + col] = amp;
    }
  }
  return matrix;
}

function matN(memory: number, buffer: number): Mat {
  const n = memory * buffer;
  const matrix = zeros(n);
  for (let na = 0; na < memory; na++) {
    for (let nb = 0; nb < buffer; nb++) {
      const i = na * buffer + nb;
      matrix.re[i * n + i] = na;
    }
  }
  return matrix;
}

function buildMat(tree: ExprTree, memory: number, buffer: number): Mat {
  const n = memory * buffer;
  const a = matA(memory, buffer);
  const ad = matDag(a);
  const b = buffer > 1 ? matB(memory, buffer) : zeros(n);
  const bd = matDag(b);
  const build = (node: ExprTree): Mat => {
    switch (node.op) {
      case 'num':
        return matScale(eye(n), node.value, node.imag ?? 0);
      case 'param':
        return eye(n);
      case 'sqrt':
        if (node.arg.op === 'param') return eye(n);
        if (node.arg.op === 'num') {
          const root = sqrtComplex(node.arg.value, node.arg.imag ?? 0);
          return matScale(eye(n), root.re, root.im);
        }
        throw new Error('sqrt');
      case 'sym':
        if (node.name === 'a') return a;
        if (node.name === 'ad') return ad;
        if (node.name === 'b') return b;
        if (node.name === 'bd') return bd;
        if (node.name === 'I') return eye(n);
        if (node.name === 'n_a') return matN(memory, buffer);
        throw new Error(node.name);
      case 'add':
        return node.args.slice(1).reduce((acc, arg) => matAdd(acc, build(arg)), build(node.args[0]));
      case 'mul':
        return node.args.slice(1).reduce((acc, arg) => matMul(acc, build(arg)), build(node.args[0]));
      case 'pow': {
        if (node.exp === 0) return eye(n);
        let acc = build(node.base);
        for (let i = 1; i < node.exp; i++) acc = matMul(acc, build(node.base));
        return acc;
      }
      case 'dag':
        return matDag(build(node.arg));
      default:
        throw new Error('op');
    }
  };
  return build(tree);
}

const LATEX_PARAM: Record<string, string> = {
  g2: 'g_{2}',
  eps_d: '\\varepsilon_{d}',
  kappa_b: '\\kappa_{b}',
  kappa_a: '\\kappa_{a}',
  kappa2: '\\kappa_{2}',
  alpha: '\\alpha',
  eps_z: '\\varepsilon_{Z}',
  eps_x: '\\varepsilon_{X}',
  K: 'K',
  chi: '\\chi',
};

export function formatReal(value: number): string {
  if (!Number.isFinite(value)) throw new Error('non-finite number');
  if (value === 0) return '0';
  if (Number.isInteger(value)) return String(value);
  for (let digits = 1; digits <= 15; digits++) {
    const text = value.toFixed(digits);
    if (Number(text) === value) return trimDecimal(text);
  }
  return trimDecimal(value.toFixed(15));
}

function trimDecimal(text: string): string {
  return text.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
}

function formatComplex(re: number, imag: number): string {
  if (imag === 0) return formatReal(re);
  if (re === 0) {
    if (imag === 1) return '1j';
    if (imag === -1) return '-1j';
    return `${formatReal(imag)}j`;
  }
  const sign = imag < 0 ? '-' : '+';
  return `(${formatReal(re)}${sign}${formatReal(Math.abs(imag))}j)`;
}

function pySym(name: string): string {
  switch (name) {
    case 'a':
      return 'a';
    case 'ad':
      return 'a.dag()';
    case 'b':
      return 'b';
    case 'bd':
      return 'b.dag()';
    case 'I':
      return 'dq.eye(N)';
    case 'n_a':
      return 'a.dag()@a';
    default:
      return name;
  }
}

function lxSym(name: string): string {
  switch (name) {
    case 'a':
      return 'a';
    case 'ad':
      return 'a^{\\dagger}';
    case 'b':
      return 'b';
    case 'bd':
      return 'b^{\\dagger}';
    case 'I':
      return 'I';
    case 'n_a':
      return 'a^{\\dagger} a';
    default:
      return name;
  }
}

const DAG_SYM: Record<string, string> = {
  a: 'ad',
  ad: 'a',
  b: 'bd',
  bd: 'b',
  I: 'I',
  n_a: 'n_a',
};

function pushDag(tree: ExprTree): ExprTree {
  switch (tree.op) {
    case 'dag':
      return daggerOf(pushDag(tree.arg));
    case 'add':
    case 'mul':
      return { op: tree.op, args: tree.args.map(pushDag) };
    case 'pow':
      return { op: 'pow', base: pushDag(tree.base), exp: tree.exp };
    case 'sqrt':
      return { op: 'sqrt', arg: pushDag(tree.arg) };
    default:
      return tree;
  }
}

function daggerOf(tree: ExprTree): ExprTree {
  switch (tree.op) {
    case 'num':
      return num(tree.value, -(tree.imag ?? 0));
    case 'param':
      return tree;
    case 'sym':
      return sym(DAG_SYM[tree.name] ?? tree.name);
    case 'add':
      return { op: 'add', args: tree.args.map(daggerOf) };
    case 'mul':
      return { op: 'mul', args: [...tree.args].reverse().map(daggerOf) };
    case 'pow':
      return { op: 'pow', base: daggerOf(tree.base), exp: tree.exp };
    case 'sqrt':
      return { op: 'sqrt', arg: daggerOf(tree.arg) };
    case 'dag':
      return tree.arg;
    default:
      return tree;
  }
}

function expandPow(tree: ExprTree): ExprTree {
  switch (tree.op) {
    case 'pow': {
      const base = expandPow(tree.base);
      if (!Number.isInteger(tree.exp)) return { op: 'pow', base, exp: tree.exp };
      if (tree.exp === 0) return num(1);
      if (tree.exp === 1) return base;
      return { op: 'mul', args: Array.from({ length: tree.exp }, () => base) };
    }
    case 'add':
    case 'mul':
      return { op: tree.op, args: tree.args.map(expandPow) };
    case 'sqrt':
      return { op: 'sqrt', arg: expandPow(tree.arg) };
    default:
      return tree;
  }
}

function flattenAdd(tree: ExprTree): ExprTree[] {
  if (tree.op !== 'add') return [tree];
  return tree.args.flatMap(flattenAdd);
}

function flattenMul(tree: ExprTree): ExprTree[] {
  if (tree.op !== 'mul') return [tree];
  return tree.args.flatMap(flattenMul);
}

function isScalarTree(tree: ExprTree): boolean {
  switch (tree.op) {
    case 'num':
    case 'param':
    case 'sqrt':
      return true;
    case 'sym':
      return false;
    case 'pow':
      return isScalarTree(tree.base);
    case 'mul':
    case 'add':
      return tree.args.every(isScalarTree);
    case 'dag':
      return isScalarTree(tree.arg);
    default:
      return false;
  }
}

function splitSign(tree: ExprTree): { sign: 1 | -1; rest: ExprTree } {
  if (tree.op === 'num' && (tree.imag ?? 0) === 0 && tree.value < 0) {
    return { sign: -1, rest: num(-tree.value) };
  }
  if (tree.op === 'mul') {
    const flat = flattenMul(tree);
    let sign: 1 | -1 = 1;
    const kept: ExprTree[] = [];
    for (const factor of flat) {
      if (sign === 1 && factor.op === 'num' && (factor.imag ?? 0) === 0 && factor.value < 0) {
        sign = -1;
        if (factor.value !== -1) kept.push(num(-factor.value));
        continue;
      }
      kept.push(factor);
    }
    if (sign === -1) {
      const rest = kept.length === 0 ? num(1) : kept.length === 1 ? kept[0] : mul(...kept);
      return { sign, rest };
    }
  }
  return { sign: 1, rest: tree };
}

export function toPython(tree: ExprTree): string {
  // Match server/app/expr.py: expand integer powers, and do not cancel daggers.
  return formatTop(expandPow(tree));
}

function formatTop(tree: ExprTree): string {
  if (tree.op === 'add') return formatAdd(tree);
  const { sign, rest } = splitSign(tree);
  const body = formatSignedBody(rest);
  return sign === -1 ? `-${body}` : body;
}

function formatAdd(tree: ExprTree): string {
  const terms = flattenAdd(tree);
  if (terms.length === 0) return '0';
  let out = '';
  terms.forEach((termNode, index) => {
    const { sign, rest } = splitSign(termNode);
    const body = formatSignedBody(rest);
    if (index === 0) out += sign === -1 ? `-${body}` : body;
    else out += sign === -1 ? ` - ${body}` : ` + ${body}`;
  });
  return out;
}

function formatSignedBody(tree: ExprTree): string {
  if (tree.op === 'add') return `(${formatAdd(tree)})`;
  if (tree.op === 'mul') return formatMul(tree);
  return formatAtom(tree);
}

function formatMul(tree: ExprTree): string {
  const factors = flattenMul(tree);
  const runs: { scalar: boolean; items: ExprTree[] }[] = [];
  for (const factor of factors) {
    const scalar = isScalarTree(factor);
    const last = runs[runs.length - 1];
    if (last && last.scalar === scalar) last.items.push(factor);
    else runs.push({ scalar, items: [factor] });
  }
  const rendered = runs.map((run) => {
    if (run.scalar) return run.items.map((item) => formatAtom(item)).join('*');
    return run.items.map((item) => formatAtom(item)).join('@');
  });
  return rendered.join('*');
}

function formatDag(arg: ExprTree): string {
  if (arg.op === 'sym' && (arg.name === 'a' || arg.name === 'b')) return `${arg.name}.dag()`;
  const inner = formatAtom(arg);
  if (arg.op === 'sym' || arg.op === 'dag' || arg.op === 'param' || arg.op === 'num') return `${inner}.dag()`;
  return `(${inner}).dag()`;
}

function formatAtom(tree: ExprTree): string {
  switch (tree.op) {
    case 'add':
      return `(${formatAdd(tree)})`;
    case 'mul':
      return formatMul(tree);
    case 'sqrt':
      return `jnp.sqrt(${formatAtom(tree.arg)})`;
    case 'num':
      return formatComplex(tree.value, tree.imag ?? 0);
    case 'param':
      return tree.name;
    case 'sym':
      return pySym(tree.name);
    case 'pow': {
      if (!Number.isInteger(tree.exp)) {
        const atom = formatAtom(tree.base);
        const wrapped = atom.startsWith('(') ? atom : `(${atom})`;
        return `${wrapped}**${tree.exp}`;
      }
      const joiner = isScalarTree(tree.base) ? '*' : '@';
      if (tree.exp === 0) return isScalarTree(tree.base) ? '1' : 'dq.eye(N)';
      return Array.from({ length: tree.exp }, () => formatAtom(tree.base)).join(joiner);
    }
    case 'dag':
      return formatDag(tree.arg);
    default:
      return '?';
  }
}

export function toLatex(tree: ExprTree): string {
  const simplified = pushDag(tree);
  return simplified.op === 'add' ? latexAdd(simplified) : latexSigned(simplified);
}

function latexAdd(tree: ExprTree): string {
  const terms = flattenAdd(tree);
  if (terms.length === 0) return '0';
  let out = '';
  terms.forEach((termNode, index) => {
    const { sign, rest } = splitSign(termNode);
    const body = rest.op === 'add' ? `(${latexAdd(rest)})` : latexPiece(rest);
    if (index === 0) out += sign === -1 ? `-${body}` : body;
    else out += sign === -1 ? ` - ${body}` : ` + ${body}`;
  });
  return out;
}

function latexSigned(tree: ExprTree): string {
  const { sign, rest } = splitSign(tree);
  const body = rest.op === 'add' ? `(${latexAdd(rest)})` : latexPiece(rest);
  return sign === -1 ? `-${body}` : body;
}

function latexPiece(tree: ExprTree): string {
  if (tree.op === 'mul') return latexMul(tree);
  return latexAtom(tree);
}

function latexMul(tree: ExprTree): string {
  const factors = flattenMul(tree);
  const runs: { scalar: boolean; items: ExprTree[] }[] = [];
  for (const factor of factors) {
    const scalar = isScalarTree(factor);
    const last = runs[runs.length - 1];
    if (last && last.scalar === scalar) last.items.push(factor);
    else runs.push({ scalar, items: [factor] });
  }
  const parts = runs.map((run) => {
    if (run.scalar) return run.items.map((item) => latexAtom(item)).join('');
    return run.items.map((item) => latexAtom(item)).join(' ');
  });
  let out = '';
  for (const part of parts) {
    if (!out) {
      out = part;
      continue;
    }
    out += part.startsWith('(') ? part : ` ${part}`;
  }
  return out;
}

function latexAtom(tree: ExprTree): string {
  switch (tree.op) {
    case 'add':
      return `(${latexAdd(tree)})`;
    case 'mul':
      return latexMul(tree);
    case 'sqrt':
      return `\\sqrt{${latexAtom(tree.arg)}}`;
    case 'num':
      return formatComplex(tree.value, tree.imag ?? 0).replace(/j/g, ' i').replace('1 i', 'i').replace('-1 i', '-i');
    case 'param':
      return LATEX_PARAM[tree.name] ?? tree.name;
    case 'sym':
      return lxSym(tree.name);
    case 'pow': {
      const base = latexAtom(tree.base);
      const wrapped =
        tree.base.op === 'add' ||
        tree.base.op === 'mul' ||
        (tree.base.op === 'sym' && tree.base.name !== 'a' && tree.base.name !== 'b')
          ? `(${base})`
          : base;
      return `${wrapped}^{${tree.exp}}`;
    }
    case 'dag':
      return latexAtom(pushDag(tree));
    default:
      return '?';
  }
}

export function serializeProgram(program: { H: ExprTree; jumps: ExprTree[] }): string {
  return JSON.stringify({ H: program.H, jumps: program.jumps });
}

export function deserializeProgram(text: string): { H: ExprTree; jumps: ExprTree[] } {
  const value = JSON.parse(text) as { H?: ExprTree; jumps?: ExprTree[] };
  if (!value || typeof value !== 'object' || !value.H || !Array.isArray(value.jumps)) {
    throw new Error('program JSON must have H and jumps');
  }
  return { H: value.H, jumps: value.jumps };
}
