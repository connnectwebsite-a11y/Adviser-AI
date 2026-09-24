import hashlib
import hmac
import os


ITERATIONS = 600_000


def hash_password(password):
    password = str(password)

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password,
    stored_password
):
    try:
        salt_hex, hash_hex = (
            str(stored_password)
            .split(":", 1)
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected_hash = bytes.fromhex(
            hash_hex
        )

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt,
            ITERATIONS
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (
        ValueError,
        TypeError
    ):
        return False
