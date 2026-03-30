import { validateDeepAnalyzeSchema, type DeepAnalyzeResult } from '@/lib/medgemma-safety';

const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';
const GROQ_MODEL = 'llama-3.1-8b-instant';
// V7: primary synthesis model; fallback chain: groq-70b → groq-8b → openai-4o-mini
const GROQ_SYNTHESIS_MODEL = 'llama-3.3-70b-versatile';
const GROQ_SYNTHESIS_FALLBACK_MODEL = 'llama-3.1-8b-instant';
const OPENAI_SYNTHESIS_MODEL = 'gpt-4o-mini';

const SAFETY_SYSTEM_PROMPT = `You are a medical communication safety filter. Rewrite only the user-facing narrative fields so they stay warm, non-diagnostic, and appropriately uncertain.

Rules:
- Never say a diagnosis is confirmed unless the input explicitly says it is already medically confirmed
- Use possibility framing such as "may suggest", "could indicate", and "worth discussing with your doctor"
- Remove alarmist wording, but do not soften or delete urgent safety guidance when red-flag symptoms are present
- Remove dismissive reassurance such as "nothing serious", "you are fine", "safe to ignore", "safe to stay home", "no need to see a doctor", "just stress", "watch and see", "likely benign", "not worrisome", or long delays like "wait a few weeks" / "wait a month" / "wait a year"
- If the content mentions red-flag symptoms such as chest pain, breathlessness, black stools, jaundice, confusion, fainting, near-fainting, or palpitations, the output must keep or add urgent review language such as "urgent", "prompt", "same day", "today", "immediate", or "emergency"
- Keep the same overall meaning, specificity, and structure
- Rewrite these user-facing narrative fields when present: summaryPoints[], personalizedSummary, declinedSuspicions[].reason, recoveryOutlook, insights[].personalNote, nextSteps, doctorKitSummary, recommendedDoctors[].reason, doctorKits[].openingSummary, doctorKits[].whatToSay
- Do not modify immutable fields such as diagnosisId, doctorKitQuestions, doctorKitArguments, suggestedTests, symptomsToDiscuss, concerningSymptoms, recommendedTests, discussionPoints, bringToAppointment, priority, specialty
- Return valid JSON only, same schema as input`;

function parseJsonObject(raw: string): Record<string, unknown> | null {
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) return null;
  try {
    return JSON.parse(jsonMatch[0]) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function mergeWithImmutableFields(
  original: DeepAnalyzeResult,
  rewritten: DeepAnalyzeResult,
): DeepAnalyzeResult {
  return {
    ...original,
    personalizedSummary: rewritten.personalizedSummary,
    summaryPoints: rewritten.summaryPoints ?? original.summaryPoints,
    insights: original.insights.map((item, index) => ({
      diagnosisId: item.diagnosisId,
      personalNote: rewritten.insights[index]?.personalNote?.trim() || item.personalNote,
    })),
    declinedSuspicions: original.declinedSuspicions?.map((item, index) => ({
      diagnosisId: item.diagnosisId,
      reason: rewritten.declinedSuspicions?.[index]?.reason?.trim() || item.reason,
    })),
    recoveryOutlook: rewritten.recoveryOutlook ?? original.recoveryOutlook,
    nextSteps: rewritten.nextSteps,
    doctorKitSummary: rewritten.doctorKitSummary ?? original.doctorKitSummary,
    doctorKitQuestions: original.doctorKitQuestions,
    doctorKitArguments: original.doctorKitArguments,
    recommendedDoctors: original.recommendedDoctors.map((doctor, index) => ({
      ...doctor,
      reason: rewritten.recommendedDoctors[index]?.reason?.trim() || doctor.reason,
    })),
    doctorKits: original.doctorKits.map((kit, index) => ({
      ...kit,
      openingSummary: rewritten.doctorKits[index]?.openingSummary?.trim() || kit.openingSummary,
      ...(kit.whatToSay
        ? { whatToSay: rewritten.doctorKits[index]?.whatToSay?.trim() || kit.whatToSay }
        : {}),
    })),
    allClear: original.allClear,
  };
}

/**
 * V6: Primary Groq synthesis call. Takes the full synthesis prompt (built by
 * buildGroqSynthesisPromptV6 or buildAllClearPrompt) and returns a validated
 * DeepAnalyzeResult. Returns null on timeout, parse failure, or missing API key
 * so the caller can fall back gracefully.
 */
async function callGroqSynthesis(
  synthesisPrompt: string,
  groqKey: string,
  model: string,
  timeoutMs: number,
): Promise<DeepAnalyzeResult | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${groqKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content:
              'You output valid JSON only. No markdown, no thinking, no explanations, no preamble. Start your response immediately with { and end with }.',
          },
          { role: 'user', content: synthesisPrompt },
        ],
        max_tokens: 3500,
        temperature: 0.3,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errBody = await response.text().catch(() => '');
      console.warn(`[Groq synthesis][${model}] API error: ${response.status}`, errBody.slice(0, 300));
      return null;
    }

    const data = await response.json();
    const content: string = data.choices?.[0]?.message?.content ?? '';
    const parsed = parseJsonObject(content);
    if (!parsed) {
      console.warn(`[Groq synthesis][${model}] Could not parse JSON. Raw:`, content.slice(0, 500));
      return null;
    }

    const validation = validateDeepAnalyzeSchema(parsed);
    if (!validation.ok) {
      console.warn(`[Groq synthesis][${model}] Schema failed: ${validation.reason} | keys: ${Object.keys(parsed).join(', ')}`);
      return null;
    }

    return validation.data;
  } catch (err) {
    console.warn(`[Groq synthesis][${model}] Error: ${String(err)}`);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

async function callOpenAISynthesis(
  synthesisPrompt: string,
  openaiKey: string,
  timeoutMs: number,
): Promise<DeepAnalyzeResult | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${openaiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: OPENAI_SYNTHESIS_MODEL,
        messages: [
          {
            role: 'system',
            content:
              'You output valid JSON only. No markdown, no thinking, no explanations, no preamble. Start your response immediately with { and end with }.',
          },
          { role: 'user', content: synthesisPrompt },
        ],
        max_tokens: 3500,
        temperature: 0.3,
        response_format: { type: 'json_object' },
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errBody = await response.text().catch(() => '');
      console.warn(`[OpenAI synthesis][${OPENAI_SYNTHESIS_MODEL}] API error: ${response.status}`, errBody.slice(0, 300));
      return null;
    }

    const data = await response.json();
    const content: string = data.choices?.[0]?.message?.content ?? '';
    const parsed = parseJsonObject(content);
    if (!parsed) {
      console.warn(`[OpenAI synthesis] Could not parse JSON. Raw:`, content.slice(0, 500));
      return null;
    }

    const validation = validateDeepAnalyzeSchema(parsed);
    if (!validation.ok) {
      console.warn(`[OpenAI synthesis] Schema failed: ${validation.reason} | keys: ${Object.keys(parsed).join(', ')}`);
      return null;
    }

    console.info('[OpenAI synthesis] Success via fallback');
    return validation.data;
  } catch (err) {
    console.warn(`[OpenAI synthesis] Error: ${String(err)}`);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export async function synthesizeNarrativeWithGroqV6(
  synthesisPrompt: string,
): Promise<DeepAnalyzeResult | null> {
  const groqKey = process.env.GROQ_API_KEY;
  const openaiKey = process.env.OPENAI_API_KEY;

  // 1. Try primary Groq model (45s)
  if (groqKey) {
    const primary = await callGroqSynthesis(synthesisPrompt, groqKey, GROQ_SYNTHESIS_MODEL, 45_000);
    if (primary) return primary;

    // 2. Try smaller Groq model (30s)
    console.warn('[synthesis] Primary Groq failed — retrying with Groq fallback model');
    const groqFallback = await callGroqSynthesis(synthesisPrompt, groqKey, GROQ_SYNTHESIS_FALLBACK_MODEL, 30_000);
    if (groqFallback) return groqFallback;
  }

  // 3. Try OpenAI as final fallback
  if (openaiKey) {
    console.warn('[synthesis] Groq exhausted — trying OpenAI fallback');
    return callOpenAISynthesis(synthesisPrompt, openaiKey, 45_000);
  }

  return null;
}

export async function rewriteDeepAnalyzeTone(
  report: DeepAnalyzeResult,
): Promise<{
  data: DeepAnalyzeResult;
  rewriteSource:
    | 'live_groq_success'
    | 'fallback_no_groq_key'
    | 'fallback_groq_http_error'
    | 'fallback_parse_failed'
    | 'fallback_schema_failed'
    | 'fallback_exception';
  groqStatus?: number;
  groqErrorSnippet?: string;
}> {
  const groqKey = process.env.GROQ_API_KEY;
  if (!groqKey) {
    return {
      data: report,
      rewriteSource: 'fallback_no_groq_key',
    };
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const groqResponse = await fetch(GROQ_API_URL, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${groqKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [
          { role: 'system', content: SAFETY_SYSTEM_PROMPT },
          { role: 'user', content: JSON.stringify(report) },
        ],
        max_tokens: 1000,
        temperature: 0.2,
      }),
      signal: controller.signal,
    }).finally(() => clearTimeout(timeout));

    if (!groqResponse.ok) {
      const errorBody = await groqResponse.text().catch(() => '');
      return {
        data: report,
        rewriteSource: 'fallback_groq_http_error',
        groqStatus: groqResponse.status,
        groqErrorSnippet: errorBody.slice(0, 200),
      };
    }

    const groqData = await groqResponse.json();
    const content: string = groqData.choices?.[0]?.message?.content ?? '';
    const parsed = parseJsonObject(content);
    if (!parsed) {
      return {
        data: report,
        rewriteSource: 'fallback_parse_failed',
        groqErrorSnippet: content.slice(0, 200),
      };
    }

    const validation = validateDeepAnalyzeSchema(parsed);
    if (!validation.ok) {
      return {
        data: report,
        rewriteSource: 'fallback_schema_failed',
        groqErrorSnippet: validation.reason.slice(0, 200),
      };
    }

    return {
      data: mergeWithImmutableFields(report, validation.data),
      rewriteSource: 'live_groq_success',
    };
  } catch {
    return {
      data: report,
      rewriteSource: 'fallback_exception',
      groqErrorSnippet: 'exception_during_groq_fetch',
    };
  }
}
