# m989-v4-public-base-capability-step-fault-design Research Review

## Summary

- Generated at UTC: 20260526T130536Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: capability_step_fault_design_admit_smoke
- Decision reason: M989 reuses the existing fault-event corpus harness for M974 current-base smoke and keeps per-wheel faults future-only under the P0 actor contract

## Hypothesis

Explicit hidden capability-step events will create stronger online self-identification pressure than static episode-level randomization while preserving the P0 actor-input contract.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m988-v4-public-base-extreme-scenario-family-synthesis.md
- parent_config: experiments/manifests/m988-v4-public-base-extreme-scenario-family-synthesis.json
- parent_objective: design hidden capability-step/fault events after config-only global randomization failed to expose source-diverse proof rows
- derived_from: m988-v4-public-base-extreme-scenario-family-synthesis
- blocked_by: M988 pivots from config-only mining to capability-step/fault event design
- supersedes: None
- invalidates: claiming split-mu or per-wheel fault support before dynamics support exists

## Success Criteria

- design artifact exists
- supported global single-track capability steps are specified
- unsupported asymmetric/per-wheel faults are separated
- actor input contract preservation is explicit
- implementation and test route is explicit
- no PPO or promotion occurs

## Failure Criteria

- design artifact is missing
- hidden parameters would enter actor observation
- unsupported per-wheel faults are claimed as implemented
- training or PPO starts
- route decision is missing

## Evidence Gates

- M989 must not run PPO
- M989 must not promote
- M989 must preserve P0 actor-input contract
- M989 must keep hidden capability changes simulator-only/logging-only
- M989 must distinguish global single-track faults from future asymmetric/per-wheel faults

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden parameters to actor inputs
- do not train or optimize
- do not use private holdout
- do not claim split-mu or individual-wheel failure support without changing dynamics
- do not promote any checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m989-v4-public-base-capability-step-fault-design
- type: infrastructure
- checkpoint: docs/m989-v4-public-base-capability-step-fault-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_step_fault_design_admit_smoke
- reason: M989 reuses the existing fault-event corpus harness for M974 current-base smoke and keeps per-wheel faults future-only under the P0 actor contract

## Next Blocker

m990-v4-public-base-capability-step-fault-smoke
