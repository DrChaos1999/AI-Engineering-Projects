"""Task definitions for the Facebook post generation workflow."""

from __future__ import annotations

from textwrap import dedent
from typing import Sequence

from crewai import Agent, Task


class FacebookMarketingTasks:
    """Factory for research, copywriting, visual, and review tasks."""

    def product_analysis(
        self,
        agent: Agent,
        inputs: dict[str, str],
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Analyse the following offer for a Facebook campaign.

                Name/topic: {inputs['name']}
                Website: {inputs['website']}
                Supplied details: {inputs['details']}
                Intended audience: {inputs['audience']}
                Campaign objective: {inputs['objective']}
                Desired tone: {inputs['tone']}
                Output language: {inputs['language']}
                Requested call to action: {inputs['cta']}

                When a website is provided, inspect it. Build a reliable brief covering:
                - what is being offered
                - the audience's likely situation, needs, objections, and motivations
                - features, benefits, differentiators, and proof supplied by the source
                - the strongest credible campaign promise
                - missing information and claims that must not be invented
                - brand voice guidance
                - possible risks, sensitivities, or compliance concerns

                Never convert assumptions into facts. Label every important inference.
                """
            ),
            expected_output=(
                "A structured product-and-audience brief with evidence, inferences, "
                "message opportunities, missing information, and prohibited unsupported claims."
            ),
            agent=agent,
        )

    def competitor_research(
        self,
        agent: Agent,
        inputs: dict[str, str],
        context: Sequence[Task],
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Research the competitive and Facebook content environment for:

                Name/topic: {inputs['name']}
                Website: {inputs['website']}
                Details: {inputs['details']}
                Audience: {inputs['audience']}
                Objective: {inputs['objective']}

                Use web search and public Facebook-indexed search when tools are available.
                Identify up to three relevant competitors, substitutes, or comparable pages.

                Analyse:
                - positioning and recurring promises
                - content angles and post patterns visible in reliable results
                - audience language, questions, objections, and emotional triggers
                - gaps or overused messages
                - opportunities for differentiation
                - evidence quality and research limitations

                Do not pretend that private, unindexed, or login-only Facebook content was seen.
                Do not invent engagement metrics. Links and snippets are research leads, not
                automatically verified facts.
                """
            ),
            expected_output=(
                "An evidence-aware competitor and Facebook landscape report containing "
                "up to three comparisons, content patterns, audience insights, gaps, "
                "opportunities, sources or leads, and explicit limitations."
            ),
            agent=agent,
            context=list(context),
        )

    def campaign_strategy(
        self,
        agent: Agent,
        inputs: dict[str, str],
        context: Sequence[Task],
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Build one coherent Facebook campaign strategy for {inputs['name']}.

                Objective: {inputs['objective']}
                Audience: {inputs['audience']}
                Tone: {inputs['tone']}
                Language: {inputs['language']}
                CTA: {inputs['cta']}

                Use the earlier analysis and research to define:
                - primary audience segment and insight
                - campaign promise and supporting reasons to believe
                - message hierarchy
                - emotional angle
                - three post concepts:
                  1. story-led organic post
                  2. benefit-led promotional post
                  3. community or conversation post
                - CTA logic
                - suitable visual direction
                - claims and approaches to avoid
                - simple A/B test recommendation

                Keep the plan focused enough that a copywriter can execute it directly.
                """
            ),
            expected_output=(
                "A concise but complete Facebook campaign strategy with one core "
                "positioning, message hierarchy, three post concepts, CTA logic, "
                "visual direction, claim boundaries, and an A/B test."
            ),
            agent=agent,
            context=list(context),
        )

    def write_facebook_posts(
        self,
        agent: Agent,
        inputs: dict[str, str],
        context: Sequence[Task],
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Write three finished Facebook post options for {inputs['name']}.

                Audience: {inputs['audience']}
                Objective: {inputs['objective']}
                Tone: {inputs['tone']}
                Language: {inputs['language']}
                CTA: {inputs['cta']}

                Required options:
                1. Story-led organic post
                2. Benefit-led promotional post
                3. Community / conversation post

                For each option provide:
                - label and strategic purpose
                - opening hook
                - complete ready-to-publish body copy
                - one clear CTA
                - zero to five relevant hashtags; do not stuff hashtags
                - a suggested first comment
                - a one-sentence explanation of why the option fits the audience

                Writing requirements:
                - sound natural on Facebook rather than like a generic advertisement
                - use readable spacing
                - use emojis only when appropriate to the requested tone
                - avoid invented facts, fake testimonials, fake scarcity, and guarantees
                - preserve any uncertainty identified by the researchers
                - make all three options meaningfully different
                """
            ),
            expected_output=(
                "Three polished, ready-to-publish Facebook posts in the requested "
                "language, each with a hook, body, CTA, limited hashtags, suggested "
                "first comment, and brief strategic rationale."
            ),
            agent=agent,
            context=list(context),
        )

    def visual_concepts(
        self,
        agent: Agent,
        inputs: dict[str, str],
        approved_copy: str,
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Create three visual concepts for the Facebook campaign below.

                Brand/topic: {inputs['name']}
                Website: {inputs['website']}
                Audience: {inputs['audience']}
                Objective: {inputs['objective']}
                Tone: {inputs['tone']}
                Product details: {inputs['details']}

                COPY CREW OUTPUT
                ----------------
                {approved_copy}
                ----------------

                Create one visual direction for each post option. For every direction include:
                - concept title
                - communication goal
                - scene and subject
                - composition and camera framing
                - environment, lighting, mood, and colour guidance
                - whether the product should be shown
                - minimal text-overlay recommendation
                - accessibility / readability note
                - a self-contained image-generation prompt
                - a short negative prompt listing unwanted visual problems

                The visual must support the message, not merely look attractive.
                Avoid unreadable text, clutter, distorted anatomy, fake interfaces,
                and visual claims that the copy cannot support.
                """
            ),
            expected_output=(
                "Three specific Facebook visual concepts matched to the three copy "
                "options, each including art direction, overlay guidance, accessibility "
                "notes, a complete image prompt, and a negative prompt."
            ),
            agent=agent,
        )

    def final_review(
        self,
        agent: Agent,
        inputs: dict[str, str],
        approved_copy: str,
        context: Sequence[Task],
    ) -> Task:
        return Task(
            description=dedent(
                f"""
                Perform the final creative-director review for this Facebook campaign.

                Name/topic: {inputs['name']}
                Audience: {inputs['audience']}
                Objective: {inputs['objective']}
                Tone: {inputs['tone']}
                Language: {inputs['language']}
                CTA: {inputs['cta']}

                COPY PACKAGE
                ------------
                {approved_copy}
                ------------

                Review the copy package and the visual concepts supplied in task context.

                Deliver:
                1. A brief quality assessment
                2. Any factual, credibility, tone, or CTA issues
                3. A final recommended post option, reproduced in full
                4. Its final matching visual prompt, reproduced in full
                5. Two alternative approved combinations
                6. A pre-publication checklist covering:
                   - factual verification
                   - link and CTA check
                   - spelling and language
                   - permissions for people, logos, or copyrighted assets
                   - accessibility
                   - manual human approval

                Edit where necessary. Do not praise weak work merely because another
                agent produced it.
                """
            ),
            expected_output=(
                "A final reviewed campaign package with one recommended copy-and-visual "
                "combination, two approved alternatives, corrections, and a practical "
                "pre-publication checklist."
            ),
            agent=agent,
            context=list(context),
        )
