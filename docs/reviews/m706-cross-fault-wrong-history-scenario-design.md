# m706-cross-fault-wrong-history-scenario-design Research Review

## Summary

- Generated at UTC: 20260524T183642Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: cross_fault_wrong_history_scenario_design_admit_m707
- Decision reason: M706 designs a cross-fault pairing matrix severity contrast ladder wrong-history-specific gates and no-training M707 artifacts while blocking source export PPO and promotion

## Hypothesis

Cross-fault wrong-history pairing will produce stronger self-ID evidence than nominal-vs-fault pairing because the wrong hidden state will encode an incompatible capability belief.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m705-extreme-dynamics-scenario-corpus-audit.md, runs/m704_extreme_dynamics_scenario_corpus/summary.json, runs/m704_extreme_dynamics_scenario_corpus/accepted_rows.csv, runs/m704_extreme_dynamics_scenario_corpus/fault_family_summary.csv
- parent_config: experiments/manifests/m705-extreme-dynamics-scenario-corpus-audit.json, configs/extreme_hidden_condition_scenarios.json
- parent_objective: design cross-fault wrong-history scenario pairing after M704 reset-only result
- derived_from: m705-extreme-dynamics-scenario-corpus-audit
- blocked_by: m705-extreme-dynamics-scenario-corpus-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines cross-fault pairing matrix
- design defines wrong-history-specific acceptance criteria
- design defines severity contrast ladder
- design defines no-training artifacts
- design preserves model-fidelity limits
- objective actor update PPO and promotion remain blocked

## Failure Criteria

- design treats reset-only rows as source-positive
- design omits wrong-history-specific gates
- design admits actor update or PPO before source-positive evidence
- design changes actor input contract
- design ignores model fidelity limits

## Evidence Gates

- design prioritizes wrong-history evidence over reset-only evidence
- design specifies cross-fault pairing matrix
- design defines severity contrast ladder
- design keeps hidden fault labels out of actor input
- design blocks actor update PPO and promotion
- design defines no-training implementation artifacts

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor
- do not run PPO
- do not promote a checkpoint
- do not add fault labels to actor observations
- do not treat reset-only rows as source-positive
- do not relax wrong-history gates after seeing results
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m706-cross-fault-wrong-history-scenario-design
- type: infrastructure
- checkpoint: docs/m706-cross-fault-wrong-history-scenario-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: cross_fault_wrong_history_scenario_design_admit_m707
- reason: M706 designs a cross-fault pairing matrix severity contrast ladder wrong-history-specific gates and no-training M707 artifacts while blocking source export PPO and promotion

## Next Blocker

m707-cross-fault-wrong-history-scenario-implementation
