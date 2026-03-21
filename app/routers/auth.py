import bcrypt
import jwt
import datetime
from fastapi import APIRouter, HTTPException, Response, Request
from app.models import User
from app.database import users_collection
from app.config import SECRET_KEY

router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/signup/")
async def signup(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"email": user.email, "password": hashed_password})
    return {"message": "User created successfully"}

@router.post("/login/")
async def login(user: User, response: Response):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_password = db_user["password"]
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    if not bcrypt.checkpw(user.password.encode('utf-8'), stored_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({"sub": user.email, "exp": expiration}, SECRET_KEY, algorithm="HS256")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        expires=86400,
        samesite="none",
        secure=True, 
    )
    return {"message": "Login successful"}

@router.post("/logout/")
async def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@router.get("/verify/")
async def verify_session(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")