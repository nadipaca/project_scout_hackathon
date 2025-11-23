import asyncio
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from agi_agents.project_scout.models import AgentInput

load_dotenv()

async def test():
    agent = ProjectScoutAgent()
    agent_input = AgentInput(
        goal_text="Portfolio AI project",
        difficulty="intermediate",
        time_budget="1-2 weeks",
        preferred_stack="Python React",
        search_keywords="AI project, NLP, recommender systems, computer vision, open-source datasets",
        project_type="repo",
        recency_preference="latest",
        domain="AI",
        goal_type="portfolio"
    )
    
    print("Input keywords:", agent_input.search_keywords)
    repos = await agent._search_github(agent_input)
    print(f"Found {len(repos)} repos")
    for r in repos:
        print(f"- {r['full_name']}")

asyncio.run(test())
