import type { LevelId, LevelSpec } from '../types';
import { L1 } from './L1';
import { L2 } from './L2';
import { L3 } from './L3';
import { L4 } from './L4';
import { L5 } from './L5';
import { L6 } from './L6';
import { L7 } from './L7';
import { L8 } from './L8';

export const LEVELS: LevelSpec[] = [L1, L2, L3, L4, L5, L6, L7, L8];

export function levelById(id: string): LevelSpec | undefined {
  return LEVELS.find((level) => level.id === id);
}

export function nextLevelId(id: LevelId): LevelId {
  const i = LEVELS.findIndex((level) => level.id === id);
  return LEVELS[Math.min(LEVELS.length - 1, i + 1)]!.id;
}

export { L1, L2, L3, L4, L5, L6, L7, L8 };
