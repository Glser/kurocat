import { defineConfig } from 'vite';
import path from 'node:path';
export default defineConfig({
  root: path.resolve('website'), base: '/kurocat/',
  define: { 'import.meta.env.VITE_PHOTO_SLEEP_PREVIEW': true },
  cacheDir: path.resolve('node_modules/.vite-kitten-lab'),
  server: { host: '127.0.0.1', port: 1422, strictPort: true, fs: { allow: [process.cwd()] } },
});
