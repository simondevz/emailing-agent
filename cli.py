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
from typing import Dict

from agents.agent import run_email_agent
from agents.actions.playwright_execution import PlaywrightExecutor

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

# Shared provider configuration (aligned with PlaywrightExecutor)
PROVIDER_CONFIG = {
    "gmail": {"url": "https://mail.google.com", "session_file": "sessions/gmail_auth.json", "compose_selector": "[aria-label='Compose']"},
    "outlook": {"url": "https://outlook.live.com", "session_file": "sessions/outlook_auth.json", "compose_selector": "[aria-label*='New message']"}
}

async def setup_session(provider: str) -> bool:
    """Set up authentication session for a given provider."""
    from playwright.async_api import async_playwright
    import json
    
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        console.print(f"[bold red]❌ Invalid provider: {provider}[/bold red]")
        return False
    
    console.print(f"\n[bold cyan]🔧 Setting up {provider} session...[/bold cyan]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to provider
        await page.goto(config["url"])
        
        console.print(f"[yellow]📝 Please log into your {provider} account in the browser window.[/yellow]")
        console.print("[dim]After logging in successfully, press Enter to save the session (or Ctrl+C to cancel)...[/dim]")
        
        try:
            input()  # Wait for user to log in
            # Verify login by checking for a key element (e.g., compose button)
            compose_selector = config.get("compose_selector", "[aria-label*='Compose'], [aria-label*='New message']")
            if await page.locator(compose_selector).count() == 0:
                console.print(f"[bold red]❌ Login verification failed for {provider}. Please ensure you logged in correctly.[/bold red]")
                await browser.close()
                return False
            
            # Save the session
            storage_state = await context.storage_state()
            session_file = Path(config["session_file"])
            session_file.parent.mkdir(exist_ok=True)
            with open(session_file, "w") as f:
                json.dump(storage_state, f, indent=2)
            
            await browser.close()
            console.print(f"[green]✅ {provider.capitalize()} session saved successfully![/green]")
            return True
        
        except KeyboardInterrupt:
            console.print(f"[yellow]⚠️ {provider.capitalize()} session setup cancelled by user.[/yellow]")
            await browser.close()
            return False
        except Exception as e:
            console.print(f"[bold red]❌ Error setting up {provider} session: {str(e)}[/bold red]")
            await browser.close()
            return False

async def handle_session(provider: str) -> bool:
    """Check if session exists, ask user, and either reuse or setup a new session."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        console.print(f"[bold red]❌ Invalid provider: {provider}[/bold red]")
        return False
    
    session_file = Path(config["session_file"])
    
    if session_file.exists():
        use_existing = typer.confirm(
            f"Existing {provider} session found at {session_file}. Do you want to use it?",
            default=True
        )
        if use_existing:
            console.print(f"[green]✅ Using existing {provider} session.[/green]")
            return True
        else:
            console.print(f"[cyan]🔄 Setting up new {provider} session...[/cyan]")
            return await setup_session(provider)
    else:
        console.print(f"[cyan]🔄 No existing {provider} session found. Setting up new session...[/cyan]")
        return await setup_session(provider)

@app.command("start")
def start_sessions(
    provider: Provider = typer.Option(Provider.gmail, help="Email provider to set up (gmail, outlook, or both)")
):
    """Set up pre-authenticated browser sessions for Gmail and/or Outlook."""
    async def async_start():
        console.print(Panel(
            Text("🔧 Session Setup Guide", style="bold cyan"),
            title="[bold blue]Authentication Setup[/bold blue]",
            border_style="blue"
        ))
        
        console.print("\n[bold yellow]This will help you create pre-authenticated sessions for your email provider(s).[/bold yellow]")
        console.print("\n[dim]The process involves:[/dim]")
        console.print("[dim]1. Opening a browser window[/dim]")
        console.print("[dim]2. You manually log into your email account[/dim]")
        console.print("[dim]3. The session is saved for future automated use[/dim]")
        
        try:
            success = True
            if provider in [Provider.gmail, Provider.both]:
                success &= await handle_session(Provider.gmail.value)
            if provider in [Provider.outlook, Provider.both]:
                success &= await handle_session(Provider.outlook.value)
            
            if success:
                console.print("\n[bold green]✅ Session setup completed![/bold green]")
            else:
                console.print("\n[bold red]❌ Session setup failed for one or more providers.[/bold red]")
        
        except Exception as e:
            console.print(f"\n[bold red]❌ Setup error: {str(e)}[/bold red]")
    
    asyncio.run(async_start())

@app.command("run")
def run_agent(
    provider: Provider = typer.Option(Provider.gmail, help="Email provider to use (gmail or outlook)")
):
    """Run the email agent for the specified provider."""
    async def async_run():
        console.print(Panel(
            Text(f"🤖 Starting Email Agent for {provider.value.capitalize()}", style="bold cyan"),
            title="[bold blue]Email Agent[/bold blue]",
            border_style="blue"
        ))
        
        if provider == Provider.both:
            console.print("[bold red]❌ The 'both' option is not supported for running the agent. Please choose 'gmail' or 'outlook'.[/bold red]")
            raise typer.Exit(code=1)
        
        session_file = Path(PROVIDER_CONFIG[provider.value]["session_file"])
        if not session_file.exists():
            console.print(f"[bold yellow]⚠️ No session found for {provider.value}. Please run 'start' to set up a session first.[/bold yellow]")
            if typer.confirm(f"Do you want to set up a {provider.value} session now?", default=True):
                if await handle_session(provider.value):
                    console.print(f"[green]✅ Session setup complete. Starting email agent...[/green]")
                else:
                    console.print(f"[bold red]❌ Failed to set up {provider.value} session. Aborting.[/bold red]")
                    raise typer.Exit(code=1)
            else:
                console.print(f"[yellow]⚠️ Aborting email agent run due to missing session.[/yellow]")
                raise typer.Exit(code=1)
        
        try:
            await run_email_agent(provider=provider.value)
            console.print(f"\n[bold green]✅ Email agent execution completed for {provider.value}.[/bold green]")
        except KeyboardInterrupt:
            console.print("\n[bold yellow]⚠️ Agent execution interrupted by user.[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]❌ Agent execution error: {str(e)}[/bold red]")
            import traceback
            traceback.print_exc()
    
    asyncio.run(async_run())

@app.command("check-sessions")
def check_sessions():
    """Check available authentication sessions."""
    console.print(Panel(
        Text("🔍 Checking Authentication Sessions", style="bold cyan"),
        title="[bold blue]Session Status[/bold blue]",
        border_style="blue"
    ))
    
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    found = False
    for provider, config in PROVIDER_CONFIG.items():
        session_file = Path(config["session_file"])
        if session_file.exists():
            console.print(f"[green]✅ {provider.capitalize()} session found at {session_file}[/green]")
            found = True
        else:
            console.print(f"[yellow]⚠️ No {provider.capitalize()} session found at {session_file}[/yellow]")
    
    if not found:
        console.print("\n[bold yellow]⚠️ No sessions found. Run 'start' to set up new sessions.[/bold yellow]")

if __name__ == "__main__":
    app()