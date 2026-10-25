// Operator blocks. Memory, buffer and parameters use different Okabe–Ito hues,
// and every block also says what it is, so colour is not the only cue.
// a²b† is the two-photon exchange; ε(a+a†) is not a preparation drive.

import * as Blockly from 'blockly';

import { adaptLive, blockToExpr, type LiveBlock } from './compile.js';
import { toPython } from './expr.js';

export const COLOURS = {
  memory: '#0072B2',
  buffer: '#D55E00',
  param: '#009E73',
  structure: '#56B4E9',
  holder: '#332288',
  jump: '#CC79A7',
} as const;

export const BLOCK_TYPES = [
  'op_a',
  'op_ad',
  'op_b',
  'op_bd',
  'op_n_a',
  'op_I',
  'num',
  'param',
  'sqrt_param',
  'sqrt_num',
  'mul',
  'add',
  'pow',
  'dag',
  'hamiltonian',
  'jumps',
] as const;

export const PARAM_OPTIONS: [string, string][] = [
  ['g₂', 'g2'],
  ['ε_d', 'eps_d'],
  ['κ_b', 'kappa_b'],
  ['κ_a', 'kappa_a'],
  ['κ₂', 'kappa2'],
  ['α', 'alpha'],
  ['ε_Z', 'eps_z'],
  ['ε_X', 'eps_x'],
  ['K', 'K'],
  ['χ', 'chi'],
];

export const RATE_OPTIONS: [string, string][] = [
  ['κ_b', 'kappa_b'],
  ['κ_a', 'kappa_a'],
  ['κ₂', 'kappa2'],
];

export const BLOCK_JSON = [
  {
    type: 'op_a',
    message0: 'a  memory',
    output: 'Expr',
    tooltip: 'Memory annihilation a. One memory photon out.',
    extensions: ['colour_memory'],
  },
  {
    type: 'op_ad',
    message0: 'a†  memory',
    output: 'Expr',
    tooltip: 'Memory creation a†.',
    extensions: ['colour_memory'],
  },
  {
    type: 'op_n_a',
    message0: 'n  memory',
    output: 'Expr',
    tooltip: 'Memory photon number n = a†a. Kerr is K·n.',
    extensions: ['colour_memory'],
  },
  {
    type: 'op_I',
    message0: 'I  identity',
    output: 'Expr',
    tooltip: 'Identity. Use it in √κ₂(a² − α² I).',
    extensions: ['colour_memory'],
  },
  {
    type: 'op_b',
    message0: 'b  buffer',
    output: 'Expr',
    tooltip: 'Buffer annihilation b. Buffer loss is √κ_b·b.',
    extensions: ['colour_buffer'],
  },
  {
    type: 'op_bd',
    message0: 'b†  buffer',
    output: 'Expr',
    tooltip: 'Buffer creation b†. a²b† swaps two memory photons for one buffer photon.',
    extensions: ['colour_buffer'],
  },
] as const;

const PLUS =
  'data:image/svg+xml,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"><rect width="18" height="18" rx="3" fill="#222"/><path d="M8 3h2v12H8zM3 8h12v2H3z" fill="#fff"/></svg>',
  );
const MINUS =
  'data:image/svg+xml,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"><rect width="18" height="18" rx="3" fill="#222"/><path d="M3 8h12v2H3z" fill="#fff"/></svg>',
  );

interface ShapeBlock extends Blockly.Block {
  itemCount_: number;
  signs_: string[];
  prefix_: string;
  signed_: boolean;
  minCount_: number;
  grow: () => void;
  shrink: () => void;
  updateShape_: () => void;
  loadExtraState: (state: { count?: number; signs?: string[] }) => void;
  saveExtraState: () => { count: number; signs?: string[] };
}

const registered = { done: false };

export function registerBlocks(): void {
  if (registered.done) return;
  registered.done = true;
  registerColour('colour_memory', COLOURS.memory);
  registerColour('colour_buffer', COLOURS.buffer);
  registerColour('colour_param', COLOURS.param);
  registerColour('colour_structure', COLOURS.structure);
  Blockly.common.defineBlocksWithJsonArray([...BLOCK_JSON]);
  defineNumber();
  defineParam();
  defineSqrtParam();
  defineSqrtNum();
  definePow();
  defineDag();
  defineVariadic('add', 'ADD', true, 2, COLOURS.structure, 'Sum. Set a term to − for the buffer-drive minus.');
  defineVariadic('mul', 'MUL', false, 2, COLOURS.structure, 'Product, left to right. a and a† do not commute.');
  defineHolders();
  registerGenerator();
}

function registerColour(name: string, colour: string): void {
  if (Blockly.Extensions.isRegistered(name)) return;
  Blockly.Extensions.register(name, function (this: Blockly.Block) {
    this.setColour(colour);
  });
}

function defineNumber(): void {
  Blockly.Blocks['num'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('number')
        .appendField(new Blockly.FieldNumber(0), 'RE')
        .appendField('+')
        .appendField(new Blockly.FieldNumber(0), 'IM')
        .appendField('i');
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.param);
      this.setInputsInline(true);
      this.setTooltip('Complex number. 0 + 1 i is the factor in the real-axis drive i(a† − a).');
    },
  };
}

function defineParam(): void {
  Blockly.Blocks['param'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('param')
        .appendField(new Blockly.FieldDropdown(PARAM_OPTIONS), 'NAME');
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.param);
      this.setInputsInline(true);
      this.setTooltip('A rate or scale from the allowlist. Values stay in rad/µs on the server.');
    },
  };
}

function defineSqrtParam(): void {
  Blockly.Blocks['sqrt_param'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('√')
        .appendField(new Blockly.FieldDropdown(RATE_OPTIONS), 'NAME');
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.jump);
      this.setInputsInline(true);
      this.setTooltip('Jump coefficient. A rate only enters a jump under a square root.');
    },
  };
}

function defineSqrtNum(): void {
  Blockly.Blocks['sqrt_num'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput()
        .appendField('√ number')
        .appendField(new Blockly.FieldNumber(1), 'RE')
        .appendField('+')
        .appendField(new Blockly.FieldNumber(0), 'IM')
        .appendField('i');
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.jump);
      this.setInputsInline(true);
      this.setTooltip('Square root of a number. sqrt is only legal on a number or a parameter.');
    },
  };
}

function definePow(): void {
  Blockly.Blocks['pow'] = {
    init(this: Blockly.Block) {
      this.appendValueInput('BASE')
        .setCheck('Expr')
        .appendField('power')
        .appendField(
          new Blockly.FieldDropdown([
            ['2', '2'],
            ['3', '3'],
            ['4', '4'],
            ['1', '1'],
            ['0', '0'],
          ]),
          'EXP',
        );
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.structure);
      this.setInputsInline(true);
      this.setTooltip('Integer power 0–4. a² is two memory photons. The printer expands it to a@a.');
    },
  };
}

function defineDag(): void {
  Blockly.Blocks['dag'] = {
    init(this: Blockly.Block) {
      this.appendValueInput('ARG').setCheck('Expr').appendField('†');
      this.setOutput(true, 'Expr');
      this.setColour(COLOURS.structure);
      this.setInputsInline(true);
      this.setTooltip('Dagger. (XYZ)† = Z† Y† X†.');
    },
  };
}

function defineVariadic(
  type: string,
  prefix: string,
  signed: boolean,
  minCount: number,
  colour: string,
  tooltip: string,
): void {
  Blockly.Blocks[type] = {
    init(this: ShapeBlock) {
      this.prefix_ = prefix;
      this.signed_ = signed;
      this.minCount_ = minCount;
      this.itemCount_ = Math.max(minCount, 2);
      this.signs_ = Array.from({ length: this.itemCount_ }, () => '+');
      this.setOutput(true, 'Expr');
      this.setColour(colour);
      this.setTooltip(tooltip);
      this.setInputsInline(true);
      this.updateShape_();
    },
    saveExtraState(this: ShapeBlock) {
      return { count: this.itemCount_, signs: this.signs_.slice(0, this.itemCount_) };
    },
    loadExtraState(this: ShapeBlock, state: { count?: number; signs?: string[] }) {
      this.itemCount_ = Math.max(this.minCount_, Number(state?.count ?? this.itemCount_));
      this.signs_ = Array.from({ length: this.itemCount_ }, (_, i) => state?.signs?.[i] ?? '+');
      this.updateShape_();
    },
    grow(this: ShapeBlock) {
      this.itemCount_ += 1;
      this.signs_.push('+');
      this.updateShape_();
    },
    shrink(this: ShapeBlock) {
      if (this.itemCount_ <= this.minCount_) return;
      this.itemCount_ -= 1;
      this.signs_.pop();
      this.updateShape_();
    },
    updateShape_(this: ShapeBlock) {
      if (this.getInput('BUTTONS')) this.removeInput('BUTTONS');
      for (let i = 0; i < this.itemCount_; i++) {
        const name = this.prefix_ + i;
        if (!this.getInput(name)) {
          const input = this.appendValueInput(name).setCheck('Expr');
          if (this.signed_) {
            input.appendField(new Blockly.FieldDropdown([['+', '+'], ['−', '-']]), `SIGN${i}`);
          }
        }
        if (this.signed_ && this.getField(`SIGN${i}`)) {
          try {
            this.setFieldValue(this.signs_[i] || '+', `SIGN${i}`);
          } catch {
            // The field can reject a value before the block is on a rendered workspace.
          }
        }
      }
      let extra = this.itemCount_;
      while (this.getInput(this.prefix_ + extra)) {
        this.removeInput(this.prefix_ + extra);
        extra += 1;
      }
      const buttons = this.appendDummyInput('BUTTONS');
      buttons.appendField(new Blockly.FieldImage(PLUS, 18, 18, 'Add input', () => this.grow()));
      if (this.itemCount_ > this.minCount_) {
        buttons.appendField(new Blockly.FieldImage(MINUS, 18, 18, 'Remove input', () => this.shrink()));
      }
    },
  };
}

function defineHolders(): void {
  Blockly.Blocks['hamiltonian'] = {
    init(this: Blockly.Block) {
      this.appendDummyInput('TITLE').appendField('H =');
      this.appendValueInput('H').setCheck('Expr');
      this.setColour(COLOURS.holder);
      this.setInputsInline(true);
      this.setTooltip('Hamiltonian. It has to equal its own dagger, or the server will reject it.');
    },
  };
  Blockly.Blocks['jumps'] = {
    init(this: ShapeBlock) {
      this.prefix_ = 'J';
      this.signed_ = false;
      this.minCount_ = 0;
      this.itemCount_ = 2;
      this.signs_ = [];
      this.appendDummyInput('TITLE').appendField('Jumps');
      this.setColour(COLOURS.jump);
      this.setTooltip('Jump list. Each rate is wrapped in √. Buffer loss √κ_b·b is what lets pairs leave.');
      this.setInputsInline(true);
      this.updateShape_();
    },
    saveExtraState(this: ShapeBlock) {
      return { count: this.itemCount_ };
    },
    loadExtraState(this: ShapeBlock, state: { count?: number }) {
      this.itemCount_ = Math.max(0, Number(state?.count ?? 0));
      this.updateShape_();
    },
    grow(this: ShapeBlock) {
      this.itemCount_ += 1;
      this.updateShape_();
    },
    shrink(this: ShapeBlock) {
      if (this.itemCount_ <= 0) return;
      this.itemCount_ -= 1;
      this.updateShape_();
    },
    updateShape_(this: ShapeBlock) {
      if (this.getInput('BUTTONS')) this.removeInput('BUTTONS');
      for (let i = 0; i < this.itemCount_; i++) {
        const name = `J${i}`;
        if (!this.getInput(name)) this.appendValueInput(name).setCheck('Expr');
      }
      let extra = this.itemCount_;
      while (this.getInput(`J${extra}`)) {
        this.removeInput(`J${extra}`);
        extra += 1;
      }
      const buttons = this.appendDummyInput('BUTTONS');
      buttons.appendField(new Blockly.FieldImage(PLUS, 18, 18, 'Add jump', () => this.grow()));
      if (this.itemCount_ > 0) {
        buttons.appendField(new Blockly.FieldImage(MINUS, 18, 18, 'Remove jump', () => this.shrink()));
      }
    },
  };
}

export const exprPythonGenerator = new Blockly.CodeGenerator('ExprPython');

function registerGenerator(): void {
  for (const type of BLOCK_TYPES) {
    exprPythonGenerator.forBlock[type] = (block) => {
      if (block.type === 'jumps') return '';
      const code = toPython(blockToExpr(adaptLive(block as unknown as LiveBlock)));
      if (block.type === 'hamiltonian') return `${code}\n`;
      return [code, 0];
    };
  }
}

registerBlocks();
