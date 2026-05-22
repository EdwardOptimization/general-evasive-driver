# M138 Retention Loss Rollout Misalignment Audit

M137 showed a counterintuitive result: fixed M136 retention loss and fixed M128
outcome loss both improve, behavior gates pass, but strict rollout proof-surface
diversity collapses. M138 audits that mismatch at the retained-key level.

## Artifacts

Run directory: `runs/m138_retention_loss_rollout_misalignment_audit`.

Artifacts:

- `key_loss_rollout_audit.csv`
- `audit_summary.json`

The audit uses the 20 M136 retained rows and 11 unique M133 keys
`(seed, source_condition, source_step, paired_step)`.

## Aggregate Result

| Policy | Objective loss | Delta vs M132 | Retained unique keys | Lost unique keys |
| --- | ---: | ---: | ---: | ---: |
| M132 s60 | 0.105571 | 0.000000 | 11 | 0 |
| M137 s20 a20 | 0.103103 | -0.002467 | 7 | 4 |
| M137 s40 a20 | 0.101464 | -0.004106 | 7 | 4 |
| M137 s40 a50 | 0.104001 | -0.001569 | 8 | 3 |

All M137 candidates reduce the fixed retained-key objective, but each loses
M133 keys under strict rollout selection.

## Lost-Key Evidence

Examples from `key_loss_rollout_audit.csv`:

| Candidate | Lost rows | Lost unique keys | Notable penalty deltas |
| --- | ---: | ---: | --- |
| s20 a20 | 5 | 4 | lost rows include penalty deltas down to `-0.032033` |
| s40 a20 | 5 | 4 | lost rows include penalty deltas down to `-0.060017` |
| s40 a50 | 3 | 3 | lost rows include penalty deltas down to `-0.013025` |

The important point is that lost rows often have **lower** retained-snippet
penalty than M132. For example, `s40 a20` loses the duplicated seed `9906`
step `44 -> 44` rows while decreasing their per-row penalties by about
`0.058-0.060`. So the failure is not simply "the retained rows were not fit".
The fixed logprob objective moves the local distribution in a way that does not
preserve rollout-level margin or selected-key survival.

## Interpretation

M138 confirms that retained-snippet logprob is not a safe proxy for strict
rollout proof-surface preservation.

What is now known:

- behavior success can stay unchanged;
- zero-response degradation can stay visible;
- fixed M136/M128 losses can improve;
- per-row retained penalties can decrease on rows that later disappear;
- strict rollout selected-pair and selected-seed diversity can still collapse.

This means the next repair must constrain rollout behavior more directly. A
plain logprob preference loss on retained snippets is not enough.

## Decision

Close M138 as a diagnostic positive.

The next objective should use direct key-action retention or a rollout-aware
guard. The simplest next experiment is to anchor action means on the M136
retained keys to M132 while allowing controlled improvement elsewhere, then run
the same M133 strict gates.

## Next Step

M139 should prototype a key-action retention objective or optimizer path:

- preserve M132 action means on the M136 retained keys;
- keep M136/M128 fixed losses from regressing materially;
- require M133 strict selected-pair and selected-seed diversity to survive;
- keep the actor input contract unchanged.
