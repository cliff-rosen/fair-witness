"""v3 Stage 3 — Place each claim on the topic map.

The merge point. For every extracted claim it makes ONE combined call against the
independent topic map: WHERE the claim sits (settled fact / contradicts settled
fact / a side's substantiated argument / a side's unsubstantiated talking point /
novel) AND HOW the article handles it, citing the map's quote/source where one
applies. No new web research — it reasons over the map already gathered.
"""

from typing import List, Tuple

from agents.base_prompt_caller import BasePromptCaller
from agents.boe_topic_mapper import brief_topic_map
from schemas.boe import ClaimPlacement, ClaimSet, PlacementSet, TopicMap


def _render_claims(claims: ClaimSet) -> str:
    lines = []
    for c in claims.claims:
        lines.append(f"  [{c.id}] ({c.as_presented}, centrality {c.centrality}) {c.text}")
    return "\n".join(lines) or "  (none)"


class ClaimPlacer(BasePromptCaller):
    def __init__(self) -> None:
        system_message = """You compare an article's claims against an independent, web-grounded map of
the topic's debate, and place each claim on that map.

For EACH claim you are given, return one placement with:
- `claim_id`: echo the id you were given (e.g. 'c2').
- `location`: where the claim sits relative to the map —
    • matches_settled_fact — it lines up with a fact the map treats as settled
    • contradicts_settled_fact — it conflicts with a settled fact
    • substantiated_argument — it's a legitimate, substantiated argument of a side
    • unsubstantiated_talking_point — it's a side's talking point that the map
      flags as unsubstantiated or merely contested
    • novel_or_unverifiable — not covered by the map / can't be located
- `side`: which side's position it belongs to, if any (else "").
- `handling`: how the ARTICLE treats it given where it sits —
    fair / overstated / asserted_as_fact (a contested point stated flatly as fact)
    / missing_context / misleading.
- `note`: 1–2 sentences explaining the call.
- `source_quote` + `source_url`: the map fact/talking-point (and its source) that
  grounds your placement, where one applies (else "").

Be fair and literal: judge the claim as stated, not a strawman. A correctly
attributed claim ("the report projects X") is handled fairly if the map supports
that the source really says X, even if X itself is uncertain."""
        super().__init__(
            response_model=PlacementSet,
            system_message=system_message,
            temperature=0.0,
            max_tokens=3072,
        )

    async def place(
        self, claims: ClaimSet, topic_map: TopicMap
    ) -> Tuple[List[ClaimPlacement], dict]:
        user_message = (
            f"TOPIC: {claims.topic}\n\n"
            f"GROUNDED TOPIC MAP:\n{brief_topic_map(topic_map)}\n\n"
            f"ARTICLE CLAIMS TO PLACE:\n{_render_claims(claims)}\n\n"
            "Place every claim on the map."
        )
        result: PlacementSet = await self.invoke(user_message)  # type: ignore[assignment]

        # Authoritative claim text by id — don't trust the model to echo it.
        by_id = {c.id: c.text for c in claims.claims}
        for p in result.placements:
            if p.claim_id in by_id:
                p.claim = by_id[p.claim_id]

        io = {
            "model": self.model,
            "system_prompt": self.system_message,
            "user_message": user_message,
        }
        return result.placements, io
