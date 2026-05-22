# m279-recovery-anchored-actor-update Research Review

## Summary

- Generated at UTC: 20260522T184225Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_recovery_anchored_actor_update_current_family_washout
- Decision reason: M279 improves exact M270 objective and repairs M183/M170 row16 but fails M267/M264 current-family replay with success drops reduced from 17 to 12

## Hypothesis

Adding the M278 current-hidden recovery anchor to the M270 objective and M275 retention anchor can improve objective while preserving row16 terminal-margin slack.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz, runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.npz, runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
- parent_config: experiments/manifests/m278-current-hidden-recovery-anchor-probe.json, docs/m278-current-hidden-recovery-anchor-probe.md
- parent_objective: M270 source-balanced objective plus M275 retention anchor plus M278 recovery anchor
- derived_from: m278-current-hidden-recovery-anchor-probe
- blocked_by: m278-current-hidden-recovery-anchor-probe
- supersedes: None
- invalidates: None

## Success Criteria

- start from m272b_a0_01025
- use M270 source-balanced objective and a combined trajectory anchor that keeps M275 retention while replacing recovered step0 targets with M278 recovery actions
- run exactly one small actor-coupling update before any repeat or PPO
- improve fixed M270 objective versus M272
- preserve M183/M170 row16 terminal margin above the registered required floor
- preserve all six replay surfaces, protected key, and behavior seeds if row16 passes
- actor input contract remains unchanged

## Failure Criteria

- row16 terminal margin crosses the registered floor
- combined objective improves but row16 or replay surfaces regress
- recovery anchor creates objective movement but loses behavior retention
- PPO is run
- actor observation inputs change

## Evidence Gates

- fixed sampled and exact M270 objective improvement
- M183/M170 row16 terminal-margin hard gate
- M278 recovery-anchor MSE check
- six replay surfaces if row16 passes
- old protected-key diagnostic if replay passes
- behavior seeds 9505 and 9506 if replay passes
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M279
- do not change actor inputs
- do not use old checkpoint hidden states
- do not skip M183/M170 row16
- do not promote based only on objective improvement

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m279-recovery-anchored-actor-update
- type: driver_candidate
- checkpoint: runs/m279_m272_actor_coupling_m270_retention_recovery_anchor_s10_lr5e5_seed10076/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_recovery_anchored_actor_update_current_family_washout
- reason: M279 improves exact M270 objective and repairs M183/M170 row16 but fails M267/M264 current-family replay with success drops reduced from 17 to 12

## Next Blocker

m280-current-family-wrong-history-washout-audit
