from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import logging
from tools import get_user_info, save_user_info, check_current_time

load_dotenv()

# Logger config
logging.basicConfig(
    filename='agent.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

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
}, {
    "type": "function",
    "function": {
        "name": "check_current_time",
        "description": "Get current date, time and day of the week.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    }
}]


""" Functions """
def call_function(name, args):
    if name == "get_user_info":
        return get_user_info(client, **args)
    if name == "save_user_info":
        return save_user_info(client, **args)
    if name == "check_current_time":
        return check_current_time()

def ask_chat(global_chat_history, user_msg):
    local_chat_history = []

    global_chat_history.append({"role": "user", "content": user_msg})
    local_chat_history.append({"role": "user", "content": user_msg})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=global_chat_history,
        tools=tools
    )

    # Add the tool_calls to context
    assistant_message = completion.choices[0].message
    local_chat_history.append(assistant_message)
    logging.info(f"0) local_chat_history={local_chat_history}")

    if completion.choices[0].message.tool_calls is not None:
        flag = True
    else:
        flag = False    

    # Executing tool_calls
    while flag:
        for tool_call in completion.choices[0].message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            logging.info(f"### Executing function: {name}, with args: {args} ###")

            result = call_function(name, args)

            local_chat_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

            logging.info(f"1) local_chat_history={local_chat_history}")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=local_chat_history,
            tools=tools
        )

        # Add next step to the llm context
        assistant_message = completion.choices[0].message
        local_chat_history.append(assistant_message)
        logging.info(f"2) local_chat_history={local_chat_history}")

        if completion.choices[0].message.tool_calls is None:
            break

    global_chat_history.append({"role": "assistant", "content": completion.choices[0].message.content})
    logging.info(f"global_chat_history={global_chat_history}")
    return completion.choices[0].message.content


print("Type your message to chat-gpt:")
iters = 0

system_prompt = "Your goal is to shortly answer to users message."
chat_history = [{"role": "system", "content": system_prompt}]

logging.info(f"==== Different Conversation ====")
while True:
    logging.info(f"---- Different Question ----")
    iters += 1
    user_msg = input("User: ")

    if user_msg == "quit":
        break

    # Chat's answer
    print(f"AI: {ask_chat(chat_history, user_msg)}")

    # Emergency break
    if iters >=15:
        print("Chat ended. Limit of answers is 15")
        break
