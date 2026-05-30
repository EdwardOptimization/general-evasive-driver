# M1804 Executable V2 Stable Source-Label Top-Up Execution Design

- status: completed
- decision: `stable_source_label_topup_execution_design_admit_preflight_run`
- source helper: `src/autodrift/executable_v2_stable_source_label_topup_preflight.py`
- execution in this milestone: `false`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Exact Command

M1805 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_stable_source_label_topup_preflight \
  --replacement-needs runs/m1800_executable_v2_label_source_compatibility_preflight/replacement_need_rows.csv \
  --source-label-support runs/m1800_executable_v2_label_source_compatibility_preflight/source_label_support.csv \
  --bounded-panel-specs runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json \
  --output-dir runs/m1805_executable_v2_stable_source_label_topup_preflight \
  --target-topup-count 3 \
  --next-blocker m1806-executable-v2-stable-source-label-topup-result-audit
```

This command is no-reset and no-rollout. It only reads M1800 replacement/support
artifacts and M1771 stable bounded-panel metadata.

## Input Artifacts

Required inputs:

```text
runs/m1800_executable_v2_label_source_compatibility_preflight/replacement_need_rows.csv
runs/m1800_executable_v2_label_source_compatibility_preflight/source_label_support.csv
runs/m1771_metric_specific_bounded_panel_materialization_preflight/bounded_panel_specs.json
```

Expected output directory:

```text
runs/m1805_executable_v2_stable_source_label_topup_preflight
```

Expected artifacts:

```text
summary.json
stable_topup_targets.csv
stable_candidate_source_pool.csv
stable_topup_candidate_rows.csv
stable_new_materialization_need_rows.csv
stable_topup_claim_boundary.csv
```

## Expected Counts

Pre-registered expected counts from M1800 replacement needs and M1771 stable
source metadata:

| field | expected |
| --- | ---: |
| `stable_topup_target_count` | 3 |
| `target_missing_profile_count_total` | 36 |
| `stable_candidate_source_count` | 6 |
| `candidate_row_count` | 5 |
| `direct_replacement_count` | 0 |
| `new_materialization_need_count` | 3 |
| `labels_enter_actor_input_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected candidate class counts:

| candidate class | rows |
| --- | ---: |
| `metadata_only_untrusted` | 2 |
| `near_existing_candidate` | 3 |
| `exact_existing_candidate` | 0 |

Expected claim-admission flags:

```text
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Expected Interpretation

The execution should confirm that the stable source pool does not contain a
trusted direct replacement for the three systematic stable label-source gaps:

- `m1771-bp1-00/aes_feasible/nominal/nominal/medium/center` is metadata
  compatible but observed as `unsupported_systematic`;
- `m1771-bp1-02/aes_feasible/friction_step/nominal/late/center` is metadata
  compatible but observed as `unsupported_systematic`;
- `m1771-bp1-05/aeb_feasible/brake_variation/moderate/late/wide_offset` has no
  observed direct stable source in the current M1771 pool.

The expected result therefore remains a planning result, not a repaired
execution result. Candidate rows can guide later source materialization or
targeted reset probes, but no row is admissible for measured execution or
controller-family ranking.

## Pass Criteria

M1805 should pass if:

- the command completes with
  `result_class=executable_v2_stable_source_label_topup_preflight_pass`;
- all expected counts match;
- all expected artifacts exist;
- no direct replacement is admitted from metadata-only support;
- no reset, rollout, policy action, measured rollout, training, replay, PPO,
  private holdout, promotion, actor-input change, profile tuning, ranking,
  paper-level, or level3 claim occurs;
- the next blocker is
  `m1806-executable-v2-stable-source-label-topup-result-audit`.

M1805 should not materialize new source specs or run targeted reset probes. Its
job is only to materialize the top-up planning evidence.

## Route Decision

Route to:

```text
m1805-executable-v2-stable-source-label-topup-preflight
```

M1805 executes the exact command above. M1806 should then audit whether the
result supports new stable-source materialization, targeted reset probes, or a
design repair.

## Guardrails

- top-up preflight executed in M1804: `false`
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

- exact no-reset stable source-label top-up execution design;
- pre-registered expected candidate and materialization-need counts for M1805.

Unsupported:

- top-up execution result;
- stable source materialization;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
