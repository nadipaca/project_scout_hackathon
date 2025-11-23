from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your agent and RunHarness here
from src.arena.run import RunHarness
# from your_agent_module import YourAgentClass

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize your agent (replace with your actual agent)
agent = ...  # TODO: Load your trained agent here

@app.post("/run-agent")
async def run_agent(request: Request):
    data = await request.json()
    url = data.get("url")
    goal = data.get("goal")
    # You may need to create a task spec from url/goal
    task_spec = ...  # TODO: Build task spec from url/goal

    harness = RunHarness(agent, tasks=[task_spec], parallel=1, sample_count=1)
    await harness.run()
    # Return a simple success message for now
    return {"success": True, "message": "Agent run complete."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)