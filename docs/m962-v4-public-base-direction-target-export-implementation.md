# M962 V4 Public Base Direction Target Export Implementation

## Purpose

M962 implements the no-training direction-target export designed in M961.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_direction_target_export
```

## Artifacts

```text
runs/m962_v4_public_base_direction_target_export/summary.json
runs/m962_v4_public_base_direction_target_export/accepted_direction_targets.csv
runs/m962_v4_public_base_direction_target_export/direction_target_family_catalog.csv
runs/m962_v4_public_base_direction_target_export/branch_separated_proof_targets.csv
runs/m962_v4_public_base_direction_target_export/retention_anchor_targets.csv
runs/m962_v4_public_base_direction_target_export/rejected_export_candidates.csv
runs/m962_v4_public_base_direction_target_export/route_decision.csv
```

## Implementation

M962 adds:

```text
src/autodrift/public_base_direction_target_export.py
tests/test_public_base_direction_target_export.py
```

The exporter reads the accepted M960 family summary and reconstructs M755/M960
rows. It exports only primary joint candidates:

```text
family_type == primary
normal_retention_pass == true
behavior_grounded == true
m267_target_preflight_pass == true
joint_direction_target_candidate == true
```

It rejects diagnostic-only anti-aligned families and keeps secondary families
out of training-target export.

## Result

```text
result_class: direction_target_export_pass
accepted_family_count: 20
accepted_direction_target_count: 1280
branch_separated_proof_target_count: 160
retention_anchor_count: 1149
diagnostic_target_count: 0
max_direction_family_fraction: 0.25
```

The family catalog is source-balanced across the four primary directions:

```text
throttle_minus
toward_intervention
brake_plus
steer_minus_brake_plus
```

The top-ranked family remains:

```text
throttle_minus_amp_0_0080:
  terminal_margin_mean_delta: +0.00009178
  terminal_margin_p10_delta: +0.00004844
  recommended_weight: 1.0
```

## Interpretation

M962 materializes the target-space result from M960 into a training-ready, but
not-yet-trained, corpus:

- `accepted_direction_targets.csv` contains the normal low-tail target rows.
- `branch_separated_proof_targets.csv` keeps normal-history success anchors and
  wrong-history failure anchors separate.
- `retention_anchor_targets.csv` anchors non-target positive rows to base
  actions.
- `rejected_export_candidates.csv` records why diagnostic and secondary
  families are not exported as training targets.

Supported:

- accepted M960 targets can be reconstructed and exported;
- diagnostic-only anti-aligned families are excluded from target export;
- the export is not dominated by one direction family;
- proof and retention anchors are available before actor fitting.

Falsified:

- M960's joint candidates are only an in-memory diagnostic result;
- actor fitting has to start before target corpus materialization;
- accepted target export requires changing the actor input/output contract.

## Next Blocker

The natural technical route is:

```text
direction-target actor-fit objective implementation
```

However, the current branch started at M953 and M962 is the tenth non-synthesis
milestone in the branch. The workflow cadence therefore requires a synthesis
milestone before actor-fit implementation.

M962 routes to:

```text
m963-v4-public-base-target-feasibility-export-branch-synthesis
```

M963 should synthesize M953-M962 and decide whether to continue into the
direction-target actor-fit branch, refresh target sources, or pivot.
