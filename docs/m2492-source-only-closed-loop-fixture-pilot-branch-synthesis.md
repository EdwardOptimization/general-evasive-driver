# M2492 Source-Only Closed-Loop Fixture Pilot Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- decision: `promote_to_engineering_controller_source_only_metric_panel`
- manifest: `experiments/manifests/m2492-source-only-closed-loop-fixture-pilot-branch-synthesis.json`
- synthesis artifact: `docs/m2492-source-only-closed-loop-fixture-pilot-branch-synthesis.md`
- parent evidence window: `m2487` through `m2491`
- next milestone: `m2493-engineering-controller-source-only-role-metric-panel`
- external high-fidelity simulation installed/imported/executed in M2492: `false`
- new policy action/measured validation/training/replay/PPO/ranking/winner selection in M2492: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

M2487-M2491 moved the project from HF0/source-only interface smoke back to
bounded closed-loop policy-action evidence:

```text
M2487:
  designed the source-only closed-loop fixture pilot
  admitted actor candidate:
    runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  required same-contract admission:
    observation dim 72
    action dim 3
    actor_encoder in {human_view_online_gru, response_critical_online_gru}
  no policy action, training, ranking, or verdict

M2488:
  implemented and ran source-only path-smoke execution
  checkpoint_admitted: true
  checkpoint obs/action/encoder/horizon: 72 / 3 / human_view_online_gru / 1
  fixtures/resets/steps: 3 / 3 / 60
  all observations shape 72: true
  all actions shape 3 finite bounded: true
  all backend statuses running: true
  all actor-input leak flags: false
  policy_action: true
  policy_rollout_run: true

M2489:
  audited and accepted M2488 as path-smoke evidence
  rejected driver-performance, validation, ranking, paper, FW-vs-GRU, and
  self-ID interpretations

M2490:
  extended the source-only execution to 100 steps per fixture
  checkpoint_admitted: true
  fixtures/resets/steps: 3 / 3 / 300
  role counts:
    stable_aes: 100
    drift_required_recovery: 100
    unavoidable_mitigation: 100
  all observations shape 72: true
  all actions shape 3 finite bounded: true
  all backend statuses running: true
  all actor-input leak flags: false

M2491:
  audited and accepted M2490 as extended source-only execution evidence
  routed to branch synthesis before another extension or route escalation
```

The source-only branch therefore changed actual project capability: the
repository can now execute a same-contract recurrent actor through the admitted
source-only HF0 fixtures and preserve the actor-input boundary. It still lacks
role metrics, failure taxonomy beyond path gates, same-case controller
comparisons, high-fidelity validation, and paper-level mechanism evidence.

## Supported Claims

Supported:

```text
The source-only HF0 closed-loop execution path is live.

The selected recurrent actor checkpoint is admitted under the 72-observation /
3-action deployable contract.

The same actor can execute deterministic policy actions through all three
admitted source-only fixtures for 100 steps per fixture without nonfinite
actions, out-of-bound actions, backend path failure, or actor-input leakage.

The branch produced new closed-loop rows rather than only interface/process
artifacts.
```

## Falsified Or Unsupported Claims

Still unsupported:

```text
Driver performance:
  unsupported. No success, collision, road departure, spin, clearance, recovery,
  or role-specific outcome metrics have been computed.

Controller-family ranking:
  unsupported. No baseline controller or L0/L1/L2/L3 family comparison ran.

Checkpoint promotion:
  unsupported. The checkpoint was admitted for evaluation path smoke only and
  was not promoted.

High-fidelity validation readiness:
  unsupported. The runs used source_only_four_wheel_hf0, not Chrono or another
  external high-fidelity backend.

Current-sim benchmark verdict:
  unsupported. Current-sim remains diagnostic and was not repaired or rerun.

Finite-window-vs-GRU or level-3 self-ID evidence:
  unsupported. No fair controller-family matrix, finite-window comparison,
  wrong-history intervention, reset-hidden control, or terminal-boundary
  mechanism test ran.

Paper-level evidence:
  unsupported. The branch is source-only engineering path evidence only.
```

## Failure Taxonomy Summary

Observed:

```text
none for the M2488/M2490 execution gates
```

Controlled:

```text
contract_violation:
  controlled by checkpoint admission and 72/3 reset/step/action gates.

lineage_invalid:
  controlled by manifests, committed run artifacts, milestone docs, reviews,
  queue/status, and scoreboard rows.

metric_artifact:
  controlled so far because the branch rejects success-rate/performance
  interpretation. Risk becomes high if the 300 source-only rows are used as a
  driver-quality claim.

objective_overfit:
  medium. The branch escaped the HF0 interface loop by producing closed-loop
  rows, but another source-only horizon extension would now be low-value unless
  it adds new role metrics or failure evidence.
```

Active blockers:

```text
scenario_sampling_failure:
  active outside this branch. Source-only fixtures do not repair current-sim
  stable-AES readiness.

behavior_regression:
  unmeasured. No baseline comparison, role metric panel, or regression panel
  exists for the source-only rows.
```

## Public Gate Overfit Risk

Risk entering M2492: `medium`.

Reason:

```text
The branch produced real closed-loop rows, so it is not only process overhead.
However, the fixtures are fixed and public, and the current evidence only proves
that the execution path runs. Continuing by horizon length alone would optimize
the same narrow public fixtures without clarifying engineering capability.
```

Risk after M2492: `medium-low` if the next branch turns the rows into a
role-metric and failure-taxonomy panel before any claim escalation.

Mitigation:

```text
Do not continue directly to another source-only horizon extension.

Do not compute a success-rate verdict yet.

Promote to an engineering-controller source-only metric panel branch that
records deployable closed-loop telemetry, role-specific nonverdict metrics,
runtime/action statistics, and failure taxonomy hooks while preserving the
actor-input contract.
```

## Next Branch Decision

Decision:

```text
promote_to_engineering_controller_source_only_metric_panel
```

Rationale:

```text
Stopping would waste the new source-only closed-loop execution path.

Continuing with another plain horizon extension would be mostly local-search
over the same fixtures.

Returning immediately to paper-route comparison is premature because the
source-only branch has no role metrics or baseline panel.

Returning immediately to external high-fidelity backend work is useful later,
but the engineering route first needs a compact source-only telemetry and
failure panel so the project knows what the admitted actor actually does.
```

Required next route:

```text
m2493-engineering-controller-source-only-role-metric-panel
```

M2493 should run a bounded evaluation-only source-only panel using the same
admitted actor and three fixtures. It should write telemetry rows and a
role-metric panel containing nonverdict engineering diagnostics such as action
saturation, speed/yaw/y-envelope ranges, backend-alive fraction, finite-state
checks, and role coverage.

M2493 must not compute success rate, rank controllers, select a winner, promote
a checkpoint, claim driver performance, claim high-fidelity validation, or make
paper/self-ID/FW-vs-GRU claims.

## Evidence Scope

M2492 is synthesis only. It does not execute new policy actions, run measured
validation, train, replay, use PPO, rank controllers, select winners, or claim
driver performance. It promotes the source-only execution branch to an
engineering-controller diagnostic branch because that is the next step that can
turn closed-loop rows into actionable evidence without overstating them.
