/** Browser worker. Vite bundles this; the node tests use worker-entry.ts. */

import { simulate } from './simulate.ts';
import type { SimRequest, SimResult } from './types.ts';

function buffersOf(result: SimResult): ArrayBuffer[] {
  const out: ArrayBuffer[] = [];
  const push = (a?: Float64Array) => {
    if (a) out.push(a.buffer);
  };
  push(result.tUs);
  push(result.n);
  push(result.parity);
  push(result.reA);
  push(result.finalPops);
  if (result.wigner) {
    push(result.wigner.x);
    push(result.wigner.y);
    for (const frame of result.wigner.frames) push(frame.w);
  }
  return out;
}

self.onmessage = (ev: MessageEvent<SimRequest>) => {
  try {
    const result = simulate(ev.data);
    self.postMessage(result, { transfer: buffersOf(result) });
  } catch (err) {
    self.postMessage({ __error: err instanceof Error ? err.message : String(err) });
  }
};
