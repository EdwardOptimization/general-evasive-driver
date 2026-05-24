# m749-v4-extreme-fault-coverage-implementation Research Review

## Summary

- Generated at UTC: 20260524T231825Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: cross_fault_reset_only
- Decision reason: M749 runs 14848 v4 scenarios and 12288 matched pairs with 1171 reset-only rows but 0 wrong-history action rows so sequence intervention is the next likely branch after audit

## Hypothesis

The v4 extreme-fault coverage config will produce broader reset, action, or outcome-sensitive command-response self-ID source rows than the v3 source wave alone.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m748-v4-extreme-fault-coverage-design.md, runs/m746_v3_sequence_outcome_corpus_export/summary.json
- parent_config: experiments/manifests/m748-v4-extreme-fault-coverage-design.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: run no-training v4 extreme-fault source-mining wave before objective work
- derived_from: m748-v4-extreme-fault-coverage-design
- blocked_by: m748-v4-extreme-fault-coverage-design
- supersedes: None
- invalidates: None

## Success Criteria

- M749 validates v4 config
- M749 runs the registered no-training v4 data wave
- M749 writes scenario matched-pair accepted rejected and summary artifacts
- M749 reports source diversity reset wrong-history action and outcome metrics separately
- M749 records current-model proxy versus future-fidelity claim boundary
- no training PPO actor update or promotion occurs

## Failure Criteria

- future-fidelity faults are counted as current-model evidence
- runner mutates actor observations with hidden fault labels
- runner combines reset action and outcome claims
- runner changes actor input contract
- runner starts optimizer training PPO or checkpoint promotion

## Evidence Gates

- M749 validates v4 config with supported current-model fault families
- M749 runs a no-training v4 data wave
- M749 reports source reset action outcome and sentinel metrics separately
- M749 preserves future-fidelity faults as metadata only
- actor update PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim proxy faults are true per-wheel physics
- do not inject hidden fault labels into actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not lower gates after seeing M749 output

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m749-v4-extreme-fault-coverage-implementation
- type: infrastructure
- checkpoint: runs/m749_extreme_fault_distribution_v4/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_reset_only
- reason: M749 runs 14848 v4 scenarios and 12288 matched pairs with 1171 reset-only rows but 0 wrong-history action rows so sequence intervention is the next likely branch after audit

## Next Blocker

m750-v4-extreme-fault-coverage-audit
