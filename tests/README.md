# ProjectScout Agent Tests

This directory contains comprehensive tests for the ProjectScout agent.

## Test Files

### 1. `test_project_scout_scenarios.py`
Full pytest test suite with 10 scenario-based tests + unit tests.

**Requirements:**
- pytest installed
- OPENAI_API_KEY environment variable set

**Run with:**
```bash
uv run python -m pytest tests/test_project_scout_scenarios.py -v
```

### 2. `run_scenario_tests.py` ⭐ **Recommended**
Standalone test runner that doesn't require pytest.

**Requirements:**
- OPENAI_API_KEY environment variable set

**Run with:**
```bash
# Set API key first (PowerShell)
$env:OPENAI_API_KEY="your-key-here"

# Run tests
uv run python tests/run_scenario_tests.py
```

**For Bash/Linux:**
```bash
export OPENAI_API_KEY="your-key-here"
uv run python tests/run_scenario_tests.py
```

## Test Coverage

All 10 test scenarios from the specification:

1. **Beginner Python Ideas** - Validates difficulty level questions
2. **Advanced Backend Career** - Tests tech stack preservation (Java/Spring)
3. **Unrealistic Combo** - Validates conflict detection and rescoping
4. **Vague Frontend SPA** - Tests SPA identification
5. **India Market Localization** - Validates React+Node preservation
6. **Privacy-Sensitive Local** - Tests privacy concern detection
7. **Upgrade Existing Project** - Validates upgrade intent detection
8. **Hackathon Short Time** - Tests constraint handling
9. **Indecisive User** - Validates default usage
10. **Overwhelmed User** - Tests motivation-aware suggestions

**Plus:**
- Spring AI Preservation (regression test)

## Expected Output

```
============================================================
ProjectScout Agent Scenario Tests
============================================================

[1/10] Testing: Beginner Python Ideas...
[2/10] Testing: Advanced Backend Career...
[3/10] Testing: Unrealistic Combo Conflict...
...

============================================================
Test Results
============================================================
✓ Test 1: PASS - Agent should ask about difficulty level
✓ Test 2: PASS - Agent should preserve Java/Spring/Postgres stack
...

============================================================
Summary
============================================================
Total Tests: 11
Passed: 10
Failed: 1
Accuracy: 90.9%
============================================================
```

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
Set your OpenAI API key before running tests:
```powershell
$env:OPENAI_API_KEY="sk-..."
```

### "No module named 'pytest'"
Use the standalone runner instead:
```bash
uv run python tests/run_scenario_tests.py
```

### Tests timing out
The tests make real API calls to OpenAI. If you're experiencing timeouts:
- Check your internet connection
- Verify your API key is valid
- Check OpenAI API status

## Notes

- Tests make **real API calls** to OpenAI (costs ~$0.01-0.05 per full test run)
- Each test simulates a multi-turn conversation with the agent
- Tests validate both question-asking behavior and final recommendations
- Minimum 70% pass rate is considered successful
