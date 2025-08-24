# 🤖 Email Agent CLI

A multi-agent email automation system using **LangGraph** and **Playwright**. This project allows you to interact with an AI-powered email agent that can draft and send emails for Gmail and Outlook through pre-authenticated browser sessions.

---

## Features

- Conversational User Agent for collecting email details.
- Planner Agent for step-by-step execution.
- Playwright Agent for browser automation.
- Pre-authenticated sessions to avoid repeated logins.
- Support for Gmail and Outlook.
- Command-line interface for easy interaction.

---

## Installation

1. **Clone the repository**:

```bash
git clone <your-repo-url>
cd emailing-agent
```

2. **Create a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root with the following:

```env
GROQ_API_KEY=gsk_M\
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_sk_6ed743
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_PROJECT="emailBot"
```

> Make sure to replace keys with your valid API credentials.

---

## CLI Usage

The entry point is `cli.py`. You can run commands using:

```bash
python cli.py <command> [options]
```

### Commands

1. **`start`** – Set up pre-authenticated browser sessions.

```bash
python cli.py start --provider <gmail|outlook|both>
```

- `--provider`: Choose the provider to set up (default: `gmail`).
- Guides you to log in via a browser and saves the session for automation.

---

2. **`run`** – Run the email agent for a specific provider.

```bash
python cli.py run --provider <gmail|outlook>
```

- `--provider`: Choose `gmail` or `outlook`.
- Launches the email agent to collect details and send emails.
- **Note:** The `both` option is not supported for running the agent.

---

3. **`check-sessions`** – Verify saved authentication sessions.

```bash
python cli.py check-sessions
```

- Displays the status of saved sessions.
- Prompts to run `start` if no sessions are found.

---

## Session Setup Workflow

1. Run the `start` command.
2. A browser window opens for manual login.
3. Once logged in, press Enter to save the session.
4. The saved session is stored under `sessions/<provider>_auth.json`.
5. Subsequent runs of the agent will use this session automatically.

---

## Example Workflow

```bash
# 1. Set up Gmail session
python cli.py start --provider gmail

# 2. Run the email agent
python cli.py run --provider gmail

# 3. Check sessions
python cli.py check-sessions
```

---

## Notes

- Ensure your `.env` file is loaded before running the agent.
- The agent requires a browser window for authentication during session setup.
- Playwright will launch in **non-headless mode** for login and interaction.
- All actions, DOM snapshots, and email drafts are tracked in real-time.

---

## Dependencies

- Python 3.12+
- [LangGraph](https://github.com/langchain/langgraph)
- [Playwright](https://playwright.dev/python/)
- [Rich](https://github.com/Textualize/rich)
- [Typer](https://typer.tiangolo.com/)
