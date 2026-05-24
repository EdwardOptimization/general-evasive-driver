# m673-response-amplification-actor-coupling-design Research Review

## Summary

- Generated at UTC: 20260524T145848Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: response_amplification_actor_coupling_design_admit_m674
- Decision reason: M673 designs a frozen-backbone residual sequence-head actor-coupling probe with fused-plus-next-hidden features alpha ladder exact source-heldout metrics and no PPO promotion or actor-input changes

## Hypothesis

A conservative no-PPO actor-coupling probe can be designed from M671 shadow evidence by using the same human-view actor inputs, exact normal-retention gates, bounded wrong-history sequence targets, and interpolation before replay.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m671_response_amplification_shadow/shadow_corpus.npz, runs/m671_response_amplification_shadow/shadow_metadata.csv, runs/m671_response_amplification_shadow/summary.json, docs/m672-response-amplification-shadow-audit.md
- parent_config: experiments/manifests/m672-response-amplification-shadow-audit.json
- parent_objective: design conservative actor-coupling probe from positive shadow evidence
- derived_from: m672-response-amplification-shadow-audit
- blocked_by: m672-response-amplification-shadow-audit
- supersedes: None
- invalidates: None

## Success Criteria

- actor-coupling objective is specified
- exact metrics and pass/fail thresholds are specified
- trust-region and interpolation rules are specified
- implementation milestone is pre-registered
- PPO and promotion remain blocked

## Failure Criteria

- design changes actor input contract
- design admits PPO before exact actor-coupling probe
- design lacks normal-retention gates
- design treats M671 shadow result as closed-loop proof

## Evidence Gates

- design uses M671 shadow corpus and metrics
- no PPO in first actor-coupling probe
- normal-retention constraints are first-class
- wrong-history sequence amplification is bounded
- exact objective gate precedes replay gates
- promotion remains forbidden

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run training in this design milestone
- do not run PPO
- do not promote a checkpoint
- do not change actor observation inputs
- do not use privileged hidden parameters or labels as actor inputs
- do not skip exact source-heldout metrics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m673-response-amplification-actor-coupling-design
- type: infrastructure
- checkpoint: docs/m673-response-amplification-actor-coupling-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: response_amplification_actor_coupling_design_admit_m674
- reason: M673 designs a frozen-backbone residual sequence-head actor-coupling probe with fused-plus-next-hidden features alpha ladder exact source-heldout metrics and no PPO promotion or actor-input changes

## Next Blocker

m674-response-amplification-actor-coupling-implementation
