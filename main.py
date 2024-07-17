from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

import os
import openai
import json
import requests

load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response.content)
    #print("audio output: " + audio_output)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="audio/mpeg")
    

def transcribe_audio(file):
    audio_file= open(file.filename, "rb")
    transcript = openai.audio.transcriptions.create(model="whisper-1",file=audio_file)
    #print(transcript)
    return transcript


def get_chat_response(user_message):
    messages = load_messages()
    messages.append({"role": "user", "content": user_message.text})
    
    gpt_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
        )
    
    parsed_gpt_response = gpt_response.choices[0].message
    #print(parsed_gpt_response.content)
    save_messages(user_message.text, parsed_gpt_response)

    return parsed_gpt_response
    
    
def load_messages():
    messages = []
    file = "database.json"
    
    empty = os.stat(file).st_size == 0
    
    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)
                
    else:
        messages.append(
            {"role": "system", "content": "You are a rude assistant, who doesn't help but tricks the people."}
        )
    return messages


def save_messages(user_message, gpt_response):
    file = "database.json"
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": gpt_response.role, "content": gpt_response.content})
    with open(file, 'w') as f:
        json.dump(messages, f)


def text_to_speech(text):
    voice_id = "pNInz6obpgDQGcFmaJgB"

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
