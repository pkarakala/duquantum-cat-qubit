import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { compileProgram, exprToBlockView, programToViews, blockToExpr } from './compile.js';
import {
  deserializeProgram,
  isHermitianNumeric,
  isHermitianSymbolic,
  mul,
  num,
  param,
  pow,
  serializeProgram,
  sqrt,
  sym,
  toLatex,
  toPython,
  validate,
  validateProgram,
  dag,
  add,
  PARAM_NAMES,
} from './expr.js';
import { parseEquation } from './parse.js';
import { H2PH_PYTHON, PRESET_NAMES, getPreset } from './presets.js';
import { detect } from './wrong-builds.js';

const h2ph = getPreset('h2ph_correct');

describe('operator blocks', () => {
  it('compile_h2ph', () => {
    const compiled = compileProgram(programToViews(h2ph));
    expect(compiled).toEqual({ H: h2ph.H, jumps: h2ph.jumps });
    expect(toPython(compiled.H)).toBe(H2PH_PYTHON);
    for (const name of PRESET_NAMES) {
      const preset = getPreset(name);
      expect(compileProgram(programToViews(preset))).toEqual({ H: preset.H, jumps: preset.jumps });
    }
  });

  it('validate_rejects', () => {
    expect(validate(sym('c'), 'one').errors).toContain('unknown symbol "c"');
    expect(validate(sym('b'), 'one').errors).toContain('symbol "b" is only allowed in two-mode');
    expect(validate(sym('bd'), 'one').errors).toContain('symbol "bd" is only allowed in two-mode');
    expect(validate(sym('b'), 'two').errors.some((error) => error.includes('only allowed'))).toBe(false);

    let deep = sym('a');
    for (let i = 0; i < 8; i++) deep = dag(deep);
    expect(validate(deep, 'one').errors).toContain('expression depth 9 exceeds 8');

    let okDepth = sym('a');
    for (let i = 0; i < 7; i++) okDepth = dag(okDepth);
    expect(validate(okDepth, 'one').errors.some((error) => error.includes('exceeds'))).toBe(false);

    const wide = add(...Array.from({ length: 64 }, () => sym('a')));
    expect(validate(wide, 'one').errors).toContain('expression has 65 nodes; limit is 64');

    expect(validate(pow(sym('a'), 5), 'one').errors).toContain('power exponent 5 is outside 0–4');
    expect(validate(sqrt(sym('a')), 'one').errors).toContain('sqrt applies only to a param or a number');
    expect(validate(mul(param('kappa_b'), sym('b')), 'two', 'jump').errors).toContain(
      'jump coefficient must be wrapped in sqrt',
    );
    expect(validate(mul(sqrt(param('kappa_b')), sym('b')), 'two', 'jump').ok).toBe(true);
    expect(validate(param('not_a_rate'), 'one').errors).toContain('unknown param "not_a_rate"');
  });

  it('to_python_matches_fixtures', () => {
    const dir = fileURLToPath(new URL('../../../server/tests/fixtures/expr/', import.meta.url));
    if (!existsSync(dir)) {
      expect(toPython(h2ph.H), 'fixtures absent; canonical h2ph string').toBe(H2PH_PYTHON);
      return;
    }
    const files = readdirSync(dir).filter((name) => name.endsWith('.json'));
    expect(files.length).toBeGreaterThan(0);
    for (const name of files) {
      const fixture = JSON.parse(readFileSync(`${dir}/${name}`, 'utf8')) as { tree: typeof h2ph.H; python: string };
      expect(toPython(fixture.tree), name).toBe(fixture.python);
    }
  });

  it('to_python_canonical', () => {
    expect(toPython(h2ph.H)).toBe('g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())');
    expect(toPython(h2ph.jumps[0])).toBe('jnp.sqrt(kappa_b)*b');
    expect(toPython(h2ph.jumps[1])).toBe('jnp.sqrt(kappa_a)*a');
    expect(toPython(getPreset('one_mode_cat').jumps[0])).toBe(
      'jnp.sqrt(kappa2)*(a@a - alpha*alpha*dq.eye(N))',
    );
    expect(toPython(getPreset('state_prep_x').H)).toBe('1j*eps_x*(a.dag() - a)');
    expect(toPython(mul(param('K'), sym('n_a')))).toBe('K*(a.dag()@a)');
    expect(toPython(num(2))).toBe('2');
    expect(toPython(num(0.5))).toBe('0.5');
    expect(toPython(num(1, 2))).toBe('(1+2j)');
    expect(toPython(getPreset('readout_z').H)).toBe(
      'g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag()) + eps_z*(a + a.dag())',
    );
  });

  it('to_latex_smoke', () => {
    const latex = toLatex(h2ph.H);
    expect(latex).toContain('a^{2} b^{\\dagger}');
    expect(latex).toContain('\\varepsilon_{d}');
    expect(latex).toContain('g_{2}');
  });

  it('hermitian', () => {
    expect(isHermitianSymbolic(h2ph.H)).toBe(true);
    expect(isHermitianNumeric(h2ph.H)).toBe(true);
    const missing = mul(param('g2'), mul(pow(sym('a'), 2), sym('bd')));
    expect(isHermitianSymbolic(missing)).toBe(false);
    expect(isHermitianNumeric(missing)).toBe(false);
    expect(toPython(missing)).toBe('g2*(a@a@b.dag())');
    expect(isHermitianSymbolic(getPreset('state_prep_x').H)).toBe(true);
    expect(isHermitianNumeric(getPreset('state_prep_x').H)).toBe(true);
    expect(isHermitianSymbolic(getPreset('wrong_conversion').H)).toBe(true);
    expect(isHermitianNumeric(getPreset('kerr').H)).toBe(true);
    expect(validate(h2ph.H, 'two').ok).toBe(true);
    expect(validateProgram(h2ph, 'two').ok).toBe(true);
    expect(validate(getPreset('wrong_missing_hc').H, 'two').ok).toBe(false);
  });

  it('wrong_builds', () => {
    expect(detect(h2ph)).toEqual([]);
    expect(detect(getPreset('readout_z')).map((finding) => finding.key)).toEqual([]);
    expect(detect(getPreset('state_prep_x')).map((finding) => finding.key)).toEqual([]);
    expect(detect(getPreset('one_mode_cat')).map((finding) => finding.key)).toEqual([]);
    expect(keys('wrong_drive_on_memory')).toEqual(['drive_on_memory_not_buffer']);
    expect(keys('wrong_no_dissipation')).toEqual(['no_dissipation']);
    expect(keys('wrong_conversion')).toEqual(['wrong_conversion']);
    expect(keys('wrong_missing_hc')).toEqual(['missing_hc']);
    const drive = detect(getPreset('wrong_drive_on_memory'))[0];
    expect(drive.message).toBe("this pushes along the ridge between the wells, so it can't make a cat");
    expect(detect(getPreset('wrong_no_dissipation'))[0].misconception).toBe('M3');
  });

  it('parse_roundtrip', () => {
    const cases: Array<[string, string]> = [
      [
        'g2*(a^2*bd + ad^2*b) - eps_d*(b+bd)',
        'g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())',
      ],
      ['1j*eps_x*(ad - a)', '1j*eps_x*(a.dag() - a)'],
      ['sqrt(kappa2)*(a^2 - alpha^2*I)', 'jnp.sqrt(kappa2)*(a@a - alpha*alpha*dq.eye(N))'],
      ['dag(a)', 'a.dag()'],
      ['g2*a^2*bd', 'g2*(a@a@b.dag())'],
    ];
    for (const [input, python] of cases) {
      expect(toPython(parseEquation(input).H), input).toBe(python);
    }
    const dissipated = parseEquation('g2*a^2*bd + D[sqrt(kappa_b)*b]');
    expect(toPython(dissipated.H)).toBe('g2*(a@a@b.dag())');
    expect(toPython(dissipated.jumps[0])).toBe('jnp.sqrt(kappa_b)*b');
    expect(toPython(parseEquation(toPython(h2ph.H)).H)).toBe(toPython(h2ph.H));
    expect(toPython(parseEquation('a.dag()').H)).toBe('a.dag()');
    expect(toPython(parseEquation('jnp.sqrt(kappa_a)*a').H)).toBe('jnp.sqrt(kappa_a)*a');
  });

  it('serialization_round_trip', () => {
    const text = serializeProgram(h2ph);
    expect(deserializeProgram(text)).toEqual({ H: h2ph.H, jumps: h2ph.jumps });
    expect(text.includes('eval')).toBe(false);
    for (const name of PARAM_NAMES) {
      expect(blockToExpr({ type: 'param', fields: { NAME: name }, inputs: {} })).toEqual(param(name));
    }
    expect(exprToBlockView(sym('bd')).type).toBe('op_bd');
  });
});

function keys(name: string): string[] {
  return detect(getPreset(name)).map((finding) => finding.key);
}
