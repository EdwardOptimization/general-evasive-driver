# M3246: C1-v4 Distill Stage A

Status: completed. Frozen Stage A gate passed.

## Artifacts

- Preregistration: `experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_prereg.json`
- Quick artifact: `experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a_quick.json`
- Result JSON: `experiments/feasibility_audit/c5prime_c1_v4_distill_stage_a.json`
- Harness run: `runs/research/m3246-c1-v4-distill-stage-a_20260612T160635Z/command.log`
- Teacher rollouts: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/teacher_rollout_rows.csv`
- Training metrics: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/training_metrics.csv`
- Primary candidate rows: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/candidate_rows_primary.csv`
- Exploratory candidate rows: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/candidate_rows_exploratory.csv`
- Primary distillation dataset: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/distill_dataset_primary.npz`
- Primary checkpoint: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/primary_distiller.pt`
- Exploratory checkpoint: `runs/feasibility_audit/c5prime_c1_v4_distill_stage_a/stage_a/exploratory_distiller.pt`

## Measured

M3246 executed the preregistered C1-v4 Stage A protocol through the research
harness. It trained a supervised MLP residual student to imitate
`v4_pertuned(obs) - fixed_v4(obs)` on 24 disjoint C5-prime T-limit training
rows, then evaluated deterministic closed-loop behavior on the frozen A3
S1/S2/S3 validation rows. The incumbent `ActiveSafetyReflexDriver` v4 was
used only as the frozen base and was not edited.

Run scale:

| metric | value |
|---|---:|
| wall time | 31.380 s |
| training rows | 24 |
| distillation frames | 2777 |
| epochs | 600 |
| validation rows per cell | 144 |
| primary validation episodes | 432 |
| exploratory validation episodes | 432 |
| primary Stage A pass cells | 3 / 3 |

Primary arm, with the frozen M3245 `delta_max = [0.35, 0.45, 0.45]`, passed
the frozen Stage A decision rule. PASS required candidate success within 0.05
paired of `v4_pertuned` in every qualified T-limit cell.

| cell | fixed v4 | v4_pertuned | oracle | primary student | student - pertuned | CI95 | paired disagreements | pass |
|---|---:|---:|---:|---:|---:|---|---:|---|
| S1/T_limit | 0.2014 | 0.8403 | 1.0000 | 0.8542 | +0.0139 | [-0.0347, 0.0625] | 14 | true |
| S2/T_limit | 0.3194 | 0.7847 | 1.0000 | 0.7639 | -0.0208 | [-0.0764, 0.0347] | 17 | true |
| S3/T_limit | 0.4861 | 0.8264 | 1.0000 | 0.8264 | +0.0000 | [0.0000, 0.0000] | 0 | true |

The representation check found that the primary M3245 action bounds do not
fully contain the per-tuned residual target: max absolute target units were
`[1.456238, 0.676537, 2.081652]`, with overbound frame counts `[36, 0, 441]`
and an any-channel overbound share of `0.171768`. Per the preregistration, an
exploratory widened-delta arm was therefore trained and reported, using
`delta_max = [0.535167, 0.45, 0.983581]`. This exploratory arm also passed the
within-0.05 cell rule but is not the Stage A gate:

| cell | exploratory student | v4_pertuned | student - pertuned | CI95 | pass |
|---|---:|---:|---:|---|---|
| S1/T_limit | 0.8472 | 0.8403 | +0.0069 | [-0.0556, 0.0694] | true |
| S2/T_limit | 0.7361 | 0.7847 | -0.0486 | [-0.1182, 0.0208] | true |
| S3/T_limit | 0.8264 | 0.8264 | +0.0000 | [-0.0208, 0.0208] | true |

The supervised fit was not a no-op. Primary final validation MSE was
`0.003854` and channel MSE was `[0.002884, 0.001408, 0.005320]`; exploratory
final validation MSE was `0.001595` and channel MSE was
`[0.001159, 0.001029, 0.002255]`.

## Inferred

Stage A passes. The bounded residual architecture can represent enough of the
per-instance `v4_pertuned` recalibration to match the honest floor in closed
loop on the frozen A3 validation panel. This directly addresses the M3245
failure mode: PPO did not discover the recalibration from sparse outcome reward,
but supervised distillation of the same recalibration is learnable and
closed-loop viable.

The overbound representation finding remains important. The primary bound
passes despite 17.18% teacher-frame overbound, so the original M3245 bounds are
not an immediate blocker for Stage B admission. However, Stage B should
pre-register whether it keeps the primary bounds for comparability, uses the
distilled primary checkpoint as the main warm start, and treats widened
`delta_max` only as an exploratory or explicitly separate arm.

M3246 does not mutate the incumbent driver, does not run RL, and does not make
a validation-ranking, driver-performance, high-fidelity sufficiency,
repair-success, robustness-result, feasibility-proof, paper, or self-ID claim.

## Next

C1-v4 Stage B is admitted by the Stage A gate, but only after a new
pre-registration. The next unit should freeze the guarded-RL warm-start
protocol, including seed streams, first-rung budget, entropy/log-std schedule,
behavior-neutral stop rule, and the unchanged C1-v3 four-arm outcome judging.
