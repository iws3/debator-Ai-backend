import requests
import urllib.parse

def generate_text(prompt):
    # Pollinations text API: https://text.pollinations.ai/{prompt}
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    print(f"Generating text for prompt: '{prompt}'")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print("Success!")
            print("Response:", response.text)
            return response.text
        else:
            print(f"Failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    generate_text("Write a short poem about coding in Nigerian Pidgin.")
