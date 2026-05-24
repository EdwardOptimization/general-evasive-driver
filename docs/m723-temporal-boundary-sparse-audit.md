# M723 Temporal Boundary Sparse Audit

## Purpose

M723 audits the M722 `temporal_action_only_boundary_sparse` result before any
additional boundary mining, source export, actor objective design, PPO, or
checkpoint promotion.

This milestone is process-only:

```text
no rerun
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M722 implemented the no-training temporal action-boundary outcome miner and ran
the registered data wave:

```text
source_candidate_rows:         128
candidate_variant_count:      6984
accepted_rows:                   0
result_class: temporal_action_only_boundary_sparse
```

It preserved the intervention cleanliness requirements:

```text
actor_parameters_changed: false
training_started:         false
optimizer_started:        false
ppo_used:                 false
promoted:                 false
```

The main action/outcome split is:

```text
temporal_action_critical_rows:  921
temporal_outcome_critical_rows:   0
```

Variant-level evidence:

```text
mismatch_zero_command_history:
  rows:                         1536
  temporal action-critical:      864
  temporal outcome-critical:       0
  first action distance mean: 0.020037
  first action distance max:  0.030529
  margin gap max:            0.002842

reset_hidden:
  rows:                         1536
  action-critical:               848
  outcome-critical:                0
  margin gap max:            0.001957

delayed_hidden_20:
  rows:                         1536
  temporal action-critical:       32
  temporal outcome-critical:       0
  margin gap max:            0.000473

pre_fault_stale_hidden:
  rows:                          840
  temporal action-critical:       25
  temporal outcome-critical:       0
  margin gap max:            0.000188
```

The sentinel gate was clean:

```text
sentinel_rows:                732
sentinel_false_positive_rows:   0
sentinel_false_positive_rate: 0.0
```

The source-pool issue is visible:

```text
source_candidate_rows: 128
source_role_counts:
  primary:  115
  sentinel:  13

unique source seeds: 4
source seed counts:
  72000: 50
  72001: 35
  72002: 30
  72003: 13
```

Fault-family spread is broader than the seed spread:

```text
combined_fault:                37
brake_authority_drop:          23
global_mu_drop:                17
steering_fault:                12
drive_authority_drop:          11
mass_cg_shift:                  9
rear_lateral_authority_drop:    7
delay_noise_fault:              6
front_lateral_authority_drop:   6
```

Rejections:

```text
normal_failed_rejected:        660
history_insensitive_rejected: 6063
```

All rejected rows are `normal_history_failed` when a rejection reason is
recorded, but most rollout rows are simply history-insensitive under the local
boundary grid.

## What This Means

M722 is a useful negative, not a dead end.

It supports:

```text
temporal command-history changes actor action under boundary relocation.
```

It does not support:

```text
those temporal action differences currently cause collision, recovery failure,
or clearance-margin loss.
```

The local obstacle relocation grid was strong enough to create some
normal-history failures, but not the desired class:

```text
normal history viable,
temporal mismatch action differs,
temporal mismatch margin drops by >= 0.02 m or fails.
```

This means simply increasing the same M722 boundary grid is not the cleanest
next step. The more direct issue is that M722 inherited a source-concentrated
M719 pool: only four seeds survived into the selected source rows because the
original M719 matching filled `max_pairs` early.

## Supported Claims

M723 supports:

```text
1. The actor still has strong action-level temporal command-history dependence.

2. M722's negative result is not explained by sentinel false positives.

3. Local obstacle relocation around M719 source rows is insufficient for
   closed-loop outcome proof.

4. M719/M722 source concentration is now a first-order blocker.

5. Source export, actor objective design, PPO, and promotion remain blocked.
```

## Falsified Claims

M723 falsifies:

```text
1. M719/M720 were negative only because obstacle placement was slightly too
   easy.

2. M722's local boundary grid is enough to convert temporal action rows into
   source-positive outcome rows.

3. The current M719 source pool is sufficiently diverse for paper-quality
   closed-loop self-ID evidence.

4. The project should proceed directly to PPO from temporal action-only rows.
```

M723 does not falsify:

```text
1. A fresh source-balanced temporal data wave may produce better rows.

2. A stronger normal-retention-controlled boundary search may be needed after a
   better source pool exists.

3. Sequence-level interventions may be required if single-step action deltas
   remain outcome-neutral.

4. True wheel-asymmetric faults may require four-wheel or explicit
   yaw-disturbance dynamics.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The registered boundary miner found 921 temporal action-critical rows but 0
temporal outcome-critical rows, and the source pool remained concentrated in
only four seeds.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
Temporal action-critical rows remain action metrics. Reporting them as
closed-loop self-identification proof would overclaim.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.

private_holdout_contamination:
  no private holdout was used.
```

## Public Gate Overfit Risk

The active risk is:

```text
source-pool overfitting to M719 early seeds.
```

M719 and M722 both derive from the same broad v2 scenario generator, but the
actual temporal action rows used by M722 are not source-balanced across the
registered `512` seeds. Reusing this pool for another local miner would produce
more rows, but the claim would still be limited by the same source bottleneck.

The second risk is:

```text
action-only metric overclaiming.
```

`mismatch_zero_command_history` is consistently action-sensitive, but its margin
gap remains far below the registered `0.02` threshold under M722:

```text
margin gap max: 0.002842
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close branch:

```text
temporal_action_boundary_outcome_mining
```

Open branch:

```text
fresh_source_balanced_temporal_wave
```

Next task:

```text
m724-fresh-source-balanced-temporal-wave-design
```

Rationale:

```text
The immediate blocker is not PPO and not actor architecture. It is evidence
generation: the project needs a fresh temporal command-response data wave whose
pair selection is source-balanced by construction, rather than taking the first
max_pairs that happen to fill from early seeds.
```

M724 should design a no-training temporal wave with:

```text
per-seed quotas
per-fault-family quotas
per-source-role quotas
fresh seed ordering or stratified sampling
explicit sentinel allocation
normal-history retention before local boundary mining
heldout split retained
no actor input change
no actor update
no PPO
no promotion
```

Only after that fresh wave should the project decide whether to rerun boundary
mining, design sequence-level interventions, or move to higher-fidelity
asymmetric dynamics.
