from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security_scheme = HTTPBearer()

def create_access_token(data: dict)-> str:
   
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security_scheme)) ->dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        return {"email": email, "role": role}
    except JWTError:
        raise credentials_exception
    

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
 
 
def require_doctor(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    return current_user


def require_patient(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return current_user