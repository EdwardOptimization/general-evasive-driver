# M1557 Paper-Route Temporal Active-Set Anchor-Sensitivity Miner Result Audit

## Summary

M1557 audits the corrected M1556 temporal active-set miner result.

Decision:

```text
temporal_active_set_miner_audit_sparse_active_set_route_to_branch_synthesis
```

M1556 is a clean implementation milestone, but it does not provide a usable
active set for history-intervention replay. The failure is classified as:

```text
scenario_sampling_failure
```

The next step is branch synthesis, not another direct miner or history
intervention.

## M1556 Evidence

Corrected final smoke:

```text
anchor_candidate_count: 96
local_perturbation_row_count: 576
action_sensitive_anchor_count: 2
predecision_sensitive_anchor_count: 2
source_family_count: 5
max_single_family_share: 0.20833333333333334
active_source_family_count: 1
max_single_active_family_share: 1.0
active_anchor_window_count: 1
success_flip_count: 4
collision_flip_count: 0
max_abs_terminal_margin_gap: 0.010894415363880583
anchor_replay_failure_count: 20
local_perturbation_failure_count: 120
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
```

Active rows:

```text
source_family: curved_boundary_obstacle
anchor_window: reveal
active_anchor_count: 2
normal_terminal_margin: 5.299181885232641
best_override: steer_right_brake_more
```

The active rows are not near the terminal boundary. They are large-positive
clearance cases where some overrides prevent obstacle completion within the
continuation horizon. That is useful for checking the runner, but it is not a
good terminal-boundary active set.

## Failure Analysis

The implementation plumbing is valid:

```text
focused tests: 4 passed
summary artifact exists
guardrail_violation_count: 0
history_interventions_executed: false
actor_input_contract_changed: false
training_started: false
ppo_used: false
```

The evidence failure is real:

```text
action_sensitive_anchor_count < 12
predecision_sensitive_anchor_count < 6
active_source_family_count < 4
active_anchor_window_count < 3
max_single_active_family_share > 0.35
max_abs_terminal_margin_gap < 0.02
collision_flip_count == 0
```

The corrected active rows are source- and window-concentrated. They do not
support a materialized corpus, a history-intervention replay, or any self-ID
claim.

## Near-Boundary Audit

M1556 did find near-boundary normal terminal margins, but these rows are already
terminal collision rows:

```text
ok anchors: 76
near abs(margin) <= 0.1: 21
near-boundary terminal reason: collision for all 21
```

On those near-boundary collision anchors, one-step local action overrides
remain weak:

```text
max near-boundary local gap: 0.005470471755265827
near-boundary success flips: 0
near-boundary collision flips: 0
```

So the blocker is not simply "there are no near-boundary rows." The current
calibrated sources contain two unhelpful regimes:

```text
1. already-colliding near-boundary rows that one-step local action cannot fix;
2. safe high-margin rows where local overrides affect completion timing but not terminal boundary outcome.
```

Neither regime is a good source for wrong-history intervention evidence.

## Interpretation

M1556 falsifies the narrow plan:

```text
take M1550/M1555 calibrated pair-expansion anchors;
try earlier temporal windows;
then run history interventions if local action sensitivity appears.
```

Earlier windows alone are not enough. The source generator needs to target a
recoverable active set, not merely terminal near-boundary margins or pairable
current states.

This does not falsify the overall driver-like RL project. It only says the
current public calibrated pair-expansion branch has exhausted the useful
evidence in this source construction.

## Route Decision

Do not run history interventions on the M1556 anchors.

Do not immediately implement another narrow miner over the same branch.

Next route:

```text
m1558-paper-route-calibrated-pair-expansion-branch-synthesis-after-active-set-miner
```

The synthesis should decide whether to promote to a new branch focused on
recoverable active-set task generation. That prospective branch should consider:

```text
source generation that explicitly searches for recoverable terminal-boundary rows;
multi-step local action holds as controllability diagnostics;
separate gates for already-colliding, high-margin-safe, and recoverable-boundary anchors;
source diversity before any history intervention replay;
no training, PPO, materialization, private holdout, actor-input change, or level3 self-ID claim.
```

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1558-paper-route-calibrated-pair-expansion-branch-synthesis-after-active-set-miner
```
