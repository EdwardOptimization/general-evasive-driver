# M381 Old-Key Surrogate Replay Alignment Audit

M381 audits whether exact old-key surrogate improvements are aligned with
closed-loop cumulative old-key replay tails. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Inputs

M381 compares two recent interpolation families:

| Family | Base | Final direction | Old-key surrogate corpus |
| --- | --- | --- | --- |
| M374 gap-tail v1 | `runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt` | `runs/m374_gap_tail_weighted_repair_final_from_alpha06_s40_seed10110/candidate_checkpoint.pt` | `runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.npz` |
| M378 gap-tail v2 | `runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt` | `runs/m378_v2_gap_tail_repair_final_from_alpha02_s40_seed10113/candidate_checkpoint.pt` | `runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz` |

Artifacts:

```text
runs/m381_old_key_surrogate_replay_alignment_audit/alignment_rows.csv
runs/m381_old_key_surrogate_replay_alignment_audit/family_alignment_summary.csv
runs/m381_old_key_surrogate_replay_alignment_audit/summary.json
```

## Result

The exact old-key surrogate is directionally misaligned with closed-loop
lower-tail safety. Larger surrogate improvement tracks worse replay gap p10.

| Metric | Value |
| --- | ---: |
| alignment rows | 18 |
| overall corr: surrogate improvement vs gap p10 | -0.993196 |
| overall corr: surrogate improvement vs gap-p10 erosion | +0.991817 |
| M374 corr: surrogate improvement vs gap p10 | -0.999937 |
| M378 corr: surrogate improvement vs gap p10 | -0.999927 |

Family summary:

| Family | Max passing alpha | First failing alpha | Best surrogate alpha | Best surrogate gate pass |
| --- | ---: | ---: | ---: | --- |
| M374 gap-tail v1 | 0.100 | 0.200 | 1.000 | false |
| M378 gap-tail v2 | 0.050 | 0.100 | 1.000 | false |

Selected rows:

| Family | Alpha | Old-key surrogate delta | Gap p10 | Accepted regressions | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M374 v1 | 0.000 | +0.000000 | -0.000380 | 0 | true |
| M374 v1 | 0.100 | -0.003164 | -0.000453 | 0 | true |
| M374 v1 | 0.200 | -0.006328 | -0.000527 | 0 | false |
| M374 v1 | 1.000 | -0.031693 | -0.001147 | 2 | false |
| M378 v2 | 0.000 | +0.000000 | -0.000453 | 0 | true |
| M378 v2 | 0.050 | -0.001611 | -0.000488 | 0 | true |
| M378 v2 | 0.100 | -0.003223 | -0.000524 | 0 | false |
| M378 v2 | 1.000 | -0.032301 | -0.001196 | 2 | false |

## Interpretation

The current exact old-key surrogate is useful as a local indicator only after
external interpolation bounds it. Optimizing it harder is not aligned with the
closed-loop replay tail: the best surrogate endpoints are the worst old-key
tail endpoints. This explains why M374 and M378 both needed tight interpolation
after apparently strong exact improvements.

The next repair objective should bind the update to actual terminal margin or
recoverable local action targets on tail rows. A plain v3 branch-weight overlay
would likely repeat the same pattern: exact surrogate improves, but cumulative
old-key gap p10 erodes until the replay gate clips movement.

## Decision

Admit:

```text
m382-terminal-margin-recovery-residual-design
```

Decision:

```text
admit_m382_terminal_margin_recovery_residual_design
```
