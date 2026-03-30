import { NextRequest, NextResponse } from 'next/server';
import { applyHardSafetyRules, validateDeepAnalyzeSchema } from '@/lib/medgemma-safety';
import { rewriteDeepAnalyzeTone } from '@/src/lib/server/deepAnalyzeSafety';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const candidate = (body?.report ?? body) as Record<string, unknown>;
  const inputValidation = validateDeepAnalyzeSchema(candidate);
  if (!inputValidation.ok) {
    return NextResponse.json(
      { error: 'invalid_input_schema', detail: inputValidation.reason },
      { status: 400 },
    );
  }

  const rewriteResult = await rewriteDeepAnalyzeTone(inputValidation.data);
  const safetyResult = applyHardSafetyRules(rewriteResult.data);
  const response = NextResponse.json(safetyResult.data);
  response.headers.set('x-safety-rewrite-source', rewriteResult.rewriteSource);
  if (rewriteResult.groqStatus !== undefined) {
    response.headers.set('x-safety-groq-status', String(rewriteResult.groqStatus));
  }
  if (rewriteResult.groqErrorSnippet) {
    response.headers.set(
      'x-safety-groq-error-snippet',
      encodeURIComponent(rewriteResult.groqErrorSnippet),
    );
  }
  response.headers.set(
    'x-safety-hard-rules-applied',
    safetyResult.warnings.length > 0 ? 'true' : 'false',
  );
  response.headers.set(
    'x-safety-hard-rule-count',
    String(safetyResult.warnings.length),
  );
  return response;
}
