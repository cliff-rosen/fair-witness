"""Stage 2 — Issue Map builder.

Builds an independent map of the debate around the topic — the sides, their
typical arguments and talking points, the settled facts, and the biases articles
on this topic tend to exhibit.

Crucially, this runs **blind to the article**: it sees only the topic (and
subject), never the article text. That independence is what lets the map serve
as a neutral reference frame — the article is diffed against it downstream to
detect omission, selectivity, adopted framing, and false balance / false
consensus. Deriving the map from the article would be circular.
"""

from agents.base_prompt_caller import BasePromptCaller
from schemas.analysis import IssueMap


def brief_issue_map(issue_map: IssueMap) -> str:
    """Render a compact text summary of the map for use as evaluator context."""
    lines = [
        f"Topic: {issue_map.topic}",
        f"Structure: {issue_map.structure} — {issue_map.structure_note}",
    ]
    for side in issue_map.sides:
        lines.append(f"\nSide '{side.name}': {side.position}")
        for arg in side.typical_arguments:
            lines.append(f"  • arg: {arg}")
        for tp in side.talking_points:
            lines.append(f"  • talking point [{tp.status}]: {tp.point}")
    if issue_map.settled_facts:
        lines.append("\nSettled facts:")
        for f in issue_map.settled_facts:
            lines.append(f"  • ({f.confidence}%) {f.fact}")
    if issue_map.common_biases:
        lines.append("\nCommon biases on this topic: " + "; ".join(issue_map.common_biases))
    return "\n".join(lines)


class IssueMapBuilderPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You map the landscape of a debate so an article about it can be judged fairly.

You are given ONLY a topic (and its main subject) — NOT any article. Build a
neutral, independent reference map of the discourse around that topic.

Produce:
1. `structure` + `structure_note`: how the topic is ACTUALLY structured. Be
   honest and resist a reflexive two-sided frame:
   - "settled" — there is broad expert/factual consensus and at most a vocal
     minority. Say so plainly; do NOT manufacture false balance.
   - "genuinely-two-sided" — two legitimate opposing positions.
   - "multi-sided" — several legitimate positions.
   - "not-adversarial" — not really a debate.
   In the note, warn explicitly if the topic is commonly (but wrongly) framed as
   evenly two-sided when it is not.
2. `sides`: each recognized position with its strongest `typical_arguments` and
   its common `talking_points`, each talking point flagged by substantiation
   (substantiated / partly-substantiated / unsubstantiated / contested). For a
   settled topic you may still list a minority side, but its status should show
   in the talking points.
3. `settled_facts`: facts widely treated as established regardless of side, each
   with a confidence (100 = beyond serious dispute).
4. `common_biases`: the slants articles on this topic typically exhibit.

Be even-handed across sides. Do not let your own view of who is "right" distort
the map — represent each side as its better advocates would, while being
accurate about what is and isn't substantiated. Use general knowledge; if the
topic involves very recent events your knowledge may be incomplete — reflect
that in confidence levels rather than guessing.
"""
        super().__init__(
            response_model=IssueMap,
            system_message=system_message,
            temperature=0.0,
            max_tokens=3072,
        )

    async def build(self, topic: str, main_subject: str) -> IssueMap:
        user_content = (
            f"TOPIC: {topic}\n"
            f"MAIN SUBJECT: {main_subject}\n\n"
            "Build the issue map for this topic. Remember: you have NOT seen any "
            "article — map the debate itself."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
