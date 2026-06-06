# M2837 Engineering Controller Post Route C HF3 Stop Evidence-Producing Branch Selection Design

## Metadata

- status: completed
- decision: `select_route_a_post_route_c_hf3_stop_fresh_source_diverse_closed_loop_evidence_preflight`
- manifest: `experiments/manifests/m2837-engineering-controller-post-route-c-hf3-stop-evidence-producing-branch-selection-design.json`
- design artifact: `docs/m2837-engineering-controller-post-route-c-hf3-stop-evidence-producing-branch-selection-design.md`
- parent audit: `docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-refresh-or-stop-result-audit.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2838-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-preflight.json`
- next: `m2838-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-preflight`

## Design Premise

M2836 accepted M2835 and keeps Route C/HF3 stopped under M2638 until a valid
source root, approved package route, dependency acquisition manifest, or
alternate backend contract is supplied. Another Route C dependency artifact is
therefore not an evidence-producing next step.

The next useful move should produce driver evidence, not more dependency
process. M2837 selects Route A over Route B as the immediate branch:

```text
selected route: Route A engineering controller evidence
selected follow-up: fresh source-diverse closed-loop diagnostic execution
reason: Route A can immediately produce bounded closed-loop data with existing
  runner infrastructure while preserving actor 72/action 3 and no hidden/oracle
  actor input
Route B deferred because: paper/controller-family comparison is important but
  should follow a concrete post-stop evidence refresh rather than another
  process-only selection milestone
Route C stopped because: M2638 source dependency remains unavailable
```

M2837 is design-only. It does not reset, step, roll out, validate, train, rank,
promote, import, build, probe, or mutate dependencies. It selects a bounded
follow-up that can produce new Route A diagnostic rows.

## Candidate Surface Selection

M2837 inspected the current M1690 executable workload and excluded already used
Route A `L3_online_gru` task-source ids from:

```text
M2737 post-negative source-diverse bounded execution
M2759 post-cross-axis negative action-response containment probe execution
M2807 post-clearance non-same-repair cross-axis bounded execution
M2816 post-action-response recoverability-window instrumented execution
M2828 post-package source-diverse closed-loop evidence expansion
```

The live M1690 workload has:

```text
available L3_online_gru rows with config/checkpoint present: 72
previously used task-source ids across the exclusion set: 43
unused task-source ids available: 29
unused T4 ids: 13
unused T5 ids: 16
```

M2837 fixes exactly 16 unused M1690 `L3_online_gru` task-source ids for M2838,
balanced across T4 and T5:

```text
m1680-spec-0012  T4  t4_capability_step_temporal|capability_step_down mapping_window_unspecified
m1680-spec-0019  T4  t4_capability_step_temporal|capability_step_down mapping_window_unspecified
m1680-spec-0020  T4  t4_staged_warmup_capability|capability_step_up   mapping_window_unspecified
m1680-spec-0024  T4  t4_actuator_delay_response|actuator_delay_step   mapping_window_unspecified
m1680-spec-0025  T4  t4_actuator_delay_response|capability_step_up    mapping_window_unspecified
m1680-spec-0027  T4  t4_staged_warmup_capability|capability_step_up   mapping_window_unspecified
m1680-spec-0028  T4  actuator_delay_step|capability_step_up           reveal_plus_4
m1680-spec-0029  T4  actuator_delay_step|t4_capability_step_temporal  mapping_window_unspecified
m1680-spec-0054  T5  actuator_delay_step|t5_near_boundary_warmup      reveal_plus_4
m1680-spec-0055  T5  capability_step_down|t5_near_boundary_warmup     decision_minus_24
m1680-spec-0056  T5  curved_boundary_obstacle|t5_boundary_axis_retarget decision_minus_32
m1680-spec-0057  T5  actuator_delay_step|t5_near_boundary_warmup      reveal_plus_4
m1680-spec-0059  T5  curved_boundary_obstacle|t5_boundary_axis_retarget decision_minus_32
m1680-spec-0060  T5  actuator_delay_step|t5_near_boundary_warmup      reveal_plus_4
m1680-spec-0061  T5  capability_step_down|t5_near_boundary_warmup     decision_minus_24
m1680-spec-0062  T5  curved_boundary_obstacle|t5_boundary_axis_retarget decision_minus_32
```

Selection rules:

```text
profile_name: L3_online_gru
config_exists: true
checkpoint_exists: true
profile_specific_tuning: false
used in M2737/M2759/M2807/M2816/M2828: false
actor input change required: false
hidden/oracle actor input required: false
private holdout used: false
```

Diagnostic grouping is artifact-only:

```text
T4 actuator response/capability:
  m1680-spec-0012, 0019, 0020, 0024, 0025, 0027, 0028, 0029

T5 near-boundary/capability/curved-obstacle:
  m1680-spec-0054, 0055, 0056, 0057, 0059, 0060, 0061, 0062
```

These tags are not actor inputs, rewards, rank groups, success labels, or
verdict labels.

## Follow-Up Requirements

M2838 must be an implementation plus bounded execution preflight. It should
materialize a new module:

```text
src/autodrift/engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight.py
```

M2838 should execute exactly one diagnostic rollout per resolved fixed row,
write failure rows instead of substituting candidates, and register a result
audit before interpretation. It must use:

```text
output dir:
  runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_evidence_preflight/

eval_seed_base:
  283800

device:
  cpu
```

Required output families:

```text
summary.json
selected_candidate_rows.csv
execution_candidate_resolution_rows.csv
candidate_execution_rows.csv
candidate_execution_failure_rows.csv
scenario_role_metric_rows.csv
failure_taxonomy_rows.csv
prior_surface_exclusion_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2838-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-preflight.md
experiments/manifests/m2839-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-result-audit.json
```

M2838 may record reset, step, policy action, and rollout fields only for the
fixed 16 diagnostic rows. It must not replay, validate, train, run PPO, build
source, probe adapters, import external simulators, start external backends,
rank, select winners, promote checkpoints, compute success-rate verdicts, or
claim driver performance.

## Actor Contract Boundary

The selected Route A preflight does not change the deployed actor:

```text
observation shape: 72
action shape: 3
actor-visible extractor: ActorView only
hidden/oracle actor input detected: false
labels actor visible: false
diagnostics actor visible: false
route/source/stress labels actor visible: false
```

Allowed actor-visible information remains only deployable observation:

```text
ego kinematics and IMU-like response
steering throttle brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
recurrent/history state
```

Forbidden actor-visible information remains hidden dynamics, labels, and rule
answers including `mu`, mass, tire stiffness, brake scale, actuator tau, slip,
tire force, oracle feasibility, AEB/AES/drift labels, controller mode,
speed_ref, beta_target, path error, heading error, path curvature, TTC,
required clearance, oracle stopping distance, reward terms, collision/success
labels, progress labels, route labels, and selected-platform state.

## Supported Claims

M2837 supports only:

```text
Route C/HF3 remains stopped under M2638.

The immediate next step should produce Route A closed-loop diagnostic data
rather than another Route C dependency artifact.

The fixed M2838 16-row surface is disjoint from M2737, M2759, M2807,
M2816, and M2828 task-source ids.

M2838 is admitted as a bounded diagnostic execution preflight, not as
validation, ranking, performance, paper, current-sim, high-fidelity,
full-driver, or self-ID evidence.
```

## Rejected Claims

M2837 rejects:

```text
Route C dependency readiness
high-fidelity validation readiness
driver performance
success-rate verdict
controller-family ranking
source-family ranking
scenario-role ranking
winner selection
checkpoint promotion
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation result
level3 self-identification
full ideal driver completion
```

## Next

Route to:

```text
m2838-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-closed-loop-evidence-preflight
```

M2838 must produce new closed-loop diagnostic rows or fail with explicit
failure rows. It must not weaken M2638, reuse M2828's exact surface, change the
actor contract, or claim validation/performance/paper/self-ID results.
