# M888 V4 Enriched Pair-Delta Replay Proof Gate Design

## Purpose

M888 designs the first closed-loop replay/proof gate for the M886
exact-admissible objective-only candidate.

The selected candidate from M887 is:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
```

Fallback candidate:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_05.pt
```

M888 is design-only:

```text
no replay execution
no training
no PPO
no promotion
```

## Gate Order

M889 should run gates in this order:

```text
1. exact objective recheck
2. first replay gates: M183/M170 and M267/M264
3. six public replay surfaces
4. behavior seeds 9505 and 9506
5. audit and routing
```

The first replay gates are intentionally early because historical failures often
show up on:

```text
M183/M170 old fragile row family
M267/M264 current-family wrong-history rows
```

## Baseline

Because M886 was initialized from the active diagnostic BC checkpoint, all M889
proof comparisons should use:

```text
base = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
candidate = runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
fallback = runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_05.pt
```

Do not compare M886 directly against the latest public-gate base as a promotion
claim. M886 is a diagnostic-objective branch rooted at M568.

## Exact Objective Recheck

Before closed-loop replay, M889 should re-run exact no-update sanity for the
candidate and fallback with the M883/M880 reconstruction inputs.

Candidate command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_enriched_pair_delta_objective_sanity \
  --checkpoint runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --objective-train-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv \
  --objective-eval-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv \
  --source-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv \
  --new-signature-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv \
  --run-dir runs/m889_alpha_0_1_exact_recheck \
  --device cpu
```

Fallback command is identical with:

```text
--checkpoint runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_05.pt
--run-dir runs/m889_alpha_0_05_exact_recheck
```

Pass condition:

```text
all rows reconstruct
exact losses finite
candidate objective_train weighted loss <= M568 base
candidate objective_eval/source_holdout/new_signature_holdout weighted losses <= M568 base + 1e-4
```

## Replay Proof Surfaces

M889 should evaluate the six public replay surfaces versus M568:

```text
M183/M168: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
M183/M170: runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
M193/M189: runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv
M212/M204: runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv
M223/M219: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv
M267/M264: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

Recommended command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_diverse_protected_gate \
  --checkpoint-policy m568_base=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy m886_a010=runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt \
  --replay-gate m183_m168=runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --replay-gate m183_m170=runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --replay-gate m193_m189=runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --replay-gate m212_m204=runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --replay-gate m223_m219=runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --replay-gate m267_m264=runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv,m568_base,m886_a010 \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m889_m886_a010_replay_proof_gate
```

If `alpha_0_1` fails a replay surface, run the same command for `m886_a005`
using `alpha_0_05.pt` before redesigning the objective.

## Behavior Retention

Only if exact recheck and replay gates pass, M889 should run behavior retention
against M568 on seeds `9505` and `9506`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.benchmark \
  --checkpoint-policy m568_base=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy m886_a010=runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt \
  --checkpoint-policy m886_a010_reset=runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt@reset_recurrent_state \
  --checkpoint-policy m886_a010_zero_all=runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt@zero_all_response \
  --episodes 80 \
  --seed 9505 \
  --device cpu \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --run-dir runs/m889_m886_a010_behavior_seed9505
```

Repeat with:

```text
--seed 9506
--run-dir runs/m889_m886_a010_behavior_seed9506
```

Pass condition:

```text
candidate success >= M568 base success
candidate termination <= M568 base termination
clearance margin regression <= 0.005
reset/zero_all diagnostics recorded but not used for promotion
```

## Pass/Fail Routing

M889 should classify outcomes as:

```text
exact_recheck_failure:
  stop and audit objective metrics; do not run replay

first_replay_failure:
  run alpha_0_05 fallback once; if fallback also fails, route to replay failure audit

six_surface_replay_failure:
  classify as proof_washout; audit failed surface rows before any further objective update

behavior_regression:
  classify as behavior_regression; do not admit PPO or promotion

all_gates_pass:
  admit an audit milestone only; do not promote directly
```

Even if all M889 gates pass, the correct next step is an audit, not promotion.
M886/M887/M888 are still public-objective/proof workflow milestones rooted at
the M568 diagnostic checkpoint.

## Decision

Decision:

```text
v4_enriched_pair_delta_replay_proof_gate_design_admit_m889
```

Next:

```text
m889-v4-enriched-pair-delta-replay-proof-gate-implementation
```
