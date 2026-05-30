"""Stage 5 — Synthesizer.

Takes the plan, the independent issue map, every dimension specialist's verdict,
and the claim analysis, and produces a holistic TWO-AXIS verdict:

- presentation_score — HOW the article says it (language, framing, tone, balance)
- substantive_score  — WHAT it says (claims, facts, coverage vs the map)

plus a blended overall, the fairness label, political lean + confidence, the
framing the article adopts relative to the map, and the both-sidesing /
false-consensus flags.
"""

import json
from typing import List

from agents.base_prompt_caller import BasePromptCaller
from schemas.analysis import (
    AnalysisPlan,
    ClaimAssessment,
    DimensionAssessment,
    IssueMap,
    OverallAssessment,
)


class SynthesizerPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You are the synthesis stage of a fairness & bias analysis pipeline.

You are given, as JSON:
- A plan describing the article (type, topic, subject, summary, claims).
- An ISSUE MAP of the topic built independently of the article (sides, arguments,
  talking points by substantiation, settled facts, common biases, and whether the
  topic is settled / genuinely two-sided / multi-sided).
- Dimension assessments (the "how it says it" specialists), each 0-100 (100 = fair).
- A claim analysis: each material claim located against the issue map and rated
  for how appropriately the article handles it.

Produce a holistic verdict on TWO axes (both 0-100, 100 = perfectly fair):
- `presentation_score`: HOW the article communicates — derived mainly from the
  dimension assessments (language, framing, tone, balance, attribution…).
- `substantive_score`: WHAT it communicates — derived mainly from the claim
  analysis and coverage vs the map: Does it contradict settled facts? Lean on
  unsubstantiated talking points presented as fact? Omit a side's strongest
  arguments? Cherry-pick?
- `overall_score`: a reasoned blend of the two. Do NOT just average — weight by
  severity and centrality. A single high-severity, load-bearing problem (on
  either axis) should dominate trivial nits.
- `fairness_label`: Highly Fair / Mostly Fair / Mixed / Slanted / Heavily Biased,
  consistent with the overall score.
- `political_lean` + `lean_confidence`: overall direction the article leans, if
  any. "not-applicable" for non-political topics, "undetermined" when balanced.
- `adopted_framing`: whose framing (which side of the map) the article adopts, or
  "balanced" if it fairly represents the landscape.
- `both_sidesing`: TRUE if the article presents a topic the map marks "settled"
  as if it were a live, evenly-matched two-sided debate.
- `false_consensus`: TRUE if the article presents a genuinely contested point
  (per the map) as settled.
- `executive_summary`, `key_strengths`, `key_concerns`: grounded in the findings
  above; reference omitted arguments / mishandled claims / adopted framing where
  relevant.

Be fair to genre (an op-ed may argue a position — judge whether it argues fairly,
not whether it has a view). Judge against the map, not your own opinion of the
topic. Do not introduce issues no specialist or claim finding raised.
"""
        super().__init__(
            response_model=OverallAssessment,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def synthesize(
        self,
        plan: AnalysisPlan,
        issue_map: IssueMap,
        assessments: List[DimensionAssessment],
        claims: List[ClaimAssessment],
    ) -> OverallAssessment:
        payload = {
            "plan": plan.model_dump(),
            "issue_map": issue_map.model_dump(),
            "dimension_assessments": [a.model_dump() for a in assessments],
            "claim_analysis": [c.model_dump() for c in claims],
        }
        user_content = (
            "Here is everything the pipeline produced, as JSON. Synthesize the "
            "two-axis overall verdict.\n\n"
            f"{json.dumps(payload, indent=2)}"
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
