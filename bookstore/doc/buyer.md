## 买家下单

#### URL：
POST http://[address]/buyer/new_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "user_id",
  "store_id": "store_id",
  "books": [
    {
      "id": "1000067",
      "count": 1
    },
    {
      "id": "1000134",
      "count": 4
    }
  ]
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
store_id | string | 商铺ID | N
books | class | 书籍购买列表 | N

books数组：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍的ID | N
count | string | 购买数量 | N


#### Response

Status Code:

码 | 描述
--- | ---
200 | 下单成功
5XX | 买家用户ID不存在
5XX | 商铺ID不存在
5XX | 购买的图书不存在
5XX | 商品库存不足

##### Body:
```json
{
  "order_id": "uuid"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
order_id | string | 订单号，只有返回200时才有效 | N


## 买家付款

#### URL：
POST http://[address]/buyer/payment

#### Request

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id",
  "password": "password"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 买家用户密码 | N 


#### Response

Status Code:

码 | 描述
--- | ---
200 | 付款成功
519 | 账户余额不足
520 | 该订单已付款
521 | 该订单已取消
5XX | 无效参数
401 | 授权失败 


## 买家充值

#### URL：
POST http://[address]/buyer/add_funds

#### Request

##### Body:
```json
{
  "user_id": "user_id",
  "password": "password",
  "add_value": 10
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
password | string | 用户密码 | N
add_value | int | 充值金额，以分为单位 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 充值成功
401 | 授权失败
5XX | 无效参数

## 查询订单

#### URL：
POST http://[address]/buyer/query_orders

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 查询成功
401 | 授权失败 
5XX | 无效参数

##### Body:
```json
[
  {"order_id": "order_id", 
  "store_id": "store_id", 
  "order_time": "datetime.datetime", 
  "total_price": 2440630, 
  "paid": 0, 
  "cancelled": 0, 
  "order_books": 
    [
      {"book_id": "1000067", "count": 40, "price": 3879}, 
      {"book_id": "1000134", "count": 5, "price": 3000}
    ]
  }
]
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
order_id | string | 订单号，只有返回200时才有效 | N
store_id | string | 书店ID | N
order_time | TIME | 下单时间 | N
total_price | integer | 订单总价 | N
paid | bool | 是否支付 | N
cancelled | bool | 是否取消 | N
order_books | class | 书籍购买列表 | N

books list:
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
book_id | string | 书籍ID | N
count | integer | 购买数量 | N
price | integer | 书籍单价 | N

## 取消订单

#### URL：
POST http://[address]/buyer/cancel_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N

#### Response 

Status Code:

码 | 描述
--- | ---
200 | 取消订单成功
401 | 授权失败
518 | 订单ID不存在
521 | 订单已取消
