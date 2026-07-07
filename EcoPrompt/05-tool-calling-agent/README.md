# Tool-Calling Agent

A minimal but real AI **agent**: the model is given a set of tools, decides on
its own which ones to call (and in what order), runs them, reads the results,
and keeps going until it can answer. The UI shows every tool call so you can
watch the agent "think" step by step.

Ask something like:

> **What's the weather in Tokyo and Dhaka, and what is 18% of 245?**

The agent calls `get_weather` twice and `calculator` once, then composes one
final answer from all three results.

---

## What it teaches

| Concept | Where it shows up |
|---|---|
| Function / tool calling | Tools defined as JSON schemas, passed to the model |
| **The agent loop** | model → tool calls → results → model, repeated until done |
| Letting the model choose | The model decides which tools to call, not your code |
| Multi-tool calls in one turn | Weather for two cities requested together |
| Feeding results back | Tool outputs returned as `role: "tool"` messages |
| Safety: never `eval()` model output | Calculator parses math via a restricted AST |
| Loop guards | Hard cap on iterations so an agent can't run forever |

---

## The agent loop (the core idea)

This is the pattern behind essentially every AI agent product. In plain terms:

1. Send the conversation **plus the tool definitions** to the model.
2. If the model's reply contains **tool calls**, your code runs those tools
   locally, appends the results to the conversation, and goes back to step 1.
3. If the reply has **no tool calls**, the model is done — return its answer.

```
                ┌──────────────────────────────┐
                │  Send messages + tools to     │
                │  the model                     │
                └──────────────┬────────────────┘
                               │
                   ┌───────────▼───────────┐
                   │  Did it request tools? │
                   └───────┬───────┬────────┘
                       yes │       │ no
            ┌──────────────▼─┐   ┌─▼───────────────┐
            │ Run the tools  │   │ Return the final│
            │ Append results │   │ answer          │
            └──────────────┬─┘   └─────────────────┘
                           │
                           └──────────► (loop back to top)
```

A counter caps the loop at 6 rounds so a misbehaving model can never spin
forever.

---

## The tools in this demo

| Tool | What it does | Notes |
|---|---|---|
| `calculator` | Evaluates an arithmetic expression like `245 * 0.18` | Parsed with a restricted AST — **never** `eval()` |
| `get_weather` | Returns weather for a city | Hardcoded demo data (Tokyo, London, Dhaka, New York) — stands in for a real weather API |
| `get_time` | Returns the current local date and time | No arguments |

Each tool is described to the model with a name, a description, and a JSON
schema for its inputs. The model uses those descriptions to decide what to call.

---

## Project structure

```
05-tool-calling-agent/
├── main.py            # FastAPI backend: tool definitions + the agent loop
├── requirements.txt   # Python dependencies
├── .env.example       # Template for your API key (NEVER commit your real .env)
└── static/
    └── index.html     # Frontend: question box + live tool-call trace
```

---

## Requirements

- **Python 3.10+** — check with `python --version`
- **An OpenAI API key** with a little billing credit — the agent makes one or
  more model calls per question.

---

## Setup & run

Run these from inside the `05-tool-calling-agent/` folder.

**1. Create and activate a virtual environment**

```bash
python -m venv .venv
```

| OS / shell | Activate command |
|---|---|
| Windows (cmd) | `.venv\Scripts\activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Mac / Linux | `source .venv/bin/activate` |

`(.venv)` appears at the start of your prompt when it's active.

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Add your API key**

```bash
# Windows
copy .env.example .env
# Mac / Linux
cp .env.example .env
```

Open `.env` and paste your real key (from https://platform.openai.com/api-keys):

```
OPENAI_API_KEY=sk-...your-real-key...
```

> ⚠️ **Never commit `.env` to GitHub.** Keep a `.gitignore` containing `.env`
> so your key stays private. Only `.env.example` (the placeholder) belongs in
> the repo.

**4. Start the server**

```bash
python main.py
```

Wait for the line saying it's running on port `8000`.

**5. Open the app**

Go to **http://localhost:8000** in your browser.

> Do **not** open `http://0.0.0.0:8000` — that's the address the server
> *listens on*, not one a browser can reach. Always use `localhost`.

**6. Stop the server**

Press `Ctrl+C` in the terminal.

---

## Things to try

- `What's the weather in Tokyo and Dhaka, and what is 18% of 245?`
  — multiple tools across two categories in one question
- `What time is it, and how many minutes are in 3.5 hours?`
  — `get_time` plus `calculator`
- `What's the weather in Paris?`
  — the demo has no Paris data; watch how the agent handles a tool that
    returns "no data"
- `What is 2 to the power of 10, then add 24?`
  — chained arithmetic in a single calculator call

Each run shows the ordered list of tool calls (name, input, output) above the
final answer.

---

## How a request flows through the code

1. Your question becomes the first `user` message.
2. The backend loops:
   - Calls the model with the full message list **and** the tool definitions.
   - If the model returns tool calls, each one is executed by a matching Python
     function, and its output is appended as a `tool` message (tied to the
     call's id).
   - The loop repeats so the model can react to the results (and call more
     tools if needed).
3. When the model replies with no further tool calls, that text is the final
   answer, returned along with the full trace for display.

---

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| `ERR_ADDRESS_INVALID` in browser | You opened `0.0.0.0:8000`. Use `http://localhost:8000`. |
| `401` / `AuthenticationError` | Key in `.env` is missing or mistyped; confirm `.env` sits next to `main.py`. |
| `insufficient_quota` (429) | Add billing credit to your OpenAI account. |
| Push to GitHub blocked: "Push cannot contain secrets" | A real key is in a committed `.env`. Remove it from tracking, revoke the key at OpenAI, and recommit. |
| `python` not recognized (Windows) | Python isn't on PATH — try `py main.py`, or reinstall with "Add to PATH" ticked. |
| Agent says "hit the step limit" | The model looped 6 times without finishing — rare; usually means the question was ambiguous. |
| Port already in use | `Ctrl+C` the other server, or change `port=8000` to `8001` at the bottom of `main.py`. |

---

## Extending it

- **Add a real tool.** Replace `get_weather`'s hardcoded data with an actual
  weather API call. The model needs no changes — just update the function and
  keep the schema accurate.
- **Add new tools.** Write a Python function, add a matching entry to the
  `TOOLS` list (name + description + input schema) and to `TOOL_FUNCS`. The
  model will start using it based on the description you give.
- **Tune the loop cap.** The `range(6)` limit balances capability against
  runaway cost; raise or lower it as needed.

---

## Notes

- Tools are deliberately simple so the *loop* is the star, not the tools. The
  same loop scales to real tools (web search, database queries, file I/O).
- The calculator parses expressions through a whitelist of math operations
  rather than running `eval()`, because executing model-generated code directly
  is a serious security risk.
- Model names and pricing change over time. If the model string in `main.py` is
  ever deprecated, check https://platform.openai.com/docs/models for a current
  one.