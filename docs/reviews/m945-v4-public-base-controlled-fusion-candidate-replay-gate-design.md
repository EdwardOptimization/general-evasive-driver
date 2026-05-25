# m945-v4-public-base-controlled-fusion-candidate-replay-gate-design Research Review

## Summary

- Generated at UTC: 20260525T234230Z
- Type: gate
- Gate tier: process
- Promotion decision: controlled_fusion_candidate_replay_gate_design_admit_m946
- Decision reason: M945 designs no-training replay/proof retention for the materialized alpha 0.0725 candidate including six public replay surfaces behavior seeds and PPO promotion blocked

## Hypothesis

The materialized M944 primary candidate should be checked on closed-loop replay/proof surfaces before any PPO or promotion path.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/interpolation/checkpoints/alpha_0_0725.pt
- parent_dataset: docs/m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation.md, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/summary.json, runs/m944_v4_public_base_controlled_fusion_candidate_compatibility/candidate_compatibility.csv
- parent_config: experiments/manifests/m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation.json
- parent_objective: design no-training replay/proof retention for materialized controlled-fusion candidate
- derived_from: m944-v4-public-base-controlled-fusion-candidate-compatibility-implementation
- blocked_by: materialized exact candidate has not yet been checked on closed-loop replay/proof surfaces
- supersedes: None
- invalidates: None

## Success Criteria

- M945 names the primary candidate checkpoint
- M945 defines replay/proof retention gates
- M945 defines behavior-retention checks
- M945 blocks PPO and promotion
- M945 defines route logic for pass/fail

## Failure Criteria

- M945 allows promotion from exact objective metrics alone
- M945 omits replay/proof retention
- M945 admits PPO before replay proof
- M945 changes actor inputs

## Evidence Gates

- M945 must design replay/proof retention before any promotion
- M945 must keep PPO blocked
- M945 must preserve P0 actor input contract
- M945 must identify primary and backup checkpoints

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M945
- do not run PPO
- do not promote a checkpoint
- do not change actor inputs
- do not treat exact objective compatibility as closed-loop proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m945-v4-public-base-controlled-fusion-candidate-replay-gate-design
- type: gate
- checkpoint: docs/m945-v4-public-base-controlled-fusion-candidate-replay-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_candidate_replay_gate_design_admit_m946
- reason: M945 designs no-training replay/proof retention for the materialized alpha 0.0725 candidate including six public replay surfaces behavior seeds and PPO promotion blocked

## Next Blocker

m946-v4-public-base-controlled-fusion-candidate-replay-gate-implementation
