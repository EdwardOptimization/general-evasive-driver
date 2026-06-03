# M2486 High-Fidelity Interface Preparation Post-Smoke Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- decision: `promote_to_source_only_closed_loop_fixture_pilot_branch`
- manifest: `experiments/manifests/m2486-high-fidelity-interface-preparation-post-smoke-branch-synthesis.json`
- synthesis artifact: `docs/m2486-high-fidelity-interface-preparation-post-smoke-branch-synthesis.md`
- parent evidence window: `m2477` through `m2485`
- next milestone: `m2487-source-only-closed-loop-fixture-pilot-design`
- external high-fidelity simulation installed/imported/executed in M2486: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2486: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

M2477 allowed the high-fidelity interface route to continue only because the
next step would add executable adapter evidence rather than another interface
catalog. M2478-M2485 then produced the following scoped evidence:

```text
M2478:
  source-only FourWheelDriftModel through HF0 backend
  reset/step count: 1 / 2
  observation/action shape: 72 / 3
  per-wheel forces and fault scales: diagnostics only
  external high-fidelity simulation required/imported/run: false

M2479:
  HF0 scenario taxonomy mapping design
  roles: stable avoidable, stable AES, drift-required recovery,
         hidden-dynamics robustness, unavoidable mitigation
  labels and feasibility classes: metadata only

M2480:
  materialized surface-role matrix
  rows: 10
  surfaces: current_sim_autodrift_hf0, source_only_four_wheel_hf0
  support statuses: supported 5, limited_fixture 5, blocked 0
  observation/action shape: 72 / 3

M2481:
  fixture admission design for five limited rows
  current-sim limited rows: diagnostic/reference only
  source-only four-wheel limited rows: admitted for fixture catalog

M2482:
  checked fixture catalog
  rows: 10
  baseline_reference: 5
  diagnostic_reference_only: 2
  admitted_for_materialization: 3
  labels and hidden/oracle fields: metadata only

M2483:
  bounded source-only fixture smoke design
  admitted source-only fixtures: stable_aes, drift_required_recovery,
                                  unavoidable_mitigation
  actions: canned adapter-smoke actions only

M2484:
  source-only fixture smoke implementation preflight
  result_class: hf0_source_only_fixture_smoke_pass
  fixtures/resets/steps: 3 / 3 / 6
  observation/action shape: 72 / 3
  wheel-force diagnostic counts: [4, 4, 4, 4, 4, 4]
  policy_action: false
  training/ranking/winner/verdict claims: false

M2485:
  result audit accepts M2484 as complete source-only fixture smoke evidence
  rejects driver performance, validation, current-sim verdict, paper evidence,
  finite-window-vs-GRU evidence, and self-ID interpretations
  routes to M2486 branch synthesis
```

The post-M2470 route plan remains the governing route constraint: current-sim
readiness work should remain diagnostic, and high-fidelity preparation should
not become another static infrastructure loop.

## Supported Claims

Supported:

```text
The HF0 actor/action boundary is locally machine-checkable.

The canonical P0 actor observation shape remains 72.

The deployed action contract remains shape 3:
  [steer_command, throttle_command, brake_command]

The current-sim and source-only four-wheel surfaces can both be represented
through the HF0 interface without adding hidden or oracle actor inputs.

The source-only four-wheel surface now has checked fixture coverage for:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation

M2484 proves the admitted source-only fixtures can reset and accept two bounded
steps each through the HF0 interface with diagnostics kept outside ActorView.

The branch has enough interface scaffolding to design a bounded closed-loop
pilot over the admitted source-only fixtures.
```

## Falsified Or Unsupported Claims

Still unsupported:

```text
Driver capability improved:
  unsupported. M2478-M2485 executed no deployable policy action, measured
  rollout, training, replay, PPO, checkpoint promotion, controller ranking, or
  winner selection.

High-fidelity validation readiness:
  blocked. No external high-fidelity backend was installed, imported, run, or
  smoke-tested. The source-only FourWheelDriftModel adapter is not external
  high-fidelity validation.

Current-sim benchmark readiness:
  unsupported. Current-sim remains a diagnostic/mining layer and the source-only
  branch did not repair stable-AES current-sim readiness.

Finite-window-vs-GRU evidence:
  unsupported. No fair controller-family matrix, history-necessity test, or
  recurrent comparison ran.

Level-3 self-identification:
  unsupported. No terminal-boundary self-ID proof or wrong-history comparison
  ran.

Paper-level evidence:
  unsupported. The branch is interface preparation and bounded smoke only.
```

## Failure Taxonomy Summary

Observed or active:

```text
contract_violation:
  controlled. M2478 and M2484 preserve observation shape 72, action shape 3,
  and diagnostics outside ActorView. No contract violation is observed.

lineage_invalid:
  controlled by manifests, explicit parent artifacts, queue status, scoreboard,
  and research log updates.

metric_artifact:
  medium. It becomes high if the M2484 canned smoke is treated as policy
  performance. M2485 rejects that interpretation and M2486 keeps the scope
  infrastructure-only.

scenario_sampling_failure:
  active but inherited. The current-sim stable-AES readiness issue is not fixed
  by source-only fixture smoke.

objective_overfit:
  medium. The branch avoided public current-sim row optimization, but continued
  HF0 metadata or catalog work would now risk optimizing process gates instead
  of producing closed-loop evidence.

dependency/API blocker:
  active. Chrono-family backend work remains plausible but locally nonexecutable
  under the current no-install/no-import gate because pychrono/projectchrono is
  absent.
```

Not observed:

```text
private holdout contamination
checkpoint promotion without proof/generalization gates
controller-family ranking
winner selection
actor input oracle leakage
```

## Public Gate Overfit Risk

Risk entering M2486: `medium`.

Reason:

```text
M2478-M2485 produced useful HF0 source-only scaffolding, but the branch has
again accumulated multiple interface/taxonomy/fixture milestones. Another
catalog, audit, or static design would likely improve bookkeeping without
changing driver or paper evidence.
```

Risk after M2486: `medium-low` only if the next branch leaves interface
preparation and heads toward bounded closed-loop evidence.

Mitigation:

```text
Close the high_fidelity_interface_preparation branch for now.

Do not continue directly to another HF0 metadata/catalog task.

Open a new source_only_closed_loop_fixture_pilot branch whose first design gate
must specify an actor source, rollout scope, leak checks, metrics, and a follow-
up implementation preflight.

Keep source-only pilot evidence separate from high-fidelity validation and
paper-level evidence.
```

## Next Branch Decision

Decision:

```text
promote_to_source_only_closed_loop_fixture_pilot_branch
```

Rationale:

```text
Stopping now would leave the project with a clean interface but no route back
to deployable closed-loop driver evidence.

Continuing the HF0 interface branch would repeat the post-M2470 problem: useful
infrastructure becoming the main loop.

Direct external-backend implementation remains blocked by local dependency/API
availability and by the current no-install/no-import gate.

The next bounded evidence-producing route is a source-only closed-loop fixture
pilot. It can reuse the M2484 admitted fixtures, preserve the same P0 actor
contract, and prepare an implementation preflight that executes deployable
policy actions rather than canned adapter-smoke actions.
```

Required next constraints:

```text
M2487 must be a design gate only.

M2487 must define the bounded closed-loop pilot over the three M2484 admitted
source-only fixtures.

M2487 must preserve observation shape 72 and action shape 3.

M2487 must keep fixture labels, scenario labels, feasibility classes, hidden
dynamics, wheel diagnostics, oracle labels, TTC, required clearance, reward
terms, and success/progress labels out of actor input.

M2487 must specify the actor source and admission rule before any implementation
preflight. It must not silently use a canned controller as a policy result.

M2487 must not train, rank controllers, select a winner, or claim driver
performance, high-fidelity validation, paper evidence, finite-window-vs-GRU
evidence, or level-3 self-identification.
```

## Evidence Scope

M2486 is synthesis only. It closes the current HF0 interface preparation loop
and registers a bounded route back toward closed-loop evidence. It does not
execute policy action, run measured validation, train, replay, use PPO, rank
controllers, select a winner, promote a checkpoint, or make a driver/paper/
validation verdict.
