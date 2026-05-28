# m1270-paper-route-four-wheel-source-viability-calibration-design Research Review

## Summary

- Generated at UTC: 20260528T124220Z
- Type: gate
- Gate tier: process
- Promotion decision: four_wheel_source_viability_calibration_design_admit_smoke
- Decision reason: M1270 designs calibrated four-wheel source viability grid after M1268 collision dominance and admits bounded no-policy M1271 smoke

## Hypothesis

A bounded viability calibration design can preserve M1268's high-regret signal while targeting own-branch viability under unchanged thresholds.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1269-paper-route-four-wheel-fault-source-shape-result-audit.md, runs/m1268_four_wheel_fault_source_shape_smoke/summary.json
- parent_config: experiments/manifests/m1269-paper-route-four-wheel-fault-source-shape-result-audit.json
- parent_objective: design bounded four-wheel source viability calibration after high-regret rows are collision dominated
- derived_from: m1269-paper-route-four-wheel-fault-source-shape-result-audit
- blocked_by: M1269 admits own-branch viability calibration as the next source variable
- supersedes: another same-grid four-wheel source-shape run
- invalidates: None

## Success Criteria

- docs/m1270-paper-route-four-wheel-source-viability-calibration-design.md exists
- design cites M1268 high-regret/collision-dominance evidence
- design defines calibrated scenario/action axes
- design preserves success semantics and strict thresholds
- design pre-registers one bounded implementation if admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design lowers strict accepted-source thresholds
- design treats horizon-only rows as success
- design ignores collision-dominance diagnostics
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1270 must preserve actor input contract
- M1270 must not train controllers
- M1270 must not run PPO
- M1270 must not use private holdout
- M1270 must not promote
- M1270 must design a new viability variable without threshold relaxation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not treat collision-dominated rows as source-positive
- do not revert to horizon-only success

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1270-paper-route-four-wheel-source-viability-calibration-design
- type: gate
- checkpoint: docs/m1270-paper-route-four-wheel-source-viability-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_viability_calibration_design_admit_smoke
- reason: M1270 designs calibrated four-wheel source viability grid after M1268 collision dominance and admits bounded no-policy M1271 smoke

## Next Blocker

m1271-paper-route-four-wheel-source-viability-calibration-smoke
