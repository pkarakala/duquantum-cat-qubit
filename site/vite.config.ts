/// <reference types="vitest/config" />
import { defineConfig } from "vite";

// base './' keeps every asset path relative, so dist/ works under any Pages sub-path.
export default defineConfig({
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 6000,
  },
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
    testTimeout: 20000,
  },
});
