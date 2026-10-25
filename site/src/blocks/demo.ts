import { serializeProgram, toLatex, toPython, validateProgram } from './expr.js';
import { PRESET_NAMES, getPreset, type PresetName } from './presets.js';
import { detect } from './wrong-builds.js';
import { mountBlocks, type BlocksHandle } from './workspace.js';

const editor = document.querySelector<HTMLElement>('#editor')!;
const latex = document.querySelector<HTMLElement>('#latex')!;
const python = document.querySelector<HTMLElement>('#python')!;
const json = document.querySelector<HTMLElement>('#json')!;
const checks = document.querySelector<HTMLElement>('#checks')!;
const presets = document.querySelector<HTMLElement>('#presets')!;
const modes = document.querySelector<HTMLSelectElement>('#modes')!;
const reload = document.querySelector<HTMLButtonElement>('#reload')!;

let current: BlocksHandle | null = null;

for (const name of PRESET_NAMES) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = name.replaceAll('_', ' ');
  button.addEventListener('click', () => load(name));
  presets.append(button);
}

modes.addEventListener('change', () => {
  const mode = modes.value === 'one' ? 'one' : 'two';
  remount(mode);
  current?.loadPreset(mode === 'two' ? 'h2ph_correct' : 'one_mode_cat');
});

reload.addEventListener('click', () => {
  if (!current) return;
  current.loadProgram(JSON.parse(json.textContent || '{}'));
});

remount('two');
current?.loadPreset('h2ph_correct');

function remount(mode: 'one' | 'two'): void {
  current?.dispose();
  current = mountBlocks(editor, { modes: mode });
  current.onChange(render);
  render();
}

function load(name: PresetName): void {
  const preset = getPreset(name);
  if (!current || current.modes !== preset.modes) {
    modes.value = preset.modes;
    remount(preset.modes);
  }
  current?.loadPreset(name);
}

function render(): void {
  if (!current) return;
  const program = current.getTree();
  const validation = validateProgram(program, current.modes);
  const findings = detect({ ...program, modes: current.modes });
  latex.textContent = toLatex(program.H);
  const jumpText = program.jumps.map((jump) => toPython(jump)).join(', ');
  python.textContent = `H = ${toPython(program.H)}\njumps = [${jumpText}]`;
  json.textContent = serializeProgram(program);
  checks.replaceChildren();
  const items = [
    ...validation.errors.map((text) => ({ text, bad: true })),
    ...findings.map((finding) => ({ text: `${finding.key}: ${finding.message}`, bad: true })),
  ];
  if (items.length === 0) items.push({ text: 'Hermitian, jumps carry √, no known wrong build.', bad: false });
  for (const item of items) {
    const li = document.createElement('li');
    li.className = item.bad ? 'bad' : 'ok';
    li.textContent = item.text;
    checks.append(li);
  }
}
