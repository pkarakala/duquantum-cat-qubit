// Block graph ↔ ExprTree. Blockly objects are adapted to BlockView so the
// compiler can be tested without the Blockly runtime.

import type { ExprTree } from './expr.js';
import { mul, num } from './expr.js';

export interface BlockView {
  type: string;
  fields: Record<string, string>;
  inputs: Record<string, BlockView | null>;
  extra?: Record<string, unknown>;
}

export interface LiveBlock {
  type: string;
  inputList: Array<{
    name: string;
    connection: { targetBlock(): LiveBlock | null } | null;
    fieldRow: Array<{ name?: string; getValue(): unknown }>;
  }>;
  saveExtraState?: (doFullSerialization?: boolean) => unknown;
}

export interface Program {
  H: ExprTree;
  jumps: ExprTree[];
}

export function adaptLive(block: LiveBlock): BlockView {
  const fields: Record<string, string> = {};
  const inputs: Record<string, BlockView | null> = {};
  for (const input of block.inputList) {
    for (const field of input.fieldRow) {
      if (field.name) fields[field.name] = String(field.getValue());
    }
    if (input.connection) {
      const child = input.connection.targetBlock();
      inputs[input.name] = child ? adaptLive(child) : null;
    }
  }
  const extra = block.saveExtraState?.();
  if (extra && typeof extra === 'object') {
    const state = extra as { count?: number; signs?: string[] };
    if (state.count !== undefined) fields.COUNT = String(state.count);
    state.signs?.forEach((sign, index) => {
      if (!fields[`SIGN${index}`]) fields[`SIGN${index}`] = sign;
    });
  }
  return {
    type: block.type,
    fields,
    inputs,
    extra: extra && typeof extra === 'object' ? (extra as Record<string, unknown>) : undefined,
  };
}

export function blockToExpr(block: BlockView | null): ExprTree {
  if (!block) return num(0);
  switch (block.type) {
    case 'op_a':
      return { op: 'sym', name: 'a' };
    case 'op_ad':
      return { op: 'sym', name: 'ad' };
    case 'op_b':
      return { op: 'sym', name: 'b' };
    case 'op_bd':
      return { op: 'sym', name: 'bd' };
    case 'op_n_a':
      return { op: 'sym', name: 'n_a' };
    case 'op_I':
      return { op: 'sym', name: 'I' };
    case 'num': {
      const value = Number(block.fields.RE ?? block.fields.NUM ?? 0);
      const imag = Number(block.fields.IM ?? 0);
      return imag === 0 ? { op: 'num', value } : { op: 'num', value, imag };
    }
    case 'param':
      return { op: 'param', name: block.fields.NAME ?? 'g2' };
    case 'sqrt_param':
      return { op: 'sqrt', arg: { op: 'param', name: block.fields.NAME ?? 'kappa_b' } };
    case 'sqrt_num': {
      const value = Number(block.fields.RE ?? 0);
      const imag = Number(block.fields.IM ?? 0);
      const arg = imag === 0 ? { op: 'num' as const, value } : { op: 'num' as const, value, imag };
      return { op: 'sqrt', arg };
    }
    case 'pow': {
      const exp = Number(block.fields.EXP ?? 2);
      return { op: 'pow', base: blockToExpr(block.inputs.BASE ?? null), exp };
    }
    case 'dag':
      return { op: 'dag', arg: blockToExpr(block.inputs.ARG ?? null) };
    case 'mul':
      return joinSlots(block, 'MUL', false);
    case 'add':
      return joinSlots(block, 'ADD', true);
    case 'hamiltonian':
      return blockToExpr(block.inputs.H ?? null);
    default:
      return num(0);
  }
}

function joinSlots(block: BlockView, prefix: string, signed: boolean): ExprTree {
  const count = slotCount(block, prefix);
  const args: ExprTree[] = [];
  for (let i = 0; i < count; i++) {
    const child = block.inputs[`${prefix}${i}`];
    if (!child) continue;
    let expr = blockToExpr(child);
    if (signed && block.fields[`SIGN${i}`] === '-') expr = applyMinus(expr);
    args.push(expr);
  }
  if (args.length === 0) return num(prefix === 'MUL' ? 1 : 0);
  if (args.length === 1) return args[0];
  return prefix === 'MUL' ? { op: 'mul', args } : { op: 'add', args };
}

function slotCount(block: BlockView, prefix: string): number {
  if (block.fields.COUNT !== undefined && block.fields.COUNT !== '') return Number(block.fields.COUNT);
  let count = 0;
  while (`${prefix}${count}` in block.inputs) count++;
  return count;
}

function applyMinus(expr: ExprTree): ExprTree {
  if (expr.op === 'num' && (expr.imag ?? 0) === 0) return num(-expr.value);
  if (expr.op === 'mul') return mul(num(-1), ...expr.args);
  return mul(num(-1), expr);
}

export function exprToBlockView(tree: ExprTree): BlockView {
  switch (tree.op) {
    case 'sym':
      return { type: symBlock(tree.name), fields: {}, inputs: {} };
    case 'param':
      return { type: 'param', fields: { NAME: tree.name }, inputs: {} };
    case 'num':
      return {
        type: 'num',
        fields: { RE: String(tree.value), IM: String(tree.imag ?? 0) },
        inputs: {},
      };
    case 'sqrt':
      if (tree.arg.op === 'param') {
        return { type: 'sqrt_param', fields: { NAME: tree.arg.name }, inputs: {} };
      }
      if (tree.arg.op === 'num') {
        return {
          type: 'sqrt_num',
          fields: { RE: String(tree.arg.value), IM: String(tree.arg.imag ?? 0) },
          inputs: {},
        };
      }
      return { type: 'sqrt_num', fields: { RE: '0', IM: '0' }, inputs: {} };
    case 'pow':
      return {
        type: 'pow',
        fields: { EXP: String(tree.exp) },
        inputs: { BASE: exprToBlockView(tree.base) },
      };
    case 'dag':
      return { type: 'dag', fields: {}, inputs: { ARG: exprToBlockView(tree.arg) } };
    case 'mul':
      return variadicView('mul', 'MUL', tree.args, false);
    case 'add':
      return variadicView('add', 'ADD', tree.args, true);
    default:
      return { type: 'num', fields: { RE: '0', IM: '0' }, inputs: {} };
  }
}

function symBlock(name: string): string {
  switch (name) {
    case 'a':
      return 'op_a';
    case 'ad':
      return 'op_ad';
    case 'b':
      return 'op_b';
    case 'bd':
      return 'op_bd';
    case 'n_a':
      return 'op_n_a';
    case 'I':
      return 'op_I';
    default:
      return 'op_a';
  }
}

function peelSign(tree: ExprTree): { sign: '+' | '-'; expr: ExprTree } {
  if (tree.op === 'num' && (tree.imag ?? 0) === 0 && tree.value < 0) {
    return { sign: '-', expr: num(-tree.value) };
  }
  if (tree.op === 'mul' && tree.args[0]?.op === 'num' && (tree.args[0].imag ?? 0) === 0 && tree.args[0].value === -1) {
    const rest = tree.args.slice(1);
    const expr = rest.length === 1 ? rest[0] : mul(...rest);
    return { sign: '-', expr };
  }
  return { sign: '+', expr: tree };
}

function variadicView(type: string, prefix: string, args: ExprTree[], signed: boolean): BlockView {
  const fields: Record<string, string> = { COUNT: String(args.length) };
  const inputs: Record<string, BlockView | null> = {};
  const signs: string[] = [];
  args.forEach((arg, index) => {
    const peeled = signed ? peelSign(arg) : { sign: '+' as const, expr: arg };
    if (signed) {
      signs.push(peeled.sign);
      fields[`SIGN${index}`] = peeled.sign;
    }
    inputs[`${prefix}${index}`] = exprToBlockView(peeled.expr);
  });
  return {
    type,
    fields,
    inputs,
    extra: signed ? { count: args.length, signs } : { count: args.length },
  };
}

export function programToViews(program: Program): { hamiltonian: BlockView; jumps: BlockView } {
  const inputs: Record<string, BlockView | null> = {};
  program.jumps.forEach((jump, index) => {
    inputs[`J${index}`] = exprToBlockView(jump);
  });
  return {
    hamiltonian: {
      type: 'hamiltonian',
      fields: {},
      inputs: { H: exprToBlockView(program.H) },
    },
    jumps: {
      type: 'jumps',
      fields: { COUNT: String(program.jumps.length) },
      inputs,
      extra: { count: program.jumps.length },
    },
  };
}

export function compileProgram(roots: {
  hamiltonian: BlockView | null;
  jumps: BlockView | null;
}): Program {
  const H = roots.hamiltonian ? blockToExpr(roots.hamiltonian) : num(0);
  const jumps: ExprTree[] = [];
  if (roots.jumps) {
    const count = slotCount(roots.jumps, 'J');
    for (let i = 0; i < count; i++) {
      const child = roots.jumps.inputs[`J${i}`];
      if (child) jumps.push(blockToExpr(child));
    }
  }
  return { H, jumps };
}
