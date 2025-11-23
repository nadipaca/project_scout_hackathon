import asyncio
import sys
from dotenv import load_dotenv
from agi_agents.project_scout.agent import ProjectScoutAgent
from agi_agents.project_scout.models import AgentInput

load_dotenv()

async def test_search():
    agent = ProjectScoutAgent()
    
    # Simulate the exact input that was failing
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
    
    print("Testing with problematic keywords...")
    print(f"Input keywords: {agent_input.search_keywords}")
    print("=" * 80)
    
    repos = await agent._search_github(agent_input)
    
    print("=" * 80)
    print(f"✓ Found {len(repos)} repositories")
    for repo in repos:
        print(f"  - {repo['full_name']}: {repo.get('description', 'No description')[:60]}...")

if __name__ == "__main__":
    asyncio.run(test_search())
