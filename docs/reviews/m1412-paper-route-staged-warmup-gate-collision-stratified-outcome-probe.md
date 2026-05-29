# m1412-paper-route-staged-warmup-gate-collision-stratified-outcome-probe Research Review

## Summary

- Generated at UTC: 20260529T005402Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: staged_warmup_gate_outcome_history_sparse_route_to_result_audit
- Decision reason: M1412 finds 14 warmup-history-positive rows from 3 seeds and 7 capability pairs with 10 clear-stratum positives but zero wrong-warmup positives so it routes to audit not training

## Hypothesis

The staged warmup gate source rows will reveal whether warmup command-response history interventions cause outcome-relevant margin/success gaps, and collision stratification will show whether any signal is only an invasive-gate artifact.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1410_staged_warmup_gate_source_smoke/matched_or_bucketed_rows.csv, runs/m1410_staged_warmup_gate_source_smoke/summary.json, docs/m1411-paper-route-staged-warmup-gate-source-result-audit.md
- parent_config: configs/m1410_staged_warmup_gate_source_wave.json, experiments/manifests/m1411-paper-route-staged-warmup-gate-source-result-audit.json
- parent_objective: run no-training outcome interventions over M1410 matched/bucketed rows while preserving warmup gate collision/source diagnostics
- derived_from: m1411-paper-route-staged-warmup-gate-source-result-audit
- blocked_by: M1411 admits only collision-stratified outcome probing before retune, corpus export, or training
- supersedes: running unstratified M1410 outcome probing, training from M1410 source materialization
- invalidates: None

## Success Criteria

- outcome probe propagates source warmup gate diagnostics into outcome artifacts
- runs/m1412_staged_warmup_gate_collision_stratified_outcome_probe/summary.json exists
- summary reports accepted rows by variant and warmup gate collision stratum
- summary reports warmup-history-positive rows separately from reset/zero-current controls
- result chooses next route without training, PPO, promotion, private holdout, corpus export, or actor-input expansion

## Failure Criteria

- outcome artifact is missing
- warmup gate collision/source diagnostics are missing from outcome reporting
- result aggregates collision-heavy and collision-free rows without stratification
- result routes directly to training, PPO, promotion, private holdout, corpus export, or claim expansion

## Evidence Gates

- M1412 must run no-training outcome probing only
- M1412 must preserve and report warmup gate collision/source diagnostics
- M1412 must separate warmup-history-positive rows from reset/zero-current rows
- M1412 must not train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

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
- do not aggregate collision-heavy and collision-free rows without stratified reporting

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1412-paper-route-staged-warmup-gate-collision-stratified-outcome-probe
- type: infrastructure
- checkpoint: runs/m1412_staged_warmup_gate_collision_stratified_outcome_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: staged_warmup_gate_outcome_history_sparse_route_to_result_audit
- reason: M1412 finds 14 warmup-history-positive rows from 3 seeds and 7 capability pairs with 10 clear-stratum positives but zero wrong-warmup positives so it routes to audit not training

## Next Blocker

m1413-paper-route-staged-warmup-outcome-result-audit
