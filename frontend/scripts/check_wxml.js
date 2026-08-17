#!/usr/bin/env node
// scripts/check_wxml.js — WXML 条件链语法检查
// 规则:
//   1. <block wx:if> 链必须以 wx:if 开头
//   2. wx:elif 必须紧邻 wx:if / wx:elif
//   3. wx:else 后不能再有 wx:elif
//   4. wx:if/elif 缺 {{...}} 条件值

const fs = require('fs');
const path = require('path');

function findFiles(dir, ext) {
  let out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === 'node_modules' || e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out = out.concat(findFiles(p, ext));
    else if (p.endsWith(ext)) out.push(p);
  }
  return out;
}

let failed = 0;

function checkFile(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  let lastConditional = null; // 'if' | 'elif' | 'else' | null

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    // 检查 1+4: wx:if/wx:elif 缺 {{...}} 条件值
    const condAttr = line.match(/\swx:(elif|if)([^=>]*)/);
    if (condAttr) {
      const [, kind, rest] = condAttr;
      // rest 不应以非 = 字符开头
      if (rest && !rest.startsWith('=')) {
        console.error(`${file}:${lineNum}: wx:${kind} 后接其他属性 (wx:${kind} 必须 wx:${kind}="{{ cond }}")`);
        failed++;
      } else if (rest === '=' || rest.startsWith('=')) {
        // 检查 = 后内容是否包含 {{
        const m = line.match(new RegExp(`wx:${kind}=\\"([^\\"]*)\\"`));
        if (m && !m[1].includes('{{')) {
          console.error(`${file}:${lineNum}: wx:${kind} 缺 {{...}} 条件值: ${m[1]}`);
          failed++;
        }
      }
    }

    // 检查 2+3: wx:elif 必须紧跟 wx:if/wx:elif; wx:else 后不能再有 wx:elif
    if (/\swx:elif\b/.test(line)) {
      if (lastConditional !== 'if' && lastConditional !== 'elif') {
        const why = lastConditional === 'else'
          ? 'wx:elif 不能跟在 wx:else 后 (链必须以 wx:if 开头并连续)'
          : 'wx:elif 必须跟在 wx:if/wx:elif 后面';
        console.error(`${file}:${lineNum}: ${why}`);
        failed++;
      }
      lastConditional = 'elif';
    } else if (/\swx:else\b/.test(line)) {
      if (lastConditional !== 'if' && lastConditional !== 'elif') {
        console.error(`${file}:${lineNum}: wx:else 必须跟在 wx:if/wx:elif 后`);
        failed++;
      }
      lastConditional = 'else';
    } else if (/\swx:if\b/.test(line)) {
      lastConditional = 'if';
    } else {
      // 其他行不影响链状态 (但同一行 if+elif 应被识别; 简化为只取第一个)
      // 实际场景大多一行一节点, 此简化足够
    }
  }
}

const dir = process.argv[2] || 'frontend';
const files = findFiles(dir, '.wxml');
for (const f of files) checkFile(f);

if (failed > 0) {
  console.error(`\n❌ ${failed} WXML conditional chain error(s)`);
  process.exit(1);
}
console.log(`✅ WXML conditional chain OK (${files.length} files)`);