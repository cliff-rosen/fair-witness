"""v2 Synthesizer — blend Ring 0 + Ring 1 into the two-axis Verdict.

Non-agentic reasoning over everything already gathered. Crucially, it is told to
keep the two axes honest: coherence is text-grounded (trust it), correspondence
is only as strong as what Ring 1 could actually verify (don't inflate it when
claims came back unverifiable).
"""

from typing import List

from agents.base_prompt_caller import BasePromptCaller
from schemas.analysis import (
    ArgumentMap,
    ClaimCheck,
    CoherenceAssessment,
    OmissionAssessment,
    RealityModel,
    RhetoricAssessment,
    StructuralAssessment,
    Verdict,
)


def _render_inputs(
    am: ArgumentMap,
    coherence: CoherenceAssessment,
    rhetoric: RhetoricAssessment,
    structural: StructuralAssessment,
    reality: RealityModel,
    claim_checks: List[ClaimCheck],
    omission: OmissionAssessment,
) -> str:
    verified = sum(1 for c in claim_checks for e in c.evidence if e.verified)
    checks = "\n".join(
        f"  • [{c.verdict}/{c.handling}] {c.claim[:90]} "
        f"({sum(1 for e in c.evidence if e.verified)} verified quotes)"
        for c in claim_checks
    ) or "  (none checked)"
    return (
        f"GENRE: {am.genre}\nTHESIS: {am.thesis}\n\n"
        f"--- RING 0 (internal, text-grounded) ---\n"
        f"Coherence: score={coherence.score}, thesis_follows={coherence.thesis_follows}, "
        f"issues={len(coherence.issues)} ({', '.join(i.kind for i in coherence.issues[:4])})\n"
        f"Rhetoric: score={rhetoric.score}, tone={rhetoric.tone!r}, findings={len(rhetoric.findings)}\n"
        f"Structural: score={structural.score}, headline_matches={structural.headline_matches_body}, "
        f"opinion_separated={structural.opinion_fact_separation}\n\n"
        f"--- RING 1 (external, web-grounded) ---\n"
        f"Reality: structure={reality.structure}; {reality.structure_note[:160]}\n"
        f"Claim checks ({verified} verified quotes total):\n{checks}\n"
        f"Omission: coverage={omission.score}, framing={omission.adopted_framing!r}, "
        f"both_sidesing={omission.both_sidesing}, false_consensus={omission.false_consensus}; "
        f"top omissions: {'; '.join(o.missing[:60] for o in omission.omissions[:3])}\n"
    )


class SynthesizerV2PromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You write the final fairness verdict by blending two independent axes.

- `coherence_score` (Ring 0): internal quality — logic, rhetoric, self-consistency.
  This is text-grounded, so judge it confidently.
- `correspondence_score` (Ring 1): how the article holds up against reality —
  claim checks + omissions. BE HONEST about grounding: if most load-bearing
  claims came back `unverifiable` or carried no verified evidence, you CANNOT
  give a high correspondence score — lean toward the middle and say so. Reward
  it only when claims were actually verified as supported and little was omitted.

`overall_score` is a REASONED blend, not an average: a single severe, load-bearing
failure on either axis should pull it down more than several minor nits. A piece
can be highly coherent yet score low on correspondence (tight reasoning on shaky
facts) or vice-versa — let the two diverge when they should.

Also set: `fairness_label`, `political_lean` + `lean_confidence` (infer from
rhetoric, claim handling, and adopted framing — not from whether you agree),
`both_sidesing`/`false_consensus` (carry over from the omission assessment),
a plain-language `executive_summary`, and `key_strengths` / `key_concerns` (each
a specific, concrete point a reader could check — not vague praise/criticism).
Judge by genre: an op-ed may argue a side; hold news to a neutral standard."""
        super().__init__(response_model=Verdict, system_message=system_message, max_tokens=2048)

    async def synthesize(
        self,
        am: ArgumentMap,
        coherence: CoherenceAssessment,
        rhetoric: RhetoricAssessment,
        structural: StructuralAssessment,
        reality: RealityModel,
        claim_checks: List[ClaimCheck],
        omission: OmissionAssessment,
    ) -> Verdict:
        user_content = (
            _render_inputs(am, coherence, rhetoric, structural, reality, claim_checks, omission)
            + "\nWeigh all of this into the two-axis verdict."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
