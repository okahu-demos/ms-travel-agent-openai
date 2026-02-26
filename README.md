# Okahu agent demo with Microsoft Agent Framework (OpenAI)

This repo includes a demo travel assistant built with Microsoft Agent Framework and instrumented with Monocle/Okahu tracing. You can run it locally to test interactive flight-booking conversations with server-managed OpenAI thread memory.

## Prerequisites

- Python 3.10+
- OpenAI API key
- (Optional) Okahu API key if you want to export traces to Okahu cloud
- (Optional) Okahu VS Code extension for trace inspection

## Get started

### 1) Create a Python virtual environment

```bash
python3 -m venv .venv
```

### 2) Activate virtual environment

**Mac/Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment

Create a `.env` file in the repo root:

```dotenv
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_CHAT_MODEL_ID=gpt-4.1-mini
```

Notes:
- `OPENAI_CHAT_MODEL_ID` is the primary model variable used by this app.
- You can also set `OPENAI_MODEL` or `OPENAI_ASSISTANT_MODEL` as fallback values in code.

### 5) Run the app

```bash
python ms-travel-agent.py
```

You will get an interactive prompt:
- Type user requests directly in terminal
- Type `exit` or `quit` to end the session

## What this demo does

- Uses **one agent**: `Flight Agent`
- Uses **one tool**: `book_flight(from_airport, to_airport, travel_date)`
- Uses **OpenAIAssistantsClient** (OpenAI Assistants API)
- Maintains session context via server-managed thread IDs (`service_thread_id`)

## Session behavior

The app stores and reuses `service_thread_id` during the interactive run:

1. First request creates an OpenAI thread
2. App prints the thread ID (for example: `thread_...`)
3. Next requests reuse that thread ID
4. Model responds with conversation memory from prior turns

## Example interaction

```text
🧳 Flight Agent is ready.
Type your request and press Enter.
Type 'exit' or 'quit' to end.

[User]: Book a flight from BOM to JFK on 2026-12-15
[Agent]: ...successfully booked...
📋 Thread ID: thread_xxx

[User]: Also add a return flight on 2026-12-21
[Agent]: ...return flight booked...

[User]: What did we plan so far?
[Agent]: ...summarizes both flights...
```

## Troubleshooting

### `OpenAI model ID is required`
Set one of these in `.env`:
- `OPENAI_CHAT_MODEL_ID` (recommended)
- `OPENAI_MODEL`
- `OPENAI_ASSISTANT_MODEL`

### `OpenAI API key is missing`
Set:
- `OPENAI_API_KEY=<your-key>`

### Trace JSON printing in terminal
If telemetry exporter setup falls back to console, spans may print as JSON.

Use file-only exporter in code:
```python
setup_monocle_telemetry(
	workflow_name="okahu_demos_microsoft_travel_agent",
	monocle_exporters_list="file",
)
```

Also ensure shell/env does not override exporter unexpectedly:
```bash
unset MONOCLE_EXPORTER
```

## View traces

### Local trace files

Monocle writes traces to local files (for example under `.monocle/`).

### VS Code extension

Use the Okahu/Monocle extension to open and inspect generated traces.

## Project files

- `ms-travel-agent.py` — main interactive app
- `requirements.txt` — Python dependencies
- `.gitignore` — ignores `.venv/`, `.env`, `.monocle/`
