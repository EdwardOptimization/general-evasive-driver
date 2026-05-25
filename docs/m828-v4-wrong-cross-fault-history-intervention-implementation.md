# M828 V4 Wrong-Cross-Fault History Intervention Implementation

## Purpose

M828 implements the no-training wrong-cross-fault history intervention designed
in M827.

The experiment question is:

```text
If current emergency geometry is held fixed, does injecting recurrent hidden
state from a matched different hidden-dynamics source degrade action or margin?
```

M828 is infrastructure/data-route only:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_wrong_cross_fault_history_intervention.py
```

New tests:

```text
tests/test_v4_wrong_cross_fault_history_intervention.py
```

The implementation:

- joins M825 `matched_pair_rows.csv` to `candidate_plan_rows.csv`;
- reconstructs left/right temporal snapshots from M825 `source_rows.csv`;
- relocates the left snapshot to the left target geometry;
- replays the left current geometry under normal/reset/zero/shift/delay/wrong
  variants;
- injects right recurrent hidden state for `wrong_cross_fault_hidden`;
- keeps the M568 actor and M761 residual head frozen;
- logs zero-command evidence separately from wrong-history evidence.

The key variant is:

```text
wrong_cross_fault_hidden:
  env = copy(left relocated env)
  obs_t = left current observation
  hidden_t = right.hidden
  rollout continues in left env
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_wrong_cross_fault_history_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --matched-pairs runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --run-dir runs/m828_v4_wrong_cross_fault_history_intervention \
  --device cpu
```

## Result

Run directory:

```text
runs/m828_v4_wrong_cross_fault_history_intervention
```

Summary:

```text
result_class: v4_wrong_cross_fault_history_intervention_history_insensitive
raw_matched_pair_rows: 256
selected_pair_rows: 108
reconstructed_snapshot_rows: 15
reconstructed_pairs: 108
wrong_history_replay_rows: 756
accepted_primary_wrong_history_rows: 0
accepted_mitigation_rows: 0
zero_command_accepted_like_rows: 0
rejected_pair_rows: 148
```

The result is a clean negative:

```text
wrong-history replay works,
but wrong hidden alone does not create enough action or margin degradation.
```

## Variant Metrics

Per-variant maximum margin gaps:

```text
reset_hidden_each_step:   0.003792395652133518
reset_hidden_then_normal: 0.0010199475969434602
zero_command_obs:         0.004455360584227908
command_shift_obs:        0.0009262217984864485
response_delay_obs:       0.000010002057777125373
wrong_cross_fault_hidden: 0.00002602146853414311
```

Per-variant mean margin gaps:

```text
reset_hidden_each_step:   0.002154545244661702
reset_hidden_then_normal: 0.0005876195653684621
zero_command_obs:         0.002486210685418355
command_shift_obs:        0.0005178202268021882
response_delay_obs:      -0.000016946046468850567
wrong_cross_fault_hidden: 0.00000457997085936248
```

Per-variant maximum action-prefix/first-action gaps:

```text
zero_command_obs prefix max:         0.057107235715469475
command_shift_obs first max:         0.03941242240728992
reset_hidden_each_step prefix max:   0.026675493021242006
wrong_cross_fault_hidden first max:  0.006900976889874039
wrong_cross_fault_hidden prefix max: 0.003167964278124878
```

Wrong hidden was directionally meaningful but too weak:

```text
wrong_history_closer_to_right_action: 108 / 108
accepted_primary_wrong_history_rows: 0
```

Every wrong-history first action moved closer to the matched right action, but
the movement was below the action threshold and had negligible margin impact.

## Contract Checks

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

The P0 actor contract remains unchanged. Fault labels and pair metadata are
source-selection/logging only.

## Interpretation

M828 supports:

- wrong-cross-fault hidden injection is implemented and reconstructs matched
  pairs successfully;
- right hidden state affects action direction consistently;
- actor and residual-head boundaries stay clean.

M828 does not support:

- strong wrong-history margin degradation;
- strong response-history self-ID evidence from hidden injection alone;
- PPO admission;
- checkpoint promotion.

The important negative detail is:

```text
hidden-only wrong-history injection is directionally correct but too small.
```

This suggests the next audit should decide whether to:

- implement full wrong-history observation replay rather than only hidden
  injection;
- mine stronger matched pairs where current geometry is closer to the boundary;
- or conclude that this M568/M761 family is not strongly response-history
  sensitive enough for the current evidence route.

## Decision

Decision:

```text
v4_wrong_cross_fault_history_intervention_history_insensitive
```

Next:

```text
m829-v4-wrong-cross-fault-history-intervention-audit
```

PPO, checkpoint promotion, learned gating, and threshold relaxation remain
blocked.
