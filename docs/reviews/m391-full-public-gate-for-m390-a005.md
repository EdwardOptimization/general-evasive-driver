# m391-full-public-gate-for-m390-a005 Research Review

## Summary

- Generated at UTC: 20260523T142759Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m390_step17_a005_public_gate_base
- Decision reason: M391 promotes M390 alpha 0.005 after six public replay surfaces and behavior seeds pass; proof-safe micro promotion

## Hypothesis

The M390 alpha 0.005 bounded repair candidate can pass the full public promotion gate after exact objectives, M267/M264, cumulative old-key, source-diverse, and M183/M170 proof gates already passed.

## Lineage

- parent_checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt, runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: runs/m390_step17_a005_exact_eval/summary.json, runs/m390_step17_micro005_m267_m264_first_replay/summary.json, runs/m390_step17_a005_old_key_replay_gate/summary.json, runs/m390_step17_a005_source_diverse_protected_gate/summary.json, runs/m390_step17_a005_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m390-m267-conflict-residual-repair-probe.json
- parent_objective: run full public replay and behavior gates for the M390 alpha 0.005 bounded repair candidate
- derived_from: m390-m267-conflict-residual-repair-probe
- blocked_by: m390-m267-conflict-residual-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six public replay gates pass
- behavior seeds 9505 and 9506 do not regress aggregate success or termination versus the current public base
- checkpoint is promoted only if proof and behavior retention both pass
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior retention regresses
- actor contract changes
- research validation fails

## Evidence Gates

- six public replay surfaces pass versus m333_base
- behavior seeds 9505 and 9506 retain success and termination
- M390 exact and proof-gate evidence retained
- no actor input/output contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote without all six replay gates
- do not promote without behavior retention
- do not lower replay thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m391-full-public-gate-for-m390-a005
- type: driver_candidate
- checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844192
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m390_step17_a005_public_gate_base
- reason: M391 promotes M390 alpha 0.005 after six public replay surfaces and behavior seeds pass; proof-safe micro promotion

## Next Blocker

m392-m391-micro-promotion-utility-audit
