"""
Simple diagnostic test to see actual agent responses.
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def simple_test():
    print("=" * 80)
    print("SIMPLE DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Turn 1
    print("\n--- TURN 1 ---")
    print("Sending: 'I want python projects with pytorch'")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/run-agent",
                json={"goal": "I want python projects with pytorch", "history": []}
            )
            
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response type: {data.get('type')}")
            print(f"Message: {data.get('message')}")
            print()
            
            # Save for Turn 2
            turn1_response = data.get("message", "")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Turn 2
    print("\n--- TURN 2 ---")
    print("Sending: 'beginner and 2 weeks, portfolio'")
    print(f"With history of {2} messages")
    
    history = [
        {"role": "user", "content": "I want python projects with pytorch"},
        {"role": "agent", "content": turn1_response}
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/run-agent",
                json={"goal": "beginner and 2 weeks, portfolio", "history": history}
            )
            
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response type: {data.get('type')}")
            print(f"Message: {data.get('message')}")
            print()
            
            # Compare
            turn2_response = data.get("message", "")
            
            print("\n--- COMPARISON ---")
            print(f"Turn 1 length: {len(turn1_response)}")
            print(f"Turn 2 length: {len(turn2_response)}")
            print(f"Responses identical: {turn1_response == turn2_response}")
            
            if turn1_response != turn2_response:
                print("✅ Responses are different!")
            else:
                print("❌ Responses are identical (BUG!)")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
