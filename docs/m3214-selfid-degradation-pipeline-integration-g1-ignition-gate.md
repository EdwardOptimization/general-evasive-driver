# M3214 Self-ID Degradation Pipeline Integration + G1 Ignition Gate

Status: completed (harness run
`runs/research/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate_20260611T024006Z`,
returncode 0). Auxiliary diagnostic branch `selfid_degradation_diagnostic_g1`;
the active-safety driver objective boundary is unchanged and
`ActiveSafetyReflexDriver` was not touched.

`self_id_evidence_discipline.claim_level`: `not_applicable`.

## 1. What this milestone delivered

### 1.1 D1 pipeline integration (pre-gate infrastructure)

The pre-launch audit (`experiments/feasibility_audit/selfid_gate_pipeline_check.json`)
found `ObservationDegradationWrapper` unintegrated: `vector_env.py`,
`train_ppo.evaluate_actor`, `evaluate.evaluate_policy`, and
`hidden_swap_gate.collect_decision_snapshot` all constructed bare
`AutoDriftEnv`. M3214 ships the integration:

- `DriftEnvConfig.observation_degradation: ObservationDegradationConfig | None`
  (default `None`; loud validation on every field).
- `build_env_config` / `merge_env_config` accept the `observation_degradation`
  block (unknown sub-keys raise `ValueError`).
- Unified factory `observation_degradation_wrapper.make_env_from_config`:
  without the block it returns a bare `AutoDriftEnv` (bit-for-bit unchanged
  behavior, verified); with the block every entry point — sync/parallel vector
  envs including fork workers, `evaluate_actor`, `evaluate_policy` (also when
  the env config is recovered from checkpoint metadata), and the hidden-swap
  gate — mounts the wrapper, including the wrapped-clean T1 cell so all matrix
  cells share one construction path.
- 14 new integration tests (`tests/test_observation_degradation_integration.py`)
  plus 91 existing regression tests pass (105 total); G2 retest at the real
  training entry reproduced the audit health check (delay stream
  `first_diff_step=1`, rewards bitwise identical, parallel fork == sync
  bit-for-bit).

### 1.2 G1 ignition gate (this harness milestone)

`scripts/feasibility_audit/selfid_g1_ignition_gate.py` answers one
infrastructure question at minutes scale, with the verdict criteria frozen in
the script docstring and echoed into `summary.json` BEFORE the run:

> Does the delay-25 task condition produce a measurable outcome-distribution
> difference against the wrapped-clean condition when the degradation runs
> through the real, integrated training -> checkpoint -> evaluation chain?

## 2. Pre-registered design and criteria (frozen before the run)

- Conditions (both through the wrapper): `clean` = `{delay_steps: 0,
  noise_std: 0.0}`; `delay_25` = `{delay_steps: 25, noise_std: 0.0}`.
- Base config `configs/selfid_positive_control_p0_smoke.json` (obs72 P0
  contract, online_gru); no condition-specific tuning.
- 4 training seeds `[710001..710004]` x 65,536 steps per seed, `num_envs=16`,
  sync, cpu, `OMP_NUM_THREADS=1`, 8 concurrent jobs.
- 200 fresh eval episodes per run in the run's OWN condition, shared seed list
  `7,700,000 + [0..199]`, disjoint from training seeds.
- Verdict: seed-paired deltas `delay_25 - clean` for `success_rate` and
  `clearance_margin_p10`; 95% percentile bootstrap CI (B=20,000, numpy seed
  20260611). **G1 PASS iff either CI excludes 0.** G1 FAIL routes to the
  pre-registered Outcome B/D analogue: the full 20-cell matrix is cancelled
  and the task design is reworked; no threshold weakening, no budget
  extension.
- Auxiliary (non-decisive): open-loop action divergence on shared clean
  observation streams.

## 3. Measured results (deterministic; repeat-run bitwise identical up to wall time)

Execution health: 8/8 trainings and 8/8 evals succeeded, all required metrics
finite; training 66.7 s wall total (7,865 aggregate env steps/s),
evaluation 5.2 s total; `budget_is_preregistered: true`.

Per-run outcomes (200 shared-seed episodes each):

| condition | seed | success_rate | collision_rate | offtrack_rate | clearance_margin_p10 | margin_mean | return_mean |
|---|---|---|---|---|---|---|---|
| clean | 710001 | 0.545 | 0.455 | 0.000 | -0.1499 | 0.6091 | 55.31 |
| clean | 710002 | 0.565 | 0.435 | 0.000 | -0.1404 | 0.6026 | 56.03 |
| clean | 710003 | 0.015 | 0.985 | 0.000 | -0.2186 | -0.1029 | 20.71 |
| clean | 710004 | 0.000 | 1.000 | 0.000 | -0.2384 | -0.1305 | 19.13 |
| delay_25 | 710001 | 0.500 | 0.500 | 0.000 | -0.1523 | 0.5408 | 52.43 |
| delay_25 | 710002 | 0.755 | 0.245 | 0.000 | -0.0687 | 1.1790 | 66.36 |
| delay_25 | 710003 | 0.065 | 0.935 | 0.000 | -0.2468 | -0.0741 | 25.45 |
| delay_25 | 710004 | 0.040 | 0.960 | 0.000 | -0.2150 | -0.1009 | 20.49 |

Pre-registered verdict statistics (paired deltas `delay_25 - clean`):

| metric | paired deltas (seed 1..4) | mean | 95% bootstrap CI | excludes 0 |
|---|---|---|---|---|
| success_rate | -0.045, +0.190, +0.050, +0.040 | +0.0588 | [-0.0213, +0.1525] | no |
| clearance_margin_p10 | -0.0024, +0.0717, -0.0282, +0.0234 | +0.0161 | [-0.0153, +0.0532] | no |

Auxiliary action-divergence probe (NOT part of the verdict): mean L2 action
distance clean-vs-delay25 on shared streams = 0.091-0.272 per seed, which is
SMALLER than the clean-vs-different-clean-seed baseline 0.195-0.544 on the
same streams — seed-to-seed optimization noise exceeds the condition-induced
policy difference at this budget.

## 4. G1 verdict and pre-registered routing

**G1 = FAIL.** Neither CI excludes 0. The dominant signal is within-condition
seed variance (clean success_rate spans 0.000-0.565 across 4 seeds; delay_25
spans 0.040-0.755), an order of magnitude larger than the paired condition
effect — the signature anticipated by pre-registered Outcome D (optimization,
not information, is the binding constraint at this budget), with Outcome B
(degradation does not bite outcomes) not separable from it at ignition scale.

Pre-registered routing, applied as written, with no threshold weakening:

1. The full 20-cell degradation matrix is **CANCELLED** under the current
   pre-registration. No matrix cell may be funded from this branch.
2. The task/budget design goes back to the drawing board ("回炉任务设计"):
   any future attempt requires a FRESH pre-registration that addresses the
   seed-variance floor measured here (e.g. variance-reduction or budget/task
   redesign) before any cell is launched.
3. The D1 pipeline integration itself remains valid, tested infrastructure
   and is NOT cancelled; it is condition-agnostic plumbing.

## 5. Claim boundary

Allowed claim: the observation-degradation pipeline is integrated at all four
real entry points with bit-for-bit backward compatibility, and the
pre-registered G1 ignition gate executed deterministically end to end and
returned FAIL, cancelling the full matrix under the current design.

Rejected claims (explicitly): self-identification evidence at any level above
`not_applicable`; profile ranking or architecture preference; gate validity or
invalidity (requires full-budget Experiment 2); information ceiling;
task-family difficulty or dose-response shape; any driver-performance,
current-sim, high-fidelity, full-driver, repair-success, robustness-result,
or feasibility-proof claim. G1 numbers are ignition-budget plumbing readouts
(65,536 steps/seed is ~13% of the pre-registered 500k floor; M1199/M1497
discipline applies) and must never be quoted as scientific evidence.

## 6. Artifacts

- `runs/feasibility_audit/selfid_g1_ignition_gate/summary.json` (criteria,
  per-run table, bootstrap CIs, verdict, health, probe)
- `runs/feasibility_audit/selfid_g1_ignition_gate/g1_run_rows.csv`
- `runs/feasibility_audit/selfid_g1_ignition_gate/runs/<condition>_seed<seed>/`
  (per-run configs, train logs, checkpoints, eval episodes.csv)
- `scripts/feasibility_audit/selfid_g1_ignition_gate.py` (frozen criteria in
  docstring)
- harness record:
  `runs/research/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate_20260611T024006Z/command.log`
