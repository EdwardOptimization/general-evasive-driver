# m761-v4-sequence-objective-only-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T001241Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_sequence_objective_probe_candidate
- Decision reason: M761 residual-only frozen-backbone probe reconstructs 1213 of 1213 rows with unchanged actor checksum and candidate alphas 0.2 0.5 1.0 while PPO and promotion remain blocked

## Hypothesis

A frozen-backbone residual objective-only probe can improve M758 exact gap metrics while keeping normal-history behavior within retention gates.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m760-v4-sequence-objective-only-probe-design.md, runs/m758_v4_sequence_objective_sanity/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m760-v4-sequence-objective-only-probe-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: implement no-PPO residual objective-only probe with exact alpha gates
- derived_from: m760-v4-sequence-objective-only-probe-design
- blocked_by: m760-v4-sequence-objective-only-probe-design
- supersedes: None
- invalidates: None

## Success Criteria

- M761 implements residual probe and focused tests
- base actor checksum remains unchanged
- residual-only training artifacts are written separately
- exact alpha metrics are written for all registered alphas
- at least one result class is assigned without PPO or promotion
- hard-negative sparsity is reported

## Failure Criteria

- base actor parameters change
- PPO runs
- checkpoint is promoted
- fault labels leak into residual inputs
- normal drift or gap metrics are not reported
- hard-negative sparsity is hidden

## Evidence Gates

- M761 freezes base actor parameters
- M761 trains only residual probe parameters
- M761 evaluates exact alpha ladder with M758-style metrics
- M761 reports normal drift and gap lift separately
- PPO and checkpoint promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train base actor parameters
- do not run PPO
- do not promote a checkpoint
- do not use hidden fault labels as residual inputs
- do not hide hard-negative sparsity
- do not skip exact alpha metrics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m761-v4-sequence-objective-only-probe-implementation
- type: infrastructure
- checkpoint: runs/m761_v4_sequence_objective_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_sequence_objective_probe_candidate
- reason: M761 residual-only frozen-backbone probe reconstructs 1213 of 1213 rows with unchanged actor checksum and candidate alphas 0.2 0.5 1.0 while PPO and promotion remain blocked

## Next Blocker

m762-v4-sequence-objective-only-probe-audit
