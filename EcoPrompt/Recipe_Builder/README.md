# RecipeForge 🍳 — An Agentic Recipe Builder

> A small but complete **multi-tool agent** built on the **OpenAI Agents SDK**
> (`openai-agents`) and `gpt-4o-mini`. Give it the ingredients you have on hand and it
> designs a dish, suggests cheap flavor upgrades, prices the meal, and tells you how long
> it takes to cook — each as a discrete, typed tool the agent orchestrates.

---

## Table of Contents

1. [What it is](#1-what-it-is)
2. [Why it exists (design goals)](#2-why-it-exists-design-goals)
3. [System architecture](#3-system-architecture)
4. [The agent layer — how orchestration works](#4-the-agent-layer--how-orchestration-works)
5. [The four tools — deep dive with pros & cons](#5-the-four-tools--deep-dive-with-pros--cons)
6. [Data models (Pydantic v2)](#6-data-models-pydantic-v2)
7. [Control flow, end to end](#7-control-flow-end-to-end)
8. [Setup & run](#8-setup--run)
9. [Configuration](#9-configuration)
10. [Honest limitations](#10-honest-limitations)
11. [Cost, latency & security notes](#11-cost-latency--security-notes)
12. [What makes this project interesting](#12-what-makes-this-project-interesting)
13. [Extension roadmap](#13-extension-roadmap)
14. [File map](#14-file-map)

---

## 1. What it is

RecipeForge is a command-line **agent** with **four function tools**. The agent is the
"brain" — it reads your request, decides which tools to call and in what order, then
synthesizes the tool outputs into one clean answer. The tools are the "hands" — each does
one narrow job and returns a **validated, structured object** rather than free text.

| Tool | Single responsibility |
|------|----------------------|
| `create_strict_recipe` | Build a dish using **only** the ingredients you gave (water, salt, heat assumed). |
| `suggest_budget_boosters` | Recommend 3–5 cheap, common add-ons that raise flavor the most per unit cost. |
| `estimate_cost` | Approximate the meal's cost (price table + LLM fallback) in a chosen currency. |
| `estimate_cooking_time` | Estimate prep + cook minutes to make ("build") the dish. |

> **Terminology note.** Your brief said "estimated time to **build the project**." In a
> cooking context that means the time to *prepare the dish*, which is exactly what
> `estimate_cooking_time` returns. If you meant software build-effort instead, that tool
> can be repurposed trivially.

---

## 2. Why it exists (design goals)

The project is intentionally a **teaching-grade reference** for four agentic-engineering
patterns that show up in real production systems:

1. **Multi-tool orchestration** — one agent coordinating several specialized tools.
2. **Constraint enforcement inside a tool** — the "strict ingredients" rule lives in the
   tool's own prompt, not just a hope that the top-level model behaves.
3. **Structured outputs everywhere** — every tool returns a Pydantic object, so the
   downstream synthesis never has to parse loose prose.
4. **Hybrid deterministic + LLM logic** — the cost tool prefers a lookup table and only
   falls back to the model for unknown items, trading a little accuracy for big savings
   in latency and token cost.

---

## 3. System architecture

```
                       user ingredients / request
                                  │
                                  ▼
                  ┌────────────────────────────────┐
                  │        RecipeForge agent        │
                  │  gpt-4o-mini · OpenAI Agents SDK │
                  │  (decides which tools, in order) │
                  └───────────────┬─────────────────┘
                                  │  function calls
        ┌─────────────────┬───────┴────────┬──────────────────┐
        ▼                 ▼                ▼                  ▼
 create_strict_     suggest_budget_   estimate_cost     estimate_cooking_
 recipe             boosters                             time
   │ LLM              │ LLM            │ table + LLM       │ LLM
   │ (structured)     │ (structured)   │ fallback          │ (structured)
   ▼                  ▼                ▼                  ▼
  Recipe          BudgetBoosters   CostBreakdown       TimeEstimate
        └─────────────────┴────────┬───────┴──────────────────┘
                                   ▼
                    agent synthesizes ONE final answer
```

There are **two layers of model use**: the orchestrating agent (decides *what* to do)
and the in-tool model calls (do the actual creative/estimation work). That separation is
the most important architectural idea in the project.

---

## 4. The agent layer — how orchestration works

The agent is defined in `recipe_agent.py` with three things: a name, an instruction
prompt, and the tool list. The instruction prompt tells it the preferred call order and
the exact output sections to produce. The OpenAI Agents SDK turns each `@function_tool`
function's signature and docstring into a JSON schema the model sees, so the model knows
what arguments each tool needs.

**Pros of this approach**

- **Declarative.** You describe the goal and hand over tools; you don't hand-code the
  branching logic. Adding a fifth capability is "write a tool + add it to the list."
- **Self-documenting tools.** Docstrings *are* the tool descriptions the model reads, so
  good documentation directly improves tool-selection accuracy.
- **Composable.** The same tools could be driven by a different agent, an API endpoint,
  or a test harness with no changes.

**Cons / trade-offs**

- **Less determinism.** The agent *may* skip a tool, reorder calls, or call one twice.
  For a strict pipeline you'd often be better served by a hard-coded sequence (a
  "workflow") rather than an autonomous agent.
- **Extra model round-trips.** Each tool decision is itself a model call, so a four-tool
  run can mean five-plus LLM calls — more latency and cost than a scripted pipeline.
- **Prompt-sensitive.** Tool selection quality depends on prompt wording and docstrings;
  small changes can shift behavior, which makes regression testing important.

---

## 5. The four tools — deep dive with pros & cons

### 5.1 `create_strict_recipe(ingredients, servings=2) -> Recipe`

Generates a single coherent dish constrained to the supplied ingredients (plus water,
salt, heat). The constraint is enforced in the tool's **own** system prompt, so even if
the orchestrating agent were sloppy, the recipe tool still refuses to invent ingredients.

- **Pros:** constraint lives at the point of generation; returns a fully structured
  `Recipe` (named steps with per-step durations), which feeds the time/cost tools cleanly.
- **Cons:** "strict" is enforced by prompt, not by code — a determined model could still
  drift, so it's *soft* enforcement. There's no post-generation validator that rejects a
  recipe containing an off-list ingredient (a natural hardening step — see §13).

### 5.2 `suggest_budget_boosters(ingredients, cuisine_hint="") -> BudgetBoosters`

Recommends 3–5 cheap, widely available add-ons ranked by flavor impact, each with a
reason, a rough USD cost, and a low/medium/high impact tag.

- **Pros:** directly encodes the "maximum flavor for minimum cost" intent; structured
  output makes the suggestions sortable/filterable downstream.
- **Cons:** the cost figures are model estimates, not real prices, so they're directional
  only. "Cheap" and "available" are also region-dependent — what's a pantry staple in
  Dhaka differs from Genoa — and the tool doesn't yet take a locale.

### 5.3 `estimate_cost(ingredients, servings=2, currency="USD") -> CostBreakdown`

The only **hybrid** tool. Known ingredients are priced from a built-in USD table; unknown
ones are batched into a single LLM estimation call; everything is converted to the chosen
currency and divided per serving.

- **Pros:** fast and cheap for common ingredients (no model call at all when everything
  is in the table); the single batched fallback avoids one call per unknown item;
  currency conversion is centralized and easy to extend.
- **Cons:** the price table is a small hard-coded snapshot that goes stale and is
  USD-anchored; currency rates are fixed constants, not live FX; quantities are assumed
  "typical recipe amount" rather than parsed from the recipe, so two recipes using the
  same ingredient list cost the same even if portions differ.

### 5.4 `estimate_cooking_time(dish_name, ingredients) -> TimeEstimate`

Estimates prep and cook minutes for a typical home cook and recomputes the total in code
so prep + cook always equals total (a small guard against the model's arithmetic drifting).

- **Pros:** simple, fast, and the code-side total recomputation removes a classic LLM
  arithmetic failure; takes only primitive arguments so the agent fills them easily.
- **Cons:** it estimates from the dish name + ingredients rather than from the actual
  recipe steps, so it can't see, say, an overnight marinade implied by a step. Passing the
  full structured `Recipe` would be more accurate but makes the agent reconstruct a large
  nested object as an argument — a deliberate **accuracy-vs-robustness** trade.

---

## 6. Data models (Pydantic v2)

Every tool returns a Pydantic model defined in `models.py`: `Recipe` (+ `RecipeStep`),
`BudgetBoosters` (+ `BudgetSuggestion`), `CostBreakdown` (+ `IngredientCost`),
`TimeEstimate`, and an internal `PriceGuesses` (+ `PriceGuess`) used only by the cost
tool's fallback.

**Why no default values on response models?** OpenAI structured outputs work best when
every field is required (the strict schema marks all keys required). Keeping response
models default-free avoids schema friction with `client.beta.chat.completions.parse`.

- **Pros:** validation happens automatically; the agent's final synthesis consumes typed
  data, not strings; the models double as living documentation of each tool's contract.
- **Cons:** all-required fields mean the model must always produce every field, which can
  force slightly awkward filler on optional-feeling data; schema changes ripple through
  any code that reads the models.

---

## 7. Control flow, end to end

1. User enters ingredients (and optionally a currency / serving count) in `main.py`.
2. `Runner.run(recipe_agent, user_input)` hands control to the agent.
3. The agent calls `create_strict_recipe`, then `suggest_budget_boosters`, then
   `estimate_cost`, then `estimate_cooking_time` (order guided by its instructions).
4. Each tool runs its own logic — three call the model with a Pydantic `response_format`,
   one mostly reads a table.
5. The agent receives all four structured results and writes a single sectioned answer.
6. `main.py` prints `result.final_output` and loops for the next request.

---

## 8. Setup & run

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env          # then add your OPENAI_API_KEY
python main.py
```

Example:

```
Ingredients > eggs, rice, onion, oil, salt for 4 people, costs in BDT

The Dish — Onion Fried Rice
A fast, savory one-pan rice...
Steps: 1) ... 2) ...
Budget boosters: garlic, soy sauce, chili flakes — small cost, big lift
Approximate cost: ~124 BDT total (~31 BDT / serving)
Estimated time to make: ~22 min (10 prep + 12 cook)
```

---

## 9. Configuration

| Where | Knob | Notes |
|-------|------|-------|
| `tools.py` | `MODEL` | Defaults to `gpt-4o-mini`; swap for any chat model that supports structured outputs. |
| `tools.py` | `PRICE_TABLE_USD` | Add/adjust per-ingredient USD prices. |
| `tools.py` | `CURRENCY_RATES` | Static USD→X rates; replace with a live FX call for accuracy. |
| `recipe_agent.py` | `INSTRUCTIONS` | Controls call order and output formatting. |
| `.env` | `OPENAI_API_KEY` | Required. |

---

## 10. Honest limitations

- **Soft constraints.** "Strict ingredients" is prompt-enforced, not validated in code.
- **Estimates, not facts.** Costs and times are approximations; treat them as directional.
- **Stale data.** Price table and FX rates are hard-coded snapshots.
- **No locale awareness.** "Cheap" and "available" don't yet adapt to your region.
- **Non-deterministic.** As an autonomous agent it may occasionally skip or reorder a tool.
- **No memory.** Each run is independent; there's no conversation history or user profile.

---

## 11. Cost, latency & security notes

- **Token cost:** a full run is the agent's planning calls plus up to three in-tool model
  calls. The cost tool deliberately avoids a model call when all ingredients are known.
- **Latency:** dominated by the number of sequential model round-trips; batching the
  unknown-price estimation into one call is a conscious latency optimization.
- **Secrets:** the API key is read from `.env` via `python-dotenv` and never hard-coded;
  keep `.env` out of version control.
- **Tracing:** the Agents SDK emits traces by default; disable via its tracing controls if
  you don't want runs logged.

---

## 12. What makes this project interesting

- **Two-level model use.** It cleanly separates *deciding what to do* (the agent) from
  *doing it* (tools that themselves call the model). That mirror-of-mirrors structure is
  the heart of modern agent design and is easy to see here in one small codebase.
- **Constraint-at-the-source.** The strict-ingredients rule shows that the right place to
  enforce a constraint is often *inside the tool*, not in the orchestrator — a transferable
  lesson for any agent that must respect hard rules.
- **A genuinely hybrid tool.** `estimate_cost` is a clear, honest example of *not* using
  the LLM when a lookup is cheaper, and using it *only* for the gap. Knowing when **not**
  to call the model is an underrated engineering skill.
- **Visible trade-offs.** The time-tool's "simple args vs. richer input" choice and the
  models' "all-required fields" choice are real design tensions, documented rather than
  hidden — which makes the project a good study piece, not just a demo.
- **Small surface, full pattern.** In ~four short files it exercises orchestration,
  function-calling schemas, structured outputs, and deterministic/LLM blending — the same
  ingredients (fittingly) as much larger production agents.

---

## 13. Extension roadmap

- **Hard validation:** reject any recipe containing an off-list ingredient (turn the soft
  constraint into a guarded one).
- **Real prices & FX:** swap the static table and rates for live APIs; parse quantities
  from recipe steps for true portion-based costing.
- **Locale-aware suggestions:** pass a region so "cheap/available" reflects your market.
- **HTTP service:** wrap `run_once()` in a FastAPI endpoint + Dockerfile (same pattern as
  the Bangla Order Agent) for a deployable API.
- **New tools:** nutrition estimate, dietary guardrail (vegan/halal), shopping-list export.
- **Evals:** add an LLM-as-judge test that checks recipes never use off-list ingredients.

---

## 14. File map

```
recipeforge/
├── models.py          # Pydantic v2 models for every tool's output
├── tools.py           # the four @function_tool definitions + price table
├── recipe_agent.py    # Agent: tools + orchestration instructions
├── main.py            # interactive CLI (Runner.run loop)
├── requirements.txt
├── .env.example
└── README.md          # this file
```