from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

import os
import openai
import json
import requests
import json
import os
import time

import dynamodb
import localdb
import sqldb

load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")


# Choose the database that you want to use
#dbservice = localdb
dbservice = dynamodb
#dbservice = sqldb

app = FastAPI()

#if __name__ == '__main__':


@app.get("/")
async def root():
    return {"message": "Sorry, no frontend. For APIs, check <this-site>/docs"}


@app.post("/talk")
async def post_audio(file: UploadFile):    
    await save_file(file)
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response.content)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


async def save_file(file): 
    with open(file.filename, 'wb') as f:
        content = await file.read()
        f.write(content)
        print(f"Received file named: {file.filename} ,containing: {len(content)} bytes. ")


def transcribe_audio(file):
    audio_file= open(file.filename, "rb")
    transcript = openai.audio.transcriptions.create(model="whisper-1",file=audio_file)
    return transcript


def get_chat_response(user_message):
    messages = dbservice.load_messages()
    messages.append({"role": "user", "content": user_message.text})
    
    gpt_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
        )
    
    parsed_gpt_response = gpt_response.choices[0].message
    dbservice.save_messages(user_message.text, parsed_gpt_response)
    return parsed_gpt_response


def text_to_speech(text):
    voice_id = "pNInz6obpgDQGcFmaJgB" # Adam

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_key
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.request("POST", url, json=data, headers=headers)
        if response.status_code == 200:
            with open('output.mp3', 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return response.content
        else:
            print("Something went wrong, status code: ", response.status_code)
    except Exception as e:
        print("text to speech error")
