""" Functions for tool calling """
import json
from models import KeysList, SaveUserInfo, UpdateInformation
from datetime import datetime

def get_user_info(client, question):
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

# Add information about the user to the .json db
def add_user_info(client, information, key_name):
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

    # Load json database
    with open('user_info.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Add new data
    data[key_name] = parsed_result.values[0] if len(parsed_result.values) == 1 else parsed_result.values

    # Save modified data to json file
    with open('user_info.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Update information about the user in the .json db
def update_user_info(client, information, key_name):
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
    
    # Load data from json file
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

    # Update the data
    data[key_name] = parsed_result.values[0] if len(parsed_result.values) == 1 else parsed_result.values

    # Save modified data
    with open('user_info.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Save informations about the user - decide if update or add new data
def save_user_info(client, information):
    # Get a list of keys from a json db
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
        add_user_info(client, information, key_name)
    else:
        update_user_info(client, information, key_name)

    return "User information updated."

def check_current_time():
    # Get the current date and time
    now = datetime.now()

    # Format the date as day-month-year
    date_str = now.strftime("%d-%m-%Y")

    # Get the exact time
    time_str = now.strftime("%H:%M:%S")

    # Get the day of the week
    day_of_week = now.strftime("%A")

    result = f"""
    Current date: {date_str} (day-month-year)
    Current time: {time_str}
    Day of the week: {day_of_week}"""
    return result