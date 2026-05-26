# m998-v4-public-base-capability-step-fault-generation-synthesis Research Review

## Summary

- Generated at UTC: 20260526T152618Z
- Type: gate
- Gate tier: process
- Promotion decision: capability_step_fault_generation_synthesis_open_temporal_sequence_objective
- Decision reason: M998 synthesizes M989-M997 closes capability-step fault generation and opens temporal sequence objective design while blocking cross-fault overclaims

## Hypothesis

M989-M997 should be synthesized before temporal objective design because the branch produced a usable temporal corpus but did not produce cross-fault wrong-history evidence.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m989-v4-public-base-capability-step-fault-design.md, runs/m990_v4_public_base_capability_step_fault_smoke/summary.json, runs/m991_v4_public_base_capability_step_fault_source_wave/summary.json, docs/m992-v4-public-base-capability-step-reset-only-audit.md, docs/m993-v4-public-base-capability-step-sequence-intervention-design.md, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json, docs/m995-v4-public-base-capability-step-temporal-history-audit.md, docs/m996-v4-public-base-temporal-sequence-corpus-export-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/summary.json
- parent_config: configs/m990_capability_step_fault_scenarios.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: synthesize capability-step fault generation evidence before temporal objective design
- derived_from: m989-v4-public-base-capability-step-fault-design, m990-v4-public-base-capability-step-fault-smoke, m991-v4-public-base-capability-step-fault-source-wave, m992-v4-public-base-capability-step-reset-only-audit, m993-v4-public-base-capability-step-sequence-intervention-design, m994-v4-public-base-capability-step-sequence-intervention-probe, m995-v4-public-base-capability-step-temporal-history-audit, m996-v4-public-base-temporal-sequence-corpus-export-design, m997-v4-public-base-temporal-sequence-corpus-export-implementation
- blocked_by: M997 produces an exact-auditable temporal corpus while cross-fault positives remain absent
- supersedes: None
- invalidates: continuing capability-step fault generation without synthesis, training from the temporal corpus before opening a new objective branch

## Success Criteria

- synthesis artifact exists
- supported and falsified claims are explicit
- failure taxonomy is explicit
- public gate overfit risk is updated
- next branch decision is explicit
- no training or promotion occurs

## Failure Criteria

- synthesis artifact is missing
- route decision is missing
- M997 is overclaimed as cross-fault self-ID
- training or PPO starts
- unsupported per-wheel failure claims are made

## Evidence Gates

- M998 must synthesize M989-M997 before objective design
- M998 must not run PPO
- M998 must not promote
- M998 must not use private holdout
- M998 must preserve P0 actor-input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or optimize
- do not claim cross-fault wrong-history self-ID
- do not claim per-wheel or asymmetric faults under the current single-track model
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m998-v4-public-base-capability-step-fault-generation-synthesis
- type: gate
- checkpoint: docs/m998-v4-public-base-capability-step-fault-generation-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_step_fault_generation_synthesis_open_temporal_sequence_objective
- reason: M998 synthesizes M989-M997 closes capability-step fault generation and opens temporal sequence objective design while blocking cross-fault overclaims

## Next Blocker

m999-v4-public-base-temporal-sequence-objective-design
