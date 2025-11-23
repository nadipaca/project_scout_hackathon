import os
import re
from typing import Optional, List, Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

class ChatTurn(BaseModel):
    role: Literal["user", "agent"]
    content: str


class TaskRequest(BaseModel):
    goal: str                      # latest user message
    history: Optional[List[ChatTurn]] = None  # previous turns


# -------------------------------------------------------------------
# Slot Extraction Logic (core fields)
# -------------------------------------------------------------------

LEVEL_OPTIONS = ["beginner", "intermediate", "advanced"]
TIME_OPTIONS = ["weekend", "1-2 weeks", "1 – 2 weeks", "1 to 2 weeks", "3+ weeks", "3 plus weeks"]
GOAL_OPTIONS = ["learning", "portfolio", "hackathon", "job", "interview"]  # a few synonyms


def extract_option(text: str, options: List[str]) -> Optional[str]:
    text_l = text.lower()
    for opt in options:
        if opt in text_l:
            # map some synonyms back to canonical values
            if opt in ["job", "interview"]:
                return "portfolio"
            return opt
    return None


def extract_slots(history: List[ChatTurn]) -> dict:
    """
    Combine all user messages and try to infer:
    - experience level
    - time budget
    - goal type (learning / portfolio / hackathon)
    """
    combined = " ".join(m.content for m in history if m.role == "user").lower()

    level = extract_option(combined, LEVEL_OPTIONS)
    time = extract_option(combined, TIME_OPTIONS)
    goal_type = extract_option(combined, GOAL_OPTIONS)

    return {
        "level": level,
        "time": time,
        "goal_type": goal_type,
    }


# -------------------------------------------------------------------
# Response Normalization
# -------------------------------------------------------------------

def normalize_reply(text: str) -> str:
    """
    Make the model output more human-readable and less 'template-y':
    - strip headings like '### 1. ...'
    - drop lines with noisy labels like 'Full-Stack Template', 'Production Potential'
    - collapse extra blank lines
    """
    text = text.strip()
    cleaned_lines: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Strip markdown headings (#, ##, ### ...)
        line = re.sub(r"^#{1,6}\s*", "", line)

        # Remove overly verbose template labels
        noisy_phrases = [
            "Full-Stack Template",
            "Production Potential",
            "Tutorial**",
            "Template**",
        ]
        if any(phrase in line for phrase in noisy_phrases):
            continue

        cleaned_lines.append(line)

    # Rejoin and collapse 3+ blank lines into just 2
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# -------------------------------------------------------------------
# System Prompts
# -------------------------------------------------------------------

# This prompt is for follow-up questions
PROJECTSCOUT_CLARIFY_SYSTEM = """
You are ProjectScout, a friendly AI mentor helping a developer pick good projects.

You are trying to fully understand what they want so you can suggest *specific* project ideas.

Core fields you must know:
- experience_level: beginner / intermediate / advanced
- time_budget: weekend / 1–2 weeks / 3+ weeks
- goal_type: learning / portfolio / hackathon

Additional understanding that helps you:
- domain / topic (e.g., AI, web apps, data engineering, agents)
- tech stack preference (e.g., Python only, Python + React, Lovable + Supabase, etc.)
- project type: completed GitHub repos vs tutorials vs just ideas/challenges
- any constraints (e.g., only browser-based, wants to use OpenAI, wants multi-agent, etc.)

Behavior rules:
- First, read the entire conversation and infer as much as possible.
- Then ask about the fields that are still missing or genuinely unclear.
- You may ask 2–3 short questions in ONE message if needed, but keep it natural and not overwhelming.
- NEVER re-ask about a field that is already clearly answered in the chat history.
- Write like a human in chat: no headings, no bullet lists, just 2–4 sentences.
"""

# This prompt is for final project suggestions
PROJECTSCOUT_PLAN_SYSTEM = """
You are ProjectScout, a friendly AI mentor.

You already know:
- the user's experience level
- their time budget
- their goal (learning / portfolio / hackathon)
- plus any domain/stack preferences you've gathered from the conversation.

Respond in clear, concise, human-readable Markdown:
- Start with one short, encouraging summary sentence.
- Then give exactly 3 project ideas as a numbered list: 1., 2., 3.
- For EACH project, use exactly 3 short lines:
  1) "**Title** — one-sentence description."
  2) "Stack: ..."
  3) "Rough time: ..."

Rules:
- Do NOT use headings like #, ##, ###.
- Do NOT include long templates or many sub-bullets.
- Tailor the ideas to the user's level, time, goal, and stack/domain preferences.
- Keep the whole answer under about 250–300 words.
- Tone: practical, encouraging, and easy to scan.
"""


# -------------------------------------------------------------------
# Endpoint
# -------------------------------------------------------------------

@app.post("/run-agent")
async def run_agent(request: TaskRequest):
    try:
        # Log incoming request
        print("\n" + "=" * 80)
        print("Incoming request:")
        print(f"  Goal: {request.goal}")
        print(f"  History length: {len(request.history) if request.history else 0}")

        # Build full history including the latest user message
        history: List[ChatTurn] = (request.history or []) + [
            ChatTurn(role="user", content=request.goal)
        ]

        slots = extract_slots(history)
        print(f"  Extracted slots: {slots}")

        missing = [k for k, v in slots.items() if v is None]
        print(f"  Missing core slots: {missing}")

        # ------------------------------------------------------------------
        # 1) Need more info → clarifying follow-up(s)
        # ------------------------------------------------------------------
        if missing:
            messages = [{"role": "system", "content": PROJECTSCOUT_CLARIFY_SYSTEM}]

            # Replay conversation for context
            for turn in history:
                role = "assistant" if turn.role == "agent" else "user"
                messages.append({"role": role, "content": turn.content})

            # Also tell the model exactly which core fields are missing
            messages.append({
                "role": "system",
                "content": (
                    "Core fields still missing: "
                    + ", ".join(missing)
                    + ". Ask about these, and optionally one more helpful question "
                      "about domain, tech stack, or project type if needed."
                ),
            })

            completion = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.35,
            )
            reply_raw = completion.choices[0].message.content
            reply = normalize_reply(reply_raw)

            print(f"  Clarification reply: {reply[:120]}...")

            return {
                "status": "completed",
                "message": reply,
                "data": slots,   # current understanding of core fields
                "finished": False,
                "type": "clarification",
            }

        # ------------------------------------------------------------------
        # 2) All core slots filled → suggest projects
        # ------------------------------------------------------------------
        messages = [{"role": "system", "content": PROJECTSCOUT_PLAN_SYSTEM}]

        # Replay conversation for flavor/context (includes domain, stack prefs, etc.)
        for turn in history:
            role = "assistant" if turn.role == "agent" else "user"
            messages.append({"role": role, "content": turn.content})

        # Provide a clean state summary so the model is grounded
        summary = (
            f"User state:\n"
            f"- experience_level: {slots['level']}\n"
            f"- time_budget: {slots['time']}\n"
            f"- goal_type: {slots['goal_type']}\n"
            f"- latest_goal_message: {request.goal}\n"
            f"Use the conversation history above to infer domain, stack, "
            f"and any constraints they mentioned."
        )
        messages.append({"role": "system", "content": summary})

        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
        )
        reply_raw = completion.choices[0].message.content
        reply = normalize_reply(reply_raw)

        print(f"  Plan reply: {reply[:120]}...")

        return {
            "status": "completed",
            "message": reply,
            "data": slots,
            "finished": True,
            "type": "results",
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in run_agent: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
