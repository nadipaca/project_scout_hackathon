import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI
from arena import BaseAgent, AgentBrowser, AgentState
from .models import AgentInput, AgentOutput, Project, Roadmap, Phase, StackOption, Clarification

class ProjectScoutAgent(BaseAgent):
    """
    ProjectScout AI Agent: Helps developers find their next project.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str | None = "https://api.openai.com/v1",
        api_key: str | None = None,
    ):
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.github_token = os.getenv("GITHUB_TOKEN")

    async def step(self, browser: AgentBrowser, state: AgentState) -> AgentState:
        """
        Execute the ProjectScout workflow.
        """
        if state.finished:
            return state

        # Collect all user messages to understand context
        # In the demo script, state.goal is the initial input.
        # Subsequent user inputs might be in state.messages if we were in a chat loop,
        # but the harness/demo structure is a bit rigid.
        # For now, let's assume state.goal + any "user" messages in state.messages form the context.
        
        context = f"Initial Goal: {state.goal}\n"
        for msg in state.messages:
            if msg["role"] == "user":
                context += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                context += f"Agent: {msg['content']}\n"

        # 1. Analyze Request
        analysis = await self._analyze_request(context)
        
        if isinstance(analysis, Clarification):
            # Ask questions
            questions_text = "\n".join(analysis.questions)
            state.messages.append({"role": "assistant", "content": questions_text})
            # We are NOT finished, we wait for user input.
            # The demo script needs to handle this by checking if finished is False and last msg is assistant.
            return state
            
        # If we got AgentInput, we proceed
        agent_input = analysis
        
        # 2. Search GitHub
        repos = await self._search_github(agent_input)
        
        # 3. Classify and Select
        selected_projects = await self._classify_and_select(agent_input, repos)

        if not selected_projects:
            state.messages.append({"role": "assistant", "content": "No suitable projects found."})
            state.finished = True
            return state

        # 4. Generate Roadmap for the top pick
        top_project = selected_projects[0]
        roadmap = await self._generate_roadmap(agent_input, top_project)

        # 5. Construct Output
        output = AgentOutput(
            projects=selected_projects,
            plan_for_selected_project=roadmap,
            agent_trace=["Analyzed request", "Searched GitHub", "Generated Roadmap"]
        )

        state.messages.append({
            "role": "assistant", 
            "content": output.model_dump_json(indent=2)
        })
        
        state.finished = True
        return state

    async def _analyze_request(self, context: str) -> AgentInput | Clarification:
        prompt = f"""
        You are ProjectScout AI. Analyze the conversation to understand the user's project goal.
        
        Context:
        {context}
        
        Your task:
        1. Infer the following fields:
           - domain (e.g. AI, web)
           - tech_stack (e.g. Python, React)
           - difficulty (beginner/intermediate/advanced)
           - time_budget (weekend/1-2 weeks/3+ weeks)
           - project_type (repo/tutorial/idea)
           - recency_preference (latest/any)
           - goal_type (portfolio/learning/hackathon)
           
           # V2 Fields Inference:
           - cost_constraints (free-only/free-preferred/any)
           - data_source_preference (own-data/public-data/any)
           - deployment_target (local/web/mobile/cloud/any)
           - collaboration_mode (solo/team/any)
           - doc_emphasis (low/medium/high)
           - quality_focus (prototype/production)
           - focus_area (frontend/backend/balanced)
           - confidence_level (beginner-anxious/intermediate-confident/advanced)
           - has_existing_project (true/false)
           - existing_project_tech (string)
           
        2. Check for MISSING IMPORTANT INFO.
           - If difficulty is unknown, ask.
           - If recency matters (e.g. AI) and is unknown, ask.
           - If tech_stack is unknown for a general request, ask.
           - If time_budget is unknown, default to "1-2 weeks".
           - If project_type is unknown, default to "repo".
           
        3. ADVANCED ANALYSIS RULES (V2):
           
           A. Intent Splitting (Multi-Domain Detection):
              - If user mentions 2+ unrelated domains (AI + web3 + mobile), return Clarification asking which to focus on first.
              - Example: "I see AI, web3, and mobile. Which would you like to focus on first?"

           B. Constraint Conflict Detection:
              - Check if difficulty + time_budget are realistic.
              - If "advanced distributed systems" + "weekend" -> ask to adjust.
              - If "beginner" + "3+ weeks" -> suggest they could do intermediate.

           C. User Confidence Detection:
              - Words like "new", "stuck", "confused", "unsure" -> set confidence_level = "beginner-anxious"
              - Words like "confident", "experienced", "familiar" -> set confidence_level = "advanced"
              - Default -> "intermediate-confident"

           D. Ambiguity Handling:
              - If user says "anything", "you decide", "don't care" -> DO NOT ask questions.
              - Set reasonable defaults and proceed immediately.
              - Add note: "Using reasonable defaults since you're flexible"

           E. Existing Project Detection:
              - If user mentions "I have", "I already built", "extend my" -> set has_existing_project = true
              - Extract the tech from their description.

           F. Focus Area Detection:
              - Words like "UI", "design", "frontend", "interface" -> focus_area = "frontend"
              - Words like "API", "database", "backend", "server" -> focus_area = "backend"
              - If both or neither -> focus_area = "balanced"
           
           G. Clarification Rules:
              - Ask MAX 2 questions (merged if possible).
              - If you can infer a reasonable default (e.g. "simple" -> beginner), DO NOT ask.
              - If user says "any", pick a default (Intermediate, 1-2 weeks).
              - IMPORTANT: If the user provides a long, detailed prompt with multiple preferences, extract AS MUCH AS POSSIBLE and DO NOT ask for information they already gave.
           
        4. Output:
           - If you need clarification, return JSON with "questions" (list of strings) and "reasoning".
           - If you have enough info (or defaults), return JSON matching AgentInput schema.
           
        Schema for Clarification:
        {{
            "questions": ["Question 1", "Question 2"],
            "reasoning": "Why I need this info"
        }}
        
        Schema for AgentInput:
        {{
            "goal_text": "summary of goal",
            "difficulty": "beginner" | "intermediate" | "advanced",
            "time_budget": "weekend" | "1-2 weeks" | "3+ weeks",
            "preferred_stack": string | null,
            "search_keywords": "string - CRITICAL: Must be GitHub-searchable technical terms",
            "project_type": "repo" | "tutorial" | "idea",
            "recency_preference": "latest" | "any",
            "domain": string,
            "goal_type": string,
            "cost_constraints": "free-only" | "free-preferred" | "any",
            "data_source_preference": "own-data" | "public-data" | "any",
            "deployment_target": "local" | "web" | "mobile" | "cloud" | "any",
            "collaboration_mode": "solo" | "team" | "any",
            "doc_emphasis": "low" | "medium" | "high",
            "quality_focus": "prototype" | "production",
            "focus_area": "frontend" | "backend" | "balanced",
            "confidence_level": "beginner-anxious" | "intermediate-confident" | "advanced",
            "has_existing_project": boolean,
            "existing_project_tech": string
        }}
        
        CRITICAL EXAMPLES FOR search_keywords (STUDY THESE):
        
        BAD (too vague, won't find repos):
        ❌ "AI project ideas"
        ❌ "portfolio projects"  
        ❌ "NLP, recommender systems, computer vision"
        ❌ "machine learning for beginners"
        
        GOOD (specific, matches GitHub):
        ✓ "python transformers huggingface"
        ✓ "recommendation-engine collaborative-filtering"
        ✓ "opencv computer-vision python"
        ✓ "scikit-learn classification"
        ✓ "langchain rag chatbot"
        ✓ "react flask full-stack"
        
        RULES FOR search_keywords:
        1. Use actual technology names (transformers, opencv, scikit-learn)
        2. Use hyphenated project types (recommendation-engine, chatbot, image-classifier)
        3. Combine tech + domain (python nlp, react dashboard, pytorch vision)
        4. NEVER use: project, ideas, portfolio, learning, beginner, intermediate, advanced
        5. Think: "What would this repo be tagged/named on GitHub?"
        6. CRITICAL: When user wants DIVERSE project types (NLP, CV, web apps):
           - Generate COMMA-SEPARATED query groups: "python nlp transformers, opencv computer-vision, react flask"
           - NOT space-separated mashups like "nlp opencv react"
           - This ensures we search for each domain separately!
        
        DOMAIN -> KEYWORD MAPPING:
        - "AI/ML" -> "python machine-learning scikit-learn" or "pytorch tensorflow"
        - "NLP" -> "python nlp transformers spacy"
        - "Computer Vision" -> "opencv computer-vision pytorch"
        - "Recommender" -> "recommendation-engine collaborative-filtering"
        - "Web + AI" -> "flask fastapi react chatbot"
        - "Data Science" -> "python pandas jupyter data-analysis"
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        if "questions" in data:
            return Clarification(**data)
        else:
            return AgentInput(**data)

    async def _search_github(self, input_data: AgentInput) -> List[Dict]:
        """
        Search GitHub for repositories.
        """
        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text
        
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
        
        # Apply mapping if query contains conceptual terms
        query_lower = query.lower()
        for concept, technical in keyword_map.items():
            if concept in query_lower:
                query = query.replace(concept, technical)
                query = query.replace(concept.title(), technical)
                query = query.replace(concept.upper(), technical)
        
        # Clean up: remove vague non-technical terms
        remove_terms = {'project', 'projects', 'idea', 'ideas', 'portfolio', 
                       'beginner', 'intermediate', 'advanced', 'learning', 'simple', 'ai', 'ml'}
        
        # Split by commas to handle diverse queries
        # E.g., "python nlp transformers, opencv pytorch, react flask" -> search ALL separately
        alternatives = [q.strip() for q in input_data.search_keywords.split(',')] if input_data.search_keywords else [input_data.preferred_stack or input_data.goal_text]
        
        # Collect results from ALL alternatives for true diversity
        all_repos = []
        
        async with httpx.AsyncClient() as client:
            for alt_query in alternatives:
                # Clean this specific alternative
                words = alt_query.split()
                filtered_words = [w for w in words if w.lower() not in remove_terms and len(w) > 2]
                
                if not filtered_words:
                    continue  # Skip empty queries
                
                query = ' '.join(filtered_words)
                print(f"DEBUG: Trying query: {query}")
                
                params = {
                    "q": f"{query} created:>2023-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5  # Fetch fewer per domain to get variety
                }
                
                headers = {"Accept": "application/vnd.github.v3+json"}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"

                try:
                    resp = await client.get("https://api.github.com/search/repositories", params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        
                        if items:
                            print(f"DEBUG: Found {len(items)} repositories for query: {query}")
                            # Take top 2 from each domain for diversity
                            all_repos.extend(items[:2])
                except Exception as e:
                    print(f"GitHub search failed for '{query}': {e}")
                    continue  # Try next alternative

            # If we found repos across domains, fetch READMEs
            if all_repos:
                # Limit to top 10 overall
                top_items = all_repos[:10]
                tasks = [self._fetch_readme(client, item["owner"]["login"], item["name"]) for item in top_items]
                readmes = await asyncio.gather(*tasks)
                
                detailed_repos = []
                for item, readme in zip(top_items, readmes):
                    item["readme_content"] = readme
                    detailed_repos.append(item)
                
                return detailed_repos
            
            # No results from any alternative
            print("DEBUG: No results found for any alternative")
            return []

    async def _fetch_readme(self, client: httpx.AsyncClient, owner: str, repo: str) -> str:
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            headers = {"Accept": "application/vnd.github.v3.raw"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text[:2000] # Truncate to avoid context limit issues
            return ""
        except Exception:
            return ""

    async def _classify_and_select(self, input_data: AgentInput, repos: List[Dict]) -> List[Project]:
        if not repos:
            return []

        # Prepare repo info for LLM
        repo_summaries = []
        for r in repos:
            repo_summaries.append({
                "name": r["name"],
                "full_name": r["full_name"],
                "html_url": r["html_url"],
                "description": r["description"],
                "stars": r["stargazers_count"],
                "readme_snippet": r.get("readme_content", "")[:2000]
            })

        prompt = f"""
        You are an expert tech career coach. 
        User Goal: {input_data.goal_text}
        Difficulty: {input_data.difficulty}
        Time Budget: {input_data.time_budget}
        Preferred Stack: {input_data.preferred_stack}
        
        # V2 Constraints
        Cost: {input_data.cost_constraints}
        Deployment: {input_data.deployment_target}
        Quality Focus: {input_data.quality_focus}

        Here are some candidate GitHub repositories:
        {json.dumps(repo_summaries, indent=2)}

        Task:
        1. Analyze each repo.
        2. Select the top 3-5 that best match the user's goal and constraints.
        3. For each, determine difficulty, estimated time, and stack tags.
        4. Explain why it's a match.

        CLASSIFICATION REQUIREMENTS (V2):

        1. Diversity Guarantee (STRICT):
           - Unless user specifically asked for ONE narrow thing (e.g. "only chatbots"), you MUST select diverse projects.
           - Mix domains: NLP, CV, Web, Data.
           - Mix types: Libraries, Apps, Tutorials.
           - AVOID selecting 3 projects that are all "Python NLP libraries".
           - Explain: "I chose varied projects (NLP, CV, Web) so you can pick what excites you."

        2. Frontend/Full-stack Check:
           - Check if repo has a frontend (React, Vue, HTML/JS).
           - If backend-only, NOTE THIS in why_match: "Backend-only repo (great for adding your own React UI)."
           - If full-stack, highlight it: "Includes full React frontend."

        3. Template Detection:
           - If project matches common patterns (SaaS dashboard, RAG chatbot, etc.)
           - Mention it in why_match: "This is a great [RAG chatbot] template you can adapt"

        4. Cost Constraints:
           - If user wants free-only, prefer projects that don't require paid APIs.
           - Note in why_match if a project uses free/open-source tools.

        5. Quality Indicators:
           - Check for good documentation, tests, CI/CD.
           - Prioritize if user wants production-quality or portfolio showcase.

        Return a JSON object with a key "projects" containing a list of objects matching this schema:
        {{
            "name": "string",
            "github_url": "string",
            "summary": "string",
            "difficulty": "beginner" | "intermediate" | "advanced",
            "estimated_time": "weekend" | "1-2 weeks" | "3+ weeks",
            "stack_tags": ["string"],
            "why_match": "string"
        }}
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        try:
            data = json.loads(response.choices[0].message.content)
            projects = [Project(**p) for p in data.get("projects", [])]
            return projects
        except Exception as e:
            print(f"Error parsing classification: {e}")
            return []

    async def _generate_roadmap(self, input_data: AgentInput, project: Project) -> Roadmap:
        prompt = f"""
        Create a detailed implementation roadmap for this project:
        Project: {project.name}
        URL: {project.github_url}
        Summary: {project.summary}
        
        User Constraints:
        Time: {input_data.time_budget}
        Stack: {input_data.preferred_stack}
        
        # V2 Context
        Doc Emphasis: {input_data.doc_emphasis}
        Quality Focus: {input_data.quality_focus}
        Confidence: {input_data.confidence_level}

        Generate:
        1. 3-4 phases.
        2. Tasks per phase.
        3. 2-3 specific stack implementation options.
        
        ROADMAP REQUIREMENTS (V2):

        1. Checkpoints (Rule 18):
           - For each phase, add a checkpoint with:
             * What should be working at this point
             * A "share tip" for LinkedIn/portfolio
           - Example: "After Phase 1: You'll have the API working. Share: 'Built my first ML API'"

        2. Upgrade Path (Rule 16):
           - Add 2-3 CONCRETE suggestions for what to build next.
           - Be ambitious: "Add multi-modal support", "Scale to 10k users", "Add real-time collaboration".

        3. Documentation Tasks (Rule 10):
           - If doc_emphasis = high or goal_type = "portfolio":
             * Add tasks: "Create Architecture Diagram (Mermaid/Excalidraw)", "Record 30s Demo Video/GIF", "Write 'Lessons Learned' blog post".

        4. Deployment Strategy (New):
           - Suggest a FREE/CHEAP way to deploy this specific stack.
           - Example: "Frontend: Vercel/Netlify (Free). Backend: Render/Railway (Free Tier). DB: Supabase (Free)."
           - If constraints are tight, suggest: "Run locally with Ollama/LocalAI to avoid API costs."

        5. Testing Tasks (Rule 11):
           - If quality_focus = "production":
             * Add tasks for "Unit tests", "Integration tests", "CI/CD setup"

        6. Scope Sanity Check (Rule 13):
           - Before finalizing, check if phases fit time_budget.
           - If not, add scope_note: "This is ambitious for [timeframe]. Consider these as stretch goals."

        7. Safety Nudge (Rule 19):
           - If project involves scraping, security tools, personal data:
             * Add a note: "Reminder: Follow terms of service and local laws"

        Return JSON matching this schema:
        {{
            "project_name": "{project.name}",
            "github_url": "{project.github_url}",
            "phases": [
                {{ "name": "string", "duration": "string", "goals": "string", "tasks": ["string"] }}
            ],
            "stack_options": [
                {{ "name": "string", "description": "string" }}
            ],
            "upgrade_path": ["string"],
            "checkpoints": [
                {{ "phase": "string", "milestone": "string", "share_tip": "string" }}
            ],
            "scope_note": "string | null",
            "deployment_strategy": "string | null"
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        return Roadmap(**data)
