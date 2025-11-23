from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from dotenv import load_dotenv
from typing import Optional, List, Literal
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Import your agent
from src.agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState, AgentBrowser

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatTurn(BaseModel):
    role: Literal["user", "agent"]
    content: str

class TaskRequest(BaseModel):
    goal: str  # latest user message
    history: Optional[List[ChatTurn]] = None  # full chat history from frontend

@app.post("/run-agent")
async def run_agent(request: TaskRequest):
    """
    Stateless endpoint that accepts full chat history from frontend.
    """
    try:
        # Log incoming request
        print(f"\n{'='*80}")
        print(f"Incoming request:")
        print(f"  Goal: {request.goal}")
        print(f"  History length: {len(request.history) if request.history else 0}")
        
        # Create a new agent and browser for this request
        agent = ProjectScoutAgent()
        browser = AgentBrowser(headless=True)
        await browser.start()
        
        try:
            # Build conversation context from history
            messages = []
            
            # 1. Replay chat history so the agent has context
            if request.history:
                print(f"  Replaying {len(request.history)} history turns:")
                for i, turn in enumerate(request.history):
                    role = "assistant" if turn.role == "agent" else "user"
                    messages.append({"role": role, "content": turn.content})
                    print(f"    Turn {i+1} ({turn.role}): {turn.content[:50]}...")
            
            # 2. Append the latest user message
            messages.append({"role": "user", "content": request.goal})
            print(f"  Total messages for agent: {len(messages)}")
            
            # Create agent state with full conversation history
            state = AgentState(
                goal=request.goal,
                messages=messages,
                finished=False,
                step=len(messages)
            )
            
            print(f"  Agent state created with {len(state.messages)} messages")
            
            # Run the agent step
            result_state = await agent.step(browser, state)
            
            print(f"  Agent returned {len(result_state.messages)} messages")
            
            # Extract the response
            if result_state.messages:
                last_message = result_state.messages[-1]
                response_content = last_message.get("content", "")
                
                print(f"  Response preview: {response_content[:100]}...")
                
                # Try to parse as JSON if it looks like JSON (final results)
                try:
                    response_data = json.loads(response_content)
                    # This is the final project results
                    return {
                        "status": "completed",
                        "message": json.dumps(response_data, indent=2),
                        "data": response_data,
                        "finished": result_state.finished,
                        "type": "results"
                    }
                except:
                    # This is a clarification question (plain text)
                    return {
                        "status": "completed",
                        "message": response_content,
                        "finished": result_state.finished,
                        "type": "clarification",
                        "requires_input": True
                    }
            else:
                return {
                    "status": "error",
                    "message": "No response from agent"
                }
        
        finally:
            # Always clean up browser
            await browser.stop()
    
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