import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { browserSolverPlugin } from "./vite.config";

// One self-contained index.html. publicDir is off so audio files cannot land
// beside that html (the offline build has no narration files).
export default defineConfig({
  base: "./",
  publicDir: false,
  plugins: [browserSolverPlugin({ inlineWorker: true }), viteSingleFile()],
  worker: {
    format: "es",
    plugins: () => [browserSolverPlugin({ inlineWorker: true })],
  },
  build: {
    outDir: "dist-single",
    emptyOutDir: true,
    chunkSizeWarningLimit: 15000,
    cssCodeSplit: false,
    assetsInlineLimit: 100000000,
  },
});
