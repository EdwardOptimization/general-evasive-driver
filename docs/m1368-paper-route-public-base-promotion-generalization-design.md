# M1368 Paper-Route Public-Base Promotion Generalization Design

## Summary

M1368 designs the formal no-training promotion/generalization gate for the
M1362 alpha `0.1` broad-public-replay-passing candidate.

Candidate:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Current public base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Decision:

```text
public_base_promotion_generalization_design_admit_gate_implementation
```

M1368 does not promote the candidate. It only defines the evidence that the
next milestone must collect before a separate promotion audit can decide whether
M1362 alpha `0.1` should replace M1154 as the public base.

## Why This Gate Exists

M1365 is strong public proof evidence:

```text
six public replay surfaces: pass
source-diverse protected diagnostics: pass
old-key neighborhood: diagnostic only
behavior seeds 9505/9506: pass
actor input contract: unchanged
```

But it is still not enough for a public-base promotion:

```text
public replay surfaces were used during candidate selection and repair
fresh public scenario distribution has not been rerun for this candidate
moderate OOD scenario distribution has not been rerun for this candidate
private holdout has not been used and must stay unused here
PPO continuation stability is untested
level3 self-identification remains unproven
```

So the next step must be a formal promotion/generalization gate, not PPO, not
private holdout, and not more local active-set tuning.

## Candidate Eligibility Evidence

The candidate is eligible to enter the gate because M1362 and M1365 provide:

```text
exact source-history lift over M1154:
  combined_loss_delta_vs_base: -0.5148637349
  group_min_joint_margin_delta_vs_base: +0.5245143565
  eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667957

two-surface preflight:
  M267/M264: pass
  M183/M170: pass

broad public replay:
  six public replay surfaces: 6 / 6 pass
  source-diverse protected diagnostic: pass
  behavior seeds 9505/9506: pass
```

These values are eligibility evidence only. M1369 must recompute or explicitly
verify the gate tiers in one fresh run artifact before the candidate can enter a
promotion audit.

## Gate Tiers

The M1369 gate must evaluate tiers in this order.

### Tier 0: Contract And Mutation

Required:

```text
canonical 72-value human-view online recurrent actor input
no actor input contract change
no hidden/oracle input added
no slip, tire-force, friction-margin, TTC, reference, success, collision, or progress label input
no log_std mutation
no forbidden parameter mutation
```

Allowed parameter differences are only those already used by the M1360/M1362
family:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

If Tier 0 fails, classify the result as:

```text
contract_violation
```

and do not run promotion, PPO, private holdout, or repair from private evidence.

### Tier 1: Exact Source-History Retention

Required relative to M1154:

```text
combined_loss_delta_vs_base <= 0
group_min_joint_margin_delta_vs_base >= 0
eval_fold_4_group_min_joint_margin_delta_vs_base >= 0
all exact metrics finite
actor_inputs_changed == false
forbidden_parameter_mutation_detected == false
log_std_l2 == 0
```

The exact tier should use the active M1336 materialized source-history corpus
and the same pair-group metric interpretation used by M1362. It must not accept
the candidate only because a cached M1362 row exists unless the artifact clearly
records that the checkpoint path, base path, corpus path, and metric schema all
match.

If Tier 1 fails, classify the result as:

```text
proof_washout
```

or `metric_artifact` if the failure is caused by missing or non-finite metrics.

### Tier 2: Public Proof Replay

Required:

```text
M183/M168: pass
M183/M170: pass
M193/M189: pass
M212/M204: pass
M223/M219: pass
M267/M264: pass
source-diverse protected diagnostic: pass
```

The old `9944|perturbed|28|28` protected key remains diagnostic-only. It can
inform a later audit, but it must not single-handedly veto M1369 if the
source-diverse protected surface passes.

If Tier 2 fails, classify the result as:

```text
proof_washout
```

and route to a proof failure audit, not to private holdout and not to PPO.

### Tier 3: Fresh Public Generalization

Required distributions:

```text
fresh_public:
  env config: configs/m121_human_view_zero_obstacle_relvel.json
  seeds: at least 3 fixed fresh seeds not used by M1365 behavior replay
  episodes: at least 256 per seed

moderate_ood:
  env config: configs/eval_m574_moderate_ood_l3.json
  seeds: at least 2 fixed fresh seeds
  episodes: at least 128 per seed
```

Per distribution/seed, compare candidate against M1154 with the same seed and
episode count.

Pass tolerances:

```text
success_delta >= -0.01
termination_delta <= 0.01
collision_rate_delta <= 0.01
min_clearance_margin_mean_delta >= -0.005
```

If Tier 3 fails, classify the result as:

```text
scenario_sampling_failure
```

and preserve the failed scenario rows. Do not repair from private holdout. Do
not tune only the failed distribution and then call the same distribution fresh.

### Tier 4: Behavior And Ablation Retention

Required:

```text
behavior seeds: 9505, 9506, plus at least two new fixed public behavior seeds
episodes: at least 80 per seed
candidate normal success >= M1154 success - 0.01
candidate termination <= M1154 termination + 0.01
candidate normal success >= reset_recurrent_state success
reset_recurrent_state success >= zero_all_response success
```

This tier is not strong self-identification evidence. It only checks that the
candidate still has the public behavior ordering expected from the existing
human-view recurrent actor family.

If Tier 4 fails, classify the result as:

```text
behavior_regression
```

## Source-Rich Extreme Scenario Policy

Source-rich extreme and fault-proxy scenarios are important for the paper route,
but they should not be mixed into this first public-base promotion gate unless a
pre-registered evaluator already exists.

M1369 should record whether it can run an existing source-rich extreme public
diagnostic. If not, the candidate may still enter a public-base promotion audit
after passing Tiers 0-4, but the promotion audit must state:

```text
public-base promotion only
not paper-level source-rich extreme validation
not high-fidelity asymmetric-wheel fault evidence
```

The next branch after public-base promotion should add source-rich extreme
generalization and later L0/L1/L2/L3 comparison evidence.

## Private Holdout Policy

M1369 must not use private holdout.

Private holdout remains reserved for later paper-quality evidence. If a later
milestone uses private holdout to diagnose or repair a failure, that holdout
must be marked contaminated and rotated before being used for paper claims.

M1369 can only produce:

```text
promotion-audit candidate
repair/audit route
reject/archive route
```

It cannot itself promote the checkpoint.

## Gate Utility Classification

M1368 also fixes the engineering-logic status of current gates.

Core for public-base promotion:

```text
actor input contract check
exact source-history retention over M1336/M1342 metrics
six public replay surfaces
source-diverse protected diagnostic
fresh public and moderate-OOD generalization
behavior and ablation retention
```

Research-only:

```text
row-level wrong-history diagnostics
old-key neighborhood diagnostics
individual row15/row16 cliff explanations
current active-set objective deltas
```

Extended-regression:

```text
source-rich extreme fault-proxy distributions
future four-wheel or high-fidelity fault scenarios
private holdout
L0/L1/L2/L3 fair comparison matrices
guarded PPO continuation stability
```

Legacy or diagnostic-only:

```text
single protected key vetoes
local alpha tuning after broad public replay pass
lineage-specific row15/row16 blockers as permanent promotion blockers
same-shape relocation artifacts
```

This means M1369 should not let a single historical row override a
source-diverse public pass. Conversely, broad aggregate success cannot override
an explicit proof replay or input-contract failure.

## Promotion Decision Rule

If all Tiers 0-4 pass:

```text
M1369 result: public_base_promotion_generalization_gate_candidate
next route: separate promotion audit
```

If any tier fails:

```text
Tier 0: contract audit
Tier 1 or 2: proof failure audit
Tier 3: generalization regression audit
Tier 4: behavior regression audit
```

No M1369 outcome may route directly to PPO. PPO can only start after:

```text
1. M1369 passes,
2. a separate promotion audit accepts or rejects public-base replacement,
3. a guarded PPO readiness design defines rollback, exact/proof retention,
   generalization retention, and repair/projection rules.
```

## M1369 Pre-Registered Command Shape

M1369 should implement or use a generic materialized-source-history promotion
gate. It should avoid hard-coded Candidate B labels from older tools.

Expected command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_public_base_promotion_generalization_gate \
  --base-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --candidate-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --run-dir runs/m1369_public_base_promotion_generalization_gate \
  --device auto \
  --fresh-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --ood-env-config configs/eval_m574_moderate_ood_l3.json \
  --fresh-seeds 136900,136901,136902 \
  --ood-seeds 136920,136921 \
  --behavior-seeds 9505,9506,136930,136931 \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80 \
  --max-continuation-steps 60
```

Required artifacts:

```text
runs/m1369_public_base_promotion_generalization_gate/summary.json
runs/m1369_public_base_promotion_generalization_gate/exact_contract_summary.csv
runs/m1369_public_base_promotion_generalization_gate/proof_replay_summary.csv
runs/m1369_public_base_promotion_generalization_gate/generalization_comparison.csv
runs/m1369_public_base_promotion_generalization_gate/behavior_comparison.csv
docs/m1369-paper-route-public-base-promotion-generalization-gate-implementation.md
```

## Guardrails

M1368 performs no training, PPO, actor update, replay run, checkpoint mutation,
promotion, private holdout, threshold relaxation, actor-input expansion,
high-fidelity claim, paper-level claim, or level3 self-identification claim.

## Next

```text
m1369-paper-route-public-base-promotion-generalization-gate-implementation
```
