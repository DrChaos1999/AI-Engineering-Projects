"""Tool definitions for the RecipeForge agent.

Four `@function_tool`s:
  1. create_strict_recipe   -> recipe using ONLY the given ingredients
  2. suggest_budget_boosters -> cheap 'least resource' add-ons for more flavor
  3. estimate_cost           -> approximate cost (price table + LLM fallback)
  4. estimate_cooking_time   -> time to make ("build") the dish

Tools 1, 2 and 4 reason with the model via structured outputs; tool 3 is mostly
deterministic (a small price table) with an LLM fallback for unknown items.
"""
from __future__ import annotations

from functools import lru_cache

from openai import OpenAI
from dotenv import load_dotenv
from agents import function_tool

from models import (
    Recipe,
    BudgetBoosters,
    CostBreakdown,
    IngredientCost,
    TimeEstimate,
    PriceGuesses,
)

load_dotenv()

MODEL = "gpt-4o-mini"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Lazily create a single OpenAI client (reads OPENAI_API_KEY from env)."""
    return OpenAI()


def _structured(system: str, user: str, schema):
    """Run one structured-output completion and return the parsed pydantic object."""
    completion = get_client().beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=schema,
    )
    return completion.choices[0].message.parsed


# Rough per-recipe-usage prices in USD for common ingredients.
PRICE_TABLE_USD = {
    "egg": 0.25, "eggs": 0.25, "rice": 0.30, "flour": 0.20, "onion": 0.20,
    "garlic": 0.10, "tomato": 0.40, "potato": 0.30, "oil": 0.15, "butter": 0.40,
    "milk": 0.30, "cheese": 0.80, "chicken": 1.50, "beef": 2.50, "fish": 1.80,
    "salt": 0.02, "sugar": 0.10, "pepper": 0.10, "chili": 0.10, "bread": 0.50,
    "pasta": 0.60, "carrot": 0.20, "spinach": 0.40, "lemon": 0.30, "yogurt": 0.40,
    "beans": 0.50, "lentil": 0.40, "lentils": 0.40, "ginger": 0.10,
    "coriander": 0.15, "cumin": 0.10, "turmeric": 0.08, "corn": 0.30,
}

# Very rough conversion: 1 USD -> X currency.
CURRENCY_RATES = {"USD": 1.0, "EUR": 0.92, "BDT": 118.0, "INR": 83.0, "GBP": 0.78}


@function_tool
def create_strict_recipe(ingredients: list[str], servings: int = 2) -> Recipe:
    """Create a complete recipe using ONLY the provided ingredients.

    The recipe must NOT introduce any ingredient outside the given list. Only water,
    salt and a heat source may be assumed available. Call this first to honor the
    constraint of cooking strictly with what the user has.
    """
    system = (
        "You are a resourceful chef. Build ONE coherent dish using ONLY the "
        "ingredients the user provides. You may assume water, salt and a heat source "
        "are available, but you must NOT add any other ingredient. Number the steps "
        "clearly and give a realistic duration for each."
    )
    user = (
        f"Ingredients available: {', '.join(ingredients)}.\n"
        f"Servings: {servings}.\n"
        "Create the best possible dish using strictly these ingredients."
    )
    return _structured(system, user, Recipe)


@function_tool
def suggest_budget_boosters(ingredients: list[str], cuisine_hint: str = "") -> BudgetBoosters:
    """Suggest a few cheap, low-resource add-on ingredients that most improve the dish.

    These are inexpensive, widely-available 'least resource' items (e.g. garlic, oil,
    chili, herbs, a single spice) chosen for maximum flavor impact per cost.
    """
    system = (
        "You are a chef focused on maximum flavor for minimum cost. Given a set of base "
        "ingredients, suggest 3 to 5 cheap, widely-available add-on ingredients that "
        "would most improve the taste. Prefer pantry staples and spices. For each, give "
        "a short reason, a rough cost in USD, and a flavor impact of low/medium/high."
    )
    user = (
        f"Base ingredients: {', '.join(ingredients)}.\n"
        f"Cuisine hint: {cuisine_hint or 'none'}.\n"
        "Suggest the best budget flavor boosters."
    )
    return _structured(system, user, BudgetBoosters)


@function_tool
def estimate_cost(ingredients: list[str], servings: int = 2, currency: str = "USD") -> CostBreakdown:
    """Estimate the approximate total cost of the given ingredients.

    Common items are priced from a built-in table; unknown items are estimated by the
    model. Returns a per-item breakdown, total, and cost per serving in `currency`
    (supported: USD, EUR, BDT, INR, GBP).
    """
    currency = currency.upper()
    rate = CURRENCY_RATES.get(currency, 1.0)

    known: dict[str, float] = {}
    unknown: list[str] = []
    for raw in ingredients:
        key = raw.strip().lower()
        if key in PRICE_TABLE_USD:
            known[raw] = PRICE_TABLE_USD[key]
        else:
            unknown.append(raw)

    estimated: dict[str, float] = {}
    if unknown:
        guesses = _structured(
            "Estimate a rough per-recipe cost in USD for each ingredient, assuming a "
            "typical amount used in one home recipe.",
            f"Ingredients: {', '.join(unknown)}",
            PriceGuesses,
        )
        estimated = {g.ingredient: g.usd_cost for g in guesses.items}

    items: list[IngredientCost] = []
    total_usd = 0.0
    for raw in ingredients:
        usd = known.get(raw, estimated.get(raw, 0.30))  # 0.30 fallback if model missed one
        total_usd += usd
        items.append(
            IngredientCost(
                ingredient=raw,
                quantity_note="typical recipe amount",
                cost=round(usd * rate, 2),
            )
        )

    total = round(total_usd * rate, 2)
    per_serving = round(total / max(servings, 1), 2)
    return CostBreakdown(
        currency=currency, items=items, total_cost=total, cost_per_serving=per_serving
    )


@function_tool
def estimate_cooking_time(dish_name: str, ingredients: list[str]) -> TimeEstimate:
    """Estimate prep + cook time (minutes) to make ("build") the dish.

    Here 'building the project' means preparing the actual dish, so this returns prep,
    cook, and total minutes for a typical home cook.
    """
    system = (
        "You estimate cooking time. Given a dish name and its ingredients, estimate "
        "realistic prep minutes and cook minutes for a home cook, plus a one-line "
        "breakdown of where the time goes."
    )
    user = f"Dish: {dish_name}\nIngredients: {', '.join(ingredients)}"
    est = _structured(system, user, TimeEstimate)
    est.total_minutes = round(est.prep_minutes + est.cook_minutes, 1)
    return est
