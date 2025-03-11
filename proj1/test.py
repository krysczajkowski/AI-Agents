import json

with open("user_info.json", "r") as memory:
    memory_text = memory.read()
    memory_json = json.loads(memory_text)
    keys = list(memory_json.keys())

    for key, value in memory_json.items():
        keys.append(key)

    print(keys)