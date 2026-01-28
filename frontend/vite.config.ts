import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');

    // 从环境变量读取端口
    const BACKEND_PORT = env.VITE_BACKEND_PORT || '8080';
    const AGENT_SERVICE_PORT = env.VITE_AGENT_SERVICE_PORT || '8081';

    return {
      server: {
        port: 3000,  // 恢复标准端口
        host: '0.0.0.0',
        strictPort: true,
        allowedHosts: ['localhost', '.localhost', '127.0.0.1'],
        hmr: {
          protocol: 'ws',
          host: '0.0.0.0',
          port: 3000,
        },
        watch: {
          usePolling: true,
        },
        // 恢复完整的代理配置
        proxy: {
          '/api/v1/agents': {
            target: `http://127.0.0.1:${AGENT_SERVICE_PORT}`,
            changeOrigin: true,
            rewrite: (path) => path,
            buffer: false,
            preserveHeaderKeyCase: true,
            configure: (proxy, options) => {
              proxy.on('proxyReq', (proxyReq, req, res) => {
                console.log('[Proxy Agent]', req.method, req.url, '→', options.target);
              });
              proxy.on('proxyRes', (proxyRes, req, res) => {
                console.log('[Proxy Agent Response]', proxyRes.statusCode, req.url);
              });
            }
          },
          '/api/v1': {
            target: `http://127.0.0.1:${BACKEND_PORT}`,
            changeOrigin: true,
            rewrite: (path) => path,
            buffer: false,
            configure: (proxy, options) => {
              proxy.on('proxyReq', (proxyReq, req, res) => {
                console.log('[Proxy Backend]', req.method, req.url, '→', options.target);
              });
              proxy.on('proxyRes', (proxyRes, req, res) => {
                console.log('[Proxy Backend Response]', proxyRes.statusCode, req.url);
              });
            }
          },
          '/lmp-cloud-ias-server': {
            target: `http://127.0.0.1:${BACKEND_PORT}`,
            changeOrigin: true,
            rewrite: (path) => path,
            buffer: false,
            configure: (proxy, options) => {
              proxy.on('proxyReq', (proxyReq, req, res) => {
                console.log('[Proxy IAS]', req.method, req.url, '→', options.target);
              });
            }
          }
        },
        headers: {
          'Cache-Control': 'no-store',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
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
