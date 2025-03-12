from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

""" Structured outputs """
# Structures for get_user_info function
class Key(BaseModel):
    key: str

class KeysList(BaseModel):
    keys: list[Key]


# Structures for ask_chat function
class Answer(BaseModel):
    isAnswered: bool
    reasoning: str
    answer: str

# Structures for save_user_info
class SaveUserInfo(BaseModel):
    key_name: str
    create_new_key: bool

class UpdateInformation(BaseModel):
    values: list[str]


""" Function calling """
tools = [{
    "type": "function",
    "function": {
        "name": "get_user_info",
        "description": "Retrieve and return any stored information about the user. This function should be called whenever the query requires details about the user, even if the request is indirect or implicit. For example, if the user asks for opinions on their hobbies, preferences, or personal traits, this function should be invoked to fetch the relevant data.",
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
}, {
    "type": "function",
    "function": {
        "name": "save_user_info",
        "description": "Save user information. You are user's personal assistant and this function should be called whenever the user's message contains data worth storing, such as personal details, location, hobby, goals, work, user's name or age etc",
        "parameters": {
            "type": "object",
            "properties": {
                "information": {
                    "type": "string",
                    "description": "Information about the user like: User's name is John"
                }
            },
            "required": [
                "information"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
}]


""" Tool call functions """
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


def add_user_info(information, key_name):
    add_info_prompt = """
You are an intelligent system that analyzes JSON structures containing information about the user. You will be given a key and a piece of information, and your goal is to extract the relevant value(s) from the information and attach them to the key. The output must be a list of strings (even if there is only one value).
Return only the value(s) as a list of strings without any additional text.

Examples:
USER:
key: passions
information: User's passions are skating and drawing.

AI: ['skating', 'drawing']

USER:
key: location
information: User lives in Warsaw

AI: ['Warsaw']
"""

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": add_info_prompt},
            {"role": "user", "content": f"Key: {key_name} \nInformation: {information}"}
        ],
        response_format=UpdateInformation
    )

    parsed_result = completion.choices[0].message.parsed  

    # Wczytanie danych z pliku JSON
    with open('user_info.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Dodanie nowego członu (klucz-wartość)
    data[key_name] = parsed_result.values[0] if len(parsed_result.values) == 1 else parsed_result.values

    # Zapisanie zmodyfikowanych danych z powrotem do pliku JSON
    with open('user_info.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def update_user_info(information, key_name):
    update_info_prompt = """
You are an intelligent system that analyzes JSON structures containing information about the user. You will be given a key, the current value associated with that key (which may be a single string or a list of strings), and a new piece of information. Your goal is to intelligently update the value based on the new information.

For fields that should only contain a single value (e.g., name, current location), if the new information contradicts the old one, you must replace the old value with the new one. For fields that can contain multiple values (e.g., passions, interests), merge the old and new values into a combined list, ensuring both pieces of information are preserved and removing duplicates if present. Always return the updated value as a list of strings (even if it contains only one element).

Return only the updated value as a list of strings, with no additional text.

Examples:
USER:
key: passions
old value: 'programming'
information: User's passions include skating and drawing.
AI: ['programming', 'skating', 'drawing']

USER:
key: name
old value: 'Krystian'
information: User's name is Bartek.
AI: ['Bartek']
"""
    
    # Wczytanie danych z pliku JSON
    with open('user_info.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": update_info_prompt},
            {"role": "user", "content": f"Key: {key_name} \nold value: {data[key_name]}\nInformation: {information}"}
        ],
        response_format=UpdateInformation
    )

    parsed_result = completion.choices[0].message.parsed
    data[key_name] = parsed_result.values[0] if len(parsed_result.values) == 1 else parsed_result.values

    # Zapisanie zmodyfikowanych danych z powrotem do pliku JSON
    with open('user_info.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def save_user_info(information):
    with open("user_info.json", "r") as memory:
        memory_text = memory.read()
        memory_json = json.loads(memory_text)
        keys = list(memory_json.keys())

    system_prompt = """
You are an intelligent system that analyzes JSON structures containing information about the user. You will be given a list of keys in the JSON structure and a piece of information that must be stored within it. Your goal is to determine whether the information belongs under an existing key or if a new key should be created. In making your decision, consider all relevant contextual cues (such as temporal aspects, current vs. historical status, or other semantic details) to ensure the data is accurately categorized. Return whether a new key must be created, along with the name of the key (either an existing key or the new one).
"""   

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Information: {information} \nKeys list: {keys}"}
        ],
        response_format=SaveUserInfo
    )

    parsed_result = completion.choices[0].message.parsed
    key_name = parsed_result.key_name
    create_new_key_flag = parsed_result.create_new_key

    if create_new_key_flag:
        add_user_info(information, key_name)
    else:
        update_user_info(information, key_name)

    return "User information updated."

""" Functions """
def call_function(name, args):
    if name == "get_user_info":
        return get_user_info(**args)
    if name == "save_user_info":
        return save_user_info(**args)

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

    # Executing tool_calls
    while flag:
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"### Executing function: {name}, with args: {args} ###")
            result = call_function(name, args)
            print(f"Result: {result}")
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
    user_msg = input("User: ")

    if user_msg == "quit":
        break

    # Chat's answer
    print(f"AI: {ask_chat(user_msg)}")

    # Emergency break
    if iters >=15:
        print("Chat ended. Limit of answers is 15")
        break
