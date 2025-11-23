import asyncio
import json
import sys
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

load_dotenv()

async def test_v2_flow():
    print("Testing V2 Features End-to-End...")
    agent = ProjectScoutAgent()
    
    # User input that triggers V2 features:
    # - Portfolio goal -> should trigger Doc Emphasis
    # - "Free" -> should trigger Cost Constraints
    # - "React" -> should trigger Tech Stack
    goal = "I want to build a React AI app for my portfolio. I want to keep it free, no paid APIs."
    
    state = AgentState(goal=goal)
    
    # Step 1: Analyze Request
    print("\n1. Analyzing Request...")
    analysis = await agent._analyze_request(f"User: {goal}")
    
    if hasattr(analysis, 'questions'):
        print("Agent asked for clarification (unexpected for this clear prompt):")
        print(analysis.questions)
        return

    print("Agent Input Analysis:")
    print(f"  - Goal: {analysis.goal_text}")
    print(f"  - Cost Constraints: {analysis.cost_constraints} (Expected: free-only/free-preferred)")
    print(f"  - Goal Type: {analysis.goal_type} (Expected: portfolio)")
    print(f"  - Doc Emphasis: {analysis.doc_emphasis} (Expected: high/medium)")
    
    # Step 2: Search GitHub
    print("\n2. Searching GitHub...")
    repos = await agent._search_github(analysis)
    print(f"Found {len(repos)} repos")
    
    # Step 3: Classify
    print("\n3. Classifying & Selecting...")
    projects = await agent._classify_and_select(analysis, repos)
    
    if not projects:
        print("No projects selected.")
        return

    top_project = projects[0]
    print(f"Selected Project: {top_project.name}")
    print(f"Why Match: {top_project.why_match}")
    
    # Step 4: Generate Roadmap
    print("\n4. Generating Roadmap...")
    roadmap = await agent._generate_roadmap(analysis, top_project)
    
    print("Roadmap V2 Features:")
    if roadmap.checkpoints:
        print(f"  - Checkpoints: {len(roadmap.checkpoints)} found")
        print(f"    Example: {roadmap.checkpoints[0]}")
    else:
        print("  - Checkpoints: NONE (Failed)")
        
    if roadmap.upgrade_path:
        print(f"  - Upgrade Path: {len(roadmap.upgrade_path)} items")
        print(f"    Example: {roadmap.upgrade_path[0]}")
    else:
        print("  - Upgrade Path: NONE (Failed)")
        
    if roadmap.scope_note:
        print(f"  - Scope Note: {roadmap.scope_note}")
        
    if roadmap.deployment_strategy:
        print(f"  - Deployment Strategy: {roadmap.deployment_strategy}")
    else:
        print("  - Deployment Strategy: NONE (Failed)")
    
    # Check for doc tasks
    has_doc_task = False
    has_demo_task = False
    for phase in roadmap.phases:
        for task in phase.tasks:
            if "README" in task or "Document" in task:
                has_doc_task = True
            if "Demo" in task or "Video" in task or "GIF" in task:
                has_demo_task = True
                
    print(f"  - Documentation Tasks Found: {has_doc_task}")
    print(f"  - Demo/Video Task Found: {has_demo_task}")

if __name__ == "__main__":
    asyncio.run(test_v2_flow())
