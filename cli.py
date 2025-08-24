"""
Command Line Interface for the Email Agent System.
"""
import asyncio
import enum
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agents.agent import run_email_agent

app = typer.Typer(
    name="emailing-agent",
    help="🤖 Multi-agent email automation system using LangGraph and Playwright",
    add_completion=False
)

console = Console()

class Provider(str, enum.Enum):
    gmail = "gmail"
    outlook = "outlook"
    both = "both"


async def handle_session(provider: Provider):
    """Check if session exists, ask user, and either reuse or setup a new session."""
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    session_file = None
    if provider == Provider.gmail:
        session_file = sessions_dir / "gmail_auth.json"
    elif provider == Provider.outlook:
        session_file = sessions_dir / "outlook_auth.json"
    
    if session_file and session_file.exists():
        use_existing = typer.confirm(
            f"Existing {provider.value} session found. Do you want to use it?",
            default=True
        )
        if use_existing:
            console.print(f"[green]✅ Using existing {provider.value} session.[/green]")
            run_email_agent(provider=provider.value)
            return
        else:
            console.print(f"[cyan]🔄 Re-logging into {provider.value}...[/cyan]")

    # No session or user chose to login again
    if provider == Provider.gmail:
        await setup_gmail_session()
    elif provider == Provider.outlook:
        await setup_outlook_session()


@app.command("start")
def start_sessions():
    """
    Set up pre-authenticated browser sessions for Gmail and Outlook.
    """
    console.print(Panel(
        Text("🔧 Session Setup Guide", style="bold cyan"),
        title="[bold blue]Authentication Setup[/bold blue]",
        border_style="blue"
    ))
    
    console.print("\n[bold yellow]This will help you create pre-authenticated sessions for Gmail and Outlook.[/bold yellow]")
    console.print("\n[dim]The process involves:[/dim]")
    console.print("[dim]1. Opening a browser window[/dim]")
    console.print("[dim]2. You manually log into your email account[/dim]")
    console.print("[dim]3. The session is saved for future automated use[/dim]")
    
    provider = typer.prompt(
        "\nWhich provider would you like to set up 'google' or 'outlook'?",
        type=Provider,
        default="gmail"
    )
    
    try:
        if provider in [Provider.gmail, Provider.both]:
            asyncio.run(handle_session(Provider.gmail))
        if provider in [Provider.outlook, Provider.both]:
            asyncio.run(handle_session(Provider.outlook))
        
        console.print("\n[bold green]✅ Session setup completed![/bold green]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Setup interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Setup error: {str(e)}[/bold red]")


async def setup_gmail_session():
    """Set up Gmail authentication session."""
    from playwright.async_api import async_playwright
    import json
    from pathlib import Path
    
    console.print("\n[bold cyan]🔧 Setting up Gmail session...[/bold cyan]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to Gmail
        await page.goto("https://mail.google.com")
        
        console.print("[yellow]📝 Please log into your Gmail account in the browser window that just opened.[/yellow]")
        console.print("[dim]After logging in successfully, press Enter here to save the session...[/dim]")
        
        input()  # Wait for user to log in
        
        # Save the session
        storage_state = await context.storage_state()
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        with open(sessions_dir / "gmail_auth.json", "w") as f:
            json.dump(storage_state, f, indent=2)
        
        await browser.close()
        console.print("[green]✅ Gmail session saved successfully![/green]")
        run_email_agent()


async def setup_outlook_session():
    """Set up Outlook authentication session."""
    from playwright.async_api import async_playwright
    import json
    from pathlib import Path
    
    console.print("\n[bold cyan]🔧 Setting up Outlook session...[/bold cyan]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to Outlook
        await page.goto("https://outlook.live.com")
        
        console.print("[yellow]📝 Please log into your Outlook account in the browser window that just opened.[/yellow]")
        console.print("[dim]After logging in successfully, press Enter here to save the session...[/dim]")
        
        input()  # Wait for user to log in
        
        # Save the session
        storage_state = await context.storage_state()
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        with open(sessions_dir / "outlook_auth.json", "w") as f:
            json.dump(storage_state, f, indent=2)
        
        await browser.close()
        console.print("[green]✅ Outlook session saved successfully![/green]")

if __name__ == "__main__":
    app()  # Typer automatically parses sys.argv