# m3238-c1-family-selector-repricing Research Review

## Summary

- Generated at UTC: 20260612T074539Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: family_selector_repricing_negative
- Decision reason: Completed: no deterministic train-only selector cleared all M3238 gates. Best row-level selector accuracy was 0.803119 over the 0.538012 majority floor, but predicted-family reconstruction MSE was 0.268415 and structured:coast_steer_-0.7 stayed 0/101, predicted as structured:brake_steer_-1.0. Local selector/interface training is rejected pending PI or new nonlocal-interface pricing; C2/C3 remain blocked.

## Hypothesis

A preregistered read-only C1 family-selector separability repricing pass can decide whether the current local structured-family selector route is worth another training milestone after M3237, before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3237-c1-tail-family-interface-synthesis-repricing.md
- parent_dataset: experiments/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick.json, runs/feasibility_audit/c5prime_c1_tail_family_interface_pretrain_quick/quick/interface_pretrain_dataset.npz
- parent_config: experiments/feasibility_audit/c5prime_c1_family_selector_repricing_prereg.json, scripts/feasibility_audit/c5prime_c1_family_selector_repricing.py
- parent_objective: price whether the local family-selector route is learnable enough to justify training
- derived_from: M3234 positive admission-interface pricing, M3235 exact structured tail-family representation, M3236 rare-family selector failure, M3237 pivot to read-only family-selector/separability repricing
- blocked_by: C2 remains blocked until a C1 admission artifact passes
- supersedes: direct continuation of local tail-family selector/interface training after M3237
- invalidates: training another local selector without rare-family separability pricing, opening controlled rollout design from aggregate selector accuracy

## Success Criteria

- experiments/feasibility_audit/c5prime_c1_family_selector_repricing.json exists with protocol c5prime_c1_family_selector_repricing
- result reports train-only selector battery metrics and required rare-family gates
- decision admits selector training only if at least one selector clears all gates
- decision keeps C2 blocked
- the result document separates measured and inferred sections

## Failure Criteria

- M3238 runs rollout or training
- M3238 writes a checkpoint or dataset
- M3238 admits local selector/interface training without rare-family and reconstruction gates
- M3238 admits C2
- M3238 claims driver performance

## Evidence Gates

- M3238 must be read-only over the M3236 dataset and M3237 synthesis
- M3238 must not run rollout or training
- M3238 must not write a checkpoint or dataset
- M3238 must require both aggregate and required rare-family selector gates
- M3238 must keep C2 blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, or guarded RL
- do not write a checkpoint or dataset
- do not admit controlled rollout design from aggregate selector accuracy
- do not admit C2
- do not claim driver performance, validation ranking, promotion, high-fidelity sufficiency, repair-success, robustness-result, feasibility-proof, or self-ID

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m3238-c1-family-selector-repricing
- type: infrastructure
- checkpoint: experiments/feasibility_audit/c5prime_c1_family_selector_repricing.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: family_selector_repricing_negative
- reason: Completed: no deterministic train-only selector cleared all M3238 gates. Best row-level selector accuracy was 0.803119 over the 0.538012 majority floor, but predicted-family reconstruction MSE was 0.268415 and structured:coast_steer_-0.7 stayed 0/101, predicted as structured:brake_steer_-1.0. Local selector/interface training is rejected pending PI or new nonlocal-interface pricing; C2/C3 remain blocked.

## Next Blocker

C2 remains blocked. M3238 rejects the local family-selector route; C1 local selector/interface training is blocked pending PI or a new nonlocal-interface pricing route.
