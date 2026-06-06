# M2883 Engineering Controller Route C HF3 Chrono Next Dependency Gate Or Stop Design

## Metadata

- status: completed
- decision: `stop_route_c_hf3_chrono_under_source_unavailable_pivot_to_route_b_capability_prediction_panel_inventory_preflight`
- manifest: `experiments/manifests/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.json`
- design artifact: `docs/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.md`
- parent audit: `docs/m2882-engineering-controller-route-c-hf3-chrono-source-availability-result-audit.md`
- parent summary: `runs/m2881_engineering_controller_route_c_hf3_chrono_source_availability_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight.json`
- next: `m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight`

## Design Decision

M2883 selects exactly one next route:

```text
keep Route C/HF3 Chrono stopped under source_unavailable and pivot to Route B
capability-prediction panel inventory preflight
```

The formal decision is:

```text
stop_route_c_hf3_chrono_under_source_unavailable_pivot_to_route_b_capability_prediction_panel_inventory_preflight
```

This closes the current Chrono dependency branch as blocked by missing source,
not as failed validation. The accepted M2881/M2882 evidence remains:

```text
source root: /home/quyaonan/workspace/hf_backends/chrono/10.0.0/source
source root exists: false
CMakeLists.txt exists: false
outcome: source_unavailable_claim_safe
cmake command: /usr/bin/cmake
C++ command: /usr/bin/c++
```

Available toolchain commands are insufficient to admit configure/build while
the source root is missing.

## Rejected Alternatives

M2883 rejects these alternatives for the immediate next route:

```text
manual source provision: rejected because source has not been supplied
dependency acquisition execution: rejected because no explicit allowance exists
alternate backend contract design: rejected for now because it would be another
  dependency process branch without new controller-family or self-ID evidence
continuing Chrono configure/build/import/reset gates: rejected because source
  availability is false
full Route C branch stop without pivot: rejected because Route A/B still have
  available evidence-producing work
```

The selected route is therefore not another HF3 dependency-process milestone.
It moves the active work back to a current-simulator Route B evidence program.

## Route B Rationale

`docs/self-id-go-no-go-paper-route-plan.md` and
`docs/paper-route-finite-window-vs-gru-plan.md` both require a fair
L0/L1/L2/L3 comparison before paper-level self-ID claims. They also require
capability-prediction evidence before another training branch:

```text
future braking envelope
future yaw authority
future lateral acceleration response
actuator response lag proxy
recovery margin after maneuver
first-critical action quality
```

This is higher leverage than another design-only dependency step because it can
test whether deployable current/finite-window/recurrent observations actually
contain information about future capability before more PPO or promotion work.

## Claim Boundary

M2883 supports only this claim:

```text
Given the accepted source_unavailable Chrono result, the current Route C/HF3
Chrono branch should remain stopped and the next admitted milestone should be a
Route B capability-prediction panel inventory preflight.
```

M2883 does not claim:

```text
dependency execution readiness: false
source-build readiness: false
Chrono configure build install link/import reset or rollout readiness: false
high-fidelity validation readiness or result: false
driver performance: false
finite-window-vs-GRU verdict: false
self-ID evidence: false
current-sim verdict: false
controller winner selection or promotion: false
```

## M2884 Admission Contract

M2884 is admitted as a bounded read-only inventory/materialization preflight:

```text
m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight
```

M2884 must inspect existing artifacts and produce a machine-auditable candidate
panel for capability-prediction work. It must not train, reset, step, roll out,
rank controllers, promote checkpoints, or claim self-ID.

Required inventory questions:

```text
Which existing post-M2470 artifacts can provide source-diverse candidate rows?
Which rows have enough deployable observation/action/response history for L0/L1/L2/L3 features?
Which rows can support future-capability targets without exposing targets to actor input?
Which rows are stale protected public gates or package limitations and should stay guards?
Which gaps block a fair capability-prediction panel?
```

Admitted outputs:

```text
summary.json
candidate_panel_rows.csv
source_inventory_rows.csv
target_inventory_rows.csv
actor_contract_rows.csv
gate_rows.csv
claim_rows.csv
follow-up result-audit manifest
```

## Failure Taxonomy

Controlled or inactive after M2883:

```text
claim_boundary_violation: controlled by rejecting all dependency execution and validation claims
metric_artifact: controlled by keeping source availability as dependency-process evidence only
lineage_invalid: controlled by selecting one explicit next route
proof_washout: controlled by not converting missing source into HF3 readiness
```

Still active:

```text
source_unavailable: active for Chrono/HF3 until source is supplied or a later route is explicitly allowed
high_fidelity_dependency_gap: active because no HF3 source/build/reset gate has passed
self_id_gap: active because no fair L0/L1/L2/L3 capability-prediction panel has been materialized
scenario_sampling_failure: active until the panel inventory proves source diversity and row validity
behavior_regression: active because recent Route A closed-loop diagnostics remain weak
objective_overfit: active if M2884 only reuses stale public proof rows
```

## Public Gate Overfit Risk

Public-gate overfit risk is medium. The project has accumulated many guarded
public surfaces, package limitations, protected rows, and diagnostic-only
artifacts. M2884 must not treat those artifacts as paper proof. Its job is to
classify them into usable candidate rows, guards, stale/protected rows, or
missing data gaps.

The selected route is acceptable only if M2884 expands evidence toward a fair
capability-prediction panel. If it cannot find source-diverse rows with
deployable histories and legitimate future-capability targets, the next audit
must report that as a negative panel-inventory result instead of weakening the
actor contract.

## Forbidden Work

M2883 did not execute dependency or policy work. M2884 must also avoid:

```text
network fetch or clone
external dependency directory creation
package install
Chrono configure build install import or link probe
backend reset or step
policy action rollout replay validation training PPO ranking promotion
actor input expansion
hidden/oracle actor labels
driver-performance paper current-sim high-fidelity full-driver or self-ID claim
```

## Next Route

The next task is:

```text
m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight
```

M2884 should move from route decision to evidence inventory. It should produce
new panel artifacts or a concrete negative report explaining why existing
artifacts are insufficient for capability-prediction work.
