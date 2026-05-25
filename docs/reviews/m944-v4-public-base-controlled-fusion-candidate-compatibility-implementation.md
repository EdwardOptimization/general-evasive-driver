# m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation Research Review

## Summary

- Generated at UTC: 20260525T233905Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_controlled_fusion_candidate_compatibility_primary_candidate_route_to_replay_gate_design
- Decision reason: M944 materializes M942 candidates and all three remain exact candidates from ordinary checkpoint loading; primary alpha 0.0725 passes with training replay PPO and promotion blocked

## Hypothesis

The M942 candidate alphas remain exact candidates after materializing them as ordinary loadable checkpoints.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt
- parent_dataset: docs/m943-v4-public-base-controlled-fusion-candidate-compatibility-design.md, runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/summary.json, runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/alpha_metrics.csv
- parent_config: experiments/manifests/m943-v4-public-base-controlled-fusion-candidate-compatibility-design.json
- parent_objective: materialize M942 candidate checkpoints and re-run exact no-update objective compatibility
- derived_from: m943-v4-public-base-controlled-fusion-candidate-compatibility-design
- blocked_by: candidate checkpoint materialization and exact compatibility have not yet run
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- materialized_checkpoint_count is 3
- exact_candidate_count >= 1
- primary_candidate_exact_pass is true
- forbidden_parameter_changed is false
- training_started optimizer_started replay_used ppo_used and promoted are false

## Failure Criteria

- candidate checkpoint materialization fails
- primary candidate no longer passes exact metrics after loading
- forbidden parameters change
- M944 runs replay PPO or promotion

## Evidence Gates

- M944 must materialize candidate checkpoints for alphas 0.0675 0.0700 0.0725
- M944 must re-run exact objective metrics from materialized checkpoints
- M944 must keep forbidden parameters unchanged
- M944 must keep training replay PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not change actor inputs
- do not unfreeze response_encoder context_encoder or online_gru_cell

## Failure Taxonomy

- none

## Scoreboard

- milestone: m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation
- type: infrastructure
- checkpoint: runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_controlled_fusion_candidate_compatibility_primary_candidate_route_to_replay_gate_design
- reason: M944 materializes M942 candidates and all three remain exact candidates from ordinary checkpoint loading; primary alpha 0.0725 passes with training replay PPO and promotion blocked

## Next Blocker

m945-v4-public-base-controlled-fusion-candidate-replay-gate-design
