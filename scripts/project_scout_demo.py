import asyncio
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agi_agents.project_scout.agent import ProjectScoutAgent
from arena import AgentState

load_dotenv()
console = Console()

async def main():
    console.print(Panel.fit("[bold blue]ProjectScout AI[/bold blue]\nFind your next coding project!"))

    # Get user input
    goal = console.input("[bold green]What kind of project are you looking for?[/bold green] (e.g. 'Intermediate Python React app'): ")
    
    if not goal:
        console.print("[red]Goal cannot be empty.[/red]")
        return

    console.print(f"\n[italic]Scouting projects for: {goal}...[/italic]")

    # Initialize agent
    agent = ProjectScoutAgent()
    
    # Create state
    state = AgentState(goal=goal)
    
    # Run agent loop
    while not state.finished:
        try:
            await agent.step(None, state)
        except Exception as e:
            console.print(f"[bold red]Error running agent:[/bold red] {e}")
            import traceback
            traceback.print_exc()
            return

        # Check if agent has a question (not finished, last msg is assistant)
        if not state.finished and state.messages and state.messages[-1]["role"] == "assistant":
            question = state.messages[-1]["content"]
            console.print(Panel(f"[bold yellow]Agent:[/bold yellow] {question}"))
            
            # Get user answer
            answer = console.input("[bold green]You:[/bold green] ")
            state.messages.append({"role": "user", "content": answer})
            continue

    # Display results
    if state.messages and state.messages[-1]["role"] == "assistant":
        content = state.messages[-1]["content"]
        try:
            result = json.loads(content)
            
            # Print Projects
            console.print("\n[bold]Found Projects:[/bold]")
            for p in result.get("projects", []):
                console.print(Panel(
                    f"[bold]{p['name']}[/bold] ({p['difficulty']})\n"
                    f"Stack: {', '.join(p['stack_tags'])}\n"
                    f"Time: {p['estimated_time']}\n"
                    f"URL: {p['github_url']}\n\n"
                    f"{p['summary']}\n\n"
                    f"[italic]{p['why_match']}[/italic]",
                    title=p['name']
                ))

            # Print Roadmap
            roadmap = result.get("plan_for_selected_project")
            if roadmap:
                console.print(f"\n[bold blue]Roadmap for {roadmap['project_name']}[/bold blue]")
                
                for phase in roadmap.get("phases", []):
                    tasks = "\n".join([f"- {t}" for t in phase['tasks']])
                    console.print(Panel(
                        f"[bold]Duration:[/bold] {phase['duration']}\n"
                        f"[bold]Goal:[/bold] {phase['goals']}\n\n"
                        f"[bold]Tasks:[/bold]\n{tasks}",
                        title=phase['name']
                    ))
                
                console.print("\n[bold]Stack Options:[/bold]")
                for opt in roadmap.get("stack_options", []):
                    console.print(f"- [bold]{opt['name']}[/bold]: {opt['description']}")

        except json.JSONDecodeError:
            console.print("[red]Could not parse agent output.[/red]")
            console.print(content)
    else:
        console.print("[red]Agent did not return a result.[/red]")

if __name__ == "__main__":
    asyncio.run(main())
