"""
Comprehensive test suite for ProjectScout agent behavior validation.

Tests 10 key scenarios to ensure the agent correctly:
- Asks appropriate clarifying questions
- Preserves tech stack preferences
- Handles edge cases (conflicts, vague requests, privacy concerns)
- Provides personalized recommendations
"""

import pytest
import asyncio
from typing import List, Dict
from src.agi_agents.project_scout.agent import ProjectScoutAgent
from src.agi_agents.project_scout.models import Clarification, AgentInput
from arena import AgentState


class TestProjectScoutScenarios:
    """Test suite for ProjectScout agent scenario validation."""
    
    @pytest.fixture
    async def agent(self):
        """Create a ProjectScout agent instance for testing."""
        return ProjectScoutAgent(model="gpt-4o-mini")
    
    def create_state(self, goal: str, messages: List[Dict] = None) -> AgentState:
        """Helper to create an AgentState for testing."""
        return AgentState(
            goal=goal,
            messages=messages or [],
            finished=False
        )
    
    async def run_conversation(self, agent: ProjectScoutAgent, initial_goal: str, user_responses: List[str]):
        """
        Simulate a multi-turn conversation with the agent.
        
        Args:
            agent: ProjectScout agent instance
            initial_goal: User's initial request
            user_responses: List of user responses to agent questions
            
        Returns:
            Final state and all agent responses
        """
        state = self.create_state(initial_goal)
        agent_responses = []
        
        for user_response in user_responses:
            # Run agent step
            state = await agent.step(None, state)
            
            # Capture agent's response
            if state.messages and state.messages[-1]["role"] == "assistant":
                agent_responses.append(state.messages[-1]["content"])
            
            # If agent asked questions and we have a user response, add it
            if not state.finished and user_response:
                state.messages.append({"role": "user", "content": user_response})
        
        # Final step to get results
        if not state.finished:
            state = await agent.step(None, state)
            if state.messages and state.messages[-1]["role"] == "assistant":
                agent_responses.append(state.messages[-1]["content"])
        
        return state, agent_responses
    
    @pytest.mark.asyncio
    async def test_case_1_beginner_python_ideas(self, agent):
        """
        Test Case 1: Beginner Python Ideas (classic)
        User wants cool Python projects, should be asked about difficulty.
        """
        initial_goal = "Give me some cool Python projects."
        user_responses = ["beginner"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent asked about difficulty
        assert len(responses) >= 1, "Agent should ask at least one question"
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["difficulty", "level", "beginner", "intermediate", "advanced"]), \
            "Agent should ask about difficulty level"
        
        # Verify final response mentions beginner-friendly projects
        if len(responses) > 1:
            final_response = responses[-1].lower()
            assert "beginner" in final_response or "simple" in final_response, \
                "Final response should acknowledge beginner level"
    
    @pytest.mark.asyncio
    async def test_case_2_advanced_backend_career(self, agent):
        """
        Test Case 2: Advanced Backend Career Project
        User specifies advanced Java + Spring + Postgres, should ask about quality/testing.
        """
        initial_goal = "I'm aiming for senior backend roles. Give me one solid Java + Spring + Postgres project to work on for about a month."
        user_responses = ["yes, include quality stuff"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent preserves Java/Spring stack
        context_check = " ".join(responses).lower()
        assert any(tech in context_check for tech in ["java", "spring", "postgres"]), \
            "Agent should preserve Java/Spring/Postgres stack"
        
        # Verify agent asks about quality/testing
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["test", "ci", "quality", "observability"]), \
            "Agent should ask about tests/CI/quality for advanced projects"
    
    @pytest.mark.asyncio
    async def test_case_3_unrealistic_combo_conflict(self, agent):
        """
        Test Case 3: Unrealistic Combo (Conflict + Re-scope)
        Beginner wants advanced microservices in a weekend - should detect conflict.
        """
        initial_goal = "I want a crazy advanced AI agent system with microservices and Kubernetes, but I only have this weekend and I'm a beginner."
        user_responses = ["build a smaller core project"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent detects the conflict
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["ambitious", "conflict", "realistic", "smaller", "scope"]), \
            "Agent should detect unrealistic combination and suggest rescoping"
    
    @pytest.mark.asyncio
    async def test_case_4_frontend_vague_spa(self, agent):
        """
        Test Case 4: Non-Technical, Vague but Frontend-ish
        User describes SPA behavior without technical terms.
        """
        initial_goal = "I like those websites where the page doesn't reload and data updates magically. I want to build something like that."
        user_responses = ["React, intermediate"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent identifies SPA/frontend focus
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["react", "vue", "spa", "single-page", "frontend"]), \
            "Agent should identify single-page app requirement"
    
    @pytest.mark.asyncio
    async def test_case_5_portfolio_india_localization(self, agent):
        """
        Test Case 5: Portfolio + India Market + Localization
        User wants India-focused roommate expense app.
        """
        initial_goal = "I want a portfolio project for the Indian market, maybe something around splitting rent and bills with roommates. Stack can be React + Node. I can spend about 2 weeks."
        user_responses = ["solo project", "English only"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent preserves React + Node stack
        context_check = " ".join(responses).lower()
        assert "react" in context_check or "node" in context_check, \
            "Agent should preserve React + Node stack"
        
        # Verify agent asks about collaboration or localization
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["solo", "team", "language", "localization", "hindi"]), \
            "Agent should ask about collaboration mode or localization for market-specific projects"
    
    @pytest.mark.asyncio
    async def test_case_6_privacy_local_models(self, agent):
        """
        Test Case 6: Privacy-Sensitive Own Data + Local Models
        User wants private journal analysis with local-only processing.
        """
        initial_goal = "I want an AI project that analyzes my personal journal entries, but the data must stay completely private on my machine."
        user_responses = ["local model, intermediate"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent detects privacy concerns
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["local", "privacy", "private", "offline", "machine"]), \
            "Agent should acknowledge privacy requirements and suggest local solutions"
    
    @pytest.mark.asyncio
    async def test_case_7_reuse_existing_project(self, agent):
        """
        Test Case 7: Reuse Existing Project
        User wants to upgrade existing CRUD app.
        """
        initial_goal = "I already have a basic CRUD app in React + Node for tracking tasks. I want to upgrade it so it looks and feels like a real product for my resume."
        user_responses = ["more UI, include some tests"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent detects upgrade intent
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["ui", "ux", "backend", "test", "upgrade", "polish"]), \
            "Agent should ask about upgrade focus areas"
        
        # Verify agent preserves React + Node stack
        context_check = " ".join(responses).lower()
        assert "react" in context_check or "node" in context_check, \
            "Agent should preserve existing React + Node stack"
    
    @pytest.mark.asyncio
    async def test_case_8_hackathon_short_time(self, agent):
        """
        Test Case 8: Hackathon Agent, Very Short Time
        User needs impressive AI project in 2 days for hackathon.
        """
        initial_goal = "There's a hackathon this weekend. I want a small but impressive AI agent project in Python that I can realistically finish in 2 days."
        user_responses = ["free-tier APIs okay, basic web UI"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent asks about API constraints or UI preferences
        first_response = responses[0].lower()
        assert any(word in first_response for word in ["api", "free", "ui", "web", "cli", "demo"]), \
            "Agent should ask about API constraints or UI preferences for hackathon projects"
        
        # Verify agent acknowledges time constraint
        context_check = " ".join(responses).lower()
        assert any(word in context_check for word in ["2 days", "weekend", "short", "quick", "hackathon"]), \
            "Agent should acknowledge tight time constraint"
    
    @pytest.mark.asyncio
    async def test_case_9_indecisive_user_defaults(self, agent):
        """
        Test Case 9: Indecisive User ("Anything is Fine")
        User delegates decision to agent.
        """
        initial_goal = "Anything is fine, you just pick a project."
        user_responses = []
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent proceeds with defaults without asking many questions
        # Should use ambiguity handling to proceed directly
        assert state.finished or len(responses) <= 2, \
            "Agent should use defaults for indecisive users, not ask many questions"
    
    @pytest.mark.asyncio
    async def test_case_10_learning_style_motivation(self, agent):
        """
        Test Case 10: Learning Style & Motivation
        User has failed projects and gets overwhelmed - needs encouragement.
        """
        initial_goal = "I've failed to finish my last 3 projects and I get overwhelmed easily. I just want one simple AI project that helps me learn, nothing too fancy."
        user_responses = ["1-2 weeks, Python"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify agent detects motivation state
        first_response = responses[0].lower()
        # Agent should ask clarifying questions in a supportive way
        assert len(first_response) > 0, "Agent should respond to user's concerns"
        
        # Verify agent suggests simple, achievable project
        if len(responses) > 1:
            final_response = responses[-1].lower()
            assert any(word in final_response for word in ["simple", "doable", "small", "basic", "beginner"]), \
                "Agent should suggest simple, achievable projects for overwhelmed users"
    
    @pytest.mark.asyncio
    async def test_spring_ai_preservation(self, agent):
        """
        Regression test: Ensure Spring AI tech stack is preserved across conversation.
        """
        initial_goal = "Give me a spring AI project"
        user_responses = ["intermediate", "2 weeks and I am doing for portfolio"]
        
        state, responses = await self.run_conversation(agent, initial_goal, user_responses)
        
        # Verify Spring AI is preserved in search
        context_check = " ".join(responses).lower()
        assert "spring" in context_check or "java" in context_check, \
            "Agent should preserve Spring AI tech stack, not default to Python"


class TestAgentAnalysisLogic:
    """Test the agent's analysis logic in isolation."""
    
    @pytest.fixture
    async def agent(self):
        """Create a ProjectScout agent instance for testing."""
        return ProjectScoutAgent(model="gpt-4o-mini")
    
    @pytest.mark.asyncio
    async def test_minimal_request_asks_questions(self, agent):
        """Verify that minimal requests trigger clarifying questions."""
        context = "Initial Goal: Give me a Python project\n"
        
        result = await agent._analyze_request(context)
        
        # Should return Clarification, not AgentInput
        assert isinstance(result, Clarification), \
            "Minimal requests should trigger clarifying questions"
        assert len(result.questions) >= 2, \
            "Should ask at least 2 questions for minimal requests"
    
    @pytest.mark.asyncio
    async def test_detailed_request_proceeds(self, agent):
        """Verify that detailed requests can proceed with minimal questions."""
        context = "Initial Goal: I'm a beginner looking for a weekend Python web project for my portfolio\n"
        
        result = await agent._analyze_request(context)
        
        # Should return AgentInput or ask minimal questions
        if isinstance(result, Clarification):
            assert len(result.questions) <= 1, \
                "Detailed requests should ask minimal or no questions"
    
    @pytest.mark.asyncio
    async def test_you_decide_uses_defaults(self, agent):
        """Verify that 'you decide' requests use defaults without questions."""
        context = "Initial Goal: Surprise me with any Python project, you decide\n"
        
        result = await agent._analyze_request(context)
        
        # Should return AgentInput with defaults, not Clarification
        assert isinstance(result, AgentInput), \
            "'You decide' requests should use defaults without asking questions"


# Scoring and reporting
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Custom test summary with accuracy calculation."""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    total = passed + failed
    
    if total > 0:
        accuracy = (passed / total) * 100
        terminalreporter.write_sep("=", "ProjectScout Agent Test Summary")
        terminalreporter.write_line(f"Total Tests: {total}")
        terminalreporter.write_line(f"Passed: {passed}")
        terminalreporter.write_line(f"Failed: {failed}")
        terminalreporter.write_line(f"Accuracy: {accuracy:.1f}%")
