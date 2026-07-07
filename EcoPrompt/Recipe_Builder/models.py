"""Pydantic v2 models for RecipeForge tool inputs/outputs.

All response models keep every field required (no defaults) so they play nicely
with OpenAI structured outputs (`client.beta.chat.completions.parse`).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ---------- Recipe ----------
class RecipeStep(BaseModel):
    step_number: int = Field(..., description="1-indexed order of the step")
    instruction: str = Field(..., description="Clear, single-action instruction")
    duration_minutes: float = Field(..., description="Approx minutes this step takes")


class Recipe(BaseModel):
    dish_name: str
    description: str = Field(..., description="One or two sentence summary of the dish")
    ingredients_used: list[str] = Field(..., description="Only ingredients the user provided")
    steps: list[RecipeStep]
    servings: int


# ---------- Budget boosters ----------
class BudgetSuggestion(BaseModel):
    ingredient: str
    reason: str = Field(..., description="Why this cheap add-on improves the dish")
    approx_cost_usd: float
    flavor_impact: str = Field(..., description="low | medium | high")


class BudgetBoosters(BaseModel):
    suggestions: list[BudgetSuggestion]
    note: str = Field(..., description="One-line overall tip")


# ---------- Cost ----------
class IngredientCost(BaseModel):
    ingredient: str
    quantity_note: str
    cost: float


class CostBreakdown(BaseModel):
    currency: str
    items: list[IngredientCost]
    total_cost: float
    cost_per_serving: float


# ---------- Time ----------
class TimeEstimate(BaseModel):
    prep_minutes: float
    cook_minutes: float
    total_minutes: float
    breakdown: str = Field(..., description="One-line explanation of the estimate")


# ---------- Internal helper (cost estimation of unknown items) ----------
class PriceGuess(BaseModel):
    ingredient: str
    usd_cost: float


class PriceGuesses(BaseModel):
    items: list[PriceGuess]
