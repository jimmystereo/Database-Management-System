import time
import sqlite3
import os
import copy
import uuid
from datetime import datetime, timedelta
from typing import Optional


from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# os.chdir('w:\\DBMS')
# os.getcwd()

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
IMAGEDIR = "./image_db"
DBDIR = './final.db'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/signIn")

app = FastAPI()


class User(BaseModel):
    name: str
    email: str
    password: str
    type: str
    phone: str


class Product(BaseModel):
    name: str
    description: str
    picture: str
    inventory: int
    price: int
    startSaleTime: str
    endSaleTime: str


class Order(BaseModel):
    productId: int
    amount: int


def execute_sql(s):
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(s)
    conn.commit()
    conn.close()
    return c


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class User(BaseModel):
    name: str
    email: str
    type: str
    phone: str
    password: str


class SignInForm(BaseModel):
    email: str
    password: str


class UserInDB(User):
    password: str


def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password
    # return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    # return password
    return pwd_context.hash(password)


def get_user(email: str):
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM USER WHERE email='{email}'")
    records = c.fetchall()

    insertObject = []
    columnNames = [column[0] for column in c.description]

    for record in records:
        insertObject.append(dict(zip(columnNames, record)))
    result = insertObject[0]
    return UserInDB(**result)


def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def dict_to_sql(s, table):
    query = "INSERT INTO " + table + " ("
    first = True
    for i in s.keys():
        if not first:
            query += ','
        query += i
        first = False

    query += ") VALUES ("
    first = True
    for i in s.keys():
        if not first:
            query += ','
        item = s[i]
        if isinstance(item, str) or isinstance(item, list):
            item = f"'{item}'"
        query += str(item)
        first = False

    query += ")"
    return query


@app.post("/users/signIn", response_model=Token)
async def login_for_access_token(form_data: SignInForm):
    user = authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.patch("/users/me")  # 指定 api 路徑 (get方法)
def read_user(update_info: dict, current_user: User = Depends(get_current_active_user)):
    result = {
        "status": 0,
        "message": "string",
    }
    if 'email' in update_info.keys():
        result = {
            "status": 1,
            "message": "Changing email is unavailable",
        }
        return result
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    for i in update_info.keys():
        if isinstance(update_info[i], str):
            update_info[i] = f"'{update_info[i]}'"
        c.execute(f"UPDATE USER set {i}={str(update_info[i])} WHERE email='{current_user.email}'")
    conn.commit()
    return get_user(current_user.email)


@app.post("/users")  # 指定 api 路徑 (get方法)
def create_user(user: User):
    execute_sql(
        f"INSERT INTO User (NAME,TYPE,PASSWORD,EMAIL,PHONE) VALUES ('{user.name}', '{user.type}','{user.password}', '{user.email}', '{user.phone}')")
    return user.dict()


@app.post("/products")  # 指定 api 路徑 (get方法)
def create_product(product: Product):
    sql = dict_to_sql(product.dict(), 'product')
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    return product.dict()


@app.get("/products")  # 指定 api 路徑 (get方法)
def get_products():
    result = {"status": 0, "message": "string", "data": []}
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute("SELECT * FROM PRODUCT")
    records = c.fetchall()
    columnNames = [column[0] for column in c.description]
    for record in records:
        result['data'].append(dict(zip(columnNames, record)))
    return result


@app.get("/products/{id}")  # 指定 api 路徑 (get方法)
def get_product(id: int):
    result = {"status": 0, "message": "string", "data": []}
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM PRODUCT WHERE id={id}")
    records = c.fetchall()
    columnNames = [column[0] for column in c.description]
    if len(records) == 0:
        return f"product id={id} not found."
    result['data'].append(dict(zip(columnNames, records[0])))
    return result


@app.patch("/products/{id}")  # 指定 api 路徑 (get方法)
def update_product(id: int, product: Product):
    target = product.dict()
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM PRODUCT WHERE id={id}")
    records = c.fetchall()
    if len(records) == 0:
        return f"product id={id} not found."
    for i in target.keys():
        if isinstance(target[i], str):
            target[i] = f"'{target[i]}'"
        c.execute(f"UPDATE product set {i}={str(target[i])} WHERE id={id}")
        conn.commit()

    return product.dict()


@app.delete("/products/{id}")
def delete_product(id: int):
    result = {
        "status": 0,
        "message": "Item Deleted"}
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM PRODUCT WHERE id={id}")
    records = c.fetchall()
    columnNames = [column[0] for column in c.description]
    if len(records) == 0:
        return f"product id={id} not found."
    c.execute(f"DELETE FROM product WHERE id={id}")
    conn.commit()
    result['data'] = dict(zip(columnNames, records[0]))

    return result


@app.post("/orders")
async def make_order(orders: list, current_user: User = Depends(get_current_active_user)):
    order_dict = {
        "id": None,
        "buyerName": current_user.name,
        "buyerEmail": current_user.email,
        "buyerPhone": current_user.phone,
        "timestamp": time.time(),
        "products": ''
    }

    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    for order in orders:
        productId = order['productId']
        amount = order['amount']
        c.execute(f"SELECT * FROM product WHERE id={productId}")
        records = c.fetchall()
        if len(records) == 0:
            return f"product {productId} not found"
        columnNames = [column[0] for column in c.description]
        result_dict = dict(zip(columnNames, records[0]))
        if result_dict['inventory'] < amount:
            return f"{result_dict['name']} not enough. {result_dict['inventory']} left but ordering {amount}"
        startTime = datetime.strptime(result_dict['startSaleTime'], "%Y-%m-%d")
        endTime = datetime.strptime(result_dict['endSaleTime'], "%Y-%m-%d")

        if not (startTime <= datetime.now() <= endTime):
            return f"{result_dict['name']} is not available now."

    result = []
    for order in orders:
        productId = order['productId']
        amount = order['amount']
        encode = 'i' + str(productId) + 'a' + str(amount) + ","
        order_dict['products'] += encode
        c.execute(f"SELECT * FROM product WHERE id={productId}")
        records = c.fetchall()
        columnNames = [column[0] for column in c.description]
        result_dict = dict(zip(columnNames, records[0]))
        if result_dict['inventory'] < amount:
            return f"{result_dict['name']} not enough. {result_dict['inventory']} left but ordering {amount}"
        c.execute(f"UPDATE product set inventory={result_dict['inventory'] - amount} WHERE id={productId}")
        conn.commit()
        result_dict['amount'] = order['amount']
        result.append(result_dict)

    order_dict['products'] = order_dict['products'].strip(",")
    copied_order_dict = copy.copy(order_dict)
    copied_order_dict.pop("id")
    sql = dict_to_sql(copied_order_dict, '`order`')
    c.execute(sql)
    conn.commit()
    order_dict['products'] = result
    c.execute('SELECT MAX(id) from `Order`')
    order_dict['id'] = c.fetchall()[0][0]
    return order_dict


def parse_products(x):
    products = x.split(',')
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    result = []
    for product in products:
        product_id = int(product.split('i')[1].split('a')[0])
        amount = int(product.split('i')[1].split('a')[1])
        c.execute(f"SELECT * FROM `Product` WHERE id={product_id}")
        records = c.fetchall()
        columnNames = [column[0] for column in c.description]
        result_dict = dict(zip(columnNames, records[0]))
        result_dict['amount'] = amount
        result.append(result_dict)
    return result


@app.get("/orders")
async def get_all_order(current_user: User = Depends(get_current_active_user)):
    result = {
        "status": 0,
        "message": 'string',
        "data": []
    }
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM `Order` WHERE buyerEmail='{current_user.email}'")
    records = c.fetchall()
    columnNames = [column[0] for column in c.description]
    for record in records:
        result_dict = dict(zip(columnNames, record))
        result_dict['products'] = parse_products(result_dict['products'])
        result['data'].append(result_dict)

    return result


@app.get("/orders/{product_id}")
async def get_id_order(product_id: int, current_user: User = Depends(get_current_active_user)):
    result = {
        "status": 0,
        "message": 'string'
    }
    conn = sqlite3.connect(DBDIR)
    c = conn.cursor()
    c.execute(f"SELECT * FROM `Order` WHERE (buyerEmail='{current_user.email}' and id={product_id})")
    records = c.fetchall()
    columnNames = [column[0] for column in c.description]
    result_dict = dict(zip(columnNames, records[0]))
    result_dict['products'] = parse_products(result_dict['products'])
    result['data'] = result_dict

    return result


@app.post("/images")
async def post_image(file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    file.filename = f"{uuid.uuid4()}.jpg"
    contents = await file.read()  # <-- Important!
    with open(f"{IMAGEDIR}/{file.filename}", "wb") as f:
        f.write(contents)
    return {"filename": file.filename}
