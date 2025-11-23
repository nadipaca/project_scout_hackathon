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
           
        2. Check for MISSING IMPORTANT INFO.
           - If difficulty is unknown, ask.
           - If project_type is unknown, ask.
           - If recency matters (e.g. AI) and is unknown, ask.
           - If time_budget is unknown for a concrete plan, ask.
           - If tech_stack is unknown for a general request, ask.
           
        3. Rules for Clarification:
           - Ask MAX 2 questions.
           - If you can infer a reasonable default (e.g. "simple" -> beginner), DO NOT ask.
           - If user says "any", pick a default (Intermediate, 1-2 weeks).
           
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
            "search_keywords": "string",
            "project_type": "repo" | "tutorial" | "idea",
            "recency_preference": "latest" | "any",
            "domain": string,
            "goal_type": string
        }}
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
        
        # Construct GitHub API query
        # We want recent, non-trivial repos.
        # created:>2023-01-01
        
        params = {
            "q": f"{query} created:>2023-01-01",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get("https://api.github.com/search/repositories", params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])
                
                # Fetch READMEs for the top 3 to save time/tokens
                detailed_repos = []
                for item in items[:3]:
                    readme = await self._fetch_readme(client, item["owner"]["login"], item["name"])
                    item["readme_content"] = readme
                    detailed_repos.append(item)
                
                return detailed_repos
            except Exception as e:
                print(f"GitHub search failed: {e}")
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

        Here are some candidate GitHub repositories:
        {json.dumps(repo_summaries, indent=2)}

        Task:
        1. Analyze each repo.
        2. Select the top 3-5 that best match the user's goal and constraints.
        3. For each, determine difficulty, estimated time, and stack tags.
        4. Explain why it's a match.

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

        Generate:
        1. 3-4 phases.
        2. Tasks per phase.
        3. 2-3 specific stack implementation options (e.g. "Next.js + Supabase").

        Return JSON matching this schema:
        {{
            "project_name": "{project.name}",
            "github_url": "{project.github_url}",
            "phases": [
                {{ "name": "string", "duration": "string", "goals": "string", "tasks": ["string"] }}
            ],
            "stack_options": [
                {{ "name": "string", "description": "string" }}
            ]
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        return Roadmap(**data)
