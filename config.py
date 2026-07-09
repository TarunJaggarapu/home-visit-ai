"""
Central configuration. Change the model or provider in ONE place here.

By default this uses OpenAI. To switch providers later:
  - Gemini:  set base_url + key (OpenAI-compatible endpoint), or use langchain-google-genai
  - Ollama (free, local): OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
LangChain is not required for this project; the plain SDK is used for clarity.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file if present

# Cheap + supports structured outputs. Bump to a bigger model any time.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# Reads OPENAI_API_KEY from the environment automatically.
client = OpenAI()
