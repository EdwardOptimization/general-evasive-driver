# m534-matched-history-natural-surface-eval-design Research Review

## Summary

- Generated at UTC: 20260524T030620Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m535_frozen_source_surface_eval_implementation
- Decision reason: M534 designs frozen M399 source-surface evaluation so trained L0 L2 and L3 can be compared on matched natural states without projected-surface leakage

## Hypothesis

A natural-surface evaluation can be designed for the matched short-train checkpoints so the project measures whether trained L2/L3 policies preserve the M524/M526 history-value event advantage rather than only improving smoke returns.

## Lineage

- parent_checkpoint: runs/m532_matched_l0_short_train_seed3530/checkpoint.pt, runs/m532_matched_l2_short_train_seed3530/checkpoint.pt, runs/m532_matched_l3_short_train_seed3530/checkpoint.pt, runs/m533_matched_l0_short_train_seed3531/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt, runs/m533_matched_l0_short_train_seed3532/checkpoint.pt, runs/m533_matched_l2_short_train_seed3532/checkpoint.pt, runs/m533_matched_l3_short_train_seed3532/checkpoint.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json, runs/m524_natural_history_value_ablation/summary.json
- parent_config: configs/ppo_m531_matched_l0_short_train.json, configs/ppo_m531_matched_l2_short_train.json, configs/ppo_m531_matched_l3_short_train.json
- parent_objective: matched baseline natural history-value surface evaluation
- derived_from: m533-matched-short-train-repeat-seeds, m526-history-value-event-audit
- blocked_by: m533-matched-short-train-repeat-seeds
- supersedes: None
- invalidates: None

## Success Criteria

- define which natural surfaces and metrics to evaluate
- define how to map trained L0/L2/L3 checkpoints into the evaluation harness
- define public diagnostic versus future holdout usage
- select the next executable natural-surface eval milestone

## Failure Criteria

- design uses projected rows as natural evidence
- design tunes checkpoint selection from diagnostic rows before declaring evidence
- design omits metadata checks
- checkpoint promotion is performed

## Evidence Gates

- designed natural history-value surface eval for trained L0/L2/L3 checkpoints
- kept M526 natural event rows as public diagnostic surfaces
- preserved projected-vs-natural provenance
- no checkpoint promoted from route metrics alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune checkpoint choice on the same natural diagnostic rows and call it unbiased
- do not mix projected and natural rows in one claim
- do not promote checkpoint
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m534-matched-history-natural-surface-eval-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m535_frozen_source_surface_eval_implementation
- reason: M534 designs frozen M399 source-surface evaluation so trained L0 L2 and L3 can be compared on matched natural states without projected-surface leakage

## Next Blocker

m535-frozen-source-surface-eval-implementation
