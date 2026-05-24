# M583 BC5660 Recurrent Ablation Moderate-OOD Eval

## Purpose

M583 repeats the M582 recurrent-ablation diagnostic on the moderate-OOD route
distribution from M574. It uses the same checkpoint, ablation set, and
pre-registered M581 degradation thresholds.

This milestone is diagnostic only:

```text
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Command

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --policies checkpoint \
  --checkpoint-policy bc5660_normal=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy bc5660_reset=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy bc5660_zero_current=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_current_response \
  --checkpoint-policy bc5660_zero_action=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_action_history \
  --checkpoint-policy bc5660_zero_all=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt@zero_all_response \
  --episodes 256 \
  --seed 24560 \
  --device cpu \
  --env-config configs/eval_m574_moderate_ood_l3.json \
  --run-dir runs/m583_bc5660_recurrent_ablation_moderate_ood_eval
```

## Artifacts

```text
runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/manifest.json
runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/episodes.csv
runs/m583_bc5660_recurrent_ablation_moderate_ood_eval/policy_summary.csv
```

`episodes.csv` has `1281` rows: one header plus `5 * 256` evaluated episodes.

## Results

| policy | success | collision | return | mean margin | min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| bc5660_normal | 0.621094 | 0.378906 | 61.001557 | 0.985368 | -0.316697 |
| bc5660_reset | 0.617188 | 0.382812 | 60.824774 | 0.972476 | -0.326826 |
| bc5660_zero_action | 0.605469 | 0.394531 | 60.098648 | 0.948422 | -0.331259 |
| bc5660_zero_all | 0.585938 | 0.414062 | 58.835028 | 0.885047 | -0.290747 |
| bc5660_zero_current | 0.585938 | 0.414062 | 58.835028 | 0.885047 | -0.290747 |

Delta against `bc5660_normal`:

| ablation | success drop | margin drop | collision increase | return delta | label |
| --- | ---: | ---: | ---: | ---: | --- |
| reset_recurrent_state | 0.003906 | 0.012892 | 0.003906 | -0.176783 | weak |
| zero_action_history | 0.015625 | 0.036946 | 0.015625 | -0.902909 | weak |
| zero_all_response | 0.035156 | 0.100321 | 0.035156 | -2.166529 | strong |
| zero_current_response | 0.035156 | 0.100321 | 0.035156 | -2.166529 | strong |

## Interpretation

M583 repeats the main M582 signal under moderate-OOD conditions:
`zero_current_response` and `zero_all_response` both cause meaningful success
and collision degradation and cross the strong margin threshold.

The result supports this narrower claim:

```text
BC5660 behavior depends on the deployable current ego/IMU-like response stream
on both fresh same-distribution and moderate-OOD route seeds.
```

It does not yet support the stronger claim:

```text
BC5660 needs accumulated online-GRU hidden belief over longer command-response
history on these route distributions.
```

`reset_recurrent_state` remains weak, and `zero_action_history` is weaker on
moderate-OOD than it was on M582. The current evidence is therefore response
dependence first, not full recurrent self-identification. The next milestone
should audit M582/M583 together and choose a sharper intervention, likely
wrong-history or delayed-history, before promotion or PPO.

## Decision

```text
bc5660_ood_response_ablation_positive_admit_m584_audit
```

M583 passes as a positive moderate-OOD current-response ablation diagnostic.
Promotion and PPO remain blocked.

## Next

```text
M584: audit M582/M583 ablation evidence and select the next self-ID diagnostic.
```
