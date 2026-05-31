"""Ring 1 · Claim-check — reality-check one spine claim against the web.

Agentic: searches/fetches, then emits a verdict + finding. Run one per
load-bearing claim (the "spine"), concurrently.
"""

from agents.agentic_caller import AgenticPromptCaller, verify_evidence
from schemas.analysis import ArgClaim, ClaimCheck


class ClaimCheckAgent(AgenticPromptCaller):
    def __init__(self):
        system_message = """You fact-check ONE claim from a news article against current web evidence.

Process: search the web (multiple queries if needed), read promising pages, then
call emit_result. NEVER answer from memory — search first.

Judge two things:
- `verdict`: how the claim holds up against what you find — supported,
  mostly_supported, mixed, contradicted, unsupported, or unverifiable (if you
  genuinely can't find evidence either way — don't guess).
- `handling`: how the ARTICLE presents it given the evidence — appropriate,
  overstated, missing_context, misleading, or outdated.
- `finding`: 1–2 sentences stating what the evidence actually shows.
- `evidence`: the specific quotes backing your verdict. For each: the `source_url`
  you found it at, a SHORT VERBATIM `quote` copied EXACTLY from that page or
  search snippet (do NOT paraphrase — it will be checked against the retrieved
  text and dropped if it doesn't match), and `stance` (supports / contradicts /
  contextualizes). Include at least one for any verdict other than unverifiable.
  Leave `verified` false — the system sets it.

Be fair and literal: check the specific claim as stated, not a strawman of it.
A correctly-attributed estimate ("the Cook Report projects X") is supported if
that source really projects X — even if X is uncertain."""
        super().__init__(response_model=ClaimCheck, system_message=system_message, max_tokens=1536)

    async def check(self, claim: ArgClaim, topic: str) -> ClaimCheck:
        user_content = (
            f"TOPIC: {topic}\n"
            f"CLAIM TO CHECK [{claim.id}]: {claim.text}\n"
            f"(The article presents this as {claim.as_presented}; kind: {claim.kind}.)\n\n"
            "Search the web to assess whether this claim holds up, then emit_result."
        )
        result, sources, trace, corpus = await self.invoke(user_content)
        result.claim_id = claim.id          # authoritative — don't trust the model to echo
        result.claim = claim.text
        verify_evidence(result.evidence, corpus)   # confirm quotes against retrieved text
        result.sources = sources[:8]
        result.trace = trace
        return result
