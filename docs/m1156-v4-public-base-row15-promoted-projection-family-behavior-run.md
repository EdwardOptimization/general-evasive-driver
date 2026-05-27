# M1156 V4 Public Base Row15 Promoted Projection Family Behavior Run

## Purpose

M1156 runs the diagnostics designed in M1155 for the M1154 projection
candidate:

```text
candidate_label: alpha_0_05
candidate_checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

base_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

The milestone is diagnostic only. It does not train actor weights, run PPO,
mine rows, promote, use private holdout, or change actor inputs.

## Commands

M1144 exact recheck:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy alpha_0_05=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --device cpu \
  --exact \
  --baseline-policy row15_current \
  --logprob-margin 0.05 \
  --run-dir runs/m1156_row15_promoted_projection_m1144_exact_eval
```

Expanded public diagnostic:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.candidate_b_combined_active_set_full_public_gate \
  --base-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --candidate-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --temporal-corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --temporal-base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --combined-anchor-npz runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz \
  --fresh-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --ood-env-config configs/eval_m574_moderate_ood_l3.json \
  --behavior-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --fresh-seeds 103900,103901 \
  --ood-seeds 103920 \
  --behavior-seeds 9505,9506,103930,103931 \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80 \
  --max-continuation-steps 60 \
  --preference-margin 0.05 \
  --lambda-pref 1.0 \
  --lambda-anchor 0.25 \
  --device auto \
  --run-dir runs/m1156_row15_promoted_projection_expanded_public_diagnostic
```

## Result

M1156 passes both diagnostic stages:

```text
M1144 exact recheck: pass
expanded public diagnostic: pass
result_class: candidate_b_combined_active_set_full_public_gate_candidate
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
```

No training, PPO, mining, promotion, private holdout, or actor-input change
occurred.

## M1144 Exact Recheck

The selected candidate retains the M1154 exact M1144 improvement:

```text
row15_current exact loss: 0.417700052
alpha_0_05 exact loss:  0.417321652
delta:                 -0.000378400
snippets:               76
mode:                   exact
```

## Expanded Public Diagnostic

The expanded wrapper reports all diagnostic tiers passing.

Contract and exact diagnostics:

```text
actor_inputs_changed: false
allowed_surface_contract_pass: true
changed parameter prefixes:
  actor_mean.
  response_context_fusion.0.
M297/M270 exact pass: true
full exact contract gate pass: true
```

Old-public proof replay:

```text
m183_m168: 16 / 16 success drops retained
m183_m170: 17 / 17 success drops retained
m193_m189: 14 / 14 success drops retained
m212_m204: 17 / 17 success drops retained
m223_m219: 17 / 17 success drops retained
m267_m264: 17 / 17 success drops retained
```

M1061 family-intersection replay:

```text
short61049 surface: 25 / 25 retained
short61050 surface: 27 / 27 retained
short61051 surface: 27 / 27 retained
```

Source-diverse protected replay:

```text
current_m333_surface:    17 / 17 retained
m317_continuity_surface: 17 / 17 retained
m314_continuity_surface: 17 / 17 retained
```

Fresh and OOD evals retain base success:

```text
fresh seed 103900: base 0.867188, candidate 0.867188, delta 0.0
fresh seed 103901: base 0.871094, candidate 0.871094, delta 0.0
OOD seed 103920:   base 0.640625, candidate 0.640625, delta 0.0
```

Behavior seeds retain base success and reset/zero-all ordering:

```text
seed 9505:   base 0.8625, candidate 0.8625, reset 0.8500, zero-all 0.8000
seed 9506:   base 0.8625, candidate 0.8625, reset 0.8500, zero-all 0.8000
seed 103930: base 0.8375, candidate 0.8375, reset 0.8125, zero-all 0.8000
seed 103931: base 0.8250, candidate 0.8250, reset 0.8000, zero-all 0.7875
```

The old `9944|perturbed|28|28` neighborhood remains diagnostic-only. Both base
and candidate have the same diagnostic pass status there, so it does not create
a new blocker for this candidate.

## Interpretation

M1156 supports a narrow public-diagnostic claim: the M1154 `alpha_0_05`
projection preserves exact M1144 improvement while passing the current expanded
public proof, family-intersection, source-diverse, fresh/OOD, and behavior
diagnostics.

This is still not a driver-performance claim and not a private-holdout or
paper-level claim. The candidate is also near an unsafe-margin boundary from
M1154:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

Because of that near-zero margin, M1156 should route to a separate diagnostic
result audit or promotion-audit design rather than directly promoting the
checkpoint.

## Artifacts

```text
runs/m1156_row15_promoted_projection_m1144_exact_eval/summary.json
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/summary.json
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/exact_contract_summary.csv
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/proof_replay_summary.csv
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/family_intersection_public_gate/replay_gate_summary.csv
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/source_diverse_protected_diagnostic/replay_gate_summary.csv
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/generalization_comparison.csv
runs/m1156_row15_promoted_projection_expanded_public_diagnostic/behavior_comparison.csv
```

## Decision

```text
decision: row15_promoted_projection_expanded_diagnostic_pass_route_to_result_audit
next: m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit
```
