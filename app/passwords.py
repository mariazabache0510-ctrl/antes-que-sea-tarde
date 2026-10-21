from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

# Argon2id is the PasswordHasher default. Parameters stay explicit so the
# choice is visible during the hackathon defense.
_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16)
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False


def verify_dummy(password: str) -> None:
    """Spend the same hash time when the account does not exist."""
    verify_password(password, _DUMMY_HASH)
