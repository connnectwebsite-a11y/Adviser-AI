
def select_sample_groups(groups, sample_count=12):
    """
    Select representative groups evenly across
    the beginning, middle and end of a book.
    """

    total = len(groups)

    if total <= sample_count:
        return list(range(total))

    return sorted(set(
        round(
            i * (total - 1) / (sample_count - 1)
        )
        for i in range(sample_count)
    ))


def sampled_status(
    processor,
    book_path,
    pages,
    mind_module,
    sample_count=12
):
    groups = mind_module.group_pages(
        pages,
        max_chars=22000
    )

    indexes = select_sample_groups(
        groups,
        sample_count
    )

    numbers = [
        index + 1
        for index in indexes
    ]

    folder = processor.get_book_checkpoint_dir(
        book_path
    )

    completed = []
    pending = []

    for number in numbers:
        saved = processor.load_group_summary(
            folder,
            number
        )

        if saved:
            completed.append(number)
        else:
            pending.append(number)

    return {
        "sample_numbers": numbers,
        "completed": completed,
        "pending": pending,
        "total_samples": len(numbers),
        "folder": str(folder),
    }


def process_sampled_groups(
    processor,
    mind_module,
    client,
    book_path,
    pages,
    max_new_groups=3,
    sample_count=12
):
    """
    Process only representative Adviser Mind groups.

    The entire book can still be embedded separately
    into FAISS for retrieval.
    """

    groups = mind_module.group_pages(
        pages,
        max_chars=22000
    )

    indexes = select_sample_groups(
        groups,
        sample_count
    )

    folder = processor.get_book_checkpoint_dir(
        book_path
    )

    processed_now = []

    for index in indexes:

        number = index + 1

        existing = processor.load_group_summary(
            folder,
            number
        )

        if existing:
            continue

        if len(processed_now) >= max_new_groups:
            break

        try:
            summary = mind_module.summarize_group(
                client,
                groups[index]
            )

        except Exception as exc:
            error_text = str(exc).lower()

            if (
                "429" in error_text
                or "rate limit" in error_text
                or "rate_limit" in error_text
            ):
                status = sampled_status(
                    processor,
                    book_path,
                    pages,
                    mind_module,
                    sample_count
                )

                status["processed_now"] = processed_now
                status["stopped_reason"] = "rate_limit"
                status["next_group"] = number

                return status

            raise

        if not summary or not summary.strip():
            raise RuntimeError(
                f"Sampled group {number} returned empty summary."
            )

        processor.save_group_summary(
            folder,
            number,
            summary.strip()
        )

        processed_now.append(number)

    status = sampled_status(
        processor,
        book_path,
        pages,
        mind_module,
        sample_count
    )

    status["processed_now"] = processed_now
    status["stopped_reason"] = None

    if status["pending"]:
        status["next_group"] = status["pending"][0]
    else:
        status["next_group"] = None

    return status

def collect_sampled_summaries(
    processor,
    mind_module,
    book_path,
    pages,
    sample_count=12
):
    """
    Collect representative summaries in original
    book order for final Adviser Mind generation.
    """

    status = sampled_status(
        processor=processor,
        book_path=book_path,
        pages=pages,
        mind_module=mind_module,
        sample_count=sample_count
    )

    folder = processor.get_book_checkpoint_dir(
        book_path
    )

    summaries = []
    missing = []

    for number in status["sample_numbers"]:

        saved = processor.load_group_summary(
            folder,
            number
        )

        if saved:
            summaries.append({
                "group": number,
                "summary": saved
            })
        else:
            missing.append(number)

    return {
        "summaries": summaries,
        "missing": missing,
        "complete": len(missing) == 0
    }

def build_sampled_adviser_mind(
    processor,
    mind_module,
    client,
    book_path,
    pages,
    sample_count=12
):
    """
    Build the final Adviser Mind from completed
    representative summaries.

    No final mind is generated until every required
    sampled summary exists.
    """

    collection = collect_sampled_summaries(
        processor=processor,
        mind_module=mind_module,
        book_path=book_path,
        pages=pages,
        sample_count=sample_count
    )

    if not collection["complete"]:
        missing = collection["missing"]

        raise RuntimeError(
            "Sampled Adviser Mind is not ready. "
            f"Missing groups: {missing}"
        )

    summaries = [
        item["summary"]
        for item in collection["summaries"]
    ]

    if not summaries:
        raise RuntimeError(
            "No sampled summaries are available."
        )

    # Reuse the existing recursive condensation logic
    final_mind = mind_module.condense_summary_group(
        client,
        summaries
    )

    if not final_mind or not final_mind.strip():
        raise RuntimeError(
            "Final Adviser Mind returned empty."
        )

    return final_mind.strip()

def adviser_mind_progress(
    processor,
    mind_module,
    book_path,
    pages,
    sample_count=12
):
    """
    Return progress for sampled Adviser Mind generation.
    Makes no AI/API calls.
    """

    status = sampled_status(
        processor=processor,
        book_path=book_path,
        pages=pages,
        mind_module=mind_module,
        sample_count=sample_count
    )

    total = status["total_samples"]
    completed_count = len(status["completed"])

    percent = (
        completed_count / total * 100
        if total
        else 100.0
    )

    return {
        **status,
        "completed_count": completed_count,
        "remaining_count": len(status["pending"]),
        "percent": percent,
        "next_group": (
            status["pending"][0]
            if status["pending"]
            else None
        )
    }

