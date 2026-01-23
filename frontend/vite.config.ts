import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
        }
      },
      // 优化依赖预构建
      optimizeDeps: {
        // 强制预构建，将所有依赖打包成少数几个文件
        force: true,
        // 使用 esbuild 来合并这些库
        include: [
          'react',
          'react-dom',
          'lucide-react',
          'react-markdown',
          'react-syntax-highlighter',
          'react-syntax-highlighter/dist/esm/styles/prism',
          'remark-gfm',
          'remark-parse',
          'remark-stringify',
          'unified',
          'bail',
          'trough',
          'vfile',
          'is-plain-obj',
          'trough',
          'unist-util-stringify-position',
          'unist-util-from',
          'mdast-util-to-markdown',
          'mdast-util-from-markdown',
          'micromark',
          'micromark-core-commonmark',
          'micromark-factory-space',
          'micromark-util-character',
          'micromark-util-symbol',
          'micromark-util-chunked',
          'micromark-util-combine-extensions',
          'micromark-util-decode-numeric-character-reference',
          'micromark-util-encode',
          'micromark-util-normalize-identifier',
          'micromark-util-resolve-all',
          'micromark-util-subtokenize',
          'micromark-util-types',
          'parse-entities',
          'property-information',
          'html-url-attributes',
          'web-namespaces'
        ],
        exclude: [],
        disabled: false
      },
      // 构建优化
      build: {
        // 减少chunk数量
        rollupOptions: {
          output: {
            manualChunks(id) {
              // 将所有 node_modules 中的包打包到 vendor
              if (id.includes('node_modules')) {
                return 'vendor';
              }
            }
          }
        },
        chunkSizeWarningLimit: 1000
      }
    };
});
