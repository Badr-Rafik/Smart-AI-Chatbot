# Smart AI Chatbot

Small Streamlit-based chatbot that can connect to Cohere or Hugging Face Inference API for text generation.

## Features
- Secure API credential loading with `python-dotenv` or environment variables
- Modular `ai_service.py` handling prompt construction, API calls, and error handling
- Conversation history persisted in `st.session_state.messages`
- Input validation and graceful error messages

## Setup

1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure API keys

- Copy `.env.example` to `.env` and fill in `COHERE_API_KEY` and/or `HUGGINGFACE_API_TOKEN`.
- Alternatively set environment variables in your system.

4. Run the app

```bash
streamlit run app.py
```

## Usage

- Choose provider (`cohere` or `huggingface`) and specify a model name in the sidebar.
- Optionally edit the `System instruction` to guide assistant behavior.
- Type messages in the input area and click `Send`.
- Use `Clear Conversation` to reset history.

## Notes & Troubleshooting

- Keep your real API keys secret — do not commit `.env` to Git.
- If you receive authentication errors, verify your keys and scopes.
- If a provider SDK is not installed (e.g., `cohere`), the app reports it in the UI.

## Setting API keys (secure)

Do NOT paste secrets into public chat. Instead add them locally using one of these methods.

1) Create a `.env` file in the project root (recommended):

```powershell
Copy-Item .env.example .env
notepad .env
# Edit the file and paste your keys, e.g.:
# COHERE_API_KEY=your_cohere_api_key_here
# HUGGINGFACE_API_TOKEN=your_hf_token_here
```

2) Set for the current PowerShell session (temporary):

```powershell
$env:COHERE_API_KEY = "<YOUR_COHERE_KEY>"
# then start Streamlit in the same session
streamlit run app.py
```

3) Set permanently for your user (Windows):

```powershell
setx COHERE_API_KEY "<YOUR_COHERE_KEY>"
# restart your shell/IDE to pick up the new variable
```

4) Quick verification (any shell):

```bash
python -c "import os; print(bool(os.getenv('COHERE_API_KEY')))"
```

Security notes:
- Never commit your `.env` file to version control; `.gitignore` already excludes it.
- If you accidentally committed a key, rotate it immediately from the provider dashboard.

Helper scripts
----------------

You can use the included helper scripts to create a `.env` file locally without pasting your key into chat.

- PowerShell (Windows):

```powershell
.
\scripts\set_env.ps1
```

- Bash (macOS / Linux / WSL):

```bash
bash ./scripts/set_env.sh
```

Both scripts prompt securely for `COHERE_API_KEY` and `HUGGINGFACE_API_TOKEN` and write a `.env` file in the project root.

Quick test (performed by the assistant):

```bash
python test_cohere_call.py
```

This script calls Cohere Chat v2 using the `COHERE_API_KEY` from your environment and prints a sample assistant response.

