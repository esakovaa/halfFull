import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { writeLog } from '@/src/lib/logger';

/**
 * POST /api/bayesian-questions
 *
 * Returns structured follow-up questions for conditions that cleared the
 * ML trigger threshold (default 0.40), plus PHQ-2 / GAD-2 confounder questions.
 *
 * Body: { mlScores: Record<string, number>, patientSex?: string }
 *
 * Response:
 * {
 *   confounderQuestions: BayesianQuestion[],
 *   conditionQuestions:  ConditionQuestion[],
 * }
 */

const PROJECT_ROOT = path.resolve(process.cwd(), '..');
const PYTHON = process.env.PYTHON_BIN
  ?? path.join(PROJECT_ROOT, 'ml_project_env', 'bin', 'python3');
const SCRIPT = path.join(PROJECT_ROOT, 'bayesian', 'run_bayesian.py');

function runPython(input: object): Promise<Record<string, unknown>> {
  return new Promise((resolve) => {
    const child = spawn(PYTHON, [SCRIPT], {
      cwd: PROJECT_ROOT,
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT },
    });

    child.stdin.write(JSON.stringify(input));
    child.stdin.end();

    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk: Buffer) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk: Buffer) => { stderr += chunk.toString(); });

    child.on('close', (code) => {
      if (!stdout.trim()) {
        resolve({ error: `Python exited ${code}. stderr: ${stderr.slice(0, 400)}` });
        return;
      }
      try {
        resolve(JSON.parse(stdout.trim()) as Record<string, unknown>);
      } catch {
        resolve({ error: `Could not parse Python output: ${stdout.slice(0, 200)}` });
      }
    });

    child.on('error', (err) => resolve({ error: `Spawn failed: ${err.message}` }));
  });
}

export async function POST(req: NextRequest) {
  let mlScores: Record<string, number>;
  let patientSex: string | undefined;

  try {
    const body = await req.json() as { mlScores?: unknown; patientSex?: unknown };
    mlScores   = (body.mlScores ?? {}) as Record<string, number>;
    patientSex = typeof body.patientSex === 'string' ? body.patientSex : undefined;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const result = await runPython({ mode: 'questions', ml_scores: mlScores, patient_sex: patientSex });

  if (result.error) {
    writeLog('bayesian_questions_error', { mlScores, error: result.error });
    return NextResponse.json({ error: result.error }, { status: 500 });
  }

  writeLog('bayesian_questions', { mlScores, result });
  return NextResponse.json(result);
}
