# RecipeForge 🍳

An agentic recipe builder using the **OpenAI Agents SDK** (`openai-agents`) and
`gpt-4o-mini`. Give it the ingredients you have and it designs a dish, suggests cheap
flavor add-ons, estimates the cost, and estimates how long it takes to make.

## What it does

A single orchestrating agent (`RecipeForge`) calls four tools:

| Tool | Job |
|------|-----|
| `create_strict_recipe` | Builds a dish using **only** your ingredients (water, salt, heat assumed). |
| `suggest_budget_boosters` | Recommends 3–5 cheap "least resource" add-ons for max flavor per cost. |
| `estimate_cost` | Approximates cost from a built-in price table + LLM fallback for unknown items. |
| `estimate_cooking_time` | Estimates prep + cook time to make ("build") the dish. |

> **Note on "estimated time to build the project":** in this cooking context that means
> the time to prepare the dish, which is what `estimate_cooking_time` returns.

Tools 1, 2 and 4 reason with the model via **structured outputs**
(`client.beta.chat.completions.parse` + Pydantic v2). Tool 3 is mostly deterministic.

## Architecture

```
        user ingredients
              │
              ▼
   ┌──────────────────────┐
   │   RecipeForge agent  │   (gpt-4o-mini, OpenAI Agents SDK)
   └──────────┬───────────┘
              │ orchestrates, in order
   ┌──────────┼───────────────────────────┐
   ▼          ▼            ▼               ▼
create_    suggest_     estimate_       estimate_
strict_    budget_      cost            cooking_
recipe     boosters                     time
              │
              ▼
   final structured answer
```

## Setup

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env          # then put your OPENAI_API_KEY in .env
```

## Run

```bash
python main.py
```

Example session:

```
Ingredients > eggs, rice, onion, oil, salt

The Dish: Quick Onion Fried Rice
...
Budget flavor boosters: garlic, soy sauce, chili flakes ...
Approximate cost: $1.05 total ($0.53 / serving)
Estimated time to make: 20 min (10 prep + 10 cook)
```

You can also pass a currency or servings naturally, e.g.
`eggs, rice, onion for 4 people, costs in BDT`.

## Files

```
recipeforge/
├── models.py          # Pydantic v2 models for all tool outputs
├── tools.py           # the four @function_tool definitions
├── recipe_agent.py    # Agent wiring tools + instructions
├── main.py            # interactive CLI
├── requirements.txt
└── .env.example
```

## Extending

- Wrap `run_once()` in a FastAPI endpoint for an HTTP API (same pattern as your
  Bangla Order Agent), add a Dockerfile, and you have a deployable service.
- Swap the price table for a real grocery price API.
- Add a `nutrition_estimate` tool, or a `dietary_filter` (vegan/halal) guardrail.
