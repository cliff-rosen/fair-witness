import { Link } from 'react-router-dom'

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

const FAQ: { q: string; a: React.ReactNode }[] = [
  {
    q: 'Is this telling me what’s true?',
    a: 'No. Fair Witness measures how even-handedly an article is written — balance, evidence, transparency — not whether its claims are factually correct. It’s a lens, not a verdict.',
  },
  {
    q: 'Does it fact-check the article?',
    a: 'Not against live sources. It builds an independent map of the topic from model knowledge, then judges how the article handles its claims relative to that map. Treat it as informed analysis, not ground truth.',
  },
  {
    q: 'Will the same article always get the same score?',
    a: 'Roughly, but not exactly — it’s a language-model judgment, so results can vary somewhat between runs.',
  },
  {
    q: 'Why do I need a passphrase to run one?',
    a: 'Each analysis calls a paid AI model. The passphrase keeps that cost in check while letting anyone read and share the results freely. You only need it to start a new analysis.',
  },
  {
    q: 'Can I share a result?',
    a: 'Yes — every analysis gets a permanent public link. Anyone can open it, no passphrase required. That’s the whole idea: post it, send it, compare notes.',
  },
]

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="mb-2 text-lg font-semibold text-slate-800">{title}</h2>
      <div className="space-y-3 text-[15px] leading-relaxed text-slate-600">{children}</div>
    </section>
  )
}

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-800">About Fair Witness</h1>
        <p className="mt-1 text-slate-500">What it measures, how it works, and what it isn’t.</p>
      </header>

      <Section title="What it measures">
        <p>
          Fair Witness estimates how <strong>even-handedly</strong> an article treats its subject —
          not whether you agree with it. Fairness here means balance of voices, grounding in
          evidence, and transparency about what is fact versus opinion. A piece can take a strong
          position and still be fair; it can also be technically accurate yet deeply slanted in what
          it emphasizes and omits.
        </p>
        <p>
          The analysis is <strong>genre-aware</strong>. An op-ed is allowed to argue a point of
          view, so it is judged differently from a straight news report, where editorial voice is a
          problem rather than the point.
        </p>
      </Section>

      <Section title="How the analysis works">
        <p>
          Rather than ask a single model “is this biased?”, Fair Witness breaks the question into
          focused judgments and runs them as an orchestrated pipeline. Decomposing the problem keeps
          each judgment narrow and auditable, and avoids one sprawling prompt blurring distinct
          concerns together.
        </p>
        <ol className="ml-1 space-y-3">
          <li>
            <span className="font-semibold text-slate-700">1. Plan.</span> A planning stage reads
            the article once, classifies it (news, op-ed, analysis…), summarizes it neutrally,
            extracts its central claims, and <em>selects the bias dimensions that actually
            matter</em> for this piece.
          </li>
          <li>
            <span className="font-semibold text-slate-700">2. Map the debate.</span> Before judging
            the article, the system builds an independent map of the topic (see below). This is the
            reference frame everything else is measured against.
          </li>
          <li>
            <span className="font-semibold text-slate-700">3. Examine (in parallel).</span> A panel
            of dimension specialists each looks at the article through one lens — language, framing,
            balance… — backing findings with verbatim quotes and measuring against the map, while a
            claim analyst locates each of the article’s claims against the map.
          </li>
          <li>
            <span className="font-semibold text-slate-700">4. Synthesize.</span> A final stage weighs
            all of it into a two-axis verdict, a fairness label, a political-lean estimate, and a
            plain-language summary.
          </li>
        </ol>
        <p>
          You can watch this unfold live: the plan, then the map, then each specialist and the claim
          analyst lighting up as they land, then the synthesis.
        </p>
      </Section>

      <Section title="Mapping the debate">
        <p>
          Much of bias is only visible relative to <em>what could have been said</em>. So the system
          first builds a map of the topic’s debate — its sides, each side’s typical arguments and
          talking points (flagged by whether they’re substantiated), the facts widely treated as
          settled, and the slants articles on this topic tend to exhibit.
        </p>
        <p>
          The crucial detail: the map is built <strong>blind to the article</strong>, from the topic
          alone. If we derived “the two sides” from a one-sided piece, we’d inherit its bias and call
          it balanced. Building the map independently lets us measure the article against a neutral
          expectation — what it included, what it left out, and whose framing it adopted.
        </p>
        <p>
          The map is also honest about <strong>structure</strong>: not every topic is evenly
          two-sided. It marks whether an issue is settled, genuinely two-sided, multi-sided, or not
          really a debate — which lets the analysis flag two opposite failures:{' '}
          <em>both-sidesing</em> a settled question, and presenting a genuinely contested point as{' '}
          <em>settled</em>.
        </p>
      </Section>

      <Section title="How scoring works">
        <p>
          Every score runs from <strong>0 to 100, where 100 is perfectly fair and unbiased</strong> —
          higher is always better. The verdict reports <strong>two axes</strong>, because they can
          diverge:
        </p>
        <ul className="ml-5 list-disc space-y-1">
          <li>
            <strong>Presentation</strong> — <em>how</em> it says it: language, framing, tone,
            balance. Driven by the dimension specialists.
          </li>
          <li>
            <strong>Substance</strong> — <em>what</em> it says: how its claims hold up against the
            map, and what it covers or omits. Driven by the claim analysis.
          </li>
        </ul>
        <p>
          The <strong>overall</strong> score is a reasoned blend of the two, <em>not a simple
          average</em>: a single high-severity, load-bearing problem on either axis pulls it down
          more than several trivial nits.
        </p>
      </Section>

      <Section title="The dimensions">
        <p>
          The specialists are drawn from a fixed catalogue of fairness lenses. The planner picks the
          relevant subset for each article (typically four to six):
        </p>
        <ul className="space-y-2">
          {DIMENSIONS.map((d) => (
            <li key={d.label} className="rounded-lg bg-slate-50 px-3 py-2">
              <span className="font-medium text-slate-700">{d.label}.</span> <span>{d.blurb}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="What this is not">
        <p>
          Fair Witness is a <strong>lens, not a verdict</strong>. It is a language-model judgment, so
          treat it as informed analysis rather than ground truth. It does not independently
          fact-check claims against live sources; the map itself is a model-generated view of the
          topic that can be stale on very recent events; and results can vary between runs. Used
          well, it’s a fast way to surface where a piece may be leaning and to point you at the
          specific passages worth a second look.
        </p>
      </Section>

      <Section title="FAQ">
        <dl className="space-y-4">
          {FAQ.map((item) => (
            <div key={item.q} className="rounded-lg border border-slate-200 bg-white p-4">
              <dt className="font-semibold text-slate-800">{item.q}</dt>
              <dd className="mt-1 text-slate-600">{item.a}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <div className="mt-10 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-6 text-center">
        <p className="font-semibold text-slate-700">Ready to try it?</p>
        <Link
          to="/"
          className="mt-3 inline-block rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
        >
          Analyze an article
        </Link>
      </div>
    </div>
  )
}
