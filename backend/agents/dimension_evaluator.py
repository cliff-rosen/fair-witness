"""Stage 2 — Dimension evaluator (the fan-out workers).

One instance per selected dimension. Each is a specialist that looks at the
whole article through a single lens and returns a typed ``DimensionAssessment``
with a score, severity, evidence quotes, and concrete suggestions.

These run concurrently in the orchestrator's fan-out stage.
"""

from typing import Optional

from agents.base_prompt_caller import BasePromptCaller
from agents.dimensions import DIMENSION_CATALOG
from schemas.analysis import DimensionAssessment, PlannedDimension


class DimensionEvaluatorPromptCaller(BasePromptCaller):
    def __init__(self, planned: PlannedDimension):
        spec = DIMENSION_CATALOG[planned.key]
        self.planned = planned

        system_message = f"""You are a specialist evaluator on a fairness & bias analysis panel.

You assess exactly ONE dimension: {spec.label} ({planned.key}).

What this dimension covers:
{spec.description}

What to look for:
{spec.looks_for}

Focus hint for this specific article:
{planned.focus}

Instructions:
- Judge ONLY your dimension. Ignore issues that belong to other specialists.
- Ground every finding in the text: include short verbatim quotes as evidence.
- Score 0-100 where 100 = perfectly fair/unbiased on THIS dimension and 0 =
  heavily biased. Set severity accordingly (none/low/moderate/high).
- If your dimension leans the article in a political direction, set `lean`;
  otherwise use "not-applicable".
- Be calibrated and fair to the article's genre. Do not invent problems; if the
  article is clean on your dimension, say so and score it high.
- Give concrete, actionable suggestions only where there is a real issue.
- You may be given an ISSUE MAP: an independent picture of the topic's debate
  (sides, arguments, settled facts, common biases) built without seeing this
  article. Use it as a reference for what a balanced treatment would include —
  e.g. to judge what voices/arguments were omitted or which side's framing was
  adopted. The map is context, not the thing you score.

Set `key` to "{planned.key}" and `label` to "{spec.label}".
"""
        super().__init__(
            response_model=DimensionAssessment,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def evaluate(
        self,
        article_title: str,
        article_text: str,
        map_reference: Optional[str] = None,
    ) -> DimensionAssessment:
        parts = [f"ARTICLE TITLE: {article_title}\n"]
        if map_reference:
            parts.append(f"ISSUE MAP (reference, built blind to this article):\n{map_reference}\n")
        parts.append(f"ARTICLE BODY:\n{article_text}")
        user_content = "\n".join(parts)
        result: DimensionAssessment = await self.invoke(user_content)  # type: ignore[assignment]
        # Defensively pin identity fields in case the model drifts.
        result.key = self.planned.key
        result.label = DIMENSION_CATALOG[self.planned.key].label
        return result
