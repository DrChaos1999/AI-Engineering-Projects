"""Pydantic contracts shared between CrewAI tasks and the application."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class FeatureRequirement(BaseModel):
    """One feature that the proposed AI application should contain."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="A concise, professional feature name.",
    )
    description: str = Field(
        ...,
        min_length=10,
        description="What the feature does for the user or system.",
    )
    priority: Literal["must_have", "should_have", "nice_to_have"] = Field(
        ...,
        description="The implementation priority of the feature.",
    )
    reason: str = Field(
        ...,
        min_length=10,
        description="Why the feature is useful for this project.",
    )


class ProjectRequirements(BaseModel):
    """Structured specification produced by the requirements analyst."""

    project_title: str = Field(..., min_length=3, max_length=150)
    problem_statement: str = Field(
        ...,
        min_length=30,
        description="The concrete problem the application solves.",
    )
    target_users: list[str] = Field(..., min_length=1)
    core_features: list[FeatureRequirement] = Field(
        ...,
        min_length=3,
        max_length=6,
    )
    data_inputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(..., min_length=2)

    @field_validator("target_users", "data_inputs", "constraints", "success_metrics")
    @classmethod
    def remove_empty_list_items(cls, values: list[str]) -> list[str]:
        """Strip whitespace and remove empty strings from string lists."""

        cleaned = [value.strip() for value in values if value.strip()]
        return list(dict.fromkeys(cleaned))


class ArchitectureComponent(BaseModel):
    """One major component in the proposed software architecture."""

    name: str = Field(..., min_length=2)
    responsibility: str = Field(..., min_length=10)
    technology: str = Field(..., min_length=2)
    communicates_with: list[str] = Field(default_factory=list)


class Milestone(BaseModel):
    """One implementation milestone in the project roadmap."""

    week: int = Field(..., ge=1, le=8)
    goal: str = Field(..., min_length=5)
    deliverables: list[str] = Field(..., min_length=1)


class ProjectPlan(BaseModel):
    """Final architecture and implementation plan."""

    project_name: str = Field(..., min_length=3, max_length=150)
    summary: str = Field(..., min_length=30)
    architecture: list[ArchitectureComponent] = Field(..., min_length=3)
    request_flow: list[str] = Field(..., min_length=3)
    api_endpoints: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(..., min_length=3)
    milestones: list[Milestone] = Field(..., min_length=3)
    testing_strategy: list[str] = Field(..., min_length=2)
    risks: list[str] = Field(default_factory=list)
    github_deliverables: list[str] = Field(..., min_length=3)
    resume_bullet: str = Field(..., min_length=30)
