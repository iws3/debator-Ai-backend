import os
import time
import uuid
import uvicorn
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
import traceback
import base64

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for audio files
os.makedirs("static", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 50)
    print("🚀 Debator Backend Starting...")
    print("=" * 50)

# Configuration
YARNGPT_API_KEY = os.getenv("YARNGPT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not YARNGPT_API_KEY:
    print("⚠️  Warning: YARNGPT_API_KEY not found in environment variables.")
if not GOOGLE_API_KEY:
    print("⚠️  Warning: GOOGLE_API_KEY not found in environment variables.")

# Initialize Gemini Client
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✅ Gemini Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Gemini Client: {e}")
    client = None

# In-memory storage for debates
debates = {}

# Pydantic Models
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

# Helper Functions
def generate_pidgin_text(prompt: str) -> str:
    """Generate text using Gemini"""
    if not client:
        print("❌ Client not initialized")
        return "Abeg, system no dey work. I no fit talk now."
    
    log_file = "debug_log.txt"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Generating text\n")
            f.write(f"Model: gemini-2.0-flash-exp\n")
            f.write(f"Prompt: {prompt[:100]}...\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")
    
    try:
        print(f"🎨 Generating text with prompt: {prompt[:80]}...")
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=200,
            )
        )
        
        # Check if response has text
        if hasattr(response, 'text') and response.text:
            result_text = response.text.strip()
            print(f"✅ Got response: {result_text[:100]}")
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to extract text from candidates
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts_text = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        parts_text.append(part.text)
                result_text = ' '.join(parts_text).strip() if parts_text else ""
                print(f"✅ Extracted from candidates: {result_text[:100]}")
            else:
                result_text = ""
        else:
            result_text = ""
        
        # Fallback if empty
        if not result_text:
            print("⚠️  Empty response, using fallback")
            result_text = "Oya na, make we see wetin you fit do! I ready for this debate o!"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"✅ Response received: {len(result_text)} chars\n")
                f.write(f"Response: {result_text}\n")
        except:
            pass
            
        return result_text
        
    except Exception as e:
        error_msg = f"Error generating text: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"❌ EXCEPTION: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass
            
        return "Abeg, e be like say network no good. Make we try again o!"

def generate_image_base64(prompt: str) -> Optional[str]:
    """Generate image using Gemini and return base64 string"""
    if not client:
        print("❌ Gemini client not initialized")
        return None
        
    try:
        print(f"🎨 Generating image: {prompt[:50]}...")
        
        # Use gemini-2.0-flash-exp with IMAGE modality
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )
        
        # Extract image data from response
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data is not None:
                            # Return base64 encoded image
                            base64_image = base64.b64encode(part.inline_data.data).decode('utf-8')
                            mime_type = part.inline_data.mime_type or "image/png"
                            print(f"✅ Image generated successfully ({len(base64_image)} bytes)")
                            return f"data:{mime_type};base64,{base64_image}"
        
        # Also check response.parts directly
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    base64_image = base64.b64encode(part.inline_data.data).decode('utf-8')
                    mime_type = part.inline_data.mime_type or "image/png"
                    print(f"✅ Image generated successfully ({len(base64_image)} bytes)")
                    return f"data:{mime_type};base64,{base64_image}"
        
        print("⚠️  No image data in response")
        print(f"Response structure: {dir(response)}")
        return None
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        print(f"Full error: {traceback.format_exc()}")
        return None

def generate_audio(text: str, voice: str = "Osagie") -> str:
    """Generate audio using YarnGPT TTS API"""
    if not YARNGPT_API_KEY:
        print("⚠️  YarnGPT API key not available, skipping audio generation")
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
        print(f"🔊 Generating audio: {text[:30]}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            filename = f"audio_{uuid.uuid4()}.mp3"
            filepath = os.path.join("static", filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Audio generated: {filename}")
            return f"/static/{filename}"
        else:
            print(f"❌ YarnGPT Error: {response.status_code} - {response.text[:200]}")
            return ""
            
    except requests.exceptions.Timeout:
        print("⏱️  Audio generation timed out")
        return ""
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return ""

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "🎭 Debator Backend is running!",
        "status": "healthy",
        "gemini_client": "initialized" if client else "not initialized",
        "yarngpt_api": "configured" if YARNGPT_API_KEY else "not configured"
    }

@app.post("/generate-image")
async def generate_image_endpoint(request: ImageGenerationRequest):
    """Generate character portrait using Gemini"""
    try:
        print(f"\n{'='*50}")
        print(f"📸 Image generation request for: {request.character_name}")
        print(f"{'='*50}")
        
        prompt = (
            f"Create a professional portrait photo of {request.character_name}, "
            f"photorealistic, high quality, studio lighting, neutral background, "
            f"facing camera, serious expression, head and shoulders shot"
        )
        
        image_data = generate_image_base64(prompt)
        
        if image_data:
            print(f"✅ Image generated successfully for {request.character_name}")
            return {"imageUrl": image_data}
        else:
            print(f"❌ Failed to generate image for {request.character_name}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate image. The frontend will use avatar fallback."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in image generation endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_debate", response_model=DebateResponse)
async def start_debate(request: DebateStartRequest):
    """Start a new debate"""
    try:
        print(f"\n{'='*50}")
        print(f"🥊 Starting debate: {request.char1} vs {request.char2}")
        print(f"User playing as: {request.user_side}")
        print(f"{'='*50}")
        
        debate_id = str(uuid.uuid4())
        
        # Determine AI character
        ai_character = (
            request.char2 
            if request.user_side.lower() == request.char1.lower() 
            else request.char1
        )
        user_character = request.user_side
        
        print(f"🤖 AI will play as: {ai_character}")
        print(f"👤 User will play as: {user_character}")
        
        # Initial Prompt for debate
        system_prompt = f"""You are {ai_character} in a debate against {user_character}.
The topic is: Who is better between {ai_character} and {user_character}?
Speak in Nigerian Pidgin English.
Be funny, witty, and aggressive but playful.
Keep it short (max 2 sentences).
Start the debate now by making your opening statement."""
        
        print(f"📝 Generating opening statement...")
        ai_text = generate_pidgin_text(system_prompt)
        
        print(f"🔊 Generating audio...")
        ai_audio = generate_audio(ai_text, voice="Osagie")
        
        # Store debate
        debates[debate_id] = {
            "char1": request.char1,
            "char2": request.char2,
            "user_side": user_character,
            "ai_side": ai_character,
            "start_time": time.time(),
            "history": [f"{ai_character}: {ai_text}"],
            "turn_count": 0
        }
        
        print(f"✅ Debate started: {debate_id}")
        print(f"💬 AI opening: {ai_text}")
        
        return DebateResponse(
            debate_id=debate_id,
            ai_text=ai_text,
            ai_audio_url=ai_audio,
            is_finished=False
        )
        
    except Exception as e:
        print(f"❌ Error starting debate: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start debate: {str(e)}")

@app.post("/turn", response_model=DebateResponse)
async def turn(request: DebateTurnRequest):
    """Process a debate turn"""
    try:
        debate = debates.get(request.debate_id)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        print(f"\n{'='*50}")
        print(f"💬 Turn {debate['turn_count'] + 1} in debate {request.debate_id[:8]}...")
        print(f"👤 User ({debate['user_side']}): {request.user_text}")
        
        debate["history"].append(f"{debate['user_side']}: {request.user_text}")
        debate["turn_count"] += 1
        
        # Check for time limit (5 mins = 300 seconds)
        elapsed_time = time.time() - debate["start_time"]
        print(f"⏱️  Elapsed time: {elapsed_time:.1f}s / 300s")
        
        if elapsed_time > 300:
            print("🏁 Time limit reached! Judging winner...")
            
            judge_prompt = f"""Judge this debate between {debate['char1']} and {debate['char2']}.
Debate History:
{chr(10).join(debate['history'])}

Based on intelligence, wit, and points made, who won?
Reply with ONLY the winner's name, nothing else."""
            
            winner = generate_pidgin_text(judge_prompt).strip()
            final_message = f"Time don reach! The winner na {winner}! 🏆"
            
            print(f"🏆 Winner: {winner}")
            
            return DebateResponse(
                debate_id=request.debate_id,
                ai_text=final_message,
                ai_audio_url=None,
                is_finished=True,
                winner=winner
            )

        # Generate AI Response
        prompt = f"""You are {debate['ai_side']} debating against {debate['user_side']}.

Recent conversation:
{chr(10).join(debate['history'][-5:])}

The user ({debate['user_side']}) just said: "{request.user_text}"

Respond in Nigerian Pidgin English. Be sharp, funny, and defend yourself.
Maximum 2 sentences. Make it witty and entertaining!"""
        
        print(f"🤖 Generating AI response...")
        ai_text = generate_pidgin_text(prompt)
        debate["history"].append(f"{debate['ai_side']}: {ai_text}")
        
        print(f"💬 AI ({debate['ai_side']}): {ai_text}")
        
        print(f"🔊 Generating audio...")
        ai_audio = generate_audio(ai_text, voice="Osagie")
        
        return DebateResponse(
            debate_id=request.debate_id,
            ai_text=ai_text,
            ai_audio_url=ai_audio,
            is_finished=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing turn: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process turn: {str(e)}")

# Mount static files AFTER all routes
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎭 Starting Debator Backend Server")
    print("="*50 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )