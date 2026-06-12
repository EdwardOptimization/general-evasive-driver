# m3235-c1-tail-family-interface-smoke Research Review

## Summary

- Generated at UTC: 20260612T070255Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: tail_family_interface_smoke_passed
- Decision reason: Completed: no-PPO structured tail-family interface smoke passed all gates; 11/11 frozen demo replays succeeded, held-out family train coverage was 1.0, tail reconstruction was exact, and interface_targets.npz was written without a policy checkpoint. C1 remains open for pretrain design; C2/C3 remain blocked.

## Hypothesis

A no-PPO C1 structured tail-family interface quick smoke can replay the frozen v2 structured-oracle quick rows, encode prefix/tail interface targets, and pass family-coverage plus exact tail-reconstruction gates before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: experiments/feasibility_audit/c5prime_c1_admission_interface_pricing.json, experiments/feasibility_audit/c5prime_c1_oracle_bc_v2_prereg.json
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv
- parent_config: experiments/feasibility_audit/c5prime_c1_tail_family_interface_smoke_prereg.json, scripts/feasibility_audit/c5prime_c1_tail_family_interface_smoke.py
- parent_objective: smoke the positive M3234 tail-family admission interface before any pretraining
- derived_from: M3234 positive admission-interface pricing, M3232 v2 rare-tail preregistration, M3229 tail-action failure localization
- blocked_by: C1 remains open; C2 is blocked until a C1 admission artifact passes
- supersedes: unexecuted tail-family interface smoke proposal after M3234
- invalidates: starting tail-family pretraining without an interface smoke, using a process-only pricing artifact as C2 admission

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_tail_family_interface_smoke.json exists with protocol c5prime_c1_tail_family_interface_smoke
- runs/feasibility_audit/c5prime_c1_tail_family_interface_smoke/quick/interface_targets.npz exists
- gates.all_passed is true
- the decision keeps C2 blocked
- the result document separates measured and inferred sections

## Failure Criteria

- M3235 runs PPO or behavior pretraining
- M3235 writes a policy checkpoint
- M3235 admits C2 or full C1 training
- M3235 changes the structured action decoder to pass the smoke

## Evidence Gates

- M3235 must be preregistered before execution
- M3235 must use the M3232 v2 frozen row design
- M3235 must not run PPO or behavior pretraining
- M3235 must not write a policy checkpoint
- M3235 must pass family-coverage and exact tail-reconstruction gates
- M3235 must keep C2 blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo or behavior pretraining
- do not write a policy checkpoint
- do not admit C2 or full C1 training
- do not claim driver performance, validation ranking, promotion, high-fidelity sufficiency, or self-ID

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3235-c1-tail-family-interface-smoke
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_tail_family_interface_smoke.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: tail_family_interface_smoke_passed
- reason: Completed: no-PPO structured tail-family interface smoke passed all gates; 11/11 frozen demo replays succeeded, held-out family train coverage was 1.0, tail reconstruction was exact, and interface_targets.npz was written without a policy checkpoint. C1 remains open for pretrain design; C2/C3 remain blocked.

## Next Blocker

C1 remains open; if M3235 passes, the next C1 unit is a tail-family interface pretrain design/quick milestone. C2 remains blocked.
