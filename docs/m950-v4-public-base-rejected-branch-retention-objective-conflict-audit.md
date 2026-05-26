# M950 V4 Public Base Rejected-Branch Retention Objective Conflict Audit

## Purpose

M950 audits the M949 result before any further local objective tuning. M949
implemented rejected-branch retention, but produced no exact candidate.

M950 does not train, run full replay, run PPO, change actor inputs, or promote.

## M949 Summary

M949 was valid:

```text
reconstructed_rows: 1213 / 1213
active_rejected_rows: 4 / 4
joined_target_rows: 122
missing_target_keys: 0
actor_mean_changed: true
fusion_changed: true
forbidden_parameter_changed: false
ppo_used: false
promoted: false
```

But it was not a candidate:

```text
result_class: controlled_fusion_rejected_branch_retention_objective_conflict
exact_candidate_alpha_count: 0
m267_preflight_pass_alpha_count: 3
candidate_alpha_count: 0
```

## Alpha Conflict

The alpha table shows two incompatible bands:

| alpha band | exact objective | M267/M264 preflight | interpretation |
| --- | --- | --- | --- |
| 0.005-0.010 | normal retained, no tail lift | pass | too small to improve low-tail surface |
| 0.020-0.075 | normal retained, no tail lift | fail | moving toward lift but eroding rejected branch |
| 0.100-0.150 | tail lift, normal not retained | fail | low-tail objective works but trust region/proof fail |
| 0.200 | tail lift, normal not retained | pass | rejected branch can be restored, but too far from base |
| 0.250 | tail lift, normal not retained | full gate normal success regresses | too aggressive |

The most important boundary is:

```text
alpha 0.075:
  normal_retention_pass: true
  tail_lift_pass: false
  M267 preflight: fail
  normal_intervention_gap_p10: 0.010755
  gap_deficit_mean: 0.013556
  low_tail_fraction: 0.343776

alpha 0.100:
  normal_retention_pass: false
  tail_lift_pass: true
  M267 preflight: fail
  normal_intervention_gap_p10: 0.012271
  gap_deficit_mean: 0.012419
  low_tail_fraction: 0.302556
```

This is not a no-signal result. It is a multi-objective conflict:

```text
low-tail lift wants larger alpha;
normal retention wants smaller alpha;
M267 rejected-branch retention is non-monotonic and only passes at tiny alphas
or at alpha 0.200 where normal retention is already lost.
```

## Training-Signal Audit

The rejected-branch proxy terms are active and go nearly to zero:

```text
epoch 80 rejected_wrong_action_anchor: 2.432e-07
epoch 80 rejected_wrong_separation_floor: 0.0
epoch 80 rejected_wrong_direction_anchor: 0.0
epoch 80 rejected_gap_mean: 0.080004
```

So the rejected proxy is not missing from the loss. The issue is that training
at M948's inherited boundary alphas `0.125, 0.150, 0.175` pushes the raw
direction into a high-alpha solution. When interpolated down to the
normal-retained region, the low-tail lift is insufficient; when interpolated up
to the tail-lift region, normal retention fails.

## Route Decision

Do not run full replay from M949.
Do not run PPO.
Do not promote.
Do not open actor inputs, encoders, or GRU.

A bounded retune is justified before branch synthesis because:

- rejected-branch retention is live;
- exact low-tail metrics are close near alpha `0.075-0.100`;
- the train alphas were inherited from M940 and not aligned with the new
  M267 preflight constraint;
- no private holdout was used.

The retune should be exactly one bounded implementation. It should:

```text
train at lower boundary alphas: 0.0675, 0.0750, 0.0900, 0.1000
increase normal-retention pressure near the boundary
reduce wrong-action anchor pressure enough to avoid killing low-tail lift
keep wrong-vs-normal separation and direction anchors active
keep M267/M264 row 6/13/15/16 preflight mandatory
keep full replay, PPO, and promotion blocked
```

If the retune still yields no alpha with both exact objective compatibility and
M267 preflight, the branch should not continue with another local coefficient
tweak. The next route should then be either rejected-branch trajectory target
export or controlled-fusion branch synthesis.

## Decision

Route to one bounded retune implementation:

```text
m951-v4-public-base-rejected-branch-boundary-retune-probe
```

M951 may extend M949's CLI to expose the rejected-branch coefficients and run
one objective-only probe. It must not run PPO or promote.
