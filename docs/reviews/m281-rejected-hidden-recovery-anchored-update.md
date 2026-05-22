# m281-rejected-hidden-recovery-anchored-update Research Review

## Summary

- Generated at UTC: 20260522T185021Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_rejected_hidden_action_anchor_update
- Decision reason: M281 improves exact M270 objective and repairs M183/M170 row16 but worsens M267/M264 current-family replay with success drops reduced from 17 to 11

## Hypothesis

Rejected-hidden snippet action anchoring can preserve current-family wrong-history contrast while the M279 combined recovery anchor repairs normal terminal-margin slack.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz, runs/m279_m267_m264_replay_gate_seed10070/boundary_replay_rows.csv
- parent_config: experiments/manifests/m280-current-family-wrong-history-washout-audit.json, docs/m280-current-family-wrong-history-washout-audit.md
- parent_objective: M270 objective plus M279 combined recovery anchor plus preferred and rejected hidden snippet action anchoring
- derived_from: m280-current-family-wrong-history-washout-audit
- blocked_by: m280-current-family-wrong-history-washout-audit
- supersedes: None
- invalidates: None

## Success Criteria

- start from m272b_a0_01025
- use M270 source-balanced objective and M279 combined retention/recovery trajectory anchor
- enable snippet action anchoring for both preferred and rejected hidden states
- run exactly one small actor-coupling update before any repeat or PPO
- improve fixed and exact M270 objective versus M272
- preserve M183/M170 row16 terminal margin above the registered required floor
- preserve M267/M264 success drops at 17/17 before broader gates
- actor input contract remains unchanged

## Failure Criteria

- row16 terminal margin crosses the registered floor
- M267/M264 success drops are below 17/17
- objective improves but any required proof surface regresses
- PPO is run
- actor observation inputs change

## Evidence Gates

- fixed sampled and exact M270 objective improvement
- M183/M170 row16 terminal-margin hard gate
- M267/M264 current-family wrong-history success-drop retention
- remaining replay surfaces if first two gates pass
- old protected-key diagnostic if replay passes
- behavior seeds 9505 and 9506 if replay passes
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M281
- do not change actor inputs
- do not use old checkpoint hidden states
- do not pass --snippet-action-anchor-preferred-only
- do not skip M183/M170 row16 or M267/M264

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m281-rejected-hidden-recovery-anchored-update
- type: driver_candidate
- checkpoint: runs/m281_m272_actor_coupling_m270_rejected_hidden_recovery_anchor_s10_lr5e5_seed10077/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_rejected_hidden_action_anchor_update
- reason: M281 improves exact M270 objective and repairs M183/M170 row16 but worsens M267/M264 current-family replay with success drops reduced from 17 to 11

## Next Blocker

m282-current-family-rejected-trajectory-anchor-design
