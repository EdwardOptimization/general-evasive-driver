# m617-expanded-sequence-target-miner Research Review

## Summary

- Generated at UTC: 20260524T094632Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: expanded_sequence_target_miner_diagnostic_positive_admit_audit
- Decision reason: M617 repeats sequence mining on 30 expanded source rows and selects 6 accepted sequences with mean margin improvement 0.056784 but accepted diversity remains below optimizer-admission target

## Hypothesis

Repeating the bounded K=3/5 sequence target miner on the M616 expanded source table will test whether the M613 sequence signal is repeatable across a broader source set.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv, docs/m616-expanded-sequence-source-miner-implementation.md
- parent_config: experiments/manifests/m616-expanded-sequence-source-miner-implementation.json, docs/m615-sequence-source-expansion-design.md
- parent_objective: repeat diagnostic sequence target mining on expanded source rows
- derived_from: m616-expanded-sequence-source-miner-implementation
- blocked_by: m616-expanded-sequence-source-miner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- sequence candidates are evaluated on 30 expanded source rows
- summary records diagnostic_only true actor_parameters_changed false ppo_used false promoted false optimizer_admission false
- accepted and unaccepted rows are written
- accepted sequence diversity is reported
- research validation and focused tests pass

## Failure Criteria

- miner trains any model
- miner runs PPO
- miner promotes a checkpoint
- miner lowers the 0.02 margin or 0.05 risk thresholds
- miner omits unaccepted rows
- miner treats diagnostic accepted sequences as optimizer-ready without a later audit

## Evidence Gates

- write sequence_candidates.csv
- write accepted_sequences.csv
- write unaccepted_rows.csv
- write summary with diagnostic_only true
- keep M613 target acceptance thresholds unchanged
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not lower margin or risk target acceptance thresholds
- do not add privileged actor inputs
- do not hide unaccepted rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m617-expanded-sequence-target-miner
- type: infrastructure
- checkpoint: runs/m617_expanded_sequence_target_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: expanded_sequence_target_miner_diagnostic_positive_admit_audit
- reason: M617 repeats sequence mining on 30 expanded source rows and selects 6 accepted sequences with mean margin improvement 0.056784 but accepted diversity remains below optimizer-admission target

## Next Blocker

m618-expanded-sequence-target-mining-audit
