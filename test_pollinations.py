import requests
import time

def generate_image(prompt):
    # Pollinations.ai is a free, no-key API for image generation
    # URL format: https://image.pollinations.ai/prompt/{prompt}
    
    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    print(f"Generating image for prompt: '{prompt}'")
    print(f"URL: {url}")
    
    try:
        # We can just return the URL directly as it serves the image
        # But let's check if it's reachable
        response = requests.get(url)
        if response.status_code == 200:
            print("Success! Image generated.")
            return url
        else:
            print(f"Failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Test with a prompt
    image_url = generate_image("A realistic portrait of a Nigerian debate champion, professional photography, 8k")
    if image_url:
        print(f"Image URL: {image_url}")
