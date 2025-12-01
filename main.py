import os
import uuid
import logging
import requests
import re
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found")
if not YARNGPT_API_KEY:
    logger.warning("YARNGPT_API_KEY not found")

try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {e}")
    client = None

debates = {}

class StartDebateRequest(BaseModel):
    user_goat: str
    ai_goat: str
    domain: str = "General"
    user_name: str = "Friend"  # Added user_name

class DebateTurnRequest(BaseModel):
    debate_id: str
    user_text: str

class GenerateImageRequest(BaseModel):
    goat_name: str
    domain: str = "General"

class SpeechToTextRequest(BaseModel):
    audio_base64: str

def clean_text(text: str) -> str:
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = text.strip('"\'')
    text = text.replace('`', '')
    return text.strip()

def generate_audio(text: str, voice: str = "Idera") -> Optional[str]:
    if not YARNGPT_API_KEY:
        return None
    
    try:
        clean_content = clean_text(text)
        url = "https://yarngpt.ai/api/v1/tts"
        headers = {
            "Authorization": f"Bearer {YARNGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"text": clean_content, "voice": voice}
        
        for attempt in range(2):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    audio_filename = f"audio_{uuid.uuid4().hex}.mp3"
                    audio_path = os.path.join("static", "audio", audio_filename)
                    
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    
                    return f"/static/audio/{audio_filename}"
                else:
                    if attempt < 1:
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < 1:
                    continue
                return None
            except Exception as e:
                if attempt < 1:
                    continue
                return None
                
    except Exception as e:
        logger.error(f"Audio error: {ege}")
        return None

def generate_pollinations_text(prompt: str) -> str:
    try:
        # Pollinations text API: https://text.pollinations.ai/{prompt}
        response = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=30)
        if response.status_code == 200:
            return clean_text(response.text)
        return "I dey try think but network no gree."
    except Exception as e:
        logger.error(f"Pollinations text error: {e}")
        return "Error generating speech."

def generate_gemini_response(prompt: str) -> str:
    if not client:
        logger.warning("Gemini client not available, using Pollinations fallback")
        return generate_pollinations_text(prompt)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=1000,
            )
        )
        if hasattr(response, 'text') and response.text:
            return clean_text(response.text)
        
        logger.warning("Gemini returned no text, using Pollinations fallback")
        return generate_pollinations_text(prompt)
    except Exception as e:
        logger.error(f"Gemini error: {e}, falling back to Pollinations")
        return generate_pollinations_text(prompt)

def calculate_debate_scores(user_text: str, ai_text: str) -> tuple:
    """Smart scoring based on argument quality"""
    if not client:
        return (10, 15)
    
    try:
        scoring_prompt = f"""Rate these debate arguments 0-20 points each:

User: "{user_text}"
AI: "{ai_text}"

Criteria:
- Logic & reasoning (0-7)
- Evidence & examples (0-7)
- Style & delivery (0-6)

Respond ONLY: user_score,ai_score
Example: 15,12"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=scoring_prompt,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=50)
        )
        
        if hasattr(response, 'text') and response.text:
            scores = response.text.strip().split(',')
            return (int(scores[0].strip()), int(scores[1].strip()))
    except:
        pass
    
    # Fallback
    return (min(20, len(user_text.split()) // 2), min(20, len(ai_text.split()) // 2))

@app.get("/")
async def root():
    return {"message": "Debator API running"}

@app.post("/start-goat-debate")
async def start_debate(request: StartDebateRequest):
    debate_id = str(uuid.uuid4())
    
    # Updated prompt: User vs AI debating about GOATs
    prompt = f"""You are debating with {request.user_name} about who is the greater GOAT between {request.user_goat} and {request.ai_goat}.
{request.user_name} supports {request.user_goat}, and you support {request.ai_goat}.
Greet {request.user_name} warmly and make your opening argument for why {request.ai_goat} is better than {request.user_goat}.
Speak in Nigerian Pidgin English.
Be funny, witty, and playful.
Keep it short (max 3 sentences).
No quotes, asterisks, or markdown."""
    
    ai_text = generate_gemini_response(prompt)
    audio_url = generate_audio(ai_text)
    
    debates[debate_id] = {
        "id": debate_id,
        "user_goat": request.user_goat,
        "ai_goat": request.ai_goat,
        "domain": request.domain,
        "user_name": request.user_name,
        "history": [{"speaker": "AI", "text": ai_text}],
        "user_score": 0,
        "ai_score": 0
    }
    
    return {
        "debate_id": debate_id,
        "ai_text": ai_text,
        "ai_audio_url": audio_url or "",
        "user_score": 0,
        "ai_score": 0
    }

@app.get("/debate/{debate_id}")
async def get_debate(debate_id: str):
    if debate_id not in debates:
        raise HTTPException(404, "Not found")
    
    debate = debates[debate_id]
    opening_text = debate["history"][0]["text"]
    audio_url = generate_audio(opening_text)
    
    return {
        "opening_message": opening_text,
        "opening_audio_url": audio_url or ""
    }

@app.post("/debate-turn")
async def debate_turn(request: DebateTurnRequest):
    if request.debate_id not in debates:
        raise HTTPException(404, "Not found")
    
    debate = debates[request.debate_id]
    debate["history"].append({"speaker": "User", "text": request.user_text})
    
    # Updated prompt: User vs AI debating about GOATs
    prompt = f"""You are debating with a user about who is the greater GOAT.
You support {debate['ai_goat']} and the user supports {debate['user_goat']}.
Recent conversation: {[f"{m['speaker']}: {m['text']}" for m in debate['history'][-5:]]}
User just said: "{request.user_text}"
Respond defending {debate['ai_goat']} and counter their argument for {debate['user_goat']}.
Speak in Nigerian Pidgin English.
Be funny, witty, and engaging.
Max 3 sentences. No quotes, asterisks, markdown."""
    
    ai_text = generate_gemini_response(prompt)
    debate["history"].append({"speaker": "AI", "text": ai_text})
    audio_url = generate_audio(ai_text)
    
    # Smart scoring
    user_pts, ai_pts = calculate_debate_scores(request.user_text, ai_text)
    debate["user_score"] += user_pts
    debate["ai_score"] += ai_pts
    
    return {
        "ai_text": ai_text,
        "ai_audio_url": audio_url or "",
        "user_score": debate["user_score"],
        "ai_score": debate["ai_score"],
        "is_finished": False,
        "winner": None
    }

@app.post("/generate-goat-image")
async def generate_goat_image(request: GenerateImageRequest):
    # Using Pollinations.ai (Free, No API Key required)
    prompt = f"epic portrait of {request.goat_name}, {request.domain} theme, hyperrealistic, dramatic lighting, highly detailed, 8k uhd"
    encoded_prompt = requests.utils.quote(prompt)
    seed = abs(hash(request.goat_name)) % 100000
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&seed={seed}&nologo=true"
    return {"imageUrl": image_url}

@app.post("/speech-to-text")
async def speech_to_text(request: SpeechToTextRequest):
    return {"success": False, "text": "", "message": "Voice captured. Please type for now."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)