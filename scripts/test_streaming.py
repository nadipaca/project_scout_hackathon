import asyncio
import json
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

load_dotenv()

async def test_streaming():
    print("Testing Streaming Responses...")
    agent = ProjectScoutAgent()
    goal = "I want to build a React AI app for my portfolio. I want to keep it free, no paid APIs."
    state = AgentState(goal=goal)
    
    step_count = 0
    status_messages = []
    
    while not state.finished:
        step_count += 1
        print(f"\n--- Step {step_count} ---")
        await agent.step(None, state)
        
        if state.messages:
            last_msg = state.messages[-1]
            content = last_msg["content"]
            
            if last_msg["role"] == "assistant":
                if content.startswith("[STATUS]"):
                    print(f"Received Status: {content}")
                    status_messages.append(content)
                elif "{" in content and "}" in content:
                    print("Received Final JSON Output")
                else:
                    print(f"Received Message: {content[:50]}...")

    print("\n--- Test Results ---")
    print(f"Total Steps: {step_count}")
    print(f"Status Messages Received: {len(status_messages)}")
    for msg in status_messages:
        print(f"  - {msg}")
        
    # Assertions
    assert len(status_messages) >= 3, "Should receive at least 3 status updates (Analysis, Search, Classification)"
    assert any("Analysis complete" in msg for msg in status_messages)
    assert any("Found" in msg and "repositories" in msg for msg in status_messages)
    assert any("Selected" in msg for msg in status_messages)
    print("\n✅ Streaming Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_streaming())
