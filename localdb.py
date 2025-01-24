import os
import json


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