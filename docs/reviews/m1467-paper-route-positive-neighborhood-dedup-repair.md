# m1467-paper-route-positive-neighborhood-dedup-repair Research Review

## Summary

- Generated at UTC: 20260529T051125Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: positive_neighborhood_dedup_repair_implemented_admit_rerun
- Decision reason: M1467 deduplicates selected positive_neighborhood_key rows and adds focused tests before rerunning proposal smoke

## Hypothesis

Dropping duplicate positive_neighborhood_key rows before selection removes M1465's metric artifact without actor changes.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1465_positive_neighborhood_expansion_smoke/summary.json, docs/m1466-paper-route-boundary-retarget-validation-synthesis.md
- parent_config: experiments/manifests/m1466-paper-route-boundary-retarget-validation-synthesis.json
- parent_objective: repair duplicate selected positive_neighborhood_key rows before further preflight or replay
- derived_from: m1466-paper-route-boundary-retarget-validation-synthesis
- blocked_by: M1465 selected 192 rows but only 20 unique positive_neighborhood_key values
- supersedes: replaying duplicated M1465 selected candidates
- invalidates: None

## Success Criteria

- dedup repair is implemented
- focused tests pass for duplicate candidate-pool rows
- focused tests pass for unique selected positive_neighborhood_key
- docs/m1467-paper-route-positive-neighborhood-dedup-repair.md exists
- no preflight replay training PPO promotion private holdout corpus export or actor-input change occurs

## Failure Criteria

- implementation is missing
- tests do not cover duplicate selected keys
- implementation starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1467 must deduplicate positive_neighborhood_key before selection
- M1467 must add tests for duplicate candidate-pool rows
- M1467 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source preflight
- do not run bounded replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1467-paper-route-positive-neighborhood-dedup-repair
- type: infrastructure
- checkpoint: docs/m1467-paper-route-positive-neighborhood-dedup-repair.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: positive_neighborhood_dedup_repair_implemented_admit_rerun
- reason: M1467 deduplicates selected positive_neighborhood_key rows and adds focused tests before rerunning proposal smoke

## Next Blocker

m1468-paper-route-positive-neighborhood-dedup-smoke
