import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import traceback

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"Key: {GOOGLE_API_KEY}")

client = genai.Client(api_key=GOOGLE_API_KEY)

try:
    print("Listing models...")
    for model in client.models.list(config={'page_size': 100}):
        print(model.name)
except Exception as e:
    traceback.print_exc()
    print(f"Error: {e}")
