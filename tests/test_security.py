from src.utils.security import get_password_hash, verify_password


def test_password_hashing_success():
    password = "StrongPassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_password_verification_failure():
    password = "CorrectPass"
    wrong_pasword = "WrongPass"
    hashed = get_password_hash(password)

    assert verify_password(wrong_pasword, hashed) is False


def test_bcrypt_72_byte_limit_handling():
    long_password = "a" * 100
    hashed = get_password_hash(long_password)

    assert verify_password(long_password, hashed) is True
