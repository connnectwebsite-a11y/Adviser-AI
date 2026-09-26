
def run_safe_sampled_batch(
    sampled_processor,
    processor,
    mind_module,
    client,
    book_path,
    readable_pages,
    max_groups=3,
    sample_count=12
):
    """
    Safely process representative Adviser Mind samples.

    The full book remains available separately for
    FAISS retrieval.
    """

    before = sampled_processor.sampled_status(
        processor=processor,
        book_path=book_path,
        pages=readable_pages,
        mind_module=mind_module,
        sample_count=sample_count
    )

    print("=" * 60)
    print("ADVISER AI — SAMPLED BOOK BATCH")
    print("=" * 60)

    print("Samples:", before["sample_numbers"])
    print("Completed:", before["completed"])
    print("Pending:", before["pending"])

    if not before["pending"]:
        print("All Adviser Mind samples are complete.")
        return before

    print("Starting from:", before["pending"][0])
    print("Maximum new samples:", max_groups)

    result = sampled_processor.process_sampled_groups(
        processor=processor,
        mind_module=mind_module,
        client=client,
        book_path=book_path,
        pages=readable_pages,
        max_new_groups=max_groups,
        sample_count=sample_count
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
        "Completed samples:",
        result["completed"]
    )

    print(
        "Still required:",
        result["pending"]
    )

    if result.get("stopped_reason") == "rate_limit":
        print("Groq rate limit reached.")
        print(
            "Resume from sampled group:",
            result["next_group"]
        )
        print("Completed work is safely checkpointed.")

    elif not result["pending"]:
        print("ALL ADVISER MIND SAMPLES COMPLETE")

    else:
        print(
            "Next sampled group:",
            result["next_group"]
        )

    return result
