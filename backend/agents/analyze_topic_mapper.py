"""Stage 2 — Map the topic, blind to the article, grounded on the web.

Builds a richly-structured map of the debate — sides, each with talking points
flagged by substantiation, plus settled facts — grounded in real web sources.
It never sees the article, so it serves as a neutral yardstick the claims are
later snapped onto.
"""

from typing import Tuple

from agents.agentic_caller import AgenticPromptCaller
from schemas.analyze import TopicMap


def brief_topic_map(tm: TopicMap) -> str:
    """Compact rendering of the map for the downstream (non-web) stages."""
    lines = [
        f"TOPIC: {tm.topic}",
        f"STRUCTURE: {tm.structure} — {tm.structure_note}",
    ]
    for s in tm.sides:
        lines.append(f"\nSIDE '{s.name}': {s.position}")
        for tp in s.talking_points:
            lines.append(f"  • talking point [{tp.substantiation}]: {tp.point}")
    if tm.settled_facts:
        lines.append("\nSETTLED FACTS:")
        for f in tm.settled_facts:
            src = f" ({f.source_url})" if f.source_url else ""
            lines.append(f"  • ({f.confidence}%) {f.fact}{src}")
    if tm.common_biases:
        lines.append("\nCOMMON BIASES: " + "; ".join(tm.common_biases))
    return "\n".join(lines)


class TopicMapper(AgenticPromptCaller):
    def __init__(self) -> None:
        system_message = """You build a NEUTRAL, web-grounded map of a topic's debate — the reference
frame an article about it will be judged against. You have NOT seen the article.

Search the web (current, authoritative sources), read as needed, then emit_result:
- `structure` + `structure_note`: is the topic settled, genuinely-two-sided,
  multi-sided, or not-adversarial? Be honest — do NOT manufacture false balance
  on a settled question, and don't flatten a genuinely contested one. Warn in the
  note if the topic is commonly but wrongly framed as evenly two-sided.
- `sides`: each recognized position with its `position` and its `talking_points`,
  EACH flagged by substantiation (substantiated / partly-substantiated /
  contested / unsubstantiated). Represent each side as its better advocates would.
- `settled_facts`: facts widely treated as established regardless of side, each
  with a `source_url` where you found it and a `confidence` (100 = beyond dispute).
- `common_biases`: ways coverage of this topic typically skews.

Ground everything in what you actually find — NEVER build this from memory.
Search first."""
        super().__init__(
            response_model=TopicMap,
            system_message=system_message,
            max_tokens=3072,
        )

    async def build(self, topic: str, main_subject: str) -> Tuple[TopicMap, dict]:
        user_message = (
            f"TOPIC: {topic}\n"
            f"MAIN SUBJECT: {main_subject}\n\n"
            "Search the web and build the grounded map of this debate, then emit_result. "
            "Remember: you have NOT seen any article — map the debate itself."
        )
        result, sources, trace, _corpus = await self.invoke(user_message)
        result.sources = sources[:10]
        io = {
            "model": self.model,
            "system_prompt": self.system_message,
            "user_message": user_message,
            "sources": sources[:10],
            "web_steps": [s.model_dump() for s in trace],
        }
        return result, io
