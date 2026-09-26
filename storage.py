import os
from pathlib import Path


DRIVE_DATA_ROOT = Path(
    "/content/drive/MyDrive/AdviserAI"
)

FALLBACK_DATA_ROOT = Path(
    "/tmp/AdviserAI"
)


def get_data_root():
    """
    Return Adviser AI's writable data root.

    Priority:
    1. ADVISER_DATA_DIR environment variable
    2. Google Drive when available in Colab
    3. /tmp/AdviserAI fallback
    """

    configured = os.getenv(
        "ADVISER_DATA_DIR",
        ""
    ).strip()

    if configured:
        return Path(
            configured
        ).expanduser()

    if Path(
        "/content/drive/MyDrive"
    ).is_dir():
        return DRIVE_DATA_ROOT

    return FALLBACK_DATA_ROOT
