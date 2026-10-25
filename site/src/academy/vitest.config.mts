import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { defineConfig } from 'vitest/config';

const here = dirname(fileURLToPath(import.meta.url));
const site = resolve(here, '../..');
const repo = resolve(here, '../../..');

export default defineConfig({
  root: site,
  server: { fs: { allow: [repo, site] } },
  test: {
    include: ['src/academy/**/*.test.ts'],
    environment: 'node',
  },
});
