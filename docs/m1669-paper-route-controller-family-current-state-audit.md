# M1669 Paper-Route Controller-Family Current-State Audit

## Summary

M1669 audits the current controller-family evidence after M1668 closed the
exact-residual checkpoint artifact route.

Decision:

```text
controller_family_current_state_audit_route_to_decisive_evidence_matrix_design
```

This milestone does not train, run replay, run PPO, promote a checkpoint, use
private holdout, change actor inputs, repair the M1663 artifact, or claim
paper-level or level3 self-identification evidence.

## Current Evidence Map

### Standard Profile Matrix

The corrected public profile infrastructure exists:

```text
L0_current_masked
L1_one_step
L2_window_13 / 25 / 50 / 100
L2_window_13 / 25 / 50 / 100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

M1497 completed the public three-seed 12-profile pilot:

```text
profile_count: 12
completed_seed_runs: 36
failed_seed_runs: 0
all_eval_metrics_finite: true
private_holdout_used: false
profile_specific_tuning: false
actor_input_contract_changed: false
```

Main aggregate results:

| Profile | Success | Collision | Mean Margin |
| --- | ---: | ---: | ---: |
| L0_current_masked | 0.177083 | 0.718750 | 0.260532 |
| L1_one_step | 0.296875 | 0.593750 | 0.412606 |
| L2_window_13 | 0.166667 | 0.739583 | 0.147432 |
| L2_window_25 | 0.182292 | 0.713542 | 0.235919 |
| L2_window_50 | 0.182292 | 0.713542 | 0.235935 |
| L2_window_100 | 0.182292 | 0.713542 | 0.235935 |
| L3_online_gru | 0.286458 | 0.640625 | 0.480487 |
| L3_reset_control_corrected | 0.317708 | 0.604167 | 0.502408 |

The L2 current-tiled controls remained close to L2 normal:

```text
L2_window_13 success delta over current-tiled: 0.015625
L2_window_25 success delta over current-tiled: 0.052083
L2_window_50 success delta over current-tiled: 0.052083
L2_window_100 success delta over current-tiled: 0.052083
```

M1498 therefore correctly stopped standard-profile scaling:

```text
finite_window_history_necessity_on_standard_profile: not_supported
online_gru_hidden_advantage_on_standard_profile: not_supported
level3_self_identification_on_standard_profile: not_supported
```

The standard matrix is useful engineering evidence, but it is not the decisive
self-identification task family.

### Decisive-History Task Infrastructure

M1499-M1509 built T4/T5 task definitions and scaffolding:

```text
T4: same-current, same-recent-window, different-older-history
T5: terminal-boundary near-constraint avoidance
metadata planner rows: 66 accepted, 33 T4, 33 T5
env-hook source families: 6
synthetic measured candidates: 2
```

This branch established task and artifact contracts but did not prove real
current-sim T4/T5 candidate existence or level3 self-identification.

### T5 Timing And Fresh Ambiguity Evidence

M1510-M1526 found that the first T5 high-speed subset was useful for response
removal/timing sensitivity, but not for wrong-history proof:

```text
M1521 max timing-amplified margin gap: 0.027952724375794435
M1524 donor response/action variants max gap: <= 0.000443
wrong-history success drops: 0
current T5 wrong-history route: closed as insufficient
```

M1538 then produced a stronger public fresh-ambiguity result:

```text
accepted pairs: 13
accepted source-family edges: 11
T5 / terminal-boundary accepted pairs: 5
wrong-history max margin gap: 0.1224
donor-response/action-plus-hidden max margin gap: 0.1260
max reset/zero-control gap: 0.0933
```

That result is important but still not paper-level:

```text
terminal target-side history positives: absent
success-drop evidence: absent
public development rows only
controls remain active
```

### Clean History-Vs-Control Surface

M1585 proved broad pairability and intervention plumbing, but it was
control-dominated:

```text
selected pairs: 72
selected source edges: 19
history-positive directed pairs: 23
control-substitution dominated share: 0.7184466019417476
success-drop count: 0
```

M1588 separated clean rows from dominated/control-only rows:

```text
clean directed pairs: 7
clean source edges: 4
clean endpoint source families: 6
```

M1592 expanded the clean surface:

```text
clean directed pairs: 34
clean source edges: 5
clean endpoint source families: 6
max clean source-edge share: 0.35294117647058826
```

M1609/M1615 then produced the current contour-aware public proof package:

```text
positive candidate rows: 39
diagnostic guardrail rows: 232
positive rows all clean: true
diagnostic rows used as positive: false
passes public smoke gates: true
passes evidence quality targets: true
```

This is the best current source of clean public history-control separation.
Its scope is still narrow and public, so it should be used for controlled
diagnostic benchmarking, not private claims or promotion.

### Exact-Residual Artifact Route

M1630-M1668 tested whether the clean contour package could become an
exact-objective repair route.

Positive infrastructure:

```text
full tensor materialization works;
exact evaluator works;
damped projection repairs controlled exact residuals;
fusion_actor repair reduces selected same-line proposal residuals;
M1663 materialized a checksum-clean alpha 0.2 checkpoint artifact.
```

Blocking negative result:

```text
M1666 checkpoint sanity: true
M1666 P0 actor contract: true
M183/M170 first-check pass: false
M267/M264 first-check pass: false
M183/M170 normal_success_delta: -1.0
M267/M264 normal_success_delta: -0.8823529411764706
primary blocker: behavior_regression
secondary blocker: proof_washout
```

M1668 correctly closed this route. Fixed-public exact residual repair is not
enough to make a replay-worthy driver artifact.

## Claim Status

### Supported

Supported now:

```text
P0 human-view/no-oracle controller profiles and configs exist;
standard public profile matrix is reproducible;
standard profile does not support L2 history necessity or L3 online-GRU advantage;
T4/T5 decisive-history harnesses and source-generation tools exist;
clean public history-vs-control rows exist in a 39-positive / 232-diagnostic package;
exact-objective artifact repair can be built and falsified by closed-loop replay gates.
```

### Unsupported

Unsupported now:

```text
finite-window history necessity on the standard profile distribution;
online GRU advantage over corrected reset-control on the standard profile distribution;
source-diverse terminal-boundary success-drop evidence;
controller-family ranking on decisive T4/T5 or clean contour tasks;
checkpoint promotion;
private-holdout generalization;
paper-level self-identification;
level3 anticipatory self-identification.
```

### Conditional

The strongest conditional claim is:

```text
There are public clean active-set rows where history variants and current-frame
controls can be separated under the existing online-GRU proof harness.
```

That does not answer whether a finite-window controller can match or beat the
online-GRU controller on the same decisive rows.

## Gaps

The current repo is missing one central paper-route experiment:

```text
a fair controller-family decisive evidence matrix that evaluates L0/L1/L2/L2
current-tiled/L3/L3-reset families on standard, decisive-history, and clean
active-set tasks under pre-registered budgets and no profile-specific tuning.
```

Without that matrix, the project can keep producing clean public proof rows or
repair objectives, but it cannot answer the paper question:

```text
When is current response enough, when is finite-window history enough, and when
does recurrent hidden state add value?
```

## Decision

Do not repair the M1663 artifact now. Do not resume standard-profile scaling.
Do not run PPO or private holdout.

Route to a design milestone:

```text
m1670-paper-route-controller-family-decisive-evidence-matrix-design
```

M1670 should design the controller-family decisive evidence matrix. It should
specify:

```text
controller profiles to compare;
task families and artifact sources;
public pilot budgets;
metrics and stop rules;
how to keep L2 current-tiled and L3 reset controls fair;
how to keep the M1615 clean package diagnostic rather than private evidence;
how to decide between negative, conditional, finite-window, and GRU-positive
paper routes.
```

## Guardrails

```text
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
artifact_repair_started: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next_branch: paper_route_controller_family_decisive_evidence_matrix
next: m1670-paper-route-controller-family-decisive-evidence-matrix-design
```
