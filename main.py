from dotenv import load_dotenv
load_dotenv()

import logging
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)

# Import Router
from orchestrator.router import run_orchestrator

log = logging.getLogger(__name__)
console = Console()

def main():
    """
    Main entry point for the CoderLang CLI.
    """
    if not os.environ.get("GOOGLE_API_KEY"):
        console.print("[bold red]Error: GOOGLE_API_KEY not set. Please create a .env file.[/bold red]")
        sys.exit(1)

    console.print(Panel.fit("[bold blue]CoderLang Enterprise Agent[/bold blue]\nType 'exit' to quit.", subtitle="Powered by Gemini"))

    while True:
        user_input = Prompt.ask("\n[bold green]User Request[/bold green]")
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            console.print("[yellow]Goodbye![/yellow]")
            break
            
        if not user_input.strip():
            continue

        console.print(f"[dim]Processing: {user_input}[/dim]")
        
        try:
            results = run_orchestrator(user_input)
            
            # Pretty print the Evaluation Score
            if "final_evaluation" in results:
                eval_text = results["final_evaluation"]
                color = "green" if "10/10" in eval_text or "9/10" in eval_text else "yellow"
                console.print(Panel(eval_text, title="[bold]Evaluator Score[/bold]", border_style=color))
            
        except Exception as e:
            console.print(f"[bold red]System Error:[/bold red] {e}")

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()