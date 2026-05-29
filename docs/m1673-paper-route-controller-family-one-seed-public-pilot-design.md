# M1673 Paper-Route Controller-Family One-Seed Public Pilot Design

## Summary

M1673 designs the first one-seed public plumbing pilot after the M1672 protocol
preflight audit.

Decision:

```text
one_seed_public_pilot_design_admit_standard_layer_implementation
```

This milestone is design-only. It does not execute training, replay, PPO,
promotion, private holdout, actor-input changes, artifact repair, paper-level
claims, or level3 self-identification claims.

## Purpose

The first one-seed pilot should test the runner and profile matrix, not make an
architecture claim.

Primary question:

```text
Can the current code train/evaluate all 12 controller-family profiles under one
public seed block with finite metrics and no profile-specific tuning?
```

This is a plumbing question. It is not the decisive-history result.

## Task-Layer Decision

M1615 remains diagnostic-only for this pilot.

Reason:

```text
M1615 was generated through online-GRU proof tooling;
directly treating its clean rows as a fair controller-family benchmark could
leak L3-specific semantics into the comparison.
```

Therefore M1674 should run only the standard corrected profile layer:

```text
configs/paper_route_corrected_profiles/m1207_*.json
```

The decisive-history and clean active-set layers remain in the protocol for
later task-source mapping design. They are not executed in M1674.

## Controller Profiles

M1674 must run all 12 profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

No profile may receive profile-specific hyperparameters.

## Command

M1674 should run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --training-seed-base 167400 \
  --seed-offsets 0 \
  --eval-seed-base 167500 \
  --eval-episodes 64 \
  --device cpu
```

This uses PPO because `corrected_profile_pilot` trains each profile with its
committed profile config. PPO is allowed only inside this pre-registered public
pilot command.

## Required Artifacts

```text
runs/m1674_controller_family_one_seed_public_pilot/summary.json
runs/m1674_controller_family_one_seed_public_pilot/protocol.json
runs/m1674_controller_family_one_seed_public_pilot/profile_seed_rows.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_aggregate.csv
runs/m1674_controller_family_one_seed_public_pilot/eval_rows.csv
```

## Success Criteria

M1674 passes as plumbing if:

```text
profile_count == 12
total_seed_runs == 12
completed_seed_runs == 12
failed_seed_runs == 0
all_selected_profile_seed_runs_complete == true
all_eval_metrics_finite == true
private_holdout_used == false
profile_specific_tuning == false
actor_input_contract_changed == false
promoted == false
self_identification_claimed == false
paper_level_claimed == false
```

The result must still route to audit before any interpretation.

## Failure Criteria

M1674 fails or routes to repair if:

```text
any profile train/eval run fails;
any selected metric is non-finite;
any profile uses private holdout or profile-specific tuning;
any actor input contract changes;
the run omits current-tiled or reset controls;
the output is interpreted as architecture ranking before audit.
```

## Metrics To Report

Report at least:

```text
success_rate
collision_rate
clearance_margin_mean
clearance_margin_p10
termination_rate
control_smoothness
spin_or_unstable_rate
parameter_count
```

And comparison deltas:

```text
L2 normal minus matched L2 current-tiled success and margin;
L3 online minus L3 reset success and margin;
L1 one-step versus best L2 and L3 success and margin.
```

These deltas are diagnostic only for one seed.

## Post-Run Audit

M1674 must route to:

```text
m1675-paper-route-controller-family-one-seed-public-pilot-result-audit
```

The audit should decide whether to:

```text
repeat/fix runner plumbing;
design decisive task-source mapping;
admit a three-seed standard-layer repeat;
or stop if one-seed results reveal a structural protocol issue.
```

## Guardrails

```text
training_started: false in M1673
pilot_execution_started: false in M1673
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_specific_tuning_admitted: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1674-paper-route-controller-family-one-seed-public-pilot-implementation
```
