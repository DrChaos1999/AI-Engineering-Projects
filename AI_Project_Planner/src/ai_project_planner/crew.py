"""CrewAI agents, tasks, and orchestration."""

import os
from functools import lru_cache

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from ai_project_planner.schemas import ProjectPlan, ProjectRequirements


load_dotenv()


@lru_cache(maxsize=1)
def build_llm() -> LLM:
    """Create one reusable CrewAI LLM configuration."""

    model_name = os.getenv("MODEL", "openai/gpt-4o-mini").strip()

    if not model_name:
        raise RuntimeError(
            "MODEL is empty. Add a supported model name to your .env file."
        )

    return LLM(
        model=model_name,
        temperature=0,
    )


@CrewBase
class AIProjectPlannerCrew:
    """Turn an AI project idea into validated requirements and a build plan."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def requirements_analyst(self) -> Agent:
        """Create the agent that defines what should be built."""

        return Agent(
            config=self.agents_config["requirements_analyst"],
            llm=build_llm(),
            verbose=True,
            allow_delegation=False,
            max_iter=6,
        )

    @agent
    def solution_architect(self) -> Agent:
        """Create the agent that defines how the project should be built."""

        return Agent(
            config=self.agents_config["solution_architect"],
            llm=build_llm(),
            verbose=True,
            allow_delegation=False,
            max_iter=8,
        )

    @task
    def analyze_requirements(self) -> Task:
        """Convert a rough project idea into structured requirements."""

        return Task(
            config=self.tasks_config["analyze_requirements"],
            output_pydantic=ProjectRequirements,
        )

    @task
    def design_project(self) -> Task:
        """Convert validated requirements into an implementation plan."""

        return Task(
            config=self.tasks_config["design_project"],
            context=[self.analyze_requirements()],
            output_pydantic=ProjectPlan,
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the agents and tasks into a sequential workflow."""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
