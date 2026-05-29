# m1565-paper-route-flip-anchor-source-generation-repair-design Research Review

## Summary

- Generated at UTC: 20260529T135438Z
- Type: gate
- Gate tier: process
- Promotion decision: flip_anchor_source_generation_repair_design_admit_bounded_generator
- Decision reason: M1565 designs bounded source-generation repair targeting source-diverse distinct collision/success flip anchors before history interventions

## Hypothesis

A bounded source-generation repair can be designed to produce more source-diverse distinct collision/success flip anchors before any history-intervention replay.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1563_source_balanced_recoverable_active_set_selector/summary.json, docs/m1564-paper-route-source-balanced-selector-result-audit.md
- parent_config: experiments/manifests/m1564-paper-route-source-balanced-selector-result-audit.json
- parent_objective: design a bounded source-generation repair that increases source-diverse distinct flip anchors before history interventions
- derived_from: m1564-paper-route-source-balanced-selector-result-audit
- blocked_by: M1563 selector has enough balanced recoverable anchors but only 5 distinct collision/success flip anchors from one source family
- supersedes: direct history interventions over M1563 selected set, silent reinterpretation of local variant counts as independent flip anchors
- invalidates: None

## Success Criteria

- docs/m1565-paper-route-flip-anchor-source-generation-repair-design.md exists
- design targets distinct flip anchors rather than local variant counts
- design includes source-family and window diversity gates
- design keeps history interventions materialization training PPO promotion private holdout actor-input changes and training-corpus export blocked
- the next route is explicit

## Failure Criteria

- design document is missing
- design reinterprets variant counts as independent anchors
- design routes directly to history interventions training promotion private holdout or materialization
- design changes actor inputs or weakens the evidence standard

## Evidence Gates

- M1565 must design a bounded source-generation repair for distinct flip anchors
- M1565 must not reinterpret local variant counts as independent anchors
- M1565 must not run simulator or history interventions
- M1565 must preserve P0 actor input contract
- M1565 must keep materialization training PPO promotion and private holdout blocked

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

- milestone: m1565-paper-route-flip-anchor-source-generation-repair-design
- type: gate
- checkpoint: docs/m1565-paper-route-flip-anchor-source-generation-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: flip_anchor_source_generation_repair_design_admit_bounded_generator
- reason: M1565 designs bounded source-generation repair targeting source-diverse distinct collision/success flip anchors before history interventions

## Next Blocker

m1566-paper-route-flip-anchor-source-generation-repair-implementation
