# m1416-paper-route-warmup-retarget-sampling-repair-design Research Review

## Summary

- Generated at UTC: 20260529T011417Z
- Type: gate
- Gate tier: process
- Promotion decision: warmup_retarget_sampling_repair_design_admit_repaired_source_smoke
- Decision reason: M1416 repairs M1415 sampling by preserving the retuned warmup gate but relaxing obstacle filters toward M1410 and admits source smoke only

## Hypothesis

Relaxing the obstacle sampling filter while preserving the retuned warmup gate can repair M1415 source materialization without claim expansion.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1415_clear_near_boundary_warmup_retarget_source_smoke/summary.json, docs/m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke.md
- parent_config: configs/ppo_m1415_clear_near_boundary_warmup_retarget_figure_eight.json, configs/m1415_clear_near_boundary_warmup_retarget_source_wave.json, experiments/manifests/m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke.json
- parent_objective: design a sampling repair after M1415 fails before source materialization
- derived_from: m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke
- blocked_by: M1415 source smoke produced zero rows due obstacle scenario sampling failure
- supersedes: rerunning M1415 with the same over-constrained obstacle filter, treating M1415 no-rows as evidence against the retuned warmup gate
- invalidates: None

## Success Criteria

- docs/m1416-paper-route-warmup-retarget-sampling-repair-design.md exists
- design identifies the M1415 sampling failure
- design specifies repaired obstacle and warmup gate parameters
- design admits or rejects one repaired source smoke without training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- repair design document is missing
- repair ignores M1415 sampling failure
- repair reruns the same over-constrained obstacle filter
- repair routes directly to outcome probing, training, PPO, promotion, private holdout, corpus export, or claim expansion

## Evidence Gates

- M1416 must repair scenario sampling before another source smoke
- M1416 must preserve the retuned warmup gate geometry unless explicitly justified
- M1416 must not train, run PPO, run source smoke, run outcome interventions, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source smoke
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not claim self-identification from M1415 no-rows
- do not rerun the same over-constrained obstacle filter

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1416-paper-route-warmup-retarget-sampling-repair-design
- type: gate
- checkpoint: docs/m1416-paper-route-warmup-retarget-sampling-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: warmup_retarget_sampling_repair_design_admit_repaired_source_smoke
- reason: M1416 repairs M1415 sampling by preserving the retuned warmup gate but relaxing obstacle filters toward M1410 and admits source smoke only

## Next Blocker

m1417-paper-route-warmup-retarget-sampling-repair-source-smoke
