# m1499-paper-route-decisive-history-task-matrix-design Research Review

## Summary

- Generated at UTC: 20260529T075458Z
- Type: gate
- Gate tier: process
- Promotion decision: decisive_history_task_matrix_design_admit_task_harness_implementation
- Decision reason: M1499 designs T4/T5 decisive history task matrix and routes to no-training harness implementation before candidate generation or training

## Hypothesis

After the standard profile stop rule, the correct next paper route is to design decisive T4/T5 tasks that make older action-response history necessary under fair controls.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1498-paper-route-go-no-go-three-seed-result-audit.md, runs/m1497_go_no_go_profile_three_seed_public_pilot/profile_aggregate.csv, docs/m1492-paper-route-self-id-go-no-go-matrix-design.md
- parent_config: experiments/manifests/m1498-paper-route-go-no-go-three-seed-result-audit.json
- parent_objective: design decisive T4/T5 history-necessity task matrix after standard profile scaling stop rule
- derived_from: m1498-paper-route-go-no-go-three-seed-result-audit
- blocked_by: standard public profile distribution does not support finite-window history necessity or online-GRU hidden advantage
- supersedes: another standard fixed-budget profile pilot without decisive history tasks, immediate L3 recipe repair before proving the task needs older history
- invalidates: None

## Success Criteria

- docs/m1499-paper-route-decisive-history-task-matrix-design.md exists
- design defines T4 same-current same-recent-window different-older-history task family
- design defines T5 terminal-boundary near-constraint task family
- design defines required controls and shared budgets
- design pre-registers success and falsification criteria
- design blocks training PPO replay promotion private holdout corpus export and actor-input changes

## Failure Criteria

- design document is missing
- T4/T5 tasks do not isolate older-history necessity
- controls or budgets are omitted
- design uses private holdout for tuning
- design starts training replay PPO promotion corpus export or actor-input change

## Evidence Gates

- M1499 must design T4 same-current same-recent-window different-older-history tasks
- M1499 must design T5 terminal-boundary near-constraint tasks
- M1499 must define L0/L1/L2/L2-current-tiled/L3/reset controls under shared budgets
- M1499 must block training, PPO, replay, private holdout, promotion, corpus export, and actor-input changes

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
- do not claim level3 self-identification from design alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1499-paper-route-decisive-history-task-matrix-design
- type: gate
- checkpoint: docs/m1499-paper-route-decisive-history-task-matrix-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_task_matrix_design_admit_task_harness_implementation
- reason: M1499 designs T4/T5 decisive history task matrix and routes to no-training harness implementation before candidate generation or training

## Next Blocker

m1500-paper-route-decisive-history-task-harness-implementation
