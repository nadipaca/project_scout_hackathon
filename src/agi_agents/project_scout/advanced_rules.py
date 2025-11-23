"""
Advanced Rules Module for ProjectScout Agent

This module contains detection and handling functions for 11 advanced rules:
1. Motivation & Learning Style Detection
2. Constraint Conflict Detection & Rescoping
3. Ambiguity Cooldown
4. Persona-Based Scaffolding
5. Inspiration-Driven Discovery
6. Context-Aware Ideation
7. Reuse/Upgrade Existing Project
8. Locale/Market Awareness
9. Privacy Sensitivity
10. Quality/Showcase/Polish Emphasis
11. Upgrade Path & Portfolio Story

All functions are designed to be called from the main agent without modifying existing logic.
"""

import re
from typing import Optional, Dict, List, Literal


# Rule 1: Motivation & Learning Style Detection
def detect_motivation_state(context: str) -> Literal["uninspired", "overwhelmed", "failed-projects", "normal"]:
    """
    Detect user's motivation state from context.
    
    Args:
        context: Full conversation context
        
    Returns:
        One of: "uninspired", "overwhelmed", "failed-projects", "normal"
    """
    context_lower = context.lower()
    
    # Keywords for different states
    uninspired_keywords = ["bored", "uninspired", "don't know what", "no idea", "can't think", "stuck on ideas"]
    overwhelmed_keywords = ["overwhelmed", "too much", "too complicated", "confused", "don't understand", "lost"]
    failed_keywords = ["failed", "gave up", "couldn't finish", "abandoned", "didn't work out", "stuck and"]
    
    # Check for failed projects
    for keyword in failed_keywords:
        if keyword in context_lower:
            return "failed-projects"
    
    # Check for overwhelmed
    for keyword in overwhelmed_keywords:
        if keyword in context_lower:
            return "overwhelmed"
    
    # Check for uninspired
    for keyword in uninspired_keywords:
        if keyword in context_lower:
            return "uninspired"
    
    return "normal"


# Rule 2: Constraint Conflict Detection & Rescoping
def detect_constraint_conflicts(
    difficulty: Optional[str],
    time_budget: Optional[str],
    domain: Optional[str]
) -> Optional[str]:
    """
    Detect conflicts between difficulty, time, and domain complexity.
    
    Args:
        difficulty: User's skill level
        time_budget: Available time
        domain: Project domain
        
    Returns:
        Conflict message if detected, None otherwise
    """
    if not difficulty or not time_budget:
        return None
    
    # Advanced + Weekend = Conflict
    if difficulty == "advanced" and time_budget == "weekend":
        if domain and any(complex_term in domain.lower() for complex_term in 
                         ["distributed", "blockchain", "kubernetes", "microservices", "ml ops"]):
            return "Advanced distributed systems typically need more than a weekend. Consider: (1) Simplify to a proof-of-concept, or (2) Extend timeline to 1-2 weeks."
        return "Advanced projects usually need more than a weekend. Consider extending to 1-2 weeks or choosing an intermediate project."
    
    # Beginner + 3+ weeks = Opportunity
    if difficulty == "beginner" and time_budget == "3+ weeks":
        return "You have plenty of time! With 3+ weeks, you could tackle an intermediate project. Would you like me to suggest intermediate-level projects instead?"
    
    # Intermediate + Weekend for complex domains
    if difficulty == "intermediate" and time_budget == "weekend":
        if domain and any(complex_term in domain.lower() for complex_term in 
                         ["machine learning", "deep learning", "ai", "blockchain"]):
            return "ML/AI projects can be time-intensive. For a weekend, I'll focus on tutorial-based or starter projects with pre-trained models."
    
    return None


# Rule 3: Ambiguity Cooldown
def should_apply_ambiguity_cooldown(clarification_count: int, recent_responses: List[str]) -> bool:
    """
    Determine if we should stop asking questions and use defaults.
    
    Args:
        clarification_count: Number of times we've asked for clarification
        recent_responses: List of recent user responses
        
    Returns:
        True if we should apply cooldown (stop asking, use defaults)
    """
    # If we've asked 2+ times, check for vague responses
    if clarification_count >= 2:
        return True
    
    # Check if recent responses are vague
    vague_patterns = [
        r"\b(don't know|dunno|not sure|whatever|anything|you decide|up to you|don't care)\b",
        r"^(idk|dk|any|sure|ok|okay)$"
    ]
    
    vague_count = 0
    for response in recent_responses[-3:]:  # Check last 3 responses
        response_lower = response.lower().strip()
        for pattern in vague_patterns:
            if re.search(pattern, response_lower):
                vague_count += 1
                break
    
    # If 2+ vague responses, apply cooldown
    return vague_count >= 2


# Rule 4: Persona-Based Scaffolding
def detect_skill_bridge_opportunity(context: str) -> Optional[Dict]:
    """
    Detect if user has mixed skill levels (advanced in one area, beginner in another).
    
    Args:
        context: Full conversation context
        
    Returns:
        Dict with skill analysis if bridge opportunity detected, None otherwise
    """
    context_lower = context.lower()
    
    # Patterns indicating skill mix
    skill_mix_patterns = [
        (r"good at (\w+) but (new to|beginner in|don't know) (\w+)", "bridge_needed"),
        (r"experienced (?:with|in) (\w+) but want to learn (\w+)", "bridge_needed"),
        (r"know (\w+) well but (\w+) is new", "bridge_needed"),
        (r"strong in (\w+).*weak in (\w+)", "bridge_needed"),
    ]
    
    for pattern, _ in skill_mix_patterns:
        match = re.search(pattern, context_lower)
        if match:
            return {
                "bridge_needed": True,
                "strong_skill": match.group(1) if match.lastindex >= 1 else None,
                "weak_skill": match.group(3) if match.lastindex >= 3 else match.group(2),
                "suggestion": f"I'll suggest projects that use {match.group(1)} as a foundation while teaching {match.group(3) if match.lastindex >= 3 else match.group(2)}."
            }
    
    return None


# Rule 5: Inspiration-Driven Discovery
def detect_inspiration_need(context: str) -> bool:
    """
    Detect if user needs inspiration rather than technical guidance.
    
    Args:
        context: Full conversation context
        
    Returns:
        True if user needs inspiration
    """
    context_lower = context.lower()
    
    inspiration_keywords = [
        "bored", "uninspired", "no idea", "don't know what to build",
        "suggest something", "surprise me", "what should i build",
        "need ideas", "looking for inspiration"
    ]
    
    return any(keyword in context_lower for keyword in inspiration_keywords)


# Rule 6: Context-Aware Ideation (Trending)
def detect_trending_request(context: str) -> bool:
    """
    Detect if user wants trending/hot/recent projects.
    
    Args:
        context: Full conversation context
        
    Returns:
        True if user wants trending projects
    """
    context_lower = context.lower()
    
    trending_keywords = [
        "trending", "hot", "popular", "latest", "recent", "new",
        "what's hot", "what's new", "current", "modern", "cutting edge",
        "state of the art", "sota"
    ]
    
    return any(keyword in context_lower for keyword in trending_keywords)


# Rule 7: Reuse/Upgrade Existing Project
def detect_upgrade_intent(context: str) -> Optional[Dict]:
    """
    Detect if user wants to upgrade an existing project.
    
    Args:
        context: Full conversation context
        
    Returns:
        Dict with existing project info if upgrade intent detected, None otherwise
    """
    context_lower = context.lower()
    
    # Patterns indicating existing project
    upgrade_patterns = [
        r"i have (?:a |an )?(\w+)(?: app| project| application)?",
        r"i (?:already )?built (?:a |an )?(\w+)",
        r"extend my (\w+)",
        r"add (?:features |functionality )?to my (\w+)",
        r"upgrade my (\w+)",
        r"improve my (\w+)",
    ]
    
    for pattern in upgrade_patterns:
        match = re.search(pattern, context_lower)
        if match:
            # Extract tech stack
            tech = match.group(1)
            
            # Look for additional context about what they want to add
            add_patterns = [
                r"add (\w+(?: \w+)?)",
                r"want to (\w+(?: \w+)?)",
                r"include (\w+(?: \w+)?)",
            ]
            
            features_to_add = []
            for add_pattern in add_patterns:
                add_match = re.search(add_pattern, context_lower)
                if add_match:
                    features_to_add.append(add_match.group(1))
            
            return {
                "upgrade_mode": True,
                "existing_tech": tech,
                "features_to_add": features_to_add,
                "suggestion": f"I'll create an upgrade roadmap for your {tech} project."
            }
    
    return None


# Rule 8: Locale/Market Awareness
def detect_locale_or_market(context: str) -> Optional[str]:
    """
    Detect if user mentions a specific market or locale.
    
    Args:
        context: Full conversation context
        
    Returns:
        Locale/market name if detected, None otherwise
    """
    context_lower = context.lower()
    
    # Common markets/locales
    markets = [
        "india", "indian", "china", "chinese", "japan", "japanese",
        "europe", "european", "us", "usa", "america", "american",
        "africa", "african", "latin america", "southeast asia",
        "middle east", "brazil", "brazilian"
    ]
    
    for market in markets:
        if market in context_lower:
            return market.title()
    
    # Check for locale-specific patterns
    locale_patterns = [
        r"for (?:the )?(\w+) market",
        r"in (\w+)",
        r"targeting (\w+) users",
    ]
    
    for pattern in locale_patterns:
        match = re.search(pattern, context_lower)
        if match:
            return match.group(1).title()
    
    return None


# Rule 9: Privacy Sensitivity
def detect_privacy_concerns(context: str) -> bool:
    """
    Detect if user has privacy concerns.
    
    Args:
        context: Full conversation context
        
    Returns:
        True if privacy concerns detected
    """
    context_lower = context.lower()
    
    privacy_keywords = [
        "privacy", "private", "local", "offline", "no cloud",
        "don't want to use cloud", "on-premise", "self-hosted",
        "data privacy", "secure", "confidential"
    ]
    
    return any(keyword in context_lower for keyword in privacy_keywords)


# Rule 10: Quality/Showcase/Polish Emphasis
def analyze_quality_emphasis(context: str) -> Dict:
    """
    Analyze user's quality and polish requirements.
    
    Args:
        context: Full conversation context
        
    Returns:
        Dict with quality preferences
    """
    context_lower = context.lower()
    
    quality_indicators = {
        "tests": any(kw in context_lower for kw in ["test", "testing", "tdd", "unit test"]),
        "ci_cd": any(kw in context_lower for kw in ["ci", "cd", "ci/cd", "pipeline", "github actions"]),
        "documentation": any(kw in context_lower for kw in ["documentation", "docs", "readme", "documented"]),
        "production": any(kw in context_lower for kw in ["production", "production-ready", "deploy", "deployment"]),
        "portfolio": any(kw in context_lower for kw in ["portfolio", "showcase", "resume", "job"]),
        "polish": any(kw in context_lower for kw in ["polish", "polished", "professional", "clean"])
    }
    
    # Determine overall quality focus
    quality_count = sum(quality_indicators.values())
    
    if quality_count >= 3:
        quality_focus = "production"
        doc_emphasis = "high"
    elif quality_count >= 1:
        quality_focus = "production"
        doc_emphasis = "medium"
    else:
        quality_focus = "prototype"
        doc_emphasis = "low"
    
    return {
        "quality_focus": quality_focus,
        "doc_emphasis": doc_emphasis,
        "indicators": quality_indicators
    }


# Rule 11: Portfolio Narrative Generation
def generate_portfolio_narrative(project_name: str, domain: str, user_context: str) -> str:
    """
    Generate a portfolio narrative for career-focused users.
    
    Args:
        project_name: Name of the project
        domain: Project domain
        user_context: User's context/goals
        
    Returns:
        Portfolio narrative string
    """
    context_lower = user_context.lower()
    
    # Detect career goals
    career_keywords = {
        "faang": "FAANG companies",
        "startup": "startups",
        "freelance": "freelance work",
        "job": "job applications",
        "career": "career growth",
        "interview": "technical interviews"
    }
    
    target = "employers"
    for keyword, value in career_keywords.items():
        if keyword in context_lower:
            target = value
            break
    
    narrative = f"""
    📖 Portfolio Story for {project_name}:
    
    This project demonstrates:
    • Technical depth in {domain}
    • Ability to build production-ready applications
    • Problem-solving and system design skills
    
    How to present this to {target}:
    1. Highlight the technical challenges you solved
    2. Emphasize the technologies and best practices used
    3. Showcase the end-to-end implementation (frontend, backend, deployment)
    4. Include metrics (performance, scalability, test coverage)
    
    LinkedIn Post Template:
    "Just completed a {domain} project that [key achievement]. Built with [tech stack], 
    featuring [key features]. Check it out: [GitHub link]"
    
    Resume Bullet Point:
    "Developed a {domain} application using [tech stack], implementing [key features] 
    and achieving [measurable outcome]"
    """
    
    return narrative.strip()


# Helper function to get adaptive tone based on motivation state
def get_adaptive_tone(motivation_state: str) -> str:
    """
    Get adaptive tone message based on user's motivation state.
    
    Args:
        motivation_state: One of "uninspired", "overwhelmed", "failed-projects", "normal"
        
    Returns:
        Tone adaptation message
    """
    tones = {
        "uninspired": "I hear you! Let's find something that sparks your interest. I'll ask a few questions to discover what excites you.",
        "overwhelmed": "No worries! Let's start small. I'll suggest beginner-friendly, hands-on projects that build confidence.",
        "failed-projects": "That's totally normal - every developer has unfinished projects! Let's find something achievable and motivating.",
        "normal": ""
    }
    
    return tones.get(motivation_state, "")


# Helper function to generate sensible defaults for ambiguous requests
def generate_sensible_defaults() -> Dict:
    """
    Generate sensible defaults when user is ambiguous.
    
    Returns:
        Dict with default values
    """
    return {
        "difficulty": "intermediate",
        "time_budget": "1-2 weeks",
        "project_type": "repo",
        "recency_preference": "latest",
        "cost_constraints": "free-preferred",
        "deployment_target": "web",
        "collaboration_mode": "solo",
        "doc_emphasis": "medium",
        "quality_focus": "prototype",
        "focus_area": "balanced",
        "confidence_level": "intermediate-confident",
        "note": "Using reasonable defaults since you're flexible. We can adjust as needed!"
    }
