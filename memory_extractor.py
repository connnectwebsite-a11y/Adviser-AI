import json


def extract_memory(
    client,
    user_message,
    existing_memories
):
    prompt = f"""
You are the memory manager for an AI adviser.

Determine whether the user's latest message contains
long-term personal information worth remembering or asks
for an existing memory to be changed or forgotten.

Return ONLY valid JSON.

Allowed actions:

1. Add:
{{
  "action": "add",
  "memory": "concise memory",
  "old_memory": ""
}}

2. Replace:
{{
  "action": "replace",
  "memory": "new corrected memory",
  "old_memory": "exact old memory to replace"
}}

3. Delete:
{{
  "action": "delete",
  "memory": "",
  "old_memory": "exact memory to delete"
}}

4. Nothing:
{{
  "action": "none",
  "memory": "",
  "old_memory": ""
}}

Remember durable information such as:
- preferences
- goals
- ongoing projects
- important personal facts
- recurring constraints
- explicit requests to remember something

Do not save:
- casual temporary remarks
- one-off questions
- information with no likely future usefulness
- assistant responses

If the user corrects previously saved information,
prefer "replace".

If the user asks to forget something, use "delete".

EXISTING MEMORIES:
{existing_memories}

LATEST USER MESSAGE:
{user_message}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=180
        )

        raw = (
            response.choices[0]
            .message.content.strip()
        )

        # Some models may wrap JSON in markdown fences.
        if raw.startswith("```"):
            raw = raw.replace(
                "```json",
                "",
                1
            )
            raw = raw.replace(
                "```",
                ""
            ).strip()

        result = json.loads(raw)

        action = str(
            result.get("action", "none")
        ).lower().strip()

        if action not in {
            "add",
            "replace",
            "delete",
            "none"
        }:
            action = "none"

        return {
            "action": action,
            "memory": str(
                result.get("memory", "")
            ).strip(),
            "old_memory": str(
                result.get("old_memory", "")
            ).strip()
        }

    except Exception as error:
        print(
            "Memory extraction error:",
            error
        )

        # Memory failure must never stop the chat.
        return {
            "action": "none",
            "memory": "",
            "old_memory": ""
        }
