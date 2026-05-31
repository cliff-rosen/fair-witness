"""Ring 0 · Coherence — does the argument hold together on its own terms?

Text-only. ASSUMES every claim is true as stated — this stage does NOT
fact-check. It judges the *logic*: does the thesis follow from the claims, are
there gaps, contradictions, unsupported leaps, circularity. This is the facet
the old pipeline barely had.
"""

from agents.base_prompt_caller import BasePromptCaller
from agents.extractor import brief_argument
from schemas.analysis import ArgumentMap, CoherenceAssessment


class CoherencePromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You judge whether an article's argument is internally COHERENT — on its own
terms. This is a logic check, NOT a fact check.

Critical rule: ASSUME every claim in the argument map is TRUE AS STATED. You are
not assessing whether the claims are correct about the world — only whether the
reasoning built on them holds together.

Assess:
- `thesis_follows`: given the claims as presented, does the thesis actually follow?
- `closes_loop`: does the piece resolve the central question it raises, or leave
  it dangling / pivot away?
- `issues[]`: concrete logical faults — a `gap` (the claims don't establish the
  conclusion), `contradiction` (it argues against itself), `unsupported_leap`,
  `circular_reasoning`, `non_sequitur`, `overgeneralization`, `missing_premise`.
  Cite the argument-map claim ids involved.
- `score`: 0–100 internal coherence. A piece can argue a position you disagree
  with and still be highly coherent — score the reasoning, not the conclusion.
  Reserve low scores for genuine logical failure, not mere strong opinion."""
        super().__init__(
            response_model=CoherenceAssessment,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def analyze(self, title: str, text: str, argument_map: ArgumentMap) -> CoherenceAssessment:
        user_content = (
            f"ARTICLE TITLE: {title}\n\n"
            f"ARGUMENT MAP:\n{brief_argument(argument_map)}\n\n"
            f"ARTICLE TEXT:\n{text}\n\n"
            "Assess the internal coherence of this argument. Remember: assume the "
            "claims are true; judge only whether the reasoning holds together."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
