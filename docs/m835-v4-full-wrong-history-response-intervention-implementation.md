# M835 V4 Full Wrong-History Response Intervention Implementation

## Purpose

M835 implements the no-training response/action observation intervention
designed in M834.

The experiment question is:

```text
Does swapping deployable ego-response/action observation fields from matched
wrong-history sources create stronger counterfactual action or margin
degradation than hidden-only injection?
```

M835 is implementation/data-route only:

```text
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_full_wrong_history_response_intervention.py
```

New tests:

```text
tests/test_v4_full_wrong_history_response_intervention.py
```

The implementation:

- reuses M832 near-boundary pairs and accepted boundary rows;
- reconstructs left/right snapshots from M825 source rows;
- keeps left environment dynamics and left scene context fixed;
- swaps only deployable observation fields in the first policy step;
- separates hidden-only, ego-response-only, previous-command-only, and combined
  variants;
- keeps zero-command evidence separate;
- verifies frozen actor and M761 residual-head checksums.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_full_wrong_history_response_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --near-boundary-pairs runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m835_v4_full_wrong_history_response_intervention \
  --device cpu
```

## Result

Run directory:

```text
runs/m835_v4_full_wrong_history_response_intervention
```

Summary:

```text
result_class: v4_full_wrong_history_response_intervention_all_weak
raw_pair_rows: 60
selected_pair_rows: 60
reconstructed_snapshot_rows: 16
response_intervention_replay_rows: 540
accepted_primary_response_history_rows: 0
accepted_component_attribution_rows: 0
accepted_mitigation_rows: 0
zero_command_component_like_rows: 0
```

Checksums stayed unchanged:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

## Variant Results

Per-variant maximum action and margin effects:

```text
wrong_hidden_only:
  max_action: 0.006654849690777518
  max_gap:    0.000036904085711997325

wrong_ego_response_obs:
  max_action: 0.004164497484585927
  max_gap:    0.0000773029595060315

wrong_action_history_obs:
  max_action: 0.011563982377362824
  max_gap:    0.0001976526344089624

wrong_response_action_obs:
  max_action: 0.014695116575514424
  max_gap:    0.0002744146905726552

wrong_ego_response_hidden:
  max_action: 0.00910725583954952
  max_gap:    0.00010486855160873887

wrong_action_history_hidden:
  max_action: 0.017168803000693903
  max_gap:    0.0002169713213744373

wrong_response_action_hidden:
  max_action: 0.019600431767721204
  max_gap:    0.00030215729621496656

zero_command_obs:
  max_action: 0.03573703003115858
  max_gap:    0.004670113250027308
```

Thresholds:

```text
action_l2_threshold: 0.014
primary_margin_gap_threshold: 0.01
mitigation_margin_gap_threshold: 0.02
```

Some response/action variants cross the action threshold, but none produce a
meaningful margin or outcome effect.

## Interpretation

M835 supports:

- response/action observation swaps are implemented;
- left scene context and left dynamics stay fixed;
- actor and residual-head contracts are preserved;
- current response/action swaps can move first action more than hidden-only;
- those action changes still do not affect near-boundary outcome enough.

M835 does not support:

- primary response-history proof;
- component attribution proof;
- mitigation proof;
- zero-command dominated proof;
- PPO admission or checkpoint promotion.

The important negative result is:

```text
The M568/M761 family is not behaviorally sensitive enough to hidden or current
response/action counterfactuals on the M832 near-boundary pair set.
```

This is stronger than M832: it shows the blocker is not only hidden-state
injection. Even direct response/action observation swaps do not create terminal
margin effects.

## Failure Taxonomy

### metric_artifact

Several variants produce action drift, but margin effects remain tiny. Action
drift alone is not proof.

### scenario_sampling_failure

The input pair set remains the M832 `60` pairs, below the source-diverse `80`
row target.

### not contract_violation

All checksums are unchanged and no forbidden inputs were added.

## Decision

Decision:

```text
v4_full_wrong_history_response_intervention_all_weak
```

Next:

```text
m836-v4-full-wrong-history-response-intervention-audit
```

M836 should decide whether this branch should pivot from more no-training
interventions to objective/architecture evidence, because both hidden-only and
response/action counterfactuals are outcome-weak on current M568/M761 behavior.
