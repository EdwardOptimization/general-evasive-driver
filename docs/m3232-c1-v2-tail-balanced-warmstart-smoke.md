# M3232: C1 v2 Tail-balanced Warm-start Smoke

Status: failed. This is a revised C1 protocol quick smoke only. It does not
complete C1, admit C2, mutate the incumbent, or make a driver-performance,
validation, promotion, high-fidelity sufficiency, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3232-c1-v2-tail-balanced-warmstart-smoke.json`
- V2 preregistration: `experiments/feasibility_audit/c5prime_c1_oracle_bc_v2_prereg.json`
- Quick summary: `experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart_v2_quick.json`
- Quick checkpoint: `runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/v2_tail_balanced/quick/checkpoint.pt`
- Quick dataset: `runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/v2_tail_balanced/quick/dataset.npz`
- Harness log: `runs/research/m3232-c1-v2-tail-balanced-warmstart-smoke_20260612T062602Z/command.log`

## Preregistered Revision

M3232 keeps the M3228 validation action-MSE gate unchanged. The v2
pre-registration changes the row design instead of changing the criterion:

- new seed base: `20260819`;
- base panel: one structured-oracle row per S1/S2/S3 T-limit instance;
- rare-tail support: distinct train and validation rows for
  `structured:coast_steer_+0.7` and `structured:coast_steer_-0.7`;
- heldout-family support: distinct train rows for any remaining oracle action
  family that appears in selection/validation but is absent from train.

The frozen v2 preregistration contains 41 rows: train 26, selection 8, and
validation 7.

## Measured

The harness command returned `1` after writing the quick summary, checkpoint,
and dataset artifacts. Demo replay was not the failure: every selected quick
demo replayed to `success_obstacle_pass`.

Quick gates:

| gate | value |
|---|---:|
| demo replay all success | true |
| checkpoint exists | true |
| dataset exists | true |
| validation action-MSE gate passed | false |
| all passed | false |

BC readouts:

| readout | value |
|---|---:|
| validation action MSE | 0.291470 |
| zero-action baseline MSE | 0.559903 |
| selection MSE at selected epoch | 0.026215 |
| train MSE at selected epoch | 0.135366 |
| validation rollout success context | 2/3 |

The quick validation rows included both rare coast probes:

| row | oracle | rollout outcome |
|---|---|---|
| `S3-inst04-seed7720117` | `structured:coast_steer_+0.7` | success |
| `S2-inst08-seed7540299` | `structured:coast_steer_-0.7` | off_track |
| `S1-inst00-seed7300026` | `structured:brake_steer_+0.4` | success |

## Interpretation

M3232 confirms that merely adding rare-tail support rows is not enough to make
the current MLP BC warm-start clear the frozen C1 behavior gate when rare coast
tail probes are included in validation. The failure is not an artifact-writing
or demo-replay issue; it is still behavior imitation quality under the held-out
gate.

The 2/3 validation rollout success context is useful but cannot override the
pre-registered action-MSE failure.

## Decision

C1 remains open. Do not run the full v2 warm-start or start C2 from this
artifact. Because M3228 full and M3232 quick both failed action-MSE gates on
the same C1 target, the next C1 step should be synthesis/repricing before any
additional local BC repair.
