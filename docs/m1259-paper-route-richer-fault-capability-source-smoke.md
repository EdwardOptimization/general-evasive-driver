# M1259 Paper-Route Richer-Fault Capability Source Smoke

## Summary

M1259 runs the bounded no-training richer v4 proxy-fault source smoke admitted
by M1258.

Final strict result:

```text
richer_fault_capability_source_smoke_infrastructure_pass_source_negative_route_to_result_audit
```

The infrastructure part passes: the v4 proxy-fault source config is compatible
with the capability-separable constructor, proposals and rollouts are produced,
model-fidelity limits are written, and no actor mutation, training, PPO,
promotion, private holdout, actor-input expansion, threshold relaxation, or
high-fidelity physical fault claim occurred.

The strict source result remains negative:

```text
accepted_separable_pairs: 0
result_class: action_divergent_low_regret
source_positive: false
```

## Strict Acceptance Correction

During M1259 audit, the first run exposed a semantic mismatch in the constructor:
`asymmetric_success_drop` rows could be counted as `accepted`, even when one
own-branch best candidate was nonviable. That contradicted the paper-route
source-positive criterion used in M1258/M1259:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Fix:

```text
accepted = symmetric_margin_accept
```

The diagnostic flag remains:

```text
asymmetric_success_drop
```

and the summary now reports:

```text
asymmetric_success_drop_pairs
```

Focused evidence:

```text
new red test:
  test_evaluate_action_separability_rejects_asymmetric_nonviable_best_branch

before fix:
  failed because accepted was true

after fix:
  tests/test_capability_separable_source_constructor.py -> 9 passed
```

The M1259 run was rerun after this fix. The numbers below are the strict rerun.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 78048 \
  --seed-count 4 \
  --max-pairs 12 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 4 \
  --candidate-mode trajectory_proposal \
  --sequence-length 4 \
  --proposal-count-per-condition 24 \
  --proposal-seed 125900 \
  --proposal-steer-scale 0.45 \
  --proposal-brake-scale 0.45 \
  --proposal-throttle-scale 0.25 \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.002 \
  --target-max-best-margin 0.08 \
  --max-relocation-candidates 12 \
  --fine-relocation \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1259_richer_fault_capability_source_smoke
```

## Evidence

Primary artifact:

```text
runs/m1259_richer_fault_capability_source_smoke/summary.json
```

Summary metrics:

```text
scenario_count: 116
snapshot_count: 812
candidate_pair_count: 784
matched_pair_count: 12
trajectory_proposals: 642
trajectory_proposal_rollouts: 1284
relocation_candidates: 144
coarse_relocation_candidates: 96
fine_relocation_candidates: 48
near_boundary_viability_pairs: 8
best_actions_diverged_pairs: 4
asymmetric_success_drop_pairs: 0
low_regret_pairs: 12
accepted_separable_pairs: 0
unique_matched_fault_family_pairs: 3
unique_matched_seeds: 3
result_class: action_divergent_low_regret
```

Guardrails:

```text
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

## Pair Diagnostics

The richer v4 source family improved source shape compared with M1255:

```text
M1255 near_boundary_viability_pairs: 1
M1259 near_boundary_viability_pairs: 8

M1255 best_actions_diverged_pairs: 2
M1259 best_actions_diverged_pairs: 4
```

But accepted strict source rows remain absent.

Closest viable/action-divergent row:

```text
pair_id: 5
seed: 78049
fault_family_pair: global_mu_drop->brake_authority_drop
condition_A_fault: mu_drop_extreme_preexisting
condition_B_fault: brake_fade_extreme_pre_emergency
best_action_l2: 0.7001441121
margin_A_best_A: 0.0799886482
margin_A_best_B: 0.0747198233
margin_B_best_B: 0.0337841324
margin_B_best_A: 0.0295662466
cross_regret_A: 0.0052688249
cross_regret_B: 0.0042178858
rejection_reason: insufficient_cross_regret
```

This row is important but not accepted: both branches are viable and actions
differ strongly, but two-sided regret is below the `0.02` threshold.

High one-sided-regret nonviable examples:

```text
pair_id: 6
fault_family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.3671781421
cross_regret_A: 0.3547101085
cross_regret_B: 0.0036265200
pair_min_best_margin: -0.0215043970
rejection_reason: best_candidate_not_viable

pair_id: 7
fault_family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.3796271086
cross_regret_A: 0.3529748276
cross_regret_B: 0.0018674623
pair_min_best_margin: -0.0315347489
rejection_reason: best_candidate_not_viable
```

Dominant negative pattern:

```text
global_mu_drop->brake_authority_drop:
  action divergence exists, but min two-sided regret is below threshold or
  own-branch viability fails.

global_mu_drop->front_lateral_authority_drop:
  mostly viable/action-equivalent or tiny-regret rows.

global_mu_drop->rear_lateral_authority_drop:
  viable/action-equivalent rows dominate.
```

## Fidelity Boundary

M1259 uses current single-track/current-model proxy faults for source mining.

Allowed claim:

```text
v4 proxy fault source family is richer and produces stronger source diagnostics
than the narrower M1236/M1241 source family.
```

Blocked claims:

```text
true single-wheel blowout physics
true stuck-caliper yaw moment physics
true halfshaft asymmetric torque loss
true split-mu left/right physics
true suspension/toe damage physics
real-vehicle evidence
paper-level self-identification evidence
```

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

Subtype:

```text
richer_fault_source_low_regret
```

Additional process issue found and fixed:

```text
metric_artifact:
  asymmetric_success_drop was previously counted as accepted.
```

The final rerun is strict and does not contain this artifact.

## Decision

M1259 is an infrastructure pass and a strict source-negative result.

Do not train or start PPO.

Do not claim source-positive capability separability.

Next milestone:

```text
m1260-paper-route-richer-fault-capability-source-result-audit
```

The audit should decide whether to try one richer-fault repair variable, such
as boundary/regret retargeting around pair 5, or stop/pivot before another
source run. It must preserve strict accepted-source criteria.
