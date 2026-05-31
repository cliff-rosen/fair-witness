"""Ring 0 · Rhetoric — the manner: loaded language, tone, editorializing.

Text-only and genre-aware. An op-ed is allowed to argue forcefully; a straight
news report editorializing is a problem. Findings cite verbatim quotes.
"""

from agents.base_prompt_caller import BasePromptCaller
from agents.extractor import brief_argument
from schemas.analysis import ArgumentMap, RhetoricAssessment


class RhetoricPromptCaller(BasePromptCaller):
    def __init__(self):
        system_message = """You judge the LANGUAGE and TONE of an article — its manner, not its facts.

Look for: emotionally loaded or slanted word choice, editorializing bleeding
into ostensibly factual reporting, sarcasm/snark, framing verbs ("admitted",
"slammed"), and adjectives that smuggle in a judgment.

Be GENRE-AWARE (the genre is in the argument map): an op-ed or analysis may
argue forcefully and use vivid language — that is appropriate and should NOT be
penalized heavily; the concern there is only manipulation or strawmanning. A
straight news report, by contrast, should stay neutral, so editorializing counts
against it.

For each `finding`, give the VERBATIM quote, why it's loaded, and a severity
(none/low/moderate/high). `tone` is one or two words (e.g. "measured",
"polemical", "snarky"). `score` is 0–100 for neutrality of language (100 =
even-handed and measured for its genre)."""
        super().__init__(
            response_model=RhetoricAssessment,
            system_message=system_message,
            temperature=0.0,
            max_tokens=2048,
        )

    async def analyze(self, title: str, text: str, argument_map: ArgumentMap) -> RhetoricAssessment:
        user_content = (
            f"ARTICLE TITLE: {title}\n"
            f"GENRE: {argument_map.genre}\n\n"
            f"ARTICLE TEXT:\n{text}\n\n"
            "Assess the article's language and tone, judged appropriately for its genre."
        )
        return await self.invoke(user_content)  # type: ignore[return-value]
