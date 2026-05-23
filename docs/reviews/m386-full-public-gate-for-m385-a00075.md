# m386-full-public-gate-for-m385-a00075 Research Review

## Summary

- Generated at UTC: 20260523T135452Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m385_micro_a00075_public_gate_base
- Decision reason: M386 promotes M385 micro alpha 0.00075 after exact cumulative old-key source-diverse six replay and behavior gates pass; proof-safe micro promotion

## Hypothesis

The M385 micro-alpha 0.00075 candidate can pass the full public promotion gate after exact, cumulative old-key, source-diverse, and first replay proof gates already passed.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt, runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: runs/m385_micro_a0_00075_exact_eval_vs_m378/summary.json, runs/m385_micro_a0_00075_old_key_replay_gate/summary.json, runs/m385_micro_a0_00075_source_diverse_protected_gate/summary.json, runs/m385_micro_a0_00075_m183_m170_first_replay/summary.json, runs/m385_micro_a0_00075_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m385-old-key-recovery-residual-repair-probe.json
- parent_objective: full public promotion gate for the M385 micro-alpha proof-gate candidate
- derived_from: m385-old-key-recovery-residual-repair-probe
- blocked_by: m385-old-key-recovery-residual-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six public replay surfaces pass with no success-drop regression
- behavior seeds 9505 and 9506 do not regress versus current base
- actor contract remains unchanged
- artifacts and decision are documented
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior retention regresses
- actor contract changes
- research validation fails

## Evidence Gates

- M385 exact M297/M270 no-regression retained
- M385 cumulative old-key replay retained
- M385 source-diverse protected gate retained
- all six public replay surfaces pass versus m333_base
- behavior seeds 9505 and 9506 retained
- preserve actor input/output contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not lower replay or old-key thresholds
- do not promote if any public replay or behavior gate fails
- do not add hidden or oracle actor inputs
- do not replace direct steer/throttle/brake output

## Failure Taxonomy

- none

## Scoreboard

- milestone: m386-full-public-gate-for-m385-a00075
- type: driver_candidate
- checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844184
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m385_micro_a00075_public_gate_base
- reason: M386 promotes M385 micro alpha 0.00075 after exact cumulative old-key source-diverse six replay and behavior gates pass; proof-safe micro promotion

## Next Blocker

m387-m386-micro-promotion-utility-audit
