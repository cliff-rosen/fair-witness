"""Stage 1 — Planner.

Reads the article once and decides *how* it should be evaluated: what kind of
article it is, what it's about, its central claims, and which bias/fairness
dimensions are most relevant (with a focus hint for each downstream evaluator).
"""

from agents.base_prompt_caller import BasePromptCaller
from agents.dimensions import catalog_for_planner
from schemas.analysis import AnalysisPlan


class PlannerPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = f"""You are the planning stage of a fairness & bias analysis pipeline.

You will be given an article. Your job is NOT to judge its bias yet — it is to
set up the evaluation so specialist evaluators can do their work well.

Do all of the following:
1. Classify the article (news report, op-ed, feature, analysis, blog, etc.).
2. Identify the topic and the main subject (person/org/event covered).
3. Write a short, strictly neutral 2-3 sentence summary.
4. Extract the central factual claims/assertions the article makes.
5. Select the bias/fairness dimensions that are MOST relevant to THIS article,
   ordered most-relevant first. Choose only dimensions that genuinely apply —
   typically 4 to 6. For each, say why it is relevant here and give the
   evaluator a concrete focus hint.

Be fair to the genre: an op-ed is *allowed* to have a point of view, so weigh
tone/subjectivity accordingly.

Available dimensions (use these exact keys):
{catalog_for_planner()}
"""
        super().__init__(
            response_model=AnalysisPlan,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def plan(self, article_title: str, article_text: str) -> AnalysisPlan:
        user_content = (
            f"ARTICLE TITLE: {article_title}\n\n"
            f"ARTICLE BODY:\n{article_text}"
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
