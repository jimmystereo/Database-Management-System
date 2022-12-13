from typing import Optional

from fastapi import FastAPI

import sqlite3
import os
from pydantic import BaseModel

os.chdir('w:\\DBMS')
os.getcwd()


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


class SignIn(BaseModel):
    username: str
    password: str


def execute_sql(s):
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(s)
    conn.commit()
    conn.close()
    return c


# @app.get("/")  # 指定 api 路徑 (get方法)
# def read_root():
#     return {"Hello": "World"}
# app.current_user = None


from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "tommy": {
        "username": "tommy",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": '$2b$12$V1CHy4Iy5vgKcGiSGoylC.IJmre1E83aIy7gmjIk3zK3hkdOlgIpe',
        "disabled": False,
    }

}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class SignInForm(BaseModel):
    username: str
    password: str

class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/signIn")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    # return plain_password == hashed_password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    # return password
    return pwd_context.hash(password)
# get_password_hash("demo")

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# @app.post("/users/signIn", response_model=Token)
@app.post("/users/signIn")
async def login_for_access_token(form_data: SignInForm):
    # return {"Hello": "World"}

    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # return User('aaa')
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


































# # TODO search user
@app.get("/users/{user_id}")  # 指定 api 路徑 (get方法)
def read_user(user_id: int, q: Optional[str] = None):
    return {"user_id": user_id, "q": q}


@app.post("/users")  # 指定 api 路徑 (get方法)
def create_user(user: User):
    # return user.dict()
    execute_sql(
        f"INSERT INTO User (NAME,TYPE,PASSWORD,EMAIL,PHONE) VALUES ('{user.name}', '{user.type}','{user.password}', '{user.email}', '{user.phone}')")
    return user.dict()

#
# TODO
@app.post("/users/signIn")  # 指定 api 路徑 (get方法)
async def login_for_access_token(form_data: SignInForm):
    # return {"Hello": "World"}

    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    # return user.dict()
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(f"SELECT id FROM USER WHERE email='{s.email}' AND password='{s.password}'")
    for row in c:
        id = row[0]
        break
    conn.close()
    return id

#
# TODO
@app.get("/users/me")  # 指定 api 路徑 (get方法)
def me():
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM USER WHERE id={app.current_user}")

    # c = execute_sql(
    #     f"SELECT id FROM User WHERE email='{s.email}' & password='{s.password}'")
    for row in c:
        return row
        break
    conn.close()
    current_user = id
    return id


def json_to_sql(s, table):
    query = "INSERT INTO " + table + " ("
    first = True
    for i in s.dict().keys():
        if not first:
            query += ','
        query += i
        first = False

    query += ") VALUES ("
    first = True
    for i in s.dict().keys():
        if not first:
            query += ','
        item = s.dict()[i]
        if isinstance(item, str):
            item = f"'{item}'"
        query += str(item)
        first = False

    query += ")"
    return query


@app.post("/products")  # 指定 api 路徑 (get方法)
def create_product(product: Product):
    sql = json_to_sql(product, 'product')
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    return product.dict()


@app.get("/products")  # 指定 api 路徑 (get方法)
def get_products():
    result = {"status": 0, "message": "string", "data": []}
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute("SELECT * FROM PRODUCT")
    for row in c:
        row_result = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "picture": row[3],
            "inventory": row[4],
            "price": row[5],
            "startSaleTime": row[6],
            "endSaleTime": row[7]}
        result['data'].append(row_result)
    return result


@app.get("/products/{id}")  # 指定 api 路徑 (get方法)
def get_product(id: int):
    result = {"status": 0, "message": "string", "data": []}
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM PRODUCT WHERE id={id}")
    for row in c:
        row_result = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "picture": row[3],
            "inventory": row[4],
            "price": row[5],
            "startSaleTime": row[6],
            "endSaleTime": row[7]}
        result['data'].append(row_result)
    return result


@app.patch("/products/{id}")  # 指定 api 路徑 (get方法)
def update_product(id: int, product: Product):
    target = product.dict()
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    for i in target.keys():
        if isinstance(target[i], str):
            target[i] = f"'{target[i]}'"
        c.execute(f"UPDATE product set {i}={str(target[i])} WHERE id={id}")
        conn.commit()

    return product.dict()


@app.delete("/products/{id}")
def delete_product(id: int):
    conn = sqlite3.connect('./final.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM product WHERE id={id}")
    conn.commit()
    result = {
        "status": 0,
        "message": "string",
        "data": "string"}
    return result
