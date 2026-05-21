# M69 Broader Matched Hidden-Dynamics Mining

M68 validated the matched-action corpus harness on the M65 response-necessity
seeds, but found no privileged-packet action divergence. M69 broadens the search
to fresh seeds and three hidden perturbation axes:

```text
friction step
weak brake authority
slow actuator response
```

The purpose is to decide whether the missing self-identification signal is just
a narrow M65 corpus issue or a deeper teacher/action-sensitivity issue.

## Common Setup

Teacher checkpoint:

```text
runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt
```

Base env config:

```text
configs/ppo_m67e_warm_started_privileged_teacher.json
```

Matching thresholds:

```text
max_visible_distance = 0.75
max_response_distance = 0.25
max_context_distance = 0.05
min_action_distance = 0.05
```

Each sweep uses 80 fresh seeds.

## Commands

Friction:

```text
conda run -n autodrift python -m autodrift.matched_action_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 80 \
  --seed 6900 \
  --device cpu \
  --top-k 40 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-action-distance 0.05 \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --run-dir runs/m69_matched_action_friction_fresh80_seed6900
```

Weak brake:

```text
conda run -n autodrift python -m autodrift.matched_action_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 80 \
  --seed 7000 \
  --device cpu \
  --top-k 40 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-action-distance 0.05 \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization brake_scale_range=1.20,1.40 \
  --perturbed-randomization brake_scale_range=0.50,0.60 \
  --run-dir runs/m69_matched_action_brake_fresh80_seed7000
```

Slow actuator:

```text
conda run -n autodrift python -m autodrift.matched_action_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --episodes 80 \
  --seed 7100 \
  --device cpu \
  --top-k 40 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-action-distance 0.05 \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.85,1.15 \
  --nominal-randomization actuator_tau_scale_range=0.55,0.75 \
  --perturbed-randomization actuator_tau_scale_range=2.50,3.20 \
  --run-dir runs/m69_matched_action_actuator_fresh80_seed7100
```

## Results

| Axis | Pairs | Visible Matches | Action Div. | Paired-Action Div. | Wrong-History Div. | Privileged-Packet Div. | Mean Wrong-History Dist | Mean Priv-Packet Dist | Max Action Dist |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Friction | 80 | 21 | 13 | 13 | 1 | 0 | 0.033062 | 0.000041 | 0.466453 |
| Weak brake | 80 | 53 | 6 | 6 | 3 | 0 | 0.022678 | 0.000161 | 0.228988 |
| Slow actuator | 80 | 70 | 0 | 0 | 0 | 0 | 0.012402 | 0.001147 | 0.054836 |

Top wrong-history candidates:

| Axis | Seed | Max Action Dist | Max Wrong-History Dist | Max Priv-Packet Dist | Response Dist | Context Dist |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Friction | 6905 | 0.107268 | 0.051810 | 0.000037 | 0.227934 | 0.023754 |
| Weak brake | 7002 | 0.073994 | 0.052539 | 0.000156 | 0.188506 | 0.007218 |
| Weak brake | 7059 | 0.068511 | 0.052911 | 0.000180 | 0.175457 | 0.012620 |
| Weak brake | 7019 | 0.087074 | 0.069026 | 0.000190 | 0.240207 | 0.005826 |

## Interpretation

The broader sweep confirms the M68 diagnosis.

Useful signals:

- weak-brake perturbations produce more strict visible matches than friction;
- weak-brake also gives the most wrong-history divergent candidates;
- slow-actuator perturbations create many visible matches, but not action
  divergence for this teacher.

Negative signals:

- all three axes have zero privileged-packet divergent pairs;
- privileged-packet action distances remain tiny even when privileged-tail
  distance is large;
- paired-action divergence is still mostly driven by current response mismatch;
- current M67-E teacher is not using its teacher-only hidden packet in an
  action-relevant way.

Conclusion:

```text
M69 does not produce a clean teacher-distillation corpus.
It does produce a small wrong-history candidate set, especially on weak-brake
perturbations, that is worth testing with continuation outcomes.
```

## Next Step

Run a wrong-history continuation gate on the M69 candidate seeds.

The key question is no longer just "does the first action change?" It is:

```text
Does wrong recurrent history reduce clearance margin or cause failure when the
visible state is matched?
```

If the answer is no, the current task/teacher still does not create causal
self-identification evidence. If yes, those snippets become training and gate
targets for the next student objective.
