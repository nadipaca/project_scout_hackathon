"""
Quick manual test of advanced rules using the agent directly
"""
import asyncio
from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

async def test_rule(name: str, goal: str):
    """Test a specific rule with a goal"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Goal: {goal}")
    print(f"{'='*60}")
    
    agent = ProjectScoutAgent()
    state = AgentState(goal=goal)
    
    try:
        # Just analyze the request to see if rules are detected
        analysis = await agent._analyze_request(f"User: {goal}")
        
        if hasattr(analysis, 'questions'):
            print(f"✅ Agent asked for clarification:")
            for q in analysis.questions:
                print(f"   - {q}")
        else:
            print(f"✅ Agent analyzed successfully")
            print(f"   - Motivation: {getattr(analysis, 'motivation_state', 'N/A')}")
            print(f"   - Privacy Mode: {getattr(analysis, 'privacy_mode', 'N/A')}")
            print(f"   - Upgrade Mode: {getattr(analysis, 'upgrade_mode', 'N/A')}")
            print(f"   - Quality Focus: {getattr(analysis, 'quality_focus', 'N/A')}")
            print(f"   - Locale: {getattr(analysis, 'locale_preference', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all rule tests"""
    print("\n🚀 TESTING PROJECTSCOUT ADVANCED RULES\n")
    
    tests = [
        ("Rule 1: Motivation (Overwhelmed)", "I'm overwhelmed and don't know what to build"),
        ("Rule 2: Constraint Conflict", "I want to build an advanced distributed system this weekend"),
        ("Rule 3: Ambiguity Cooldown", "I don't know, you decide, whatever"),
        ("Rule 7: Upgrade Intent", "I have a Flask app and want to add AI features"),
        ("Rule 8: Locale Awareness", "Building an app for the Indian market"),
        ("Rule 9: Privacy Sensitivity", "I don't want to use any cloud APIs, privacy is important"),
        ("Rule 10: Quality Emphasis", "Need a production-ready project with tests and CI/CD"),
    ]
    
    passed = 0
    for name, goal in tests:
        if await test_rule(name, goal):
            passed += 1
        await asyncio.sleep(0.5)  # Brief pause between tests
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{len(tests)} tests passed")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
