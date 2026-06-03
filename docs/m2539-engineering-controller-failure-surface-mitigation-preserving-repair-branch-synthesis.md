# M2539 Engineering Controller Failure-Surface Mitigation-Preserving Repair Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- operational decision: `pivot_to_route_a_baseline_and_interface_preparation`
- manifest: `experiments/manifests/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.json`
- synthesis artifact: `docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md`
- parent audit: `docs/m2538-engineering-controller-failure-surface-mitigation-preserving-repair-execution-result-audit.md`
- next milestone: `m2540-engineering-controller-route-a-baseline-and-interface-pivot-design`
- external high-fidelity simulation installed/imported/executed in M2539: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2539: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2539: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

M2526-M2538 is a Route A failure-surface intervention and repair branch. It
produced two behavior-changing repair executions and several design, audit,
localization, and synthesis artifacts.

Evidence-producing milestones:

```text
M2529 no-update repair smoke:
  status_pass true
  45 protected/reference rows
  7 protected gate evaluations
  contract/no-oracle/no-ranking gates passed
  road-boundary, mitigation, and command-conflict proof gates failed

M2532 guarded repair execution:
  behavior-changing checkpoint written under M2532
  4500 telemetry rows
  45 post-repair protected/reference rows
  road_boundary_proof passed: 10/10 improved, 0 regressed
  command_conflict_proof passed: 15/15 improved, 0 regressed
  mitigation_proof failed: 4/5 improved, 1 regressed

M2534 localization:
  localized the remaining mitigation regression to seed 254302
  all mitigation rows improved road margin
  all mitigation rows improved command conflict
  metric_artifact_detected false

M2537 mitigation-preserving repair execution:
  behavior-changing checkpoint written under M2537
  selected candidate: m2537_relax_m2532_bias_8
  candidate sweep rows: 7
  4500 telemetry rows
  45 post-repair protected/reference rows
  retained road_boundary_proof passed: 10/10 improved, 0 regressed
  retained command_conflict_proof passed: 15/15 improved, 0 regressed
  mitigation_proof failed: 4/5 improved, 1 regressed
```

Process milestones:

```text
M2526 design
M2527 protected-row and gate materialization
M2528 immutable candidate config materialization
M2530 no-update smoke audit
M2531 guarded repair execution design
M2533 guarded repair result audit
M2535 mitigation-preserving design
M2536 branch synthesis approving exactly one bounded M2537 execution
M2538 M2537 result audit
```

The branch changed behavior and narrowed the failure surface, but it did not
complete protected proof. The remaining mitigation severity regression repeated
after the one M2536-approved mitigation-preserving execution.

## Supported Claims

Supported within Route A diagnostic scope:

```text
1. The failure-surface intervention harness is executable and traceable.
2. The actor contract stayed inside the P0 human-view 72/3 no-oracle boundary.
3. M2532 and M2537 both produced behavior-changing repaired checkpoints under
   their own run directories.
4. Road-boundary protected proof can be retained under the current actor-head
   repair family.
5. Command-conflict protected proof can be retained under the selected M2537
   candidate.
6. The branch reduced the initial three failed proof surfaces to one repeated
   mitigation severity proof failure.
7. The current public protected-row repair loop has reached a useful stopping
   point: it has characterized a failure, not solved the full driver problem.
```

Not supported:

```text
driver performance
deployment readiness
controller-family ranking
checkpoint promotion
success-rate verdict
fresh/generalization result
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
current-sim or high-fidelity validation verdict
```

## Falsified Claims

The branch falsifies or rejects the following shortcuts:

```text
1. M2529 falsified config-only/no-update smoke as sufficient repair evidence.
2. M2532 falsified command-conflict removal as sufficient mitigation repair:
   severity can regress even when road margin and command conflict improve.
3. M2534 falsified metric artifact as the explanation for the mitigation
   regression.
4. M2535 and M2537 falsified seed-254302-only repair as an acceptable route by
   requiring all mitigation-primary rows and retained proof gates.
5. M2537 falsified the current actor-head relaxation sweep as a complete
   mitigation-preserving fix: no candidate passed all protected proof gates.
6. M2538 rejected interpreting M2537 status_pass as proof-gate success.
```

## Failure Taxonomy Summary

Accepted failure classes:

```text
behavior_regression:
  the mitigation-primary surface still has one severity regression after M2537.

proof_washout:
  road-boundary and command-conflict retained proof pass while mitigation proof
  remains failing.

objective_overfit:
  the current repair objective can preserve public retained gates but still
  leaves mitigation severity non-regression unresolved.
```

Rejected failure classes for the branch evidence:

```text
contract_violation:
  all audited repair artifacts preserve observation shape 72, action shape 3,
  no hidden/oracle actor inputs, and no rule-switching controller mode.

lineage_invalid:
  source checkpoints, repaired checkpoints, candidate config, protected rows,
  and gate bindings remain traceable.

metric_artifact:
  the row-level severity regression is directly visible in protected smoke rows.

training_instability:
  M2532 and M2537 wrote finite behavior-changing checkpoints and traces.
```

Scenario sampling remains a risk because the protected proof panel is public
and narrow. It is not a fresh/generalization gate.

## Public Gate Overfit Risk

Risk level: `high`.

Reasons:

```text
1. The branch has now used M2529 no-update smoke plus two behavior-changing
   repair executions around the same protected public proof panel.
2. The remaining failure is the same mitigation-primary sentinel surface,
   seed 254302, after both M2532 and M2537.
3. M2537's candidate sweep shows a narrow tradeoff: stronger relaxations can
   reduce the mitigation severity delta but wash out retained command-conflict
   proof, while retained-gate candidates leave mitigation proof failing.
4. Continuing this branch would likely optimize public proof rows rather than
   create broader driver-like evidence.
5. Protected proof gates are still incomplete, so fresh/generalization,
   promotion, ranking, and performance claims remain blocked.
```

The overfit risk does not mean the evidence is useless. It means this branch
has done its job as a failure-surface diagnostic and should stop being the
main loop.

## Process Overhead

Process overhead is `high`.

Only M2532 and M2537 changed actor behavior. M2526-M2528, M2530-M2531,
M2533-M2536, and M2538 were design/materialization/audit/localization/synthesis
work. The overhead was justified until M2537 because M2532 reduced three proof
failures to one and M2536 approved exactly one bounded repair attempt.

After M2537, another direct public-row repair would have poor leverage. The
branch now needs a pivot to broader Route A evidence.

## Next Branch Decision

Decision: `pivot`.

Operational route:

```text
m2540-engineering-controller-route-a-baseline-and-interface-pivot-design
```

The next branch should combine the useful part of Route A with the
post-M2470 route plan:

```text
Route A baseline/failure taxonomy:
  baseline checkpoint list
  actor input/output contract
  public benchmark pack
  known failure taxonomy
  runtime/inference-cost report
  scenario-role metric report

Route C HF0 interface preparation:
  DynamicsBackend boundary
  reset/step API mapping
  time-step and actuator-latency contract
  state extraction boundary
  failure/status taxonomy
```

This pivot does not promote M2537, does not discard its evidence, and does not
claim driver performance. It changes the next work unit from public
protected-row repair to a broader baseline/interface preparation branch.

## Rules For The Pivot Branch

The pivot branch must preserve:

```text
actor input contract:
  human-view ego response, actuator state, previous commands, scene geometry,
  and recurrent/history state only

action contract:
  steer, throttle, brake

forbidden actor shortcuts:
  mu, mass, tire stiffness, brake scale, actuator tau, slip, tire force,
  oracle feasibility, AEB/AES/drift labels, controller mode, speed_ref,
  beta_target, path error, heading error, path curvature, TTC, required
  clearance, oracle stopping distance
```

The pivot branch should not start with another trainer or another protected-row
repair. It should first materialize the baseline/interface evidence map so the
next training or benchmark milestone is attached to a broader driver-like
claim surface rather than a single public proof row.

## Registered Follow-Up

M2539 registers:

```text
experiments/manifests/m2540-engineering-controller-route-a-baseline-and-interface-pivot-design.json
```

M2540 is design-only. It should define the artifacts and gate boundaries for
the new branch. It must not install or run external simulation, train, rank,
promote, compute success rates, or claim validation.
