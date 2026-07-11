"""Application entry point for the AI Project Planner crew."""

from pathlib import Path
from typing import Any

from ai_project_planner.crew import AIProjectPlannerCrew
from ai_project_planner.schemas import ProjectPlan, ProjectRequirements


OUTPUT_DIRECTORY = Path("output")


def build_inputs() -> dict[str, str]:
    """Return the values inserted into the YAML task templates."""

    return {
        "project_idea": (
            "Build an AI assistant for predictive maintenance of pneumatic "
            "industrial systems. It should analyze equipment manuals, sensor "
            "alerts, and maintenance history to suggest likely faults and "
            "recommended maintenance actions."
        ),
        "current_skills": (
            "Python, machine learning, FastAPI, Pydantic, LangChain, RAG, "
            "SQLite, PostgreSQL, Streamlit, Git, and GitHub"
        ),
        "time_budget": "Four weeks with approximately two hours per day",
    }


def build_markdown_report(plan: ProjectPlan) -> str:
    """Convert a validated project plan into a readable Markdown report."""

    lines: list[str] = [
        f"# {plan.project_name}",
        "",
        "## Project Summary",
        "",
        plan.summary,
        "",
        "## Architecture",
        "",
    ]

    for component in plan.architecture:
        lines.extend(
            [
                f"### {component.name}",
                "",
                f"**Responsibility:** {component.responsibility}",
                "",
                f"**Technology:** {component.technology}",
                "",
                (
                    "**Communicates with:** "
                    + ", ".join(component.communicates_with)
                    if component.communicates_with
                    else "**Communicates with:** None"
                ),
                "",
            ]
        )

    lines.extend(["## Request Flow", ""])
    for index, step in enumerate(plan.request_flow, start=1):
        lines.append(f"{index}. {step}")

    lines.extend(["", "## API Endpoints", ""])
    if plan.api_endpoints:
        lines.extend(f"- `{endpoint}`" for endpoint in plan.api_endpoints)
    else:
        lines.append("- No API endpoints were recommended.")

    lines.extend(["", "## Technology Stack", ""])
    lines.extend(f"- {technology}" for technology in plan.technology_stack)

    lines.extend(["", "## Implementation Milestones", ""])
    for milestone in sorted(plan.milestones, key=lambda item: item.week):
        lines.extend([f"### Week {milestone.week}: {milestone.goal}", ""])
        lines.extend(f"- {deliverable}" for deliverable in milestone.deliverables)
        lines.append("")

    lines.extend(["## Testing Strategy", ""])
    lines.extend(f"- {item}" for item in plan.testing_strategy)

    lines.extend(["", "## Risks", ""])
    if plan.risks:
        lines.extend(f"- {risk}" for risk in plan.risks)
    else:
        lines.append("- No major risks were identified.")

    lines.extend(["", "## GitHub Deliverables", ""])
    lines.extend(f"- {item}" for item in plan.github_deliverables)

    lines.extend(
        [
            "",
            "## Résumé Bullet",
            "",
            f"> {plan.resume_bullet}",
            "",
        ]
    )

    return "\n".join(lines)


def save_outputs(result: Any) -> tuple[Path, Path, Path]:
    """Validate and save both task outputs and the final Markdown report."""

    if not result.tasks_output or len(result.tasks_output) < 2:
        raise RuntimeError("The crew did not return both expected task outputs.")

    requirements = result.tasks_output[0].pydantic
    plan = result.pydantic

    if not isinstance(requirements, ProjectRequirements):
        raise TypeError(
            "The first task did not return a valid ProjectRequirements model."
        )

    if not isinstance(plan, ProjectPlan):
        raise TypeError("The final task did not return a valid ProjectPlan model.")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    requirements_path = OUTPUT_DIRECTORY / "project_requirements.json"
    plan_path = OUTPUT_DIRECTORY / "project_plan.json"
    markdown_path = OUTPUT_DIRECTORY / "project_plan.md"

    requirements_path.write_text(
        requirements.model_dump_json(indent=2),
        encoding="utf-8",
    )
    plan_path.write_text(
        plan.model_dump_json(indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        build_markdown_report(plan),
        encoding="utf-8",
    )

    return requirements_path, plan_path, markdown_path


def run() -> None:
    """Run the CrewAI workflow and save its validated outputs."""

    result = AIProjectPlannerCrew().crew().kickoff(inputs=build_inputs())

    requirements_path, plan_path, markdown_path = save_outputs(result)

    print("\nCrew execution completed successfully.")
    print(f"Requirements: {requirements_path.resolve()}")
    print(f"Project plan: {plan_path.resolve()}")
    print(f"Markdown report: {markdown_path.resolve()}")

    if result.token_usage is not None:
        print("\nToken usage:")
        print(result.token_usage)


if __name__ == "__main__":
    run()
