"""A realistic, fully-populated analyze sample run.

Lets the diagnostics screen render immediately (and CI/dev demo it) without
spending any API calls. The system prompts are read from the real agent classes
so the diagnostics show authentic content; the outputs are hand-authored example
data based on a real article.
"""

import time

from agents.analyze_extractor import ClaimExtractor
from agents.analyze_placer import ClaimPlacer
from agents.analyze_synth import Synthesizer
from agents.analyze_topic_mapper import TopicMapper
from schemas.analysis import ExtractedArticle
from schemas.analyze import (
    AnalyzeReport,
    AnalyzeResult,
    Claim,
    ClaimPlacement,
    ClaimSet,
    PipelineDiagnostics,
    SettledFact,
    Side,
    StageRecord,
    TalkingPoint,
    TopicMap,
    Verdict,
)

_ARTICLE_TEXT = (
    "A neighborhood in Beit Lahia, in northern Gaza, has been reduced to rubble. "
    "Among the ruins, a Civil Defense crew spent three days digging for the bodies "
    "of the Abu Naser family, more than 132 of whom were killed when an Israeli "
    "strike destroyed their five-story apartment building in October 2024. With only "
    "one working excavator available in all of Gaza for body recovery, crews rely on "
    "their hands, their noses, and the memories of survivors who identify the dead by "
    "their clothing — there are no DNA tests available. After three days they had "
    "recovered 50 bodies; 20 family members were still missing. Across Gaza, officials "
    "estimate roughly 8,000 bodies remain buried under the debris."
)


def _article() -> ExtractedArticle:
    return ExtractedArticle(
        title="Skeletons in their clothing: Recovering bodies from the rubble in Gaza",
        text=_ARTICLE_TEXT,
        source_url="https://www.npr.org/sample/gaza-recovery",
        byline="Anas Baba",
        site_name="NPR",
        published="May 6, 2026",
        word_count=len(_ARTICLE_TEXT.split()),
    )


def _claims() -> ClaimSet:
    return ClaimSet(
        genre="news report",
        topic="Gaza war body recovery efforts",
        main_subject="Recovery mission for the Abu Naser family victims in Gaza",
        summary=(
            "A Civil Defense crew spends three days recovering bodies from the rubble "
            "of an apartment building where 132 members of the Abu Naser family were "
            "killed. With scarce equipment, 50 are recovered and 20 remain missing — "
            "a fraction of the ~8,000 bodies still buried across Gaza."
        ),
        thesis=(
            "Body recovery in Gaza reveals the war's human cost and the overwhelming "
            "gap between the scale of need and the resources available."
        ),
        claims=[
            Claim(id="c1", text="An Israeli strike in Oct 2024 destroyed a building, killing 132+ of the Abu Naser family.", as_presented="asserted", centrality=90),
            Claim(id="c2", text="About 8,000 bodies remain buried under rubble across Gaza.", as_presented="attributed", centrality=80),
            Claim(id="c3", text="There is only one functioning excavator in Gaza for body recovery.", as_presented="attributed", centrality=75),
            Claim(id="c4", text="Bodies are identified by clothing because no DNA testing is available.", as_presented="asserted", centrality=60),
            Claim(id="c5", text="After three days the crew recovered 50 bodies; 20 remain missing.", as_presented="asserted", centrality=70),
        ],
    )


def _topic_map() -> TopicMap:
    return TopicMap(
        topic="Gaza war body recovery efforts",
        structure="not-adversarial",
        structure_note=(
            "This is a humanitarian/logistical topic, not a contested political debate. "
            "The broader Gaza conflict is contested, but the facts of body-recovery "
            "operations are largely agreed; coverage skews mainly by what it omits."
        ),
        sides=[
            Side(
                name="Humanitarian/relief",
                position="Recovery and dignified burial are urgent humanitarian obligations.",
                talking_points=[
                    TalkingPoint(point="Equipment restrictions are the main bottleneck to recovery.", substantiation="partly-substantiated"),
                    TalkingPoint(point="The scale of need vastly exceeds available resources.", substantiation="substantiated"),
                ],
            ),
            Side(
                name="Security-constrained",
                position="Heavy-machinery limits are necessary security measures.",
                talking_points=[
                    TalkingPoint(point="Dual-use equipment could be diverted, justifying restrictions.", substantiation="contested"),
                ],
            ),
        ],
        settled_facts=[
            SettledFact(fact="An Israeli airstrike on Oct 29, 2024 destroyed a building in Beit Lahia, killing ~132 of the Abu Naser family.", source_url="https://apps.npr.org/gaza-building-israel-strike-casualties/", confidence=92),
            SettledFact(fact="Roughly 8,000–10,000 bodies are estimated to remain under rubble across Gaza.", source_url="https://www.icrc.org/en/gaza-recovery", confidence=80),
            SettledFact(fact="Body identification in Gaza relies on visual recognition, not DNA testing.", source_url="https://www.reuters.com/world/gaza-recovery", confidence=85),
        ],
        common_biases=[
            "Framing the equipment shortage as purely political rather than also logistical.",
            "Focusing on a single family without contextualizing the broader scale.",
            "Underplaying the role of international organizations (e.g. the ICRC).",
        ],
        sources=[
            "https://apps.npr.org/gaza-building-israel-strike-casualties/",
            "https://www.icrc.org/en/gaza-recovery",
            "https://www.reuters.com/world/gaza-recovery",
        ],
    )


def _placements() -> list[ClaimPlacement]:
    return [
        ClaimPlacement(claim_id="c1", claim="An Israeli strike in Oct 2024 destroyed a building, killing 132+ of the Abu Naser family.", location="matches_settled_fact", side="", handling="fair", note="Matches a settled fact; correctly stated.", source_quote="An Israeli airstrike on Oct 29, 2024 destroyed a building in Beit Lahia, killing ~132 of the Abu Naser family.", source_url="https://apps.npr.org/gaza-building-israel-strike-casualties/"),
        ClaimPlacement(claim_id="c2", claim="About 8,000 bodies remain buried under rubble across Gaza.", location="matches_settled_fact", side="", handling="fair", note="Within the established 8,000–10,000 range and attributed.", source_quote="Roughly 8,000–10,000 bodies are estimated to remain under rubble across Gaza.", source_url="https://www.icrc.org/en/gaza-recovery"),
        ClaimPlacement(claim_id="c3", claim="There is only one functioning excavator in Gaza for body recovery.", location="substantiated_argument", side="Humanitarian/relief", handling="fair", note="A substantiated point about resource scarcity, properly attributed.", source_quote="The scale of need vastly exceeds available resources.", source_url="https://www.icrc.org/en/gaza-recovery"),
        ClaimPlacement(claim_id="c4", claim="Bodies are identified by clothing because no DNA testing is available.", location="matches_settled_fact", side="", handling="fair", note="Consistent with the settled fact on identification methods.", source_quote="Body identification in Gaza relies on visual recognition, not DNA testing.", source_url="https://www.reuters.com/world/gaza-recovery"),
        ClaimPlacement(claim_id="c5", claim="After three days the crew recovered 50 bodies; 20 remain missing.", location="novel_or_unverifiable", side="", handling="fair", note="Specific to this mission; not independently in the map, presented as reporting.", source_quote="", source_url=""),
    ]


def _verdict() -> Verdict:
    return Verdict(
        substantive_score=84,
        presentation_score=82,
        overall_score=83,
        fairness_label="Mostly Fair",
        both_sidesing=False,
        false_consensus=False,
        summary=(
            "A well-grounded, humanistic account. Its load-bearing claims match the "
            "established record and are handled fairly; the main gap is context about "
            "the broader recovery effort and the organizations involved."
        ),
        strengths=[
            "Load-bearing claims match settled facts (strike toll, scale, identification).",
            "Resource-scarcity claims are attributed, not asserted.",
            "Avoids politicizing a humanitarian subject.",
        ],
        concerns=[
            "Omits the broader organized recovery campaign and the ICRC's role.",
            "Single-family focus underplays the overall scale.",
        ],
    )


def build_sample() -> AnalyzeResult:
    """Assemble the report and a complete, authentic-looking diagnostics trace."""
    article = _article()
    claims = _claims()
    topic_map = _topic_map()
    placements = _placements()
    verdict = _verdict()

    # Real system prompts (constructors make no network calls).
    extractor, mapper, placer, synth = ClaimExtractor(), TopicMapper(), ClaimPlacer(), Synthesizer()

    from agents.analyze_topic_mapper import brief_topic_map
    from agents.analyze_placer import _render_claims
    from agents.analyze_synth import _render_placements

    stages = [
        StageRecord(
            name="extract", title="1 · Extract claims", kind="structured",
            model=extractor.model, system_prompt=extractor.system_message,
            user_message=f"ARTICLE TITLE: {article.title}\n\nARTICLE TEXT:\n{article.text}\n\nExtract the claim set for this article.",
            input={"title": article.title, "text": article.text},
            output=claims.model_dump(), duration_ms=4100,
        ),
        StageRecord(
            name="topic_map", title="2 · Map the topic (blind)", kind="agentic",
            model=mapper.model, system_prompt=mapper.system_message,
            user_message=f"TOPIC: {claims.topic}\nMAIN SUBJECT: {claims.main_subject}\n\nSearch the web and build the grounded map of this debate, then emit_result. Remember: you have NOT seen any article — map the debate itself.",
            input={"topic": claims.topic, "main_subject": claims.main_subject},
            output=topic_map.model_dump(),
            sources=topic_map.sources,
            web_steps=[
                {"kind": "search", "query": "Gaza body recovery excavator shortage", "result_count": 6, "url": None, "title": None},
                {"kind": "fetch", "query": None, "result_count": None, "url": "https://www.icrc.org/en/gaza-recovery", "title": "ICRC — Gaza recovery operations"},
                {"kind": "search", "query": "Abu Naser family strike Beit Lahia casualties", "result_count": 5, "url": None, "title": None},
                {"kind": "fetch", "query": None, "result_count": None, "url": "https://apps.npr.org/gaza-building-israel-strike-casualties/", "title": "NPR — Gaza building strike casualties"},
            ],
            duration_ms=9400,
        ),
        StageRecord(
            name="place", title="3 · Place claims on the map", kind="structured",
            model=placer.model, system_prompt=placer.system_message,
            user_message=f"TOPIC: {claims.topic}\n\nGROUNDED TOPIC MAP:\n{brief_topic_map(topic_map)}\n\nARTICLE CLAIMS TO PLACE:\n{_render_claims(claims)}\n\nPlace every claim on the map.",
            input={"claims": claims.model_dump(), "topic_map": topic_map.model_dump()},
            output={"placements": [p.model_dump() for p in placements]}, duration_ms=5200,
        ),
        StageRecord(
            name="verdict", title="4 · Verdict", kind="structured",
            model=synth.model, system_prompt=synth.system_message,
            user_message=f"GENRE: {claims.genre}\nTHESIS: {claims.thesis}\n\nTOPIC MAP (the yardstick):\n{brief_topic_map(topic_map)}\n\nHOW THE ARTICLE'S CLAIMS SIT ON THE MAP:\n{_render_placements(placements)}\n\nWeigh all of this into the two-axis fairness verdict.",
            input={"claims": claims.model_dump(), "topic_map": topic_map.model_dump(), "placements": [p.model_dump() for p in placements]},
            output=verdict.model_dump(), duration_ms=3800,
        ),
    ]

    report = AnalyzeReport(article=article, claims=claims, topic_map=topic_map, placements=placements, verdict=verdict)
    diagnostics = PipelineDiagnostics(
        article_title=article.title,
        stages=stages,
        total_ms=sum(s.duration_ms for s in stages),
    )
    return AnalyzeResult(report=report, diagnostics=diagnostics)
