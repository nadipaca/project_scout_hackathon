from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field

class AgentInput(BaseModel):
    goal_text: str
    difficulty: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    time_budget: Optional[Literal["weekend", "1-2 weeks", "3+ weeks"]] = None
    preferred_stack: Optional[str] = None
    search_keywords: Optional[str] = None
    project_type: Optional[Literal["repo", "tutorial", "idea", "skill-focused challenge"]] = None
    recency_preference: Optional[Literal["latest", "any"]] = None
    domain: Optional[str] = None
    goal_type: Optional[str] = None # portfolio, learning, etc.
    
    # V2 Advanced Fields
    cost_constraints: Optional[Literal["free-only", "free-preferred", "any"]] = None
    data_source_preference: Optional[Literal["own-data", "public-data", "any"]] = None
    deployment_target: Optional[Literal["local", "web", "mobile", "cloud", "any"]] = None
    collaboration_mode: Optional[Literal["solo", "team", "any"]] = None
    doc_emphasis: Optional[Literal["low", "medium", "high"]] = None
    quality_focus: Optional[Literal["prototype", "production"]] = None
    focus_area: Optional[Literal["frontend", "backend", "balanced"]] = None
    confidence_level: Optional[Literal["beginner-anxious", "intermediate-confident", "advanced"]] = None
    has_existing_project: Optional[bool] = None
    existing_project_tech: Optional[str] = None
    
    # Advanced Rule Tracking Fields (for 11 new rules)
    motivation_state: Optional[Literal["uninspired", "overwhelmed", "failed-projects", "normal"]] = "normal"
    clarification_count: Optional[int] = 0
    skill_bridge_needed: Optional[bool] = False
    locale_preference: Optional[str] = None
    privacy_mode: Optional[bool] = False
    upgrade_mode: Optional[bool] = False
    upgrade_project_info: Optional[str] = None

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
    
    # V2 Advanced Fields
    upgrade_path: Optional[List[str]] = None
    checkpoints: Optional[List[Dict[str, str]]] = None
    scope_note: Optional[str] = None
    deployment_strategy: Optional[str] = None  # New: Free/Cheap deployment advice

class AgentOutput(BaseModel):
    projects: List[Project]
    plan_for_selected_project: Roadmap
    agent_trace: List[str]
