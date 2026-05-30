# M1810 Executable V2 Stable Source Materialization Execution Design

- status: completed
- decision: `stable_source_materialization_execution_design_admit_preflight_run`
- source helper: `src/autodrift/executable_v2_stable_source_materialization.py`
- execution in this milestone: `false`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Exact Command

M1811 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_stable_source_materialization \
  --new-materialization-needs runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_new_materialization_need_rows.csv \
  --topup-candidates runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_topup_candidate_rows.csv \
  --bounded-panel-specs runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json \
  --bounded-panel-matrix runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv \
  --output-dir runs/m1811_executable_v2_stable_source_materialization \
  --target-materialization-count 3 \
  --target-profile-count 12 \
  --id-prefix m1811 \
  --next-blocker m1812-executable-v2-stable-source-materialization-result-audit
```

This command is no-reset and no-rollout. It only reads M1805 top-up artifacts
and M1771 bounded-panel artifacts, then writes materialization planning
artifacts.

## Input Artifacts

Required inputs:

```text
runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_new_materialization_need_rows.csv
runs/m1805_executable_v2_stable_source_label_topup_preflight/stable_topup_candidate_rows.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_matrix.csv
```

Expected output directory:

```text
runs/m1811_executable_v2_stable_source_materialization
```

Expected artifacts:

```text
summary.json
stable_source_materialization_targets.csv
stable_source_materialization_specs.csv
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
stable_source_materialization_duplicate_keys.csv
stable_source_materialization_claim_boundary.csv
```

## Expected Counts

Pre-registered expected counts from M1805 and M1771:

| field | expected |
| --- | ---: |
| `stable_materialization_target_count` | 3 |
| `stable_materialization_spec_count` | 3 |
| `stable_materialization_matrix_row_count` | 36 |
| `profile_control_count` | 12 |
| `duplicate_key_count` | 0 |
| `labels_enter_actor_input_count` | 0 |
| `reset_validation_required_count` | 3 |
| `measured_execution_admissible_count` | 0 |
| `controller_family_ranking_admissible_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected strategy counts:

| materialization strategy | rows |
| --- | ---: |
| `label_specific_stable_sampler_repair_v1` | 3 |

Expected claim-admission flags:

```text
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Pass Criteria

M1811 should pass if:

- the command completes with `result_class=executable_v2_stable_source_materialization_pass`;
- all expected counts match;
- all expected artifacts exist;
- no duplicate materialization keys are present;
- no labels enter actor input;
- all materialized sources require reset validation;
- no reset, rollout, policy action, measured rollout, training, replay, PPO,
  private holdout, promotion, actor-input change, profile tuning, ranking,
  paper-level, or level3 claim occurs;
- the next blocker is
  `m1812-executable-v2-stable-source-materialization-result-audit`.

M1811 should not run reset validation. Its job is only to materialize planning
artifacts for the three stable source-label gaps.

## Route Decision

Route to:

```text
m1811-executable-v2-stable-source-materialization
```

M1811 executes the exact command above. M1812 should then audit whether the
materialized sources are ready for targeted reset-only validation design.

## Guardrails

- source materialization executed in M1810: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- exact no-reset stable source materialization execution design;
- pre-registered expected materialization counts for M1811.

Unsupported:

- source materialization execution result;
- targeted reset validation;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
