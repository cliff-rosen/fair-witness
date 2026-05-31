"""v2 EXTRACT stage — build the article's ArgumentMap.

This is the shared front-end of the two-ring pipeline. It parses *what the
article is arguing and how its claims connect* — deliberately NOT whether any
of it is true. The high-`load_bearing` claims form the "spine" that the
external (Ring 1) stage later reality-checks; the whole structure is what the
internal (Ring 0) stage tests for coherence.
"""

from agents.base_prompt_caller import BasePromptCaller
from schemas.analysis import ArgumentMap


def brief_argument(am: ArgumentMap) -> str:
    """Compact rendering of the argument map for downstream agent context."""
    lines = [f"THESIS: {am.thesis}", "CLAIMS (id [load_bearing] kind/as_presented supports → text):"]
    for c in am.claims:
        lines.append(
            f"  {c.id} [{c.load_bearing}] {c.kind}/{c.as_presented} supports={c.supports}: {c.text}"
        )
    return "\n".join(lines)


class ExtractorPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You map the ARGUMENT STRUCTURE of an article. You judge what it is
arguing and how the pieces fit — NOT whether anything is true. No fact-checking,
no opinion on correctness.

Produce:
- `genre`: news report, op-ed, analysis, feature, blog, etc.
- `topic` + `main_subject`: the subject matter and the central person/org/event.
- `summary`: a 2–3 sentence NEUTRAL summary.
- `thesis`: the single central point the piece advances. For an argumentative
  piece this is its claim; for a straight news report it's the main takeaway or
  frame the piece is built around.
- `claims[]`: the load-bearing assertions, each with:
    • `id` (c1, c2, …)
    • `text` (tight paraphrase or short quote)
    • `kind` (factual / statistical / causal / predictive / opinion / value-judgment)
    • `as_presented`: asserted (stated in the author's own voice), attributed
      (credited to a named source), or hedged (qualified / "may" / "some say")
    • `supports`: the ids this claim backs — other claim ids and/or the literal
      string "thesis". This is the GRAPH: show how claims ladder up to the thesis.
    • `load_bearing`: 0–100 — how central to the thesis. 100 means the argument
      collapses if this claim fails; ~10 means an incidental aside.

Capture the claims that actually carry the argument (typically 4–10), not every
sentence. Be faithful to the article's own logic — if its reasoning has a gap,
represent the claims as stated; the gap gets judged downstream, not here."""
        super().__init__(
            response_model=ArgumentMap,
            system_message=system_message,
            temperature=0.0,
            max_tokens=3072,
        )

    async def extract(self, title: str, text: str) -> ArgumentMap:
        user_content = (
            f"ARTICLE TITLE: {title}\n\n"
            f"ARTICLE TEXT:\n{text}\n\n"
            "Map this article's argument structure."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
