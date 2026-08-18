// types/bill.js — JSDoc-only 类型定义（运行时无导出）

/**
 * @typedef {Object} BillItem
 * @property {number} id
 * @property {number} amount
 * @property {string} category
 * @property {string} merchant
 * @property {string} pay_method
 * @property {string} bill_time  ISO 字符串
 * @property {string} remark
 * @property {string} source     'image_ai' | 'manual' | ...
 * @property {number} ai_score
 */

/**
 * @typedef {Object} BillListParams
 * @property {number} page
 * @property {number} size
 * @property {string} [category]
 * @property {string} [date]
 */

/**
 * @typedef {Object} BillListResp
 * @property {number} total
 * @property {number} page
 * @property {number} size
 * @property {BillItem[]} items
 */

/**
 * @typedef {Object} RecognizeResult
 * @property {number} amount
 * @property {string} merchant
 * @property {string} category
 * @property {string} time      ISO 字符串
 * @property {string} payment   后端字段名，前端表单映射为 pay_method
 * @property {number} score     0-1
 */

export {};
