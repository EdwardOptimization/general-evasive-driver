# m686-split-gated-response-amplification-implementation Research Review

## Summary

- Generated at UTC: 20260524T154343Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: split_gated_response_amplification_exact_gate_failed_admit_audit
- Decision reason: M686 strongly improves normal retention but exact gate fails because normal and wrong gates collapse near 0.10 and wrong gap stays below threshold

## Hypothesis

A split/gated residual head can separate normal-history inactivity from wrong-history amplification and pass exact source-heldout response-amplification gates without changing the base actor.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m671_response_amplification_shadow/shadow_corpus.npz, runs/m671_response_amplification_shadow/shadow_metadata.csv, docs/m685-split-gated-response-amplification-design.md
- parent_config: experiments/manifests/m685-split-gated-response-amplification-design.json
- parent_objective: implement split/gated response-amplification residual head
- derived_from: m685-split-gated-response-amplification-design
- blocked_by: m685-split-gated-response-amplification-design
- supersedes: None
- invalidates: None

## Success Criteria

- gated residual-head artifacts are written
- at least one seed passes exact metrics at alpha > 0
- normal_delta_l2_mean <= 0.0025 at selected alpha
- normal_action_drift_first_l2_p95 <= 0.006 at selected alpha
- source-heldout sequence gap mean >= 0.010 at selected alpha
- gate diagnostics are reported
- actor checksum unchanged
- no base actor checkpoint written
- no PPO used
- research validation passes

## Failure Criteria

- normal and wrong gates both close and suppress gap
- normal gate leaks and normal retention fails
- bounded amplifier cannot produce enough wrong-history gap
- source-heldout feature overlap prevents gate separation
- actor checksum changes
- base actor checkpoint is written

## Evidence Gates

- gated residual head is active
- normal gate and wrong gate diagnostics are reported
- normal sequence and first-step safety losses remain active
- branch-specific detached-normal gap losses remain active
- alpha ladder exact metrics are reported
- base actor checksum is unchanged
- no base actor checkpoint is written
- no PPO is used
- no checkpoint is promoted

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not mutate base actor parameters
- do not run PPO
- do not promote a checkpoint
- do not change actor observation inputs
- do not weaken normal sequence retention gates
- do not skip exact source-heldout metrics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m686-split-gated-response-amplification-implementation
- type: infrastructure
- checkpoint: runs/m686_split_gated_response_amplification/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: split_gated_response_amplification_exact_gate_failed_admit_audit
- reason: M686 strongly improves normal retention but exact gate fails because normal and wrong gates collapse near 0.10 and wrong gap stays below threshold

## Next Blocker

m687-split-gated-response-amplification-audit
