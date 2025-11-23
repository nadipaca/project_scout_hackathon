"""
Test harness for debugging multi-turn conversation behavior.
Tests that the agent progresses through conversation instead of repeating questions.
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_two_turn_conversation():
    """
    Test a two-turn conversation to ensure agent progresses.
    """
    print("=" * 80)
    print("Testing Two-Turn Conversation")
    print("=" * 80)
    
    history = []
    
    # Turn 1: Initial request
    print("\n--- TURN 1 ---")
    turn1_goal = "I want python projects with pytorch"
    print(f"User: {turn1_goal}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
        try:
            response1 = await client.post(
                f"{BASE_URL}/run-agent",
                json={"goal": turn1_goal, "history": history}
            )
            
            if response1.status_code != 200:
                print(f"❌ Turn 1 failed with status {response1.status_code}")
                print(response1.text)
                return False
            
            data1 = response1.json()
            agent_response1 = data1.get("message", "")
            print(f"Agent: {agent_response1[:200]}...")
            
            # Add to history
            history.append({"role": "user", "content": turn1_goal})
            history.append({"role": "agent", "content": agent_response1})
        except Exception as e:
            print(f"❌ Turn 1 failed with error: {e}")
            return False
    
    # Turn 2: Answer the questions
    print("\n--- TURN 2 ---")
    turn2_goal = "beginner and 2 weeks, portfolio"
    print(f"User: {turn2_goal}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
        try:
            response2 = await client.post(
                f"{BASE_URL}/run-agent",
                json={"goal": turn2_goal, "history": history}
            )
            
            if response2.status_code != 200:
                print(f"❌ Turn 2 failed with status {response2.status_code}")
                print(response2.text)
                return False
            
            data2 = response2.json()
            agent_response2 = data2.get("message", "")
            print(f"Agent: {agent_response2[:200]}...")
        except Exception as e:
            print(f"❌ Turn 2 failed with error: {e}")
            return False
    
    # Check if responses are different
    print("\n--- ANALYSIS ---")
    
    # Simple similarity check
    response1_lower = agent_response1.lower()
    response2_lower = agent_response2.lower()
    
    # Check if Turn 2 acknowledges the user's answer
    acknowledges_beginner = "beginner" in response2_lower
    acknowledges_time = ("2 week" in response2_lower or "1-2 week" in response2_lower)
    acknowledges_portfolio = "portfolio" in response2_lower
    
    # Check if Turn 2 is asking the SAME questions again
    asks_experience_again = ("experience level" in response2_lower or 
                            "what's your experience" in response2_lower)
    asks_time_again = ("how much time" in response2_lower and 
                      not acknowledges_time)
    
    print(f"Turn 2 acknowledges 'beginner': {acknowledges_beginner}")
    print(f"Turn 2 acknowledges '2 weeks': {acknowledges_time}")
    print(f"Turn 2 acknowledges 'portfolio': {acknowledges_portfolio}")
    print(f"Turn 2 asks experience again: {asks_experience_again}")
    print(f"Turn 2 asks time again: {asks_time_again}")
    
    # Success criteria: Turn 2 should acknowledge answers and NOT repeat questions
    if (acknowledges_beginner or acknowledges_time or acknowledges_portfolio):
        if not (asks_experience_again and asks_time_again):
            print("\n✅ SUCCESS: Agent progressed in conversation!")
            return True
    
    print("\n❌ FAILURE: Agent is repeating questions or not acknowledging answers")
    return False

async def test_three_turn_with_confirmation():
    """
    Test the full flow including confirmation step.
    """
    print("\n" + "=" * 80)
    print("Testing Three-Turn Conversation with Confirmation")
    print("=" * 80)
    
    history = []
    
    # Turn 1
    print("\n--- TURN 1 ---")
    turn1_goal = "I want Spring AI projects with intermediate difficulty"
    print(f"User: {turn1_goal}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response1 = await client.post(
            f"{BASE_URL}/run-agent",
            json={"goal": turn1_goal, "history": history}
        )
        data1 = response1.json()
        agent_response1 = data1.get("message", "")
        print(f"Agent: {agent_response1[:300]}...")
        
        history.append({"role": "user", "content": turn1_goal})
        history.append({"role": "agent", "content": agent_response1})
    
    # Turn 2
    print("\n--- TURN 2 ---")
    turn2_goal = "2 weeks and for portfolio"
    print(f"User: {turn2_goal}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response2 = await client.post(
            f"{BASE_URL}/run-agent",
            json={"goal": turn2_goal, "history": history}
        )
        data2 = response2.json()
        agent_response2 = data2.get("message", "")
        print(f"Agent: {agent_response2[:300]}...")
        
        history.append({"role": "user", "content": turn2_goal})
        history.append({"role": "agent", "content": agent_response2})
    
    # Turn 3: Confirmation
    print("\n--- TURN 3 ---")
    turn3_goal = "yes"
    print(f"User: {turn3_goal}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response3 = await client.post(
            f"{BASE_URL}/run-agent",
            json={"goal": turn3_goal, "history": history}
        )
        data3 = response3.json()
        agent_response3 = data3.get("message", "")
        response_type = data3.get("type", "")
        
        print(f"Agent response type: {response_type}")
        print(f"Agent: {agent_response3[:300]}...")
        
        if response_type == "results":
            print("\n✅ Agent returned project results!")
            return True
        else:
            print(f"\n⚠️  Agent response type: {response_type} (expected 'results')")
            return False

async def main():
    print("ProjectScout Multi-Turn Conversation Test Harness")
    print("=" * 80)
    
    # Test 1: Basic two-turn
    success1 = await test_two_turn_conversation()
    
    # Test 2: Full three-turn with confirmation
    success2 = await test_three_turn_with_confirmation()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Two-turn test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Three-turn test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed. Check server implementation.")

if __name__ == "__main__":
    asyncio.run(main())
