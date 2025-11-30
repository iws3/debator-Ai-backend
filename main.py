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
        logger.error(f"Audio error: {e}")
        return None

def generate_gemini_response(prompt: str) -> str:
    if not client:
        return "AI unavailable"
    
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
        return "I'm speechless!"
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Error"

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
    
    prompt = f"""You are {request.ai_goat} debating {request.user_goat}.
Topic: Who is the greater GOAT?
Speak in Nigerian Pidgin English.
Be funny, witty, playful.
Short opening (max 2 sentences).
No quotes, asterisks, markdown."""
    
    ai_text = generate_gemini_response(prompt)
    audio_url = generate_audio(ai_text)
    
    debates[debate_id] = {
        "id": debate_id,
        "user_goat": request.user_goat,
        "ai_goat": request.ai_goat,
        "domain": request.domain,
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
    
    prompt = f"""You are {debate['ai_goat']} debating {debate['user_goat']}.
History: {[f"{m['speaker']}: {m['text']}" for m in debate['history'][-5:]]}
User said: "{request.user_text}"
Respond in Nigerian Pidgin.
Be funny, witty, roast them.
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
    encoded_name = request.goat_name.replace(" ", "%20")
    return {"imageUrl": f"https://api.dicebear.com/7.x/avataaars/svg?seed={encoded_name}"}

@app.post("/speech-to-text")
async def speech_to_text(request: SpeechToTextRequest):
    return {"success": False, "text": "", "message": "Voice captured. Please type for now."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)