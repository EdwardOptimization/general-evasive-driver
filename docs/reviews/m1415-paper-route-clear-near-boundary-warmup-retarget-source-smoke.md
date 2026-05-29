# m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke Research Review

## Summary

- Generated at UTC: 20260529T011101Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: clear_near_boundary_retarget_source_sampling_failed_route_to_sampling_repair
- Decision reason: M1415 source smoke produces zero rows under the retargeted obstacle filter and classifies the result as scenario sampling failure before warmup evidence can be tested

## Hypothesis

The retuned staged warmup gate can preserve source diversity and warmup command-response evidence while reducing collision pressure enough to justify a later outcome probe.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1414-paper-route-clear-near-boundary-warmup-retarget-design.md, runs/m1412_staged_warmup_gate_collision_stratified_outcome_probe/summary.json
- parent_config: experiments/manifests/m1414-paper-route-clear-near-boundary-warmup-retarget-design.json
- parent_objective: run source smoke for a retuned staged warmup gate that targets clear near-boundary rows
- derived_from: m1414-paper-route-clear-near-boundary-warmup-retarget-design
- blocked_by: M1414 admits source smoke only before outcome probing
- supersedes: rerunning M1410 source smoke without retuning, running outcome probe before retargeted source viability is known
- invalidates: None

## Success Criteria

- retargeted source-smoke configs exist
- runs/m1415_clear_near_boundary_warmup_retarget_source_smoke/summary.json exists
- source diversity and warmup evidence metrics meet the M1414 design thresholds or fail cleanly
- collision share is reported
- result chooses next route without outcome intervention, training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- source smoke artifact is missing
- warmup evidence metrics are missing
- collision/invasiveness metrics are missing
- result routes directly to training, PPO, promotion, private holdout, corpus export, or claim expansion

## Evidence Gates

- M1415 must run no-training source smoke only
- M1415 must report source, warmup evidence, and invasiveness metrics
- M1415 must not run outcome interventions, train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not tune only the 3 M1412 accepted-history seeds
- do not claim level3 self-identification from source materialization

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1415-paper-route-clear-near-boundary-warmup-retarget-source-smoke
- type: infrastructure
- checkpoint: runs/m1415_clear_near_boundary_warmup_retarget_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clear_near_boundary_retarget_source_sampling_failed_route_to_sampling_repair
- reason: M1415 source smoke produces zero rows under the retargeted obstacle filter and classifies the result as scenario sampling failure before warmup evidence can be tested

## Next Blocker

m1416-paper-route-warmup-retarget-sampling-repair-design
