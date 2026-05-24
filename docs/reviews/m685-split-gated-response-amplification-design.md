# m685-split-gated-response-amplification-design Research Review

## Summary

- Generated at UTC: 20260524T153607Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: split_gated_response_amplification_design_admit_m686
- Decision reason: M685 designs a gated residual head that separates activation from residual content while preserving exact gates no-PPO discipline and P0 actor inputs

## Hypothesis

A split/gated residual head can keep normal-history residuals inactive while allowing wrong-history response amplification, avoiding the scalar-loss tradeoff observed in M680 and M683.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m683_normal_sequence_safe_response_amplification/summary.json, runs/m683_normal_sequence_safe_response_amplification/alpha_summary.csv, docs/m684-normal-sequence-safe-response-amplification-audit.md
- parent_config: experiments/manifests/m684-normal-sequence-safe-response-amplification-audit.json
- parent_objective: design split/gated response-amplification residual head
- derived_from: m684-normal-sequence-safe-response-amplification-audit
- blocked_by: m684-normal-sequence-safe-response-amplification-audit
- supersedes: None
- invalidates: None

## Success Criteria

- split/gated residual architecture is specified
- normal gate and residual safety losses are specified
- wrong-history activation and gap losses are specified
- implementation milestone is pre-registered
- PPO and promotion remain blocked

## Failure Criteria

- design only retunes M683 scalar coefficients
- design weakens normal retention gates
- design changes actor observation inputs
- design admits PPO or promotion

## Evidence Gates

- design keeps frozen BC5660 actor and P0 input contract
- design separates activation gate from residual amplifier
- design retains normal sequence and first-step safety gates
- design retains detached-normal wrong-history gap pressure
- design keeps alpha ladder exact metrics
- PPO and promotion remain blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run training in this design milestone
- do not weaken exact normal retention gates
- do not run PPO
- do not promote a checkpoint
- do not change actor observation inputs
- do not use hidden physical parameters or labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m685-split-gated-response-amplification-design
- type: infrastructure
- checkpoint: docs/m685-split-gated-response-amplification-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: split_gated_response_amplification_design_admit_m686
- reason: M685 designs a gated residual head that separates activation from residual content while preserving exact gates no-PPO discipline and P0 actor inputs

## Next Blocker

m686-split-gated-response-amplification-implementation
