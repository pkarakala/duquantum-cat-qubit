/** Run `simulate` off the main thread. Node uses worker_threads; the browser uses a module worker. */

import type { SimRequest, SimResult } from './types.ts';

function settle(result: SimResult | { __error?: string }): SimResult {
  if (result && typeof result === 'object' && '__error' in result && result.__error) {
    throw new Error(result.__error);
  }
  return result as SimResult;
}

function runNode(req: SimRequest): Promise<SimResult> {
  return import('node:worker_threads').then(
    ({ Worker }) =>
      new Promise((resolve, reject) => {
        const worker = new Worker(new URL('./worker-entry.ts', import.meta.url));
        const fail = (err: Error) => {
          worker.terminate().catch(() => undefined);
          reject(err);
        };
        worker.on('message', (msg: SimResult | { __error?: string }) => {
          worker.terminate().catch(() => undefined);
          try {
            resolve(settle(msg));
          } catch (err) {
            reject(err);
          }
        });
        worker.on('error', fail);
        worker.postMessage(req);
      }),
  );
}

function runBrowser(req: SimRequest): Promise<SimResult> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL('./worker-browser.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (ev: MessageEvent<SimResult | { __error?: string }>) => {
      worker.terminate();
      try {
        resolve(settle(ev.data));
      } catch (err) {
        reject(err instanceof Error ? err : new Error(String(err)));
      }
    };
    worker.onerror = (ev) => {
      worker.terminate();
      reject(new Error(ev.message));
    };
    worker.postMessage(req);
  });
}

export function runInWorker(req: SimRequest): Promise<SimResult> {
  if (typeof window === 'undefined') return runNode(req);
  return runBrowser(req);
}
