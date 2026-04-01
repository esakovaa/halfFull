'use client';

import Link from 'next/link';
import { useState, useRef } from 'react';

const outcomes = [
  { title: 'Probable causes ranked', desc: 'The most likely reasons behind your fatigue, ordered by how well they match your answers.' },
  { title: 'A clear action list', desc: 'Concrete next steps — what to track, what to ask your doctor, what to rule out first.' },
  { title: 'A doctor-ready summary', desc: 'A structured overview you can bring to your appointment so nothing gets missed.' },
];

const comparisonRows = [
  {
    halfFull: 'Every symptom is accounted for',
    halfFullDesc: 'Structured input means nothing gets skipped or misread.',
    gpt: 'Easy to miss what you didn\'t think to mention',
  },
  {
    halfFull: 'Outputs you can trust',
    halfFullDesc: 'Safety layers flag when something is outside the model\'s confidence — it won\'t just guess.',
    gpt: 'Confident-sounding answers that may be wrong',
  },
  {
    halfFull: 'Shows its reasoning',
    halfFullDesc: 'You see why each possible cause was flagged — not just what.',
    gpt: 'No way to know how it reached its answer',
  },
  {
    halfFull: 'Built only for fatigue',
    halfFullDesc: 'Trained on real population health data. Not a general knowledge base.',
    gpt: 'Generic health knowledge, not fatigue-specific',
  },
  {
    halfFull: 'Gives you something to bring to your doctor',
    halfFullDesc: 'Clear, prioritised findings — not a wall of text to sort through yourself.',
    gpt: 'Long answers you\'d need to summarise yourself',
  },
];

const faqs = [
  {
    question: 'What does HalfFull actually do?',
    answer: 'HalfFull guides you through a short questionnaire and turns your answers into possible causes, clear priorities, and a summary you can bring to your doctor.',
  },
  {
    question: 'Does it give me a diagnosis?',
    answer: 'No. It does not diagnose conditions. It helps you organize what may be worth discussing with a clinician.',
  },
  {
    question: 'How long does it take?',
    answer: 'Most people finish in about 10 minutes.',
  },
  {
    question: 'Is it still useful if I do not have lab values?',
    answer: 'Yes. It can still be useful based on symptoms and history alone. Lab results can add context later, but they are not required.',
  },
  {
    question: 'Does this replace seeing a doctor?',
    answer: 'No. It is meant to support a doctor visit, not replace one.',
  },
  {
    question: 'Is my data safe?',
    answer: 'Your answers stay within the product experience needed to generate your results. Review the product privacy details for the latest information about storage and handling.',
  },
  {
    question: 'Is this medical advice?',
    answer: 'No. HalfFull is an informational support tool. It does not provide medical advice, diagnosis, or treatment.',
  },
  {
    question: 'Can HalfFull be wrong?',
    answer: 'Yes. The results are not a diagnosis and may miss context or point to the wrong explanation. Use them as structured support for a conversation with your doctor.',
  },
];

// Exact archive graphic — overlapping blobs with color-transition gradient
function JourneyRibbon() {
  return (
    <svg
      viewBox="0 0 360 92"
      className="h-20 w-full"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="journeyGradient" x1="14" y1="46" x2="346" y2="46" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7765f4" />
          <stop offset="0.32" stopColor="#d49ac8" />
          <stop offset="0.62" stopColor="#f0af93" />
          <stop offset="1" stopColor="#d7f068" />
        </linearGradient>
      </defs>
      <g opacity="0.95">
        <circle cx="48" cy="46" r="34" fill="#7765f4" />
        <circle cx="102" cy="46" r="34" fill="#d49ac8" fillOpacity="0.82" />
        <path
          d="M135 12c22 0 32 13 45 13s23-13 45-13c28 0 49 25 49 34s-21 34-49 34c-22 0-32-13-45-13s-23 13-45 13c-28 0-49-25-49-34s21-34 49-34Z"
          fill="url(#journeyGradient)"
        />
        <circle cx="286" cy="46" r="34" fill="#edf3a8" fillOpacity="0.88" />
        <circle cx="332" cy="46" r="34" fill="#d7f068" fillOpacity="0.95" />
      </g>
    </svg>
  );
}

function FaqItem({
  answer,
  index,
  isOpen,
  onToggle,
  question,
}: {
  answer: string;
  index: number;
  isOpen: boolean;
  onToggle: () => void;
  question: string;
}) {
  return (
    <div className={`rounded-[1.4rem] border px-4 py-2 transition-colors ${isOpen ? 'border-[rgba(119,101,244,0.2)] bg-white/84 shadow-[0_14px_26px_rgba(86,98,145,0.08)]' : 'border-[rgba(151,166,210,0.22)] bg-white/62'}`}>
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 py-3.5 text-left"
      >
        <span className="pr-2 text-[0.9rem] font-bold leading-6 text-[var(--color-ink)]">{question}</span>
        <span aria-hidden="true" className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border transition-colors ${isOpen ? 'border-[rgba(119,101,244,0.24)] bg-[rgba(119,101,244,0.1)] text-[var(--color-accent)]' : 'border-[rgba(151,166,210,0.22)] bg-[var(--color-card-muted)] text-[var(--color-ink)]'}`}>
          <svg viewBox="0 0 20 20" aria-hidden="true" className={`h-3.5 w-3.5 transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m7 4 6 6-6 6" />
          </svg>
        </span>
      </button>
      {isOpen && (
        <div className="border-t border-[rgba(151,166,210,0.18)] pb-4 pt-3 pr-6 text-sm leading-6 text-[var(--color-ink-soft)]">
          {answer}
        </div>
      )}
    </div>
  );
}

export default function StartPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [faqVisible, setFaqVisible] = useState(false);
  const faqRef = useRef<HTMLElement>(null);

  return (
    <div className="phone-frame flex flex-col">


      <main className="flex flex-1 flex-col px-5 py-6 pb-12">
        <div className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-5">

          {/* Header */}
          <header className="flex items-center justify-between">
            <span style={{ fontFamily: 'Archivo, sans-serif', fontSize: 18, letterSpacing: '-0.02em', lineHeight: 1 }}>
              <span style={{ fontWeight: 400, color: 'var(--color-ink-soft)' }}>half</span>
              <span style={{ fontWeight: 900, color: 'var(--color-ink)' }}>Full</span>
            </span>
            <button
              type="button"
              onClick={() => {
                setFaqVisible(true);
                setTimeout(() => faqRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
              }}
              className="rounded-full border border-[rgba(9,9,15,0.12)] bg-white/75 px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.1em] text-[var(--color-ink-soft)]"
            >
              FAQ
            </button>
          </header>

          {/* Hero card */}
          <section className="relative overflow-hidden rounded-[2rem] bg-[var(--color-card)] px-5 py-7 shadow-[0_14px_30px_rgba(86,98,145,0.14)]">
            <div className="pointer-events-none absolute -left-10 top-6 h-32 w-32 rounded-full bg-[rgba(119,101,244,0.08)] blur-[54px]" />
            <div className="pointer-events-none absolute -right-5 top-20 h-36 w-36 rounded-full bg-[rgba(212,154,200,0.08)] blur-[60px]" />
            <div className="relative">
              <h1 className="editorial-display text-[clamp(2.1rem,8vw,3rem)] leading-[1.0] text-[var(--color-ink)]">
                Fatigue has patterns.<br />Let&apos;s find yours.
              </h1>

              <p className="mt-4 max-w-[21rem] text-[0.95rem] leading-7 text-[var(--color-ink-soft)]">
                Tired of not being taken seriously?<br />Get clarity before your next doctor visit.
              </p>

              {/* Archive journey ribbon */}
              <div className="mt-6 mb-2">
                <JourneyRibbon />
              </div>

              {/* Step labels */}
              <div className="grid grid-cols-3 gap-3 mb-7">
                {[
                  { lines: ['Take the', 'test'], color: '#7765f4', body: 'Answer questions about your symptoms' },
                  { lines: ['We analyse', 'patterns'], color: '#c4692a', body: 'Get matched against real clinical research data' },
                  { lines: ['Get your', 'results'], color: '#6aaa08', body: 'Up to 3 possible causes explained and actionable next steps' },
                ].map((step) => (
                  <div key={step.lines[1]} className="flex flex-col items-center text-center">
                    {step.lines.map((line) => (
                      <span key={line} className="block text-[0.95rem] font-bold leading-[1.25]" style={{ color: step.color }}>{line}</span>
                    ))}
                    <span className="mt-1.5 block text-[0.68rem] leading-[1.4] text-[var(--color-ink-soft)]">{step.body}</span>
                  </div>
                ))}
              </div>

              <Link
                href="/consent"
                className="block w-full rounded-full py-4 text-center text-[0.95rem] font-bold shadow-[0_10px_24px_rgba(9,9,15,0.12)] transition-all duration-200 active:scale-[0.98]"
                style={{ backgroundColor: 'var(--color-lime)', color: 'var(--color-ink)' }}
              >
                Take the assessment test
              </Link>
            </div>
          </section>

          {/* What you get — Option B: left-border statements */}
          <section className="section-card px-5 py-5">
            <p className="mb-5 text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-accent)]">What you get</p>
            <div className="flex flex-col">
              {outcomes.map((item, i) => (
                <div
                  key={item.title}
                  className={`border-l-[3px] border-[var(--color-accent)] pl-4 ${i < outcomes.length - 1 ? 'mb-5 pb-5 border-b border-b-[rgba(151,166,210,0.18)]' : ''}`}
                >
                  <p className="text-[1.05rem] font-bold leading-[1.2] tracking-[-0.03em] text-[var(--color-ink)]" style={{ fontFamily: 'Archivo, sans-serif' }}>{item.title}</p>
                  <p className="mt-1.5 text-[0.82rem] leading-[1.6] text-[var(--color-ink-soft)]">{item.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Comparison — aligned rows, HalfFull elevated */}
          <div className="relative">
            {/* Left column visual border + shadow */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-1/2 rounded-[1.25rem] border border-[var(--color-accent)] shadow-[0_6px_24px_rgba(119,101,244,0.18)] z-10" />

            {/* Header row */}
            <div className="grid grid-cols-2">
              <div className="px-4 py-3.5 border-b border-[rgba(119,101,244,0.14)]">
                <p className="text-[0.88rem] font-bold text-[var(--color-accent)]" style={{ fontFamily: 'Archivo, sans-serif' }}>With HalfFull</p>
              </div>
              <div className="px-4 py-3.5 border-b border-[rgba(151,166,210,0.14)]">
                <p className="text-[0.88rem] font-bold text-[var(--color-ink-soft)]" style={{ fontFamily: 'Archivo, sans-serif' }}>With ChatGPT</p>
              </div>
            </div>

            {/* Content rows — each pair in same grid so heights match */}
            {comparisonRows.map((row, i) => (
              <div key={i} className="grid grid-cols-2">
                <div className={`px-4 py-3.5 flex items-start gap-2.5 ${i > 0 ? 'border-t border-[rgba(119,101,244,0.08)]' : ''}`}>
                  <span className="mt-0.5 inline-flex h-[17px] w-[17px] shrink-0 items-center justify-center rounded-full bg-[rgba(119,101,244,0.12)] text-[9px] font-bold text-[var(--color-accent)]">✓</span>
                  <div>
                    <p className="text-[0.82rem] font-bold leading-[1.35] text-[var(--color-ink)]">{row.halfFull}</p>
                    <p className="mt-0.5 text-[0.71rem] leading-[1.5] text-[var(--color-ink-soft)]">{row.halfFullDesc}</p>
                  </div>
                </div>
                <div className={`px-4 py-3.5 flex items-start gap-2 ${i > 0 ? 'border-t border-[rgba(151,166,210,0.1)]' : ''}`}>
                  <span className="mt-1 text-[9px] text-[rgba(200,100,80,0.65)] shrink-0 leading-none">✕</span>
                  <p className="text-[0.82rem] leading-[1.5] text-[var(--color-ink-soft)]">{row.gpt}</p>
                </div>
              </div>
            ))}
          </div>

          {/* FAQ */}
          {faqVisible && (
            <section ref={faqRef} className="section-card px-5 py-5">
              <h2 className="mb-4 text-[1.05rem] font-bold tracking-[-0.02em] text-[var(--color-ink)]">FAQ</h2>
              <div className="space-y-3">
                {faqs.map((item, index) => (
                  <FaqItem
                    key={item.question}
                    index={index}
                    question={item.question}
                    answer={item.answer}
                    isOpen={openFaq === index}
                    onToggle={() => setOpenFaq((c) => (c === index ? null : index))}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Disclaimer */}
          <section className="border-t border-[rgba(151,166,210,0.24)] px-1 pt-5 pb-4">
            <p className="text-xs leading-6 text-[rgba(95,103,131,0.92)]">
              Based on clinical research · Used by 14,000+ people · Trusted by Doctolib<br />
              HalfFull does not provide medical diagnoses or treatment. It helps you prepare for a conversation with a healthcare professional.
            </p>
          </section>

        </div>
      </main>
    </div>
  );
}
