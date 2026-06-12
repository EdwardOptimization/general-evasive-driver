# M3229: C1 BC Warm-start Failure Localization

Status: completed. This is a post-failure diagnostic over M3228 only. It does
not train a new model, change the M3228 criteria, mutate the incumbent, admit
C2, or make a driver-performance, validation, promotion, high-fidelity, paper,
repair-success, robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3229-c1-bc-warmstart-failure-localization.json`
- Diagnostic summary: `experiments/feasibility_audit/c5prime_c1_failure_localization.json`
- Source M3228 summary: `experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart.json`
- Source checkpoint: `runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full/checkpoint.pt`
- Harness log: `runs/research/m3229-c1-bc-warmstart-failure-localization_20260612T040821Z/command.log`

## Measured

M3229 reloaded the failed M3228 checkpoint and replayed the frozen structured
oracle labels. The original full-run gate readout is preserved:

| M3228 gate readout | value |
|---|---:|
| validation action MSE | 0.234184 |
| zero-action baseline MSE | 0.501099 |
| validation BC rollout success context | 0.5000 |
| validation MSE gate passed | false |

Frame-weighted MSE decomposition:

| slice | MSE |
|---|---:|
| train | 0.022291 |
| selection | 0.074735 |
| validation | 0.234184 |
| validation prefix | 0.026446 |
| validation tail | 0.369957 |

By action channel:

| channel | MSE |
|---|---:|
| brake | 0.201318 |
| steer | 0.073152 |
| throttle | 0.009926 |

By level:

| level | MSE |
|---|---:|
| S1 | 0.028084 |
| S2 | 0.124519 |
| S3 | 0.137524 |

Diagnostic flags:

- `selection_validation_mse_gap`
- `tail_action_generalization_dominates`
- `rollout_context_better_than_action_mse_gate`

## Interpretation

The failed gate is not a demo-replay or artifact-writing failure. It is a
generalization failure of the MLP BC warm-start under the frozen held-out split.
The prefix behavior is learned well, but validation tail actions dominate the
error, especially brake-channel actions on S2/S3. The 5/10 validation rollout
success context is useful but cannot override the failed preregistered action
MSE gate.

## Decision

C1 remains open. M3228 must not be marked as a successful C1 completion. Any
next C1 attempt needs a new preregistration that addresses the
selection/validation gap and tail-action generalization failure before running
new warm-start training. C2 remains blocked on C1.
