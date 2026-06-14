# Phase-4 F2 Build + Adversarial Review (2026-06-14)

## Status

- kind: F2 trainer scaffold + adversarial-review record. The build is
  `scripts/feasibility_audit/phase4_f2_train.py` (1194 lines, 17 tests pass,
  --quick smoke only, `--full` PI-gated to refuse). prereg is a DRAFT
  (`experiments/feasibility_audit/phase4_f2_prereg.json`, `frozen=false`).
- verdict: **NOT launch-ready.** A three-way adversarial review (asymmetric
  critic/teacher, judging/statistics, RL-loop) found 6 must-fix blockers
  that the all-green smoke structurally cannot expose. Caught before any
  14-hour run — the F1 stop discipline working as intended.
- claim boundary: engineering-only; no self-ID/attribution claim; incumbent
  untouched.

## The deepest finding (scope, not a bug): F2 as built is distillation, not RL

The build's "RL term" is `relu(advantage) * (action_mean - teacher_target)^2`
with `value.detach()` (no policy gradient, no log-prob), Monte-Carlo return
broadcast to each frame (no GAE/bootstrap), and a hand-made critic
`value_proxy` (avoidance = -min_clearance_margin, drift = 0). I.e. it is
**asymmetric-critic-weighted distillation of the per-regime oracle**, not a
real asymmetric actor-critic with exploration. This re-tests a weaker
question — "can imitation of the oracle beat the reflex" — which C1-v3/C1-v4
already largely answered negative in the avoidance regime. The drift regime
is new (oracle 0.40 where reflex 0), so distilling the drift oracle could
still capture the drift prize; but a distillation-only F2 is not the
robotics-parity RL experiment the program set out to run. **This is a PI
scope decision (S3 below).**

## Must-fix before freeze + 100M launch (B1-B6)

| # | defect | fix |
|---|---|---|
| B1 | `--resume` is dead code, zero checkpointing — a 14 h run cannot survive interruption (AGENTS.md rule 4 conflict) | checkpoint per (seed,epoch) + real resume + a kill-and-resume test |
| B2 | the avoidance oracle teacher's actions are a function of `mu_true`, so distillation writes obs72-unobservable mu-dependence into the deployable actor | avoidance teacher -> pure obs72 feedback (like DriftFeedbackPolicy), or distill only the reveal-post obs72-recoverable action segment |
| B3 | only 1 of 8 training seeds is validated; the "seed-cluster SE" buckets by validation-scenario seed, faking binomial noise as cross-seed variance | validate all 8 student seeds; cluster SE by training seed |
| B4 | the CI95 / paired tests the prereg promises do not exist in code (only point differences) | implement + freeze the CI method (cross-seed paired t-CI or seed-clustered bootstrap) |
| B5 | the avoidance floor collapses to the unmodified incumbent (RLS/per-tuned factories return FixedStar for non-drift) — strawman floor | real non-trivial classical avoidance arms, or declare the floor = single fixed* and drop "max over three arms" |
| B6 | the only reward-hacking guard (Spearman) degenerates under tied scores and is not gated at >= 0.9 | per-episode Spearman, report N/A on ties, make >= 0.9 a hard gate |

## Should-fix / close in prereg before freeze (S1-S7, abridged)

- S1 DAgger-lite avoidance relabel desyncs the stateful oracle's phase (drift exact, avoidance not) -> teacher self-generates demos on student scenarios.
- S2 avoidance scenario/teacher mu collapses to a single point (mu 0.3625, reveal 9.5); E2''s prize is across a mu/reveal spectrum -> span the spectrum (this also masks B2).
- S3 (the scope fork above) — PI decides: relabel F2 as critic-gated distillation, OR build a real asymmetric actor-critic (PPO + bootstrapped privileged GAE critic + policy gradient, teacher as warm-start/auxiliary).
- S4 prereg lacks a power analysis (8 seeds vs +0.40 drift / +0.18 avoidance against expected cross-seed SD).
- S5 avoidance reward fail-open (`completion==""` counts as pass) + unsafe-grazing can score high.
- S6 drift shaping can decouple from success.
- S7 pre-check the oracle arm's ceiling on the student/hard distribution before spending 14 h.

## Preserved correct properties (do not break in the fix pass)

Disjoint seed streams (F2 base 2026061407); held-out epoch selection; scenario-paired floor-vs-student; penalty >= reward (collision 60 / pass 40); the drift teacher is the stateless obs72 `DriftFeedbackPolicy` with CEM explicitly excluded; actor input is obs72-only (dim-checked), deployable as `act(obs72)->action3`; `--full` PI-gated; incumbent only imported.

## Route

A second build pass fixes B1-B6, closes S1/S2/S4/S5/S7, and resolves the S3
scope fork per PI decision; then re-review, freeze the prereg, and launch the
100M managed run.

## Pass 2 (real RL) — review 2026-06-14 (second pass)

PI chose S3 = real RL. Pass-2 rewrote the trainer to a genuine asymmetric
actor-critic: PPO clipped surrogate + learnable log_std + entropy +
bootstrapped privileged GAE critic + policy gradient (verified line-by-line
against `src/autodrift/train_ppo.py` conventions), teacher demoted to m1087
BC warm-start + annealed auxiliary. **The science-load-bearing core is now
correct — it is real RL, not distillation.** B1-B6 from pass-1 landed.

But the second adversarial review found 4 new launch blockers (all hidden by
the quick smoke's horizon-6 ceiling/floor effects), plus should-fix items:

- **M1 (blocker, throughput)**: the PPO rollout collection is SERIAL
  single-client (~2.1 steps/s) — it did NOT inherit the F1b 30-worker
  parallelism. Must parallelize the closed-loop rollout to the 30 workers
  (the F1b lesson recurring inside the PPO loop).
- **M2 (blocker, avoidance success)**: the success acceptance set is
  `{"max_steps","obstacle_cleared"}` but the worker emits `"obstacle_pass"`
  (`"obstacle_cleared"` does not exist in the backend) — real avoidance
  success is systematically scored as failure; the smoke hid it because at
  horizon 6 the car passes via `"max_steps"`.
- **M3 (blocker, reveal gate)**: `_obstacle_visible` never fires (info has
  no `obstacle_visible` key; falls back to constant-zero padding), so the
  avoidance BC collects 0 frames — BC warm-start is empty and avoidance
  degrades to pure-PPO-from-scratch, violating the m1087 plan.
- **M4 (blocker, S7 no-op)**: the oracle-ceiling stop-rule passes 0/0
  thresholds and doesn't gate the recommendation — it never triggers,
  never blocks (quick had drift oracle 0.0 yet proceeded).
- **M5 (should-fix)**: the managed `--full` path + seed loop are
  resume-untested; add seed-level checkpointing + a micro-full kill/resume.
- **M6 (PI sign-off)**: the B6 reward-hacking hard gate was moved from
  Spearman>=0.9 to rank-biserial AUC (textbook-correct for binary-vs-
  continuous, but moving a pre-registered gate needs PI sign-off; the
  "Spearman unreachable" justification is contradicted by the measured
  0.981).
- **M7 (fix number)**: "100M steps" is decorative — the real PPO budget is
  ~2.3M steps; freeze with the real budget + F1b-rate wall-clock.

Route: a third build pass fixes M1-M5 + M7 with regression tests (avoidance
BC frames > 0, S7 triggers under nonzero floor+prize, throughput restored),
PI signs off M6, then re-smoke -> freeze -> managed launch. Pass-2 is real
RL with mechanical plumbing blockers, not a scope problem.
