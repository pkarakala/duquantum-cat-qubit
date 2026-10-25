/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly BASE_URL: string;
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.md?raw' {
  const src: string;
  export default src;
}

declare module 'plotly.js-dist-min' {
  interface PlotlyApi {
    newPlot(el: HTMLElement, data: unknown[], layout: unknown, config?: unknown): Promise<void>;
    react(el: HTMLElement, data: unknown[], layout: unknown, config?: unknown): Promise<void>;
    purge(el: HTMLElement): void;
  }
  const Plotly: PlotlyApi;
  export default Plotly;
}
