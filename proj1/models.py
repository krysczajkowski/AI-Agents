""" Structured outputs for LLM """

from pydantic import BaseModel

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