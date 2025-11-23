import asyncio
import json
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

load_dotenv()

async def repro_fix():
    print("Testing Fix for Long/Diverse Queries...")
    agent = ProjectScoutAgent()
    
    # The exact failing prompt from the user
    goal = """Hi, I want to build a project to learn something new for my portfolio, but I’m not sure which area to focus on—NLP, web apps, or computer vision all sound interesting.I’m working solo and prefer free/open-source solutions since I’m on a budget.A mix of repo templates and tutorials would be great, and I definitely want something with a frontend component.I’ve got intermediate skills in Python and basic React, and I’d like recommendations that are well-documented, follow best practices, and can be done over 1–2 weeks.Can you show me a few diverse options and let me know which have full-stack templates I can use directly? If any would be good for upgrading to a team or production later, that’s a plus."""
    
    state = AgentState(goal=goal)
    
    while not state.finished:
        await agent.step(None, state)
        
        if state.messages and state.messages[-1]["role"] == "assistant":
            content = state.messages[-1]["content"]
            if content.startswith("[STATUS]"):
                print(f"Status: {content}")
            elif "{" in content:
                print("Received JSON Output!")
                try:
                    data = json.loads(content)
                    projects = data.get("projects", [])
                    print(f"Found {len(projects)} projects.")
                    for p in projects:
                        print(f"- {p['name']} ({p['stack_tags']})")
                    
                    if len(projects) > 0:
                        print("\n✅ Fix Verified: Projects found despite complex query!")
                    else:
                        print("\n❌ Failed: No projects found.")
                except:
                    print("Failed to parse JSON")
            else:
                print(f"Agent: {content}")

if __name__ == "__main__":
    asyncio.run(repro_fix())
