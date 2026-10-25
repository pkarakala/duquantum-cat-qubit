import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const siteRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

export default defineConfig({
  root: siteRoot,
  test: {
    environment: "jsdom",
    include: ["src/tutor/**/*.test.ts"],
  },
});
