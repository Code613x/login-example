from DBManager import VerifyLogin, Getuser_role, SaveRefreshToken, GetUsername,CreateUser, LockRefreshToken, LockRefreshTokens, CheckRefreshToken,init_mfa, verify_mfa
from datetime import datetime, timedelta
import jwt
import uuid
from argon2 import PasswordHasher
from hashlib import sha256
import re
import os
ph = PasswordHasher()

SECRET_KEY = os.environ.get("acces_secret")
REFRESH_SECRET_KEY = os.environ.get("refresh_secret")
TEMP_SECRET = os.environ.get("temp_secret")

def is_valid_email(email: str) -> bool:
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None

def is_sha256_hash(value: str) -> bool:
    return bool(re.fullmatch(r"^[a-f0-9]{64}$", value))

def is_valid_username(username: str) -> bool:
    return bool(re.fullmatch(r"^[a-zA-Z0-9_-]{3,30}$", username))

def GenerateSession(user_id: int, access_exp=None, refresh_exp=None):
    if access_exp is None:
        access_exp = datetime.utcnow() + timedelta(minutes=30)
    if refresh_exp is None:
        refresh_exp = datetime.utcnow() + timedelta(days=7)
    username = GetUsername(user_id)
    access_token = jwt.encode(
        {"user_id": user_id, "username": username, "user_role": Getuser_role(user_id), "exp": access_exp},
        SECRET_KEY,
        algorithm="HS256"
    )
    token_id = str(uuid.uuid4())
    refresh_token = jwt.encode(
        {"user_id": user_id, "token_id": token_id, "exp": refresh_exp},
        REFRESH_SECRET_KEY,
        algorithm="HS256"
    )
    SaveRefreshToken(user_id, token_id)
    return access_token, refresh_token

def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=["HS256"])
        if not CheckRefreshToken(payload["user_id"], payload.get("token_id")):
            return None, True, False, ""
        exp_timestamp = payload.get("exp")
        refreshtoken = False
        if exp_timestamp:
            exp_time = datetime.utcfromtimestamp(exp_timestamp)  
            now = datetime.utcnow()
            if exp_time - now <= timedelta(days=7):
                refreshtoken = True
        acces_token, refresh_token = GenerateSession(payload["user_id"])
        return acces_token, False, refreshtoken, refresh_token
    except jwt.ExpiredSignatureError:
        return None, True, False, ""
    except jwt.InvalidTokenError:
        return None, False, False, ""

def verify_access_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"]), 200
    except jwt.ExpiredSignatureError:
        return {"error": "Access token has expired"}, 401
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}, 400

def register(email: str, password: str, username: str):
    if not is_valid_email(email):
        return {"error": "Email format is incorrect"}
    if not is_sha256_hash(password):
        return {"error": "Password format is incorrect"}
    if not is_valid_username(username):
        return {"error": "Username format is incorrect"}
    password_hashed = ph.hash(password)
    email_hashed = sha256(email.encode()).hexdigest()
    result = CreateUser(email_hashed, password_hashed, username)
    if not result["success"]:
        return {"error": result["error"]}
    access_token, refresh_token = GenerateSession(result["user_id"])
    return {"access_token": access_token, "refresh_token": refresh_token}

def login(email, password):
    if not is_valid_email(email):
        return {"error": "Email format is incorrect"}
    if not is_sha256_hash(password):
        return {"error": "Password format is incorrect"}
    email_hashed = sha256(email.encode()).hexdigest()
    correct, user_id, username = VerifyLogin(email_hashed, password)
    if correct:
        access_token, refresh_token = GenerateSession(user_id)
        return {"msg": "Successfully logged in", "user_id": user_id, "access_token": access_token, "refresh_token": refresh_token}
    return {"error": "Password or email is incorrect"}

def logout(token):
    payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=["HS256"])
    LockRefreshToken(payload["user_id"], payload["token_id"])

def logout_all(token):
    payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=["HS256"])
    LockRefreshTokens(payload["user_id"])

def generate_temp_mfa_token(user_id):
    token = jwt.encode(
        {"user_id": user_id, "mfa_required": True, "exp": datetime.utcnow() + timedelta(minutes=5)},
        TEMP_SECRET,
        algorithm="HS256"
    )
    return token

def verify_temp_mfa_token(token):
    try:
        return True, jwt.decode(token, TEMP_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return False, "Token expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

def CreateRefreshToken(user_id: int):
        token_id = str(uuid.uuid4())
        refresh_exp = datetime.utcnow() + timedelta(days=7)
        refresh_token = jwt.encode(
        {"user_id": user_id, "token_id": token_id, "exp": refresh_exp},
        REFRESH_SECRET_KEY,
        algorithm="HS256"
    )
        return refresh_token