import hashlib
import os


DRIVE_CACHE_DIR = (
    "/content/drive/MyDrive/"
    "AdviserAI/mind_cache"
)

LOCAL_CACHE_DIR = (
    "/content/adviser/data/mind_cache"
)

# Change this whenever the Adviser Mind
# synthesis algorithm changes.
MIND_PIPELINE_VERSION = "mind-v2"


def get_cache_dir():
    if os.path.isdir("/content/drive/MyDrive"):
        cache_dir = DRIVE_CACHE_DIR
    else:
        cache_dir = LOCAL_CACHE_DIR

    os.makedirs(
        cache_dir,
        exist_ok=True
    )

    return cache_dir


def file_fingerprint(file_path):
    sha = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)

            if not block:
                break

            sha.update(block)

    return sha.hexdigest()


def versioned_fingerprint(file_hash):
    value = (
        MIND_PIPELINE_VERSION
        + ":"
        + str(file_hash)
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def cache_path(fingerprint):
    return os.path.join(
        get_cache_dir(),
        f"{fingerprint}.txt"
    )


def save_cached_mind(
    fingerprint,
    adviser_mind
):
    path = cache_path(fingerprint)

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(str(adviser_mind))

    return path


def load_cached_mind(fingerprint):
    path = cache_path(fingerprint)

    if not os.path.exists(path):
        return None

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()
