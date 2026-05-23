# m375-full-public-gate-for-m374-a010 Research Review

## Summary

- Generated at UTC: 20260523T124204Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m374_a010_gap_tail_weighted_public_gate_base
- Decision reason: M375 promotes M374 alpha 0.1 after cumulative old-key source-diverse six public replay surfaces and behavior seeds pass

## Hypothesis

The bounded M374 alpha 0.1 gap-tail weighted repair candidate may pass the full public promotion gate after preserving exact, cumulative old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt, runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m374_gap_tail_final_interp_a010_cumulative_old_key_replay_gate/summary.json, runs/m374_gap_tail_a010_source_diverse_protected_gate/summary.json, runs/m374_gap_tail_a010_m183_m170_first_replay/summary.json, runs/m374_gap_tail_a010_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m374-gap-tail-weighted-repair-probe.json
- parent_objective: run full public gate for the bounded M374 gap-tail weighted repair candidate
- derived_from: m374-gap-tail-weighted-repair-probe
- blocked_by: m374-gap-tail-weighted-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 pass
- old-key and source-diverse proof results from M374 are cited
- candidate is promoted only if no proof or behavior regression is found
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- research validation fails

## Evidence Gates

- cumulative old-key replay for M374 a010 retained
- source-diverse protected pass from M374 retained
- M183/M170 and M267/M264 first replay pass from M374 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 pass
- no actor input contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote without all six replay surfaces
- do not ignore behavior regressions
- do not hide that alpha 0.2 toward the final repair fails cumulative old-key gap p10
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m375-full-public-gate-for-m374-a010
- type: driver_candidate
- checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844193
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m374_a010_gap_tail_weighted_public_gate_base
- reason: M375 promotes M374 alpha 0.1 after cumulative old-key source-diverse six public replay surfaces and behavior seeds pass

## Next Blocker

m376-m374-alpha02-cumulative-old-key-boundary-audit
