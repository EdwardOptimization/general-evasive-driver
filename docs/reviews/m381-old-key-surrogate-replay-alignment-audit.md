# m381-old-key-surrogate-replay-alignment-audit Research Review

## Summary

- Generated at UTC: 20260523T131125Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m382_terminal_margin_recovery_residual_design
- Decision reason: M381 shows exact old-key surrogate improvement is strongly aligned with worse replay-tail erosion across M374 and M378 so next design terminal-margin or local-action recovery residual

## Hypothesis

Repeated old-key lower-tail failures may mean the exact old-key surrogate is only partially aligned with closed-loop replay tail metrics; measuring this alignment can decide whether the next repair should use another overlay or a terminal-margin/local-action recovery residual.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m374_gap_tail_final_interpolation_old_key_targeted_replay/summary.json, runs/m378_v2_gap_tail_final_interpolation_old_key_targeted_replay/summary.json, runs/m380_alpha01_cumulative_old_key_boundary_audit/summary.json
- parent_config: experiments/manifests/m380-m378-alpha01-cumulative-old-key-boundary-audit.json
- parent_objective: audit whether exact old-key surrogate improvements align with closed-loop cumulative old-key replay tail metrics
- derived_from: m380-m378-alpha01-cumulative-old-key-boundary-audit
- blocked_by: m380-m378-alpha01-cumulative-old-key-boundary-audit
- supersedes: None
- invalidates: None

## Success Criteria

- alignment table includes exact old-key surrogate deltas and closed-loop old-key gap metrics for M374 and M378 interpolation families
- audit identifies whether surrogate improvements correlate with replay tail safety
- next milestone is registered based on the alignment result
- research validation passes

## Failure Criteria

- audit treats exact surrogate improvement as sufficient without replay evidence
- audit changes thresholds or actor inputs
- audit promotes a checkpoint
- research validation fails

## Evidence Gates

- audit only; no PPO run
- compare exact old-key surrogate deltas against closed-loop old-key gap p10/min and accepted-regression metrics
- include recent M374 and M378 interpolation families
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add another gap-tail overlay before checking alignment
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m381-old-key-surrogate-replay-alignment-audit
- type: gate
- checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m382_terminal_margin_recovery_residual_design
- reason: M381 shows exact old-key surrogate improvement is strongly aligned with worse replay-tail erosion across M374 and M378 so next design terminal-margin or local-action recovery residual

## Next Blocker

m382-terminal-margin-recovery-residual-design
