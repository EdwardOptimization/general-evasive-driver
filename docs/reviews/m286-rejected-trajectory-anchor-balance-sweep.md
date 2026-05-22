# m286-rejected-trajectory-anchor-balance-sweep Research Review

## Summary

- Generated at UTC: 20260522T192307Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m286r2_a500_public_gate_base
- Decision reason: M286 repeat2 alpha 0.5 improves exact M270 by 0.002547 and passes six replay surfaces protected key and behavior gates

## Hypothesis

M284 fails because the rejected-history trajectory anchor pressure is too large; a lower-repeat or lower-pressure source-balanced variant may preserve M267/M264 without crossing the M183/M170 terminal-margin cliff.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m283-current-family-rejected-trajectory-anchor-export.json, experiments/manifests/m284-rejected-trajectory-anchored-update.json, experiments/manifests/m285-m284-interpolation-balance-probe.json
- parent_objective: M270 objective plus lower-pressure rejected-history trajectory retention
- derived_from: m285-m284-interpolation-balance-probe
- blocked_by: m285-m284-interpolation-balance-probe
- supersedes: None
- invalidates: None

## Success Criteria

- export or select lower-pressure rejected-history trajectory anchor variants
- run only no-PPO actor-coupling updates or interpolation probes from M272
- find a candidate that improves exact M270 by materially more than M285 alpha 0.0002
- preserve M183/M170 normal success and M267/M264 success drops in first gates
- actor input contract remains unchanged

## Failure Criteria

- all lower-pressure candidates either fail M183/M170 or lose M267/M264 success drops
- best safe candidate improves exact M270 only at the same microscopic scale as M285
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- keep M272 as the initial checkpoint
- sweep lower rejected trajectory repeat or anchor pressure
- evaluate exact M270 objective for each candidate
- gate M183/M170 and M267/M264 first
- run broader replay protected-key and behavior gates only if first gates pass with non-negligible improvement

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M286
- do not change actor inputs
- do not promote a microscopic interpolation-only improvement
- do not skip M183/M170 row16 or M267/M264
- do not drop the M279 recovery and retention anchor base

## Failure Taxonomy

- none

## Scoreboard

- milestone: m286-rejected-trajectory-anchor-balance-sweep
- type: driver_candidate
- checkpoint: runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844084
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m286r2_a500_public_gate_base
- reason: M286 repeat2 alpha 0.5 improves exact M270 by 0.002547 and passes six replay surfaces protected key and behavior gates

## Next Blocker

m287-balanced-rejected-trajectory-repeat
