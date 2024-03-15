from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv

import openai
import os
import json

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
    chat_response = get_chat_response(user_message)
    

# Funtions
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
    #print(parsed_gpt_response)
    save_messages(user_message.text, parsed_gpt_response)
    
    
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
            {"role": "system", "content": "You are an old pirate and you need to ask 3 pirate related questions from the user in this meeting. The user is called Ben." 
             "Welcome him and tell him what his job is going to be in this journey. Keep questions short and be funny sometimes."}
        )
    return messages


def save_messages(user_message, gpt_response):
    file = "database.json"
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": gpt_response.role, "content": gpt_response.content})
    with open(file, 'w') as f:
        json.dump(messages, f)
        