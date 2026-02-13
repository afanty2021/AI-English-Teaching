import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia']
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    exclude: ['@element-plus/icons-vue']
  },
  esbuild: {
    logOverride: { 'this-is-undefined-in-esm': 'silent' },
    // 生产环境移除 console 和 debugger
    drop: ['console', 'debugger']
  },
  build: {
    rollupOptions: {
      output: {
        // 代码分割配置
        manualChunks: {
          // 将 Element Plus 组件库单独打包
          'element-plus': ['element-plus'],
          // 将 ECharts 图表库单独打包
          'echarts': ['echarts'],
          // 将 Vue Router 和 Pinia 单独打包
          'router-store': ['vue-router', 'pinia'],
          //  vendors: ['vue', 'vue-router', 'pinia']
        },
        // 优化 chunk 命名
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: '[ext]/[name]-[hash].[ext]',
      }
    },
    // 启用 CSS 代码分割
    cssCodeSplit: true,
    // 启用 gzip 压缩提示
    reportCompressedSize: true,
    // 压缩级别
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // 生产环境移除 console
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info']
      }
    }
  }
})
