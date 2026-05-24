# M553 Route-Screen V2 Runner Implementation

## Purpose

M553 turns the M552 retrospective route-screen v2 check into reusable harness
infrastructure.

This milestone does not train or promote a checkpoint. It prevents future L3
repair pilots from using ad hoc route-health scripts or selecting a checkpoint
that is below L0 before public frozen-source diagnostics.

## Implementation

Added:

```text
src/autodrift/route_screen_v2.py
tests/test_route_screen_v2.py
```

The runner supports:

- named checkpoint policies;
- named env configs per policy;
- level-matched observation contracts, including L2 `history_length = 4`;
- one or more candidate labels;
- required L0 and L2 references;
- `episodes.csv`, `policy_summary.csv`, and `summary.json` artifacts;
- explicit `uses_public_frozen_source_rows = false` provenance;
- route-screen v2 lexicographic decision:
  - reject if candidate success is below L0;
  - reject if candidate mean clearance margin is below L0;
  - reject if candidate collision rate exceeds L0 by more than `0.02`;
  - rank admitted candidates by success, margin, collision, then return.

## Reproduction Command

```bash
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy l0_s3540=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l2_s3540=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_m542_s3540=runs/m542_matched_l3_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_m549_fast2816=runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt \
  --env-config-policy l0_s3540=configs/ppo_m541_matched_l0_variance_4096.json \
  --env-config-policy l2_s3540=configs/ppo_m541_matched_l2_variance_4096.json \
  --env-config-policy l3_m542_s3540=configs/ppo_m541_matched_l3_variance_4096.json \
  --env-config-policy l3_m549_fast2816=configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json \
  --candidate-label l3_m549_fast2816 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 64 \
  --seed 14540 \
  --device cpu \
  --run-dir runs/m553_route_screen_v2_runner_reproduce_m552
```

Output:

```text
would_admit_public_eval=False
selected_candidate_label=None
```

Artifacts:

```text
runs/m553_route_screen_v2_runner_reproduce_m552/summary.json
runs/m553_route_screen_v2_runner_reproduce_m552/policy_summary.csv
runs/m553_route_screen_v2_runner_reproduce_m552/episodes.csv
```

## Reproduction Result

The runner reproduces the M552 decision:

```text
candidate_success_minus_l0 = -0.015625
candidate_margin_minus_l0 = +0.257598
candidate_collision_minus_l0 = -0.140625

candidate_success_minus_l2 = -0.562500
candidate_margin_minus_l2 = -0.813875

passes_l0_success = false
passes_l0_margin = true
passes_l0_collision_tolerance = true
would_admit_public_eval = false
recommendation = block_public_eval_below_l0
```

The runner therefore would have blocked M549 before the M550 public
frozen-source diagnostic.

## Validation

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_route_screen_v2.py tests/test_benchmark.py tests/test_evaluate.py
```

Result:

```text
24 passed
```

The focused tests cover named checkpoint/config parsing, required level-matched
env configs, L0/L2 reference decision logic, multi-candidate selection, artifact
writing, and no-public-row provenance.

## Decision

```text
route_screen_v2_runner_pass_admit_m554_l3_repair_v2_design
```

## Next Step

M554 should design the next L3 recurrent repair branch under the new route-screen
v2 rule. No future L3 repair checkpoint should reach public frozen-source eval
unless it first clears the reusable route-screen v2 runner against L0.
