interface Props {
  onClose: () => void
}

const DIMENSIONS: { label: string; blurb: string }[] = [
  {
    label: 'Loaded language',
    blurb: 'Emotionally charged or slanted word choice that nudges the reader toward a judgment.',
  },
  {
    label: 'Source balance',
    blurb: 'Whether multiple sides are quoted, and whether one side gets more — or more sympathetic — airtime.',
  },
  {
    label: 'Framing',
    blurb: 'The narrative imposed on events: what is treated as the default, and how cause and blame are assigned.',
  },
  {
    label: 'Factual selectivity',
    blurb: 'Cherry-picking of facts or statistics, and missing context a fair reader would need.',
  },
  {
    label: 'Omission',
    blurb: 'Relevant perspectives, facts, or stakeholders left out entirely — the dog that didn’t bark.',
  },
  {
    label: 'Tone & subjectivity',
    blurb: 'Opinion and editorializing blended into ostensibly factual reporting.',
  },
  {
    label: 'Attribution',
    blurb: 'Whether contested claims are properly sourced or simply asserted in the writer’s own voice.',
  },
  {
    label: 'Headline / lede accuracy',
    blurb: 'Whether the headline and opening match what the body actually supports.',
  },
]

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h3 className="mb-2 text-lg font-semibold text-slate-800">{title}</h3>
      <div className="space-y-3 text-[15px] leading-relaxed text-slate-600">{children}</div>
    </section>
  )
}

export default function MethodologyModal({ onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="flex h-[calc(100vh-4rem)] w-[calc(100vw-4rem)] max-w-[900px] flex-col rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header — fixed */}
        <div className="flex flex-shrink-0 items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">How Fair Witness works</h2>
            <p className="text-sm text-slate-500">The methodology behind the analysis</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-500 hover:bg-slate-100"
          >
            Close ✕
          </button>
        </div>

        {/* Content — scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto max-w-2xl">
            <Section title="What it measures">
              <p>
                Fair Witness estimates how <strong>even-handedly</strong> an article treats its
                subject — not whether you agree with it. Fairness here means balance of voices,
                grounding in evidence, and transparency about what is fact versus opinion. A piece
                can take a strong position and still be fair; it can also be technically accurate
                yet deeply slanted in what it emphasizes and omits.
              </p>
              <p>
                The analysis is <strong>genre-aware</strong>. An op-ed is allowed to argue a point
                of view, so it is judged differently from a straight news report, where editorial
                voice is a problem rather than the point.
              </p>
            </Section>

            <Section title="How the analysis works">
              <p>
                Rather than ask a single model “is this biased?”, Fair Witness breaks the question
                into focused judgments and runs them as an orchestrated pipeline. Decomposing the
                problem keeps each judgment narrow and auditable, and avoids one sprawling prompt
                blurring distinct concerns together.
              </p>
              <ol className="ml-1 space-y-3">
                <li>
                  <span className="font-semibold text-slate-700">1. Plan.</span> A planning stage
                  reads the article once, classifies it (news, op-ed, analysis…), summarizes it
                  neutrally, extracts its central claims, and <em>selects the bias dimensions that
                  actually matter</em> for this piece.
                </li>
                <li>
                  <span className="font-semibold text-slate-700">2. Map the debate.</span> Before
                  judging the article, the system builds an independent map of the topic — covered
                  in its own section below. This is the reference frame everything else is measured
                  against.
                </li>
                <li>
                  <span className="font-semibold text-slate-700">3. Examine (in parallel).</span>{' '}
                  Two things run concurrently: a panel of dimension specialists (each looking at the
                  article through one lens — language, framing, balance… — backing findings with
                  verbatim quotes, and now measuring against the map to judge what was omitted or
                  whose framing was adopted), and a claim analyst that locates each of the article’s
                  claims against the map.
                </li>
                <li>
                  <span className="font-semibold text-slate-700">4. Synthesize.</span> A final stage
                  weighs all of it into a two-axis verdict (below), a fairness label, a
                  political-lean estimate, and a plain-language summary.
                </li>
              </ol>
              <p>
                You can watch this unfold live: the plan, then the map, then each specialist and the
                claim analyst lighting up as they land, then the synthesis.
              </p>
            </Section>

            <Section title="Mapping the debate">
              <p>
                Much of bias is only visible relative to <em>what could have been said</em>. So the
                system first builds a map of the topic’s debate — its sides, each side’s typical
                arguments and talking points (flagged by whether they’re substantiated), the facts
                widely treated as settled, and the slants articles on this topic tend to exhibit.
              </p>
              <p>
                The crucial detail: the map is built <strong>blind to the article</strong>, from the
                topic alone. If we derived “the two sides” from a one-sided piece, we’d inherit its
                bias and call it balanced. Building the map independently lets us measure the article
                against a neutral expectation — what it included, what it left out, and whose framing
                it adopted.
              </p>
              <p>
                The map is also honest about <strong>structure</strong>: not every topic is evenly
                two-sided. It marks whether an issue is settled, genuinely two-sided, multi-sided, or
                not really a debate at all — which lets the analysis flag two opposite failures:
                <em>both-sidesing</em> a settled question, and presenting a genuinely contested point
                as <em>settled</em>.
              </p>
            </Section>

            <Section title="Engaging the claims">
              <p>
                A neutral-sounding article can still be unfair in substance — every sentence true,
                the overall picture skewed. So alongside the presentation specialists, a claim
                analyst takes the article’s claims and locates each against the map: does it match
                or contradict a settled fact, echo a substantiated argument or an unsubstantiated
                talking point, and does the article <em>handle</em> it fairly (or overstate,
                mislead, or assert it without support)?
              </p>
              <p>
                Note what this is and isn’t: it assesses how the article <em>handles</em> its claims
                relative to the map, rather than independently fact-checking each one against live
                sources. The map does the heavy lifting of “what’s established here,” built once.
              </p>
            </Section>

            <Section title="The dimensions">
              <p>
                The specialists are drawn from a fixed catalogue of fairness lenses. The planner
                picks the relevant subset for each article (typically four to six):
              </p>
              <ul className="space-y-2">
                {DIMENSIONS.map((d) => (
                  <li key={d.label} className="rounded-lg bg-slate-50 px-3 py-2">
                    <span className="font-medium text-slate-700">{d.label}.</span>{' '}
                    <span>{d.blurb}</span>
                  </li>
                ))}
              </ul>
            </Section>

            <Section title="How scoring works">
              <p>
                Every score runs from <strong>0 to 100, where 100 is perfectly fair and
                unbiased</strong> — higher is always better. The verdict reports{' '}
                <strong>two axes</strong>, because they can diverge:
              </p>
              <ul className="ml-5 list-disc space-y-1">
                <li>
                  <strong>Presentation</strong> — <em>how</em> it says it: language, framing, tone,
                  balance. Driven by the dimension specialists.
                </li>
                <li>
                  <strong>Substance</strong> — <em>what</em> it says: how its claims hold up against
                  the map, and what it covers or omits. Driven by the claim analysis.
                </li>
              </ul>
              <p>
                A piece can be neutral in tone but factually selective, or pointed in tone yet
                well-sourced — the two axes make that visible instead of hiding it in one number.
                The <strong>overall</strong> score is a reasoned blend of the two, <em>not a simple
                average</em>: a single high-severity, load-bearing problem on either axis pulls it
                down more than several trivial nits. The synthesizer also estimates a political lean
                with its own confidence, and flags whose framing the article adopts.
              </p>
            </Section>

            <Section title="Evidence first">
              <p>
                Findings are meant to be checkable, not taken on faith. Each specialist cites short,
                verbatim quotes from the article to justify its assessment, and frames its
                suggestions as concrete edits that would make the piece fairer. Expand any dimension
                in the report to see its evidence and recommendations.
              </p>
            </Section>

            <Section title="What this is not">
              <p>
                Fair Witness is a <strong>lens, not a verdict</strong>. It is a language-model
                judgment, so treat it as informed analysis rather than ground truth:
              </p>
              <ul className="ml-5 list-disc space-y-1">
                <li>
                  It does not independently fact-check claims against live sources — it assesses how
                  the article handles them relative to the map.
                </li>
                <li>
                  The map itself is a model-generated view of the topic, built from training
                  knowledge. It can be stale on very recent events and carries its own perspective —
                  defining “the sides” and “what’s settled” is itself a judgment, which is why the
                  map is shown to you in full rather than hidden.
                </li>
                <li>
                  Results can vary somewhat between runs, and reflect patterns the model learned
                  from its training data.
                </li>
                <li>
                  It reads the text it is given. Very long articles are truncated, and a URL is only
                  as good as the text we can extract from the page.
                </li>
              </ul>
              <p>
                Used well, it is a fast way to surface where a piece may be leaning, and to point
                you at the specific passages worth a second look.
              </p>
            </Section>
          </div>
        </div>
      </div>
    </div>
  )
}
