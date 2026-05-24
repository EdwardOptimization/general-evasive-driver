# m748-v4-extreme-fault-coverage-design Research Review

## Summary

- Generated at UTC: 20260524T230815Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_extreme_fault_coverage_design_admit_m749
- Decision reason: M748 defines a runnable v4 current-model/proxy fault config plus future four-wheel claim boundary and admits only a no-training M749 source-mining wave

## Hypothesis

A v4 extreme-fault taxonomy can broaden scenario coverage while keeping honest claim boundaries between current single-track faults, proxy faults, and future four-wheel/high-fidelity faults.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint_used
- parent_dataset: docs/m747-v3-sequence-outcome-corpus-export-audit.md, docs/m746-v3-sequence-outcome-corpus-export-implementation.md, runs/m746_v3_sequence_outcome_corpus_export/summary.json
- parent_config: experiments/manifests/m747-v3-sequence-outcome-corpus-export-audit.json, configs/extreme_fault_distribution_v3_scenarios.json
- parent_objective: design v4 extreme-fault coverage taxonomy and data-wave plan before training from public v3 corpus
- derived_from: m747-v3-sequence-outcome-corpus-export-audit
- blocked_by: m747-v3-sequence-outcome-corpus-export-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M748 defines fault categories and claim levels
- M748 includes wheel blowout sudden grip loss split-mu brake faults halfshaft driveline sensor actuator suspension and combined failures
- M748 maps each fault to current_model_fault current_model_proxy or future_four_wheel_or_high_fidelity
- M748 defines no-training source generation and sequence-outcome mining gates for M749
- M748 blocks objective training PPO and checkpoint promotion

## Failure Criteria

- design overclaims true per-wheel physics from current single-track proxies
- design injects hidden fault labels into actor observations
- design omits sentinel or source-balance gates
- design admits actor training PPO or checkpoint promotion

## Evidence Gates

- M748 defines v4 fault taxonomy with current proxy and future-fidelity claim levels
- M748 covers blowout sudden grip loss split-mu brake drag brake loss halfshaft driveline sensor actuator suspension and combined failures
- M748 defines which faults are implementable in the current single-track model and which require four-wheel or high-fidelity dynamics
- M748 defines source balance sentinel and sequence-outcome gates for a later data wave
- objective training PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim current proxy faults are true per-wheel physics
- do not add hidden fault labels to actor observations
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not skip claim-boundary metadata

## Failure Taxonomy

- none

## Scoreboard

- milestone: m748-v4-extreme-fault-coverage-design
- type: infrastructure
- checkpoint: docs/m748-v4-extreme-fault-coverage-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_extreme_fault_coverage_design_admit_m749
- reason: M748 defines a runnable v4 current-model/proxy fault config plus future four-wheel claim boundary and admits only a no-training M749 source-mining wave

## Next Blocker

m749-v4-extreme-fault-coverage-implementation
