'use client';

const C = {
  ink: '#09090f',
  inkSoft: '#5f6783',
  accent: '#7765f4',
  lime: '#d7f068',
  card: '#f8f8fb',
  cardMuted: '#eaedf8',
};

const rows = [
  {
    benefit: 'Probable causes ranked by likelihood',
    contrast: 'vs. generic list from GPT',
    note: 'Based on your specific symptom pattern, not a one-size answer.',
  },
  {
    benefit: 'Structured fatigue questionnaire',
    contrast: 'vs. one vague prompt',
    note: 'Covers sleep, nutrition, hormones, mental load, and more.',
  },
  {
    benefit: 'Clear priorities and next steps',
    contrast: 'vs. long, unfocused answers',
    note: 'Know exactly what to track, test, or ask your doctor first.',
  },
  {
    benefit: 'Doctor-ready summary included',
    contrast: 'vs. not actionable',
    note: 'Bring a structured overview to your next appointment.',
  },
];

export default function SectionsC() {
  return (
    <div style={{ background: `linear-gradient(180deg, #bcc8e8 0%, #b4bfe1 100%)`, minHeight: '100vh', display: 'flex', justifyContent: 'center', padding: '40px 16px', fontFamily: '"Space Grotesk", system-ui, sans-serif' }}>
      <div style={{ width: '100%', maxWidth: 420, display: 'flex', flexDirection: 'column', gap: 16 }}>

        <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase', color: C.inkSoft, marginBottom: 4 }}>Option C</p>

        {/* Merged single section */}
        <section style={{ background: C.card, borderRadius: 24, padding: '24px 20px', boxShadow: '0 14px 30px rgba(86,98,145,0.13)' }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.accent, marginBottom: 6 }}>What you actually get</p>
          <p style={{ fontSize: 13, color: C.inkSoft, lineHeight: 1.6, marginBottom: 22 }}>
            Built for fatigue — not generic advice
          </p>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {rows.map((row, i) => (
              <div key={i} style={{
                paddingTop: i === 0 ? 0 : 18,
                paddingBottom: i < rows.length - 1 ? 18 : 0,
                borderBottom: i < rows.length - 1 ? '1px solid rgba(151,166,210,0.18)' : 'none',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 5 }}>
                  <p style={{ fontSize: 15, fontWeight: 700, color: C.ink, lineHeight: 1.3, letterSpacing: '-0.02em', flex: 1, fontFamily: '"Archivo", "Arial Narrow", sans-serif' }}>{row.benefit}</p>
                  <p style={{ fontSize: 11, color: 'rgba(151,166,210,0.8)', fontStyle: 'italic', whiteSpace: 'nowrap', paddingTop: 2, flexShrink: 0 }}>{row.contrast}</p>
                </div>
                <p style={{ fontSize: 12, color: C.inkSoft, lineHeight: 1.55 }}>{row.note}</p>
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
}
