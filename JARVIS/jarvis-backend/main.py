import os
import io
import shutil
import subprocess
import whisper
import certifi

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
#from openrouter import OpenRouter

from core.intent_router import IntentRouter
from core.intents import Intent
from core.responses import (
    format_email,
    format_email_list,
)
from services.email_service import GmailService
from services.memory_service import MemoryService
from services.memory_extractor import MemoryExtractor
from services.memory_retriever import MemoryRetriever
from models.email_models import CommandRequest
from tempfile import NamedTemporaryFile


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()

FFMPEG_PATH = os.getenv("FFMPEG_PATH")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

# ---------------------------------------------------------
# JARVIS PERSONALITY
# ---------------------------------------------------------

JARVIS_SYSTEM_PROMPT = """
You are JARVIS, a personal AI assistant.

PERSONALITY

You are intelligent, calm, composed, confident, and highly capable.

You communicate like a sophisticated personal assistant rather than
a generic chatbot.

Your tone is:

- Professional but conversational
- Calm and confident
- Concise and direct
- Helpful without being overly enthusiastic
- Occasionally witty or subtly humorous when appropriate
- Respectful and never condescending

You should feel like an assistant who is working alongside the user,
not a search engine or customer-service representative.

COMMUNICATION STYLE

Because your responses are spoken aloud through text-to-speech:

- Prefer concise responses.
- Use natural conversational language.
- Avoid unnecessary headings, bullet points, and long explanations
  unless the user specifically asks for detail.
- Do not repeat the user's question unnecessarily.
- Do not say "As an AI language model."
- Do not constantly say "Sure!", "Absolutely!", or
  "I'd be happy to help."
- Get to the point.

PERSONALITY EXAMPLES

Instead of:

"Hello! How can I assist you today?"

Prefer:

"Good to hear from you. What are we working on?"

Instead of:

"I'm sorry you're experiencing this issue."

Prefer:

"Let's figure out what's going wrong."

Instead of:

"That's a very interesting question."

Prefer:

"Good question. Here's how it works."

HUMOR

You may use subtle, dry humor occasionally.

Do not force jokes into every response.

Do not use humor when the user is discussing something serious,
urgent, emotional, or sensitive.

CONFIDENCE

Be confident when the answer is clear.

When uncertain, say so honestly rather than inventing information.

HONESTY

Never claim to have performed an action unless the system actually
performed it.

Never claim to have accessed an account, file, email, application,
device, or service unless the appropriate tool actually provided
that access.

ASSISTANT BEHAVIOR

Your primary goal is to help the user accomplish tasks efficiently.

When the user asks a simple question, give a simple answer.

When the user asks for a complex explanation, provide a structured
and useful explanation.

When the user is troubleshooting something, focus on diagnosing the
problem and moving toward a solution.

When the user gives you a task, focus on completing it rather than
talking about how helpful you are.

You are JARVIS.

You are the user's personal assistant.
"""
# ---------------------------------------------------------
# WHISPER
# ---------------------------------------------------------

whisper_model = whisper.load_model("base")


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------

app = FastAPI()


# ---------------------------------------------------------
# SERVICES
# ---------------------------------------------------------

intent_router = IntentRouter()
memory_service = MemoryService()

_gmail_service = None


def get_gmail_service():
    global _gmail_service

    if _gmail_service is None:
        _gmail_service = GmailService()

    return _gmail_service



# ---------------------------------------------------------
# OPENROUTER CLIENT
# ---------------------------------------------------------

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

memory_extractor = MemoryExtractor(
    client=client,
    model=OPENROUTER_MODEL
)

memory_retriever = MemoryRetriever(
    client=client,
    model=OPENROUTER_MODEL
)

# ---------------------------------------------------------
# STT
# ---------------------------------------------------------

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):

    temp_in_path = None
    temp_out_path = None

    try:
        # Save the uploaded Android audio to a temporary file
        with NamedTemporaryFile(delete=False) as temp_in:
            shutil.copyfileobj(
                file.file,
                temp_in
            )
            temp_in_path = temp_in.name

        # Create temporary WAV file
        with NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_out:

            temp_out_path = temp_out.name

        # Convert Android recording to 16 kHz mono WAV
        subprocess.run(
            [
                FFMPEG_PATH,
                "-y",
                "-i",
                temp_in_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                temp_out_path
            ],
            check=True
        )

        print(
            "Converted audio size:",
            os.path.getsize(temp_out_path)
        )

        # -------------------------------------------------
        # LOCAL WHISPER
        # -------------------------------------------------

        result = whisper_model.transcribe(
            temp_out_path
        )

        transcript = result["text"].strip()

        print("Transcript:", transcript)

        return {
            "text": transcript
        }

    except Exception as e:

        print("STT ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        # Clean up temporary files
        if temp_in_path and os.path.exists(temp_in_path):
            os.remove(temp_in_path)

        if temp_out_path and os.path.exists(temp_out_path):
            os.remove(temp_out_path)


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.post("/chat")
async def chat(data: dict):

    print(
        "Incoming data:",
        data
    )

    try:

        if not OPENROUTER_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OPENROUTER_API_KEY is not configured."
            )

        if not OPENROUTER_MODEL:
            raise HTTPException(
                status_code=500,
                detail="OPENROUTER_MODEL is not configured."
            )

        user_text = data.get("text", "").strip()

        if not user_text:

            raise HTTPException(
                status_code=400,
                detail="No text provided."
            )


                # -------------------------------------------------
        # MEMORY: DETECT NEW MEMORY AND CORRECTIONS
        # -------------------------------------------------

        existing_memories = memory_service.get_all_memories()

        extraction_result = memory_extractor.extract(
            user_text=user_text,
            existing_memories=existing_memories
        )

        detected_memories = extraction_result.get(
            "memories", []
        )

        superseded_ids = extraction_result.get(
            "supersedes", []
        )

        # Mark outdated memories as superseded
        if superseded_ids:

            updated_count = memory_service.supersede_memories(
                superseded_ids
            )

            print(
                f"Memories superseded: {updated_count} "
                f"(IDs: {superseded_ids})"
            )

        # Save newly detected memories
        for detected_memory in detected_memories:

            memory_text = detected_memory.get(
                "memory", ""
            ).strip()

            category = detected_memory.get(
                "category", "general"
            ).strip()

            if not memory_text:
                continue

            # Check for duplicate memories
            duplicate = memory_service.find_duplicate_memory(
                memory_text
            )

            if duplicate:
                print(
                    f"Duplicate memory skipped: "
                    f"{memory_text} "
                    f"(existing_id={duplicate['id']})"
                )
                continue

            memory_id = memory_service.save_memory(
                memory=memory_text,
                category=category
            )

            print(
                f"Memory saved: {memory_text} "
                f"(category={category}, id={memory_id})"
            )

        # -------------------------------------------------
        # MEMORY: RETRIEVE RELEVANT MEMORIES
        # -------------------------------------------------
        all_memories = memory_service.get_all_memories()
        memories = memory_retriever.retrieve(
            user_text=user_text,
            memories=all_memories
        )
        print(
            "Retrieved memories:",
            memories
        )


        # -------------------------------------------------
        # SPECIAL MEMORY QUESTIONS
        # -------------------------------------------------

        memory_question = any(
            phrase in user_text.lower()
            for phrase in [
                "what do you know about me",
                "what do you remember about me",
                "what do you remember",
                "what do you know about me",
                "tell me what you know about me",
                "what have you remembered about me"
            ]
        )


        if memory_question:

            memories = memory_service.get_all_memories()


        # -------------------------------------------------
        # FORMAT MEMORY CONTEXT
        # -------------------------------------------------

        memory_context = ""

        if memories:

            memory_context = (
                "\n\nRELEVANT MEMORY ABOUT THE USER:\n"
            )

            for memory in memories:

                memory_context += (
                    f"- {memory['memory']}\n"
                )

            memory_context += (
                "\nUse these memories when relevant. "
                "Do not mention the memory system unless "
                "the user asks about it.\n"
            )


        # -------------------------------------------------
        # BUILD JARVIS SYSTEM PROMPT
        # -------------------------------------------------

        system_prompt = (
            JARVIS_SYSTEM_PROMPT
            + memory_context
        )


        # -------------------------------------------------
        # ASK JARVIS
        # -------------------------------------------------

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )


        reply = response.choices[0].message.content


        print(
            "JARVIS:",
            reply
        )


        return {
            "reply": reply
        }


    except HTTPException:
        raise

    except Exception as e:

        print(
            "CHAT ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ---------------------------------------------------------
# TTS
# ---------------------------------------------------------
# NOTE:
# This currently remains connected to the existing
# OpenAI-compatible audio implementation.
#
# OpenRouter is being used for /chat.
# We will replace /tts separately with a dedicated
# TTS solution.
# ---------------------------------------------------------

@app.post("/tts")
async def text_to_speech(data: dict):

    try:

        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=data["text"]
        )

        audio_bytes = b"".join(
            speech.iter_bytes()
        )

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg"
        )

    except Exception as e:

        print("TTS ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------------------------------------------------
# COMMAND
# ---------------------------------------------------------

@app.post("/command")
async def command(data: CommandRequest):

    text = data.text.strip()

    if not text:

        return {
            "success": False,
            "message": "No command provided."
        }

    print(
        f"Jarvis command: {text}"
    )

    intent = intent_router.classify(text)

    print(
        f"Detected intent: {intent}"
    )

    gmail_service = get_gmail_service()


    # -----------------------------------------------------
    # CHECK EMAIL
    # -----------------------------------------------------

    if intent == Intent.CHECK_EMAIL:

        result = gmail_service.list_emails(
            max_results=10,
            query="in:inbox"
        )

        message = format_email_list(
            result.emails
        )

        return {
            "success": True,
            "intent": intent,
            "message": message,
            "emails": [
                email.model_dump()
                for email in result.emails
            ]
        }


    # -----------------------------------------------------
    # READ EMAIL
    # -----------------------------------------------------

    if intent == Intent.READ_EMAIL:

        result = gmail_service.list_emails(
            max_results=1,
            query="in:inbox"
        )

        if not result.emails:

            return {
                "success": True,
                "intent": intent,
                "message": "You don't have any emails."
            }

        email = result.emails[0]

        message = format_email(
            email
        )

        return {
            "success": True,
            "intent": intent,
            "message": message,
            "email": email.model_dump()
        }


    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    return {
        "success": False,
        "intent": Intent.UNKNOWN,
        "message": (
            "I don't know how to handle "
            "that command yet."
        )
    }
