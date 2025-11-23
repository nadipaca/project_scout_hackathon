import asyncio
import httpx

async def test_github_api():
    queries = [
        "AI projects with Python and LangChain stars:>100 created:>2022-01-01",
        "Python LangChain stars:>100 created:>2022-01-01",
        "LangChain stars:>50",
        "machine learning python stars:>100",
    ]
    
    for query in queries:
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"\nQuery: {query}")
                print("=" * 80)
                resp = await client.get("https://api.github.com/search/repositories", params=params, headers=headers)
                print(f"Status: {resp.status_code}")
                data = resp.json()
                print(f"Total count: {data.get('total_count', 0)}")
                
                items = data.get("items", [])
                for item in items[: 3]:
                    print(f"  - {item['full_name']}: {item['stargazers_count']} stars")
                    
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_github_api())
