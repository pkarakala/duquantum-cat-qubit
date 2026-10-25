import { describe, expect, it } from 'vitest';
import { divergingColor, fillRgba, WIGNER_M } from '../ui/wignerCanvas';

describe('Wigner colormap', () => {
  it('clamps a diverging blue–grey–red scale at ±2/π', () => {
    expect(divergingColor(-WIGNER_M)).toBe('#2166ac');
    expect(divergingColor(0)).toBe('#f7f7f7');
    expect(divergingColor(WIGNER_M)).toBe('#b2182b');
    expect(divergingColor(-10)).toBe('#2166ac');
    expect(divergingColor(10)).toBe('#b2182b');
    expect(divergingColor(-WIGNER_M / 2)).not.toBe(divergingColor(WIGNER_M / 2));
  });

  it('paints a 61×61 frame comfortably above 30 fps', () => {
    const nx = 61;
    const ny = 61;
    const w = new Float64Array(nx * ny);
    for (let i = 0; i < w.length; i++) w[i] = Math.sin(i * 0.17) * WIGNER_M;
    const buf = new Uint8ClampedArray(nx * ny * 4);
    const times: number[] = [];
    for (let frame = 0; frame < 40; frame++) {
      const t0 = performance.now();
      fillRgba(w, nx, ny, buf);
      times.push(performance.now() - t0);
    }
    const mean = times.reduce((sum, value) => sum + value, 0) / times.length;
    console.log(`wigner fillRgba mean ${mean.toFixed(4)} ms (${(1000 / Math.max(mean, 1e-6)).toFixed(0)} fps) over ${times.length} frames of 61×61`);
    expect(mean).toBeLessThan(1000 / 30);
  });
});
