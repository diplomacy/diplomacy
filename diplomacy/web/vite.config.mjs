import {fileURLToPath} from 'node:url';
import {defineConfig, transformWithOxc} from 'vite';
import react from '@vitejs/plugin-react';

const webRoot = fileURLToPath(new URL('.', import.meta.url));
const mapsRoot = fileURLToPath(new URL('../maps', import.meta.url));

export default defineConfig({
    base: './',
    plugins: [
        {
            name: 'jsx-in-source-js',
            enforce: 'pre',
            transform(code, id) {
                if (id.startsWith(webRoot + 'src/') && id.endsWith('.js'))
                    return transformWithOxc(code, id, {lang: 'jsx', jsx: {runtime: 'classic'}});
            }
        },
        react({jsxRuntime: 'classic'})
    ],
    optimizeDeps: {
        rolldownOptions: {moduleTypes: {'.js': 'jsx'}}
    },
    server: {
        host: 'localhost',
        port: 3000,
        strictPort: true,
        fs: {allow: [webRoot, mapsRoot]}
    },
    build: {
        outDir: 'build',
        target: ['chrome111', 'edge111', 'firefox114', 'safari16.4']
    }
});
