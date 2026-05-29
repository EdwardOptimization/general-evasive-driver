# m1421-paper-route-m1419-source-collision-stratified-outcome-probe Research Review

## Summary

- Generated at UTC: 20260529T014841Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: m1419_source_outcome_reset_or_current_only_route_to_result_audit
- Decision reason: M1421 evaluates 2016 outcome rows from M1419 source and finds 0 warmup-history positives with 1 zero-current control row so routes to audit

## Hypothesis

The less invasive M1419 source rows will reveal whether staged warmup command-response history interventions produce more source-diverse outcome-critical effects than M1412.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1419_warmup_gate_invasiveness_retune_source_smoke/summary.json, runs/m1419_warmup_gate_invasiveness_retune_source_smoke/matched_or_bucketed_rows.csv, docs/m1420-paper-route-warmup-reveal-pressure-retune-branch-synthesis.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1420-paper-route-warmup-reveal-pressure-retune-branch-synthesis.json
- parent_objective: run one no-training collision-stratified outcome probe on M1419 source rows after branch synthesis
- derived_from: m1420-paper-route-warmup-reveal-pressure-retune-branch-synthesis
- blocked_by: M1420 admits only one no-training outcome probe from M1419 before any training corpus export or further retune
- supersedes: running another source retune after M1419, training from M1419 source rows, running unstratified outcome probing
- invalidates: None

## Success Criteria

- runs/m1421_m1419_source_collision_stratified_outcome_probe/summary.json exists
- selected_candidate_rows >= 240
- outcome probe propagates source warmup gate diagnostics into outcome artifacts
- summary reports accepted rows by variant and warmup gate collision stratum
- summary reports warmup-history-positive rows separately from reset and zero-current controls
- summary reports wrong_warmup_history_same_reveal and same_recent_wrong_warmup_history rows
- result chooses next route without training PPO promotion private holdout corpus export or actor-input expansion

## Failure Criteria

- outcome artifact is missing
- candidate rows drop below 240
- warmup gate collision/source diagnostics are missing from outcome reporting
- result aggregates collision-heavy and collision-free rows without stratification
- result routes directly to training PPO promotion private holdout corpus export or claim expansion

## Evidence Gates

- M1421 must run no-training outcome probing only
- M1421 must use M1419 matched/bucketed source rows
- M1421 must preserve and report warmup gate collision/source diagnostics
- M1421 must separate warmup-history-positive rows from reset and zero-current controls
- M1421 must not train run PPO promote use private holdout export a training corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not claim self-identification from source materialization
- do not ignore the M1419 one-seed source-diversity miss
- do not aggregate collision-heavy and collision-free rows without stratified reporting

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1421-paper-route-m1419-source-collision-stratified-outcome-probe
- type: infrastructure
- checkpoint: runs/m1421_m1419_source_collision_stratified_outcome_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: m1419_source_outcome_reset_or_current_only_route_to_result_audit
- reason: M1421 evaluates 2016 outcome rows from M1419 source and finds 0 warmup-history positives with 1 zero-current control row so routes to audit

## Next Blocker

m1422-paper-route-m1419-outcome-result-audit
