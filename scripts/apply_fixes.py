"""
Comprehensive fix for ProjectScout agent search keywords
Applies both prompt improvement and keyword mapping
"""

def apply_prompt_fix():
    """Fix the _analyze_request prompt with better examples"""
    with open("src/agi_agents/project_scout/agent.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the schema section and add detailed keyword instructions
    old_schema = '''            \"search_keywords\": \"string\",'''
    
    new_schema = '''            \"search_keywords\": \"string - CRITICAL: Must be GitHub-searchable technical terms\",'''
    
    content = content.replace(old_schema, new_schema, 1)
    
    # Add examples section after the schema
    old_closing = '''        }}
        \"\"\"'''
    
    new_closing = '''        }}
        
        CRITICAL EXAMPLES FOR search_keywords (STUDY THESE):
        
        BAD (too vague, won't find repos):
        ❌ \"AI project ideas\"
        ❌ \"portfolio projects\"  
        ❌ \"NLP, recommender systems, computer vision\"
        ❌ \"machine learning for beginners\"
        
        GOOD (specific, matches GitHub):
        ✓ \"python transformers huggingface\"
        ✓ \"recommendation-engine collaborative-filtering\"
        ✓ \"opencv computer-vision python\"
        ✓ \"scikit-learn classification\"
        ✓ \"langchain rag chatbot\"
        ✓ \"react flask full-stack\"
        
        RULES FOR search_keywords:
        1. Use actual technology names (transformers, opencv, scikit-learn)
        2. Use hyphenated project types (recommendation-engine, chatbot, image-classifier)
        3. Combine tech + domain (python nlp, react dashboard, pytorch vision)
        4. NEVER use: project, ideas, portfolio, learning, beginner, intermediate, advanced
        5. Think: "What would this repo be tagged/named on GitHub?"
        
        DOMAIN → KEYWORD MAPPING:
        - "AI/ML" → "python machine-learning scikit-learn" or "pytorch tensorflow"
        - "NLP" → "python nlp transformers spacy"
        - "Computer Vision" → "opencv computer-vision pytorch"
        - "Recommender" → "recommendation-engine collaborative-filtering"
        - "Web + AI" → "flask fastapi react chatbot"
        - "Data Science" → "python pandas jupyter data-analysis"
        \"\"\"'''
    
    content = content.replace(old_closing, new_closing, 1)
    
    with open("src/agi_agents/project_scout/agent.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✓ Applied prompt improvements with examples")


def apply_mapping_layer():
    """Add keyword mapping safety net in _search_github"""
    with open("src/agi_agents/project_scout/agent.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    old_search_start = '''        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text
        
        # Construct GitHub API query'''
    
    new_search_start = '''        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text
        
        # Safety net: Map conceptual terms to technical GitHub search terms
        keyword_map = {
            'nlp': 'python nlp transformers spacy',
            'natural language processing': 'python nlp transformers',
            'recommender': 'recommendation-engine collaborative-filtering',
            'recommendation': 'recommendation-engine',
            'computer vision': 'opencv computer-vision pytorch',
            'cv': 'opencv pytorch vision',
            'chatbot': 'chatbot langchain rasa',
            'machine learning': 'python machine-learning scikit-learn',
            'deep learning': 'pytorch tensorflow keras',
            'data science': 'python pandas jupyter data-analysis',
            'web app': 'react flask django',
            'full stack': 'react nodejs mongodb',
        }
        
        # Apply mapping if query is too conceptual
        query_lower = query.lower()
        for concept, technical in keyword_map.items():
            if concept in query_lower:
                query = query.replace(concept, technical)
                query = query.replace(concept.title(), technical)
        
        # Clean up: remove vague terms
        remove_terms = ['project', 'projects', 'idea', 'ideas', 'portfolio', 
                       'beginner', 'intermediate', 'advanced', 'learning', 'simple']
        words = query.split()
        filtered = [w for w in words if w.lower() not in remove_terms and len(w) > 2]
        query = ' '.join(filtered) if filtered else (input_data.domain or "python")
        
        print(f"DEBUG: Original keywords: {input_data.search_keywords}")
        print(f"DEBUG: Mapped query: {query}")
        
        # Construct GitHub API query'''
    
    content = content.replace(old_search_start, new_search_start, 1)
    
    with open("src/agi_agents/project_scout/agent.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✓ Applied keyword mapping safety net")


if __name__ == "__main__":
    apply_prompt_fix()
    apply_mapping_layer()
    print("\n✅ All fixes applied successfully!")
    print("The agent now has:")
    print("  1. Improved prompt with explicit examples for LLM")
    print("  2. Keyword mapping layer as safety net")
