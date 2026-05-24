# m697-fresh-trajectory-boundary-sampling-design Research Review

## Summary

- Generated at UTC: 20260524T164455Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: fresh_trajectory_boundary_sampling_design_admit_m698
- Decision reason: M697 designs fresh broad scenario sampling with snapshot windowing normal prepass perturbation sensitivity source diversity and no objective PPO promotion

## Hypothesis

Fresh broad scenario sampling can find terminal-margin-sensitive rows that the M692 replay surface missed.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m696-trajectory-terminal-boundary-source-miner-audit.md, runs/m695_trajectory_terminal_boundary_source_miner/summary.json
- parent_config: experiments/manifests/m696-trajectory-terminal-boundary-source-miner-audit.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: design fresh broad scenario sampling for terminal-boundary source mining
- derived_from: m696-trajectory-terminal-boundary-source-miner-audit
- blocked_by: m696-trajectory-terminal-boundary-source-miner-audit
- supersedes: m695 source rows limited to M692 replay surface
- invalidates: None

## Success Criteria

- design defines fresh seed and scenario sampling
- design defines snapshot collection windows
- design defines normal-history prepass
- design defines perturbation sensitivity metrics
- design defines wrong/counterfactual-history tests when available
- design defines source-diversity and split rules
- objective actor update PPO and promotion remain blocked

## Failure Criteria

- design only reuses M692 rows
- design accepts normal-failed rows as action-critical
- design omits terminal-margin or risk sensitivity
- design omits diversity and heldout rules
- design admits objective training before mining

## Evidence Gates

- design samples fresh scenarios rather than only M692 rows
- design includes normal-history prepass and normal-failed rejection
- design includes terminal-margin and risk sensitivity tests
- design includes source-diversity and heldout rules
- design blocks objective actor update PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not reuse M692 rows as the only source
- do not accept already normal-failed rows as action-critical
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m697-fresh-trajectory-boundary-sampling-design
- type: infrastructure
- checkpoint: docs/m697-fresh-trajectory-boundary-sampling-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fresh_trajectory_boundary_sampling_design_admit_m698
- reason: M697 designs fresh broad scenario sampling with snapshot windowing normal prepass perturbation sensitivity source diversity and no objective PPO promotion

## Next Blocker

m698-fresh-trajectory-boundary-sampler-implementation
