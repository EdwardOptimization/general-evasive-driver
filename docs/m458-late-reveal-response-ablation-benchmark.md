# M458 Late-Reveal Response Ablation Benchmark

## Purpose

M457 created a runnable late-reveal zero-relvel challenge config. M458 tests
whether that config produces stronger source-diverse response/history ablation
evidence before matched-current mining or training.

No checkpoint is trained or promoted in this milestone.

## Commands

Each variant was evaluated for `64` episodes on each seed window:

```text
9600-9663
9900-9963
10150-10213
```

Command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.evaluate \
  --episodes 64 \
  --seed <seed_base> \
  --policy checkpoint \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-ablation <none|reset_recurrent_state|zero_current_response|zero_action_history> \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --run-dir runs/m458_late_reveal_<variant>_seed<seed_base> \
  --device cpu
```

Aggregate artifacts:

```text
runs/m458_late_reveal_ablation_summary/summary.json
runs/m458_late_reveal_ablation_summary/aggregate_summary.csv
runs/m458_late_reveal_ablation_summary/per_seed_summary.csv
runs/m458_late_reveal_ablation_summary/success_flips.csv
```

## Aggregate Results

The benchmark covers `768` total rollouts: `192` per variant.

| variant | success | termination | collision | return | clearance | success delta | return delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base | 0.812500 | 0.187500 | 0.166667 | 73.340898 | 2.107460 | 0.000000 | 0.000000 |
| reset recurrent | 0.817708 | 0.182292 | 0.161458 | 71.296894 | 2.131759 | 0.005208 | -2.044004 |
| zero current response | 0.802083 | 0.197917 | 0.177083 | 68.858890 | 2.131656 | -0.010417 | -4.482009 |
| zero action history | 0.822917 | 0.177083 | 0.156250 | 73.804156 | 2.106641 | 0.010417 | 0.463258 |

Zero-current response lowers return, but it does not create a strong success or
clearance degradation. Reset recurrent state is slightly better than base on
success, and zero-action-history is also slightly better. This is not strong
recurrent-history necessity evidence.

## Episode-Level Flips

Base-success to ablation-fail flips:

| seed base | reset | zero current | zero action history |
| --- | ---: | ---: | ---: |
| `9600` | 0 | 2 | 0 |
| `9900` | 2 | 2 | 0 |
| `10150` | 0 | 0 | 0 |
| total | 2 | 4 | 0 |

The row-level evidence is sparse but not empty. Zero-current has four
base-success to ablation-fail rows and a larger return drop than reset or
no-action. That is enough to justify a targeted matched-current mining run, but
not enough to justify training or a self-ID claim.

## Interpretation

M458 weakens the idea that the M457 late-reveal distribution alone creates
clean recurrent-history necessity. It improves over the 16-episode smoke by
showing a consistent zero-current return penalty, but the success and clearance
signals remain weak.

The next step should therefore be row-level POMDP ambiguity mining:

```text
same visible current state/context,
different hidden dynamics or response history,
different future margin/action/outcome sensitivity.
```

Do not start PPO from this result. Aggregate benchmark metrics are still too
weak, and the evidence must move from aggregate ablations to matched-current
interventions.

## Decision

M458 passes as a non-promotion diagnostic gate:

- all planned runs complete without scenario sampling failure;
- results cover three seed windows;
- no actor contract changes;
- no checkpoint is promoted.

Decision:

```text
weak_aggregate_admit_m459_matched_current_mining
```
