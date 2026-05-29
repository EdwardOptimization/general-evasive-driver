# m1581-paper-route-history-pairability-source-generation-design Research Review

## Summary

- Generated at UTC: 20260529T153156Z
- Type: gate
- Gate tier: process
- Promotion decision: history_pairability_source_generation_design_admit_bounded_implementation
- Decision reason: M1581 designs pairability-first source generation with tiered matched-current hidden-divergent gates before any interventions

## Hypothesis

A pairability-first source miner can be designed to test whether the public simulator can produce matched-current hidden-divergent source pairs before history interventions.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair.md, runs/m1576_history_sensitive_active_set_miner_smoke/summary.json, runs/m1579_high_speed_late_history_source_repair_smoke/summary.json
- parent_config: experiments/manifests/m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair.json
- parent_objective: design pairability-first source generation before more history interventions
- derived_from: m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair
- blocked_by: M1579 found zero matched-current hidden-divergent high-speed/late donor pairs
- supersedes: another recoverable active-set repair without pairability proof
- invalidates: None

## Success Criteria

- docs/m1581-paper-route-history-pairability-source-generation-design.md exists
- design defines pairability gates before interventions
- design includes source-family/window diversity gates and null taxonomy
- implementation smoke materialization training PPO promotion private holdout corpus export and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design assumes pairability instead of gating it
- design routes directly to training PPO promotion private holdout corpus export actor-input changes candidate materialization or interventions

## Evidence Gates

- M1581 must design a pairability-first source miner
- M1581 must define matched-current hidden-divergent pairability gates before interventions
- M1581 must include source-family and window diversity gates
- M1581 must include stop rules if pairability is absent
- M1581 must keep implementation smoke materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run history interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1581-paper-route-history-pairability-source-generation-design
- type: gate
- checkpoint: docs/m1581-paper-route-history-pairability-source-generation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_pairability_source_generation_design_admit_bounded_implementation
- reason: M1581 designs pairability-first source generation with tiered matched-current hidden-divergent gates before any interventions

## Next Blocker

m1582-paper-route-history-pairability-source-miner-implementation
