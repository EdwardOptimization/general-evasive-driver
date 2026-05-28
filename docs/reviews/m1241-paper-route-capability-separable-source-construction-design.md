# m1241-paper-route-capability-separable-source-construction-design Research Review

## Summary

- Generated at UTC: 20260528T085911Z
- Type: gate
- Gate tier: process
- Promotion decision: capability_separable_source_construction_design_admit_lattice_smoke
- Decision reason: M1241 defines offline matched-current hidden-dynamics action-separability criterion artifacts actor-input guardrails and admits bounded no-training M1242 lattice smoke

## Hypothesis

A source-construction branch that first proves hidden dynamics require different actions is higher leverage than more random hidden-fault intervention tests.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1240-paper-route-extreme-fault-source-generation-synthesis.md, runs/m1238_extreme_fault_sequence_intervention_probe/summary.json, runs/m1236_extreme_fault_timing_repair_smoke/summary.json
- parent_config: experiments/manifests/m1240-paper-route-extreme-fault-source-generation-synthesis.json
- parent_objective: design a source-construction branch that first proves hidden dynamics require different actions under matched current observations
- derived_from: m1240-paper-route-extreme-fault-source-generation-synthesis
- blocked_by: M1240 closes the same-source extreme/fault path after no-signal sequence evidence
- supersedes: more same-source extreme/fault hidden-swap or sequence variants
- invalidates: assuming hidden-dynamics randomization automatically creates self-ID-critical cases

## Success Criteria

- docs/m1241-paper-route-capability-separable-source-construction-design.md exists
- action-separability criterion is specified
- source artifacts are specified
- actor-input guardrails are specified
- first bounded implementation step is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1241 trains or tunes profiles
- private holdout is used
- hidden dynamics labels are added to actor inputs
- action-separability gates are left vague
- next route is left vague

## Evidence Gates

- M1241 may design source construction only
- M1241 must preserve actor input contract
- M1241 must not train controllers
- M1241 must not run PPO
- M1241 must not use private holdout
- M1241 must not promote
- M1241 must keep hidden dynamics and oracle/source labels out of deployable actor inputs
- M1241 must define a bounded first implementation step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters or oracle labels to actor inputs
- do not claim self-identification from source construction alone
- do not use a rule controller as a deployable actor

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1241-paper-route-capability-separable-source-construction-design
- type: gate
- checkpoint: docs/m1241-paper-route-capability-separable-source-construction-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_separable_source_construction_design_admit_lattice_smoke
- reason: M1241 defines offline matched-current hidden-dynamics action-separability criterion artifacts actor-input guardrails and admits bounded no-training M1242 lattice smoke

## Next Blocker

m1242-paper-route-capability-separable-source-constructor-smoke
