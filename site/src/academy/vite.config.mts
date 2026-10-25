import { defineConfig } from 'vite';

/** Lane-local dev server. Root is this folder (`npx vite src/academy` from site/). */
export default defineConfig({
  cacheDir: '../../node_modules/.vite-academy',
  server: { fs: { allow: ['../..', '../../..'] } },
});
