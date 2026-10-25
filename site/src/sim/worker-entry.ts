/** Node worker: one simulate() call, typed arrays transferred back. */

import { parentPort } from 'node:worker_threads';
import { simulate } from './simulate.ts';
import type { SimResult } from './types.ts';

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

parentPort?.on('message', (req: unknown) => {
  try {
    const result = simulate(req as Parameters<typeof simulate>[0]);
    parentPort?.postMessage(result, buffersOf(result));
  } catch (err) {
    parentPort?.postMessage({ __error: err instanceof Error ? err.message : String(err) });
  }
});
