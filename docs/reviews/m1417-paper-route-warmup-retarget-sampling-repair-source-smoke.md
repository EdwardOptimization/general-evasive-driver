# m1417-paper-route-warmup-retarget-sampling-repair-source-smoke Research Review

## Summary

- Generated at UTC: 20260529T012418Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: warmup_retarget_sampling_repair_source_structural_pass_invasiveness_fail_route_to_audit
- Decision reason: M1417 restores source materialization with 1630 source rows and 250 matched/bucketed rows but misses the matched invasiveness gate with 0.544 collision share

## Hypothesis

Relaxed obstacle sampling with the retuned warmup gate will restore source materialization and reduce collision pressure enough to justify a later outcome probe.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1415_clear_near_boundary_warmup_retarget_source_smoke/summary.json, docs/m1416-paper-route-warmup-retarget-sampling-repair-design.md
- parent_config: experiments/manifests/m1416-paper-route-warmup-retarget-sampling-repair-design.json
- parent_objective: run a repaired source smoke that relaxes obstacle sampling while preserving retuned warmup gate geometry
- derived_from: m1416-paper-route-warmup-retarget-sampling-repair-design
- blocked_by: M1416 admits repaired source smoke only
- supersedes: rerunning M1415 over-constrained sampling filter, running outcome probe before source materialization is repaired
- invalidates: None

## Success Criteria

- repaired source-smoke configs exist
- runs/m1417_warmup_retarget_sampling_repair_source_smoke/summary.json exists
- source diversity, warmup evidence, and collision metrics are reported
- result chooses next route without outcome intervention, training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- source smoke artifact is missing
- source rows are zero or metrics are missing
- result routes directly to training, PPO, promotion, private holdout, corpus export, or claim expansion

## Evidence Gates

- M1417 must run no-training repaired source smoke only
- M1417 must report source diversity, warmup evidence, and collision share
- M1417 must not run outcome interventions, train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

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
- do not claim self-identification from source materialization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1417-paper-route-warmup-retarget-sampling-repair-source-smoke
- type: infrastructure
- checkpoint: runs/m1417_warmup_retarget_sampling_repair_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: warmup_retarget_sampling_repair_source_structural_pass_invasiveness_fail_route_to_audit
- reason: M1417 restores source materialization with 1630 source rows and 250 matched/bucketed rows but misses the matched invasiveness gate with 0.544 collision share

## Next Blocker

m1418-paper-route-warmup-retarget-source-result-audit
