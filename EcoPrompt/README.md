# EcoPrompt — Energy-Aware Prompt Optimization

> **Agentic pipeline that compresses verbose prompts to cut tokens, then
> measures and tracks the resulting savings in tokens, cost, estimated energy,
> and CO₂e across multiple OpenAI models — logged to MLflow and compared with
> proper statistics.**

---

## The Idea in One Example

| | Prompt | Tokens |
|---|---|---|
| **Before** | `Can you please write me a CV of a machine learning engineer for me? Thank you so much!` | 22 |
| **After** | `Write me a CV for a machine learning engineer.` | 10 |

Same answer. **~40% fewer input tokens.** Fewer tokens = less electricity consumed
by the AI model. At one query the saving is tiny. At millions of API calls per day
it becomes real money and measurable carbon.

---

## Table of Contents

1. [The Honest Scientific Framing](#1-the-honest-scientific-framing)
2. [What the Project Does](#2-what-the-project-does)
3. [The Four Compression Techniques](#3-the-four-compression-techniques)
4. [The Energy Model — How It Works](#4-the-energy-model--how-it-works)
5. [Custom Agentic Tools](#5-custom-agentic-tools)
6. [File Structure and What Each File Does](#6-file-structure-and-what-each-file-does)
7. [Results](#7-results)
8. [Production Scale Projection](#8-production-scale-projection)
9. [MLflow — The MLOps Platform](#9-mlflow--the-mlops-platform)
10. [Statistical Testing](#10-statistical-testing)
11. [How to Run](#11-how-to-run)
12. [Limitations and How to Defend Them](#12-limitations-and-how-to-defend-them)
13. [Natural Extensions](#13-natural-extensions)

---

## 1. The Honest Scientific Framing

Three ground rules govern every number in this repository:

**Rule 1 — Tokens are measured. Energy is modelled.**
Token counts are exact via `tiktoken` (the same tokeniser OpenAI uses internally).
Energy cannot be measured from outside OpenAI's servers, so it is estimated using
a transparent physics-based formula. Every assumption lives in `config.yaml` — no
magic numbers, nothing hidden.

**Rule 2 — The answer usually costs more energy than the question.**
This is the non-obvious result most similar projects miss. Reading your prompt
(*prefill*) runs the GPU very efficiently in one big parallel matrix multiply.
Generating the answer one token at a time (*decode*) is memory-bottlenecked and
far less efficient. If your prompt is 22 tokens and the answer is 450 tokens,
compressing the prompt saves little energy in absolute terms. The project makes
this visible rather than hiding it — and it points to where compression actually
pays: long, **reused** inputs like system prompts, RAG context, and few-shot
blocks sent on every API call.

**Rule 3 — A shorter prompt that breaks the task is not efficiency. It is data loss.**
Every compressed prompt is evaluated by an LLM-as-judge for intent preservation.
Results are plotted as token-reduction versus quality-retained — a Pareto frontier
— so the trade-off is always visible.

---

## 2. What the Project Does

For a benchmark set of 11 verbose prompts, it runs a grid of
**prompts × techniques × downstream models** (176 cells total) and records per cell:

| Metric | How it is obtained |
|---|---|
| Original and optimized token counts, reduction % | Measured exactly via `tiktoken` |
| Optimizer overhead tokens | Measured — compression costs tokens too |
| Energy before / after / saved (Wh), reduction % | Modelled via `energy_model.py` |
| Cost before / after / saved (USD) | Published OpenAI pricing × token counts |
| CO₂e saved (grams) | Energy saved × grid carbon intensity |
| Quality preserved (0 to 1) | Scored by an LLM-as-judge |

**Downstream models benchmarked:** `gpt-4o`, `gpt-4o-mini`, `gpt-4.1-mini`, `gpt-3.5-turbo`

**Optimizer model (does the compression work):** `gpt-4o-mini`

The expensive frontier models are the *targets*. The basic model does the
compression work. This is the correct engineering trade-off.

---

## 3. The Four Compression Techniques

### Baseline (Control)
The prompt is returned unchanged. Every other technique is measured against this.
Optimizer cost: **zero tokens**.

### Rule Based
Deterministic regex stripping of politeness markers and filler phrases — patterns
like `can you please`, `could you please`, `thank you so much`, `kindly`, `for me`.
No LLM calls. Instantaneous. A cleanup pass fixes punctuation artifacts.

- Optimizer cost: **0 tokens** | Token reduction: **~14%** | Quality: **~0.99**

### LLM Rewrite
One API call to `gpt-4o-mini` with a system prompt instructing aggressive
compression while preserving all task constraints. One shot, no retry.

- Optimizer cost: **~200 tokens** | Token reduction: **~28.7%** | Quality: **~0.92**

### Agentic (Main Contribution)
A multi-turn tool-using loop where a basic model acts as an agent that:
1. Calls `rewrite_prompt` tool with strategy `"aggressive"`
2. Calls `count_tokens` to verify the reduction
3. Calls `estimate_energy` to quantify the saving
4. If satisfied, returns the result; if not, retries more aggressively

This is the **"custom tools + agentic AI using basic models"** design pattern
from the project brief. The agent self-corrects across turns.

- Optimizer cost: **~470 tokens** | Token reduction: **~28.7%** | Quality: **~0.92**

---

## 4. The Energy Model — How It Works

**File:** `src/energy_model.py`

### The Formula

```
FLOPs per token  ≈  2 × N     (N = active parameters; 2 = multiply + add per weight)

prefill_energy   = (2 × N × input_tokens)  ÷ (peak_FLOPS × prefill_MFU) × board_W × PUE
decode_energy    = (2 × N × output_tokens) ÷ (peak_FLOPS × decode_MFU)  × board_W × PUE

energy_Wh        = (prefill_energy + decode_energy) ÷ 3600
```

### The Prefill vs Decode Asymmetry

| Phase | What happens | GPU utilisation |
|---|---|---|
| Prefill | All input tokens processed in one large parallel matmul | ~40% (prefill_MFU) |
| Decode | Answer generated one token at a time, weights re-read from memory every step | ~5% (decode_MFU) |

Because `decode_MFU ≪ prefill_MFU`, a single decode token costs roughly **8×
more energy** than a single prefill token. For a 22-token prompt with a 450-token
answer, prefill is ~3% of total energy and decode is ~97%.

### The Constants (all in `config.yaml`)

| Constant | Value | What it represents |
|---|---|---|
| `gpu_peak_flops` | 9.89×10¹⁴ | NVIDIA H100 SXM peak FLOP/s |
| `gpu_power_watts` | 700 | Board power draw under load |
| `prefill_mfu` | 0.40 | GPU efficiency reading the prompt |
| `decode_mfu` | 0.05 | GPU efficiency generating the answer |
| `pue` | 1.20 | Datacentre overhead multiplier |

The per-model `effective_active_params` are **public-domain estimates**, not
official OpenAI figures. Adjust in `config.yaml` to recalibrate.

---

## 5. Custom Agentic Tools

**File:** `src/tools.py`

Three tools are exposed to the agentic optimizer — each is both a real Python
function and an OpenAI function-calling JSON schema.

### `count_tokens`
Counts tokens in a text string for a given model's tokeniser. The agent calls
this after rewriting to verify the actual reduction — it measures, not guesses.

### `estimate_energy`
Returns prefill Joules, decode Joules, and total Wh for given token counts and
model. The agent uses this to quantify whether a rewrite is worth it.

### `rewrite_prompt`
Compresses a prompt using strategy `"concise"` or `"aggressive"`. Returns the
rewritten text plus `tokens_before` and `tokens_after`. The agent calls this
first, checks the result with the other tools, and calls it again if needed.

---

## 6. File Structure and What Each File Does

```
ecoprompt/
│
├── config.yaml              ← single source of truth: models, prices,
│                              energy constants, technique list
├── requirements.txt         ← every package, reproducible installs
├── .env.example             ← shows key names, contains no real secrets
├── .gitignore               ← excludes .env, .venv, mlruns, generated files
├── README.md                ← this file
│
├── data/
│   └── prompts.jsonl        ← 11 benchmark prompts across 4 categories
│
├── src/
│   ├── config.py            ← loads and validates config.yaml
│   ├── token_utils.py       ← exact token counting via tiktoken
│   ├── energy_model.py      ← FLOPs→Wh formula, prefill/decode split ← CORE
│   ├── llm_client.py        ← OpenAI wrapper + deterministic offline mock
│   ├── tools.py             ← 3 custom tools + OpenAI function schemas
│   ├── optimizer.py         ← all 4 techniques incl. agentic tool loop
│   ├── evaluator.py         ← LLM-as-judge quality scoring (0 to 1)
│   ├── tracking.py          ← MLflow logging with CSV fallback
│   ├── experiment.py        ← orchestrates the full benchmark grid
│   ├── stats.py             ← Wilcoxon, ANOVA, Kruskal-Wallis, Pareto
│   └── scale.py             ← projects per-query savings to production volumes
│
├── scripts/
│   ├── run_experiment.py    ← CLI: run benchmark → runs.csv + MLflow
│   └── report.py            ← CLI: stats tables + 4 PNG charts
│
├── artifacts/               ← generated outputs (not committed to git)
│   ├── runs.csv             ← raw results, 176 rows
│   └── fig_*.png            ← 4 comparison charts
│
└── tests/
    └── test_energy_model.py ← 5 unit tests on the energy model
```

### Why the Prompt Set Has Four Categories

| Category | Example | Why included |
|---|---|---|
| **short** | "Can you please write me a CV..." | Big percentage cut, small absolute saving |
| **system** | "You are a helpful support assistant..." | Reused every call — biggest cumulative saving |
| **rag** | "Use this context to answer..." | Wrapper is compressible; retrieved facts are not |
| **fewshot** | "Here are some examples. Example 1:..." | Verbose preambles are good targets |

---

## 7. Results

> Numbers below are from the offline deterministic mock run.
> Run with `OPENAI_API_KEY` set for live figures from real models.

### Token Reduction by Technique

| Technique | Token Reduction | Quality Retained | Optimizer Overhead |
|---|---|---|---|
| agentic | **28.7%** | 0.92 | 467 tokens |
| llm_rewrite | **28.7%** | 0.92 | 201 tokens |
| rule_based | 13.9% | 0.99 | 0 tokens |
| baseline | 0% | 1.00 | 0 tokens |

### Statistical Significance

| Test | Result |
|---|---|
| Wilcoxon (each technique vs baseline) | All significant, **p ≈ 0.001** |
| One-way ANOVA across techniques | **F ≈ 36, p < 0.001** |
| Kruskal–Wallis (non-parametric) | **H ≈ 78, p < 0.001** |

### Estimated Energy per Query by Model

| Model | Energy per query (Wh, modelled) |
|---|---|
| gpt-4o | 0.174 |
| gpt-3.5-turbo | 0.087 |
| gpt-4.1-mini | 0.043 |
| gpt-4o-mini | 0.035 |

### The Central Finding

Token reduction is **14–29%** but per-query energy reduction is only **0.1–0.45%**.
This is the correct, non-obvious result — not a bug. The held-constant 450-token
answer dominates total energy. Any project claiming "29% energy saving" from prompt
compression alone is wrong. This project explains exactly why, and shows where the
real savings are.

### Charts Generated

| File | What it shows |
|---|---|
| `fig_token_reduction.png` | Mean token reduction per technique with 95% CI |
| `fig_energy_by_model.png` | Estimated energy per query across models |
| `fig_pareto.png` | Savings vs quality retained (Pareto frontier) |
| `fig_savings_by_category.png` | Absolute energy saved by prompt category |

---

## 8. Production Scale Projection

**File:** `src/scale.py`

A reused system prompt sent on every API call multiplies the per-query saving
across every request. Compressing once, saving on every call.

Projected annual savings compressing one reused system prompt on `gpt-4o`
(agentic technique):

| Calls per day | kWh saved / year | USD saved / year | tCO₂e saved / year |
|---|---|---|---|
| 10,000 | 4.8 | $252 | 0.002 |
| 100,000 | 47.6 | $2,525 | 0.019 |
| 1,000,000 | 476 | $25,246 | 0.191 |
| 10,000,000 | **4,765** | **$252,458** | **1.906** |

This is why system prompts matter more than short conversational prompts.
The compression cost is paid once. The saving is collected on every request.

---

## 9. MLflow — The MLOps Platform

**File:** `src/tracking.py`

Every cell in the benchmark grid is logged as a separate MLflow run.

**Params logged** (inputs — what was configured):
`technique`, `downstream_model`, `prompt_id`, `category`, `optimizer_model`, `live`

**Metrics logged** (outputs — what was measured):
`orig_tokens`, `opt_tokens`, `token_reduction_pct`, `energy_wh_before`,
`energy_wh_after`, `energy_reduction_pct`, `cost_usd_before`, `cost_saved_usd`,
`gco2e_saved`, `quality_score`, `optimizer_overhead_tokens`

In the MLflow UI at `http://localhost:5000` you can sort all 176 runs by any
metric, filter to a single technique, compare two runs side by side, and view
generated charts — the full MLOps experiment tracking view the project brief asks for.

A CSV fallback writes identical data to `artifacts/runs.csv` when MLflow is not
installed. All statistics and plotting work from either source.

---

## 10. Statistical Testing

**File:** `src/stats.py`

**Paired Wilcoxon Signed-Rank Test** — each technique vs baseline, paired by
prompt ID. Paired because the same 11 prompts are used for every technique,
removing prompt difficulty as a confound. Non-parametric because token counts
are not normally distributed. Result: all techniques significant at p ≈ 0.001.

**One-Way ANOVA** — tests whether mean energy reduction is the same across all
techniques. F ≈ 36, p < 0.001 — the null is rejected.

**Kruskal–Wallis** — non-parametric equivalent of ANOVA. H ≈ 78, p < 0.001.
Agreement between both tests strengthens the conclusion.

**Quality-Weighted Pareto Score** — a single efficiency metric:

```
quality_weighted_reduction = token_reduction_pct × quality_score
```

A 30% cut with 70% quality = 21.0. A 14% cut with 99% quality = 13.86.
This ranks techniques on one defensible axis without ignoring quality.

---

## 11. How to Run

### Offline Mode — No API Key, No Cost

```bash
cd ecoprompt

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the full benchmark (offline mock, 176 cells)
python scripts/run_experiment.py --no-mlflow

# Generate stats tables and 4 charts
python scripts/report.py

# Print production-scale projection
python -m src.scale
```

### Live Mode — Real OpenAI Models + MLflow

```bash
# Set API key
set OPENAI_API_KEY=sk-...          # Windows
export OPENAI_API_KEY=sk-...       # Mac/Linux

# Run benchmark (real API calls)
python scripts/run_experiment.py

# Launch MLflow dashboard
mlflow ui
# Open http://localhost:5000

# Generate report
python scripts/report.py
```

### Tests

```bash
python -m pytest tests/
```

### Windows Quick Reference (every session)

```cmd
cd C:\Projects\ecoprompt
.venv\Scripts\activate
set OPENAI_API_KEY=sk-...
python scripts\run_experiment.py
python scripts\report.py
mlflow ui
```

---

## 12. Limitations and How to Defend Them

**Energy is an estimate, not a measurement.**
OpenAI does not publish per-request energy. Absolute Wh numbers depend on assumed
parameters and hardware constants. The *relative* and *percentage* results are
robust because they are driven by exactly-measured token counts. Always label
energy as "modelled" and lead with token figures.

**Parameter counts are estimates.**
`effective_active_params` in `config.yaml` are public-domain figures, not official
OpenAI disclosures. Update them if you find more authoritative sources — all
downstream figures recalculate automatically.

**Pricing changes frequently.**
Verify `price_in` and `price_out` in `config.yaml` against
https://openai.com/api/pricing before quoting cost numbers in a presentation.

**Mock output differs from live LLM output.**
Offline numbers come from a regex compressor. A real LLM rewrite is cleaner but
occasionally more aggressive — which is what the quality judge catches. Re-run
live for final headline figures.

**Output tokens are held constant by design.**
The answer length is fixed at 450 tokens across all techniques. This isolates
the effect of input compression. If your use case also shortens outputs, model
that separately.

---

## 13. Natural Extensions

**Add LLMLingua as a fifth technique** — Microsoft's open-source learned prompt
compressor gives a published academic baseline to compare your agentic optimizer
against. Much stronger for a research paper than comparing only against a regex stripper.

**Report a sensitivity band** — vary `effective_active_params` ±50% and plot the
energy range. Turns a point estimate into an honest confidence interval.

**Add prompt caching** — for identical system prompts, OpenAI's cached token
feature avoids re-processing entirely. Often a bigger win than compression.

**Harden the quality judge** — replace the single LLM judge call with a fixed
evaluation set of human-rated reference answers. Removes the circularity of using
an LLM to judge another LLM.

**Add a FastAPI endpoint** — wrap the agentic optimizer behind `POST /optimize`
so any application can compress prompts and receive token counts and energy
estimates in the response.

---

## Data Flow — End to End

```
data/prompts.jsonl
        │
        ▼
 experiment.py ──── loops over ────► optimizer.py
        │                                  │
        │                    ┌─────────────┴─────────────┐
        │                    │  baseline  (no change)     │
        │                    │  rule_based (regex)        │
        │                    │  llm_rewrite (one-shot)    │
        │                    │  agentic ◄── tools.py      │
        │                    └─────────────┬─────────────┘
        │                                  │
        │◄──── token_utils.py ─────────────┤  count tokens (exact)
        │◄──── energy_model.py ────────────┤  estimate Wh, cost, CO₂e
        │◄──── evaluator.py ───────────────┤  judge quality (0 to 1)
        │
        ▼
 tracking.py ──► MLflow runs  +  artifacts/runs.csv
        │
        ▼
 stats.py ──► aggregates, Wilcoxon, ANOVA, Kruskal-Wallis, Pareto table
        │
        ▼
 report.py ──► printed tables  +  4 PNG comparison charts
        │
        ▼
 scale.py ──► production-volume projection table
```

---

## Summary of Key Results

| What was measured | Finding |
|---|---|
| Benchmark grid size | 11 prompts × 4 techniques × 4 models = **176 cells** |
| Token reduction — rule_based | **13.9%** (p ≈ 0.001 vs baseline) |
| Token reduction — llm_rewrite | **28.7%** (p ≈ 0.001 vs baseline) |
| Token reduction — agentic | **28.7%** (p ≈ 0.001 vs baseline) |
| Per-query energy reduction | **0.1–0.45%** (decode dominates) |
| Quality retained — rule_based | ~0.99 |
| Quality retained — agentic | ~0.92 |
| Agentic optimizer overhead | ~470 tokens per compression |
| At 10M calls/day on gpt-4o | ~4,765 kWh / ~$252k / ~1.9 tCO₂e per year |

**The central finding:** aggressive compression cuts input tokens by ~29%, but
because the answer dominates energy consumption, the per-query energy saving is
under 0.5%. The economic and environmental case rests entirely on scale and on
compressing **reused inputs** — not one-off short prompts.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| LLM API | OpenAI (`gpt-4o`, `gpt-4o-mini`, `gpt-4.1-mini`, `gpt-3.5-turbo`) |
| Token counting | `tiktoken` |
| MLOps tracking | `mlflow` |
| Data analysis | `pandas`, `numpy` |
| Statistical tests | `scipy` |
| Visualisation | `matplotlib`, `seaborn` |
| Config | `pyyaml` |
| Tests | `pytest` |

---

*Built as an AI Engineering portfolio project demonstrating agentic tool use,
MLOps instrumentation, energy-aware system design, and honest scientific reporting.*