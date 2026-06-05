# M2785 Engineering Controller Route A Source-Only Belief-Stress Candidate Closed-Loop Delta Panel Result Audit

## Metadata

- status: completed
- decision: `accept_m2784_route_to_source_only_belief_stress_branch_synthesis`
- manifest: `experiments/manifests/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.json`
- audit doc: `docs/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.md`
- parent summary: `runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/summary.json`
- parent gate matrix: `runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/gate_matrix.csv`
- parent paired execution rows: `runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/paired_execution_rows.csv`
- parent paired delta rows: `runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/paired_delta_rows.csv`
- follow-up manifest: `experiments/manifests/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.json`
- next: `m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis`

## Audit Result

M2785 accepts M2784 as complete and claim-safe source-only diagnostic evidence:

```text
M2784 status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
failed_gate_ids: none
paired_execution_rows: 144
paired_delta_rows: 72
proof_gate_rows: 12
generalization_gate_rows: 6
promotion_guard_rows: 4
actor_guard_rows: 7
mitigation_guard_rows: 8
claim_rows: 11
gate_matrix_rows: 22
```

Checkpoint lineage is auditable:

```text
source checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
source checkpoint hash:
  e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
candidate checkpoint:
  runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt
candidate checkpoint hash:
  96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
```

M2784 ran source-only closed-loop rows for the M2655 source checkpoint and the
M2782 candidate checkpoint across 18 belief-stress curriculum buckets, 4 seeds,
and an 80-step horizon. This is fresh Route A diagnostic evidence, not
validation, ranking, promotion, performance, paper, high-fidelity, full-driver,
or self-ID evidence.

## Diagnostic Delta Accounting

The M2784 paired delta rows are accepted as diagnostic row deltas only:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  mean: 0.0000268466
  median: 0.0000509576
  positive rows: 40
  negative rows: 32

candidate_minus_source_minimum_road_margin_m:
  mean: 0.0023105305
  median: 0.0024221779
  positive rows: 72
  negative rows: 0

candidate_minus_source_final_speed_mps:
  mean: -0.0012789392
  median: -0.0020687566
  positive rows: 15
  negative rows: 57

candidate_minus_source_max_abs_yaw_rate:
  mean: -0.0003123776
  median: -0.0002709007
  positive rows: 0
  negative rows: 66
  zero rows: 6

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  median: 0.0
  zero rows: 72

mean_action_delta_l1:
  mean: 0.0003095307
  median: 0.0003061991
  positive rows: 72
```

These deltas show small source-only candidate movement, with consistent road
margin and yaw-rate diagnostic shifts and mixed obstacle-clearance deltas. They
do not establish a winner, repair success, promotion basis, success-rate
verdict, driver-performance claim, paper claim, or self-ID result.

## Actor Boundary

M2784 preserved the deployed actor contract:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input required: false
actor-visible stress/admission/curriculum labels: false
actor-visible role/dynamics/outcome/success/progress/route/verdict labels: false
finite observation/action gates: pass
```

M2785 makes no actor input or action contract change. M2784 labels and paired
delta metadata are evaluator-side artifacts only.

## Gate Separation

M2784 separated gate tiers:

```text
proof gates:
  12/12 pass

generalization gates:
  6/6 pass

promotion guards:
  4/4 pass, blocking promotion/selection/verdict
```

The proof and generalization rows establish artifact completeness, paired
row accounting, role/axis/stress/seed coverage, and actor-contract preservation
for the source-only diagnostic panel. They do not establish a validated driver.

## Mitigation And Claim Boundary

M2784 mitigation reference rows are guarded:

```text
mitigation guard rows: 8
ordinary denominator allowed: false
included in paired execution rows: false
included in delta rows: false
```

M2784 claim rows reject:

```text
validation result
ranking result
winner selection
checkpoint promotion
success-rate verdict
driver performance
paper result
current-sim verdict
high-fidelity validation
level3 self-identification
```

M2785 accepts only the allowed claim that paired source-only diagnostic
artifacts are complete and claim-safe.

## Route Decision

M2785 routes to M2786 branch synthesis. The M2778-M2785 belief-stress
short-training branch now has admission-pack materialization, design, bounded
candidate checkpoint preflight, audit, paired source-vs-candidate closed-loop
diagnostic deltas, and this audit. The next step should synthesize the branch
before any additional execution, repair, ranking, promotion, or another
process-only milestone.

M2786 must answer the required synthesis questions, preserve the M2784
diagnostic scope, and decide whether to continue, pivot, stop, or package the
branch with limitations. It must not claim validation, ranking, promotion,
performance, paper evidence, high-fidelity validation, full ideal driver
completion, or level3 self-identification.

## Rejected Claims

M2785 does not support:

```text
repair success
driver performance
validation readiness
validation result
ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```
