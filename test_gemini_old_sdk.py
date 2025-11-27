import os
from dotenv import load_dotenv
import google.generativeai as genai
import traceback

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"Key: {GOOGLE_API_KEY}")

genai.configure(api_key=GOOGLE_API_KEY)

try:
    print("Listing models with google-generativeai...")
    for m in genai.list_models():
        if 'flash' in m.name:
            print(m.name)
            
    # print("\nAttempting generation with gemini-2.5-pro-preview-tts...")
    # model = genai.GenerativeModel('gemini-2.5-pro-preview-tts')
    # response = model.generate_content("Hello, are you working?")
    # print(f"Response: {response.text}")
except Exception as e:
    traceback.print_exc()
    print(f"Error: {e}")
