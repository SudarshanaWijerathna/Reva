from argon2 import PasswordHasher


salt = "HGYG^S%SG^&^6GVS6S^tg6s6s7s&S&&^7gygYfyg^Rggv&7TCR6" 
ph = PasswordHasher()


def hashing(password: str):
    password_with_salt = password + salt
    hashed_password = ph.hash(password_with_salt)
    return hashed_password

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        ph.verify(hashed_password, password + salt)
        return True
    except:
        return False