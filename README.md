# Fair Witness

An orchestrated fairness & bias analyzer for any article. Give it a URL or
pasted text and it produces a scored, evidence-backed report on how fair and
balanced the article is.

Built to mirror the **TableThat** stack and conventions (FastAPI + Pydantic
services/routers/schemas on the backend; React + Vite + TypeScript with
`lib/api` + `types` + `pages` on the frontend).

## The orchestration

The interesting part is the pipeline — a **plan → map → fan-out → synthesize**
shape, all on the Anthropic SDK using forced-tool structured output. The key
idea in V2 is the **Issue Map**: an independent picture of the topic's debate,
built *blind to the article*, that everything else is measured against.

```
            ┌─────────────┐
 article ─► │   Planner   │  classifies, extracts claims, selects dimensions,
            └──────┬──────┘  and names the TOPIC
                   │
                   ▼
            ┌─────────────┐  built from the topic ALONE (never sees the
            │  Issue Map  │  article): sides, arguments, talking points by
            └──────┬──────┘  substantiation, settled facts, common biases
                   │  (neutral reference frame)
        ┌──────────┴───────────────────────┐   fan-out (concurrent)
        ▼                                   ▼
 ┌──────────────┐                    ┌──────────────┐
 │ dimension    │  HOW it says it    │ claim        │  WHAT it says — each claim
 │ specialists  │  (map-aware)       │ analyst      │  located against the map
 └──────┬───────┘                    └──────┬───────┘
        └───────────────┬───────────────────┘
                        ▼
                 ┌─────────────┐  TWO-AXIS verdict: presentation + substance,
                 │ Synthesizer │  blended overall, lean, adopted framing,
                 └──────┬──────┘  both-sidesing / false-consensus flags
                        ▼
                   BiasReport
```

Each stage is a `BasePromptCaller` subclass that returns a **typed Pydantic
model** (no free-form parsing). The orchestrator (`AnalysisService`) is an async
generator of typed `AnalysisEvent`s, so the UI renders each stage live (plan →
map → specialists + claim analyst landing → synthesis).

| Stage | Code | Output schema |
|-------|------|---------------|
| Planner | `agents/planner.py` | `AnalysisPlan` |
| Issue Map (blind to article) | `agents/issue_map_builder.py` | `IssueMap` |
| Dimension evaluators (fan-out, map-aware) | `agents/dimension_evaluator.py` | `DimensionAssessment` |
| Claim analyst (map-aligned) | `agents/claim_analyst.py` | `ClaimAnalysis` |
| Synthesizer (two-axis) | `agents/synthesizer.py` | `OverallAssessment` |
| Orchestrator | `services/analysis_service.py` | `BiasReport` (streamed) |

Dimensions are defined as data in `agents/dimensions.py`, so the panel of
specialists is easy to extend.

### Why the map is built blind to the article

Most bias is only visible relative to *what could have been said*. If the map of
"the sides" were derived from a one-sided article, we'd inherit its bias and call
it balanced. Building the map from the topic alone makes it a neutral yardstick:
the article is diffed against it to detect omission, adopted framing, and the two
opposite failures of **both-sidesing** a settled issue and presenting a
**contested** point as settled. External per-claim fact-checking (retrieval) is a
deliberate future opt-in; today the map (model knowledge) is the grounding.

## Running it

### Backend (port 8002)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env   # then put your ANTHROPIC_API_KEY in .env
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8002
```

API docs at http://localhost:8002/docs

### Frontend (port 5175)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5175

## API

- `POST /api/analysis/analyze` → blocking, returns the full `BiasReport`.
- `POST /api/analysis/stream` → SSE, emits `AnalysisEvent`s as each stage lands.

Both accept `{ "url": "..." }` **or** `{ "text": "..." }` (exactly one).
