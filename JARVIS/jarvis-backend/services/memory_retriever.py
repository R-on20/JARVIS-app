import json
from typing import List, Dict
#
# from urllib import response
from openai import OpenAI


class MemoryRetriever:

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def analyze(self, user_text: str):
        """
        Determine whether the user's message requires memory
        and, if so, what kind of memory is relevant.
        """

        system_prompt = """
You are JARVIS's memory retrieval manager.

Your job is to understand a user's message and determine whether
existing memories about the user would help JARVIS answer it.

IMPORTANT:

Understand the meaning of the user's message.

Do NOT depend on exact keywords.

Only return needs_memory=true when the user is asking
about themselves, their history, preferences, habits,
projects, goals, career, education, interests, or other
information that JARVIS may have learned about them.

Do NOT retrieve personal memory merely because the question
could benefit from knowing the user's location or circumstances.

Questions about current events, weather, general knowledge,
technical topics, programming, mathematics, or other external
information should normally return needs_memory=false.

For example:

"What kind of things am I into?"
→ memory required

"What do I enjoy?"
→ memory required

"What am I working on these days?"
→ memory required

"What's my name?"
→ memory required

"What time do I tend to work?"
→ memory required

"What's the weather like today?"
→ memory not required

"How do I create a FastAPI endpoint?"
→ memory not required

"What's happening in Kenya today?"
→ memory not required

The user may express the same idea in many different ways.

For example:

"What kind of things am I into?"
"What do I enjoy?"
"What are my interests?"
"What do I usually do for fun?"

These can all refer to the user's interests.

Similarly:

"What am I working on these days?"
"What projects am I involved in?"
"What have I been building lately?"

can refer to the user's projects.

Return ONLY valid JSON in exactly this format:

{
    "needs_memory": true,
    "query": "A natural-language description of the information we should retrieve.",
    "categories": ["interest", "preference"]
}

If existing memories are not relevant, return:

{
    "needs_memory": false,
    "query": "",
    "categories": []
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

Do not answer the user's question.

Only analyze what information should be retrieved.
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
                temperature=0,
                max_tokens=500,
                extra_body={
                    "reasoning": {
                        "enabled": False
                    }
                }
            )

            content = response.choices[0].message.content.strip()

            result = json.loads(content)

            if not isinstance(result, dict):
                return {
                    "needs_memory": False,
                    "query": "",
                    "categories": []
                }

            return {
                "needs_memory": bool(
                    result.get("needs_memory", False)
                ),
                "query": str(
                    result.get("query", "")
                ).strip(),
                "categories": result.get(
                    "categories",
                    []
                )
            }

        except Exception as e:
            print(
                "MEMORY RETRIEVAL ANALYSIS ERROR:",
                str(e)
            )

            return {
                "needs_memory": False,
                "query": "",
                "categories": []
            }

    def retrieve(
        self,
        user_text: str,
        memories: List[Dict]
    ) -> List[Dict]:
        """
        Select memories that are semantically relevant
        to the user's message.
        """

        if not memories:
            return []

        analysis = self.analyze(user_text)

        if not analysis["needs_memory"]:
            return []

        memory_candidates = [
            {
                "id": memory["id"],
                "memory": memory["memory"],
                "category": memory["category"]
            }
            for memory in memories
        ]

        system_prompt = """
You are a memory retrieval system for a personal AI assistant.

Your task is to select only the most useful stored memories for answering
the user's current message.

RULES:

1. Select memories based on semantic relevance, not just matching keywords.
2. Return a maximum of 5 memory IDs.
3. Prefer specific memories over large, general profile summaries.
4. Avoid selecting duplicate or repetitive memories.
5. Do not select unrelated memories simply to provide more context.
6. Consider the user's actual question and what information would help answer it.
7. If a memory contains several unrelated facts, prefer more specific memories
   when available.
8. Never invent memory IDs.

For questions about:
- Interests: select hobbies, activities, and things the user enjoys.
- Projects: select current projects and relevant project details.
- Career: select education, experience, skills, and career goals.
- Preferences: select directly relevant personal preferences.
- Personal facts: select only the facts needed to answer the question.

For questions about habits or past experiences, distinguish between
what the user currently does and what they used to do.

Return ONLY valid JSON in this format:
{"memory_ids": [1, 2, 3]}

If no memories are relevant, return:
{"memory_ids": []}
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
                        "content": json.dumps({
                            "user_message": user_text,
                            "retrieval_intent": analysis,
                            "available_memories": memory_candidates
                        })
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

            message = response.choices[0].message

            content = message.content

            if not content:
                print("\n========== MODEL RESPONSE DIAGNOSTICS ==========")

                print(
                    "MODEL:",
                     response.model
                )

                print(
                    "FINISH REASON:",
                    response.choices[0].finish_reason
                )

                print(
                    "MESSAGE:",
                     message.model_dump()
                )

                print(
                    "USAGE:",
                    response.usage
                )

                print("================================================\n")

                return []

            content = content.strip()
            result = json.loads(content)

            memory_ids = result.get("memory_ids", [])

            if not isinstance(memory_ids, list):
                return []

            valid_ids = {
                memory["id"]
                for memory in memories
            }

            selected_ids = {
                memory_id
                for memory_id in memory_ids
                if isinstance(memory_id, int) 
                and memory_id in valid_ids
            }

            return [
                memory
                for memory in memories
                if memory["id"] in selected_ids
            ]

        except Exception as e:
            print(
                "MEMORY SELECTION ERROR:",
                str(e)
            )

            return []

# TEMPORARY TESTING CODE
if __name__ == "__main__":

    from dotenv import load_dotenv
    from memory_service import MemoryService
    import os

    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    retriever = MemoryRetriever(
        client=client,
        model=os.getenv("OPENROUTER_MODEL")
    )

    memory_service = MemoryService()

    test_questions = [
        "What kind of things am I into?",
        "What am I working on these days?",
        "Do you remember what position I usually play?",
        "What are my career goals?",
        "What are my ambitions?",
        "What is my educational background?",
        "What are my hobbies?"
        
    ]

    all_memories = memory_service.get_all_memories()

    for question in test_questions:

        print("\n" + "=" * 60)
        print("USER:", question)

        selected_memories = retriever.retrieve(
            user_text=question,
            memories=all_memories
        )

        print("\nSELECTED MEMORIES:")

        if selected_memories:
            for memory in selected_memories:
                print(
                    f"ID: {memory['id']} | "
                    f"Category: {memory['category']} | "
                    f"Memory: {memory['memory']}"
                )
        else:
            print("No relevant memories found.")