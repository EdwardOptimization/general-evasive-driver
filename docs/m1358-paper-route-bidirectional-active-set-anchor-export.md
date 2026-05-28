# M1358 Paper-Route Bidirectional Active-Set Anchor Export

## Summary

M1358 exported the branch-asymmetric anchor artifacts admitted by M1357.

Decision:

```text
bidirectional_active_set_anchor_export_pass_route_to_probe_design
```

This milestone is artifact-only. It does not train, run PPO, update actor
weights, run replay gates, use private holdout, promote a checkpoint, or change
the actor input contract.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.rejected_history_trajectory_anchor \
  --checkpoint-policy m1154_base=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --corpus-csv runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --base-combined-anchor-npz runs/m1355_materialized_source_history_replay_aware_retention_probe/retention_surface/retention_trajectory_anchor.npz \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --required-row-ids 6,10,13,15,16 \
  --max-continuation-steps 60 \
  --rejected-weight 10.0 \
  --failed-row-weight 50.0 \
  --rejected-repeat 16 \
  --device cpu \
  --run-dir runs/m1358_bidirectional_active_set_anchor_export
```

## Result

The run completed successfully.

Key artifact:

```text
runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
```

Summary:

```text
rows_selected: 17
required_row_ids: [6, 10, 13, 15, 16]
required_rows_present: true
rejected_trajectory_rows: 669
combined_anchor_rows: 12113
base_correct_rows: 1409
rejected_repeat: 16
forbidden_shortcuts_used: false
ppo_or_actor_update_run: false
```

Combined anchor shapes:

```text
observation:       [12113, 72]
hidden:            [12113, 128]
reference_action:  [12113, 3]
```

The exported NPZ also contains:

```text
source_index
step_index
weight
```

This is enough for the next probe to use the existing M1355 correct-history
retention anchor and the M267/M264 wrong-history rejected trajectory anchor in a
single trajectory action-anchor loss.

## Interpretation

M1358 resolves the immediate artifact blocker from M1357. The missing data for a
bidirectional active-set update now exists:

```text
correct-history branch:
  M1355 retention surface, 1409 trajectory rows.

wrong-history branch:
  M267/M264 rejected trajectories, 669 rows, repeated 16 times.

combined branch:
  12113 weighted anchor rows.
```

This does not prove that the bidirectional objective will work. It only proves
that the branch-asymmetric active-set inputs can be materialized without
violating the no-PPO/no-update/no-private-holdout guardrails.

## Guardrails

M1358 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1359-paper-route-bidirectional-active-set-probe-design
```

M1359 should design the no-PPO probe that consumes:

```text
runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
```

The probe must evaluate exact source-history metrics first, then M267/M264, then
M183/M170 only if M267/M264 passes.
