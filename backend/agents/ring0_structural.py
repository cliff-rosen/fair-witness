"""Ring 0 · Structural self-consistency.

Text-only. Does the headline/lede match what the body supports? Are contested
claims attributed to sources rather than asserted in the author's voice? Is
opinion kept distinct from reporting (genre-appropriately)?
"""

from agents.base_prompt_caller import BasePromptCaller
from agents.extractor import brief_argument
from schemas.analysis import ArgumentMap, StructuralAssessment


class StructuralPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You judge an article's INTERNAL self-consistency — text-only, no outside facts.

Assess:
- `headline_matches_body`: does the title/lede claim match what the body actually
  supports, or does it overreach / bait? Explain in `headline_note`.
- `contested_claims_attributed`: are contested or load-bearing claims sourced
  (attributed) rather than asserted flatly in the author's own voice? Use the
  argument map's `as_presented` flags.
- `opinion_fact_separation`: does the piece keep opinion distinct from reporting?
  Judge by genre — an op-ed needn't separate them; a news report must.
- `findings[]`: specific observations (e.g. "headline says X, body only shows Y").
- `score`: 0–100 self-consistency (100 = headline matches, claims sourced,
  opinion clearly separated as appropriate for the genre)."""
        super().__init__(
            response_model=StructuralAssessment,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def analyze(self, title: str, text: str, argument_map: ArgumentMap) -> StructuralAssessment:
        user_content = (
            f"ARTICLE TITLE (headline): {title}\n"
            f"GENRE: {argument_map.genre}\n\n"
            f"ARGUMENT MAP:\n{brief_argument(argument_map)}\n\n"
            f"ARTICLE TEXT:\n{text}\n\n"
            "Assess the article's internal self-consistency."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
