"""Ring 1 · Reality model — a web-grounded map of the topic.

Agentic. This is the grounded successor to the old blind IssueMap: instead of
reciting the model's memory, it searches the web and builds a sourced map of the
debate — the neutral yardstick the article is diffed against.
"""

from agents.agentic_caller import AgenticPromptCaller, verify_evidence
from schemas.analysis import RealityModel


def brief_reality(rm: RealityModel) -> str:
    """Compact rendering for the (non-web) omission reasoner."""
    lines = [
        f"TOPIC: {rm.topic}",
        f"STRUCTURE: {rm.structure} — {rm.structure_note}",
        "KEY FACTS:",
    ]
    lines += [f"  • [{f.status}] {f.fact}" for f in rm.key_facts]
    lines.append("MAIN PERSPECTIVES: " + "; ".join(rm.main_perspectives))
    if rm.common_distortions:
        lines.append("COMMON DISTORTIONS: " + "; ".join(rm.common_distortions))
    return "\n".join(lines)


class RealityModelAgent(AgenticPromptCaller):
    def __init__(self):
        system_message = """You build a NEUTRAL, web-grounded map of a topic's debate — the reference
frame an article about it will be judged against. You have NOT seen the article.

Search the web (current sources), read as needed, then emit_result with:
- `structure` + `structure_note`: is the topic settled, genuinely-two-sided,
  multi-sided, or not-adversarial? Be honest — do NOT manufacture false balance
  on a settled question, and don't flatten a genuinely contested one.
- `key_facts`: facts the evidence supports, each tagged established / contested /
  emerging / disputed, and — where you have a clean quote — `evidence` (the
  `source_url` + a SHORT VERBATIM `quote` from it + `stance`). Quote exactly; it's
  checked against retrieved text. Prefer recent, authoritative sources.
- `main_perspectives`: the legitimate positions in the debate, stated as their
  better advocates would.
- `common_distortions`: ways coverage of this topic typically skews.

Represent each side fairly; ground claims in what you actually found, not priors.
NEVER build this from memory — search first."""
        super().__init__(response_model=RealityModel, system_message=system_message, max_tokens=2560)

    async def build(self, topic: str, main_subject: str) -> RealityModel:
        user_content = (
            f"TOPIC: {topic}\n"
            f"MAIN SUBJECT: {main_subject}\n\n"
            "Search the web and build the grounded reality map for this topic, then emit_result."
        )
        result, sources, trace, corpus = await self.invoke(user_content)
        for fact in result.key_facts:
            verify_evidence(fact.evidence, corpus)
        result.sources = sources[:8]
        result.trace = trace
        return result
