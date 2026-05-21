# M40 Response-Aux Diagnostics Plan

Last updated: 2026-05-21

## Motivation

M37 produced the strongest response-critical signal so far, but M39 showed that
continuing on a sharper corpus can weaken that signal. The project currently
does not log or evaluate the response-prediction auxiliary objective directly,
so checkpoint selection is based only on downstream success and ablation
effects.

M40 should add diagnostics for the response auxiliary head before the next
training change.

## Planned Work

- Log response auxiliary loss in PPO train metrics when the auxiliary is
  enabled.
- Add an offline response-prediction evaluator for checkpoint comparisons.
- Evaluate M34, M37_102, and M39 candidates on M35/M38 corpus rollouts.
- Report prediction loss by horizon step for multi-step heads.
- Keep the actor input contract unchanged; this is diagnostic only.

## Why This Matters

If M37's response-critical behavior came from a genuinely better future
response model, M37_102 should have lower multi-step prediction error than M34
or M39 on response-change cases. If not, the auxiliary objective may be acting
as incidental regularization, and the next architecture should change the
latent objective rather than tuning the corpus mix again.
