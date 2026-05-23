# m376-m374-alpha02-cumulative-old-key-boundary-audit Research Review

## Summary

- Generated at UTC: 20260523T124204Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M376 completes when the alpha 0.2 cumulative old-key boundary is classified and the next non-PPO repair or PPO decision is registered.

## Hypothesis

The first tested M374 alpha 0.2 failure is likely a cumulative old-key lower-tail boundary rather than broad proof washout; auditing row-level contributors can decide the next repair design.

## Lineage

- parent_checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt, runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m374_gap_tail_final_interpolation_old_key_targeted_replay/guard_results.csv, runs/m374_gap_tail_final_interp_a020_cumulative_old_key_replay_gate/summary.json, docs/m375-full-public-gate-for-m374-a010.md
- parent_config: experiments/manifests/m375-full-public-gate-for-m374-a010.json
- parent_objective: audit the first cumulative old-key failure beyond the newly promoted M374 alpha 0.1 base
- derived_from: m375-full-public-gate-for-m374-a010
- blocked_by: m375-full-public-gate-for-m374-a010
- supersedes: None
- invalidates: None

## Success Criteria

- alpha 0.2 old-key failure type is classified
- row-level normal/wrong/gap contributors are summarized
- next milestone is registered based on the failure class
- research validation passes

## Failure Criteria

- audit treats threshold failure as a reason to lower thresholds
- audit changes actor inputs
- audit promotes alpha 0.2 directly
- research validation fails

## Evidence Gates

- audit only; no PPO run
- keep M375 alpha 0.1 as current promoted base
- do not lower cumulative old-key thresholds
- classify whether alpha 0.2 fails by gap-tail erosion or accepted regression
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote alpha 0.2
- do not lower old-key thresholds
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

pending M376 alpha 0.2 cumulative old-key boundary audit
