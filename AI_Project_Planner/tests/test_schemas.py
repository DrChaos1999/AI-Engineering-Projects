"""Unit tests for the Pydantic data contracts."""

import pytest
from pydantic import ValidationError

from ai_project_planner.schemas import (
    ArchitectureComponent,
    FeatureRequirement,
    Milestone,
    ProjectPlan,
    ProjectRequirements,
)


def valid_requirements() -> ProjectRequirements:
    return ProjectRequirements(
        project_title="Pneumatic Maintenance Copilot",
        problem_statement=(
            "Maintenance teams need faster access to grounded fault-diagnosis "
            "information from manuals and historical maintenance records."
        ),
        target_users=["Maintenance engineer"],
        core_features=[
            FeatureRequirement(
                name="Document ingestion",
                description="Process equipment manuals for later retrieval.",
                priority="must_have",
                reason="The assistant needs grounded maintenance evidence.",
            ),
            FeatureRequirement(
                name="Fault diagnosis",
                description="Suggest likely faults from an equipment alert.",
                priority="must_have",
                reason="Diagnosis is the project's central user value.",
            ),
            FeatureRequirement(
                name="Evidence display",
                description="Return supporting source passages with an answer.",
                priority="should_have",
                reason="Evidence improves trust and enables human verification.",
            ),
        ],
        data_inputs=["Equipment manuals", "Sensor alerts"],
        constraints=["One-developer project"],
        success_metrics=["Retrieval hit rate", "Answer faithfulness"],
    )


def test_project_requirements_accept_valid_data() -> None:
    requirements = valid_requirements()
    assert requirements.project_title == "Pneumatic Maintenance Copilot"
    assert len(requirements.core_features) == 3


def test_project_requires_at_least_three_features() -> None:
    with pytest.raises(ValidationError):
        ProjectRequirements(
            project_title="Small Project",
            problem_statement=(
                "This sufficiently long statement describes a real problem "
                "that the application is intended to solve."
            ),
            target_users=["Engineer"],
            core_features=[
                FeatureRequirement(
                    name="Only feature",
                    description="This is the only feature in the invalid model.",
                    priority="must_have",
                    reason="It exists to demonstrate failed validation.",
                )
            ],
            success_metrics=["Metric one", "Metric two"],
        )


def test_fit_plan_rejects_invalid_week_number() -> None:
    with pytest.raises(ValidationError):
        Milestone(
            week=0,
            goal="Invalid milestone",
            deliverables=["A deliverable"],
        )


def test_project_plan_accepts_valid_structure() -> None:
    plan = ProjectPlan(
        project_name="Pneumatic Maintenance Copilot",
        summary=(
            "A grounded maintenance assistant that retrieves relevant evidence "
            "before suggesting likely faults and maintenance actions."
        ),
        architecture=[
            ArchitectureComponent(
                name="API",
                responsibility="Validate requests and coordinate the workflow.",
                technology="FastAPI",
                communicates_with=["Retrieval service"],
            ),
            ArchitectureComponent(
                name="Retrieval service",
                responsibility="Find relevant passages from equipment manuals.",
                technology="Vector database",
                communicates_with=["API", "LLM"],
            ),
            ArchitectureComponent(
                name="LLM layer",
                responsibility="Generate a grounded structured recommendation.",
                technology="CrewAI-compatible LLM",
                communicates_with=["Retrieval service"],
            ),
        ],
        request_flow=[
            "A user submits an equipment alert.",
            "The retriever finds relevant evidence.",
            "The LLM produces a structured recommendation.",
        ],
        api_endpoints=["POST /diagnose", "GET /health"],
        technology_stack=["Python", "FastAPI", "Pydantic"],
        milestones=[
            Milestone(week=1, goal="Build API", deliverables=["API skeleton"]),
            Milestone(week=2, goal="Add retrieval", deliverables=["Retriever"]),
            Milestone(week=3, goal="Evaluate system", deliverables=["Report"]),
        ],
        testing_strategy=["Unit tests", "RAG evaluation dataset"],
        risks=["Unsupported recommendations"],
        github_deliverables=["Source code", "README", "Evaluation report"],
        resume_bullet=(
            "Built a structured AI maintenance assistant with validated APIs, "
            "retrieval, evaluation, and documented architecture."
        ),
    )

    assert plan.milestones[0].week == 1
