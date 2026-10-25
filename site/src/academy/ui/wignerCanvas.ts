/** Diverging Wigner paint. Fixed scale ±2/π, row = Im α, index = iy * nx + ix. */

export const WIGNER_M = 2 / Math.PI;

const BLUE = [0x21, 0x66, 0xac];
const WHITE = [0xf7, 0xf7, 0xf7];
const RED = [0xb2, 0x18, 0x2b];

function channel(hex: string): [number, number, number] {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}

function mix(a: number[], b: number[], t: number): string {
  const u = Math.min(1, Math.max(0, t));
  const parts = a.map((v, i) => Math.round(v + ((b[i] ?? v) - v) * u));
  return `#${parts.map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

/** −M blue, 0 grey, +M red. Values outside ±M are clamped. */
export function divergingColor(w: number, M = WIGNER_M): string {
  if (!Number.isFinite(w) || w === 0) return '#f7f7f7';
  if (w <= -M) return '#2166ac';
  if (w >= M) return '#b2182b';
  if (w < 0) return mix(BLUE, WHITE, (w + M) / M);
  return mix(WHITE, RED, w / M);
}

export function fillRgba(w: ArrayLike<number>, nx: number, ny: number, target: Uint8ClampedArray): void {
  const n = nx * ny;
  for (let i = 0; i < n; i++) {
    const [r, g, b] = channel(divergingColor(Number(w[i] ?? 0)));
    const o = i * 4;
    target[o] = r;
    target[o + 1] = g;
    target[o + 2] = b;
    target[o + 3] = 255;
  }
}

export function wignerLabel(w: ArrayLike<number>, nx: number, x: ArrayLike<number>, y: ArrayLike<number>): string {
  let min = Infinity;
  let max = -Infinity;
  let maxI = 0;
  for (let i = 0; i < w.length; i++) {
    const v = Number(w[i] ?? 0);
    if (v < min) min = v;
    if (v > max) {
      max = v;
      maxI = i;
    }
  }
  if (!Number.isFinite(min)) return 'Wigner map, no frame yet';
  const ix = maxI % nx;
  const iy = Math.floor(maxI / nx);
  const re = Number(x[ix] ?? 0);
  const im = Number(y[iy] ?? 0);
  return `Wigner map, minimum ${min.toFixed(3)}, peak at Re ${re.toFixed(2)}, Im ${im.toFixed(2)}`;
}

export function paintWigner(
  canvas: HTMLCanvasElement,
  w: ArrayLike<number>,
  nx: number,
  ny: number,
  x: ArrayLike<number>,
  y: ArrayLike<number>,
): void {
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', wignerLabel(w, nx, x, y));
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const rgba = new Uint8ClampedArray(nx * ny * 4);
  fillRgba(w, nx, ny, rgba);
  const image = new ImageData(rgba, nx, ny);
  const off = document.createElement('canvas');
  off.width = nx;
  off.height = ny;
  const offCtx = off.getContext('2d');
  if (!offCtx) return;
  offCtx.putImageData(image, 0, 0);
  const cssW = canvas.clientWidth || 280;
  canvas.width = cssW;
  canvas.height = Math.round(cssW * (ny / nx));
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
}
