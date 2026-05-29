# M1650 Paper-Route Proposal Source Preflight Implementation

## Summary

M1650 implements and runs the no-checkpoint proposal-source preflight admitted
by M1649.

Decision:

```text
proposal_source_preflight_public_pass_route_to_audit
```

The preflight enumerated the M1362 same-line interpolation candidates, computed
contour-aware exact residual metrics against the M1630 target tensors, recorded
parameter deltas to the M1362 alpha `0.1` base, and selected repair candidates
as metadata only.

No PPO was run, no training was started, no projection or proposal repair was
run, no checkpoint artifact was written, no closed-loop evaluation was run, no
private holdout was used, actor inputs were unchanged, diagnostics remained
zero-weight, donor-plus actions stayed excluded from loss targets, and no
paper-level or level3 self-identification claim is made.

## Implementation

Added:

```text
src/autodrift/proposal_source_preflight.py
tests/test_proposal_source_preflight.py
```

The preflight input was:

```text
base checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

candidate checkpoint table:
  runs/m1362_bidirectional_active_set_interpolation_preflight/candidate_checkpoints.csv

alpha summary:
  runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv

materialized contour-aware target tensors:
  runs/m1630_contour_aware_full_target_materialization
```

The run writes:

```text
runs/m1650_proposal_source_preflight/summary.json
runs/m1650_proposal_source_preflight/candidate_summary.csv
runs/m1650_proposal_source_preflight/guardrail_summary.csv
```

Per-candidate exact evaluator artifacts are under:

```text
runs/m1650_proposal_source_preflight/candidates/
```

These contain metrics only, not checkpoint artifacts.

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_proposal_source_preflight.py
```

Result:

```text
2 passed in 2.05s
```

Official M1650 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.proposal_source_preflight \
  --base-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --candidate-checkpoints runs/m1362_bidirectional_active_set_interpolation_preflight/candidate_checkpoints.csv \
  --alpha-summary runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --run-dir runs/m1650_proposal_source_preflight
```

Result:

```text
source_candidate_count: 10
branch_compatible_candidate_count: 10
base_anchor_count: 1
larger_proposal_candidate_count: 5
selected_repair_candidate_count: 5
checkpoint_artifact_count: 0
projection_used_count: 0
passes_public_smoke_gates: true
null_result_classification: proposal_source_preflight_public_pass
```

## Candidate Roles

Base anchor:

```text
alpha 0.1
```

Smaller controls:

```text
alpha 0.005
alpha 0.01
alpha 0.02
alpha 0.05
```

Selected repair candidates:

```text
alpha 0.2
alpha 0.4
alpha 0.6
alpha 0.8
alpha 1.0
```

The selected candidates are branch-compatible same-line proposals. They are
not PPO proposals. They are useful public proposal stressors because they are
larger M1362-line checkpoint deltas with measurable contour-aware exact
residuals and known public-gate rejection in the M1362 preflight.

Selected candidate residuals:

| Alpha | Positive Exact Residual Mean | Positive Action L2 Max | Diagnostic Action L2 Max |
| --- | ---: | ---: | ---: |
| 0.2 | 0.001240136641487762 | 0.03317370158431797 | 0.03448836653872263 |
| 0.4 | 0.010803107091018185 | 0.09548378557478591 | 0.10080410393764744 |
| 0.6 | 0.028754241166433388 | 0.15339418121822723 | 0.16388278349456725 |
| 0.8 | 0.05361722999772134 | 0.20775189182589224 | 0.2242077662719857 |
| 1.0 | 0.08403469693915355 | 0.2593698487493319 | 0.28150499236325854 |

## Guardrails

Guardrail counts:

```text
checkpoint_artifact_count: 0
projection_used_count: 0
proposal_repaired_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
actor_input_contract_changed_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
level3_self_id_claim_count: 0
```

No `.pt` or `.pth` files exist under the M1650 run directory.

## Supported Claims

M1650 supports:

```text
M1362 same-line interpolation candidates are branch-compatible proposal sources;
the M1630 contour-aware exact target evaluator can measure their action residuals;
five larger same-line proposals are available as repair-candidate metadata;
the proposal-source preflight can run without projection, repair, PPO, or checkpoint writes;
diagnostic and donor-plus role guardrails remain clean.
```

## Unsupported Claims

M1650 does not support:

```text
proposal repair works;
PPO-proposal repair works;
checkpoint artifact generation;
closed-loop replay improvement;
behavior retention;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to result audit:

```text
m1651-paper-route-proposal-source-preflight-result-audit
```

M1651 should audit whether M1650 is sufficient to admit a selected-proposal
no-checkpoint repair design. It should not run repair, projection, PPO,
closed-loop evaluation, checkpoint artifact generation, promotion, private
holdout, actor-input changes, or level3 self-ID claims.
