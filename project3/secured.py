from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerifyMismatchError

ph = PasswordHasher(type=Type.ID)

def hash_password(plain_password: str) -> str:
    return ph.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False
    


