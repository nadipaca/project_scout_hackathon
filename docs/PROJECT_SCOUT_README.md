# ProjectScout AI Agent 🚀

**ProjectScout** is an intelligent AI agent that helps developers and students find their next project by analyzing their goals, searching GitHub for relevant repositories, and generating personalized project roadmaps.

## 🎯 What is ProjectScout?

ProjectScout is a conversational AI agent that:
- **Understands your goals** through natural language conversation
- **Searches GitHub** for relevant, high-quality project repositories
- **Classifies and ranks** projects based on your skill level, time budget, and preferences
- **Generates detailed roadmaps** with implementation phases, tasks, and tech stack options
- **Provides a web interface** for easy interaction via a FastAPI server

## ✨ Features

### Core Capabilities
- **Smart Clarification**: Asks targeted questions to understand your needs without being repetitive
- **GitHub Integration**: Searches and analyzes real GitHub repositories with README content
- **Intelligent Classification**: Ranks projects by difficulty, time requirements, and tech stack match
- **Personalized Roadmaps**: Generates step-by-step implementation plans tailored to your goals
- **Slot-Filling Conversation**: Maintains context across multiple conversation turns

### Advanced Features (V2)
- **11 Advanced Rules** for sophisticated request analysis:
  1. Motivation & Learning Style Detection
  2. Constraint Conflict Detection
  3. Ambiguity Cooldown (prevents over-questioning)
  4. Persona-Based Scaffolding
  5. Inspiration-Driven Discovery
  6. Context-Aware Ideation
  7. Reuse/Upgrade Existing Project
  8. Locale/Market Awareness
  9. Privacy Sensitivity
  10. Quality/Showcase/Polish Emphasis
  11. Upgrade Path & Portfolio Story

- **Diverse Project Recommendations**: Ensures variety across domains (NLP, CV, Web, Data)
- **Cost Awareness**: Filters for free-only or free-preferred solutions
- **Privacy Mode**: Suggests local-only solutions when privacy is a concern
- **Tech Stack Preservation**: Remembers and respects your preferred technologies

## 🏗️ Architecture

```
src/
├── agi_agents/
│   └── project_scout/
│       ├── agent.py           # Main agent logic
│       ├── models.py          # Pydantic models for I/O
│       └── advanced_rules.py  # Advanced analysis rules
└── arena/
    └── server.py              # FastAPI web server
```

### Key Components

1. **ProjectScoutAgent** (`agent.py`)
   - Request analysis with LLM-powered understanding
   - GitHub repository search and README fetching
   - Project classification and selection
   - Roadmap generation

2. **FastAPI Server** (`server.py`)
   - `/run-agent` endpoint for conversational interaction
   - Slot extraction for core fields (experience, time, goal)
   - Response normalization for clean output
   - Health check endpoint

3. **Data Models** (`models.py`)
   - `AgentInput`: User requirements and preferences
   - `AgentOutput`: Project recommendations and roadmap
   - `Project`: Individual project details
   - `Roadmap`: Implementation plan with phases
   - `Clarification`: Follow-up questions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API key
- GitHub token (optional, for higher rate limits)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agisdk
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```
   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   GITHUB_TOKEN=your-github-token  # Optional but recommended
   ```

### Running the Server

Start the FastAPI server:
```bash
python -m src.arena.server
```

The server will start on `http://localhost:8000`

### Testing the Agent

Run the test script:
```bash
python scripts/test_streaming.py
```

Or use the simple test:
```bash
python scripts/simple_test.py
```

## 📡 API Usage

### Endpoint: `/run-agent`

**Method:** `POST`

**Request Body:**
```json
{
  "goal": "I want to learn React and build AI apps",
  "history": [
    {
      "role": "user",
      "content": "I want to learn React"
    },
    {
      "role": "agent",
      "content": "Great! What's your experience level?"
    }
  ]
}
```

**Response (Clarification):**
```json
{
  "status": "completed",
  "message": "I see you're interested in React AI apps! To find the perfect project:\n1. What's your experience level? (beginner/intermediate/advanced)\n2. How much time do you have? (weekend/1-2 weeks/3+ weeks)\n3. What's your goal? (learning/portfolio/hackathon)",
  "data": {
    "level": null,
    "time": null,
    "goal_type": null
  },
  "finished": false,
  "type": "clarification"
}
```

**Response (Final Results):**
```json
{
  "status": "completed",
  "message": "Here are 3 great React AI projects for you:\n\n1. **AI Chatbot with React** — Build a conversational AI interface\n   Stack: React, OpenAI API, Node.js\n   Time: 1-2 weeks\n\n2. **Image Generator Dashboard** — Create AI-powered image generation UI\n   Stack: React, Stable Diffusion, FastAPI\n   Time: 1-2 weeks\n\n3. **Smart Document Analyzer** — Upload and analyze documents with AI\n   Stack: React, LangChain, Python\n   Time: 2-3 weeks",
  "data": {
    "level": "intermediate",
    "time": "1-2 weeks",
    "goal_type": "portfolio"
  },
  "finished": true,
  "type": "results"
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

## 🎨 Example Conversations

### Example 1: Beginner Learning Project

**User:** "I want to learn Python"

**Agent:** "Great choice! Python is very beginner-friendly. To find the perfect project for you, I need to know:
1. What's your experience level? (beginner/intermediate/advanced)
2. How much time do you have? (weekend/1-2 weeks/3+ weeks)
3. What's your goal? (learning/portfolio/hackathon)"

**User:** "I'm a beginner, have a weekend, and want to learn"

**Agent:** *Returns 3-5 beginner-friendly Python projects with weekend scope*

### Example 2: Advanced Portfolio Project

**User:** "I'm an intermediate developer looking for a 2-week React AI project for my portfolio. I want to keep it free, no paid APIs."

**Agent:** *Directly searches and returns React AI projects that use free/open-source solutions*

### Example 3: Privacy-Conscious Project

**User:** "I want an AI project that analyzes my journal, but data must stay private on my machine"

**Agent:** "Got it—privacy is key. I'll focus on local-only solutions. Are you okay installing a local model (more setup), or prefer simpler offline libraries? Also, what's your experience level?"

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Manual Testing
```bash
# Test the agent directly
python scripts/simple_test.py

# Test with streaming
python scripts/test_streaming.py

# Test advanced rules
python scripts/test_advanced_rules.py
```

### Verification Tests
```bash
# Run all verification scenarios
python scripts/verify_v2_rules.py
```

## 🔧 Configuration

### Slot Extraction

The server extracts three core fields from user messages:

- **experience_level**: `beginner` | `intermediate` | `advanced`
- **time_budget**: `weekend` | `1-2 weeks` | `3+ weeks`
- **goal_type**: `learning` | `portfolio` | `hackathon`

### System Prompts

Two main prompts guide the agent:

1. **PROJECTSCOUT_CLARIFY_SYSTEM**: For asking follow-up questions
2. **PROJECTSCOUT_PLAN_SYSTEM**: For generating project suggestions

Both can be customized in `src/arena/server.py`

### Response Normalization

The `normalize_reply()` function cleans LLM output by:
- Removing markdown headings
- Filtering template-y phrases
- Collapsing excessive blank lines

## 📊 Advanced Rules

ProjectScout uses 11 advanced rules for sophisticated analysis:

1. **Motivation Detection**: Identifies overwhelmed, uninspired, or failed-project states
2. **Constraint Conflicts**: Detects unrealistic difficulty/time combinations
3. **Ambiguity Cooldown**: Prevents over-questioning by using sensible defaults
4. **Skill Bridging**: Suggests projects that connect known and new technologies
5. **Inspiration Discovery**: Asks open-ended questions when users need ideas
6. **Trending Awareness**: Focuses on latest technologies when requested
7. **Upgrade Mode**: Generates upgrade paths for existing projects
8. **Locale Awareness**: Adapts suggestions for specific markets/regions
9. **Privacy Mode**: Suggests local-only solutions when privacy is a concern
10. **Quality Focus**: Emphasizes production-ready features when needed
11. **Portfolio Story**: Helps craft compelling project narratives

## 🌐 Deployment

### Local Development
```bash
python -m src.arena.server
```

### Production (with Uvicorn)
```bash
uvicorn src.arena.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### With ngrok (for external access)
```bash
ngrok http 8000
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is part of the AGI SDK and follows its licensing terms.

## 🙏 Acknowledgments

- Built on the [AGI SDK](https://github.com/agi-inc/agisdk) framework
- Uses OpenAI's GPT models for natural language understanding
- Integrates with GitHub's API for repository search

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ❤️ for developers who want to find their next great project**
