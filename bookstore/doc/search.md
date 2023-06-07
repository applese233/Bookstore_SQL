# 搜索图书

## 查看图书信息

### URL

POST http://[address]/search/book_info

### Request

Body:

```json
{
  "id": "1000067",
  "isbn": "isbn-here"
}
```

key | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍 ID | Y 
isbn | string | ISBN 号 | Y 

### Response

Status Code:

码 | 描述
--- | ---
200 | 成功找到图书并返回 
401 | 搜索内容非法 

Body:

```json
{
  "store_id": "$store id$",
  "book_info": {
    "tags": [
      "tags1",
      "..."
    ],
    "pictures": [
      "$Base 64 encoded bytes array1$",
      "..."
    ],
    "id": "$book id$",
    "title": "$book title$",
    "author": "$book author$",
    "publisher": "$book publisher$",
    "original_title": "$original title$",
    "translator": "translater",
    "pub_year": "$pub year$",
    "pages": 10,
    "price": 10,
    "binding": "平装",
    "isbn": "$isbn$",
    "author_intro": "$author introduction$",
    "book_intro": "$book introduction$",
    "content": "$chapter1 ...$"
  },
  "stock_level": 0
}
```

各项数据说明详见 [seller.md](seller.md)

### 说明

- Request
  - ID 和 ISBN 不能同时为空







## 模糊搜索

### URL

POST http://[address]/search/fuzzy

### Request

Body:

```json
{
  "term": "term",
  "store_id": "store id",
  "page_size": page_size,
  "page_id": page_id,
}
```

key | 类型 | 描述 | 是否可为空
---|---|---|---
term | string | 搜索内容 | N
store_id | string | 商铺ID | Y 
page_size | int | 每页结果数 | Y 
page_id | int | 结果页数 | Y 

### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功并返回 

Body:

```json
{
  "result_number": 108,
  "page_number": 4,
  "page_size": 30,
  "result": [
    {
      "id": "1000067",
      "title": "The Moon and the Lotus Pond",
      "author": "Zhu Ziqing",
      "publisher": "Paper Republic Story Hub",
      "original_title": null,
      "translator": "Peter Richardson",
      "pub_year": "1927",
      "price": 990,
      "binding": "平装",
      "tags": [
        "nature",
        "Republican Era",
        "..."
      ],
      "pictures": "$Base 64 encoded bytes array1$"
    }
  ]
}
```

| 变量名        | 类型 | 描述         | 是否可为空 |
| ------------- | ---- | ------------ | ---------- |
| result_number | int  | 总结果数量   | N          |
| page_number   | int  | 结果页数     | N          |
| page_size     | int  | 每页结果数量 | N          |
| result        | list | 本页搜索结果 | N          |

Result:

> Result 不包括所有图书内容，*表示与 book_info 类中对应项定义不同

| 变量名         | 类型      | 描述             | 是否可为空 |
| -------------- | --------- | ---------------- | ---------- |
| id             | string    | 书籍ID           | N          |
| title          | stringint | 书籍题目结果页数 | N          |
| author         | string    | 作者             | Y          |
| publisher      | string    | 出版社           | Y          |
| original_title | string    | 原书题目         | Y          |
| translator     | string    | 译者             | Y          |
| pub_year       | string    | 出版年月         | Y          |
| price          | int       | 价格(以分为单位) | N          |
| binding        | string    | 装帧，精状/平装  | Y          |
| tags           | array     | 标签             | Y          |
| pictures       | string    | *首张照片        | Y          |

### 说明

- Request
  - 店铺 id 为空则为全站搜索
  - page_size 应当为 10 / 30 / 50 / 100 其中某一值，为空则默认为 30







## 精确搜索

### URL

POST http://[address]/search/cond

### Request

Body:

```json
{
  "title": "title_term",
  "author": "author_term",
  "publisher": "publisher_term",
  "pub_year_start": 1910,
  "pub_year_end": 1940,
  "price_low": 0,
  "price_high": 10000,
  "binding": "平装",
  "tags": [
    "tags1",
    "tags2",
    "tags3",
    "..."
  ]
}
```

key | 类型 | 描述 | 是否可为空
---|---|---|---
title | string | 书籍题目或原书题目 | Y 
author | string | 作者或译者 | Y 
publisher | string | 出版社 | Y 
pub_year_start | string | 最早出版年月 | Y 
pub_year_end | string | 最晚出版年月 | Y 
price_low | int | 最低价格 | Y 
price_high | int | 最高价格 | Y 
binding | string | 装帧 | Y 
tags | array | 标签 | Y 

### Response

Status Code:

码 | 描述
--- | ---
200 | 成功搜索得到结果并返回 
401 | 搜索无结果 
501 | 搜索信息非法 

Body:

```json
{
  "result_number": 108,
  "page_number": 4,
  "page_size": 30,
  "result": [
    {
      "id": "1000067",
      "title": "The Moon and the Lotus Pond",
      "author": "Zhu Ziqing",
      "publisher": "Paper Republic Story Hub",
      "original_title": null,
      "translator": "Peter Richardson",
      "pub_year": "1927",
      "price": 990,
      "binding": "平装",
      "tags": [
        "nature",
        "Republican Era",
        "..."
      ],
      "pictures": "$Base 64 encoded bytes array1$"
    }
  ]
}
```

### 说明

- Request
  - 出版年月和价格区间均为闭区间
  - 搜索标签为搜索结果图书标签子集
