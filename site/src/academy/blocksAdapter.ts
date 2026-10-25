/**
 * P3, loaded if it has merged. Absent → L6 shows the four precomputed builds.
 */

export interface BlockHandle {
  getTree: () => { H?: unknown; jumps?: unknown[] };
  onChange: (cb: () => void) => void;
  loadPreset: (name: string) => void;
}

export interface DetectHit {
  key: string;
  misconception?: string;
  message?: string;
}

interface BlocksModule {
  mountBlocks?: (el: HTMLElement, opts: { modes: 'one' | 'two' }) => BlockHandle;
  expr?: { toPython?: (tree: unknown) => string; validate?: (tree: unknown, modes: string) => unknown };
  wrongBuilds?: { detect?: (tree: unknown) => DetectHit[] };
  toPython?: (tree: unknown) => string;
  detect?: (tree: unknown) => DetectHit[];
}

const modules = import.meta.glob('../blocks/index.ts', { eager: true }) as Record<string, BlocksModule>;
const blocks = Object.values(modules)[0];

export function blocksPresent(): boolean {
  return typeof blocks?.mountBlocks === 'function';
}

export function mountBlocks(el: HTMLElement, opts: { modes: 'one' | 'two' }): BlockHandle | null {
  if (!blocks?.mountBlocks) return null;
  return blocks.mountBlocks(el, opts);
}

export function detectTree(tree: unknown): DetectHit[] {
  const detect = blocks?.wrongBuilds?.detect ?? blocks?.detect;
  if (!detect || tree == null) return [];
  return detect(tree) ?? [];
}

export function toPythonTree(tree: unknown): string | null {
  const fn = blocks?.expr?.toPython ?? blocks?.toPython;
  if (!fn || tree == null) return null;
  return fn(tree);
}
