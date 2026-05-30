"""Ad-hoc end-to-end smoke test for the orchestration pipeline."""

import asyncio

from services.analysis_service import AnalysisService
from services.article_service import ArticleService

SAMPLE = """City Council's Reckless Spending Spree Threatens Taxpayers

In yet another stunning display of fiscal irresponsibility, the city council
rammed through a bloated $4 million budget for a so-called "community center"
on Tuesday night, ignoring the concerns of hardworking taxpayers who will
foot the bill. Critics say the project is a thinly veiled handout to the
mayor's political allies.

The mayor, who has never met a spending program she didn't like, claimed the
center would "transform the neighborhood." But residents aren't buying it.
"Nobody asked us," said one frustrated homeowner. Supporters of the plan were
not made available for comment.

The vote passed 5-2. Experts warn that such projects routinely balloon over
budget, leaving ordinary families to clean up the mess.
"""


async def main():
    article = ArticleService().from_text(SAMPLE)
    print(f"Article: '{article.title}' ({article.word_count} words)\n")

    service = AnalysisService()
    async for event in service.analyze_stream(article):
        if event.type == "plan" and event.plan:
            print(f"[PLAN] type={event.plan.article_type} | topic={event.plan.topic}")
            print(f"       dims={[d.key for d in event.plan.dimensions]}")
        elif event.type == "issue_map" and event.issue_map:
            m = event.issue_map
            print(f"[MAP] structure={m.structure} | sides={[s.name for s in m.sides]} | settled_facts={len(m.settled_facts)}")
            print(f"      note: {m.structure_note}")
        elif event.type == "dimension_complete" and event.assessment:
            a = event.assessment
            print(f"  [DIM] {a.key:20s} score={a.score:3d} severity={a.severity:8s} evidence={len(a.evidence)}")
        elif event.type == "claims_analyzed" and event.claims is not None:
            print(f"  [CLAIMS] {len(event.claims)} analyzed")
            for c in event.claims:
                print(f"     - [{c.map_alignment}/{c.handling}] {c.claim[:60]}")
        elif event.type == "synthesizing":
            print("[SYNTHESIZING...]")
        elif event.type == "report" and event.report:
            o = event.report.overall
            print(f"\n[REPORT] overall={o.overall_score} (pres={o.presentation_score} subst={o.substantive_score}) label='{o.fairness_label}'")
            print(f"         lean={o.political_lean} ({o.lean_confidence}%) | framing={o.adopted_framing} | both_sidesing={o.both_sidesing} false_consensus={o.false_consensus}")
            print(f"Summary: {o.executive_summary}")
        elif event.type == "error":
            print(f"[ERROR] {event.message}")


if __name__ == "__main__":
    asyncio.run(main())
