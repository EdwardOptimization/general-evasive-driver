# m695-trajectory-terminal-boundary-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T163957Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: trajectory_terminal_boundary_source_miner_surface_empty_admit_audit
- Decision reason: M695 implements the miner cleanly but finds 0 accepted rows on the M692 source surface so objective design actor update PPO and promotion remain blocked

## Hypothesis

Closed-loop perturbation replay can identify terminal-margin-sensitive rows that are not already normal-failed and are diverse enough to support a later objective.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m694-trajectory-terminal-boundary-source-mining-design.md, runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
- parent_config: experiments/manifests/m694-trajectory-terminal-boundary-source-mining-design.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: implement trajectory and terminal-margin sensitive source miner
- derived_from: m694-trajectory-terminal-boundary-source-mining-design
- blocked_by: m694-trajectory-terminal-boundary-source-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- candidate_rows.csv is written
- perturbation_rollouts.csv is written
- accepted_rows.csv is written
- source_summary.csv is written
- split_summary.csv is written
- normal-failed rejection counts are reported
- terminal-margin sensitivity metrics are finite
- source diversity metrics are finite
- actor checksum unchanged
- no actor update PPO or promotion

## Failure Criteria

- implementation trains or mutates the actor
- implementation omits terminal-margin sensitivity metrics
- implementation accepts normal-failed rows as action-critical
- implementation hides rejected/skipped rows
- implementation admits objective training without source_positive result

## Evidence Gates

- miner writes summary candidate perturbation accepted source split and rejected artifacts
- normal-failed rows are rejected from action-critical acceptance
- terminal-margin and risk sensitivity metrics are reported
- source diversity metrics are reported
- result class is recorded
- actor checksum is unchanged
- no actor update PPO or promotion occurs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not accept output-only exact residual metrics as source evidence
- do not accept already normal-failed rows as action-critical
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m695-trajectory-terminal-boundary-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m695_trajectory_terminal_boundary_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: trajectory_terminal_boundary_source_miner_surface_empty_admit_audit
- reason: M695 implements the miner cleanly but finds 0 accepted rows on the M692 source surface so objective design actor update PPO and promotion remain blocked

## Next Blocker

m696-trajectory-terminal-boundary-source-miner-audit
