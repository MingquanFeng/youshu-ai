// frontend/eslint.config.js — ESLint 9 flat config (微信小程序适配)
// 微信小程序没有 Node 环境, 但 lint 是本地工具,
// 用 globals 声明 wx / Component / Page / App 等运行时变量。
import js from '@eslint/js';
import globals from 'globals';
import prettier from 'eslint-config-prettier';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        // 微信小程序运行时全局
        wx: 'readonly',
        getApp: 'readonly',
        getCurrentPages: 'readonly',
        Component: 'readonly',
        Page: 'readonly',
        App: 'readonly',
        Behavior: 'readonly'
      }
    },
    rules: {
      // 微信小程序里 == 与 === 都常见, 暂时只警告 eqeqeq
      eqeqeq: ['warn', 'always', { null: 'ignore' }],
      'no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrors: 'none' // catch (e) 不强制使用, 兜底场景常见
        }
      ],
      'no-undef': 'error',
      'prefer-const': 'warn',
      'no-console': 'off', // 微信 wx.showToast / console.log 是常用调试手段
      'no-empty': ['warn', { allowEmptyCatch: true }]
    }
  },
  // Node 工具脚本 (CI 用的 wxml 条件链检查器)
  {
    files: ['scripts/**/*.js'],
    languageOptions: {
      globals: { ...globals.node },
      sourceType: 'commonjs',
      ecmaVersion: 2020
    }
  },
  // 全局覆盖: prettier 处理格式问题, 关闭冲突的 format 规则
  prettier,
  // 忽略
  {
    ignores: [
      'node_modules/**',
      'miniprogram_npm/**', // 微信开发者工具生成的目录
      'components/**/dist/**'
    ]
  }
];
