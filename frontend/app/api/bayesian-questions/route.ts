import { NextRequest, NextResponse } from 'next/server';
import { writeLog } from '@/src/lib/logger';

/**
 * POST /api/bayesian-questions
 *
 * Returns structured follow-up questions for conditions that cleared the
 * ML trigger threshold (default 0.40), plus PHQ-2 / GAD-2 confounder questions.
 *
 * Body: { mlScores: Record<string, number>, patientSex?: string, existingAnswers?: Record<string, unknown> }
 *
 * Response:
 * {
 *   confounderQuestions: BayesianQuestion[],
 *   conditionQuestions:  ConditionQuestion[],
 * }
 */

const RAILWAY_URL = process.env.RAILWAY_API_URL ?? 'http://localhost:8000';

async function callRailway(body: object): Promise<Record<string, unknown>> {
  const res = await fetch(`${RAILWAY_URL}/bayesian/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await res.json() as Record<string, unknown>;

  if (!res.ok || data.error) {
    return { error: String(data.error ?? `Railway returned ${res.status}`) };
  }

  return data;
}

export async function POST(req: NextRequest) {
  let mlScores: Record<string, number>;
  let patientSex: string | undefined;
  let existingAnswers: Record<string, unknown>;

  try {
    const body = await req.json() as { mlScores?: unknown; patientSex?: unknown; existingAnswers?: unknown };
    mlScores = (body.mlScores ?? {}) as Record<string, number>;
    patientSex = typeof body.patientSex === 'string' ? body.patientSex : undefined;
    existingAnswers = (body.existingAnswers ?? {}) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const result = await callRailway({ mode: 'questions', ml_scores: mlScores, patient_sex: patientSex, existing_answers: existingAnswers });

  if (result.error) {
    writeLog('bayesian_questions_error', { mlScores, error: result.error });
    return NextResponse.json({ error: result.error }, { status: 500 });
  }

  writeLog('bayesian_questions', { mlScores, result });
  return NextResponse.json(result);
}
