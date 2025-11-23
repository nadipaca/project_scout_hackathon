"""
Comprehensive Test Suite for ProjectScout Advanced Rules

This test suite covers all 11 advanced rules with specific test cases.
Each test validates that the corresponding rule is correctly detected and handled.
"""

import asyncio
import sys
import os
from typing import Dict, List
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agi_agents.project_scout.agent import ProjectScoutAgent
from agi_agents.project_scout import advanced_rules
from arena import AgentState

load_dotenv()


class TestResult:
    """Container for test results"""
    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details


async def test_motivation_detection_uninspired() -> TestResult:
    """Test Rule 1: Detect uninspired user"""
    context = "I'm stuck and don't know what to build. Everything seems boring."
    
    state = advanced_rules.detect_motivation_state(context)
    
    if state == "uninspired":
        return TestResult(
            "Rule 1: Motivation Detection (Uninspired)",
            True,
            "✅ Correctly detected uninspired state"
        )
    else:
        return TestResult(
            "Rule 1: Motivation Detection (Uninspired)",
            False,
            f"❌ Expected 'uninspired', got '{state}'"
        )


async def test_motivation_detection_overwhelmed() -> TestResult:
    """Test Rule 1: Detect overwhelmed user"""
    context = "Everything seems too complicated. I'm overwhelmed and confused."
    
    state = advanced_rules.detect_motivation_state(context)
    
    if state == "overwhelmed":
        return TestResult(
            "Rule 1: Motivation Detection (Overwhelmed)",
            True,
            "✅ Correctly detected overwhelmed state"
        )
    else:
        return TestResult(
            "Rule 1: Motivation Detection (Overwhelmed)",
            False,
            f"❌ Expected 'overwhelmed', got '{state}'"
        )


async def test_constraint_conflict_advanced_weekend() -> TestResult:
    """Test Rule 2: Detect advanced + weekend conflict"""
    conflict = advanced_rules.detect_constraint_conflicts(
        difficulty="advanced",
        time_budget="weekend",
        domain="distributed systems"
    )
    
    if conflict and "weekend" in conflict.lower():
        return TestResult(
            "Rule 2: Constraint Conflict (Advanced + Weekend)",
            True,
            "✅ Correctly detected constraint conflict",
            conflict
        )
    else:
        return TestResult(
            "Rule 2: Constraint Conflict (Advanced + Weekend)",
            False,
            f"❌ Expected conflict message, got: {conflict}"
        )


async def test_constraint_conflict_beginner_long_time() -> TestResult:
    """Test Rule 2: Detect beginner + 3+ weeks opportunity"""
    conflict = advanced_rules.detect_constraint_conflicts(
        difficulty="beginner",
        time_budget="3+ weeks",
        domain="web development"
    )
    
    if conflict and "intermediate" in conflict.lower():
        return TestResult(
            "Rule 2: Constraint Conflict (Beginner + Long Time)",
            True,
            "✅ Correctly suggested intermediate upgrade",
            conflict
        )
    else:
        return TestResult(
            "Rule 2: Constraint Conflict (Beginner + Long Time)",
            False,
            f"❌ Expected upgrade suggestion, got: {conflict}"
        )


async def test_ambiguity_cooldown() -> TestResult:
    """Test Rule 3: Ambiguity cooldown after vague responses"""
    recent_responses = ["I don't know", "whatever", "you decide"]
    
    should_cooldown = advanced_rules.should_apply_ambiguity_cooldown(
        clarification_count=2,
        recent_responses=recent_responses
    )
    
    if should_cooldown:
        return TestResult(
            "Rule 3: Ambiguity Cooldown",
            True,
            "✅ Correctly applied cooldown after vague responses"
        )
    else:
        return TestResult(
            "Rule 3: Ambiguity Cooldown",
            False,
            "❌ Should have applied cooldown"
        )


async def test_skill_bridge() -> TestResult:
    """Test Rule 4: Detect skill bridge opportunity"""
    context = "I'm good at Python but new to React and web development"
    
    bridge = advanced_rules.detect_skill_bridge_opportunity(context)
    
    if bridge and bridge.get("bridge_needed"):
        return TestResult(
            "Rule 4: Persona-Based Scaffolding",
            True,
            "✅ Correctly detected skill bridge opportunity",
            bridge.get("suggestion", "")
        )
    else:
        return TestResult(
            "Rule 4: Persona-Based Scaffolding",
            False,
            "❌ Failed to detect skill bridge"
        )


async def test_inspiration_discovery() -> TestResult:
    """Test Rule 5: Detect need for inspiration"""
    context = "I'm bored and need some interesting project ideas"
    
    needs_inspiration = advanced_rules.detect_inspiration_need(context)
    
    if needs_inspiration:
        return TestResult(
            "Rule 5: Inspiration-Driven Discovery",
            True,
            "✅ Correctly detected inspiration need"
        )
    else:
        return TestResult(
            "Rule 5: Inspiration-Driven Discovery",
            False,
            "❌ Failed to detect inspiration need"
        )


async def test_trending_request() -> TestResult:
    """Test Rule 6: Detect trending/hot request"""
    context = "What's hot in AI right now? Show me the latest trending projects."
    
    wants_trending = advanced_rules.detect_trending_request(context)
    
    if wants_trending:
        return TestResult(
            "Rule 6: Context-Aware Ideation (Trending)",
            True,
            "✅ Correctly detected trending request"
        )
    else:
        return TestResult(
            "Rule 6: Context-Aware Ideation (Trending)",
            False,
            "❌ Failed to detect trending request"
        )


async def test_upgrade_existing_project() -> TestResult:
    """Test Rule 7: Detect upgrade intent"""
    context = "I have a Flask app and want to add AI features to it"
    
    upgrade_info = advanced_rules.detect_upgrade_intent(context)
    
    if upgrade_info and upgrade_info.get("upgrade_mode"):
        return TestResult(
            "Rule 7: Reuse/Upgrade Existing Project",
            True,
            "✅ Correctly detected upgrade intent",
            upgrade_info.get("suggestion", "")
        )
    else:
        return TestResult(
            "Rule 7: Reuse/Upgrade Existing Project",
            False,
            "❌ Failed to detect upgrade intent"
        )


async def test_locale_awareness() -> TestResult:
    """Test Rule 8: Detect locale/market"""
    context = "I'm building an app for the Indian market with local payment options"
    
    locale = advanced_rules.detect_locale_or_market(context)
    
    if locale and "india" in locale.lower():
        return TestResult(
            "Rule 8: Locale/Market Awareness",
            True,
            f"✅ Correctly detected locale: {locale}"
        )
    else:
        return TestResult(
            "Rule 8: Locale/Market Awareness",
            False,
            f"❌ Expected 'Indian', got: {locale}"
        )


async def test_privacy_sensitivity() -> TestResult:
    """Test Rule 9: Detect privacy concerns"""
    context = "I don't want to use any cloud APIs. Privacy is very important to me."
    
    privacy_mode = advanced_rules.detect_privacy_concerns(context)
    
    if privacy_mode:
        return TestResult(
            "Rule 9: Privacy Sensitivity",
            True,
            "✅ Correctly detected privacy concerns"
        )
    else:
        return TestResult(
            "Rule 9: Privacy Sensitivity",
            False,
            "❌ Failed to detect privacy concerns"
        )


async def test_quality_emphasis() -> TestResult:
    """Test Rule 10: Analyze quality emphasis"""
    context = "I need a production-ready project with tests, CI/CD, and good documentation"
    
    quality = advanced_rules.analyze_quality_emphasis(context)
    
    if quality["quality_focus"] == "production" and quality["doc_emphasis"] == "high":
        return TestResult(
            "Rule 10: Quality/Showcase/Polish Emphasis",
            True,
            "✅ Correctly analyzed quality requirements",
            f"Quality: {quality['quality_focus']}, Docs: {quality['doc_emphasis']}"
        )
    else:
        return TestResult(
            "Rule 10: Quality/Showcase/Polish Emphasis",
            False,
            f"❌ Expected production/high, got: {quality}"
        )


async def test_portfolio_narrative() -> TestResult:
    """Test Rule 11: Generate portfolio narrative"""
    context = "Building for my portfolio to get a job at FAANG companies"
    
    narrative = advanced_rules.generate_portfolio_narrative(
        project_name="AI Chatbot",
        domain="AI/ML",
        user_context=context
    )
    
    if "FAANG" in narrative and "portfolio" in narrative.lower():
        return TestResult(
            "Rule 11: Upgrade Path & Portfolio Story",
            True,
            "✅ Correctly generated portfolio narrative",
            narrative[:200] + "..."
        )
    else:
        return TestResult(
            "Rule 11: Upgrade Path & Portfolio Story",
            False,
            "❌ Failed to generate appropriate narrative"
        )


async def test_end_to_end_uninspired_user() -> TestResult:
    """End-to-end test: Uninspired user gets adaptive tone"""
    agent = ProjectScoutAgent()
    context = "I'm stuck and overwhelmed. Don't know what to build."
    
    try:
        analysis = await agent._analyze_request(context)
        
        # Check if motivation state was detected
        if hasattr(analysis, 'motivation_state'):
            if analysis.motivation_state in ["overwhelmed", "uninspired"]:
                return TestResult(
                    "E2E: Uninspired User Flow",
                    True,
                    f"✅ Agent correctly detected {analysis.motivation_state} state"
                )
        
        return TestResult(
            "E2E: Uninspired User Flow",
            False,
            "❌ Agent did not detect motivation state"
        )
    except Exception as e:
        return TestResult(
            "E2E: Uninspired User Flow",
            False,
            f"❌ Error: {str(e)}"
        )


async def test_end_to_end_privacy_mode() -> TestResult:
    """End-to-end test: Privacy-conscious user gets local suggestions"""
    agent = ProjectScoutAgent()
    context = "I want to build an AI app but don't want to use any cloud APIs. Privacy is important."
    
    try:
        analysis = await agent._analyze_request(context)
        
        # Check if privacy mode was detected
        if hasattr(analysis, 'privacy_mode'):
            if analysis.privacy_mode:
                return TestResult(
                    "E2E: Privacy Mode Flow",
                    True,
                    "✅ Agent correctly detected privacy mode"
                )
        
        return TestResult(
            "E2E: Privacy Mode Flow",
            False,
            "❌ Agent did not detect privacy mode"
        )
    except Exception as e:
        return TestResult(
            "E2E: Privacy Mode Flow",
            False,
            f"❌ Error: {str(e)}"
        )


async def run_all_tests() -> List[TestResult]:
    """Run all tests and return results"""
    tests = [
        test_motivation_detection_uninspired(),
        test_motivation_detection_overwhelmed(),
        test_constraint_conflict_advanced_weekend(),
        test_constraint_conflict_beginner_long_time(),
        test_ambiguity_cooldown(),
        test_skill_bridge(),
        test_inspiration_discovery(),
        test_trending_request(),
        test_upgrade_existing_project(),
        test_locale_awareness(),
        test_privacy_sensitivity(),
        test_quality_emphasis(),
        test_portfolio_narrative(),
        test_end_to_end_uninspired_user(),
        test_end_to_end_privacy_mode(),
    ]
    
    results = await asyncio.gather(*tests)
    return results


def print_results(results: List[TestResult]):
    """Print test results in a formatted way"""
    print("\n" + "="*80)
    print("PROJECTSCOUT ADVANCED RULES TEST RESULTS")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for result in results:
        print(f"{result.name}")
        print(f"  {result.message}")
        if result.details:
            print(f"  Details: {result.details[:100]}...")
        print()
        
        if result.passed:
            passed += 1
        else:
            failed += 1
    
    print("="*80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(results)} tests")
    print("="*80 + "\n")
    
    return passed, failed


async def main():
    """Main test runner"""
    print("\n🚀 Starting ProjectScout Advanced Rules Test Suite...\n")
    
    results = await run_all_tests()
    passed, failed = print_results(results)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"❌ {failed} test(s) failed. Please review and fix.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
