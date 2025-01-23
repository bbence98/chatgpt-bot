from dotenv import load_dotenv
from botocore.exceptions import ClientError

import os
import time
import boto3

load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

TABLE_NAME = "chat"

dynamodb_resource = boto3.resource("dynamodb")
dynamodb_client = boto3.client("dynamodb")
table = dynamodb_resource.Table(TABLE_NAME)


def count_items():
    res = table.scan(**{"TableName":TABLE_NAME})
    return res["Count"]


def create_table():
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


def load_messages():
    try:
        table.load()
    except ClientError as err:
        if err.response["Error"]["Code"] == "ResourceNotFoundException":
            create_table()
            
    messages = []
    count = count_items()
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


def save_messages(user_message, gpt_response):
    count = count_items()
    
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
    