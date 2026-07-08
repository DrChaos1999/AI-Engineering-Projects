"""Command-line entry point for the Facebook post crew."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from crewai import Crew, Process
from dotenv import load_dotenv

from .agents import FacebookMarketingAgents
from .tasks import FacebookMarketingTasks


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _raw(result: object) -> str:
    raw = getattr(result, "raw", None)
    return str(raw if raw is not None else result)


def collect_inputs() -> dict[str, str]:
    print("\nFacebook Post Crew")
    print("=" * 50)
    print("Provide a product, service, organisation, cause, event, or topic.\n")

    return {
        "name": _ask("Name or topic"),
        "website": _ask("Website URL, or write none", "No website provided"),
        "details": _ask(
            "Important details, benefits, proof, offer, restrictions, and context"
        ),
        "audience": _ask("Target audience"),
        "objective": _ask(
            "Campaign objective",
            "Increase awareness and meaningful engagement",
        ),
        "tone": _ask("Tone", "Helpful, confident, and human"),
        "language": _ask("Output language", "English"),
        "cta": _ask("Desired call to action", "Learn more"),
    }


def build_campaign(inputs: dict[str, str]) -> tuple[str, str]:
    agents = FacebookMarketingAgents()
    tasks = FacebookMarketingTasks()

    analyst = agents.product_audience_analyst()
    researcher = agents.facebook_market_researcher()
    strategist = agents.campaign_strategist()
    copywriter = agents.facebook_copywriter()

    product_task = tasks.product_analysis(analyst, inputs)
    competitor_task = tasks.competitor_research(
        researcher,
        inputs,
        context=[product_task],
    )
    strategy_task = tasks.campaign_strategy(
        strategist,
        inputs,
        context=[product_task, competitor_task],
    )
    copy_task = tasks.write_facebook_posts(
        copywriter,
        inputs,
        context=[product_task, competitor_task, strategy_task],
    )

    copy_crew = Crew(
        agents=[analyst, researcher, strategist, copywriter],
        tasks=[product_task, competitor_task, strategy_task, copy_task],
        process=Process.sequential,
        verbose=True,
    )

    copy_result = _raw(copy_crew.kickoff())

    visual_designer = agents.visual_concept_designer()
    creative_director = agents.creative_director()

    visual_task = tasks.visual_concepts(
        visual_designer,
        inputs,
        approved_copy=copy_result,
    )
    review_task = tasks.final_review(
        creative_director,
        inputs,
        approved_copy=copy_result,
        context=[visual_task],
    )

    visual_crew = Crew(
        agents=[visual_designer, creative_director],
        tasks=[visual_task, review_task],
        process=Process.sequential,
        verbose=True,
    )

    final_result = _raw(visual_crew.kickoff())
    return copy_result, final_result


def save_campaign(
    inputs: dict[str, str],
    copy_result: str,
    final_result: str,
) -> Path:
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"facebook_campaign_{timestamp}.md"

    content = f"""# Facebook Campaign: {inputs['name']}

## Campaign Inputs

- **Website:** {inputs['website']}
- **Audience:** {inputs['audience']}
- **Objective:** {inputs['objective']}
- **Tone:** {inputs['tone']}
- **Language:** {inputs['language']}
- **CTA:** {inputs['cta']}

## Copy Crew Output

{copy_result}

## Visual and Creative-Director Output

{final_result}
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def run() -> None:
    load_dotenv()

    inputs = collect_inputs()
    copy_result, final_result = build_campaign(inputs)
    output_path = save_campaign(inputs, copy_result, final_result)

    print("\n" + "#" * 70)
    print("FINAL FACEBOOK CAMPAIGN")
    print("#" * 70)
    print(final_result)
    print(f"\nSaved to: {output_path.resolve()}")


if __name__ == "__main__":
    run()
