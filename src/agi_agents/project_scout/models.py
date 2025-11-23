from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class AgentInput(BaseModel):
    goal_text: str
    difficulty: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    time_budget: Optional[Literal["weekend", "1-2 weeks", "3+ weeks"]] = None
    preferred_stack: Optional[str] = None
    search_keywords: Optional[str] = None
    project_type: Optional[Literal["repo", "tutorial", "idea"]] = None
    recency_preference: Optional[Literal["latest", "any"]] = None
    domain: Optional[str] = None
    goal_type: Optional[str] = None # portfolio, learning, etc.

class Clarification(BaseModel):
    questions: List[str]
    reasoning: str

class Project(BaseModel):
    name: str
    github_url: str
    summary: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_time: Literal["weekend", "1-2 weeks", "3+ weeks"]
    stack_tags: List[str]
    why_match: str

class Phase(BaseModel):
    name: str
    duration: str
    goals: str
    tasks: List[str]

class StackOption(BaseModel):
    name: str
    description: str

class Roadmap(BaseModel):
    project_name: str
    github_url: str
    phases: List[Phase]
    stack_options: List[StackOption]

class AgentOutput(BaseModel):
    projects: List[Project]
    plan_for_selected_project: Roadmap
    agent_trace: List[str]
