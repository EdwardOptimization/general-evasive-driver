# M2708 Engineering Controller Protected Runner Simulator/Workload Support Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_current_m1690_workload_fixture_support_design`
- manifest: `experiments/manifests/m2708-engineering-controller-protected-runner-simulator-workload-support-branch-synthesis.json`
- synthesis artifact: `docs/m2708-engineering-controller-protected-runner-simulator-workload-support-branch-synthesis.md`
- parent audit: `docs/m2707-engineering-controller-protected-runner-simulator-workload-support-materialization-result-audit.md`
- parent support summary: `runs/m2706_engineering_controller_protected_runner_simulator_workload_support/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design.json`
- next: `m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design`

## Evidence Summary

M2691-M2707 turned a Route A protected mitigation blocker into an explicit
runner support boundary, but it did not create protected execution evidence.
The branch contains one bounded diagnostic execution on the off-track side and
then a protected-side adapter/support chain that remained no-execution.

Accepted branch facts:

```text
M2691 source-diverse target panel:
  status_pass: true
  target_panel_rows: 19
  offtrack_targets: 9
  protected_targets: 10
  execution: false

M2693 bounded diagnostic execution:
  status_pass: true
  executed offtrack rows: 9
  protected rows recorded as non-executable failures: 10
  offtrack diagnostic success: 0/9
  off_track: 7/9
  speed_too_low: 2/9
  measured validation: false
  ranking/performance verdict: false

M2695 executable-surface bridge:
  status_pass: true
  protected_bridge_rows: 10
  exact current-runner executable candidates: 0
  unbridgeable_rows: 10

M2697 protected runner-spec generation:
  status_pass: true
  protected_runner_spec_rows: 12
  protected_workload_candidate_rows: 12
  spec_traceability_rows: 160
  exact M1690 workload matches: 0
  protected workload candidates outside current M1690: 12

M2700 adapter contract:
  status_pass: true
  adapter_candidate_mapping_rows: 12
  adapter_traceability_rows: 160
  exact M1690 workload matches: 0
  execution-admitted rows: 0

M2703 execution admission:
  status_pass: true
  execution_admission_candidate_rows: 12
  execution_admission_rejection_rows: 12
  execution_admission_blocked_no_current_m1690_workload: 12
  execution_admission_admitted_count: 0
  exact M1690 workload matches: 0

M2706 simulator/workload support:
  status_pass: true
  support_candidate_rows: 12
  support_blocker_rows: 12
  support_traceability_rows: 160
  support_materialized_candidate_requires_new_workload_row: 12
  support_ready_existing_m1690_workload: 0
  exact M1690 workload matches: 0
  execution-admitted source rows: 0

M2707 result audit:
  accepts M2706 complete and claim-safe as support materialization
  rejects direct protected execution
  routes to branch synthesis
```

The consistent protected-side result is:

```text
protected targets accounted: 10/10
candidate/support rows: 12
support-required rows: 12/12
support-ready rows: 0
exact M1690 matches: 0
execution-admitted rows: 0
```

Actor and claim boundaries remained intact throughout the branch:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
target/protected/blocker/route/verdict labels actor-visible: false
protected rows in ordinary success denominators: false
training/PPO/ranking/promotion/performance claims: false
paper/current-sim/high-fidelity/full-driver/self-ID claims: false
```

## Supported Claims

M2708 supports these bounded claims:

- The Route A protected runner support branch has a complete, auditable
  interface lineage from source-diverse protected targets to runner specs,
  adapter rows, execution-admission rows, and support rows.
- The current runner cannot execute the protected mitigation rows yet: M2706
  preserves 0 support-ready existing M1690 rows, 0 exact M1690 workload
  matches, and 0 execution-admitted source rows.
- The missing boundary is now concrete enough to design a current-M1690
  workload row and simulator fixture support contract.
- The actor/action contract is preserved: P0 observation 72, action 3,
  steer/throttle/brake output, no hidden/oracle actor input, and no
  actor-visible protected labels.
- A single bounded M2709 design route is admissible because it can change the
  next admission decision if it defines exact workload/fixture rows for M2710
  materialization.

## Falsified Or Rejected Claims

M2708 rejects the following claims from M2691-M2707:

- M2693 proves protected mitigation behavior. It does not: protected rows were
  recorded as `source_not_executable_in_current_runner`.
- M2697 protected workload candidates are current M1690 workload rows. They are
  not: M2697 records 0 exact M1690 workload matches.
- M2700 adapter rows or M2703 execution-admission rows are execution rows.
  They are not: M2700 admits 0 execution rows and M2703 rejects 12/12 rows.
- M2706 support rows are behavior, validation, or performance evidence. They
  are not: all 12 rows require new workload-row support and remain no-execution.
- The branch supports repair success, driver performance, validation
  readiness/result, current-sim verdict, high-fidelity validation, paper
  evidence, full ideal driver completion, finite-window-vs-GRU conclusions,
  current-response sufficiency, or level3 self-identification.
- Another design/materialization/audit loop is admissible unless it can change
  exact workload admission or support readiness.

## Failure Taxonomy Summary

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle
  input, actor-invisible target/protected/blocker/route/verdict labels, and
  protected rows outside denominators remain preserved.
- `lineage_invalid`: not observed. M2691-M2707 preserve source-diverse panel,
  protected target, runner-spec, adapter, execution-admission, support, and
  M1690 schema lineage.
- `metric_artifact`: controlled. The branch does not rank, compute verdict
  metrics, or promote from support rows. M2693 off-track execution metrics
  remain diagnostic only.
- `scenario_sampling_failure`: active. Current M1690 executable workload rows
  still do not cover protected mitigation runner candidates.
- `behavior_regression`: active/incomplete. Protected mitigation behavior
  remains unmeasured because no protected row is execution-admitted.
- `objective_overfit`: high if the next step is another static support hop
  that cannot change workload admission. Controlled only if the next step
  defines exact current-M1690 workload/fixture support rows or stops/pivots.
- `proof_washout`: controlled. The 0 support-ready, 0 exact M1690, and 0
  admitted-row blockers remain explicit.

## Public-Gate Overfit Risk

The protected support branch has high process-overhead risk. Since M2695 the
branch has produced bridge, runner-spec, adapter-contract, execution-admission,
support-design, support-materialization, and support-audit artifacts. These
are useful because each narrowed the blocker, but most did not create new
closed-loop data.

The overfit risk is unacceptable for any next milestone that only restates:

```text
protected rows are not exact M1690 workload rows
support rows are not execution rows
protected rows remain outside denominators
```

The overfit risk is lower for one specific design step: a current-M1690
workload row and simulator fixture support design. That route can change the
next admission decision because it must define how the 12 support-required rows
would become exact current-runner workload/fixture rows in a later
materialization, or explicitly prove that they cannot.

If M2709 cannot define that contract without hidden/oracle actor inputs,
actor-visible protected labels, denominator leakage, or fabricated M1690
matches, the branch should stop or pivot instead of continuing.

## Next Branch Decision

Decision:

```text
continue_to_current_m1690_workload_fixture_support_design
```

M2708 chooses `continue`, not because M2706/M2707 are driver evidence, but
because the blocker is now precise enough for one bounded design that can
change execution admission. The allowed next route is:

```text
m2709-engineering-controller-protected-runner-current-m1690-workload-fixture-support-design
```

M2709 must design a no-execution contract for:

- current-M1690 workload row source accounting;
- protected workload fixture row schema;
- simulator fixture support row schema;
- support candidate to fixture mapping rows;
- exact-match admission/rejection rows;
- traceability rows preserving 10/10 protected targets;
- actor-contract guard rows;
- claim-boundary rows;
- gate rows for M2710 materialization.

M2709 must explicitly decide what M2710 would need to materialize before any
protected execution route can be considered. It must not reset, step, roll out,
replay, validate, train, run PPO, rank, promote, compute success-rate verdicts,
or claim repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity validation, full ideal driver completion, or self-ID.

If M2709 cannot show that a workload/fixture materialization can change exact
M1690 support readiness without violating the actor or claim boundary, the
branch should stop or pivot rather than continuing into another process chain.

## Claim Boundary

Allowed M2708 claim:

```text
M2691-M2707 synthesize into a concrete protected runner support blocker:
all protected support candidates require current-M1690 workload row and
simulator fixture support before protected execution admission can be
considered.
```

Rejected claims:

```text
protected execution result
protected mitigation preservation result
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```

M2708 did not execute reset, step, rollout, replay, validation, training, PPO,
private holdout, ranking, winner selection, promotion, or verdict computation.
