
import json
import hashlib
from pathlib import Path
from storage import get_data_root

from mind import summarize_group, group_pages


CHECKPOINT_ROOT = (
    get_data_root() / "book_checkpoints"
)



def book_fingerprint(book_path):
    """Create a stable ID for a PDF."""
    hasher = hashlib.sha256()

    with open(book_path, "rb") as file:
        while True:
            block = file.read(1024 * 1024)

            if not block:
                break

            hasher.update(block)

    return hasher.hexdigest()[:16]


def get_book_checkpoint_dir(book_path):
    fingerprint = book_fingerprint(book_path)

    folder = CHECKPOINT_ROOT / fingerprint

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder


def save_group_summary(folder, group_number, summary):
    path = folder / f"group_{group_number:03}.txt"

    path.write_text(
        summary,
        encoding="utf-8"
    )


def load_group_summary(folder, group_number):
    path = folder / f"group_{group_number:03}.txt"

    if not path.exists():
        return None

    text = path.read_text(
        encoding="utf-8"
    ).strip()

    return text or None


def checkpoint_status(book_path, pages):
    folder = get_book_checkpoint_dir(book_path)

    groups = group_pages(
        pages,
        max_chars=22000
    )

    completed = []
    pending = []

    for number in range(1, len(groups) + 1):
        if load_group_summary(folder, number):
            completed.append(number)
        else:
            pending.append(number)

    return {
        "folder": str(folder),
        "total_groups": len(groups),
        "completed": completed,
        "pending": pending,
    }


def process_book_groups(
    client,
    book_path,
    pages,
    max_new_groups=5
):
    """
    Process only a limited number of unfinished groups.

    Already completed groups are loaded from Google Drive
    instead of being sent to Groq again.
    """

    folder = get_book_checkpoint_dir(book_path)

    groups = group_pages(
        pages,
        max_chars=22000
    )

    processed_now = []

    for number, group in enumerate(groups, start=1):

        existing = load_group_summary(
            folder,
            number
        )

        if existing:
            continue

        if len(processed_now) >= max_new_groups:
            break

        try:
            summary = summarize_group(
                client,
                group
            )

        except Exception as exc:
            error_text = str(exc).lower()

            if (
                "429" in error_text
                or "rate limit" in error_text
                or "rate_limit" in error_text
            ):
                status = checkpoint_status(
                    book_path,
                    pages
                )

                status["processed_now"] = processed_now
                status["stopped_reason"] = "rate_limit"
                status["next_group"] = number

                return status

            raise

        if not summary or not summary.strip():
            raise RuntimeError(
                f"Group {number} returned an empty summary."
            )

        save_group_summary(
            folder,
            number,
            summary.strip()
        )

        processed_now.append(number)

    status = checkpoint_status(
        book_path,
        pages
    )

    status["processed_now"] = processed_now

    return status
