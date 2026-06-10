# Self-ID Completion Experiment Design (2026-06 Pre-Registration)

## Status And Scope

This document pre-registers the two experiments of the feasibility-route step 5
(self-identification completion). It is written BEFORE any full-budget run.
The accompanying milestone delivers infrastructure only:

```text
src/autodrift/observation_degradation_wrapper.py        degraded-response task family
configs/selfid_positive_control_privileged_smoke.json   privileged twin (obs76)
configs/selfid_positive_control_p0_smoke.json           P0 twin (obs72)
scripts/feasibility_audit/selfid_positive_control_pilot.py  train -> hidden-swap-gate chain smoke
tests/test_observation_degradation_wrapper.py           correctness + executability smoke
```

No number produced by the smoke chain may be interpreted scientifically.
This rule exists because M1199 (8192 steps per seed, 3 seeds) and the M1497
standard fixed-budget pilot were both judged inconclusive: short budgets
produce profile rankings dominated by optimization noise, and the project must
not repeat that mistake at the decisive step.

`self_id_evidence_discipline.claim_level` for this milestone:

```text
not_applicable
```

## Why These Two Experiments

The evidence-discipline rule (docs/self-identification-evidence-discipline.md)
routes null history-intervention results to better task design, specifically:

```text
level 3 design: preparation phase before the critical maneuver, and
current-frame evidence made intentionally insufficient (delayed/noisy
current response).
```

The paper-route plan (docs/paper-route-finite-window-vs-gru-plan.md) provides
the matching task families: Family 3 (active diagnostic warmup) and Family 4
(variable diagnostic delay). The M1388/M1389 result showed the clean task has
high current-frame substitution risk; degradation of the current ego response
is the controlled way to remove that substitute.

The two prescriptions ("两味药"):

1. Observation degradation as a TASK FAMILY: the current ego response channels
   are delayed and/or noisy during BOTH training and evaluation, so the
   current frame is no longer a sufficient statistic of hidden dynamics.
2. A privileged POSITIVE CONTROL: a policy with explicit hidden-parameter
   input establishes (a) the information ceiling of the task and (b) whether
   the gate's outcome-difference detection machinery can detect a belief
   intervention at all.

Interpretation contract (required by the discipline doc): the degradation is
part of the actor's task, not an evaluation intervention and not an actor
input contract change. Claims must not mix this interpretation with eval-only
ablations such as `zero_current_response`.

## Experiment 1: Degraded-Response Profile Matrix

### Hypothesis

```text
H1: Under delayed or noisy current ego response, history-bearing controllers
    (L2 finite-window, L3 online GRU) outperform current-feedback controllers,
    and the L3 online-vs-reset gap grows with delay k.
H0: Profile ranking under degradation matches the clean task; history models
    add no outcome-relevant value (M1389-style negative).
```

### Profile Axis

All profiles keep the deployable `[steer, throttle, brake]` action contract
and the P0 human-view/no-wheel/no-oracle actor input contract.

```text
P1  L0_current_masked       current 72-dim frame, previous-command fields masked
P2  L2_window_25            explicit 0.5s finite window (temporal_gru encoder)
P3  L3_online_gru           episode-persistent online GRU hidden state
P4  L3_reset_control        same architecture as P3, every-step hidden reset
```

`L2_window_25_current_tiled` is admitted as an optional diagnostic column if
budget allows; it is not required for the primary verdict because P4 already
provides the memory-vs-architecture control for the L3 claim and the L2 claim
is read against P1.

### Task Condition Axis (Observation Degradation Wrapper)

Applied identically at training and evaluation via
`ObservationDegradationWrapper` (degraded per-frame indices 0-8; previous
commands 9-11 and scene geometry 12-71 untouched):

```text
T1  clean        delay_steps=0,  noise_std=0.0
T2  delay_5      delay_steps=5   (0.10s at dt=0.02)
T3  delay_12     delay_steps=12  (0.24s)
T4  delay_25     delay_steps=25  (0.50s)
T5  noise        delay_steps=0,  noise_std=0.05 per ego-response channel
```

Base task: the M1207-lineage emergency-avoidance env (friction step at steps
8-40, hidden-parameter randomization, AEB-infeasible obstacle, obs72 P0
frame), i.e., the same env block as the two positive-control configs.

### Budget (Pre-Registered, Non-Negotiable Floor)

```text
cells:                      4 profiles x 5 conditions = 20
training seeds per cell:    >= 10 (seed list fixed before launch)
training steps per seed:    >= 500_000
evaluation per checkpoint:  >= 300 fresh public episodes, fixed seed list,
                            disjoint from training seeds
no profile-specific tuning; same optimizer, rollout, env count, device class.
```

Budget contrast that motivates this floor:

```text
M1199 pilot:  8192 steps/seed, 3 seeds, 64 eval episodes  -> inconclusive
this design:  >= 500k steps/seed (61x), >= 10 seeds (3.3x),
              >= 300 eval episodes (4.7x)
```

If compute cannot fund the full 20-cell floor, the pre-registered reduction
order is: drop T5 (noise), then drop T2 (delay_5). Profiles and per-cell
budget must not be reduced; fewer, fully-funded cells beat more starved cells.

### Pre-Registered Verdict Criteria (M1492 Thresholds)

Primary metrics: `success_rate`, `clearance_margin_p10`. Secondary:
collision rate, off-track rate, mean margin, return, smoothness.

```text
history-positive (per condition):
  P3 (L3 online) beats P4 (L3 reset) by >= +0.02 success
  or >= +0.05 p10 clearance margin, with seed-level sign consistency
  (>= 7/10 seeds in the same direction);
  and P3 is competitive with or better than P2 and P1 on safety metrics.

finite-window-positive (per condition):
  P2 beats P1 by the same thresholds.

dose-response support:
  the P3-minus-P4 gap is non-decreasing across T2 -> T3 -> T4.
```

### Stop Rule

```text
1. Seeds, eval seeds, budgets, and thresholds are frozen at launch.
2. No outcome-based early stopping and no peeking-based extension. The only
   permitted interim look is an infrastructure check after seed index 4 of
   each cell (finite metrics, runtime, crash rate); it must not alter design.
3. A cell aborts only on non-finite metrics or runtime failure; aborted cells
   are reported as aborted, never silently re-run with new settings.
4. Analysis starts only after all funded cells complete.
5. Experiment 1 results are read only if Experiment 2's gate-validity
   criterion (below) has passed.
```

## Experiment 2: Privileged Positive Control And Gate Validation

### Hypothesis

```text
H2a (information ceiling): the privileged twin (obs76, explicit
     [mu, mass/mass0, lf/lf0, cr/cr0]) beats the P0 twin (obs72) on the same
     task at the same budget by >= +0.02 success or >= +0.05 p10 margin.
H2b (gate validity): the converged privileged policy shows a detectable
     outcome change under the privileged-value-swap intervention
     (>= 0.02 success delta or >= 0.05 p10 margin delta across matched pairs,
     source-diverse, not seed-singleton).
H2c (predicted null): the privileged policy is approximately insensitive to
     GRU hidden-swap and reset, because its belief channel is the current
     frame, not the hidden state. This null is a PREDICTION, not a failure.
```

### Design

```text
configs:     full-budget descendants of the two smoke configs
             (same env block, same online_gru encoder, only
             include_privileged_params differs)
budget:      same per-cell floor as Experiment 1 (>= 10 seeds x >= 500k steps,
             >= 300 eval episodes)
gate chain:  autodrift.hidden_swap_gate.run_hidden_swap_gate on both twins
             (nominal mu 0.85-1.15 vs perturbed mu 0.25-0.35), plus the
             privileged-value-swap probe from
             scripts/feasibility_audit/selfid_positive_control_pilot.py
matching:    max_observation_distance for the privileged twin must be raised
             above the P0 default 0.75 because the privileged channels carry
             an irreducible cross-condition distance floor (~|mu_n - mu_p|);
             context-only matching distance is reported alongside.
```

Semantics of hidden-swap under privileged inputs are documented in the pilot
script docstring and are part of this pre-registration: hidden-swap tests the
recurrent belief channel; privileged-value-swap tests the explicit belief
channel; the gate's `zero_response` correctly leaves privileged channels
intact as context.

### Gate-Validity Criterion (Pre-Registered)

```text
The hidden-swap gate methodology is declared VALID for this task family only
if H2a and H2b both hold. If H2a holds but H2b fails, the outcome-difference
detection machinery cannot detect a belief intervention even when the belief
channel is explicit and provably useful. In that case every historical and
future null hidden-swap result on P0 policies is uninformative, and the gate
methodology itself is invalid. That is a paper-level methodological finding
and must be published as such, not patched silently.
```

## The Four Pre-Registered Outcomes

```text
Outcome A: positive.
  H2a+H2b pass and Experiment 1 shows history-positive cells meeting the
  M1492 thresholds with dose-response support.
  Meaning: degraded current response creates a real self-ID niche.
  Next step: Stage 4 mechanism interventions (wrong/delayed/reset history)
  on the winning cells; paper claim ladder up to Claim C/D as supported.

Outcome B: negative.
  H2a+H2b pass but Experiment 1 shows no history-positive cell (or only
  threshold-failing trends).
  Meaning: even without current-frame sufficiency, finite windows or current
  feedback absorb the task; recurrent self-ID is not needed here.
  Next step: report as a valid negative/conditional paper result per the
  paper-route decision rules; stop self-ID proof machinery on this task.

Outcome C: gate failure.
  H2a passes, H2b fails.
  Meaning: detection machinery insensitive; all hidden-swap nulls
  uninformative; methodology finding (paper-level).
  Next step: redesign outcome metrics/matching before ANY self-ID verdict;
  Experiment 1 results are quarantined, not interpreted.

Outcome D: uninterpretable.
  H2a fails (privileged twin does not beat P0 twin), or training is unstable
  (non-finite metrics, seed variance exceeding effect thresholds), in any arm.
  Meaning: optimization or task difficulty is the binding constraint, not
  information; the experiment cannot speak about self-ID either way.
  Next step: infrastructure/budget repair (longer training, reward shaping
  audit, env difficulty audit) and a fresh pre-registration; no verdict.
```

## Required Manifest Field (For The Future Run Milestones)

```json
"self_id_evidence_discipline": {
  "claim_level": "not_applicable",
  "current_frame_substitution_risk": "Clean cells keep full current-frame sufficiency; degraded cells remove it by k-step delay or per-channel noise on ego response indices 0-8 as a task family.",
  "history_necessity_tests": [
    "normal vs reset-hidden (P3 vs P4 across conditions)",
    "normal vs delayed-history",
    "normal vs zero-current-response",
    "normal vs wrong-matched-history",
    "privileged-value-swap positive control"
  ],
  "temporal_evidence_window": "Friction step at steps 8-40 provides a pre-obstacle command-response evidence window; degradation makes the current frame insufficient.",
  "negative_result_policy": "All four outcomes above are publishable; nulls route to Outcome B/C/D as pre-registered, never to threshold weakening.",
  "allowed_claims": [
    "infrastructure and pre-registration only at this milestone"
  ]
}
```

## Claim Boundary

Allowed claim for this milestone:

```text
The observation-degradation task wrapper, the privileged/P0 positive-control
config twins, and the train->hidden-swap-gate->privileged-value-swap chain
are implemented, deterministic where specified, and executable end to end at
smoke budget with finite metrics.
```

Rejected claims:

```text
self-identification evidence at any level above not_applicable
profile ranking or architecture preference from the smoke runs
gate validity or gate failure (requires full-budget Experiment 2)
information ceiling of the privileged channels
task-family difficulty or dose-response shape
deployable-controller capability change
```

Promotion, private holdout, corpus export, and actor input contract changes
are out of scope for both this milestone and the pre-registered runs above.
The privileged twin must never be promoted or compared as an engineering
candidate; it exists only as a methodology control.
