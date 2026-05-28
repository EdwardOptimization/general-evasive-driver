# M1227 Paper-Route Terminal-Boundary Relocation Smoke

## Summary

M1227 runs the first bounded terminal-boundary relocation smoke over the M1226
source-diverse candidate export.

Decision:

```text
terminal_boundary_relocation_smoke_negative_audit_required
```

The run is negative for materialized wrong-history outcome evidence:

```text
source_budget_ready: true
candidate_selection_ready: true
relocation_replay_started: true
raw relocation rows: 7200
accepted_wrong_rows: 0
normal_success rows: 0
variant_success rows: 0
normal_collision rows: 7200
variant_collision rows: 7200
normal_margin_positive rows: 0
margin_gap >= 0.010 rows: 77
normal_near_boundary and margin_gap >= 0.010 rows: 0
```

No training, PPO, promotion, private holdout, profile tuning, or actor-input
change occurs in M1227.

## Command

The first command attempt exposed an argparse detail: negative offset lists must
be passed with `=`. The registered command was repaired before the successful
run.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --outcome-csv runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --target-normal-margins 0.0005,0.001,0.002,0.003,0.005,0.010 \
  --half-width-inflations 0,0.10 \
  --body-longitudinal-offsets=-2,0,2 \
  --body-lateral-offsets=-0.25,0,0.25 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.010 \
  --report-variants wrong_matched_history \
  --max-candidates 120 \
  --max-candidates-per-physical-pair 1 \
  --max-candidates-per-checkpoint-target 64 \
  --target-min-physical-pairs 40 \
  --target-min-left-steps 5 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.05 \
  --min-eligible-physical-pairs 40 \
  --max-candidate-pair-fraction 0.05 \
  --device cpu \
  --run-dir runs/m1227_terminal_boundary_relocation_smoke
```

## Harness Fixes

M1227 exposed two harness issues that were fixed before recording the final
run:

1. `boundary_wrong_history_surface_robustness.add_robustness_keys` did not
   handle empty typed DataFrames correctly.
2. `source_balanced_boundary_relocation_surface.select_source_balanced_candidates`
   reported `source_balanced_candidates_ready` without enforcing
   `target_min_left_steps` and `target_min_targets`.

Focused tests now cover both paths.

## Source And Candidate Gates

Source budget:

```text
candidate_wrong_history_rows:       274
eligible_physical_pairs:            110
eligible_left_steps:                  5
eligible_checkpoints:                 1
eligible_targets:                     2
eligible_source_obstacle_buckets:     5
max_candidate_pair_fraction:          0.0109489051
source_budget_ready: true
```

Candidate selection:

```text
selected_rows:                       100
selected_physical_pairs:             100
selected_left_steps:                   5
selected_targets:                      2
max_selected_pair_fraction:            0.01
decision: source_balanced_candidates_ready
```

The final run therefore did enter relocation replay under the corrected gates.

## Relocation Outcome

Relocation produced no accepted wrong-history boundary rows:

```text
boundary_relocation_rows: 7200
accepted_wrong_rows:        0
balanced_exportable_rows:   0
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

The apparent `reject_duplicate_dominated_boundary_surface` decision is a generic
downstream robustness-gate label. The real failure mode is sharper:

```text
all normal rollouts collided
all wrong-history rollouts collided
no normal rollout remained near-boundary successful
no source-diverse accepted outcome row exists
```

Observed row diagnostics:

```text
normal_success:          0 / 7200
variant_success:         0 / 7200
normal_collision:     7200 / 7200
variant_collision:    7200 / 7200
normal_margin range:  [-0.2999323157, -0.0000110193]
variant_margin range: [-0.2998067883, -0.0000528075]
margin_gap range:     [-0.2454804599, 0.2511298426]
margin_gap >= 0.010:  77 rows
accepted rows:        0 rows
```

Because `normal_success` is false for every relocated row, positive margin gap
rows cannot be used as wrong-history proof rows.

## Interpretation

M1227 does not support a causal-history or self-identification claim. It shows
that the first bounded relocation grid over M1226 candidates overshot the
terminal-boundary materialization target: the normal branch is pushed past the
boundary into collision for all replay rows.

This does not falsify terminal-boundary materialization in general. It does
falsify the current relocation grid as a useful proof generator.

## Guardrails

Verified:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
relocation_replay_started: true
full_new_mining_run: false
```

## Next

M1228 should audit the negative result before another relocation run.

The audit should decide whether the next route is:

```text
1. a narrower/safer relocation grid that keeps normal branch successful;
2. a candidate selection change that prioritizes lower base normal margins;
3. a stronger source distribution such as explicit fault/extreme scenarios;
4. closing terminal-boundary materialization if the failure repeats.
```

Do not train from M1227, do not weaken accepted-row criteria, and do not treat
positive margin gaps from all-collision rows as proof.
