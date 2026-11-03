import json
from openai import OpenAI


class MemoryExtractor:

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def extract(self, user_text: str, existing_memories=None):
        """
        Extract useful long-term memories and identify
        existing memories that should be superseded.
        """

        existing_memories = existing_memories or []

        system_prompt = """
You are JARVIS's memory manager.

Your job is to extract useful, long-term information about the
user and identify outdated memories that the new information
explicitly corrects or replaces.

Remember:
- Personal information
- Preferences
- Interests
- Habits
- Goals
- Education
- Career
- Projects
- Long-term plans
- Communication preferences

Do NOT remember:
- Temporary actions
- One-time actions
- Ordinary conversation
- Questions
- Requests
- General knowledge
- Facts about other people
- Temporary plans

IMPORTANT CORRECTION RULES:

1. Compare the user's message with the existing memories provided.
2. If the user explicitly corrects or replaces an existing fact,
   include that old memory's ID in "supersedes".
3. Only supersede memories that genuinely conflict with the
   new information.
4. Do not supersede unrelated memories merely because they
   mention the same technology, person, or project.
5. Do not supersede a historical fact just because the user's
   current situation has changed.
6. A new preference does not automatically replace an old goal.
7. If the user says they are no longer doing something,
   supersede the corresponding current activity memory.
8. If there is no correction, return an empty supersedes list.
9. Never invent memory IDs.

For example:

Existing memory:
{"id": 41, "memory": "Is learning Django."}

User:
"I am no longer learning Django. I'm currently focusing
on improving my FastAPI skills."

Expected result:
{
    "memories": [
        {
            "memory": "Is currently focusing on improving FastAPI skills.",
            "category": "education"
        }
    ],
    "supersedes": [41]
}

Another example:

Existing memory:
{"id": 25, "memory": "My preferred backend technologies are Python, FastAPI, and Django."}

User:
"I am no longer learning Django."

Do NOT supersede ID 25. A technology preference is not the
same thing as a current learning activity.

Return ONLY valid JSON in this format:

{
    "memories": [
        {
            "memory": "A concise statement of the fact.",
            "category": "personal"
        }
    ],
    "supersedes": []
}

Allowed categories:

personal
preference
interest
habit
project
career
education
goal
personality
general

If nothing is worth remembering, return:

{
    "memories": [],
    "supersedes": []
}
"""

        try:

            user_prompt = f"""
EXISTING MEMORIES:

{json.dumps(existing_memories, ensure_ascii=False)}

NEW USER MESSAGE:

{user_text}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0,
                max_tokens=1000,
                extra_body={
                    "reasoning": {
                        "enabled": False
                    }
                }
            )

            content = response.choices[0].message.content

            if not content:
                print("MEMORY EXTRACTION: Empty response")
                return {"memories": [], "supersedes": []}

            content = content.strip()

            if content.startswith("```"):
                content = content.replace("```json", "", 1)
                content = content.replace("```", "").strip()

            result = json.loads(content)

            memories = result.get("memories", [])
            supersedes = result.get("supersedes", [])

            if not isinstance(memories, list):
                memories = []

            if not isinstance(supersedes, list):
                supersedes = []

            # Only allow IDs belonging to existing memories.
            valid_ids = {
                memory["id"]
                for memory in existing_memories
                if "id" in memory
            }

            supersedes = [
                memory_id
                for memory_id in supersedes
                if isinstance(memory_id, int)
                and memory_id in valid_ids
            ]

            return {
                "memories": memories,
                "supersedes": supersedes
            }

        except Exception as e:

            print(
                "MEMORY EXTRACTION ERROR:",
                str(e)
            )

            return {
                "memories": [],
                "supersedes": []
            }