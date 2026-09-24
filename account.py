import uuid

from auth import (
    hash_password,
    verify_password
)

from database import (
    create_user,
    get_user_by_username
)


def normalize_username(username):
    return str(username).strip().lower()


def validate_credentials(
    username,
    password
):
    username = normalize_username(username)
    password = str(password)

    if len(username) < 3:
        return (
            False,
            "Username must be at least 3 characters."
        )

    if len(username) > 50:
        return (
            False,
            "Username is too long."
        )

    if len(password) < 8:
        return (
            False,
            "Password must be at least 8 characters."
        )

    return True, ""


def signup(username, password):
    username = normalize_username(username)

    valid, error = validate_credentials(
        username,
        password
    )

    if not valid:
        return {
            "success": False,
            "user_id": None,
            "message": error
        }

    if get_user_by_username(username):
        return {
            "success": False,
            "user_id": None,
            "message": "Username already exists."
        }

    user_id = "user_" + str(uuid.uuid4())

    password_hash = hash_password(
        password
    )

    created = create_user(
        user_id,
        username,
        password_hash
    )

    if not created:
        return {
            "success": False,
            "user_id": None,
            "message": "Username already exists."
        }

    return {
        "success": True,
        "user_id": user_id,
        "message": "Account created."
    }


def login(username, password):
    username = normalize_username(username)

    user = get_user_by_username(
        username
    )

    # Keep the public error deliberately generic.
    if (
        user is None
        or not verify_password(
            password,
            user["password_hash"]
        )
    ):
        return {
            "success": False,
            "user_id": None,
            "message": "Invalid username or password."
        }

    return {
        "success": True,
        "user_id": user["id"],
        "message": "Logged in."
    }
