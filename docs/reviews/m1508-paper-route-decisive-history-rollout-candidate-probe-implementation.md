# m1508-paper-route-decisive-history-rollout-candidate-probe-implementation Research Review

## Summary

- Generated at UTC: 20260529T084807Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: decisive_history_rollout_candidate_scaffold_implemented_admit_branch_synthesis
- Decision reason: M1508 implements rollout candidate scaffolding with 5 focused tests and synthetic smoke materialized 2 measured candidates while rejecting reset-only evidence

## Hypothesis

The M1507 rollout candidate design can be implemented as no-training schemas, distance helpers, and materialization guards with focused tests.

## Lineage

- parent_checkpoint: not_applicable_infrastructure_task
- parent_dataset: docs/m1507-paper-route-decisive-history-rollout-candidate-design.md, src/autodrift/decisive_history_env_runtime_smoke.py
- parent_config: experiments/manifests/m1507-paper-route-decisive-history-rollout-candidate-design.json
- parent_objective: implement no-training rollout candidate probe scaffolding for T4/T5 decisive-history evidence
- derived_from: m1507-paper-route-decisive-history-rollout-candidate-design
- blocked_by: rollout candidate-generation design must become schema/test-covered implementation before public probe
- supersedes: training corpus export before measured rollout candidate schemas
- invalidates: None

## Success Criteria

- rollout candidate probe implementation code exists
- focused tests pass
- candidate materialization guard prevents reset-only evidence from becoming candidates
- matching helpers avoid forbidden actor inputs
- next public probe smoke or bounded-runner route is explicit

## Failure Criteria

- implementation code is missing
- focused tests fail
- materialization guards are missing
- implementation starts training, PPO, promotion, private holdout, or corpus export

## Evidence Gates

- M1508 must implement rollout candidate schemas and measured-distance helpers
- M1508 must keep reset-only evidence separate from materialized candidates
- M1508 must include focused tests
- M1508 must block training, PPO, promotion, private holdout, actor-input changes, and corpus export
- M1508 must route to a public probe smoke or a bounded runner design

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not materialize candidates from reset-only evidence
- do not claim self-identification from scaffolding

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1508-paper-route-decisive-history-rollout-candidate-probe-implementation
- type: infrastructure
- checkpoint: runs/m1508_decisive_history_rollout_candidate_scaffold_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_rollout_candidate_scaffold_implemented_admit_branch_synthesis
- reason: M1508 implements rollout candidate scaffolding with 5 focused tests and synthetic smoke materialized 2 measured candidates while rejecting reset-only evidence

## Next Blocker

m1509-paper-route-decisive-history-task-matrix-synthesis
