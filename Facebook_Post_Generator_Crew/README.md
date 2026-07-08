# Facebook Post Crew

A multi-agent Facebook marketing content generator built with **Python** and **CrewAI**.

The system researches a product or topic, studies the target audience and competitors, develops a campaign strategy, writes three Facebook post options, creates matching visual concepts, and performs a final creative review.

> This project generates Facebook campaign content. It does **not** currently publish posts directly to Facebook.

---

## Table of Contents

- [Project Overview](#project-overview)
- [What the Project Produces](#what-the-project-produces)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [How the Workflow Works](#how-the-workflow-works)
- [Agents](#agents)
- [Tasks](#tasks)
- [APIs and External Services](#apis-and-external-services)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Example Input](#example-input)
- [Generated Output](#generated-output)
- [Error Handling](#error-handling)
- [Current Limitations](#current-limitations)
- [How to Add Facebook Publishing](#how-to-add-facebook-publishing)
- [Possible Future Improvements](#possible-future-improvements)

---

## Project Overview

The Facebook Post Crew is a **multi-agent AI workflow** that automates the planning and creation of Facebook marketing content.

The user supplies information such as:

- Product, service, organisation, event, cause, or topic
- Website
- Important product details
- Target audience
- Campaign objective
- Preferred tone
- Output language
- Desired call to action

The agents then collaborate to create a complete Facebook campaign package.

---

## What the Project Produces

The system generates:

1. Product and audience analysis
2. Competitor and public Facebook research
3. Facebook campaign strategy
4. Three Facebook post variations
5. Three matching visual concepts
6. Image-generation prompts
7. Creative-director review
8. Recommended final post and visual combination
9. Pre-publication checklist
10. Markdown campaign report

The generated report is saved inside:

```text
outputs/facebook_campaign_YYYYMMDD_HHMMSS.md
```

---

## Architecture

The system is divided into two CrewAI crews.

```text
User Input
    |
    v
COPY CREW
    |
    |-- Product and Audience Analyst
    |-- Facebook Market Researcher
    |-- Facebook Campaign Strategist
    `-- Senior Facebook Copywriter
    |
    v
Three Facebook post options
    |
    v
VISUAL CREW
    |
    |-- Facebook Visual Concept Designer
    `-- Chief Creative Director
    |
    v
Final reviewed Facebook campaign
```

### Copy Crew

The Copy Crew handles:

- Product understanding
- Audience analysis
- Competitor research
- Facebook content research
- Campaign strategy
- Facebook post writing

### Visual Crew

The Visual Crew handles:

- Visual concept development
- Image-generation prompts
- Copy and visual alignment
- Final editorial review
- Publication checklist

Both crews use:

```python
Process.sequential
```

This ensures that tasks run in a controlled order.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| CrewAI | Multi-agent orchestration |
| CrewAI Tools | Website scraping and search tools |
| LLM provider API | Agent reasoning and content generation |
| Serper API | Web and publicly indexed Facebook search |
| Requests | HTTP requests to the Serper API |
| python-dotenv | Loading API keys from `.env` |
| uv | Dependency and virtual-environment management |
| Markdown | Saving final campaign reports |

---

## Project Structure

```text
facebook_post_crew/
|
|-- .env.example
|-- .gitignore
|-- pyproject.toml
|-- requirements.txt
|-- README.md
|
|-- outputs/
|   `-- .gitkeep
|
`-- src/
    `-- facebook_post_crew/
        |-- __init__.py
        |-- agents.py
        |-- tasks.py
        |-- main.py
        |
        `-- tools/
            |-- __init__.py
            `-- facebook_search_tool.py
```

### Main Files

#### `main.py`

The main entry point of the application.

It:

1. Loads environment variables
2. Collects user input
3. Creates the agents and tasks
4. Runs the Copy Crew
5. Passes the copy result to the Visual Crew
6. Runs the final review
7. Prints the result
8. Saves the campaign as Markdown

#### `agents.py`

Contains all CrewAI agent definitions.

#### `tasks.py`

Contains all task definitions, descriptions, expected outputs, and task context relationships.

#### `facebook_search_tool.py`

Contains a custom CrewAI tool for searching publicly indexed Facebook content through the Serper API.

#### `.env.example`

Shows the environment variables required by the project.

#### `pyproject.toml`

Defines:

- Project metadata
- Python version
- Dependencies
- Build configuration
- Command-line entry point

---

## How the Workflow Works

### Step 1: Collect User Input

The command-line program asks for:

```text
Name or topic
Website
Important details
Target audience
Campaign objective
Tone
Output language
Call to action
```

The answers are stored in a dictionary and passed to the agents.

### Step 2: Product and Audience Analysis

The Product and Audience Analyst studies:

- The product or topic
- The supplied website
- Features and benefits
- Target customer needs
- Objections
- Differentiators
- Available proof
- Unsupported claims that must be avoided
- Brand voice
- Communication risks

### Step 3: Competitor and Facebook Research

The Facebook Market Researcher examines:

- Competitors
- Comparable products
- Similar Facebook pages
- Common campaign promises
- Audience language
- Recurring content patterns
- Overused angles
- Opportunities for differentiation
- Research limitations

When available, the agent can use:

- General web search
- Public Facebook search
- Website scraping

### Step 4: Campaign Strategy

The strategist converts the research into:

- Core campaign promise
- Audience insight
- Supporting reasons
- Message hierarchy
- Emotional angle
- CTA logic
- Visual direction
- Three campaign concepts
- Claims to avoid
- A/B testing recommendation

### Step 5: Facebook Copywriting

The copywriter creates three different post formats.

#### Story-Led Organic Post

Designed to create emotional connection through a relatable story.

#### Benefit-Led Promotional Post

Designed to communicate benefits and support conversion.

#### Community or Conversation Post

Designed to encourage comments, questions, and interaction.

Each post contains:

- Strategic label
- Opening hook
- Complete body copy
- Call to action
- Zero to five hashtags
- Suggested first comment
- Short strategic rationale

### Step 6: Visual Concept Development

The visual designer creates one matching concept for each post.

Each concept includes:

- Concept title
- Communication goal
- Scene
- Subject
- Composition
- Camera framing
- Environment
- Lighting
- Mood
- Colour guidance
- Product placement
- Text-overlay guidance
- Accessibility note
- Image-generation prompt
- Negative prompt

The project generates visual instructions. It does not generate the image itself.

### Step 7: Creative Review

The Chief Creative Director reviews:

- Factual accuracy
- Tone
- CTA quality
- Strategic consistency
- Copy and visual alignment
- Repetition
- Unsupported claims
- Facebook suitability

The final review contains:

- Quality assessment
- Required corrections
- Recommended Facebook post
- Recommended visual prompt
- Two alternative combinations
- Pre-publication checklist

### Step 8: Save the Campaign

The final campaign is saved as a Markdown file.

Example:

```text
outputs/facebook_campaign_20260708_143521.md
```

---

## Agents

The project contains six specialised agents.

### 1. Product and Audience Analyst

**Role**

```text
Product and Audience Analyst
```

**Responsibilities**

- Understand the offer
- Analyse the target audience
- Identify benefits and differentiators
- Find communication opportunities
- Detect unsupported claims
- Establish brand voice guidance

### 2. Facebook Market Researcher

**Role**

```text
Facebook Market Researcher
```

**Responsibilities**

- Research competitors
- Study public Facebook content patterns
- Identify audience language
- Find campaign gaps
- Separate evidence from inference
- Report search limitations

### 3. Facebook Campaign Strategist

**Role**

```text
Facebook Campaign Strategist
```

**Responsibilities**

- Create campaign positioning
- Define message hierarchy
- Select the emotional angle
- Develop three post concepts
- Choose CTA logic
- Recommend visual direction
- Define claim boundaries

### 4. Senior Facebook Copywriter

**Role**

```text
Senior Facebook Copywriter
```

**Responsibilities**

- Write three complete Facebook posts
- Adapt language and tone
- Create strong hooks
- Use clear formatting
- Avoid fake urgency and unsupported claims
- Add appropriate CTAs and first comments

### 5. Facebook Visual Concept Designer

**Role**

```text
Facebook Visual Concept Designer
```

**Responsibilities**

- Convert copy into visual concepts
- Design scenes and compositions
- Define lighting, mood, and framing
- Write image-generation prompts
- Add negative prompts
- Consider accessibility and text readability

### 6. Chief Creative Director

**Role**

```text
Chief Creative Director
```

**Responsibilities**

- Review the campaign
- Correct weak or inconsistent content
- Select the best post
- Select the best visual direction
- Approve alternatives
- Provide the final checklist

---

## Tasks

The project contains six CrewAI tasks.

```text
1. Product analysis
2. Competitor research
3. Campaign strategy
4. Facebook post writing
5. Visual concept creation
6. Final creative review
```

Each task contains:

```python
Task(
    description="...",
    expected_output="...",
    agent=agent,
    context=[...],
)
```

### Why `expected_output` Is Used

The `expected_output` field tells the agent exactly what kind of result is required.

This improves:

- Structure
- Consistency
- Relevance
- Output quality

### Why Task Context Is Used

Later tasks receive the output of earlier tasks.

Example:

```python
competitor_task = tasks.competitor_research(
    researcher,
    inputs,
    context=[product_task],
)
```

The strategy task receives both research tasks:

```python
context=[product_task, competitor_task]
```

The copywriting task receives:

```python
context=[
    product_task,
    competitor_task,
    strategy_task,
]
```

This creates a controlled information flow.

```text
Product Analysis
      |
      v
Competitor Research
      |
      v
Campaign Strategy
      |
      v
Facebook Copywriting
```

---

## APIs and External Services

The project uses two main API categories.

---

### 1. LLM Provider API

CrewAI agents require a Large Language Model.

The model is configured in `agents.py`:

```python
self.llm = LLM(
    model=model,
    temperature=temperature,
)
```

The model name is read from `.env`:

```env
MODEL=openai/gpt-4o-mini
```

When using an OpenAI model, add:

```env
OPENAI_API_KEY=your_openai_api_key
```

The LLM API powers:

- Product analysis
- Audience reasoning
- Competitor interpretation
- Campaign strategy
- Facebook copywriting
- Visual prompt generation
- Creative review

CrewAI handles the provider request through its LLM abstraction.

```text
CrewAI Agent
    |
    v
CrewAI LLM Wrapper
    |
    v
Model Provider API
    |
    v
Agent Response
```

#### Alternative Providers

The project can use other providers supported by the installed CrewAI version.

Possible examples include:

```env
MODEL=anthropic/claude-model-name
```

```env
MODEL=gemini/gemini-model-name
```

```env
MODEL=ollama/llama3.2
```

The correct provider API key and model identifier must be configured for the selected model.

---

### 2. Serper API

The project uses the Serper API for:

- Google search
- Competitor research
- Public Facebook discovery
- Public Facebook content research

The API key is configured with:

```env
SERPER_API_KEY=your_serper_api_key
```

The custom Facebook search tool sends a POST request to:

```text
https://google.serper.dev/search
```

Example request:

```python
response = requests.post(
    "https://google.serper.dev/search",
    headers={
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    },
    json={
        "q": f"site:facebook.com {search_query}",
        "num": 8,
    },
    timeout=30,
)
```

Example search body:

```json
{
  "q": "site:facebook.com AI marketing tools",
  "num": 8
}
```

The custom tool formats each result using:

```text
Title
Link
Snippet
```

---

### Public Facebook Search Tool

The custom tool is defined with:

```python
@tool("Search public Facebook content")
def search_public_facebook(query: str) -> str:
```

The CrewAI `@tool` decorator turns the Python function into an agent-usable tool.

The tool changes a normal query into a Facebook-restricted search.

```text
Original query:
AI prompt optimisation software

Search query:
site:facebook.com AI prompt optimisation software
```

#### Facebook Search Limitations

This search method can generally find only content that is:

- Public
- Indexed by search engines
- Accessible without private authentication

It cannot reliably access:

- Private profiles
- Private groups
- Closed groups
- Friends-only posts
- Login-protected posts
- Unindexed content
- Private engagement information

The agents are instructed not to pretend that they have searched the entire Facebook platform.

---

### Website Scraping Tool

The project uses:

```python
ScrapeWebsiteTool()
```

from `crewai_tools`.

It can help extract:

- Product descriptions
- Features
- Benefits
- Pricing
- Testimonials
- FAQs
- Brand language
- Claims
- Contact information

The tool is available to relevant research and strategy agents.

---

### Does the Project Use the Facebook Graph API?

No.

The current project does not use:

- Meta Graph API
- Facebook Pages API
- Facebook Marketing API
- Instagram Graph API

Therefore, it cannot currently:

- Publish a Facebook post
- Upload an image to Facebook
- Schedule posts
- Read Facebook Page insights
- Manage comments
- Run Facebook advertisements

It is a research, strategy, writing, and visual-planning system.

---

## Environment Variables

Create a `.env` file based on `.env.example`.

```env
MODEL=openai/gpt-4o-mini
TEMPERATURE=0.7

OPENAI_API_KEY=
SERPER_API_KEY=
```

### `MODEL`

Selects the LLM used by CrewAI.

### `TEMPERATURE`

Controls creativity and variability.

Lower value:

```env
TEMPERATURE=0.2
```

Usually produces more predictable output.

Higher value:

```env
TEMPERATURE=0.9
```

Usually produces more varied and creative output.

### `OPENAI_API_KEY`

Required when using an OpenAI model.

### `SERPER_API_KEY`

Optional but recommended for live competitor and public Facebook research.

Without a Serper key, the project can still run, but its external research will be limited.

---

## Installation

### Requirements

- Python 3.10 or newer
- `uv` or `pip`
- LLM provider API key
- Optional Serper API key

---

### Installation with `uv`

Clone or download the project, then open PowerShell inside the project folder.

```powershell
cd facebook_post_crew
```

Copy the environment example:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your API keys.

Install dependencies:

```powershell
uv sync
```

---

### Installation with `pip`

```powershell
cd facebook_post_crew
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

Add your API keys to `.env`.

---

## Running the Project

With `uv`:

```powershell
uv run facebook-post-crew
```

Alternative command:

```powershell
uv run python -m facebook_post_crew.main
```

With an activated `pip` environment:

```powershell
facebook-post-crew
```

---

## Example Input

```text
Name or topic:
EcoPrompt AI

Website:
https://example.com

Important details:
An AI application that helps businesses reduce LLM token cost and response time.

Target audience:
Startup founders and AI engineers in Bangladesh.

Campaign objective:
Generate free-trial registrations.

Tone:
Professional, helpful, and practical.

Output language:
English

Desired call to action:
Start your free trial.
```

---

## Generated Output

The final Markdown report contains:

```markdown
# Facebook Campaign: Product Name

## Campaign Inputs

- Website
- Audience
- Objective
- Tone
- Language
- CTA

## Copy Crew Output

- Product and audience analysis
- Competitor research
- Campaign strategy
- Three Facebook posts

## Visual and Creative-Director Output

- Three visual concepts
- Image prompts
- Negative prompts
- Recommended final combination
- Alternative combinations
- Pre-publication checklist
```

---

## Error Handling

The custom Facebook search tool handles missing API keys.

```python
if not api_key:
    return (
        "Facebook search was skipped because "
        "SERPER_API_KEY is not configured."
    )
```

It handles network and HTTP errors:

```python
except requests.RequestException as exc:
    return f"Facebook search failed: {exc}"
```

It also handles invalid JSON:

```python
except ValueError:
    return "Facebook search failed because the provider returned invalid JSON."
```

This allows the project to continue running even when external research is unavailable.

---

## Current Limitations

The current project does not include:

- Direct Facebook publishing
- Meta Graph API integration
- Image generation
- Streamlit interface
- Database storage
- User authentication
- Campaign scheduling
- Facebook analytics
- Engagement tracking
- Persistent agent memory
- Structured JSON output
- Cost monitoring
- Human approval interface

The system is designed primarily as a Facebook campaign research and generation pipeline.

---

## How to Add Facebook Publishing

To publish to a Facebook Page, the project would need the **Meta Graph API**.

A text post is conceptually published through:

```http
POST /{page-id}/feed
```

Example Python structure:

```python
import requests

url = f"https://graph.facebook.com/vXX.X/{page_id}/feed"

payload = {
    "message": facebook_post,
    "access_token": page_access_token,
}

response = requests.post(
    url,
    data=payload,
    timeout=30,
)

response.raise_for_status()
```

A photo post would use a Page photos endpoint.

Publishing requires:

- Meta developer account
- Meta application
- Facebook Page
- Page access token
- Required permissions
- Secure token storage
- Possible Meta app review
- Manual approval before publication

A human approval step should be placed before any publishing action.

---

## Possible Future Improvements

A production version could include:

```text
User or Streamlit Interface
          |
          v
CrewAI Research and Writing Crew
          |
          v
Structured Campaign Output
          |
          v
Human Approval
     |          |
     |          `-- Reject and Revise
     |
     `-- Approve
          |
          v
Image Generation API
          |
          v
Meta Graph API Publishing
          |
          v
Facebook Page Post
          |
          v
Insights and Analytics
          |
          v
Performance Review Agent
```

Possible additions:

- Streamlit dashboard
- Pydantic structured output
- Image-generation API
- Meta Graph API publishing
- Post scheduling
- Approval workflow
- Campaign database
- A/B testing
- Engagement analytics
- Cost tracking
- Prompt and output history
- Multi-language campaigns
- Automatic performance summaries
- Human feedback loop

---

## Summary

The Facebook Post Crew combines:

- CrewAI agents
- Sequential multi-agent workflows
- LLM reasoning
- Serper web research
- Public Facebook search
- Website scraping
- Facebook copywriting
- Visual prompt development
- Creative review
- Markdown report generation

It is suitable as a portfolio project for learning:

- Agentic AI
- Tool-using agents
- Multi-agent orchestration
- Marketing automation
- API integration
- Prompt engineering
- Social-media content pipelines
