import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI
from arena import BaseAgent, AgentBrowser, AgentState
from .models import AgentInput, AgentOutput, Project, Roadmap, Phase, StackOption, Clarification
from . import advanced_rules

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
        
        # Advanced rules tracking
        self.clarification_count = 0
        self.recent_responses = []

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
            self.clarification_count += 1  # Track for ambiguity cooldown
            questions_text = "\n".join(analysis.questions)
            state.messages.append({"role": "assistant", "content": questions_text})
            # We are NOT finished, we wait for user input.
            # The demo script needs to handle this by checking if finished is False and last msg is assistant.
            return state
            
        # If we got AgentInput, we proceed
        agent_input = analysis
        
        # Reset clarification count on successful analysis
        self.clarification_count = 0
        
        # Track user response for ambiguity detection
        if state.messages:
            last_user_msg = next((msg["content"] for msg in reversed(state.messages) if msg["role"] == "user"), "")
            if last_user_msg:
                self.recent_responses.append(last_user_msg)
                # Keep only last 5 responses
                self.recent_responses = self.recent_responses[-5:]
        
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
        """
        Analyze user request with advanced rules integration.
        
        This method now includes 11 advanced rules:
        1. Motivation & Learning Style Detection
        2. Constraint Conflict Detection
        3. Ambiguity Cooldown
        4. Persona-Based Scaffolding
        5. Inspiration-Driven Discovery
        6. Context-Aware Ideation
        7. Reuse/Upgrade Existing Project
        8. Locale/Market Awareness
        9. Privacy Sensitivity
        10. Quality/Showcase/Polish Emphasis
        11. Upgrade Path & Portfolio Story
        """
        
        # ===== ADVANCED RULES DETECTION (Pre-LLM) =====
        
        # Rule 1: Motivation & Learning Style Detection
        motivation_state = advanced_rules.detect_motivation_state(context)
        adaptive_tone = advanced_rules.get_adaptive_tone(motivation_state)
        
        # Rule 3: Ambiguity Cooldown
        apply_cooldown = advanced_rules.should_apply_ambiguity_cooldown(
            self.clarification_count, 
            self.recent_responses
        )
        
        # If cooldown applies, use sensible defaults
        if apply_cooldown:
            defaults = advanced_rules.generate_sensible_defaults()
            return AgentInput(
                goal_text=context,
                difficulty=defaults["difficulty"],
                time_budget=defaults["time_budget"],
                project_type=defaults["project_type"],
                recency_preference=defaults["recency_preference"],
                cost_constraints=defaults["cost_constraints"],
                deployment_target=defaults["deployment_target"],
                collaboration_mode=defaults["collaboration_mode"],
                doc_emphasis=defaults["doc_emphasis"],
                quality_focus=defaults["quality_focus"],
                focus_area=defaults["focus_area"],
                confidence_level=defaults["confidence_level"],
                motivation_state=motivation_state,
                clarification_count=self.clarification_count,
                search_keywords="python web"  # Basic default
            )
        
        # Rule 4: Persona-Based Scaffolding
        skill_bridge = advanced_rules.detect_skill_bridge_opportunity(context)
        
        # Rule 5: Inspiration-Driven Discovery
        needs_inspiration = advanced_rules.detect_inspiration_need(context)
        
        # Rule 6: Context-Aware Ideation
        wants_trending = advanced_rules.detect_trending_request(context)
        
        # Rule 7: Reuse/Upgrade Existing Project
        upgrade_info = advanced_rules.detect_upgrade_intent(context)
        
        # Rule 8: Locale/Market Awareness
        locale = advanced_rules.detect_locale_or_market(context)
        
        # Rule 9: Privacy Sensitivity
        privacy_mode = advanced_rules.detect_privacy_concerns(context)
        
        # Rule 10: Quality/Showcase/Polish Emphasis
        quality_analysis = advanced_rules.analyze_quality_emphasis(context)
        
        # Build context for LLM with advanced rules insights
        advanced_context = f"""
        
        === ADVANCED RULES DETECTION ===
        Motivation State: {motivation_state}
        {f"Adaptive Tone: {adaptive_tone}" if adaptive_tone else ""}
        {f"Skill Bridge Opportunity: {skill_bridge['suggestion']}" if skill_bridge else ""}
        {f"Inspiration Needed: User needs open-ended discovery questions" if needs_inspiration else ""}
        {f"Trending Request: Focus on latest/hot technologies" if wants_trending else ""}
        {f"Upgrade Mode: {upgrade_info['suggestion']}" if upgrade_info else ""}
        {f"Locale/Market: {locale}" if locale else ""}
        {f"Privacy Mode: Suggest local-only, no cloud APIs" if privacy_mode else ""}
        Quality Focus: {quality_analysis['quality_focus']}
        Doc Emphasis: {quality_analysis['doc_emphasis']}
        
        INSTRUCTIONS BASED ON ADVANCED RULES:
        {f"- Use encouraging, supportive tone. Suggest smaller, achievable projects." if motivation_state in ["overwhelmed", "failed-projects"] else ""}
        {f"- Ask open-ended questions about interests rather than technical details." if needs_inspiration else ""}
        {f"- Generate UPGRADE ROADMAP for existing {upgrade_info['existing_tech']} project, NOT new project suggestions." if upgrade_info else ""}
        {f"- Suggest LOCAL-FIRST solutions (Ollama, LocalAI, local models). Avoid cloud APIs." if privacy_mode else ""}
        {f"- Adapt suggestions for {locale} market (localization, regional preferences)." if locale else ""}
        {f"- Emphasize production-ready features: tests, CI/CD, documentation." if quality_analysis['quality_focus'] == 'production' else ""}
        """
        
        prompt = f"""
        You are ProjectScout AI. Analyze the conversation to understand the user's project goal.
        
        Context:
        {context}
        {advanced_context}
        
        Your task:
        1. Infer the following fields:
           - domain (e.g. AI, web, mobile, backend, data science)
           - tech_stack (infer from user's request - could be any language/framework combination)
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
            "existing_project_tech": string,
            "motivation_state": "uninspired" | "overwhelmed" | "failed-projects" | "normal",
            "skill_bridge_needed": boolean,
            "locale_preference": string | null,
            "privacy_mode": boolean,
            "upgrade_mode": boolean,
            "upgrade_project_info": string | null
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
        ✓ "[frontend-framework] [backend-framework] full-stack" (use actual user-preferred technologies)
        
        RULES FOR search_keywords:
        1. Use actual technology names (transformers, opencv, scikit-learn)
        2. Use hyphenated project types (recommendation-engine, chatbot, image-classifier)
        3. Combine tech + domain (python nlp, [user-framework] dashboard, pytorch vision)
        4. NEVER use: project, ideas, portfolio, learning, beginner, intermediate, advanced
        5. Think: "What would this repo be tagged/named on GitHub?"
        6. CRITICAL: When user wants DIVERSE project types (NLP, CV, web apps):
           - Generate COMMA-SEPARATED query groups: "python nlp transformers, opencv computer-vision, [user-stack] web"
           - NOT space-separated mashups like "nlp opencv react"
           - This ensures we search for each domain separately!
        
        DOMAIN -> KEYWORD MAPPING (Use user's preferred stack when available):
        - "AI/ML" -> Infer from user's tech stack:
          * Python: "python machine-learning", "pytorch", "tensorflow", "scikit-learn"
          * Java/Spring: "spring-ai", "langchain4j java", "java machine-learning"
          * JavaScript: "tensorflow-js", "brain-js", "ml5-js"
          * General: If user mentions specific framework, USE IT (e.g., "Spring AI" -> "spring-ai")
        - "NLP" -> Combine with user's language preference (e.g., "python nlp transformers", "java nlp", "nodejs nlp")
        - "Computer Vision" -> Use user's tech stack (e.g., "opencv computer-vision", "pytorch vision", "tensorflow vision")
        - "Recommender" -> "recommendation-engine collaborative-filtering" + user's stack
        - "Web + AI" -> Use user's preferred frontend/backend (e.g., "[backend] [frontend] chatbot")
        - "Data Science" -> Combine with user's language (e.g., "python pandas", "R data-analysis", "julia statistics")
        - For any domain: ALWAYS incorporate the user's preferred_stack if specified
        
        CRITICAL: If user mentions a specific framework (Spring AI, LangChain4j, etc.), preserve it exactly in search_keywords!
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
            agent_input = AgentInput(**data)
            
            # Rule 2: Constraint Conflict Detection (Post-LLM)
            # Check if the inferred difficulty/time/domain combination is realistic
            conflict_message = advanced_rules.detect_constraint_conflicts(
                agent_input.difficulty,
                agent_input.time_budget,
                agent_input.domain
            )
            
            # If there's a conflict, return a clarification with rescoping options
            if conflict_message:
                return Clarification(
                    questions=[conflict_message],
                    reasoning="Detected potential constraint conflict between difficulty, time, and scope."
                )
            
            return agent_input

    async def _search_github(self, input_data: AgentInput) -> List[Dict]:
        """
        Search GitHub for repositories.
        """
        query = input_data.search_keywords or input_data.preferred_stack or input_data.goal_text
        
        # Safety net: Map conceptual terms to technical GitHub search terms
        # Incorporate user's preferred_stack when available
        user_stack = (input_data.preferred_stack or "").lower()
        
        keyword_map = {
            'nlp': f'{user_stack} nlp' if user_stack else 'nlp transformers',
            'natural language processing': f'{user_stack} nlp' if user_stack else 'nlp transformers',
            'recommender': 'recommendation-engine collaborative-filtering',
            'recommendation': 'recommendation-engine',
            'computer vision': f'{user_stack} computer-vision' if user_stack else 'computer-vision opencv',
            'cv': f'{user_stack} vision' if user_stack else 'opencv vision',
            'chatbot': f'{user_stack} chatbot' if user_stack else 'chatbot',
            'machine learning': f'{user_stack} machine-learning' if user_stack else 'machine-learning',
            'deep learning': f'{user_stack} deep-learning' if user_stack else 'deep-learning',
            'data science': f'{user_stack} data-analysis' if user_stack else 'data-analysis',
            'web app': f'{user_stack} web' if user_stack else 'web application',
            'full stack': f'{user_stack} full-stack' if user_stack else 'full-stack',
            # Java/Spring AI frameworks
            'spring ai': 'spring-ai',
            'langchain4j': 'langchain4j java',
            'java ai': 'java machine-learning',
        }
        
        # Apply mapping if query contains conceptual terms
        query_lower = query.lower()
        for concept, technical in keyword_map.items():
            if concept in query_lower:
                query = query.replace(concept, technical)
                query = query.replace(concept.title(), technical)
                query = query.replace(concept.upper(), technical)
        
        # Split by commas to handle diverse queries
        # E.g., "python nlp transformers, opencv pytorch, react flask" -> search ALL separately
        alternatives = [q.strip() for q in input_data.search_keywords.split(',')] if input_data.search_keywords else [input_data.preferred_stack or input_data.goal_text]
        
        # Collect results from ALL alternatives for true diversity
        all_repos = []
        
        async with httpx.AsyncClient() as client:
            for alt_query in alternatives:
                # Clean this specific alternative
                # IMPORTANT: Preserve framework-specific terms like "spring-ai", "Spring AI"
                # Only remove standalone vague terms
                
                # First, check if this is a hyphenated framework term (e.g., "spring-ai")
                if '-ai' in alt_query.lower() or '-ml' in alt_query.lower():
                    # Don't filter out words from hyphenated framework names
                    query = alt_query
                else:
                    # Remove vague non-technical standalone terms
                    remove_terms = {'project', 'projects', 'idea', 'ideas', 'portfolio', 
                                   'beginner', 'intermediate', 'advanced', 'learning', 'simple'}
                    
                    # Special handling: only remove 'ai' or 'ml' if they're standalone
                    # Don't remove if part of "Spring AI", "Java AI", etc.
                    words = alt_query.split()
                    filtered_words = []
                    for i, w in enumerate(words):
                        w_lower = w.lower()
                        # Remove if it's a vague term
                        if w_lower in remove_terms and len(w) > 2:
                            continue
                        # Remove 'ai' or 'ml' ONLY if standalone (not preceded by a framework name)
                        if w_lower in {'ai', 'ml'}:
                            # Check if previous word is a framework/language
                            if i > 0 and words[i-1].lower() in {'spring', 'java', 'python', 'javascript', 'nodejs', 'react', 'angular', 'vue'}:
                                filtered_words.append(w)  # Keep it
                            else:
                                continue  # Remove standalone 'ai'/'ml'
                        else:
                            if len(w) > 2:
                                filtered_words.append(w)
                    
                    query = ' '.join(filtered_words)
                    
                    if not filtered_words:
                        continue  # Skip empty queries
                
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
           - Check if repo has a frontend (any framework: React, Vue, Angular, Svelte, vanilla HTML/JS, etc.).
           - If backend-only, NOTE THIS in why_match: "Backend-only repo (great for adding your own frontend UI)."
           - If full-stack, highlight it: "Includes full [framework name] frontend." (specify actual framework found)

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
