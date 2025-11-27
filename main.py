import os
import time
import uuid
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
import traceback

load_dotenv()

app = FastAPI()

from fastapi.staticfiles import StaticFiles

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for audio files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Debator Backend is running!"}

# In-memory storage for debates
debates = {}

# Configuration
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not YARNGPT_API_KEY:
    print("Warning: YARNGPT_API_KEY not found in environment variables.")
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")

# Initialize Gemini Client
client = genai.Client(api_key=GOOGLE_API_KEY)

class DebateStartRequest(BaseModel):
    char1: str
    char2: str
    user_side: str

class DebateTurnRequest(BaseModel):
    debate_id: str
    user_text: str

class DebateResponse(BaseModel):
    debate_id: str
    ai_text: str
    ai_audio_url: Optional[str] = None
    char1_image_url: Optional[str] = None
    char2_image_url: Optional[str] = None
    winner: Optional[str] = None
    is_finished: bool = False

class ImageGenerationRequest(BaseModel):
    character_name: str

def generate_pidgin_text(prompt: str) -> str:
    log_file = "debug_log.txt"
    
    with open(log_file, "a") as f:
        f.write(f"\n--- Generating text ---\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Key present: {bool(GOOGLE_API_KEY)}\n")
        f.write(f"Model: gemini-2.0-flash-exp\n")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
            )
        )
        with open(log_file, "a") as f:
            f.write(f"Response received: {len(response.text)} chars\n")
            
        return response.text
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"EXCEPTION: {e}\n")
            f.write(traceback.format_exc())
            
        return "Abeg, network no good. I no fit talk now."

def generate_image_base64(prompt: str) -> Optional[str]:
    """Generate image using Gemini and return base64 string"""
    try:
        print(f"Generating image for: {prompt[:50]}...")
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )
        
        # Extract image data from response
        for part in response.parts:
            if part.inline_data is not None:
                # Return base64 encoded image
                import base64
                base64_image = base64.b64encode(part.inline_data.data).decode('utf-8')
                return f"data:image/png;base64,{base64_image}"
        
        print("No image generated in response")
        return None
        
    except Exception as e:
        print(f"Error generating image: {e}")
        traceback.print_exc()
        return None

def generate_audio(text: str, voice: str = "Idera") -> str:
    """Generate audio using YarnGPT TTS API"""
    if not YARNGPT_API_KEY:
        print("YarnGPT API key not available")
        return ""
    
    url = "https://yarngpt.ai/api/v1/tts"
    headers = {
        "Authorization": f"Bearer {YARNGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice": voice,
        "response_format": "mp3"
    }
    
    try:
        print(f"Generating audio for: {text[:30]}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            filename = f"audio_{uuid.uuid4()}.mp3"
            filepath = os.path.join("static", filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"Audio generated: {filename}")
            return f"/static/{filename}"
        else:
            print(f"YarnGPT Error: {response.status_code} - {response.text}")
            return ""
            
    except Exception as e:
        print(f"Error generating audio: {e}")
        traceback.print_exc()
        return ""

@app.post("/generate-image")
async def generate_image_endpoint(request: ImageGenerationRequest):
    """Generate character portrait using Gemini"""
    try:
        prompt = f"Create a professional portrait photo of {request.character_name}, photorealistic, high quality, studio lighting, neutral background, facing camera, serious expression, head and shoulders shot"
        
        image_data = generate_image_base64(prompt)
        
        if image_data:
            return {"imageUrl": image_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate image")
            
    except Exception as e:
        print(f"Error in image generation endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_debate")
async def start_debate(request: DebateStartRequest):
    debate_id = str(uuid.uuid4())
    
    ai_character = request.char2 if request.user_side.lower() == request.char1.lower() else request.char1
    user_character = request.user_side
    
    # Initial Prompt for debate
    system_prompt = f"""
    You are {ai_character} in a debate against {user_character}.
    The topic is: Who is better?
    Speak in Nigerian Pidgin English.
    Be funny, witty, and aggressive but playful.
    Keep it short (max 2 sentences).
    Start the debate now.
    """
    
    ai_text = generate_pidgin_text(system_prompt)
    ai_audio = generate_audio(ai_text, voice="Osagie")
    
    debates[debate_id] = {
        "char1": request.char1,
        "char2": request.char2,
        "user_side": user_character,
        "ai_side": ai_character,
        "start_time": time.time(),
        "history": [f"{ai_character}: {ai_text}"],
        "turn_count": 0
    }
    
    return {
        "debate_id": debate_id,
        "ai_text": ai_text,
        "ai_audio_url": ai_audio
    }

@app.post("/turn")
async def turn(request: DebateTurnRequest):
    debate = debates.get(request.debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    debate["history"].append(f"{debate['user_side']}: {request.user_text}")
    debate["turn_count"] += 1
    
    # Check for time limit (5 mins)
    elapsed_time = time.time() - debate["start_time"]
    if elapsed_time > 300:
        judge_prompt = f"""
        Judge this debate between {debate['char1']} and {debate['char2']}.
        History:
        {chr(10).join(debate['history'])}
        
        Who won based on intelligence, wit, and points?
        Reply with just the winner's name.
        """
        winner = generate_pidgin_text(judge_prompt).strip()
        return {
            "debate_id": request.debate_id,
            "ai_text": f"Time don reach! The winner na {winner}!",
            "ai_audio_url": None,
            "is_finished": True,
            "winner": winner
        }

    # Generate AI Response
    prompt = f"""
    You are {debate['ai_side']} debating against {debate['user_side']}.
    Current conversation history:
    {chr(10).join(debate['history'])}
    
    User just said: "{request.user_text}"
    
    Reply in Nigerian Pidgin English.
    Be sharp, funny, and defend your side.
    Max 2 sentences.
    """
    
    ai_text = generate_pidgin_text(prompt)
    debate["history"].append(f"{debate['ai_side']}: {ai_text}")
    
    ai_audio = generate_audio(ai_text, voice="Osagie")
    
    return {
        "debate_id": request.debate_id,
        "ai_text": ai_text,
        "ai_audio_url": ai_audio,
        "is_finished": False
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)