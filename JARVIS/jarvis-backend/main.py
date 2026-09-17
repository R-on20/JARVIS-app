import os
import io
import shutil
import subprocess
import whisper
import certifi
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from openai import OpenAI
from fastapi import HTTPException

from core.intent_router import IntentRouter
from core.intents import Intent
from core.responses import (
    format_email,
    format_email_list,
)
from services.email_service import GmailService
from models.email_models import CommandRequest
from tempfile import NamedTemporaryFile


load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
FFMPEG_PATH = os.getenv("FFMPEG_PATH")
whisper_model = whisper.load_model("base")


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------

app = FastAPI()


# ---------------------------------------------------------
# SERVICES
# ---------------------------------------------------------

intent_router = IntentRouter()

_gmail_service = None


def get_gmail_service():
    global _gmail_service

    if _gmail_service is None:
        _gmail_service = GmailService()

    return _gmail_service


# ---------------------------------------------------------
# OPENAI CLIENT
# ---------------------------------------------------------

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
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

        # Convert the Android recording to 16 kHz mono WAV
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

        # ==============================
        # LOCAL WHISPER
        # ==============================

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
# KEEPING THIS TEMPORARILY FOR THE EXISTING ANDROID APP
# ---------------------------------------------------------

@app.post("/chat")
async def chat(data: dict):

    print(
        "Incoming data:",
        data
    )

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Jarvis, a futuristic "
                    "AI assistant."
                )
            },
            {
                "role": "user",
                "content": data["text"]
            }
        ]
    )

    return {
        "reply": response.choices[0].message.content
    }


# ---------------------------------------------------------
# TTS
# ---------------------------------------------------------

@app.post("/tts")
async def text_to_speech(data: dict):

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

    print(f"Jarvis command: {text}")

    intent = intent_router.classify(text)

    print(f"Detected intent: {intent}")

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

        message = format_email(email)

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