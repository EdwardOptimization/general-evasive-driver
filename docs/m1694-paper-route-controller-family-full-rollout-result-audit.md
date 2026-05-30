# M1694 Paper-Route Controller-Family Full Rollout Result Audit

- status: completed
- decision: `full_rollout_audit_pass_route_to_outcome_semantics_instrumentation_design`
- audited artifact: `runs/m1693_controller_family_full_rollout_execution/summary.json`
- audited episode rows: `runs/m1693_controller_family_full_rollout_execution/episode_rows.csv`
- audited aggregates: `profile_aggregate.csv`, `spec_aggregate.csv`, `stratum_aggregate.csv`, `comparison_aggregate.csv`

## Audit Result

M1693 is a clean public execution pass.

- episode count: `864`
- profile count: `12`
- spec count: `72`
- failure count: `0`
- selected metrics finite: `true`
- guardrail violation count: `0`
- required artifacts present: `true`
- training / replay / PPO / promotion: `false` / `false` / `false` / `false`
- private holdout / actor input change / profile-specific tuning: `false` / `false` / `false`

M1694 does not interpret M1693 as controller-family ranking, paper-level
evidence, private-holdout evidence, or level3 self-identification evidence.

## Outcome Semantics Caveat

The first audit blocker is outcome semantics, not execution plumbing.

Raw outcome counts:

| outcome bucket | count | share |
| --- | ---: | ---: |
| success | 32 | 0.0370 |
| collision failure | 38 | 0.0440 |
| terminated non-collision non-completion | 794 | 0.9190 |

The dominant bucket has high mean clearance margin:

| outcome bucket | margin mean | steps mean |
| --- | ---: | ---: |
| success | 2.6313 | 93.5625 |
| collision failure | -0.0699 | 68.6842 |
| terminated non-collision non-completion | 11.4088 | 71.5882 |

This means raw `success == obstacle_completed && !collision` is not sufficient
to rank controllers. Most failures are not obstacle collisions, and M1693 rows
do not record whether termination came from off-track, speed collapse, overspeed,
yaw-rate, non-finite state, or another condition.

## Diagnostic Findings

These findings are public diagnostics only.

- Overall public success rate is `0.0370`; collision rate is `0.0440`.
- Spec success distribution: `46/72` specs have zero successes across all
  profiles, `20/72` have `1/12` success, and `6/72` have `2/12` success.
- L2 normal versus current-tiled profiles have zero success-rate deltas for all
  four windows; margin deltas are mixed.
- `L3_online_gru` versus `L3_reset_control_corrected` has success delta
  `-0.0694`, collision delta `+0.0278`, margin delta `-0.1288`, and return delta
  `-3.4997`.
- `L3_online_gru` has higher raw success than the best normal L2 window, but
  also higher collision rate and lower clearance margin. This is not a clean
  recurrent-advantage result.
- T5 has higher raw success than T4 (`0.0486` versus `0.0255`) but also higher
  collision rate and lower clearance margin.

## Supported Claims

- M1693 execution artifacts are complete and internally consistent.
- The public workload can be executed end-to-end under the M1692 guardrails.
- M1693 provides a useful diagnostic dataset for the next task-quality and
  outcome-semantics audit.

## Unsupported Claims

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- level3 anticipatory self-identification
- private-holdout generalization
- paper-level evidence

## Decision

M1694 passes as a result audit, but it blocks controller-family interpretation.

Route to M1695 outcome-semantics instrumentation design. The next step should
add or design explicit termination-reason and completion-semantics evidence
before any controller-family ranking or paper-route comparison claim.
