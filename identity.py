import uuid


# DEVELOPMENT ONLY.
# Used when no authenticated user exists.
DEV_USER_ID = "adviser_dev_user"


def create_session_id():
    """
    Creates a temporary conversation/session ID.
    """
    return str(uuid.uuid4())


def memory_user_id(
    session_id,
    authenticated_user_id=None
):
    """
    Returns the identity used for persistent memory.

    Production:
        authenticated_user_id

    Development:
        adviser_dev_user

    The session_id is intentionally NOT used as
    long-term identity because a new browser session
    should not destroy persistent user memory.
    """

    if authenticated_user_id:
        user_id = str(
            authenticated_user_id
        ).strip()

        if user_id:
            return user_id

    return DEV_USER_ID


def is_development_identity(user_id):
    """
    Identifies whether the shared development identity
    is currently being used.
    """
    return (
        str(user_id).strip()
        == DEV_USER_ID
    )
