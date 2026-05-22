import bcrypt


def hashear(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar(password: str, hash_str: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_str.encode())
