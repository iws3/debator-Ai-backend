from main import generate_pidgin_text
import sys

print("Testing generation...")
try:
    text = generate_pidgin_text("Hello")
    print(f"Result: {text}")
except Exception as e:
    print(f"Caught exception: {e}")
