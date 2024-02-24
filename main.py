from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv

import openai
import os


load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    

# Funtions
def transcribe_audio(file):
    audio_file= open(file.filename, "rb")
    transcript = openai.audio.transcriptions.create(model="whisper-1",file=audio_file)
    print(transcript)
    return {"message": transcript.text}
