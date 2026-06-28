"""RecipeForge CLI — run the agent interactively.

Usage:
    python main.py
"""
from __future__ import annotations

import asyncio

from dotenv import load_dotenv
from agents import Runner

from recipe_agent import recipe_agent

load_dotenv()

BANNER = "RecipeForge — agentic recipe builder (type 'quit' to exit)"


async def run_once(user_input: str) -> str:
    result = await Runner.run(recipe_agent, user_input)
    return result.final_output


async def main() -> None:
    print(BANNER)
    print("Tip: enter ingredients like 'eggs, rice, onion, oil' or a full request.\n")
    while True:
        try:
            user_input = input("Ingredients > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input or user_input.lower() in {"quit", "exit"}:
            print("Bye!")
            break
        print("\n...cooking up something...\n")
        print(await run_once(user_input))
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
