"""v3 Stage 1 — Extract the article's load-bearing claims.

Looks ONLY at the article. Pulls what it is (genre/topic/thesis) and the handful
of claims it rests on, with how each is presented and how central it is. No
fact-checking here — that happens once the topic map exists.
"""

from typing import Tuple

from agents.base_prompt_caller import BasePromptCaller
from schemas.boe import ClaimSet


class ClaimExtractor(BasePromptCaller):
    def __init__(self) -> None:
        system_message = """You read a news/opinion article and extract the claims it rests on. You do
NOT judge whether anything is true — only identify what is being claimed.

Produce:
- `genre`: news report, op-ed, analysis, feature, blog, etc.
- `topic` + `main_subject`: the subject matter and the central person/org/event.
- `summary`: a 2–3 sentence NEUTRAL summary.
- `thesis`: the single central point the piece advances (for straight news, its
  main takeaway / frame).
- `claims[]`: the load-bearing assertions (typically 4–8), each with:
    • `id` (c1, c2, …)
    • `text` (tight paraphrase or short quote)
    • `as_presented`: asserted (stated in the author's own voice), attributed
      (credited to a named source), or hedged (qualified / "may" / "some say")
    • `centrality`: 0–100 — how load-bearing. 100 = the argument collapses
      without it; ~10 = an incidental aside.

Capture the claims that actually carry the argument, not every sentence."""
        super().__init__(
            response_model=ClaimSet,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2560,
        )

    async def extract(self, title: str, text: str) -> Tuple[ClaimSet, dict]:
        user_message = (
            f"ARTICLE TITLE: {title}\n\n"
            f"ARTICLE TEXT:\n{text}\n\n"
            "Extract the claim set for this article."
        )
        result: ClaimSet = await self.invoke(user_message)  # type: ignore[assignment]
        io = {
            "model": self.model,
            "system_prompt": self.system_message,
            "user_message": user_message,
        }
        return result, io
