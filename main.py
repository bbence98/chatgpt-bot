from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from botocore.exceptions import ClientError

import os
import openai
import json
import requests
import json
import os
import boto3
import time

load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

app = FastAPI()

TABLE_NAME = "chat3"

dynamodb_resource = boto3.resource("dynamodb")
dynamodb_client = boto3.client("dynamodb")
table = dynamodb_resource.Table(TABLE_NAME)

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
    #messages = load_messages() # loads data from local json file
    messages = load_messages_dynamodb() # loads data from aws dynamodb table 
    messages.append({"role": "user", "content": user_message.text})
    
    gpt_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
        )
    
    parsed_gpt_response = gpt_response.choices[0].message
    #save_messages(user_message.text, parsed_gpt_response) # saves messages to local json file
    save_messages_dynamodb(user_message.text, parsed_gpt_response) # saves messages to aws dynamodb table
    return parsed_gpt_response

def count_dynamodb_items():
    res = table.scan(**{"TableName":TABLE_NAME})
    return res["Count"]

def create_dynamodb_table():
    response = dynamodb_client.create_table(
                TableName=TABLE_NAME,
                AttributeDefinitions=[
                    {
                        'AttributeName': 'ID',
                        'AttributeType': 'S'
                    },
                ],
                KeySchema=[
                    {
                        'AttributeName': 'ID',
                        'KeyType': 'HASH'
                    },
                ],
                BillingMode='PROVISIONED',
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                },
            )
    while True:
        response = table.meta.client.describe_table(TableName=TABLE_NAME)
        print(response['Table']['TableStatus'])
        time.sleep(2)
        if response['Table']['TableStatus'] == 'ACTIVE':
            break


def load_messages_dynamodb():
    try:
        table.load()
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            create_dynamodb_table()
            
    messages = []
    count = count_dynamodb_items()
    print("count: ", count)
    empty = count == 0
    #print("empty: ", empty)
    
    if not empty:
        for i in range(count):
            items = dynamodb_resource.batch_get_item(
                RequestItems={
                    TABLE_NAME: {
                        "Keys": [
                            {
                                "ID": f"{i+1}"
                            }
                        ]
                    }
                }
            )
            messages.append(items["Responses"][TABLE_NAME][0])
    else:
        table.put_item(
            Item={
                "ID": "1",
                "role": "system",
                "content": "You are a rude assistant, who helps with fake data to the people."
            }
        )
        
        items = dynamodb_resource.batch_get_item(
            RequestItems={
                TABLE_NAME: {
                    "Keys": [
                        {
                            "ID": "1"
                        }
                    ]
                }
            }
        )
        messages.append(items["Responses"][TABLE_NAME][0])
    return messages


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


def save_messages_dynamodb(user_message, gpt_response):
    count = count_dynamodb_items()
    
    count += 1
    table.put_item(
            Item={
                "ID": f"{count}",
                "role": "user",
                "content": user_message
            }
        )
    
    count += 1
    table.put_item(
            Item={
                "ID": f"{count}",
                "role": gpt_response.role,
                "content": gpt_response.content
            }
        )
    

def save_messages(user_message, gpt_response):
    file = "database.json"
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": gpt_response.role, "content": gpt_response.content})
    with open(file, 'w') as f:
        json.dump(messages, f)


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
