import { defineConfig, type Plugin } from "vite";

// Vite treats every `new Worker(new URL(...))` as a bundle entry. The node
// entry imports worker_threads, which the browser build must not pull in.
// The browser worker (worker-browser.ts) stays a real module worker.
export function browserSolverPlugin(options?: { inlineWorker?: boolean }): Plugin {
  return {
    name: "browser-solver",
    enforce: "pre",
    resolveId(id) {
      if (id === "node:worker_threads") return "\0node-worker-threads";
      return null;
    },
    load(id) {
      if (id !== "\0node-worker-threads") return null;
      return [
        "export class Worker {",
        "  constructor() { throw new Error('node:worker_threads is not used in the browser'); }",
        "  terminate() { return Promise.resolve(); }",
        "  postMessage() {}",
        "  on() {}",
        "}",
      ].join("\n");
    },
    transform(code, id) {
      const file = id.split("?")[0]?.replace(/\\/g, "/") ?? "";
      if (!file.endsWith("/site/src/sim/worker.ts")) return null;
      // The browser never takes the node branch. Drop it here so Vite does not
      // bundle worker-entry.ts (that file imports node:worker_threads).
      let next = code.replace(
        /function runNode\(req: SimRequest\): Promise<SimResult> \{[\s\S]*?\n\}/,
        `function runNode(_req: SimRequest): Promise<SimResult> {
  return Promise.reject(new Error("node:worker_threads is not used in the browser"));
}`,
      );
      if (options?.inlineWorker) {
        next = next.replace(
          'import type { SimRequest, SimResult } from \'./types.ts\';',
          "import type { SimRequest, SimResult } from './types.ts';\nimport BrowserWorker from './worker-browser.ts?worker&inline';",
        );
        next = next.replace(
          "const worker = new Worker(new URL('./worker-browser.ts', import.meta.url), { type: 'module' });",
          "const worker = new BrowserWorker();",
        );
      }
      if (next === code) return null;
      return { code: next, map: null };
    },
  };
}

// base './' keeps every asset path relative, so dist/ works under any Pages sub-path.
export default defineConfig({
  base: "./",
  plugins: [browserSolverPlugin()],
  worker: {
    format: "es",
    plugins: () => [browserSolverPlugin()],
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 6000,
  },
});
