# m698-fresh-trajectory-boundary-sampler-implementation Research Review

## Summary

- Generated at UTC: 20260524T165838Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: fresh_trajectory_boundary_sampler_empty_admit_audit
- Decision reason: M698 implements fresh sampling cleanly but finds 0 accepted rows from 512 episodes so objective actor update PPO and promotion remain blocked

## Hypothesis

Fresh broad scenario sampling can find trajectory-sensitive terminal-boundary rows missed by the inherited M692 surface.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m697-fresh-trajectory-boundary-sampling-design.md, runs/m695_trajectory_terminal_boundary_source_miner/summary.json
- parent_config: experiments/manifests/m697-fresh-trajectory-boundary-sampling-design.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: implement fresh broad trajectory-boundary sampler
- derived_from: m697-fresh-trajectory-boundary-sampling-design
- blocked_by: m697-fresh-trajectory-boundary-sampling-design
- supersedes: m695 M692-row-only source miner
- invalidates: None

## Success Criteria

- summary.json is written
- episode_summary.csv is written
- snapshot_candidates.csv is written
- prepass_rows.csv is written
- perturbation_rollouts.csv is written
- accepted_rows.csv is written
- rejected_rows.csv is written
- terminal-margin and risk sensitivity metrics are finite
- source diversity metrics are finite
- actor checksum unchanged
- no objective actor update PPO or promotion

## Failure Criteria

- implementation depends only on M692 rows
- implementation omits normal-failed rejection
- implementation omits terminal-margin or risk sensitivity
- implementation hides skipped/rejected rows
- implementation admits objective design without fresh_source_positive

## Evidence Gates

- sampler uses fresh scenario seeds
- sampler writes episode snapshot prepass perturbation accepted rejected and summary artifacts
- normal-failed rows are rejected from action-critical acceptance
- terminal-margin and risk sensitivity metrics are reported
- source diversity metrics are reported
- actor checksum is unchanged
- no objective actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not use M692 rows as the only source
- do not accept already normal-failed rows as action-critical
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m698-fresh-trajectory-boundary-sampler-implementation
- type: infrastructure
- checkpoint: runs/m698_fresh_trajectory_boundary_sampler/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fresh_trajectory_boundary_sampler_empty_admit_audit
- reason: M698 implements fresh sampling cleanly but finds 0 accepted rows from 512 episodes so objective actor update PPO and promotion remain blocked

## Next Blocker

m699-fresh-trajectory-boundary-sampler-audit
