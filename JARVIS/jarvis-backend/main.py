import os
#import ssl
import certifi
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
#import httpx
from openai import OpenAI
import io
from tempfile import NamedTemporaryFile
import subprocess
import shutil
from dotenv import load_dotenv
load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()


##client = httpx.Client(verify=certifi.where())

app = FastAPI()

# Test route to verify the server runs
#@app.get("/")
#async def root():
 #   return {"message": "Jarvis backend is running!"}

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
#speech to text endpoint(hearing)
# ---------------- STT ----------------
@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):

    allowed_types = [
        "audio/wav", "audio/mpeg", "audio/mp3", "audio/mp4",
        "audio/ogg", "audio/webm", "audio/flac", "audio/m4a"
    ]

    if file.content_type not in allowed_types:
        with NamedTemporaryFile(delete=False) as temp_in:
            shutil.copyfileobj(file.file, temp_in)
            temp_in_path = temp_in.name

        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_out:
            temp_out_path = temp_out.name

        subprocess.run([
                    "ffmpeg",
                    "-y",
                    "-i", temp_in_path,
                    "-ar", "16000",   # resample to 16kHz
                    "-ac", "1",       # mono
                    temp_out_path],
                check=True)
        print("File size:", os.path.getsize(temp_out_path))

        with open(temp_out_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                file=f,
                model="whisper-1"
            )
    else:
        transcript = client.audio.transcriptions.create(
            file=file.file,
            model="whisper-1"
        )

    return {"text": transcript.text}


# ---------------- CHAT ----------------
@app.post("/chat")
async def chat(data: dict):

    print("Incoming data:", data)
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are Jarvis, a futuristic AI assistant."},
            {"role": "user", "content": data["text"]}
        ]
    )

    return {"reply": response.choices[0].message.content}


# ---------------- TTS ----------------
@app.post("/tts")
async def text_to_speech(data: dict):

    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=data["text"]
    )

    audio_bytes = b"".join(speech.iter_bytes())

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg"
    )