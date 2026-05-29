# m1501-paper-route-decisive-history-candidate-generation-design Research Review

## Summary

- Generated at UTC: 20260529T081050Z
- Type: gate
- Gate tier: process
- Promotion decision: decisive_history_candidate_generation_design_admit_planner_implementation
- Decision reason: M1501 designs no-training T4/T5 candidate generation with public source families matching tolerances diversity gates and no actor-input or training shortcuts

## Hypothesis

The decisive-history harness can be connected to a public no-training current-sim candidate-generation route with explicit matching and diversity gates.

## Lineage

- parent_checkpoint: not_applicable_process_task
- parent_dataset: docs/m1500-paper-route-decisive-history-task-harness-implementation.md, runs/m1500_decisive_history_task_harness_smoke/summary.json
- parent_config: experiments/manifests/m1500-paper-route-decisive-history-task-harness-implementation.json
- parent_objective: design public no-training candidate generation using the T4/T5 decisive-history harness
- derived_from: m1500-paper-route-decisive-history-task-harness-implementation
- blocked_by: the metadata harness exists, but current-sim candidate generation and matching sources are not yet designed
- supersedes: direct candidate-generation smoke without source/matching design, training or replay before candidate generation is source-diverse and control-clean
- invalidates: None

## Success Criteria

- docs/m1501-paper-route-decisive-history-candidate-generation-design.md exists
- design names T4/T5 source families and public seed policy
- design names current/recent matching tolerances
- design names source-diversity gates
- design blocks training PPO replay promotion private holdout corpus export and actor-input changes

## Failure Criteria

- design document is missing
- source families or matching tolerances are omitted
- diversity gates are omitted
- design starts candidate generation replay PPO training promotion corpus export or actor-input change

## Evidence Gates

- M1501 must design no-training T4/T5 current-sim candidate generation
- M1501 must name public seeds, source families, matching tolerances, and diversity gates
- M1501 must preserve the actor input contract
- M1501 must block training replay PPO promotion private holdout and corpus export

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not run candidate generation before the design is explicit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1501-paper-route-decisive-history-candidate-generation-design
- type: gate
- checkpoint: docs/m1501-paper-route-decisive-history-candidate-generation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_candidate_generation_design_admit_planner_implementation
- reason: M1501 designs no-training T4/T5 candidate generation with public source families matching tolerances diversity gates and no actor-input or training shortcuts

## Next Blocker

m1502-paper-route-decisive-history-candidate-planner-implementation
