# m679-branch-specific-response-amplification-design Research Review

## Summary

- Generated at UTC: 20260524T151623Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: branch_specific_response_amplification_design_admit_m680
- Decision reason: M679 designs detached-normal branch-specific wrong-history gap losses plus hard low-gap row pressure while preserving first-step safety gates and blocking PPO promotion and input changes

## Hypothesis

Branch-specific wrong-history pressure with detached-normal gap losses can preserve M677's first-step normal safety while restoring wrong-history sequence separation.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m677_first_step_safe_response_amplification/summary.json, runs/m677_first_step_safe_response_amplification/alpha_summary.csv, docs/m678-first-step-safe-response-amplification-audit.md
- parent_config: experiments/manifests/m678-first-step-safe-response-amplification-audit.json
- parent_objective: design branch-specific response-amplification objective
- derived_from: m678-first-step-safe-response-amplification-audit
- blocked_by: m678-first-step-safe-response-amplification-audit
- supersedes: None
- invalidates: None

## Success Criteria

- branch-specific losses are specified
- detached-normal gap pressure is specified
- hard wrong-gap row weighting is specified or explicitly rejected
- implementation milestone is pre-registered
- PPO and promotion remain blocked

## Failure Criteria

- design only reruns M677 with coefficient changes
- design weakens normal first-action drift gate
- design admits PPO or promotion
- design changes actor observation inputs

## Evidence Gates

- design preserves normal first-step safety constraints
- design adds branch-specific wrong-history pressure
- design uses detached-normal gap losses or equivalent
- design keeps frozen backbone and P0 actor inputs
- PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run training in this design milestone
- do not weaken normal first-action drift gate
- do not run PPO
- do not promote a checkpoint
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m679-branch-specific-response-amplification-design
- type: infrastructure
- checkpoint: docs/m679-branch-specific-response-amplification-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: branch_specific_response_amplification_design_admit_m680
- reason: M679 designs detached-normal branch-specific wrong-history gap losses plus hard low-gap row pressure while preserving first-step safety gates and blocking PPO promotion and input changes

## Next Blocker

m680-branch-specific-response-amplification-implementation
