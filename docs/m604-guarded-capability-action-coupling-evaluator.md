# M604 Guarded Capability-Action Coupling Evaluator

## Purpose

M604 implements and runs the exact no-update evaluator designed by M603.

Question:

```text
Where does decoded capability belief move while actor action remains nearly
unchanged?
```

This milestone is infrastructure-only:

```text
no model loading
no training
no PPO
no route evaluation
no checkpoint promotion
no action targets are generated
```

## Implementation

Added:

```text
src/autodrift/guarded_capability_action_coupling_evaluator.py
tests/test_guarded_capability_action_coupling_evaluator.py
```

The evaluator joins M601 capability rows with M591 action rows on matched-current
row identity:

```text
pair_id
checkpoint_label
surface
target
variant
left/right seed and step
```

It classifies each row using:

```text
capability_threshold = 0.25
action_threshold = 0.02
```

Classes:

| Class | Meaning |
| --- | --- |
| `belief_only_gap` | capability active, action inactive |
| `action_and_belief` | capability and action both active |
| `action_without_belief` | action active, capability inactive |
| `inactive` | both inactive |

Only real-history `belief_only_gap` rows are marked as candidates for later
grounding. They are not action targets.

## Command

```bash
PYTHONPATH=src python -m autodrift.guarded_capability_action_coupling_evaluator \
  --capability-rows runs/m601_bc_capability_belief_intervention_fresh/capability_intervention_rows.csv \
  --capability-rows runs/m601_bc_capability_belief_intervention_ood/capability_intervention_rows.csv \
  --action-rows runs/m591_bc_hidden_action_sensitivity_probe_fresh/action_sensitivity_rows.csv \
  --action-rows runs/m591_bc_hidden_action_sensitivity_probe_ood/action_sensitivity_rows.csv \
  --capability-threshold 0.25 \
  --action-threshold 0.02 \
  --run-dir runs/m604_guarded_capability_action_coupling_evaluator
```

## Artifacts

```text
runs/m604_guarded_capability_action_coupling_evaluator/summary.json
runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv
runs/m604_guarded_capability_action_coupling_evaluator/variant_summary.csv
runs/m604_guarded_capability_action_coupling_evaluator/variant_aggregate_summary.csv
```

Summary:

| Metric | Value |
| --- | ---: |
| capability input rows | `7392` |
| action input rows | `6776` |
| joined coupling rows | `6776` |
| all `belief_only_gap` rows | `3033` |
| real-history `belief_only_gap` rows | `262` |
| real-history grounding candidates | `262` |
| actor parameters changed | `false` |
| PPO used | `false` |
| promoted | `false` |

## Real-History Candidate Distribution

Aggregate by surface and variant:

| Surface | Variant | Rows | Belief-only candidates | Action-and-belief | Inactive | Mean capability z | Mean action distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh | `shuffled_history` | `329` | `84` | `15` | `230` | `0.226604` | `0.003319` |
| fresh | `delayed_history` | `329` | `24` | `0` | `305` | `0.077070` | `0.001602` |
| fresh | `wrong_matched_history` | `329` | `8` | `0` | `321` | `0.099081` | `0.000540` |
| OOD | `shuffled_history` | `287` | `77` | `1` | `209` | `0.213130` | `0.003184` |
| OOD | `wrong_matched_history` | `287` | `49` | `0` | `238` | `0.140707` | `0.000736` |
| OOD | `delayed_history` | `287` | `20` | `0` | `267` | `0.075159` | `0.001407` |

By target:

| Surface | Target | Variant | Candidates |
| --- | --- | --- | ---: |
| fresh | `future_braking_deceleration` | `shuffled_history` | `18` |
| fresh | `future_lateral_accel_response` | `shuffled_history` | `28` |
| fresh | `future_yaw_response` | `shuffled_history` | `38` |
| fresh | `future_yaw_response` | `delayed_history` | `12` |
| fresh | `future_braking_deceleration` | `wrong_matched_history` | `4` |
| fresh | `future_lateral_accel_response` | `wrong_matched_history` | `2` |
| fresh | `future_yaw_response` | `wrong_matched_history` | `2` |
| OOD | `future_yaw_response` | `shuffled_history` | `51` |
| OOD | `future_lateral_accel_response` | `wrong_matched_history` | `28` |
| OOD | `future_yaw_response` | `wrong_matched_history` | `17` |
| OOD | `future_yaw_response` | `delayed_history` | `16` |

The highest-quality matched-wrong candidate concentration is OOD
`future_lateral_accel_response`: `28 / 47` rows are belief-only gaps.

## Interpretation

M604 supports the M603 diagnosis:

```text
There are source-diverse rows where real history moves decoded capability
belief but the current actor action barely moves.
```

This is exactly the gap a future action-coupling branch must address.

However, M604 still does not admit training. A `belief_only_gap` means:

```text
capability signal exists but action is insensitive
```

It does not say:

```text
which action should be taken
whether moving action improves margin
whether wrong-history should fail
whether normal branch needs steering, braking, throttle, or timing changes
```

So the rows are candidates for grounding, not supervised targets.

## Decision

```text
guarded_capability_action_coupling_evaluator_pass_admit_grounded_target_design
```

M604 passes because it implements the no-update evaluator, writes the required
artifacts, reports real-history belief-only gap counts, and preserves the no
training / no PPO / no promotion contract.

## Next

```text
M605: design grounded capability-action target mining for the M604 candidates.
```
