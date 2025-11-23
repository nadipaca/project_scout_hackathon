"""
Quick fix script to improve search keyword filtering in agent.py
"""

with open("src/agi_agents/project_scout/agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the search function keyword filtering
old_code = '''        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text'''

new_code = '''        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text
        
        # Clean up keywords: remove vague terms, handle commas
        unwanted = {'project', 'projects', 'idea', 'ideas', 'portfolio', 'beginner', 
                    'intermediate', 'advanced', 'learning', 'simple', 'ai', 'ml'}
        words = query.replace(',', ' ').split()
        filtered = [w.strip() for w in words if w.strip().lower() not in unwanted and len(w.strip()) > 2]
        query = ' '.join(filtered) if filtered else (input_data.domain or "python")
        print(f"DEBUG: Cleaned search query: {query}")'''

content_new = content.replace(old_code, new_code, 1)

if content != content_new:
    with open("src/agi_agents/project_scout/agent.py", "w", encoding="utf-8") as f:
        f.write(content_new)
    print("✓ Successfully patched agent.py - improved keyword filtering")
else:
    print("✗ Could not find target code to replace")
