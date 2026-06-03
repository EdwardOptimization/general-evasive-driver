# M2504 Engineering Controller Public Benchmark Pack Design

- status: completed
- decision: `public_benchmark_pack_design_route_to_materialization_preflight`
- manifest: `experiments/manifests/m2504-engineering-controller-public-benchmark-pack-design.json`
- parent synthesis: `docs/m2503-engineering-controller-source-only-metric-panel-branch-synthesis.md`
- observation contract: `docs/observation-contract.md`
- route constraint: `docs/post-m2470-route-plan.md`
- next milestone: `m2505-engineering-controller-public-benchmark-pack-materialization-preflight`
- external high-fidelity simulation installed/imported/executed in M2504: `false`
- policy action/measured validation/training/replay/PPO/ranking/winner selection in M2504: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Problem

M2503 closes the source-only metric panel branch and promotes the evidence to a
public benchmark-pack preparation branch. The available evidence is useful, but
it is still source-only engineering diagnostics. It must be packaged in a way
that makes the actor contract, lineage, artifacts, limitations, and rejected
claims explicit.

M2504 designs that pack. It does not create performance evidence.

## Pack Scope

The public benchmark pack should be a bounded engineering artifact for:

```text
source-only HF0 diagnostic telemetry over fixed parameterized role fixtures
```

Allowed public description:

```text
This pack documents a same-contract recurrent actor checkpoint, the deployed
P0 observation/action boundary, source-only role diagnostic telemetry, and
open-loop comparison diagnostics. It is intended for reproducibility and
engineering inspection.
```

Forbidden public description:

```text
driver performance benchmark
controller leaderboard
success-rate benchmark
high-fidelity validation
paper result
finite-window-vs-GRU comparison
level3 self-identification proof
current-sim verdict
```

## Required Pack Contents

M2505 should materialize a pack directory:

```text
public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/
```

Required files:

```text
README.md
artifact_manifest.csv
claim_boundary.md
actor_contract.md
checkpoint_lineage.md
scenario_role_diagnostics.md
baseline_comparison_diagnostics.md
known_limitations.md
reproduce.md
summary.json
```

The pack may reference committed run artifacts by relative path. It should not
copy large binary checkpoints or create a separate release repository in M2505.

## Artifact Manifest

`artifact_manifest.csv` should include one row per source artifact:

```text
artifact_id
path
artifact_type
source_milestone
included_in_pack
public_claim_scope
forbidden_interpretation
```

Required artifact references:

```text
docs/observation-contract.md
docs/post-m2470-route-plan.md
docs/m2503-engineering-controller-source-only-metric-panel-branch-synthesis.md
docs/m2502-engineering-controller-source-only-baseline-comparison-result-audit.md
docs/m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight.md
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv
docs/m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit.md
docs/m2498-engineering-controller-parameterized-source-only-role-metric-panel-rerun.md
runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json
runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv
runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv
```

Required excluded artifact classes:

```text
uncommitted local files
private holdout data
hidden simulator/oracle state as actor input
success-rate or controller ranking tables
external high-fidelity simulator outputs
training logs not needed for checkpoint lineage
large checkpoint binary copies
```

## Actor Contract Section

`actor_contract.md` must restate the deployed contract:

```text
P0 observation shape: 72
action shape: 3
actor encoder: human_view_online_gru
action sequence horizon: 1
output: [steering_command, throttle_command, brake_command]
normalized action bounds: [-1, 1] per channel
physical_throttle = 0.5 * (throttle_command + 1)
physical_brake = 0.5 * (brake_command + 1)
```

Allowed actor-visible categories:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent state from past command-response history
```

Forbidden actor-visible categories:

```text
mu
mass
tire stiffness
brake scale
actuator tau
slip
tire force
oracle feasibility
AEB/AES/drift labels
controller mode
speed_ref
beta_target
path error
heading error
path curvature
TTC
required clearance
oracle stopping distance
reward terms
success labels
```

## Diagnostic Reports

`scenario_role_diagnostics.md` should summarize M2498/M2499:

```text
parameterized_role_fixtures: true
telemetry rows / role panel rows: 300 / 3
reset digest unique count: 3
role metrics nonidentical: true
diagnostic-only: true
driver performance claim: false
```

`baseline_comparison_diagnostics.md` should summarize M2501/M2502:

```text
comparison subjects:
  m1154_policy_actor
  coast_open_loop
  straight_full_brake_open_loop
roles:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation
telemetry rows / role-subject panel rows: 900 / 9
reset digests match within role across subjects: true
reset digests differentiated across roles: true
diagnostic-only: true
ranking/winner/success-rate claims: false
```

Neither report may order subjects by performance or name a winner.

## Summary JSON

`summary.json` should expose machine-checkable gates:

```text
result_class: engineering_controller_public_benchmark_pack_materialization_preflight_pass
pack_id: engineering_controller_source_only_diagnostics_m2505
artifact_manifest_rows: at least 13
required_files_present: true
actor_contract_shape_72_action_3: true
claim_boundary_present: true
known_limitations_present: true
source_only_diagnostic_scope: true
external_high_fidelity_simulation_included: false
success_rate_computed: false
ranking_run: false
winner_selected: false
driver_performance_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
```

## Materialization Tests

M2505 should include tests or validators that check:

```text
all required pack files exist
artifact_manifest.csv references existing source artifacts
claim_boundary.md rejects performance/ranking/success-rate/validation/paper/self-ID claims
actor_contract.md states P0 72 and action 3
diagnostic report files cite M2498/M2501 rows without selecting a winner
summary.json has all claim flags false
no policy action, training, replay, PPO, external simulator, ranking, winner, or promotion is run
```

## Supported Claim

Supported:

```text
M2504 defines a bounded public engineering benchmark-pack contract for the
source-only diagnostic evidence accumulated through M2503.
```

## Rejected Interpretations

M2504 does not support:

```text
driver performance
success-rate benchmark
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

## Route Decision

M2504 routes to:

```text
m2505-engineering-controller-public-benchmark-pack-materialization-preflight
```

M2505 should materialize the pack files and run pack-structure validators only.
It must not execute policy actions, train, rank, select a winner, compute
success rates, promote a checkpoint, or claim driver performance.
