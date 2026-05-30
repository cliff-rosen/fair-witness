"""Stage 4 — Claim analyst.

Engages the *substance* of the article by locating its claims against the
independent issue map, rather than fact-checking them in a vacuum. For each
material claim it records the type, how central it is, how the article presents
it, how it aligns with the map (matches/contradicts a settled fact, echoes a
substantiated argument or an unsubstantiated talking point, or is novel), and
whether the article *handles* it appropriately given all that.

Using the map as the reference keeps this grounded and bounded: the heavy
lifting of "what's established on this topic" was done once, blind to the
article, so we don't re-litigate truth per claim.
"""

import json

from agents.base_prompt_caller import BasePromptCaller
from schemas.analysis import AnalysisPlan, ClaimAnalysis, IssueMap


class ClaimAnalystPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You assess how fairly an article handles its factual substance.

You are given an article, a planner's list of its central claims, and an
independent ISSUE MAP of the topic (built without seeing the article: its sides,
their substantiated arguments and unsubstantiated talking points, the settled
facts, and common biases).

Identify the article's material claims (start from the planner's list, add any
important ones it missed, drop trivia). For each, record:
- `claim`: a short quote or tight paraphrase.
- `claim_type`: factual / statistical / causal / predictive / opinion / value-judgment.
- `centrality`: 0-100, how load-bearing the claim is to the article's thesis.
- `as_presented`: how the article frames it (stated as fact / attributed to X / hedged / etc.).
- `map_alignment`: relative to the issue map —
   matches_settled_fact / contradicts_settled_fact / substantiated_argument /
   unsubstantiated_talking_point / novel_or_unverifiable.
- `handling`: whether the article presents it appropriately —
   appropriate / appropriate_opinion (clearly-marked opinion is fair) /
   overstated / misleading (true-but-misleading or missing context) /
   unsupported (asserted as fact without support).
- `note`: one concise sentence justifying the alignment/handling call.

Be fair to genre and to opinion: a clearly-marked value judgment in an op-ed is
"appropriate_opinion", not a violation. Judge against the map, not against your
own preferred conclusion. Focus on the claims that matter — aim for the most
material 5-10.
"""
        super().__init__(
            response_model=ClaimAnalysis,
            system_message=system_message,
            temperature=0.0,
            max_tokens=4096,
        )

    async def analyze(
        self, article_title: str, article_text: str, plan: AnalysisPlan, issue_map: IssueMap
    ) -> ClaimAnalysis:
        user_content = (
            f"ARTICLE TITLE: {article_title}\n\n"
            f"PLANNER'S CENTRAL CLAIMS:\n{json.dumps(plan.central_claims, indent=2)}\n\n"
            f"ISSUE MAP:\n{json.dumps(issue_map.model_dump(), indent=2)}\n\n"
            f"ARTICLE BODY:\n{article_text}"
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
