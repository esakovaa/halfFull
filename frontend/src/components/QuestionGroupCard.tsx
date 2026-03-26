'use client';

import type { Question } from '@/src/lib/questions';
import { MODULE_COLORS, MODULE_LABELS } from '@/src/lib/questions';
import { AnswerSingle } from './AnswerSingle';
import { AnswerNumeric } from './AnswerNumeric';

interface Props {
  questions: Question[];
  answers: Record<string, unknown>;
  onAnswer: (questionId: string, val: unknown) => void;
  errors?: Record<string, string | Record<string, string>>;
}

function renderInput(
  question: Question,
  value: unknown,
  onChange: (val: unknown) => void,
  error?: string | Record<string, string>
) {
  switch (question.type) {
    case 'binary':
    case 'categorical':
    case 'ordinal':
      return (
        <AnswerSingle
          options={question.options}
          value={value as string | undefined}
          onChange={onChange}
          layout={question.answer_layout}
        />
      );
    case 'numeric':
      return (
        <AnswerNumeric
          value={value as string | undefined}
          onChange={onChange}
          min={question.validation?.min}
          max={question.validation?.max}
          error={typeof error === 'string' ? error : undefined}
        />
      );
    default:
      return null;
  }
}

export function QuestionGroupCard({ questions, answers, onAnswer, errors = {} }: Props) {
  if (questions.length === 0) return null;

  const first = questions[0];
  const accentColor = MODULE_COLORS[first.module] ?? '#A2B6CB';
  const moduleLabel = MODULE_LABELS[first.module] ?? first.moduleTitle;

  return (
    <div className="section-card flex flex-col gap-6 p-6">
      {/* Module tag */}
      <span
        className="pill-tag text-[var(--color-ink)] self-start"
        style={{ backgroundColor: `${accentColor}44` }}
      >
        {moduleLabel}
      </span>

      {/* Individual questions */}
      {questions.map((q) => (
        <div key={q.id} className="flex flex-col gap-3">
          <h3 className="text-[1.15rem] font-semibold leading-snug tracking-[-0.03em] text-[var(--color-ink)]">
            {q.text}
          </h3>
          {q.help_text && (
            <p className="-mt-1 max-w-[30rem] text-sm leading-6 text-[var(--color-ink-soft)]">
              {q.help_text}
            </p>
          )}
          {renderInput(q, answers[q.id], (val) => onAnswer(q.id, val), errors[q.id])}
        </div>
      ))}
    </div>
  );
}
