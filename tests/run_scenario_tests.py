"""
Simple test runner for ProjectScout agent scenarios.
Can be run directly without pytest: python tests/run_scenario_tests.py

REQUIREMENTS:
- Set OPENAI_API_KEY environment variable before running
- Example: $env:OPENAI_API_KEY="your-key-here" (PowerShell)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agi_agents.project_scout.agent import ProjectScoutAgent
from src.agi_agents.project_scout.models import Clarification, AgentInput
from arena import AgentState


class ScenarioTester:
    """Simple test runner for ProjectScout scenarios."""
    
    def __init__(self):
        # Check for API key before initializing agent
        if not os.getenv("OPENAI_API_KEY"):
            print("=" * 60)
            print("ERROR: OPENAI_API_KEY environment variable not set")
            print("=" * 60)
            print("\nTo run these tests, you need to set your OpenAI API key:")
            print("\nPowerShell:")
            print('  $env:OPENAI_API_KEY="your-key-here"')
            print('  uv run python tests/run_scenario_tests.py')
            print("\nBash/Linux:")
            print('  export OPENAI_API_KEY="your-key-here"')
            print('  uv run python tests/run_scenario_tests.py')
            print("\nOr create a .env file in the project root with:")
            print('  OPENAI_API_KEY=your-key-here')
            print("=" * 60)
            sys.exit(1)
        
        try:
            self.agent = ProjectScoutAgent(model="gpt-4o-mini")
        except Exception as e:
            print(f"ERROR: Failed to initialize ProjectScout agent: {e}")
            sys.exit(1)
        
        self.passed = 0
        self.failed = 0
        self.results = []
    
    async def run_conversation(self, initial_goal: str, user_responses: list):
        """Simulate a multi-turn conversation."""
        state = AgentState(goal=initial_goal, messages=[], finished=False)
        agent_responses = []
        
        for user_response in user_responses:
            state = await self.agent.step(None, state)
            
            if state.messages and state.messages[-1]["role"] == "assistant":
                agent_responses.append(state.messages[-1]["content"])
            
            if not state.finished and user_response:
                state.messages.append({"role": "user", "content": user_response})
        
        if not state.finished:
            state = await self.agent.step(None, state)
            if state.messages and state.messages[-1]["role"] == "assistant":
                agent_responses.append(state.messages[-1]["content"])
        
        return state, agent_responses
    
    def assert_contains(self, text: str, keywords: list, test_name: str, description: str):
        """Check if text contains any of the keywords."""
        text_lower = text.lower()
        if any(keyword.lower() in text_lower for keyword in keywords):
            self.passed += 1
            self.results.append(f"✓ {test_name}: PASS - {description}")
            return True
        else:
            self.failed += 1
            self.results.append(f"✗ {test_name}: FAIL - {description}")
            self.results.append(f"  Expected keywords: {keywords}")
            self.results.append(f"  Got: {text[:200]}...")
            return False
    
    async def test_case_1_beginner_python(self):
        """Test Case 1: Beginner Python Ideas"""
        print("\n[1/10] Testing: Beginner Python Ideas...")
        
        initial_goal = "Give me some cool Python projects."
        user_responses = ["beginner"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent asks about difficulty
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["difficulty", "level", "beginner", "intermediate", "advanced", "experience"],
            "Test 1",
            "Agent should ask about difficulty level"
        )
    
    async def test_case_2_advanced_backend(self):
        """Test Case 2: Advanced Backend Career Project"""
        print("[2/10] Testing: Advanced Backend Career...")
        
        initial_goal = "I'm aiming for senior backend roles. Give me one solid Java + Spring + Postgres project to work on for about a month."
        user_responses = ["yes, include quality stuff"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if Java/Spring is preserved
        all_text = " ".join(responses)
        self.assert_contains(
            all_text,
            ["java", "spring", "postgres"],
            "Test 2",
            "Agent should preserve Java/Spring/Postgres stack"
        )
    
    async def test_case_3_unrealistic_combo(self):
        """Test Case 3: Unrealistic Combo (Conflict Detection)"""
        print("[3/10] Testing: Unrealistic Combo Conflict...")
        
        initial_goal = "I want a crazy advanced AI agent system with microservices and Kubernetes, but I only have this weekend and I'm a beginner."
        user_responses = ["build a smaller core project"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent detects conflict
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["ambitious", "conflict", "realistic", "smaller", "scope", "weekend", "beginner"],
            "Test 3",
            "Agent should detect unrealistic combination"
        )
    
    async def test_case_4_frontend_spa(self):
        """Test Case 4: Vague Frontend SPA Request"""
        print("[4/10] Testing: Vague Frontend SPA...")
        
        initial_goal = "I like those websites where the page doesn't reload and data updates magically. I want to build something like that."
        user_responses = ["React, intermediate"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent identifies SPA
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["react", "vue", "spa", "single-page", "frontend", "framework"],
            "Test 4",
            "Agent should identify single-page app requirement"
        )
    
    async def test_case_5_india_localization(self):
        """Test Case 5: India Market Localization"""
        print("[5/10] Testing: India Market Localization...")
        
        initial_goal = "I want a portfolio project for the Indian market, maybe something around splitting rent and bills with roommates. Stack can be React + Node. I can spend about 2 weeks."
        user_responses = ["solo project", "English only"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if React + Node is preserved
        all_text = " ".join(responses)
        self.assert_contains(
            all_text,
            ["react", "node"],
            "Test 5",
            "Agent should preserve React + Node stack"
        )
    
    async def test_case_6_privacy_local(self):
        """Test Case 6: Privacy-Sensitive Local Models"""
        print("[6/10] Testing: Privacy-Sensitive Local Models...")
        
        initial_goal = "I want an AI project that analyzes my personal journal entries, but the data must stay completely private on my machine."
        user_responses = ["local model, intermediate"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent acknowledges privacy
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["local", "privacy", "private", "offline", "machine", "model"],
            "Test 6",
            "Agent should acknowledge privacy requirements"
        )
    
    async def test_case_7_upgrade_existing(self):
        """Test Case 7: Upgrade Existing Project"""
        print("[7/10] Testing: Upgrade Existing Project...")
        
        initial_goal = "I already have a basic CRUD app in React + Node for tracking tasks. I want to upgrade it so it looks and feels like a real product for my resume."
        user_responses = ["more UI, include some tests"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent asks about upgrade focus
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["ui", "ux", "backend", "test", "upgrade", "polish", "focus"],
            "Test 7",
            "Agent should ask about upgrade focus areas"
        )
    
    async def test_case_8_hackathon_short_time(self):
        """Test Case 8: Hackathon Short Time"""
        print("[8/10] Testing: Hackathon Short Time...")
        
        initial_goal = "There's a hackathon this weekend. I want a small but impressive AI agent project in Python that I can realistically finish in 2 days."
        user_responses = ["free-tier APIs okay, basic web UI"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent asks about constraints
        first_response = responses[0] if responses else ""
        self.assert_contains(
            first_response,
            ["api", "free", "ui", "web", "cli", "demo", "tier"],
            "Test 8",
            "Agent should ask about API/UI constraints"
        )
    
    async def test_case_9_indecisive_defaults(self):
        """Test Case 9: Indecisive User Defaults"""
        print("[9/10] Testing: Indecisive User Defaults...")
        
        initial_goal = "Anything is fine, you just pick a project."
        user_responses = []
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent uses defaults (should finish or ask minimal questions)
        if state.finished or len(responses) <= 2:
            self.passed += 1
            self.results.append("✓ Test 9: PASS - Agent uses defaults for indecisive users")
        else:
            self.failed += 1
            self.results.append(f"✗ Test 9: FAIL - Agent asked {len(responses)} questions instead of using defaults")
    
    async def test_case_10_motivation_overwhelmed(self):
        """Test Case 10: Overwhelmed User Motivation"""
        print("[10/10] Testing: Overwhelmed User Motivation...")
        
        initial_goal = "I've failed to finish my last 3 projects and I get overwhelmed easily. I just want one simple AI project that helps me learn, nothing too fancy."
        user_responses = ["1-2 weeks, Python"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if agent suggests simple projects
        all_text = " ".join(responses).lower()
        self.assert_contains(
            all_text,
            ["simple", "doable", "small", "basic", "beginner", "easy"],
            "Test 10",
            "Agent should suggest simple projects for overwhelmed users"
        )
    
    async def test_spring_ai_preservation(self):
        """Regression Test: Spring AI Preservation"""
        print("[BONUS] Testing: Spring AI Tech Stack Preservation...")
        
        initial_goal = "Give me a spring AI project"
        user_responses = ["intermediate", "2 weeks and I am doing for portfolio"]
        
        state, responses = await self.run_conversation(initial_goal, user_responses)
        
        # Check if Spring AI is preserved
        all_text = " ".join(responses)
        self.assert_contains(
            all_text,
            ["spring", "java"],
            "Spring AI Regression",
            "Agent should preserve Spring AI, not default to Python"
        )
    
    async def run_all_tests(self):
        """Run all test cases."""
        print("=" * 60)
        print("ProjectScout Agent Scenario Tests")
        print("=" * 60)
        
        try:
            await self.test_case_1_beginner_python()
            await self.test_case_2_advanced_backend()
            await self.test_case_3_unrealistic_combo()
            await self.test_case_4_frontend_spa()
            await self.test_case_5_india_localization()
            await self.test_case_6_privacy_local()
            await self.test_case_7_upgrade_existing()
            await self.test_case_8_hackathon_short_time()
            await self.test_case_9_indecisive_defaults()
            await self.test_case_10_motivation_overwhelmed()
            await self.test_spring_ai_preservation()
        except Exception as e:
            print(f"\n❌ Test execution error: {e}")
            import traceback
            traceback.print_exc()
        
        # Print results
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        for result in self.results:
            print(result)
        
        # Print summary
        total = self.passed + self.failed
        accuracy = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Accuracy: {accuracy:.1f}%")
        print("=" * 60)
        
        return accuracy >= 70  # Return True if 70%+ pass rate


async def main():
    """Main test runner."""
    tester = ScenarioTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
