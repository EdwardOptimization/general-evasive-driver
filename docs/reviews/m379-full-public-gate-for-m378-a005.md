# m379-full-public-gate-for-m378-a005 Research Review

## Summary

- Generated at UTC: 20260523T130434Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m378_a005_gap_tail_v2_public_gate_base
- Decision reason: M379 promotes M378 alpha 0.05 after cumulative old-key source-diverse six public replay surfaces and behavior seeds pass

## Hypothesis

The bounded M378 alpha 0.05 gap-tail v2 repair candidate may pass the full public promotion gate after preserving exact, cumulative old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt, runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m378_v2_final_interp_a005_cumulative_old_key_replay_gate/summary.json, runs/m378_v2_a005_source_diverse_protected_gate/summary.json, runs/m378_v2_a005_m183_m170_first_replay/summary.json, runs/m378_v2_a005_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m378-cumulative-gap-tail-v2-repair-probe.json
- parent_objective: run full public gate for the bounded M378 cumulative gap-tail v2 repair candidate
- derived_from: m378-cumulative-gap-tail-v2-repair-probe
- blocked_by: m378-cumulative-gap-tail-v2-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 pass
- old-key and source-diverse proof results from M378 are cited
- candidate is promoted only if no proof or behavior regression is found
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- research validation fails

## Evidence Gates

- cumulative old-key replay for M378 a005 retained
- source-diverse protected pass from M378 retained
- M183/M170 and M267/M264 first replay pass from M378 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 pass
- no actor input contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote without all six replay surfaces
- do not ignore behavior regressions
- do not hide that alpha 0.1 toward the final repair fails cumulative old-key gap p10
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m379-full-public-gate-for-m378-a005
- type: driver_candidate
- checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844172
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m378_a005_gap_tail_v2_public_gate_base
- reason: M379 promotes M378 alpha 0.05 after cumulative old-key source-diverse six public replay surfaces and behavior seeds pass

## Next Blocker

m380-m378-alpha01-cumulative-old-key-boundary-audit
