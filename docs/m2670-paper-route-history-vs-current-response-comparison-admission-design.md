# M2670 Paper Route History Vs Current Response Comparison Admission Design

## Metadata

- status: completed
- decision: `admit_protocol_materialization_preflight`
- manifest: `experiments/manifests/m2670-paper-route-history-vs-current-response-comparison-admission-design.json`
- design artifact: `docs/m2670-paper-route-history-vs-current-response-comparison-admission-design.md`
- parent synthesis: `docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md`
- governing route plan: `docs/post-m2470-route-plan.md`
- governing self-ID plan: `docs/self-id-go-no-go-paper-route-plan.md`
- governing finite-window plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- historical comparison controls: `docs/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.md`, `docs/m1199-paper-route-fair-comparison-pilot-run.md`, `docs/m1200-paper-route-fair-comparison-pilot-result-audit.md`, and `docs/m1205-paper-route-finite-window-gru-evidence-synthesis.md`
- follow-up manifest: `experiments/manifests/m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight.json`
- next: `m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight`

## Admission Decision

M2670 admits a bounded Route B protocol-materialization preflight. It does not
admit immediate training, PPO, rollout execution, controller-family ranking,
winner selection, promotion, private holdout, current-sim verdict, paper
verdict, finite-window-vs-GRU result, high-fidelity validation, full ideal
driver completion, or self-ID evidence.

The admission is needed because M2669 closed the Route A readiness loop:
readiness artifacts are integrated and packageable with limitations, but they
do not change driver capability evidence. The next useful evidence axis is a
fair history-vs-current-response comparison that can falsify the GRU/self-ID
hypothesis instead of assuming it.

## Governing Constraints

The post-M2470 route plan requires the project to separate engineering
controller packaging from paper-level self-ID evidence. Route B must make the
L0/L1/L2/L3 comparison falsifiable and must not claim L3 from aggregate success,
reset-only evidence, source-singleton positives, static materialization, single
protected rows, or current-sim readiness artifacts.

The self-ID go/no-go plan requires:

- same actor input boundary;
- same actuator-level output `[steer, throttle, brake]`;
- same budgets and seeds when training is later admitted;
- same public evals and no private holdout tuning;
- parameter count, inference cost, and latency reporting;
- source-diverse, outcome-relevant, terminal-boundary or delayed/ambiguous
  tasks before any strong self-ID claim.

The finite-window vs GRU plan adds one critical discipline rule: GRU is not the
default winner. If L1 or L2 matches L3, that is a valid engineering or paper
result rather than a failed experiment.

## Actor And Action Contract

All future variants admitted by this branch must use deployable actor inputs
only:

- ego kinematics and IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road, free-space, and obstacle geometry in ego frame;
- explicit finite-window command-response history or online recurrent hidden
  state.

Forbidden actor inputs for every controller family:

- hidden dynamics parameters such as `mu`, mass, CG, tire stiffness, brake
  scale, and actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, or friction margin;
- AEB, AES, drift-required, feasibility, controller mode, repair-target,
  taxonomy, gate, route-decision, or paper-verdict labels;
- TTC, reference trajectory, path error, heading error, path curvature,
  required clearance, oracle stopping distance, collision, success, progress,
  or any precomputed answer.

The action contract is fixed:

```text
u_t = [steer_command, throttle_command, brake_command]
```

## Comparison Matrix

The admitted comparison matrix is:

| Level | Profile | Required role | Admission notes |
| --- | --- | --- | --- |
| L0 | `L0_current` | current-frame substitution control | Current deployable frame only; no explicit history stack or recurrent hidden state. |
| L1 | `L1_one_step` | strong current-response baseline | Current deployable frame plus previous physical command and actuator state. |
| L2 | `L2_window_13` | 0.25s finite-window controller | Explicit command-response history, no online memory beyond the window. |
| L2 | `L2_window_25` | 0.5s finite-window controller | Same runtime and training protocol as other L2 windows. |
| L2 | `L2_window_50` | 1.0s finite-window controller | Must not be interpreted without current-tiled control. |
| L2 | `L2_window_100` | 2.0s finite-window controller | Must report latency and inference cost. |
| L2 control | `L2_current_tiled` | capacity/current-substitution control | Current frame tiled through the history window to isolate capacity and encoder effects. |
| L3 | `L3_online_gru` | recurrent-memory candidate | Online hidden state persists through the episode. |
| L3 control | `L3_reset_truncated_control` | recurrent-memory diagnostic | Hidden state reset every step or truncated to bounded windows; must verify reset semantics. |

M2670 does not rank these rows. It only admits them as the minimum fair matrix
needed before later evidence can say whether current-response, finite-window,
or recurrent memory is useful.

## Task Family Admission

The next protocol materialization must include rows for these task families:

| Task | Purpose | Admission requirement |
| --- | --- | --- |
| T1 reactive emergency avoidance | engineering baseline | L1/L2 matching L3 is an acceptable positive engineering result. |
| T2 delayed actuator/response feedback | history usefulness | Must measure adaptation latency and future capability prediction. |
| T3 diagnostic warmup plus obstacle reveal | deployable history signal | Warmup actions must be low-amplitude and deployable. |
| T4 same-current same-recent-window different-older-history | history beyond recent window | Current frame, previous command, actuator state, and recent K window must be matched. |
| T5 terminal-boundary near-constraint avoidance | mechanism and outcome relevance | Must report margin tails and source diversity, not aggregate success alone. |

The task family table is an admission design, not a claim that the existing
simulator already has sufficient task quality. M2671 must preserve a
`scenario_sampling_failure` stop path if any family cannot be materialized
without hidden labels, source-singleton positives, or cherry-picked public
rows.

## Fairness Gates

Any later execution route admitted from M2671 must preserve these fairness
gates:

- same deployable actor input boundary for all controller families;
- same action contract and actuator dynamics;
- same train/eval split, seeds, public gates, reward, and terminal metrics for
  a given task family;
- no private holdout tuning;
- no per-profile hyperparameter changes after seeing public results;
- parameter count, observation dimension, recurrent state dimension, CPU
  inference latency, and runtime reported;
- profile config rows must prove L0/L1/L2/L3 differ exactly as intended;
- L2 current-tiled rows must be trained/evaluated through the same runtime
  transform as ordinary L2 rows;
- L3 reset/truncated rows must prove reset/truncation semantics are honored in
  evaluation, not only in config metadata.

## Historical Pitfalls Carried Forward

The M1199 public pilot showed an L2-family trend, but M1200 and M1205 blocked
strong interpretation for two reasons:

- L2 window profiles were near-equivalent under the short public pilot;
- the original L3 reset diagnostic had reset-semantics mismatch and could not
  be used as valid recurrent-memory evidence.

M2670 therefore admits no M1199-style direct rerun until the M2671 protocol
materialization explicitly includes current-tiled L2 controls, corrected
reset/truncated L3 controls, and a claim boundary that keeps public pilot trend
separate from paper-level evidence.

## Failure Taxonomy And Stop Rules

Active risks:

- `contract_violation`: stop if any actor row exposes hidden dynamics, oracle
  labels, outcome labels, route labels, or controller-family labels as inputs.
- `scenario_sampling_failure`: stop if T2/T3/T4/T5 cannot be materialized with
  source-diverse, executable, P0-compatible task rows.
- `metric_artifact`: stop if reset/truncation or current-tiled controls are
  metadata-only and not enforced in runtime evaluation.
- `objective_overfit`: stop if the branch optimizes fixed public rows or
  repairs the same protected readiness rows instead of changing the evidence
  axis.
- `proof_washout`: stop if aggregate success is used to hide missing
  same-current, wrong-history, delayed-history, reset, or margin-tail evidence.

## Admitted Follow-Up

M2671 should materialize a machine-auditable protocol pack, not run the
comparison. Required future artifacts should include:

```text
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/summary.json
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/controller_family_rows.csv
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/task_family_rows.csv
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/fairness_gate_rows.csv
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/claim_boundary_rows.csv
runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/gate_matrix.csv
docs/m2671-paper-route-history-vs-current-response-comparison-protocol-materialization-preflight.md
```

M2671 may route later to implementation, audit, or synthesis. It must not run
reset, rollout, replay, validation, training, PPO, source build, adapter probe,
external simulation, ranking, winner selection, promotion, success-rate verdict
computation, driver-performance measurement, paper verdict, current-sim verdict,
high-fidelity validation, full ideal driver gate, or self-ID verdict.

## Claim Boundary

Allowed M2670 claim:

```text
The Route B history-vs-current-response comparison is admitted for protocol
materialization under a fair L0/L1/L2/L3 matrix with fixed actor/action
contracts, explicit current-tiled and reset/truncated controls, and no result
claim.
```

Rejected claims:

```text
driver capability improvement
controller-family ranking
finite-window superiority
GRU superiority
recurrent-belief advantage
level3 self-identification
paper verdict
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
```
