import hashlib

import bcrypt

# pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# deprecated ="auto" this help in future if we change the hashing from bcrypt to something else by automatcally rehashing old passwords


def get_password_hash(password: str):
    # We pre-hadh it with SHA-256 to ensure any length fits in bcrypt
    # This will convert any password into a 64 chatacter string
    password_bytes = password.encode("utf-8")
    digest = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(digest, salt)

    # now hash the digest using bcrypt
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")  # this convert to byte format
    digest = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")
    return bcrypt.checkpw(digest, hashed_password.encode("utf-8"))
