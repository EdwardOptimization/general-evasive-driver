# M956 V4 Public Base Low-Tail Sequence Target Audit Implementation

## Purpose

M956 implements the no-training short-horizon sequence target audit designed in
M955.

It does not train, update model weights, run PPO, change actor inputs, change
the actor output contract, use private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_low_tail_sequence_target_audit
```

## Artifacts

```text
runs/m956_v4_public_base_low_tail_sequence_target_audit/summary.json
runs/m956_v4_public_base_low_tail_sequence_target_audit/sequence_family_summary.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/low_tail_sequence_metrics.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/m267_sequence_preflight.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/m267_sequence_preflight_rows.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/sequence_row_conflicts.csv
```

## Implementation

M956 adds:

```text
src/autodrift/public_base_low_tail_sequence_target_audit.py
tests/test_public_base_low_tail_sequence_target_audit.py
```

The audit keeps `u_0` unchanged and applies small delayed projection deltas to
the following prefix actions:

```text
horizons: 2, 4, 6
amplitudes: 0.004, 0.006, 0.008
evaluated low-tail rows: 64 / 498
```

M267/M264 active-row proof retention is evaluated separately with
branch-separated target preflight.

## Result

```text
result_class: low_tail_sequence_target_audit_no_sequence_low_tail_candidate
sequence_family_count: 9
first_action_retained_family_count: 9
sequence_low_tail_candidate_count: 0
terminal_margin_positive_family_count: 0
m267_sequence_preflight_pass_count: 9
joint_sequence_candidate_count: 0
sequence_row_conflict_count: 9
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
actor_output_contract_changed: false
```

All sequence families preserve first-action retention and M267 proof retention,
but none improves terminal margin on the sampled low-tail rows.

Best family by terminal margin delta:

```text
family: delayed_projection_h2_amp_0_0040
terminal_margin_mean_delta: -0.000018
positive_margin_fraction: 0.0
prefix_l2_mean: 0.001000
success_delta: 0.0
collision_delta: 0.0
```

Larger horizons/amplitudes worsen the terminal margin monotonically in this
sample.

## Interpretation

The result is not an M267 proof-retention failure:

```text
m267_sequence_preflight_pass_count: 9 / 9
```

It is also not a first-action retention failure:

```text
first_action_retained_family_count: 9 / 9
```

The active issue is that the current low-tail projection direction is not
behaviorally grounded: delayed action-gap movement makes terminal margin
slightly worse on the evaluated low-tail rows.

Therefore the next step should not be actor training or threshold relaxation.
It should audit whether the low-tail action-gap metric is acting as a target
metric artifact for this branch.

## Next Blocker

M956 routes to:

```text
m957-v4-public-base-low-tail-target-metric-artifact-audit-design
```

M957 should design a no-training audit comparing action-gap low-tail metrics
against closed-loop terminal margin and success effects, then decide whether
the branch needs target redefinition, threshold sensitivity, or a different
source of low-tail targets.
