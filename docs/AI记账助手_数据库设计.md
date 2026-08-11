# AI记账助手数据库设计

## 1. 用户表 user

  字段         类型       说明
  ------------ ---------- ------------
  id           bigint     主键
  openid       varchar    微信用户ID
  nickname     varchar    昵称
  avatar       varchar    头像
  created_at   datetime   创建时间

------------------------------------------------------------------------

# 2. 账单表 bill

  字段         类型       说明
  ------------ ---------- ----------
  id           bigint     主键
  user_id      bigint     用户
  amount       decimal    金额
  category     varchar    分类
  merchant     varchar    商户
  pay_method   varchar    支付方式
  bill_time    datetime   消费时间
  remark       text       备注
  source       varchar    来源
  ai_score     decimal    AI可信度

source:

    manual
    image_ai
    voice_ai

------------------------------------------------------------------------

# 3. AI识别记录表 ai_record

  字段          类型       说明
  ------------- ---------- ----------
  id            bigint     主键
  bill_id       bigint     账单ID
  image_url     varchar    图片地址
  ocr_text      text       OCR文本
  model         varchar    模型
  result_json   json       结果
  created_at    datetime   时间

------------------------------------------------------------------------

# 4. 分类表 category

字段：

-   id
-   name
-   parent_id

示例：

    餐饮
     ├── 早餐
     ├── 午餐

    交通
     ├── 打车
     └── 公交

------------------------------------------------------------------------

# 5. 设计原则

-   用户数据隔离
-   AI结果可追踪
-   支持模型升级
-   支持人工修正
