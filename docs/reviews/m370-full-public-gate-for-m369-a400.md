# m370-full-public-gate-for-m369-a400 Research Review

## Summary

- Generated at UTC: 20260523T120839Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: pending
- Decision reason: M370 may promote M369 a400 only if full public replay, behavior seeds, old-key, source-diverse, and input-contract checks all pass.

## Hypothesis

The M369 a400 hard-row weighted repaired candidate may pass the full public promotion gate after preserving exact, old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt, runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- parent_dataset: runs/m369_hard_row_interp_a400_old_key_replay_gate/summary.json, runs/m369_hard_row_a400_source_diverse_protected_gate/summary.json, runs/m369_hard_row_a400_m183_m170_first_replay/summary.json, runs/m369_hard_row_a400_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m369-hard-row-weighted-repair-probe.json
- parent_objective: run full public gate for the hard-row weighted repaired alpha 0.4 candidate
- derived_from: m369-hard-row-weighted-repair-probe
- blocked_by: m369-hard-row-weighted-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 pass
- old-key and source-diverse proof results from M369 are cited
- candidate is promoted only if no proof or behavior regression is found
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- research validation fails

## Evidence Gates

- old-key replay for M369 a400 retained
- source-diverse protected pass from M369 retained
- M183/M170 and M267/M264 first replay pass from M369 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 pass
- no actor input contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote without all six replay surfaces
- do not ignore behavior regressions
- do not hide that a600 already fails old-key gap p10
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

pending M370 full public gate
