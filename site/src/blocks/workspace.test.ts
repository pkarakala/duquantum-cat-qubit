// @vitest-environment jsdom

import * as Blockly from 'blockly';
import { afterEach, describe, expect, it } from 'vitest';

import { BLOCK_TYPES, exprPythonGenerator } from './blocks.js';
import { deserializeProgram, serializeProgram, toPython } from './expr.js';
import { H2PH_PYTHON, PRESET_NAMES, getPreset } from './presets.js';
import { mountBlocks, type BlocksHandle } from './workspace.js';

let handle: BlocksHandle | null = null;

afterEach(() => {
  handle?.dispose();
  handle = null;
  document.body.replaceChildren();
});

describe('workspace', () => {
  it('mounts presets, serializes, and inserts from the keyboard toolbar', () => {
    const host = document.createElement('div');
    document.body.append(host);
    handle = mountBlocks(host, { modes: 'two' });
    let changes = 0;
    handle.onChange(() => {
      changes += 1;
    });
    const before = changes;
    (host.querySelector('button') as HTMLButtonElement).click();
    expect(changes).toBeGreaterThan(before);
    expect(handle.getTree().H).toEqual({ op: 'sym', name: 'a' });

    handle.loadPreset('h2ph_correct');
    const tree = handle.getTree();
    expect(tree).toEqual({ H: getPreset('h2ph_correct').H, jumps: getPreset('h2ph_correct').jumps });
    expect(toPython(tree.H)).toBe(H2PH_PYTHON);

    const xml = handle.saveXml();
    handle.loadXml(xml);
    expect(handle.getTree()).toEqual(tree);

    const state = handle.saveState();
    handle.loadPreset('empty');
    handle.loadState(state);
    expect(handle.getTree()).toEqual(tree);

    handle.loadProgram(deserializeProgram(serializeProgram(tree)));
    expect(handle.getTree()).toEqual(tree);

    const buttons = [...host.querySelectorAll('button')].map((button) => button.textContent);
    expect(buttons).toEqual(expect.arrayContaining(['a memory', 'b buffer', '√ rate', '+', '×', 'power']));
    expect(host.querySelectorAll('button').length).toBeGreaterThanOrEqual(BLOCK_TYPES.length - 2);

    expect(host.querySelector('svg')).toBeTruthy();
    expect(host.querySelectorAll('.expr-blocks-toolbar button').length).toBeGreaterThan(8);

    for (const name of PRESET_NAMES) {
      handle.loadPreset(name);
      const preset = getPreset(name);
      expect(handle.getTree()).toEqual({ H: preset.H, jumps: preset.jumps });
    }
    handle.loadPreset('h2ph_correct');
    const holder = Blockly.common.getMainWorkspace()?.getTopBlocks(false).find((block) => block.type === 'hamiltonian');
    expect(holder).toBeTruthy();
    const code = exprPythonGenerator.forBlock['hamiltonian'](
      holder as Parameters<(typeof exprPythonGenerator.forBlock)['hamiltonian']>[0],
      exprPythonGenerator,
    );
    expect(code).toBe(`${H2PH_PYTHON}\n`);
    expect(handle.keyboardNavigation).toBe(false);
  });
});
