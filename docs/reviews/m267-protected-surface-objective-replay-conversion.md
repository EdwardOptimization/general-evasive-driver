# m267-protected-surface-objective-replay-conversion Research Review

## Summary

- Generated at UTC: 20260522T172314Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: admit_guarded_actor_update_design
- Decision reason: M267 converts M266 into 17-row 13-pair corpora for M264 M263 M261 with 3-seed objective pass and 17 of 17 replay success drops retained

## Hypothesis

The M266 source-diverse protected surface can be converted into replay-aligned objective/proof corpora for the current M261/M263/M264 family before any further PPO.

## Lineage

- parent_checkpoint: runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt, runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt, runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m266_m264_family_boundary_surface_seed9520/accepted_wrong_history_rows.csv, runs/m266_m264_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m266-m264-family-protected-surface-refresh.json, docs/m266-m264-family-protected-surface-refresh.md
- parent_objective: convert refreshed current-family protected surface into replay-aligned objective/proof corpora
- derived_from: m266-m264-family-protected-surface-refresh
- blocked_by: m266-m264-family-protected-surface-refresh
- supersedes: None
- invalidates: None

## Success Criteria

- M267 creates compact source-diverse boundary-outcome corpora from M266 accepted rows
- objective sanity passes for the M264 public-gate base and current-family checkpoints
- replay sanity preserves normal-history success and wrong-history failure for selected rows
- M267 records whether the refreshed protected surface can replace the single-key veto as the active blocker
- actor input contract remains unchanged

## Failure Criteria

- corpus construction is duplicate-dominated
- objective sanity cannot reproduce the M266 wrong-history outcome signal
- replay sanity loses normal success or wrong-history failure on selected rows
- M267 runs PPO, changes actor inputs, or promotes a checkpoint

## Evidence Gates

- build compact source-diverse corpora from M266 accepted wrong-history rows
- include the M264 public-gate base and current-family checkpoints in corpus sanity
- run objective sanity before actor update or PPO
- run replay sanity that preserves normal success and wrong-history failure on corpus rows
- keep old protected key 9944 as a diagnostic row rather than the sole veto

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M267
- do not change actor inputs
- do not promote a checkpoint in M267
- do not tune thresholds from private holdout evidence
- do not discard the old protected key diagnostic

## Failure Taxonomy

- none

## Scoreboard

- milestone: m267-protected-surface-objective-replay-conversion
- type: objective_sanity
- checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: admit_guarded_actor_update_design
- reason: M267 converts M266 into 17-row 13-pair corpora for M264 M263 M261 with 3-seed objective pass and 17 of 17 replay success drops retained

## Next Blocker

m268-m267-guarded-actor-update-from-m264
