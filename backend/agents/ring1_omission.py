"""Ring 1 · Omission — what the article left out, vs the grounded reality model.

NOT agentic: it reasons over evidence already gathered (the reality model + the
claim checks + the article), so it needs no new searches. Omission is a diff of
the article against the reality model.
"""

from typing import List

from agents.base_prompt_caller import BasePromptCaller
from agents.extractor import brief_argument
from agents.ring1_reality import brief_reality
from schemas.analysis import (
    ArgumentMap,
    ClaimCheck,
    OmissionAssessment,
    RealityModel,
)


class OmissionAgent(BasePromptCaller):
    def __init__(self):
        system_message = """You assess what an article OMITS or how it FRAMES a topic, by diffing it
against a web-grounded reality model you are given. No new research — reason from
the materials provided.

Identify:
- `omissions`: material facts, perspectives, or stakeholders present in the
  reality model but absent from (or underplayed by) the article — each with why
  it matters and a severity.
- `adopted_framing`: whose framing the article takes as default (or 'balanced').
- `both_sidesing`: does it present a SETTLED question as a live two-sided debate?
- `false_consensus`: does it present a genuinely CONTESTED point as settled?
- `score`: 0–100 coverage completeness (100 = nothing material omitted).

Judge by genre — an op-ed needn't cover every side, but shouldn't misrepresent
what it omits."""
        super().__init__(response_model=OmissionAssessment, system_message=system_message, max_tokens=2048)

    async def analyze(
        self,
        article_title: str,
        article_text: str,
        argument_map: ArgumentMap,
        reality: RealityModel,
        claim_checks: List[ClaimCheck],
    ) -> OmissionAssessment:
        checks = "\n".join(f"  • [{c.verdict}/{c.handling}] {c.claim}" for c in claim_checks) or "  (none)"
        user_content = (
            f"ARTICLE TITLE: {article_title}\n"
            f"GENRE: {argument_map.genre}\n\n"
            f"WHAT THE ARTICLE ARGUES:\n{brief_argument(argument_map)}\n\n"
            f"GROUNDED REALITY MODEL:\n{brief_reality(reality)}\n\n"
            f"CLAIM CHECKS:\n{checks}\n\n"
            f"ARTICLE TEXT:\n{article_text}\n\n"
            "Assess omission and framing by diffing the article against the reality model."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
