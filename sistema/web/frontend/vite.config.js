import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig(({ mode }) => {
  const entry = mode === 'login' ? 'login' : 'ui';
  return {
    plugins: [vue()],
    build: {
      emptyOutDir: true,
      outDir: `../dist/${entry}`,
      cssCodeSplit: false,
      rolldownOptions: {
        input: `${entry}.js`,
        output: { entryFileNames: `${entry}.js`, assetFileNames: `${entry}[extname]` },
      },
    },
  };
});
