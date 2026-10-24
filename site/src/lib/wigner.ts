// Colour range shared by every Wigner frame, so the animation never rescales between frames.
export function wignerRange(frames: { w: number[][] }[]): [number, number] {
  let m = 0;
  for (const f of frames) for (const row of f.w) for (const v of row) if (Math.abs(v) > m) m = Math.abs(v);
  if (m === 0) m = 1;
  return [-m, m];
}

// Diverging blue-white-red scale, symmetric about W = 0.
export const WIGNER_SCALE: [number, string][] = [
  [0, "#2166ac"],
  [0.5, "#f7f7f7"],
  [1, "#b2182b"],
];
