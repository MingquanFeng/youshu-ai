// vitest.config.js — 微信小程序代码测 pure logic (无 wxss/wxml 渲染)
//
// 用 node 环境而非 jsdom: 我们测 pure functions (validateForm/isFormDirty/toAbsoluteUrl),
// 不依赖 DOM API. jsdom 在 Node 24 + undici webidl 上有兼容性 crash,
// node 环境更轻量 + 零依赖。
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.{js,mjs}'],
    exclude: ['node_modules/**', 'components/**/dist/**'],
    globals: false,
    setupFiles: ['tests/setup.js'],
    reporters: 'verbose',
    coverage: {
      provider: 'v8',
      include: ['utils/**/*.js', 'pages/**/*.js', 'components/**/*.{js,mjs}'],
      exclude: ['**/*.wxss', '**/*.wxml', '**/*.json']
    }
  }
});
