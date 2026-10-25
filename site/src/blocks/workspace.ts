// Mounts the operator-block editor. The Blockly keyboard-navigation plugin
// 4.0.0-beta.0 does not run on Blockly 13.4.0 (it calls a removed LineCursor,
// and its toolbox registration recurses), so selection is a real button toolbar:
// Tab to a block, Enter to drop it in the first empty socket.

import * as Blockly from 'blockly';

import { BLOCK_TYPES, COLOURS, PARAM_OPTIONS, RATE_OPTIONS, registerBlocks } from './blocks.js';
import {
  adaptLive,
  compileProgram,
  programToViews,
  type BlockView,
  type LiveBlock,
  type Program,
} from './compile.js';
import { getPreset, isPresetName, type PresetName } from './presets.js';

export type { PresetName };

export interface MountOptions {
  modes: 'one' | 'two';
  initialXml?: string;
}

export interface BlocksHandle {
  getTree(): Program;
  onChange(cb: () => void): () => void;
  loadPreset(name: string): void;
  loadProgram(program: Program): void;
  saveXml(): string;
  loadXml(xml: string): void;
  saveState(): { [key: string]: unknown };
  loadState(state: { [key: string]: unknown }): void;
  insertBlock(type: string): void;
  growSelected(): void;
  shrinkSelected(): void;
  dispose(): void;
  keyboardNavigation: false;
  modes: 'one' | 'two';
}

const INSERTS: { type: string; label: string; twoOnly?: boolean }[] = [
  { type: 'op_a', label: 'a memory' },
  { type: 'op_ad', label: 'a† memory' },
  { type: 'op_n_a', label: 'n memory' },
  { type: 'op_I', label: 'I' },
  { type: 'op_b', label: 'b buffer', twoOnly: true },
  { type: 'op_bd', label: 'b† buffer', twoOnly: true },
  { type: 'param', label: 'param' },
  { type: 'num', label: 'number' },
  { type: 'sqrt_param', label: '√ rate' },
  { type: 'sqrt_num', label: '√ number' },
  { type: 'mul', label: '×' },
  { type: 'add', label: '+' },
  { type: 'pow', label: 'power' },
  { type: 'dag', label: '†' },
];

interface ShapeBlock extends Blockly.Block {
  grow?: () => void;
  shrink?: () => void;
  loadExtraState?: (state: unknown) => void;
}

export function mountBlocks(el: HTMLElement, options: MountOptions): BlocksHandle {
  registerBlocks();
  el.replaceChildren();
  el.classList.add('expr-blocks-root');

  const toolbar = document.createElement('div');
  toolbar.className = 'expr-blocks-toolbar';
  toolbar.setAttribute('role', 'toolbar');
  toolbar.setAttribute('aria-label', 'Insert an operator block');

  const surface = document.createElement('div');
  surface.className = 'expr-blocks-surface';
  surface.style.minHeight = '640px';
  surface.style.height = '640px';
  el.append(toolbar, surface);

  const workspace = Blockly.inject(surface, {
    toolbox: toolboxFor(options.modes),
    media: 'https://static.blockly.com/media/',
    trashcan: true,
    sounds: false,
    zoom: { controls: true, wheel: true, startScale: 1 },
    move: { scrollbars: true, drag: true, wheel: true },
    renderer: 'zelos',
  });

  const listeners = new Set<() => void>();
  let silent = false;
  let lastInserted: Blockly.Block | null = null;

  const reInput = numberInput('Real part of the selected number');
  const imInput = numberInput('Imaginary part of the selected number');
  const paramSelect = selectInput('Parameter on the selected block', PARAM_OPTIONS);
  const rateSelect = selectInput('Rate under the square root', RATE_OPTIONS);
  const powSelect = selectInput(
    'Power',
    ['0', '1', '2', '3', '4'].map((value) => [value, value]),
  );
  const growButton = actionButton('Add socket', () => api.growSelected());
  const shrinkButton = actionButton('Remove socket', () => api.shrinkSelected());
  toolbar.append(
    ...INSERTS.filter((item) => options.modes === 'two' || !item.twoOnly).map((item) =>
      actionButton(item.label, () => api.insertBlock(item.type)),
    ),
    growButton,
    shrinkButton,
    labeled('real', reInput),
    labeled('imag', imInput),
    labeled('param', paramSelect),
    labeled('√', rateSelect),
    labeled('power', powSelect),
  );

  reInput.addEventListener('change', () => writeField('num', 'RE', reInput.value || '0'));
  imInput.addEventListener('change', () => writeField('num', 'IM', imInput.value || '0'));
  paramSelect.addEventListener('change', () => writeField('param', 'NAME', paramSelect.value));
  rateSelect.addEventListener('change', () => writeField('sqrt_param', 'NAME', rateSelect.value));
  powSelect.addEventListener('change', () => writeField('pow', 'EXP', powSelect.value));

  workspace.addChangeListener((event: Blockly.Events.Abstract) => {
    if (event.type === 'selected') syncControls();
    if (silent || event.isUiEvent) return;
    emit();
  });

  const api: BlocksHandle = {
    keyboardNavigation: false,
    modes: options.modes,
    getTree: () =>
      compileProgram({
        hamiltonian: adaptTop('hamiltonian'),
        jumps: adaptTop('jumps'),
      }),
    onChange(cb) {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    loadPreset(name) {
      if (!isPresetName(name)) throw new Error(`unknown preset "${name}"`);
      loadProgram(getPreset(name));
    },
    loadProgram,
    saveXml() {
      return Blockly.Xml.domToPrettyText(Blockly.Xml.workspaceToDom(workspace));
    },
    loadXml(xml) {
      runSilent(() => {
        workspace.clear();
        Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(xml), workspace);
        protectHolders();
      });
    },
    saveState() {
      return Blockly.serialization.workspaces.save(workspace);
    },
    loadState(state) {
      runSilent(() => {
        workspace.clear();
        Blockly.serialization.workspaces.load(state, workspace);
        protectHolders();
      });
    },
    insertBlock(type) {
      if (!(BLOCK_TYPES as readonly string[]).includes(type)) {
        throw new Error(`unknown block "${type}"`);
      }
      const created = workspace.newBlock(type);
      const createdSvg = created as Blockly.BlockSvg;
      if (!createdSvg.rendered && typeof createdSvg.initSvg === 'function') createdSvg.initSvg();
      createdSvg.render?.(false);
      const hole = firstHole();
      if (hole?.connection && created.outputConnection) {
        hole.connection.connect(created.outputConnection);
      }
      created.select();
      lastInserted = created;
      syncControls();
      emit();
    },
    growSelected() {
      const block = selectedVariadic();
      block?.grow?.();
      emit();
    },
    shrinkSelected() {
      const block = selectedVariadic();
      block?.shrink?.();
      emit();
    },
    dispose() {
      workspace.dispose();
      el.replaceChildren();
    },
  };

  if (options.initialXml) api.loadXml(options.initialXml);
  else blank();
  return api;

  function blank(): void {
    loadProgram({ H: { op: 'num', value: 0 }, jumps: [] });
    // An empty socket is what the first keyboard insert needs. getTree reports 0 until then.
    runSilent(() => {
      const hamiltonian = workspace.getTopBlocks(false).find((block) => block.type === 'hamiltonian');
      const connection = hamiltonian?.getInput('H')?.connection;
      const child = connection?.targetBlock();
      if (child && connection) {
        connection.disconnect();
        child.dispose(false);
      }
    });
  }

  function loadProgram(program: Program): void {
    const views = programToViews(program);
    silent = true;
    try {
      workspace.clear();
      const hamiltonian = spawn(views.hamiltonian);
      const jumps = spawn(views.jumps);
      hamiltonian.setDeletable(false);
      jumps.setDeletable(false);
      place(hamiltonian, 28, 28);
      place(jumps, 28, 340);
    } finally {
      silent = false;
    }
    emit();
  }

  function spawn(view: BlockView): Blockly.Block {
    const block = workspace.newBlock(view.type) as ShapeBlock;
    if (view.extra && block.loadExtraState) block.loadExtraState(view.extra);
    for (const [name, value] of Object.entries(view.fields)) {
      if (block.getField(name)) {
        try {
          block.setFieldValue(value, name);
        } catch {
          // Dropdowns reject unknown values; the allowlist is what we write.
        }
      }
    }
    const svg = block as Blockly.BlockSvg;
    if (typeof svg.initSvg === 'function') svg.initSvg();
    for (const [name, child] of Object.entries(view.inputs)) {
      if (!child) continue;
      const childBlock = spawn(child);
      const input = block.getInput(name);
      if (input?.connection && childBlock.outputConnection) {
        input.connection.connect(childBlock.outputConnection);
      }
    }
    svg.render?.(false);
    return block;
  }

  function runSilent(fn: () => void): void {
    silent = true;
    Blockly.Events.disable();
    try {
      fn();
    } finally {
      Blockly.Events.enable();
      silent = false;
    }
    emit();
  }

  function place(block: Blockly.Block, x: number, y: number): void {
    const svg = block as Blockly.BlockSvg;
    if (typeof svg.moveBy === 'function') svg.moveBy(x, y);
  }

  function adaptTop(type: string): ReturnType<typeof adaptLive> | null {
    const block = workspace.getTopBlocks(false).find((item) => item.type === type);
    return block ? adaptLive(block as unknown as LiveBlock) : null;
  }

  function protectHolders(): void {
    for (const block of workspace.getTopBlocks(false)) {
      if (block.type === 'hamiltonian' || block.type === 'jumps') block.setDeletable(false);
    }
  }

  function firstHole(): Blockly.Input | null {
    for (const type of ['hamiltonian', 'jumps']) {
      const top = workspace.getTopBlocks(false).find((block) => block.type === type);
      if (!top) continue;
      const hole = findHole(top);
      if (hole) return hole;
    }
    return null;
  }

  function findHole(block: Blockly.Block): Blockly.Input | null {
    for (const input of block.inputList) {
      if (input.connection && !input.connection.isConnected()) return input;
    }
    for (const child of block.getChildren(false)) {
      const hole = findHole(child);
      if (hole) return hole;
    }
    return null;
  }

  function selectedVariadic(): ShapeBlock | null {
    const selected = Blockly.common.getSelected();
    if (selected && selected instanceof Blockly.Block && typeof (selected as ShapeBlock).grow === 'function') {
      return selected as ShapeBlock;
    }
    const inner = workspace
      .getTopBlocks(false)
      .find((block) => block.type === 'hamiltonian')
      ?.getInputTargetBlock('H') as ShapeBlock | null;
    if (inner && typeof inner.grow === 'function') return inner;
    const jumps = workspace.getTopBlocks(false).find((block) => block.type === 'jumps') as ShapeBlock | undefined;
    return jumps ?? null;
  }

  function writeField(type: string, name: string, value: string): void {
    const block = selectedBlock();
    if (!block || block.type !== type || !block.getField(name)) return;
    block.setFieldValue(value, name);
  }

  function selectedBlock(): Blockly.Block | null {
    const selected = Blockly.common.getSelected();
    if (selected && selected instanceof Blockly.Block) return selected;
    return lastInserted;
  }

  function syncControls(): void {
    const block = selectedBlock();
    reInput.disabled = block?.type !== 'num';
    imInput.disabled = block?.type !== 'num';
    paramSelect.disabled = block?.type !== 'param';
    rateSelect.disabled = block?.type !== 'sqrt_param';
    powSelect.disabled = block?.type !== 'pow';
    if (block?.type === 'num') {
      reInput.value = String(block.getFieldValue('RE') ?? '0');
      imInput.value = String(block.getFieldValue('IM') ?? '0');
    }
    if (block?.type === 'param') paramSelect.value = String(block.getFieldValue('NAME') ?? 'g2');
    if (block?.type === 'sqrt_param') rateSelect.value = String(block.getFieldValue('NAME') ?? 'kappa_b');
    if (block?.type === 'pow') powSelect.value = String(block.getFieldValue('EXP') ?? '2');
  }

  function emit(): void {
    for (const cb of listeners) cb();
  }
}

function toolboxFor(modes: 'one' | 'two'): Blockly.utils.toolbox.ToolboxDefinition {
  const memory = ['op_a', 'op_ad', 'op_n_a', 'op_I'];
  const buffer = ['op_b', 'op_bd'];
  const params = ['param', 'num', 'sqrt_param', 'sqrt_num'];
  const combine = ['mul', 'add', 'pow', 'dag'];
  const categories = [
    category('Memory', COLOURS.memory, memory),
    ...(modes === 'two' ? [category('Buffer', COLOURS.buffer, buffer)] : []),
    category('Rates', COLOURS.param, params),
    category('Combine', COLOURS.structure, combine),
  ];
  return { kind: 'categoryToolbox', contents: categories };
}

function category(name: string, colour: string, types: string[]) {
  return {
    kind: 'category' as const,
    name,
    colour,
    contents: types.map((type) => ({ kind: 'block' as const, type })),
  };
}

function actionButton(label: string, onClick: () => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.addEventListener('click', onClick);
  return button;
}

function numberInput(label: string): HTMLInputElement {
  const input = document.createElement('input');
  input.type = 'number';
  input.step = 'any';
  input.setAttribute('aria-label', label);
  input.disabled = true;
  return input;
}

function selectInput(label: string, options: [string, string][]): HTMLSelectElement {
  const select = document.createElement('select');
  select.setAttribute('aria-label', label);
  select.disabled = true;
  for (const [text, value] of options) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    select.append(option);
  }
  return select;
}

function labeled(text: string, control: HTMLElement): HTMLLabelElement {
  const label = document.createElement('label');
  label.append(document.createTextNode(`${text} `), control);
  return label;
}
