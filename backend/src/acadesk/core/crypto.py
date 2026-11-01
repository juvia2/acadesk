"""연락처 암호화와 검색용 해시, 초대 코드 해시."""

import hashlib
import hmac
import re
import secrets

from cryptography.fernet import Fernet

from acadesk.core.config import get_settings

# 헷갈리는 글자(0/O, 1/I/L) 제외
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 10


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("82"):
        digits = "0" + digits[2:]
    return digits


def encrypt_phone(phone: str) -> bytes:
    return Fernet(get_settings().phone_encryption_key).encrypt(normalize_phone(phone).encode())


def decrypt_phone(token: bytes) -> str:
    return Fernet(get_settings().phone_encryption_key).decrypt(token).decode()


def keyed_hash(value: str, purpose: str) -> str:
    key = get_settings().hash_secret.encode()
    return hmac.new(key, f"{purpose}|{value}".encode(), hashlib.sha256).hexdigest()


def phone_hash(phone: str) -> str:
    return keyed_hash(normalize_phone(phone), "phone")


def mask_phone(last4: str) -> str:
    return f"010-****-{last4}"


def new_invitation_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(code: str) -> str:
    return re.sub(r"[\s-]", "", code).upper()


def code_hash(code: str) -> str:
    return keyed_hash(normalize_code(code), "invitation")


def opaque_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
