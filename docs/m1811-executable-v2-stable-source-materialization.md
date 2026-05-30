# M1811 Executable V2 Stable Source Materialization

- status: completed
- decision: `stable_source_materialization_pass_route_to_result_audit`
- artifact: `runs/m1811_executable_v2_stable_source_materialization/summary.json`
- reset run: `false`
- rollout started: `false`
- measured rollout started: `false`
- training/replay/PPO: `false`

## Command

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

## Result

M1811 matched the pre-registered M1810 counts:

| field | value |
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

Strategy count:

```text
label_specific_stable_sampler_repair_v1: 3
```

Claim flags:

```text
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Materialized Sources

| target | label | materialized source | materialized spec | env delta |
| --- | --- | --- | --- | --- |
| `m1771-bp1-00` | `aes_feasible` | `m1811-stable-src-000` | `m1811-stable-bp-000` | `allowed_labels=[aes_feasible]`, `require_aeb_infeasible=true` |
| `m1771-bp1-02` | `aes_feasible` | `m1811-stable-src-001` | `m1811-stable-bp-001` | `allowed_labels=[aes_feasible]`, `require_aeb_infeasible=true` |
| `m1771-bp1-05` | `aeb_feasible` | `m1811-stable-src-002` | `m1811-stable-bp-002` | `allowed_labels=[aeb_feasible]`, `require_aeb_infeasible=false` |

All materialized sources remain diagnostic and require reset-only validation
before they can repair executable v2 reset feasibility.

## Artifact Set

M1811 wrote:

```text
summary.json
stable_source_materialization_targets.csv
stable_source_materialization_specs.csv
stable_source_materialization_specs.json
stable_source_materialization_matrix.csv
stable_source_materialization_duplicate_keys.csv
stable_source_materialization_claim_boundary.csv
```

## Interpretation

M1811 repairs the missing source-materialization artifact layer, not reset
feasibility. The output now gives a concrete three-source, 36-row profile matrix
for targeted reset-only validation. Because no reset has run, measured execution
and controller-family ranking remain blocked.

The next useful step is a result audit that decides whether to proceed to
targeted reset-only validation design.

## Route Decision

Route to:

```text
m1812-executable-v2-stable-source-materialization-result-audit
```

M1812 should audit whether the materialized source artifacts are complete and
ready for targeted reset-only validation design.

## Guardrails

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

- no-reset stable source materialization artifact result;
- three materialized source specs and 36 profile-matrix rows are available for
  later reset-only validation.

Unsupported:

- targeted reset validation;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
