import os
import re
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from dotenv import load_dotenv
from typing import Optional, List, Literal
from pydantic import BaseModel
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class ChatTurn(BaseModel):
    role: Literal["user", "agent"]
    content: str

class TaskRequest(BaseModel):
    goal: str                      # latest user message
    history: Optional[List[ChatTurn]] = None  # previous turns

# --- Slot Extraction Logic ---

LEVEL_OPTIONS = ["beginner", "intermediate", "advanced"]
TIME_OPTIONS = ["weekend", "1-2 weeks", "1 – 2 weeks", "1 to 2 weeks", "3+ weeks", "3 plus weeks"]
GOAL_OPTIONS = ["learning", "portfolio", "hackathon"]

def extract_option(text: str, options: List[str]) -> Optional[str]:
    text_l = text.lower()
    for opt in options:
        if opt in text_l:
            return opt
    return None

def extract_slots(history: List[ChatTurn]) -> dict:
    # Combine all *user* messages
    combined = " ".join(m.content for m in history if m.role == "user").lower()

    level = extract_option(combined, LEVEL_OPTIONS)
    time = extract_option(combined, TIME_OPTIONS)
    goal_type = extract_option(combined, GOAL_OPTIONS)

    return {
        "level": level,
        "time": time,
        "goal_type": goal_type,
    }

# --- System Prompts ---

PROJECTSCOUT_CLARIFY_SYSTEM = """
You are ProjectScout, an AI mentor.

You are talking to a developer who wants project ideas.
We are filling three fields:

- experience_level: beginner / intermediate / advanced
- time_budget: weekend / 1-2 weeks / 3+ weeks
- goal_type: learning / portfolio / hackathon

You are ONLY responsible for asking for the fields that are still missing.
If some fields are already known from the conversation, DO NOT ask for them again.
Ask in ONE short friendly message.
"""

PROJECTSCOUT_PLAN_SYSTEM = """
You are ProjectScout, an AI mentor.

You already know the user's:
- experience_level
- time_budget
- goal_type

They told you what they want to learn/build.
Now propose 3–5 specific project ideas and a short step-by-step plan for one of them.
Be concrete and concise.
"""

# --- Endpoint ---

@app.post("/run-agent")
async def run_agent(request: TaskRequest):
    try:
        # Log incoming request
        print(f"\n{'='*80}")
        print(f"Incoming request:")
        print(f"  Goal: {request.goal}")
        print(f"  History length: {len(request.history) if request.history else 0}")

        # Build full history including the latest user message
        # Map 'agent' role from frontend to 'assistant' for OpenAI if needed, 
        # but here we keep 'agent' in ChatTurn and map it later.
        history = (request.history or []) + [
            ChatTurn(role="user", content=request.goal)
        ]

        slots = extract_slots(history)
        print(f"  Extracted slots: {slots}")
        
        missing = [k for k, v in slots.items() if v is None]
        print(f"  Missing slots: {missing}")

        # 1) Need more info → clarifying question
        if missing:
            messages = [{"role": "system", "content": PROJECTSCOUT_CLARIFY_SYSTEM}]

            # Give model the raw conversation so far for context
            for turn in history:
                role = "assistant" if turn.role == "agent" else "user"
                messages.append({"role": role, "content": turn.content})

            # Also tell it explicitly what is still missing
            messages.append({
                "role": "system",
                "content": f"Fields still missing: {', '.join(missing)}. Ask ONLY about these."
            })

            completion = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
            )
            reply = completion.choices[0].message.content
            
            print(f"  Clarification reply: {reply[:100]}...")

            # Return format expected by frontend
            return {
                "status": "completed", # "completed" just means the turn is done
                "message": reply,
                "data": slots, # useful for debugging
                "finished": False, # Conversation not finished yet
                "type": "clarification"
            }

        # 2) All slots filled → suggest projects
        messages = [{"role": "system", "content": PROJECTSCOUT_PLAN_SYSTEM}]

        # Give conversation for flavour
        for turn in history:
            role = "assistant" if turn.role == "agent" else "user"
            messages.append({"role": role, "content": turn.content})

        # Also provide a clean state summary
        summary = (
            f"User state:\n"
            f"- experience_level: {slots['level']}\n"
            f"- time_budget: {slots['time']}\n"
            f"- goal_type: {slots['goal_type']}\n"
            f"- latest_goal_message: {request.goal}"
        )
        messages.append({"role": "system", "content": summary})

        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
        )
        reply = completion.choices[0].message.content
        
        print(f"  Plan reply: {reply[:100]}...")

        return {
            "status": "completed",
            "message": reply,
            "data": slots,
            "finished": True, # We provided the plan
            "type": "results"
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in run_agent: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)