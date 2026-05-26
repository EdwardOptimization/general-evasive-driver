# M963 V4 Public Base Target Feasibility Export Branch Synthesis

## Purpose

M963 synthesizes the M953-M962 branch before actor-fit continuation.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

The branch started after M952 pivoted away from local controlled-fusion retunes
and asked a more basic question:

```text
Do replay-constrained target candidates exist before more actor updates?
```

M962 is the tenth non-synthesis milestone in this branch, so the workflow
cadence requires synthesis before opening the actor-fit branch.

## Evidence Summary

M953 designed a no-training target feasibility audit. It required any target
candidate to jointly preserve:

```text
normal retention
low-tail lift or behavior improvement
M267/M264 wrong-history proof retention
```

M954 implemented the one-step target feasibility audit. Result:

```text
joint_feasible_target_count: 0
exact_target_candidate_count: 0
m267_target_preflight_pass_count: 55 / 56
normal_safe_low_tail_trend_count: 27
```

This showed M267 proof retention was not the active bottleneck. The blocker was
one-step low-tail exact feasibility.

M955 designed a short-horizon sequence target audit. M956 implemented it.
Result:

```text
first-action retention: 9 / 9
M267 sequence preflight: 9 / 9
sequence_low_tail_candidate_count: 0
terminal_margin_positive_family_count: 0
```

Delayed action-gap projection preserved proof, but worsened terminal margin.
That pointed to metric grounding rather than first-action under-specification.

M957 designed a low-tail target metric artifact audit. M958 implemented it.
Result:

```text
away_from_intervention:
  proxy_improved_fraction: 1.000000
  behavior_improved_fraction: 0.000000
  terminal_margin_mean_delta: -0.000057

toward_intervention:
  proxy_improved_fraction: 0.000000
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000057
```

This falsified the old away-from-intervention target direction and identified
behavior-improving direction families.

M959 designed the direction-family target audit. M960 implemented it. Result:

```text
joint_direction_target_candidate_count: 20
primary_joint_candidate_count: 20
best_joint_candidate_family: throttle_minus_amp_0_0080
```

All joint candidates came from primary behavior-improving families:

```text
throttle_minus
brake_plus
toward_intervention
steer_minus_brake_plus
```

M961 designed branch-separated export and actor-fit objective. M962 implemented
the no-training export. Result:

```text
result_class: direction_target_export_pass
accepted_direction_target_count: 1280
accepted_family_count: 20
branch_separated_proof_target_count: 160
retention_anchor_count: 1149
diagnostic_target_count: 0
max_direction_family_fraction: 0.25
```

## Supported Claims

Target-space feasibility exists after the target direction is corrected.

The branch no longer supports the conclusion that no targets exist. It supports
a narrower claim:

```text
the old action-gap direction was wrong, but terminal-margin-improving direction
families produce normal-retained, proof-retained targets.
```

M267/M264 proof retention is not the current target-space blocker when proof
targets are branch-separated and wrong-history actions remain anchored.

The exported corpus is auditable and actor-contract compliant:

```text
accepted low-tail targets
branch-separated proof anchors
retention anchors
rejected export candidates
```

No actor input/output change was needed.

## Falsified Claims

The branch falsifies:

- one-step away-from-intervention target projection is behaviorally grounded;
- delayed away-from-intervention sequence projection fixes the target failure;
- the blocker is merely a strict low-tail threshold;
- actor training is justified before target feasibility and export;
- accepted target export requires diagnostic-only anti-aligned families.

It does not yet prove:

- the actor can fit these targets without replay proof washout;
- the target-fit direction improves full closed-loop public replay gates;
- PPO can use this direction safely;
- the exported targets generalize beyond the current 64 public low-tail rows.

## Failure Taxonomy Summary

M954:

```text
failure_type: objective_overfit / target_feasibility_failure
meaning: one-step target families preserved M267 but did not pass exact low-tail
```

M956:

```text
failure_type: metric_artifact
meaning: delayed low-tail projection preserved retention and proof but worsened
terminal margin
```

M958:

```text
failure_type: metric_artifact
meaning: old proxy direction was sign-suspect; proxy improvement and terminal
margin improvement were anti-aligned for away/toward intervention
```

M960 and M962:

```text
failure_type: none
meaning: corrected direction families yielded exportable target candidates
```

The main historical failure mode in this branch was not proof washout. It was
target metric misalignment.

## Public-Gate Overfit Risk

Risk remains moderate to high.

Reasons:

- the accepted direction targets are derived from `64` public low-tail rows;
- M267/M264 active rows are public proof rows;
- the export is balanced across direction families, but not yet refreshed
  across a source-diverse scenario distribution;
- M962 proves corpus materialization, not actor fit or closed-loop replay
  improvement.

Mitigation for the next branch:

- start with objective-only actor fit, not PPO;
- keep public replay gates and behavior seeds as blockers, not promotion gates;
- do not use private holdout for tuning;
- after the first actor-fit pass/fail, run a source-diverse direction-target
  refresh or synthesis before long continuation.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
v4_public_base_replay_constrained_target_feasibility
```

Open:

```text
v4_public_base_direction_target_actor_fit
```

The next branch should test:

```text
Can the actor fit the exported M962 direction-target corpus while preserving
M267/M264 proof rows, public replay surfaces, and behavior seeds?
```

This is a new evidence axis. M953-M962 established target feasibility and
export. They did not establish actor-fit feasibility.

## Next Milestone

M963 routes to:

```text
m964-v4-public-base-direction-target-actor-fit-objective-implementation
```

M964 should run an objective-only actor-fit probe using M962 exported targets.
It may update actor weights, but it must not run PPO, change actor inputs, use
private holdout, or promote.
