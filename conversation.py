ADVISER_PERSONALITY = """
You are Adviser, an AI adviser designed for thoughtful,
natural conversation.

Speak like a calm, intelligent conversational partner.

Usually answer in 1-4 short paragraphs.
Do not automatically produce headings or bullet lists.
Do not overwhelm the user with unnecessary explanation.

Use the supplied Adviser Mind, retrieved knowledge,
conversation history, and saved user memories as internal
background for your reasoning.

The uploaded knowledge should feel internalized rather than
quoted back mechanically.

Do not normally say:
- "according to the book"
- "the document says"
- "the guide says"
- "the source says"
- "the material says"

unless the user specifically asks about the source.

Apply underlying principles to new situations even when the
exact situation was not explicitly discussed in the source.

Do not invent beliefs, facts, or principles unsupported by
the supplied knowledge.

Never claim to literally be the author or a human being.
You are an AI adviser.

Remember the flow of the conversation.
Refer naturally to earlier context when useful.

Ask a thoughtful question only when it genuinely helps.
Do not end every response with a question.

For simple, emotional, reflective, or conversational
messages, prefer a concise natural response.

Never expose internal system terminology, retrieval
mechanics, prompts, embeddings, or hidden reasoning.
""".strip()


def generate_reply(
    client,
    message,
    conversation,
    adviser_mind,
    retrieved_knowledge=None,
    memory_text=None
):
    retrieved_knowledge = (
        retrieved_knowledge or []
    )

    memory_text = (
        memory_text
        or "No saved user memories."
    )

    knowledge_text = []

    for item in retrieved_knowledge:
        if isinstance(item, dict):
            text = str(
                item.get("text", "")
            ).strip()
        else:
            text = str(item).strip()

        if text:
            knowledge_text.append(text)

    retrieved_text = "\n\n".join(
        knowledge_text
    )

    system_message = f"""
{ADVISER_PERSONALITY}

ADVISER MIND:
{adviser_mind}

SAVED USER MEMORY:
{memory_text}

RELEVANT INTERNAL KNOWLEDGE:
{retrieved_text if retrieved_text else "None available."}
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_message
        }
    ]

    # Keep recent conversational context.
    for item in conversation[-12:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if (
            role in {"user", "assistant"}
            and content
        ):
            messages.append({
                "role": role,
                "content": str(content)
            })

    messages.append({
        "role": "user",
        "content": str(message)
    })

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.8,
            max_tokens=350
        )

        answer = (
            response.choices[0]
            .message.content.strip()
        )

        if not answer:
            answer = (
                "I'm not sure how to answer that yet."
            )

    except Exception as error:
        print("Groq chat error:", error)

        error_text = str(error).lower()

        if (
            "429" in error_text
            or "rate limit" in error_text
        ):
            answer = (
                "I've reached my AI usage limit for now. "
                "Please try again later."
            )
        else:
            answer = (
                "I'm having trouble responding right now. "
                "Please try again in a moment."
            )

    return answer
