# m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation Research Review

## Summary

- Generated at UTC: 20260525T235635Z
- Type: gate
- Gate tier: proof
- Promotion decision: public_base_controlled_fusion_candidate_replay_gate_proof_washout_route_to_failing_surface_audit
- Decision reason: M946 rejects alpha 0.0725 because public M267/M264 success_drop_count regresses 17 to 13 while behavior seeds pass and PPO promotion remain blocked

## Hypothesis

The M944 alpha 0.0725 candidate may retain closed-loop proof and behavior surfaces while improving the public objective surface.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
- parent_dataset: docs/m945-v4-public-base-controlled-fusion-candidate-replay-gate-design.md, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/summary.json, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/candidate_compatibility.csv
- parent_config: experiments/manifests/m945-v4-public-base-controlled-fusion-candidate-replay-gate-design.json
- parent_objective: run no-training closed-loop replay/proof retention for materialized M944 primary candidate
- derived_from: m945-v4-public-base-controlled-fusion-candidate-replay-gate-design
- blocked_by: materialized exact candidate has not yet been checked on closed-loop replay/proof surfaces
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- all six public replay surfaces are evaluated
- behavior seeds 9505 and 9506 are evaluated
- actor_inputs_changed is false
- training_started is false
- ppo_used and promoted are false

## Failure Criteria

- any replay surface fails
- behavior seeds materially regress
- actor inputs change
- M946 runs PPO or promotion

## Evidence Gates

- M946 must run no-training replay/proof retention
- M946 must evaluate six public replay surfaces
- M946 must evaluate behavior seeds 9505 and 9506
- M946 must keep PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote a checkpoint
- do not change actor inputs
- do not treat exact objective compatibility as closed-loop proof

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation
- type: gate
- checkpoint: runs/m946_v4_public_base_controlled_fusion_candidate_replay_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_controlled_fusion_candidate_replay_gate_proof_washout_route_to_failing_surface_audit
- reason: M946 rejects alpha 0.0725 because public M267/M264 success_drop_count regresses 17 to 13 while behavior seeds pass and PPO promotion remain blocked

## Next Blocker

m947-v4-public-base-controlled-fusion-candidate-failing-surface-audit
