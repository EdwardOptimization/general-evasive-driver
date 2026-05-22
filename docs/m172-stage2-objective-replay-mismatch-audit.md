# M172 Stage2 Objective-Replay Mismatch Audit

M170 and M171 both improved the fixed M162 outcome objective while failing full
M164 boundary replay. M172 audits this mismatch before any further PPO stage.

This is a negative objective-sanity result for the current fixed objective as a
stage2 admission signal. It should remain a diagnostic loss, not a standalone
promotion criterion.

## Fixed Objective Versus Replay

| Policy | Fixed loss | Normal success | Wrong-history success | Success drops | Full replay gate |
| --- | ---: | ---: | ---: | ---: | --- |
| m168_from_m167_5168 | 0.397971 | 0.681818 | 0.500000 | 16 | pass |
| m170_stage2 | 0.397740 | 0.681818 | 0.511364 | 15 | fail |
| m171_s512_a100 | 0.397869 | 0.659091 | 0.500000 | 14 | fail |

The ordering by fixed loss is the wrong ordering for replay safety:

```text
fixed objective: m170 best, m171 second, m168 third
replay retention: m168 accepted, m170 rejected, m171 rejected
```

Therefore fixed objective improvement is not aligned enough with actual
continuation outcomes for stage2 PPO.

## Lost Rows

M170 lost:

| Row | Target | Physical pair | Failure mode |
| ---: | --- | --- | --- |
| 67 | future_lateral_accel_response | 9530:21:9540:24 | wrong-history rollout changes from collision to obstacle_completed |

M171 lost:

| Row | Target | Physical pair | Failure mode |
| ---: | --- | --- | --- |
| 70 | future_lateral_accel_response | 9518:15:9550:21 | normal rollout changes from obstacle_completed to collision |
| 77 | future_lateral_accel_response | 9518:15:9550:18 | normal rollout changes from obstacle_completed to collision |

Rows `70` and `77` are not row67 failures. M171 retains row `67` but still
fails because other low-margin rows flip.

## Margin Evidence

The lost rows are near decision boundaries.

| Row | Baseline normal margin | Candidate normal margin | Baseline wrong margin | Candidate wrong margin |
| ---: | ---: | ---: | ---: | ---: |
| 67, M170 | 0.006610 | 0.007378 | -0.000448 | 0.000191 |
| 70, M171 | 0.000269 | -0.000298 | -0.005472 | -0.006189 |
| 77, M171 | 0.000269 | -0.000298 | -0.004831 | -0.005516 |

The aggregate margin gap can improve while a binary replay outcome flips. This
explains why the full replay gate is still necessary.

## Interpretation

The current fixed objective is an action/logprob-style diagnostic over the M162
snapshot corpus. It can move the policy toward the intended intervention
preference in expectation, but it does not guarantee row-level continuation
outcome retention.

The failure is not just "row67 needs protection":

- M170 loses row `67`;
- M171 protects row `67` but loses rows `70` and `77`;
- both M170 and M171 improve fixed loss;
- both fail actual replay.

This means stage2 PPO is currently more likely to erode knife-edge boundary
cases than to produce a robustly better driver.

## Decision

Pause stage2 PPO.

Do not continue with more PPO hyperparameter variants until the next audit
answers whether lost rows are caused by tiny action shifts, hidden-state shifts,
or reward/auxiliary objective mismatch.

The next step should inspect action and margin sensitivity on the fragile rows
`67`, `70`, and `77`, then decide whether to:

- add a replay-aligned fragile-row auxiliary or action anchor;
- change the boundary corpus objective;
- keep M168 as the current accepted checkpoint and return to self-ID evidence
  work instead of stage2 PPO.

## Validation

Evidence inspected:

```text
runs/m168_fixed_batch_outcome_eval_seed37/summary.json
runs/m170_fixed_batch_outcome_eval_seed37/summary.json
runs/m171_fixed_batch_outcome_eval_seed37/summary.json
runs/m168_from_m167_5168_boundary_outcome_replay_gate_seed9510/summary.json
runs/m170_boundary_outcome_replay_gate_seed9510/summary.json
runs/m171_boundary_outcome_replay_gate_seed9510/summary.json
runs/m170_fragile_row_guard_seed9510/summary.json
runs/m171_fragile_row_guard_seed9510/summary.json
```
