# m378-cumulative-gap-tail-v2-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T125948Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m379_full_public_gate_for_m378_a005
- Decision reason: M378 bounded alpha 0.05 toward the v2 gap-tail final repair passes exact cumulative old-key source-diverse and first replay proof gates; alpha 0.1 first fails cumulative old-key gap p10

## Hypothesis

The v2 cumulative gap-tail old-key corpus can produce a bounded no-PPO repair candidate beyond M375 alpha 0.1 while retaining cumulative old-key lower-tail proof.

## Lineage

- parent_checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt, runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz, runs/m377_cumulative_gap_tail_v2_overlay/old_key_feedback_overlay.csv, docs/m377-cumulative-gap-tail-v2-corpus-refresh.md
- parent_config: experiments/manifests/m377-cumulative-gap-tail-v2-corpus-refresh.json
- parent_objective: probe whether refreshed cumulative gap-tail v2 feedback can repair beyond the M375 alpha 0.1 base without PPO
- derived_from: m377-cumulative-gap-tail-v2-corpus-refresh
- blocked_by: m377-cumulative-gap-tail-v2-corpus-refresh
- supersedes: None
- invalidates: None

## Success Criteria

- v2 repair candidate passes exact M297/M270 and old-key surrogate gates
- closed-loop cumulative old-key replay passes for a nonzero candidate beyond M375 alpha 0.1
- source-diverse and first replay gates are run if cumulative old-key replay passes
- failure is classified if exact surrogate improves but closed-loop lower tail still erodes
- research validation passes

## Failure Criteria

- v2 repair cannot move beyond M375 alpha 0.1 without cumulative old-key replay failure
- exact objectives regress
- weighted old-key surrogate is insensitive to M376 gap-tail rows
- actor input contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression
- weighted old-key surrogate no-regression
- cumulative old-key replay and replay-gate adapter
- source-diverse protected gates if old-key replay passes
- first replay gates if proof gates pass
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote directly
- do not run PPO
- do not lower old-key thresholds
- do not skip cumulative old-key replay
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m378-cumulative-gap-tail-v2-repair-probe
- type: gate
- checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m379_full_public_gate_for_m378_a005
- reason: M378 bounded alpha 0.05 toward the v2 gap-tail final repair passes exact cumulative old-key source-diverse and first replay proof gates; alpha 0.1 first fails cumulative old-key gap p10

## Next Blocker

m379-full-public-gate-for-m378-a005
