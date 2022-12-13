# 資料庫系統 期末專案
### B07505024 劉厚均

## 執行方式
執行前須先進行環境的配置。
這裡附上environment.yml。
打開console並執行以下指令可以建立目標環境。
```
conda env create --file environment.yml
conda activate DBMS
```
移至main.py所在之資料夾。\
執行以下指令。
```{bash}
uvicorn main:app --reload
```

## 資料庫設計
資料庫設計參照文件上標示來實作，共分成五個table。
### Auth
id\
token
### User
id: 使用自動遞增之primary key。\
name: 使用者的名稱。\
type: 賣家或買家。\
email: 使用者的信箱，登入及驗證時使用，不可更改。\
phone: 使用者的電話號碼。\
password: 使用者的密碼，登入使用。
### Product
id: 使用自動遞增之primary key。\
name: 商品名稱。\
description: 商品描述。\
picture: 商品圖片的儲存位置。\
inventory: 商品庫存，在訂單成功時會減少。\
price: 商品售價。\
startSaleTime: 上架時間。\
endSaleTime: 下架時間。
### Order
id: 使用自動遞增之primary key\
buyerName: 買家姓名。\
buyerEmail: 買家信箱。\
buyerPhone: 買家電話號碼。\
timestamp: 購買時間。\
products: 將list進行編碼，i{商品編號}a{數量}，以逗號間格。
### ApiResponse
status\
message

## Api設計
Api設計參照文件上標示來實作。
使用語言為Python3.6。\
框架為Fastapi。

### User
#### POST: /users
建立新的使用者資料。

#### PATCH: /users/me
需登入才能使用，更新使用者資料，不必輸入所有欄位。\
因為email作為登入判斷值，因此不可更新。
這裡和文件上使用/users/{id}不同。\
考慮使用者應只能更新自己的資料，因此改成用/me。\

#### POST: /users/signIn
使用者須輸入email及password進行登入。
登入成功後會回傳一串jwt token用於驗證。
使用者將有15分鐘的有效登入時間。

#### GET: /users/me
需登入才能使用，取得使用者資料。

### Product
#### POST: /products
建立新商品。

#### GET: /products
列出所有商品。
#### GET: /products/{id}
取得指定的商品資訊，若是商品不存在回傳錯誤訊息。
#### PATCH: /products/{id}
更新指定的商品資訊，若是商品不存在回傳錯誤訊息。
#### DELETE: /products/{id}
刪除指定的商品資訊，若是商品不存在回傳錯誤訊息。

### Order
#### POST: /orders
需登入才能使用，建立訂單。
傳入參數為list of dictionaries。
會將各個產品及數量編碼成包含id及amount的字串進行儲存。
像是"i1a20,i4a3"代表20個商品1及3個商品4。\
在訂單成功前，會先檢查三個步驟。
1. 商品是否存在
2. 存貨是否充足
3. 是否在販售時間內
若每個商品皆符合，訂單才會成立，否則會在遇到第一個錯誤時就終止。
若訂單成功，將會減少Product中的庫存數量。