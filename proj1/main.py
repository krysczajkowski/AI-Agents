from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

""" Structured outputs """
# Outputs for get_user_info function
class Key(BaseModel):
    key: str

class KeysList(BaseModel):
    keys: list[Key]


# Outputs for ask_chat function
class Answer(BaseModel):
    isAnswered: bool
    reasoning: str
    answer: str


""" Function calling """
tools = [{
    "type": "function",
    "function": {
        "name": "get_user_info",
        "description": "Get any information about the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question about the user eg. user's name or user's favourite music"
                }
            },
            "required": [
                "question"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]


""" Functions supporting AI """
def get_user_info(question):
    # Get all the keys from user_info.json
    with open("user_info.json", "r") as memory:
        memory_text = memory.read()
        memory_json = json.loads(memory_text)
        keys = list(memory_json.keys())

    system_prompt = """
You are an intelligent system that analyzes the JSON structure. Your task is to select from the given list of keys the ones that are most likely to contain the answer to the given question.

Rules of operation:
You are given a question and a list of keys available in the JSON structure.
You should return a list of those keys that are most likely to contain the answer to the question.
If none of the keys match, return an empty key.
Do not provide any additional content beyond the key name.
"""

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question} \nKeys list: {keys}"}
        ],
        response_format=KeysList
    )

    result = ""
    for el in completion.choices[0].message.parsed.keys:
        result += f"{el.key}: {memory_json[el.key]}\n"

    return result

def call_function(name, args):
    if name == "get_user_info":
        return get_user_info(**args)

def ask_chat(user_msg):
    system_prompt = "Your goal is to shortly answer to users message."
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

    # Add the tool_calls to context
    assistant_message = completion.choices[0].message
    messages.append(assistant_message)

    if completion.choices[0].message.tool_calls is not None:
        flag = True
    else:
        flag = False    

    while flag:
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            result = call_function(name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        if completion.choices[0].message.tool_calls is None:
            break

    return completion.choices[0].message.content


print("Type your message to chat-gpt:")
iters = 0
while True:
    iters += 1
    user_msg = input()

    if user_msg == "quit":
        break

    # Talk with chat-gpt
    print(ask_chat(user_msg))

    # Emergency break
    if iters >=15:
        break

