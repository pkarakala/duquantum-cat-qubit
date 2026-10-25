// Typed equation line. Pratt parser for the learner dialect and for the
// dynamiqs snippet toPython prints, so a shown program can be pasted back.
// D[L] is a dissipator and becomes a jump. Nothing is eval'd.

import { PARAM_NAMES, SYM_NAMES, dag, num, sym, type ExprTree } from './expr.js';

const SYMS = new Set<string>(SYM_NAMES);
const PARAMS = new Set<string>(PARAM_NAMES);

export interface ParsedEquation {
  H: ExprTree;
  jumps: ExprTree[];
}

interface Part {
  h: ExprTree | null;
  jumps: ExprTree[];
}

type Tok =
  | { k: 'num'; re: number; im: number }
  | { k: 'id'; v: string }
  | { k: 'op'; v: string }
  | { k: 'eof' };

export function parseEquation(input: string): ParsedEquation {
  const parser = new Parser(lex(input.trim()));
  const part = parser.parseExpr(0);
  parser.expectEof();
  return { H: part.h ?? num(0), jumps: part.jumps };
}

function lex(input: string): Tok[] {
  const out: Tok[] = [];
  let i = 0;
  while (i < input.length) {
    const ch = input[i];
    if (/\s/.test(ch)) {
      i++;
      continue;
    }
    if (ch === '.' && /[0-9]/.test(input[i + 1] ?? '')) {
      out.push(readNumber(input, i).tok);
      i = readNumber(input, i).next;
      continue;
    }
    if ('+-*^@()[],.'.includes(ch)) {
      out.push({ k: 'op', v: ch });
      i++;
      continue;
    }
    if (/[0-9]/.test(ch)) {
      const read = readNumber(input, i);
      out.push(read.tok);
      i = read.next;
      continue;
    }
    if (/[A-Za-z_]/.test(ch)) {
      let j = i + 1;
      while (j < input.length && /[A-Za-z0-9_]/.test(input[j])) j++;
      out.push({ k: 'id', v: input.slice(i, j) });
      i = j;
      continue;
    }
    throw new Error(`unexpected character "${ch}"`);
  }
  out.push({ k: 'eof' });
  return out;
}

function readNumber(input: string, start: number): { tok: Tok; next: number } {
  let j = start;
  if (input[j] === '.') j++;
  while (j < input.length && /[0-9]/.test(input[j])) j++;
  if (input[j] === '.' && input[start] !== '.') {
    j++;
    while (j < input.length && /[0-9]/.test(input[j])) j++;
  }
  let re = Number(input.slice(start, j));
  let im = 0;
  if (input[j] === 'j') {
    im = re;
    re = 0;
    j++;
  }
  if (!Number.isFinite(re) || !Number.isFinite(im)) throw new Error('bad number');
  return { tok: { k: 'num', re, im }, next: j };
}

class Parser {
  private index = 0;

  constructor(private readonly tokens: Tok[]) {}

  parseExpr(min: number): Part {
    let left = this.nud();
    while (this.lbp(this.peek()) > min) left = this.led(left);
    return left;
  }

  expectEof(): void {
    if (this.peek().k !== 'eof') throw new Error(`unexpected ${this.describe(this.peek())}`);
  }

  private nud(): Part {
    const tok = this.peek();
    if (tok.k === 'num') {
      this.next();
      return this.postfix({ h: num(tok.re, tok.im), jumps: [] });
    }
    if (tok.k === 'id') {
      this.next();
      return this.postfix(this.ident(tok.v));
    }
    if (tok.k === 'op' && tok.v === '(') {
      this.next();
      const inner = this.parseExpr(0);
      this.expectOp(')');
      return this.postfix(inner);
    }
    if (tok.k === 'op' && (tok.v === '-' || tok.v === '+')) {
      this.next();
      const operand = this.parseExpr(15);
      return tok.v === '-' ? this.negate(operand) : operand;
    }
    throw new Error(`expected an expression, got ${this.describe(tok)}`);
  }

  private led(left: Part): Part {
    const tok = this.peek();
    if (tok.k === 'op' && (tok.v === '+' || tok.v === '-')) {
      this.next();
      const right = this.parseExpr(10);
      return this.add(left, right, tok.v === '-');
    }
    if (tok.k === 'op' && (tok.v === '*' || tok.v === '@')) {
      this.next();
      const right = this.parseExpr(20);
      return this.product(left, right);
    }
    if (tok.k === 'op' && tok.v === '^') {
      this.next();
      const right = this.parseExpr(29);
      return this.power(left, right);
    }
    throw new Error(`expected an operator, got ${this.describe(tok)}`);
  }

  private ident(name: string): Part {
    if (name === 'dag' && this.peekOp('(')) {
      this.expectOp('(');
      const inner = this.parseExpr(0);
      this.expectOp(')');
      return { h: dag(this.mustH(inner)), jumps: [] };
    }
    if (name === 'sqrt' && this.peekOp('(')) {
      this.expectOp('(');
      const inner = this.parseExpr(0);
      this.expectOp(')');
      return { h: { op: 'sqrt', arg: this.mustH(inner) }, jumps: [] };
    }
    if (name === 'D' && this.peekOp('[')) {
      this.expectOp('[');
      const inner = this.parseExpr(0);
      this.expectOp(']');
      if (inner.jumps.length) throw new Error('D[...] cannot contain another dissipator');
      return { h: null, jumps: [this.mustH(inner)] };
    }
    if (this.peekOp('.') && this.lookaheadId() === 'sqrt' && name === 'jnp') {
      this.expectOp('.');
      this.expectId('sqrt');
      this.expectOp('(');
      const inner = this.parseExpr(0);
      this.expectOp(')');
      return { h: { op: 'sqrt', arg: this.mustH(inner) }, jumps: [] };
    }
    if (this.peekOp('.') && this.lookaheadId() === 'eye' && name === 'dq') {
      this.expectOp('.');
      this.expectId('eye');
      this.expectOp('(');
      this.parseExpr(0);
      this.expectOp(')');
      return { h: sym('I'), jumps: [] };
    }
    if (SYMS.has(name)) return { h: sym(name), jumps: [] };
    if (PARAMS.has(name)) return { h: { op: 'param', name }, jumps: [] };
    throw new Error(`unknown name "${name}"`);
  }

  private postfix(part: Part): Part {
    if (!part.h || part.jumps.length) return part;
    let expr = part.h;
    while (this.peekOp('.') && this.lookaheadId() === 'dag') {
      this.expectOp('.');
      this.expectId('dag');
      this.expectOp('(');
      this.expectOp(')');
      expr = dag(expr);
    }
    return { h: expr, jumps: [] };
  }

  private add(left: Part, right: Part, subtract: boolean): Part {
    const jumps = [...left.jumps, ...right.jumps];
    const rightH = right.h ? (subtract ? negateTree(right.h) : right.h) : null;
    let h: ExprTree | null = null;
    if (left.h && rightH) h = { op: 'add', args: [left.h, rightH] };
    else h = left.h ?? rightH;
    return { h, jumps };
  }

  private negate(part: Part): Part {
    if (part.jumps.length) throw new Error('D[...] cannot be negated; D[L] = D[-L] already');
    return { h: part.h ? negateTree(part.h) : null, jumps: [] };
  }

  private product(left: Part, right: Part): Part {
    if (left.jumps.length || right.jumps.length) {
      throw new Error('D[...] must be added, not multiplied');
    }
    return { h: { op: 'mul', args: [this.mustH(left), this.mustH(right)] }, jumps: [] };
  }

  private power(base: Part, exp: Part): Part {
    if (base.jumps.length || exp.jumps.length) throw new Error('cannot exponentiate D[...]');
    const expTree = this.mustH(exp);
    if (expTree.op !== 'num' || (expTree.imag ?? 0) !== 0 || !Number.isInteger(expTree.value)) {
      throw new Error('exponent must be an integer');
    }
    return { h: { op: 'pow', base: this.mustH(base), exp: expTree.value }, jumps: [] };
  }

  private mustH(part: Part): ExprTree {
    if (!part.h) throw new Error('expected an operator expression');
    if (part.jumps.length) throw new Error('D[...] cannot be nested inside an operator');
    return part.h;
  }

  private lbp(tok: Tok): number {
    if (tok.k !== 'op') return 0;
    if (tok.v === '+' || tok.v === '-') return 10;
    if (tok.v === '*' || tok.v === '@') return 20;
    if (tok.v === '^') return 30;
    return 0;
  }

  private peek(): Tok {
    return this.tokens[this.index] ?? { k: 'eof' };
  }

  private next(): Tok {
    return this.tokens[this.index++] ?? { k: 'eof' };
  }

  private peekOp(value: string): boolean {
    const tok = this.peek();
    return tok.k === 'op' && tok.v === value;
  }

  private lookaheadId(): string | null {
    const tok = this.tokens[this.index + 1];
    return tok && tok.k === 'id' ? tok.v : null;
  }

  private expectOp(value: string): void {
    const tok = this.next();
    if (tok.k !== 'op' || tok.v !== value) throw new Error(`expected "${value}"`);
  }

  private expectId(value: string): void {
    const tok = this.next();
    if (tok.k !== 'id' || tok.v !== value) throw new Error(`expected "${value}"`);
  }

  private describe(tok: Tok): string {
    if (tok.k === 'eof') return 'end of input';
    if (tok.k === 'id') return tok.v;
    if (tok.k === 'op') return tok.v;
    return 'number';
  }
}

function negateTree(tree: ExprTree): ExprTree {
  if (tree.op === 'mul') return { op: 'mul', args: [num(-1), ...tree.args] };
  return { op: 'mul', args: [num(-1), tree] };
}
