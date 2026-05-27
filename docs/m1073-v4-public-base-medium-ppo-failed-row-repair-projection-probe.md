# M1073 V4 Public Base Medium PPO Failed-Row Repair Projection Probe

## Purpose

M1073 runs a no-PPO repair/projection probe using the M1072 failed-row
projection corpus. It does not run PPO, promote, or use private holdout.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_combined_active_set_repair_projection_probe \
  --base-checkpoint runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --raw-checkpoint runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt \
  --current-family-conflict-npz runs/m1072_medium_ppo_failed_row_projection_corpus/current_family_conflict_corpus.npz \
  --combined-anchor-npz runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz \
  --run-dir runs/m1073_medium_ppo_failed_row_repair_projection_probe \
  --device auto
```

## Result

```text
result_class: candidate_b_combined_active_set_projection_first_replay_candidate
selected_candidate_label: m1031_line_row16x4_s40_a1
selected_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_line_row16x4_s40_a1.pt
actor_inputs_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
```

M1073 is positive but limited. It finds a first-replay candidate; it does not
prove the candidate passes the expanded full public gate.

## Exact Repair Candidates

All three exact-repair starts found exact-lexicographic candidates:

```text
raw_row16x4_s40:
  exact_lexicographic_pass: true
  exact_m297_delta_vs_base: -0.000212669
  exact_m270_delta_vs_base: -0.000229120

base_row16x4_s40:
  exact_lexicographic_pass: true
  exact_m297_delta_vs_base: -0.000085235
  exact_m270_delta_vs_base: -0.000068545

line_row16x4_s40:
  exact_lexicographic_pass: true
  exact_m297_delta_vs_base: -0.000123620
  exact_m270_delta_vs_base: -0.000085533
```

The selected checkpoint comes from `line_row16x4_s40` with alpha `1.0`.

## Projection Metrics

```text
temporal_exact_pass_count: 30
temporal_and_exact_pass_count: 30
eligible_candidate_count: 30
first_replay_attempted_candidate_count: 1
```

Selected combined-anchor metrics:

```text
selected_combined_anchor_total_loss: 0.00000944194
selected_combined_anchor_m267_loss: 0.0000365366
selected_combined_anchor_m183_row16_loss: 0.00000266829
```

## First Replay Gates

The selected candidate passed the first replay checks:

```text
m267_m264: 17 / 17 success drops retained, pass
m183_m170: 17 / 17 success drops retained, pass
m267_m264 row15 retained: true
```

These are necessary but not sufficient. M1069 failed old public, M1061
family-intersection, and source-diverse gates; M1073 has not yet rerun the
expanded full stack against the selected candidate.

## Interpretation

The M1072 failed-row corpus gives a useful projection direction. The raw M1069
checkpoint was rejected, but treating it as a proposal and repairing/projecting
under exact objectives can recover a first-replay-safe candidate.

The next test must be a full expanded public gate. Do not promote from this
milestone.

## Decision

```text
medium_ppo_failed_row_projection_first_replay_candidate_route_to_full_public_gate
```

Next:

```text
m1074-v4-public-base-medium-ppo-repair-projection-full-public-gate
```
