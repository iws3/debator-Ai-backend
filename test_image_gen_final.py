import requests
import time

def test_image_generation():
    print("Testing Pollinations.ai Image Generation...")
    
    prompt = "A futuristic Nigerian city with flying cars, cyberpunk style, 8k"
    encoded_prompt = requests.utils.quote(prompt)
    seed = 12345
    
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&seed={seed}&nologo=true"
    
    print(f"Generated URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"Success! Image downloaded in {end_time - start_time:.2f} seconds.")
            print(f"Content Type: {response.headers.get('Content-Type')}")
            print(f"Image Size: {len(response.content)} bytes")
            
            # Save it to check
            with open("test_image.jpg", "wb") as f:
                f.write(response.content)
            print("Saved to test_image.jpg")
            return True
        else:
            print(f"Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_image_generation()
