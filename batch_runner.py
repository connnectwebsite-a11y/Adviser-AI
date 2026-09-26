
def run_safe_book_batch(
    processor,
    client,
    book_path,
    readable_pages,
    max_groups=5
):
    """
    Resume large-book processing safely.

    Completed groups are skipped.
    Successful groups are checkpointed.
    Rate limits cause a clean stop.
    """

    before = processor.checkpoint_status(
        book_path,
        readable_pages
    )

    print("=" * 60)
    print("ADVISER AI — SAFE BOOK BATCH")
    print("=" * 60)

    print("Already completed:", len(before["completed"]))
    print("Remaining:", len(before["pending"]))

    if not before["pending"]:
        print("Entire book is already processed.")
        return before

    print("Starting from group:", before["pending"][0])
    print("Maximum new groups:", max_groups)

    result = processor.process_book_groups(
        client=client,
        book_path=book_path,
        pages=readable_pages,
        max_new_groups=max_groups
    )

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        "Processed this run:",
        result.get("processed_now", [])
    )

    print(
        "Total completed:",
        len(result["completed"])
    )

    print(
        "Remaining:",
        len(result["pending"])
    )

    if result.get("stopped_reason") == "rate_limit":
        print("Groq rate limit reached.")
        print(
            "Resume later from group:",
            result.get("next_group")
        )
        print("All successful work is safely checkpointed.")

    elif not result["pending"]:
        print("ALL BOOK GROUPS COMPLETE")

    else:
        print(
            "Next pending group:",
            result["pending"][0]
        )

    return result
