"""Catalogue of bias/fairness dimensions.

The planner selects a relevant subset of these for each article; each selected
dimension gets its own specialized evaluator in the fan-out stage. Keeping the
catalogue here as data (rather than hard-coded prompts) means the orchestration
shape — which experts exist and what they look for — lives in one place.
"""

from typing import Dict

from schemas.analysis import DimensionKey


class DimensionSpec:
    def __init__(self, key: DimensionKey, label: str, description: str, looks_for: str):
        self.key = key
        self.label = label
        self.description = description  # shown to the planner
        self.looks_for = looks_for      # injected into the evaluator's system prompt


DIMENSION_CATALOG: Dict[str, DimensionSpec] = {
    spec.key: spec
    for spec in [
        DimensionSpec(
            key="loaded_language",
            label="Loaded Language",
            description="Emotionally charged, slanted, or prejudicial word choice.",
            looks_for=(
                "Emotionally loaded adjectives/verbs, euphemism or dysphemism, "
                "sarcasm, scare quotes, and connotation that pushes the reader "
                "toward a judgment instead of letting facts speak."
            ),
        ),
        DimensionSpec(
            key="source_balance",
            label="Source Balance",
            description="Diversity and balance of the sources, voices, and viewpoints quoted.",
            looks_for=(
                "Whether multiple sides are quoted, whether one side gets more "
                "and more sympathetic airtime, reliance on anonymous or partisan "
                "sources, and missing stakeholder voices."
            ),
        ),
        DimensionSpec(
            key="framing",
            label="Framing",
            description="How the issue is framed and which narrative is foregrounded.",
            looks_for=(
                "The angle/narrative imposed on events, what is treated as the "
                "default vs. the deviation, ordering that privileges one "
                "interpretation, and framing of cause and blame."
            ),
        ),
        DimensionSpec(
            key="factual_selectivity",
            label="Factual Selectivity",
            description="Cherry-picking of facts and statistics to favor one side.",
            looks_for=(
                "Selective use of data, missing base rates or context, one-sided "
                "examples, and facts presented without the countervailing facts "
                "a fair reader would need."
            ),
        ),
        DimensionSpec(
            key="omission",
            label="Omission",
            description="Relevant perspectives, facts, or context left out entirely.",
            looks_for=(
                "Obvious questions left unasked, a stakeholder never mentioned, "
                "context that would change the reader's conclusion, and 'the dog "
                "that didn't bark'."
            ),
        ),
        DimensionSpec(
            key="tone_subjectivity",
            label="Tone & Subjectivity",
            description="Opinion and editorializing blended into ostensibly factual reporting.",
            looks_for=(
                "Author opinion stated as fact, editorial asides, speculation "
                "presented as certainty, and an overall tone inconsistent with "
                "neutral reporting (note: op-eds are allowed a point of view)."
            ),
        ),
        DimensionSpec(
            key="attribution",
            label="Attribution",
            description="Whether claims are properly attributed vs. asserted as fact.",
            looks_for=(
                "Contested claims stated in the reporter's own voice, vague "
                "attribution ('experts say', 'critics argue'), and assertions "
                "with no source where one is needed."
            ),
        ),
        DimensionSpec(
            key="headline_accuracy",
            label="Headline / Lede Accuracy",
            description="Whether the headline and opening match the body.",
            looks_for=(
                "Headline or lede that overstates, sensationalizes, or skews vs. "
                "what the body actually supports; clickbait; burying the "
                "qualifier."
            ),
        ),
    ]
}


def catalog_for_planner() -> str:
    """Render the catalogue as a bulleted list for the planner's prompt."""
    return "\n".join(
        f"- {spec.key} ({spec.label}): {spec.description}"
        for spec in DIMENSION_CATALOG.values()
    )
