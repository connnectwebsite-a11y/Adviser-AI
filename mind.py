def split_large_text(text, max_chars=30000):
    text = str(text)

    if len(text) <= max_chars:
        return [text] if text else []

    parts = []
    remaining = text

    while len(remaining) > max_chars:
        window = remaining[:max_chars + 1]

        # Prefer paragraph boundaries.
        split_at = window.rfind("\n\n")

        # Then sentence boundaries.
        if split_at < max_chars * 0.5:
            positions = [
                window.rfind(". "),
                window.rfind("? "),
                window.rfind("! ")
            ]

            split_at = max(positions)

            if split_at >= 0:
                split_at += 1

        # Then word boundaries.
        if split_at < max_chars * 0.5:
            split_at = window.rfind(" ")

        # Hard split only as fallback.
        if split_at <= 0:
            split_at = max_chars

        part = remaining[:split_at]

        if len(part) > max_chars:
            part = remaining[:max_chars]
            split_at = max_chars

        parts.append(part)
        remaining = remaining[split_at:]

    if remaining:
        parts.append(remaining)

    return parts


def group_pages(pages, max_chars=30000):
    groups = []

    current_text = []
    current_chars = 0
    start_page = 1
    end_page = 1

    for index, page in enumerate(pages):
        page_number = index + 1

        if isinstance(page, dict):
            page_text = str(page.get("text", ""))
            page_number = page.get(
                "page",
                page_number
            )
        else:
            page_text = str(page)

        parts = split_large_text(
            page_text,
            max_chars=max_chars
        )

        for part in parts:
            separator = 2 if current_text else 0

            if (
                current_text
                and current_chars
                + separator
                + len(part)
                > max_chars
            ):
                groups.append({
                    "start_page": start_page,
                    "end_page": end_page,
                    "text": "\n\n".join(current_text)
                })

                current_text = []
                current_chars = 0

            if not current_text:
                start_page = page_number
            else:
                current_chars += 2

            current_text.append(part)
            current_chars += len(part)
            end_page = page_number

    if current_text:
        groups.append({
            "start_page": start_page,
            "end_page": end_page,
            "text": "\n\n".join(current_text)
        })

    return groups


def summarize_group(client, group):
    prompt = f"""
Study the following material as part of building an
AI adviser.

Extract the deeper thinking behind it rather than
merely summarizing the text.

Preserve:
- core principles
- values and priorities
- reasoning patterns
- decision rules
- recurring themes
- important distinctions
- warnings and cautions
- boundaries and limitations

Do not invent principles that are unsupported by
the material.

Material from pages
{group["start_page"]}-{group["end_page"]}:

{group["text"]}
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1600
            )

            content = response.choices[0].message.content

            if content is not None:
                result = str(content).strip()

                if result:
                    return result

            last_error = RuntimeError(
                f"Empty section summary on attempt {attempt}"
            )

        except Exception as exc:
            # A rate limit will not be fixed by immediately retrying.
            # Stop so we do not make unnecessary API attempts.
            error_text = str(exc).lower()

            if (
                "429" in error_text
                or "rate limit" in error_text
                or "rate_limit" in error_text
            ):
                raise

            last_error = exc

    raise RuntimeError(
        "Section summary failed after 3 attempts: "
        f"{last_error}"
    )

def group_summaries_by_size(
    summaries,
    max_chars=30000
):
    groups = []
    current = []
    current_chars = 0

    for summary in summaries:
        text = str(summary)

        parts = split_large_text(
            text,
            max_chars=max_chars
        )

        for part in parts:
            separator = 2 if current else 0

            if (
                current
                and current_chars
                + separator
                + len(part)
                > max_chars
            ):
                groups.append(current)
                current = []
                current_chars = 0

            if current:
                current_chars += 2

            current.append(part)
            current_chars += len(part)

    if current:
        groups.append(current)

    return groups


def condense_summary_group(client, summaries):
    combined = "\n\n".join(summaries)

    prompt = f"""
Condense the following analyses into one compact
higher-level adviser analysis.

Preserve:
- core principles
- values and priorities
- reasoning patterns
- decision rules
- warnings and cautions
- recurring themes
- important distinctions
- boundaries and limitations

Remove repetition.

Do not invent ideas that are not supported by the
analyses.

ANALYSES:

{combined}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=900
    )

    result = (
        response.choices[0]
        .message.content.strip()
    )

    if not result:
        raise RuntimeError(
            "Summary reduction returned empty."
        )

    return result


def recursively_reduce_summaries(
    client,
    summaries,
    max_chars=30000
):
    current = list(summaries)

    while (
        sum(len(str(x)) for x in current)
        > max_chars
    ):
        groups = group_summaries_by_size(
            current,
            max_chars=max_chars
        )

        reduced = [
            condense_summary_group(
                client,
                group
            )
            for group in groups
        ]

        old_size = sum(
            len(str(x))
            for x in current
        )

        new_size = sum(
            len(str(x))
            for x in reduced
        )

        if (
            len(reduced) >= len(current)
            and new_size >= old_size
        ):
            raise RuntimeError(
                "Recursive synthesis made no progress."
            )

        current = reduced

    return current


def build_adviser_mind(client, pages):
    groups = group_pages(
        pages,
        max_chars=22000
    )

    if not groups:
        raise ValueError(
            "No readable text was found in the document."
        )

    section_summaries = []

    for group in groups:
        summary = summarize_group(
            client,
            group
        )

        # Retry once if the model returns nothing.
        if not summary:
            summary = summarize_group(
                client,
                group
            )

        if not summary:
            raise RuntimeError(
                "A section summary returned empty."
            )

        section_summaries.append({
            "start_page": group["start_page"],
            "end_page": group["end_page"],
            "summary": summary
        })

    # Large books are recursively compressed before
    # the final Adviser Mind synthesis.
    summary_texts = [
        (
            f"PAGES "
            f"{item['start_page']}-"
            f"{item['end_page']}\n"
            f"{item['summary']}"
        )
        for item in section_summaries
    ]

    summary_texts = recursively_reduce_summaries(
        client,
        summary_texts,
        max_chars=30000
    )

    combined = "\n\n".join(summary_texts)

    final_prompt = f"""
Create a durable internal Adviser Mind from the
analyses below.

This is not a normal book summary.

Build a compact representation of:
- core principles
- worldview
- values and priorities
- reasoning patterns
- decision rules
- recurring themes
- important distinctions
- cautions and boundaries

The resulting adviser should be able to apply these
principles thoughtfully to new situations that may
not appear explicitly in the source material.

Do not pretend to be the author.
Do not invent unsupported beliefs.
Do not mention this synthesis process.

SECTION ANALYSES:

{combined}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": final_prompt
            }
        ],
        temperature=0.2,
        max_tokens=1800
    )

    adviser_mind = (
        response.choices[0]
        .message.content.strip()
    )

    if not adviser_mind:
        raise RuntimeError(
            "Final Adviser Mind synthesis returned empty."
        )

    return adviser_mind
