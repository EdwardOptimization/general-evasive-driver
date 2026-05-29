# m1504-paper-route-decisive-history-env-hook-design Research Review

## Summary

- Generated at UTC: 20260529T082550Z
- Type: gate
- Gate tier: process
- Promotion decision: decisive_history_env_hook_design_admit_env_hook_implementation
- Decision reason: M1504 designs no-training current-sim hook/spec layer for all six T4/T5 source families and keeps rollout replay training promotion blocked

## Hypothesis

The M1503 metadata planner pass can be translated into a concrete no-training current-sim env-hook design for T4/T5 candidate-generation probes.

## Lineage

- parent_checkpoint: not_applicable_process_task
- parent_dataset: docs/m1503-paper-route-decisive-history-public-planner-smoke.md, runs/m1503_decisive_history_public_planner_smoke/summary.json
- parent_config: experiments/manifests/m1503-paper-route-decisive-history-public-planner-smoke.json
- parent_objective: design no-training current-sim env hooks for T4/T5 decisive-history candidate generation
- derived_from: m1503-paper-route-decisive-history-public-planner-smoke
- blocked_by: metadata planner scale passed, but simulator hook scope must be designed before any rollout probe
- supersedes: direct simulator replay or training after metadata planner smoke
- invalidates: None

## Success Criteria

- docs/m1504-paper-route-decisive-history-env-hook-design.md exists
- design names env-hook API, scenario config, logging, matching outputs, and guardrails
- design covers all six M1501 source families or explicitly scopes a minimal first implementation
- design routes to implementation or records a simulator-scope blocker
- no simulator replay, training, PPO, promotion, corpus export, private holdout, or actor-input change occurs

## Failure Criteria

- design document is missing
- design leaves env-hook API or artifacts ambiguous
- design depends on forbidden actor inputs or oracle labels entering actor observations
- design starts simulator replay, PPO, training, promotion, corpus export, or private holdout

## Evidence Gates

- M1504 must design no-training current-sim hooks for T4/T5 planner source families
- M1504 must name simulator state, scenario config, logging, and matching outputs needed by M1500 rows
- M1504 must separate env-hook implementation from replay, training, PPO, promotion, private holdout, actor-input changes, and corpus export
- M1504 must route to an implementation milestone or record a simulator-scope blocker

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run simulator replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not claim simulator candidate existence before env-hook implementation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1504-paper-route-decisive-history-env-hook-design
- type: gate
- checkpoint: docs/m1504-paper-route-decisive-history-env-hook-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_env_hook_design_admit_env_hook_implementation
- reason: M1504 designs no-training current-sim hook/spec layer for all six T4/T5 source families and keeps rollout replay training promotion blocked

## Next Blocker

m1505-paper-route-decisive-history-env-hook-implementation
