# m993-v4-public-base-capability-step-sequence-intervention-design Research Review

## Summary

- Generated at UTC: 20260526T134151Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: sequence_intervention_design_admit_probe
- Decision reason: M993 designs a no-training trace-window sequence intervention probe to test action-response mismatch on M991 reset-only rows

## Hypothesis

A sequence-level action-response mismatch intervention can create a cleaner belief mismatch than single hidden-state swaps on capability-step reset-only rows.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m992-v4-public-base-capability-step-reset-only-audit.md, runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv
- parent_config: experiments/manifests/m992-v4-public-base-capability-step-reset-only-audit.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: design sequence-level action-response mismatch interventions for capability-step reset-only rows
- derived_from: m992-v4-public-base-capability-step-reset-only-audit, m991-v4-public-base-capability-step-fault-source-wave
- blocked_by: M991 wrong-history hidden swaps are too compatible while reset-hidden is strongly disruptive
- supersedes: None
- invalidates: continuing same-style single-hidden-swap mining without a new intervention

## Success Criteria

- design artifact exists
- candidate interventions are specified
- input-contract preservation is explicit
- acceptance gates include terminal margin or success relevance
- implementation route is explicit
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- route decision is missing
- hidden labels would enter actor observation
- reset-only rows are treated as proof-positive
- training or PPO starts

## Evidence Gates

- M993 must not run PPO
- M993 must not promote
- M993 must not change actor inputs
- M993 must keep reset-only rows diagnostic
- M993 must define terminal/outcome relevance before implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not count reset-only rows as accepted wrong-history rows
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m993-v4-public-base-capability-step-sequence-intervention-design
- type: infrastructure
- checkpoint: docs/m993-v4-public-base-capability-step-sequence-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_intervention_design_admit_probe
- reason: M993 designs a no-training trace-window sequence intervention probe to test action-response mismatch on M991 reset-only rows

## Next Blocker

m994-v4-public-base-capability-step-sequence-intervention-probe
