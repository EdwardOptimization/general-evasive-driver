# m691-gate-margin-closed-loop-replay-design Research Review

## Summary

- Generated at UTC: 20260524T161810Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: gate_margin_closed_loop_replay_design_admit_m692
- Decision reason: M691 designs a no-training replay admission gate comparing base and M689 residual-corrected first actions with normal retention and wrong-history or boundary-risk utility checks before any actor update PPO or promotion

## Hypothesis

A closed-loop replay admission design can test whether M689's exact residual-head output separation has trajectory-level utility without changing the base actor or admitting PPO.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m689_gate_margin_response_amplification/summary.json, runs/m689_gate_margin_response_amplification/alpha_summary.csv, runs/m689_gate_margin_response_amplification/seed_view_summary.csv, docs/m690-gate-margin-response-amplification-audit.md
- parent_config: experiments/manifests/m690-gate-margin-response-amplification-audit.json
- parent_objective: design closed-loop replay admission for M689 residual heads
- derived_from: m690-gate-margin-response-amplification-audit
- blocked_by: m690-gate-margin-response-amplification-audit
- supersedes: None
- invalidates: None

## Success Criteria

- closed-loop replay variants are specified
- normal-history retention gates are specified
- wrong-history or boundary-risk utility gates are specified
- source-heldout or source-diverse evaluation is specified
- implementation milestone is pre-registered
- PPO, actor update, and promotion remain blocked

## Failure Criteria

- design treats M689 exact output gates as closed-loop evidence
- design admits PPO or actor update
- design omits normal-history retention gates
- design omits wrong-history or boundary-risk utility gates
- design changes actor observation inputs

## Evidence Gates

- design stays no-training and no-PPO
- design compares base actor and M689 residual-corrected action
- design includes normal-history retention gates
- design includes wrong-history or boundary-risk utility gates
- design uses source-heldout or source-diverse rows
- design blocks promotion and actor update until replay gates pass
- actor input contract remains P0 human-view no-wheel

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run training in this design milestone
- do not promote M689 residual heads as driver checkpoints
- do not admit PPO
- do not change actor observation inputs
- do not use oracle labels or hidden physical parameters as actor inputs
- do not treat exact output gates as closed-loop evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m691-gate-margin-closed-loop-replay-design
- type: infrastructure
- checkpoint: docs/m691-gate-margin-closed-loop-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: gate_margin_closed_loop_replay_design_admit_m692
- reason: M691 designs a no-training replay admission gate comparing base and M689 residual-corrected first actions with normal retention and wrong-history or boundary-risk utility checks before any actor update PPO or promotion

## Next Blocker

m692-gate-margin-closed-loop-replay-implementation
