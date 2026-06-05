# M2797 Engineering Controller Route A Source-Only Belief-Stress Obstacle-Clearance Regression Atlas Result Audit

## Metadata

- status: completed
- decision: `accept_m2796_route_to_source_only_belief_stress_clearance_localized_corrective_training_design`
- manifest: `experiments/manifests/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.json`
- audit doc: `docs/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.md`
- parent summary: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/summary.json`
- parent atlas rows: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/clearance_regression_rows.csv`
- parent aggregate rows: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/clearance_regression_aggregate_rows.csv`
- parent gate matrix: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design.json`
- next: `m2798-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-training-design`

## Audit Result

M2797 accepts M2796 as complete and claim-safe source-only reanalysis evidence.
M2796 consumed M2795, M2794, and M2793 artifacts only. It did not execute reset,
step, policy action, rollout, replay, validation, training, PPO, source build,
adapter probe, external simulation, ranking, winner selection, checkpoint
promotion, success-rate verdict computation, or private holdout.

Accepted parent result:

```text
status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
clearance_regression_rows: 144
clearance_regression_aggregate_rows: 237
proof_gate_rows: 16
mitigation_reference_guard_rows: 8
claim_boundary_rows: 15
m2797_follow_up_manifest_registered: true
```

## Clearance Regression Accounting

The accepted atlas preserves the hard obstacle-clearance blocker:

```text
candidate_minus_source_clearance:
  positive rows: 30
  negative rows: 42
  mean: -0.0003189920460919861
  median: -0.0026030437199309198

candidate_minus_base_clearance:
  positive rows: 29
  negative rows: 43
  mean: -0.00013214111660788612
  median: -0.00039442807985579087

global_clearance:
  positive rows: 59
  negative rows: 85
  zero rows: 0
  mean: -0.00022556658134993614
  median: -0.0005223763685033855
```

The atlas shows that the regression is structured by role family:

```text
drift_required_recovery:
  negative rows: 48/48
  negative rate: 1.0
  mean clearance delta: -0.0022172613526741866
  mean road-margin delta: 0.0023183132483449997
  mean final-speed delta: 0.0023527273103594224

stable_aes:
  negative rows: 36/48
  negative rate: 0.75
  mean clearance delta: -0.0016715118073866257
  mean road-margin delta: 0.002309546003948624
  mean final-speed delta: 0.002357007045255724

stable_avoidable:
  negative rows: 1/48
  negative rate: 0.020833333333333332
  mean clearance delta: 0.003212073416011004
  mean road-margin delta: 0.0013661642835697864
  mean final-speed delta: 0.0011747459908904023
```

The strongest bucket-level blocker is broad in `drift_required_recovery`: all
six role/dynamics/stress buckets are 8/8 negative across the two delta families.
Stable-AES buckets are also mostly negative, especially under fault/delay/noise
history stress. Stable-avoidable rows mostly preserve clearance and therefore
must be retained as a behavior-retention guard, not used as an excuse to weaken
clearance gates.

## Boundary Audit

M2797 accepts the M2796 boundary checks:

```text
actor_contract_shape_72_action_3: true
hidden_or_oracle_actor_inputs_required: false
actor_visible_role_dynamics_stress_labels: false
mitigation_reference_rows_outside_denominators: true
ranking_admissible_count: 0
winner_selected_count: 0
success_rate_verdict_computed: false
```

Role, dynamics, stress, seed, delta-family, road-margin, speed, yaw-rate,
conflict, and action-delta labels are accepted as evaluator-side atlas metadata
only. They are not actor inputs and cannot be promoted into policy observation.

## Claim Boundary

M2797 accepts only these limited claims:

```text
M2796 atlas artifacts are complete.
M2796 reanalyzed M2793 source-only delta rows without new execution.
M2796 identifies structured clearance-regression families for future design.
M2796 preserves actor, mitigation, and claim boundaries.
```

M2797 rejects:

```text
candidate-better verdict
checkpoint ranking
winner selection
checkpoint promotion
success-rate verdict
repair success
validation readiness or validation result
driver performance
paper result
current-sim verdict
high-fidelity validation
full ideal driver completion
finite-window-vs-GRU conclusion
level3 self-identification
```

## Failure Taxonomy

Controlled failures and risks:

```text
contract_violation:
  controlled. Actor P0 observation 72/action 3 and hidden/oracle exclusion are
  preserved.

lineage_invalid:
  controlled. M2796 lineage points to M2795, M2794, and M2793 source artifacts.

scenario_sampling_failure:
  controlled for this audit. M2796 reuses the complete M2793 ordinary role,
  dynamics, stress, and seed surface.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators
  and outside delta rows.
```

Active blockers:

```text
behavior_regression:
  active. Clearance is negative in 85/144 atlas rows, including all 48
  drift_required_recovery rows and 36/48 stable_aes rows.

objective_overfit:
  active. Road-margin and speed are positive while clearance is negative, so a
  future objective must prevent road/speed gains from masking clearance loss.

metric_artifact:
  active. M2796 is source-only reanalysis of small candidate deltas and cannot
  be used as performance evidence.
```

## Route Decision

M2797 accepts M2796 completeness and claim safety, then routes to M2798:
`source_only_belief_stress_clearance_localized_corrective_training_design`.

M2798 should be design-only. It should use the atlas to specify a bounded
corrective training/update protocol that prioritizes obstacle clearance for
`drift_required_recovery` and `stable_aes`, keeps `stable_avoidable` as a
behavior-retention guard, preserves actor P0 observation 72/action 3 with no
hidden/oracle actor labels, keeps mitigation rows outside ordinary denominators,
and separates proof, generalization, behavior-retention, and promotion gates.

M2798 must not train, execute rollouts, validate, rank, promote, select a
winner, compute a success-rate verdict, or claim driver performance, paper,
current-sim, high-fidelity, full-driver, or self-ID evidence.
