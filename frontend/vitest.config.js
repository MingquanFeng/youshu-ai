// vitest.config.js — 微信小程序代码测 pure logic (无 wxss/wxml 渲染)
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // jsdom 给 wx/wxss 之外的 JS 环境 (对象/字符串/DOM)
    environment: 'jsdom',
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
