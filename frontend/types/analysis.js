// types/analysis.js — JSDoc-only 类型定义

/**
 * @typedef {Object} MonthlyResp
 * @property {number} total
 * @property {string} top_category
 * @property {string} advice
 */

/**
 * @typedef {Object} DailyItem
 * @property {string} date  YYYY-MM-DD
 * @property {number} total
 */

/**
 * @typedef {Object} DailyResp
 * @property {DailyItem[]} days
 */

/**
 * @typedef {Object} CategoryItem
 * @property {string} category
 * @property {number} amount
 * @property {number} percent  0-1
 */

/**
 * @typedef {Object} CategoryResp
 * @property {CategoryItem[]} categories
 * @property {number} total
 */

export {}