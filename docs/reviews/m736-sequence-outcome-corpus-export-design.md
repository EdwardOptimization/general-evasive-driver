# m736-sequence-outcome-corpus-export-design Research Review

## Summary

- Generated at UTC: 20260524T220504Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: sequence_outcome_corpus_export_design_admit_m737
- Decision reason: M736 designs deterministic non-sentinel sequence-outcome corpus export with matched normal rows hard negatives diversity gates and future extreme-fault coverage constraints

## Hypothesis

M734's non-sentinel sequence-outcome rows can be exported as a compact diverse corpus for later objective design.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m735-sequence-level-command-response-intervention-audit.md, docs/m734-sequence-level-command-response-intervention-implementation.md, runs/m734_sequence_command_response_intervention/summary.json, runs/m734_sequence_command_response_intervention/intervention_rollouts.csv, runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv, runs/m734_sequence_command_response_intervention/sentinel_rows.csv
- parent_config: experiments/manifests/m735-sequence-level-command-response-intervention-audit.json
- parent_objective: design sentinel-filtered sequence-outcome corpus export after M734 positive diagnostic
- derived_from: m735-sequence-level-command-response-intervention-audit
- blocked_by: m735-sequence-level-command-response-intervention-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M736 defines positive and contrast row selection
- M736 defines diversity and sentinel gates
- M736 defines export artifacts and command
- M736 blocks objective training PPO and promotion
- M736 admits only a no-training M737 implementation

## Failure Criteria

- design exports sentinel rows as positives
- design treats action-only rows as outcome positives
- design admits PPO or checkpoint promotion
- design changes actor input contract

## Evidence Gates

- M736 filters sentinel rows from M734 outcome positives
- M736 defines positive normal and rejected sequence contrast rows
- M736 defines corpus diversity gates
- M736 blocks objective training PPO and promotion
- actor input contract remains unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export sentinel rows as positives
- do not export action-only rows as outcome positives
- do not train an actor
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m736-sequence-outcome-corpus-export-design
- type: infrastructure
- checkpoint: docs/m736-sequence-outcome-corpus-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_outcome_corpus_export_design_admit_m737
- reason: M736 designs deterministic non-sentinel sequence-outcome corpus export with matched normal rows hard negatives diversity gates and future extreme-fault coverage constraints

## Next Blocker

m737-sequence-outcome-corpus-export-implementation
