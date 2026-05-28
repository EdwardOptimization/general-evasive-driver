# M1315 Paper-Route Source-History Corpus Expansion Plan

## Summary

M1315 implemented and ran the no-policy source-history corpus expansion plan
builder.

Decision:

```text
source_history_corpus_expansion_plan_gap_reported_route_to_source_generator_update_design
```

The existing source artifacts cannot support the M1314 expansion target. The
builder correctly reports coverage gaps instead of fabricating unsupported fault
families.

PPO, promotion, and further objective tuning remain blocked.

## Command

```bash
PYTHONPATH=src python -m autodrift.source_history_corpus_expansion_plan \
  --source-corpus-run-dir runs/m1273_four_wheel_source_corpus_export \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --run-dir runs/m1315_source_history_corpus_expansion_plan \
  --target-source-pairs 240 \
  --fold-count 5
```

## Result

```text
result_class: source_history_corpus_expansion_plan_gap_reported
target_source_pairs: 240
target_pair_probe_groups: 480
planned_source_pairs: 108
planned_pair_probe_groups: 216
source_fault_family_count: 3
corner_or_side_variant_count: 3
materialized_source_pair_count: 38
all_folds_nonempty: true
pair_disjoint: true
max_source_family_fold_share: 0.5789473684
pair_specific_weight_used: false
coverage_gap_reported: true
unsupported_or_undercovered_family_count: 7
```

The plan is valid as a gap-reporting infrastructure artifact. It is not an
admissible expanded corpus.

## Coverage Gaps

Missing families:

```text
global_friction_step->global_friction_step
halfshaft_torque_loss->halfshaft_torque_loss
load_cg_perturbation->load_cg_perturbation
steering_actuator_fault->steering_actuator_fault
tire_blowout_like->tire_blowout_like
```

Under-target families:

```text
left_right_split_mu->left_right_split_mu: 28 / 30
single_wheel_grip_collapse->single_wheel_grip_collapse: 21 / 30
```

Available but skewed:

```text
single_wheel_brake_pull->single_wheel_brake_pull: 59 pairs
```

Fold balance is also too concentrated. The top source family per fold is always
`single_wheel_brake_pull->single_wheel_brake_pull`, with share from `0.5217` to
`0.5789`, above the M1314 target `<=0.40`.

## Interpretation

Supported:

```text
The existing M1273/M1280 artifacts are too narrow for the desired source-history
expansion.
```

Supported:

```text
M1313's scenario_sampling_failure diagnosis is confirmed at the source-corpus
level.
```

Supported:

```text
The next step must update source generation rather than materializing the
current plan or returning to policy-side objective tuning.
```

Not supported:

```text
The existing artifacts can provide 240 source pairs, 480 pair-probe groups, or
six source families.
```

## Guardrails

No policy training occurred:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
```

The plan builder did not use pair-specific weights and did not add privileged
actor inputs.

## Next Step

M1316 should design source-generator updates to create the missing and
undercovered source families:

- tire blowout-like events;
- halfshaft / drive torque loss that creates action-level divergence;
- steering actuator faults;
- global friction steps;
- load / CG perturbations;
- more single-wheel grip collapse variants;
- more split-mu variants;
- fold balancing at generation time.

Do not materialize M1315 as the expanded corpus. It is a coverage-gap report.
