import json
from openai import OpenAI


class MemoryExtractor:

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def extract(self, user_text: str):
        """
        Analyze a user's message and determine whether it contains
        information worth remembering long-term.

        Returns a list of memory objects.
        """

        system_prompt = """
You are JARVIS's memory manager.

Your job is to identify useful, long-term information about the user
that JARVIS should remember for future conversations.

Remember information such as:

- Personal information
- Interests and hobbies
- Preferences
- Likes and dislikes
- Habits and routines
- Long-term goals
- Work and career
- Education
- Projects
- Recurring activities
- Communication preferences
- Useful personality traits
- Important long-term plans

Do NOT remember:

- Temporary actions
- One-time actions
- Ordinary conversation
- Questions
- Requests
- Temporary plans
- General knowledge
- Facts about other people
- Information that is unlikely to help JARVIS assist the user
- Small talk

IMPORTANT:

The user does NOT need to explicitly say "remember this".

Use the meaning and context of the message to determine whether
something is worth remembering.

For example:

"I play football."

should be remembered.

"I usually play midfield."

should be remembered.

"I prefer working at night."

should be remembered.

"I'm going to make coffee."

should NOT be remembered.

"I opened VS Code."

should NOT be remembered.

"Remember that my favorite language is Python."

should ALWAYS be remembered.

If a message contains multiple useful facts, extract them separately.

Return ONLY valid JSON in exactly this format:

{
    "memories": [
        {
            "memory": "A concise statement of the fact.",
            "category": "personal"
        }
    ]
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

If there is nothing worth remembering, return:

{
    "memories": []
}
"""

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ],
                temperature=0
            )

            content = response.choices[0].message.content.strip()

            result = json.loads(content)

            memories = result.get("memories", [])

            if not isinstance(memories, list):
                return []

            return memories

        except Exception as e:

            print(
                "MEMORY EXTRACTION ERROR:",
                str(e)
            )

            return []