import { defineConfig, type Plugin } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

/**
 * 修复 vite-plugin-uni mainJs 的代码缺陷：
 * 它会把 `createSSRApp` 替换成 `createVueApp as createSSRApp`，但 vue 包未导出 `createVueApp`。
 * 在 mainJs 转换后再做一次反向修正。
 */
function fixMainJsTransform(): Plugin {
  return {
    name: 'fix-uni-mainjs',
    enforce: 'post',
    transform(code, id) {
      if (!/src[/\\]main\.ts$/.test(id)) return null
      if (!code.includes('createVueApp as createSSRApp')) return null
      return {
        code: code.replace(/createVueApp as createSSRApp/g, 'createSSRApp'),
        map: null
      }
    }
  }
}

export default defineConfig({
  plugins: [uni(), fixMainJsTransform()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
