# Frontend Results UI Changes

This document tracks the UI/UX polish changes made to the HalfFull `/results` page so follow-up iterations stay easy to review and extend.

## Scope

Files currently involved:

- `frontend/app/results/page.tsx`
- `frontend/src/components/results/DiagnosisCard.tsx`

## Goals of this pass

- simplify the hero area
- move primary report actions to the bottom of the page
- reduce visual clutter
- make condition cards and doctor cards feel more cohesive
- preserve results logic, scoring, ranking inputs, persistence, and API behavior

## Implemented changes

### 1. Hero simplification

The hero teaser now contains only:

- eyebrow text
- hero title
- dynamic subline

Removed from the hero:

- CTA buttons
- additional explanatory copy

New hero subline:

- `We analyzed your answers across 12 fatigue-related conditions - most are unlikely, but X are worth a closer look.`

Dynamic behavior:

- `X` is computed from `diagnoses.length`
- this matches the number of cards rendered under the conditions section

### 2. Bottom CTA area

The main action area was moved to the bottom of the results page.

Current CTAs:

- `Email this report`
- `Save report`

Supporting hint:

- `Optional. If you skip this, your data stays only in this browser session. If you save the report, we store your responses so you can come back to them later.`

### 3. Removed card

Removed:

- `The most serious symptoms you shared`

This includes both the populated card and its loading/skeleton fallback.

### 4. Section title update

Changed:

- `Areas worth checking`

To:

- `Conditions worth checking`

### 5. Condition card cleanup

In `DiagnosisCard.tsx`:

- removed the black circled rank number
- moved the diagnosis emoji into the left icon position
- increased emoji prominence
- removed the signal pill entirely
- kept only:
  - confidence
  - urgency
- updated the condition title to a stronger h3-like treatment
- increased spacing in the expanded card from the previous tighter layout to a more breathable layout

### 6. Confidence and urgency color logic

Previous behavior:

- confidence and urgency styling depended on tier/level-specific color families

Current behavior:

- confidence UI uses fixed background color `#d7f06859`
- urgency UI uses fixed background color `#efb9732e`

This applies both to:

- collapsed pills
- expanded info boxes

### 7. Doctor section updates

In the `Next steps - Talk to a doctor` section:

- section heading was updated to use a stronger card-title / assessment-like h3 treatment
- doctor cards no longer use black circled numbers
- doctor cards now use specialty-related emojis in the left slot
- toggle icon changed from `+ / -` to the same chevron treatment used on diagnosis cards

Current specialty emoji mapping:

- `Sleep Specialist` -> `😴`
- `Endocrinologist` -> `🦋`
- `Long COVID / ME·CFS Clinic` -> `🦠`
- `Functional Medicine or Psychiatry` -> `🧠`
- fallback -> `🩺`

### 8. Header cleanup

In the results header:

- the `halfFull` logo now links to `/start`
- the `Exit` link was removed
- the `Review` link remains

## Things intentionally left unchanged

These were explicitly not changed in this pass:

- scoring
- diagnosis ranking logic
- model output handling
- backend APIs
- persistence behavior
- doctor kit export behavior
- KNN signal logic
- MedGemma deep-result reading flow

## Notes / follow-up candidates

Possible next iteration topics:

- decide whether the `Review` link in the header should remain or be simplified further
- polish the bottom CTA copy and hierarchy
- review whether the doctor badge colors should also be normalized
- review the remaining fallback / KNN copy for tone consistency with the rest of the page
- decide whether the hero title itself should be tightened in a later pass

## Verification status

Verified:

- ESLint passes for:
  - `frontend/app/results/page.tsx`
  - `frontend/src/components/results/DiagnosisCard.tsx`

Known unrelated issue:

- `tsc --noEmit` still reports a pre-existing TypeScript error in:
  - `frontend/app/designs/sections-b/page.tsx`

That issue is outside the `/results` page work and was not introduced by this pass.
