# env_check.py
from dotenv import load_dotenv
import os

load_dotenv()   # MUST be at the top

print("OPENAI:", bool(os.getenv("OPENAI_API_KEY")))  # debug check
