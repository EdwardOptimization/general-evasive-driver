# m395-full-public-gate-for-m394-s02a010 Research Review

## Summary

- Generated at UTC: 20260523T145919Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m394_s02a010_public_gate_base
- Decision reason: M395 promotes M394 s02 alpha 0.1 after six public replay surfaces and behavior seeds pass; proof-safe bounded promotion

## Hypothesis

The bounded M394 s02 alpha 0.1 candidate can retain the full public replay and behavior gates, making it eligible as the next public-gate base.

## Lineage

- parent_checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt, runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- parent_dataset: docs/m394-rejected-boundary-target-repair-probe.md, runs/m394_s02a010_m267_m264_first_replay/summary.json, runs/m394_s02a010_old_key_replay_gate/summary.json, runs/m394_s02a010_source_diverse_protected_gate/summary.json, runs/m394_s02a010_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m394-rejected-boundary-target-repair-probe.json
- parent_objective: full public promotion gate for bounded M394 rejected-boundary repair candidate
- derived_from: m394-rejected-boundary-target-repair-probe
- blocked_by: m394-rejected-boundary-target-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six public replay surfaces pass
- behavior seeds 9505 and 9506 retain success and termination versus the current public base
- old-key compact and source-diverse proof evidence remain valid
- document whether promotion is meaningful driver improvement or another proof-safe micro-step

## Failure Criteria

- any public replay surface fails
- behavior success or termination regresses
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- six public replay surfaces pass versus public baselines
- behavior seeds 9505 and 9506 retain success and termination
- old-key compact replay remains pass
- source-diverse protected gate remains pass
- preserve actor input/output contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote if any public replay or behavior gate fails
- do not lower replay thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m395-full-public-gate-for-m394-s02a010
- type: driver_candidate
- checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844089
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m394_s02a010_public_gate_base
- reason: M395 promotes M394 s02 alpha 0.1 after six public replay surfaces and behavior seeds pass; proof-safe bounded promotion

## Next Blocker

m396-m395-micro-promotion-utility-audit
