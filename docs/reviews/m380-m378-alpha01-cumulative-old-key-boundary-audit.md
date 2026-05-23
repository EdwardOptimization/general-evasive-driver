# m380-m378-alpha01-cumulative-old-key-boundary-audit Research Review

## Summary

- Generated at UTC: 20260523T130739Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m381_old_key_surrogate_replay_alignment_audit
- Decision reason: M380 classifies alpha 0.1 as repeated cumulative old-key gap-tail erosion with zero accepted regressions and admits surrogate-vs-replay alignment audit before another overlay

## Hypothesis

The first tested M378 alpha 0.1 failure is likely a cumulative old-key lower-tail boundary rather than broad proof washout; auditing row-level contributors can decide the next repair design.

## Lineage

- parent_checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt, runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m378_v2_final_interp_a005_cumulative_old_key_replay_gate/summary.json, runs/m378_v2_final_interp_a010_cumulative_old_key_replay_gate/summary.json, docs/m379-full-public-gate-for-m378-a005.md
- parent_config: experiments/manifests/m379-full-public-gate-for-m378-a005.json
- parent_objective: audit the first cumulative old-key failure beyond the newly promoted M378 alpha 0.05 base
- derived_from: m379-full-public-gate-for-m378-a005
- blocked_by: m379-full-public-gate-for-m378-a005
- supersedes: None
- invalidates: None

## Success Criteria

- alpha 0.1 old-key failure type is classified
- row-level normal/wrong/gap contributors are summarized
- next milestone is registered based on the failure class
- research validation passes

## Failure Criteria

- audit treats threshold failure as a reason to lower thresholds
- audit changes actor inputs
- audit promotes alpha 0.1 directly
- research validation fails

## Evidence Gates

- audit only; no PPO run
- keep M378 alpha 0.05 as current promoted base
- do not lower cumulative old-key thresholds
- classify whether alpha 0.1 fails by gap-tail erosion or accepted regression
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote alpha 0.1
- do not lower old-key thresholds
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m380-m378-alpha01-cumulative-old-key-boundary-audit
- type: gate
- checkpoint: runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m381_old_key_surrogate_replay_alignment_audit
- reason: M380 classifies alpha 0.1 as repeated cumulative old-key gap-tail erosion with zero accepted regressions and admits surrogate-vs-replay alignment audit before another overlay

## Next Blocker

m381-old-key-surrogate-replay-alignment-audit
