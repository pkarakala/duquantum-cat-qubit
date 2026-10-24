import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// One self-contained index.html (JS, CSS and data inlined) that opens from file:// with no network.
export default defineConfig({
  base: "./",
  plugins: [viteSingleFile()],
  build: {
    outDir: "dist-single",
    emptyOutDir: true,
    chunkSizeWarningLimit: 15000,
  },
});
