# m1507-paper-route-decisive-history-rollout-candidate-design Research Review

## Summary

- Generated at UTC: 20260529T084110Z
- Type: gate
- Gate tier: process
- Promotion decision: decisive_history_rollout_candidate_design_admit_probe_implementation
- Decision reason: M1507 designs measured rollout candidate generation with source traces matching metrics interventions and materialization guardrails before implementation or corpus export

## Hypothesis

The M1506 reset-viable hook specs can be extended into a no-training rollout candidate-generation design that measures T4/T5 history necessity without actor-input leakage.

## Lineage

- parent_checkpoint: not_applicable_process_task
- parent_dataset: docs/m1506-paper-route-decisive-history-env-hook-runtime-smoke.md, runs/m1506_decisive_history_env_hook_runtime_smoke/summary.json
- parent_config: experiments/manifests/m1506-paper-route-decisive-history-env-hook-runtime-smoke.json
- parent_objective: design no-training rollout candidate generation after env-hook reset viability
- derived_from: m1506-paper-route-decisive-history-env-hook-runtime-smoke
- blocked_by: env-hook specs reset successfully, but measured rollout candidate generation is not yet designed
- supersedes: direct corpus export or training after reset-only runtime smoke
- invalidates: None

## Success Criteria

- docs/m1507-paper-route-decisive-history-rollout-candidate-design.md exists
- design names source history collection, matching metrics, terminal-margin measurement, and interventions
- design defines when candidates may be materialized
- design blocks training, PPO, promotion, private holdout, and corpus export
- design routes to implementation or records a blocker

## Failure Criteria

- design document is missing
- design leaves rollout candidate materialization ambiguous
- design relies on reset-only evidence as self-ID evidence
- design starts training, PPO, promotion, private holdout, or corpus export

## Evidence Gates

- M1507 must design no-training rollout candidate generation for T4/T5 hooks
- M1507 must define source history collection, matching distances, terminal-margin measurement, and intervention variants
- M1507 must preserve public/private holdout separation and actor-input contract
- M1507 must block training, PPO, promotion, private holdout, and corpus export
- M1507 must route to implementation or record a simulator-scope blocker

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not claim self-identification from reset-only evidence
- do not materialize candidates without measured rollout margins and interventions

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1507-paper-route-decisive-history-rollout-candidate-design
- type: gate
- checkpoint: docs/m1507-paper-route-decisive-history-rollout-candidate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_rollout_candidate_design_admit_probe_implementation
- reason: M1507 designs measured rollout candidate generation with source traces matching metrics interventions and materialization guardrails before implementation or corpus export

## Next Blocker

m1508-paper-route-decisive-history-rollout-candidate-probe-implementation
