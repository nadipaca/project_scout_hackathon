import asyncio
import json
import sys
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

load_dotenv()

# Redirect all output to a file
log_file = open("debug_detailed.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

async def main():
    agent = ProjectScoutAgent()
    
    goal = "I'm looking for AI project ideas using the latest tools and libraries. Not sure what I want to build, just want something that will look good for my future job search and LinkedIn. I'm open to any tech stack, and I can put about a week into it. Any suggestions?"
    
    # Simulate the state after the first turn and user response
    messages = [
        {"role": "assistant", "content": "What's your main goal (portfolio/learning/interview) AND what's your skill level?"},
        {"role": "user", "content": "I want it for my portfolio, and I'd say I'm at an intermediate level."}
    ]
    
    state = AgentState(goal=goal)
    state.messages = messages
    
    print("Running full agent flow...")
    print("=" * 80)
    
    # Run the agent loop to handle any clarifications
    max_turns = 5
    turn = 0
    while not state.finished and turn < max_turns:
        turn += 1
        print(f"\n=== TURN {turn} ===")
        try:
            new_state = await agent.step(None, state)
            state = new_state
            
            if not state.finished and state.messages and state.messages[-1]["role"] == "assistant":
                # Agent is asking a question
                question = state.messages[-1]["content"]
                print(f"Agent question: {question}")
                
                # Auto-answer based on context
                if "type of project" in question.lower():
                    answer = "I want to find existing repos to learn from and build my own version."
                    state.messages.append({"role": "user", "content": answer})
                    print(f"Auto-answer: {answer}")
                elif "latest tools" in question.lower():
                    answer = "Yes, I prefer the latest AI tools and libraries."
                    state.messages.append({"role": "user", "content": answer})
                    print(f"Auto-answer: {answer}")
                else:
                    print(f"Unknown question, stopping")
                    break
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print("=" * 80)
    print(f"Finished: {state.finished}")
    if state.messages:
        last_content = state.messages[-1]['content']
        print(f"Last message length: {len(last_content)} chars")
        print(f"Last message content:")
        print(last_content)
        
        # Try to parse as JSON
        try:
            result = json.loads(last_content)
            print(f"✓ Valid JSON with {len(result.get('projects', []))} projects")
        except json.JSONDecodeError as e:
            print(f"✗ Not valid JSON. Error: {e}")
            print(f"Content: {last_content}")
    
    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())
