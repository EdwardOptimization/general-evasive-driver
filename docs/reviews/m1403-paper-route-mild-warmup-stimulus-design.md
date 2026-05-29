# m1403-paper-route-mild-warmup-stimulus-design Research Review

## Summary

- Generated at UTC: 20260529T000359Z
- Type: gate
- Gate tier: process
- Promotion decision: mild_warmup_stimulus_design_admit_config_source_smoke
- Decision reason: M1403 designs figure-eight mild warmup stimulus and near-boundary obstacle pressure before source smoke or outcome probing

## Hypothesis

A mild warmup stimulus design can create deployable command-response evidence and near-boundary reveals without adding oracle actor inputs.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1402-paper-route-warmup-reveal-pressure-outcome-result-audit.md, runs/m1401_warmup_reveal_pressure_outcome_probe/summary.json, runs/m1401_warmup_reveal_pressure_outcome_probe/normal_margin_band_summary.csv
- parent_config: experiments/manifests/m1402-paper-route-warmup-reveal-pressure-outcome-result-audit.json
- parent_objective: design mild warmup stimulus and near-boundary reveal task route after late reveal alone is action-only
- derived_from: m1402-paper-route-warmup-reveal-pressure-outcome-result-audit
- blocked_by: M1401 action-only result shows late reveal alone does not create near-boundary outcome gaps
- supersedes: running another late-reveal grid without a new evidence axis, training from action-only M1401 rows
- invalidates: None

## Success Criteria

- docs/m1403-paper-route-mild-warmup-stimulus-design.md exists
- design specifies warmup stimulus, near-boundary reveal criteria, current/recent controls, source-diversity thresholds, and next implementation route
- design does not route directly to training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- design document is missing
- design ignores M1401 action-only result
- design adds actor oracle labels or scripted controller mode
- design omits near-boundary or current/recent controls
- design routes directly to training or claim expansion

## Evidence Gates

- M1403 must design a mild warmup stimulus task route before implementation
- M1403 must define how warmup evidence is created without actor-input oracle labels
- M1403 must define near-boundary reveal and current/recent substitution controls
- M1403 must not train, run PPO, run a source sweep, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run a new source sweep
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not add oracle mode/reference labels to actor observation
- do not count action-only evidence as self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1403-paper-route-mild-warmup-stimulus-design
- type: gate
- checkpoint: docs/m1403-paper-route-mild-warmup-stimulus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: mild_warmup_stimulus_design_admit_config_source_smoke
- reason: M1403 designs figure-eight mild warmup stimulus and near-boundary obstacle pressure before source smoke or outcome probing

## Next Blocker

m1404-paper-route-mild-warmup-stimulus-source-smoke
