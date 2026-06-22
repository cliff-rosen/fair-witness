"""Stage 4 — Synthesize the two-axis verdict.

Reasons over everything already gathered (claims + map + placements). Keeps the
two axes honest: SUBSTANTIVE is how well the article tracks the map; PRESENTATION
is how it's written. Carries the both-sidesing / false-consensus flags from how
the article's claims sit against the map's structure.
"""

from typing import List, Tuple

from agents.base_prompt_caller import BasePromptCaller
from agents.analyze_topic_mapper import brief_topic_map
from schemas.analyze import ClaimPlacement, ClaimSet, TopicMap, Verdict


def _render_placements(placements: List[ClaimPlacement]) -> str:
    lines = []
    for p in placements:
        side = f" [{p.side}]" if p.side else ""
        lines.append(f"  • [{p.location}/{p.handling}]{side} {p.claim[:100]} — {p.note}")
    return "\n".join(lines) or "  (none)"


class Synthesizer(BasePromptCaller):
    def __init__(self) -> None:
        system_message = """You write the final fairness verdict from how an article's claims sit against
an independent, grounded map of the topic.

- `substantive_score` (0–100): does the article track the map? Lower it for
  claims that contradict settled facts, launder a side's unsubstantiated talking
  points as fact, or cherry-pick. Reward claims that match settled facts and
  legitimate substantiated arguments handled fairly.
- `presentation_score` (0–100): how it's written — loaded language, framing,
  tone. Judge by genre: an op-ed may argue a side; hold news to a neutral bar.
- `overall_score`: a REASONED blend, NOT an average — one severe, load-bearing
  failure should pull it down more than several minor nits. Let the two axes
  diverge when they should.
- `fairness_label`: Highly Fair / Mostly Fair / Mixed / Slanted / Heavily Biased.
- `both_sidesing`: true if the article presents a SETTLED question (per the map's
  structure) as a live two-sided debate.
- `false_consensus`: true if it presents a genuinely CONTESTED point as settled.
- `summary`: a plain-language verdict a normal reader can act on.
- `strengths` / `concerns`: specific, concrete, checkable points — not vague
  praise or criticism."""
        super().__init__(
            response_model=Verdict,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def synthesize(
        self,
        claims: ClaimSet,
        topic_map: TopicMap,
        placements: List[ClaimPlacement],
    ) -> Tuple[Verdict, dict]:
        user_message = (
            f"GENRE: {claims.genre}\n"
            f"THESIS: {claims.thesis}\n\n"
            f"TOPIC MAP (the yardstick):\n{brief_topic_map(topic_map)}\n\n"
            f"HOW THE ARTICLE'S CLAIMS SIT ON THE MAP:\n{_render_placements(placements)}\n\n"
            "Weigh all of this into the two-axis fairness verdict."
        )
        result: Verdict = await self.invoke(user_message)  # type: ignore[assignment]
        io = {
            "model": self.model,
            "system_prompt": self.system_message,
            "user_message": user_message,
        }
        return result, io
