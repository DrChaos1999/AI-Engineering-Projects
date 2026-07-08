"""Agent definitions for the Facebook post generation workflow."""

from __future__ import annotations

import os

from crewai import Agent, LLM
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

from .tools import search_public_facebook


class FacebookMarketingAgents:
    """Factory for the specialized agents used by both crews."""

    def __init__(self) -> None:
        model = os.getenv("MODEL", "openai/gpt-4o-mini")
        temperature = float(os.getenv("TEMPERATURE", "0.7"))

        self.llm = LLM(
            model=model,
            temperature=temperature,
        )

        self.scrape_tool = ScrapeWebsiteTool()

        self.research_tools = [self.scrape_tool]
        if os.getenv("SERPER_API_KEY"):
            self.research_tools.extend(
                [
                    SerperDevTool(),
                    search_public_facebook,
                ]
            )

    def product_audience_analyst(self) -> Agent:
        return Agent(
            role="Product and Audience Analyst",
            goal=(
                "Understand the offer, audience, proof points, differentiators, "
                "risks, and communication opportunities without inventing facts."
            ),
            backstory=(
                "You are a senior brand analyst who converts messy product "
                "information and website content into a precise, evidence-aware "
                "marketing brief."
            ),
            tools=self.research_tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=8,
        )

    def facebook_market_researcher(self) -> Agent:
        return Agent(
            role="Facebook Market Researcher",
            goal=(
                "Find useful competitor, audience, and content-pattern insights "
                "for Facebook while clearly separating evidence from inference."
            ),
            backstory=(
                "You study how brands and communities communicate on Facebook. "
                "You know public search coverage is incomplete, so you never claim "
                "that search snippets represent the whole platform."
            ),
            tools=self.research_tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=10,
        )

    def campaign_strategist(self) -> Agent:
        return Agent(
            role="Facebook Campaign Strategist",
            goal=(
                "Turn the analysis into a focused Facebook campaign angle, "
                "message hierarchy, content approach, and conversion path."
            ),
            backstory=(
                "You are a pragmatic social strategist. You prefer one clear "
                "campaign promise, credible support, and an appropriate call to "
                "action over vague or exaggerated marketing."
            ),
            tools=self.research_tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=8,
        )

    def facebook_copywriter(self) -> Agent:
        return Agent(
            role="Senior Facebook Copywriter",
            goal=(
                "Write distinctive Facebook posts that feel natural in the feed, "
                "communicate value, invite interaction, and support the campaign goal."
            ),
            backstory=(
                "You are an experienced direct-response and community copywriter. "
                "You can write story-led, promotional, and conversational posts "
                "without clickbait, fake urgency, or unsupported claims."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=8,
        )

    def visual_concept_designer(self) -> Agent:
        return Agent(
            role="Facebook Visual Concept Designer",
            goal=(
                "Create scroll-stopping visual concepts that reinforce the post "
                "message and can be executed by a photographer, designer, or image model."
            ),
            backstory=(
                "You are an art director who translates strategy and copy into "
                "specific scenes, compositions, emotions, lighting, text-overlay "
                "guidance, and brand-safe visual direction."
            ),
            tools=self.research_tools,
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=8,
        )

    def creative_director(self) -> Agent:
        return Agent(
            role="Chief Creative Director",
            goal=(
                "Review the complete Facebook campaign package for strategic fit, "
                "clarity, credibility, platform suitability, and consistency."
            ),
            backstory=(
                "You lead a social creative team and make the final editorial "
                "decision. You remove repetition, unsupported promises, confusing "
                "CTAs, and visual-copy mismatches."
            ),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=8,
        )
