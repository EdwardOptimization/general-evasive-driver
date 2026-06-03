# M2536 Engineering Controller Failure-Surface Mitigation-Preserving Repair Branch Synthesis

- status: completed
- synthesis decision: `continue`
- operational decision: `continue_to_mitigation_preserving_repair_execution_preflight`
- manifest: `experiments/manifests/m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.json`
- synthesis artifact: `docs/m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md`
- parent design: `docs/m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design.md`
- next milestone: `m2537-engineering-controller-failure-surface-mitigation-preserving-repair-execution-preflight`
- external high-fidelity simulation installed/imported/executed in M2536: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2536: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2536: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

M2526-M2535 is a Route A failure-surface intervention branch. It has produced
one behavior-changing repair result and several process artifacts around that
result.

Evidence-producing artifacts:

```text
M2529 negative no-update repair smoke:
  45 protected/reference rows matched
  7 protected gate evaluations
  contract/no-oracle/no-ranking gates passed
  road-boundary, mitigation, and command-conflict proof gates failed
  status_pass true means artifact execution, not repair success

M2532 guarded repair execution:
  4500 telemetry rows
  45 post-repair protected/reference rows
  7 protected gate evaluations
  repaired checkpoint written under M2532 run directory
  checkpoint_behavior_changed true
  road_boundary_proof passed: 10/10 improved, 0 regressed
  command_conflict_proof passed: 15/15 improved, 0 regressed
  mitigation_proof failed: 4/5 improved, 1 regressed

M2534 localization:
  localized the single remaining mitigation regression to seed 254302
  all mitigation rows improved road margin
  all mitigation rows improved command conflict
  metric_artifact_detected false
```

Process and scaffolding artifacts:

```text
M2526 design:
  defined road-boundary, mitigation, and command-conflict intervention targets

M2527 materialization:
  wrote 45 protected/reference rows and 7 gate rows

M2528 config materialization:
  wrote immutable candidate config and protected gate bindings

M2530 audit:
  accepted M2529 negative no-update smoke

M2531 design:
  required actual guarded repair execution after no-update evidence

M2533 audit:
  accepted M2532 partial guarded repair evidence and rejected promotion

M2535 design:
  converted M2534 localization into retained proof gates and all-mitigation-row
  severity non-regression guardrails
```

Actual capability change:

```text
M2532 demonstrated that a bounded source-only actor-head repair can change
closed-loop behavior while preserving the 72/3 no-oracle actor contract and can
fix two protected proof surfaces. It did not produce a complete driver-like
repair because mitigation proof still failed and fresh/generalization remains
deferred.
```

## Supported Claims

Supported within Route A diagnostic scope:

```text
1. The failure-surface harness is executable and traceable.
2. The P0 actor contract remains preserved across the branch:
   observation shape 72, action shape 3, no hidden/oracle actor inputs, no
   rule-switching controller mode.
3. M2532 produced behavior-changing source-only repair evidence.
4. Road-boundary and command-conflict protected proof surfaces can be improved
   by the current repair mechanism.
5. The remaining blocker is narrower than M2529: mitigation severity
   non-regression on one low-baseline unavoidable-mitigation row.
6. M2535's mitigation-preserving objective is strong enough to justify one
   bounded execution attempt, because it adds group-level retained gates and
   explicitly forbids seed-only repair.
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

The branch falsifies or rejects several shortcuts:

```text
1. M2529 falsified config-only/no-update smoke as sufficient repair evidence.
2. M2532 falsified the idea that command-conflict removal alone is sufficient:
   mitigation severity can regress even when road margin and command conflict
   improve.
3. M2533 rejected treating `status_pass` as full proof-gate success.
4. M2534 rejected metric artifact as the explanation for the mitigation
   regression.
5. M2535 rejected seed `254302` as a sole tuning target.
```

## Failure Taxonomy Summary

Observed failure classes:

```text
behavior_regression:
  M2532 left one mitigation-primary row with severity_delta +0.674427724901157.

proof_washout:
  road-boundary and command-conflict proof passed while mitigation proof failed.

objective_overfit:
  M2534 classified the coarse command-conflict projection as objective weakness
  because it removed simultaneous throttle-brake without enforcing mitigation
  severity non-regression.

scenario_sampling_failure:
  risk only. The protected panel is public and only five mitigation seeds; it
  cannot support promotion or driver-performance claims.
```

Rejected failure classes:

```text
contract_violation:
  actor contract 72/3 and no-oracle boundary remained preserved.

lineage_invalid:
  source checkpoint, repaired checkpoint, candidate config, protected rows, and
  gate artifacts remain traceable.

metric_artifact:
  row-level artifacts show the severity regression directly.

training_instability:
  M2532 wrote a finite behavior-changing checkpoint and traces.
```

## Public Gate Overfit Risk

Risk level: `medium-high`.

Reasons:

```text
1. The next repair would be the second behavior-changing public protected-gate
   repair in this branch and the third repair-like step if M2529 no-update
   smoke is counted as a repair attempt.
2. The protected proof panel is public and narrow: 15 primary rows plus
   reference context, with only 5 mitigation-primary seeds.
3. M2535 reduces seed-only overfit risk by requiring all mitigation-primary
   rows and retained road-boundary/command-conflict gates, but it does not add
   fresh/generalization evidence.
4. If M2537 passes protected proof, the next route must be fresh/generalization
   design before any promotion or performance claim.
5. If M2537 fails mitigation proof or washes out retained gates, the branch
   must synthesize/pivot rather than continue public-gate repair.
```

## Process Overhead

Process overhead is `medium-high`.

The branch needed design, materialization, config binding, no-update smoke,
result audit, execution design, execution, result audit, localization, repair
design, and this synthesis. Only M2532 changed driver behavior. M2529 and M2534
were useful evidence, but not new capability. The overhead is justified for one
more bounded execution only because M2532 reduced the failure surface from
three failed proof gates to one and M2535 added anti-overfit constraints.

## Next Branch Decision

Decision: `continue`.

Operational route:

```text
m2537-engineering-controller-failure-surface-mitigation-preserving-repair-execution-preflight
```

M2537 is admitted with these constraints:

```text
1. It may run bounded source-only repair execution inside the M2537 run
   directory only.
2. It must start from the M2532 repaired checkpoint and keep that checkpoint,
   the M2528 candidate config, and active configs immutable.
3. It must write candidate-sweep evidence so rejected candidates remain visible.
4. It must pass or fail retained road-boundary, retained command-conflict, and
   mitigation-preserving proof separately.
5. It must not rank controllers, select a winner, promote, compute success
   rate, or claim validation/performance/paper evidence.
```

Mandatory route after M2537:

```text
if protected proof passes:
  route to fresh/generalization design, not promotion

if mitigation proof fails or retained gates wash out:
  route to branch synthesis or pivot, not another public-gate repair

if artifacts are incomplete but contract is preserved:
  route to artifact repair

if actor contract is violated:
  stop the branch and repair contract before any further driver claim
```
