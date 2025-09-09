from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import psycopg2
import uvicorn

# JWT Config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI()

# Database connection
def get_db():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
    return conn

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TokenRequest(BaseModel):
    token: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(username: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM iam.users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"username": row[0], "password": row[1]}
    return None

def create_user(username: str, password: str):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO iam.users (username, password) VALUES (%s, %s)", (username, get_password_hash(password)))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    cur.close()
    conn.close()

# Endpoints

@app.post("/create")
def create(user: UserCreate):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    create_user(user.username, user.password)
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = get_user(user.username)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/validate")
def validate(token_req: TokenRequest):
    try:
        payload = jwt.decode(token_req.token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or not get_user(username):
            return {"isValid": False}
    except JWTError:
        return {"isValid": False}
    return {"isValid": True}

def main():
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()