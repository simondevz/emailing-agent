import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def get_dotenv_value(val: str):
    return os.getenv(val)


# LLM Initialization
llm_instance = None


def get_llm():
    global llm_instance
    if llm_instance is None:
        llm_instance = ChatGroq(model="openai/gpt-oss-20b", temperature=2, api_key=get_dotenv_value("GROQ_API_KEY"))
    return llm_instance