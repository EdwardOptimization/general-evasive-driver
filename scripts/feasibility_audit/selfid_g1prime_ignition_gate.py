"""G1' ignition gate: can a HISTORY-bearing learner learn the probe->commit map
from demonstrations, and does that ability actually DEPEND on history?

Supervised-level replacement for the G1 RL ignition gate (M3214 FAIL was a
variance bed, not an identifiability verdict). Pure CPU, minutes-scale
supervised training (the only training allowed in this phase), new files only.

Task family: the FINAL B2K2 spec (experiments/feasibility_audit/
selfid_task_final_spec.json) -- continuous mu in [0.25, 1.15], mu-correlated
jittered hazard distance, reveal 10 m, deadline, recalibrated rewards. The env
family, jitter law and seed-stream conventions are loaded from the spec JSON at
runtime so G1' always measures the final spec, never a stale copy.

Teacher (scripted per-mu oracle, phase-1 machinery):
  steps 0..11   track v0 = 8 m/s (mu-independent),
  steps 12..21  full-brake PROBE PULSE (= PULSES[0] of the Task-B controller,
                so the gate anchor frame <= step 11 stays pre-pulse),
  step  22..    COMMIT: track v_oracle_est(mu) (privileged mu, piecewise-linear
                design-oracle speed knots from the final spec),
  post-reveal   reactive swerve avoidance (CommitmentController reaction,
                steer_cap 0.85 / offset 3.0 / gain 3.0).
Only the teacher sees mu. Demonstrations keep SUCCESS episodes only.

Two arms, parameter-aligned (+/-10 %), hidden <= 64, same demo data, same
epoch/batch budget, same optimizer (Adam, lr 1e-3, MSE on actions):
  history arm        GRU(72 -> 40) + Linear(40 -> 3), tanh
  current-frame arm  MLP 72 -> 64 -> 64 -> 64 -> 3 (ReLU, tanh out), sees ONLY
                     the current frame (identical per-frame features).
8 seeds per arm (init + batch order); every run is evaluated CLOSED-LOOP on the
SAME held-out continuous-mu episode set (paired across arms and seeds).

#############################  PRE-REGISTRATION  #############################
Written BEFORE any G1' training or evaluation run. The mechanical copy of this
block is emitted to experiments/feasibility_audit/selfid_g1prime_preregistration.json
at process start, before demonstrations / training / evaluation execute.

Primary criterion (adjudicating). Per run, compute Spearman(speed_at_reveal,
mu) over held-out closed-loop episodes that reach a reveal crossing.
  G1' PASS  =  (a) history-arm 8-seed MEDIAN Spearman >= 0.8
          AND (b) current-frame-arm 8-seed MEDIAN Spearman <= 0.4
          AND (c) the 8-seed PAIRED bootstrap 95 % CI (10000 resamples,
                  percentile 2.5/97.5) of (history - current) per-seed
                  Spearman excludes 0 (CI low > 0).

FAIL semantics (pre-registered routing):
  history median < 0.8                  -> TEACHER/TASK REWORK: the task or the
                                           demonstration design goes back to the
                                           drawing board (no RL escalation).
  history >= 0.8 AND current > 0.4      -> CURRENT-FRAME LEAK: both arms learn
                                           the map, the gate self-check fails,
                                           route back to P4 protocol review.
  medians in range, CI contains 0       -> UNDERPOWERED: more seeds/demos, rerun;
                                           no capability claim either way.
  history < 0.8 AND current > 0.4       -> LEAK + WEAK TEACHER: P4 review first,
                                           then teacher rework.

Validity preconditions (run is void, not FAIL, if violated):
  kept (successful) demos >= 60 % of generated (>= 240 of 400);
  >= 50 % of eval episodes reach a reveal crossing per run (>= 32 of 64),
  runs below that are invalid; each arm needs >= 6 of 8 valid runs.

Auxiliary readouts (NOT adjudicating): hidden-reset ablation of the history arm
(zero the GRU state at the commitment step 22 -- the signature should degrade);
free-prior hedge baseline (medium-bin best fixed plan from the final spec)
signature; teacher closed-loop signature; per-arm panel success vs the gate-3
bar; preparation-segment action energy vs the no-probe baseline (S2 analogue).
##############################################################################

Claim boundary: feasibility-audit ignition-gate measurement only -- scripted
demonstrations and minutes-scale supervised imitation probes of HISTORY
DEPENDENCE. No driver-performance, repair-success, robustness, validation,
ranking, promotion, paper, or self-ID *capability* claim is made.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/selfid_g1prime_ignition_gate.py
    PYTHONPATH=src python scripts/feasibility_audit/selfid_g1prime_ignition_gate.py --quick
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
FINAL_SPEC_SCRIPT = REPO / "scripts/feasibility_audit/selfid_task_final_spec.py"
FINAL_SPEC_JSON = REPO / "experiments/feasibility_audit/selfid_task_final_spec.json"
RUN_DIR = REPO / "runs/feasibility_audit/selfid_g1prime"
SUMMARY_JSON = REPO / "experiments/feasibility_audit/selfid_g1prime_summary.json"
PREREG_JSON = REPO / "experiments/feasibility_audit/selfid_g1prime_preregistration.json"

G1_SEED = 20260616  # fresh stream (final spec = 20260615)
OBS_DIM = 72
DT = 0.02
V0 = 8.0
PULSE_START, PULSE_END = 12, 22  # = PULSES[0] of the Task-B controller
COMMIT_STEP = 22  # first post-pulse step: teacher switches to v_oracle_est(mu)
MU_LO, MU_HI = 0.25, 1.15

GRU_HIDDEN = 40
MLP_HIDDEN = (64, 64, 64)
EPOCHS = 25
LR = 1e-3
BATCH_EPISODES = 16
GRAD_CLIP = 1.0

DEMO_SEED_OFFSET = 300000  # env seeds G1_SEED*10 + 300000 + i (disjoint from phase-1)
EVAL_SEED_OFFSET = 600000  # env seeds G1_SEED*10 + 600000 + j

PREREGISTERED_CRITERIA: dict[str, Any] = {
    "question": (
        "Can a history-bearing learner learn the probe->commit mapping from "
        "demonstrations on the final B2K2 spec, and does that ability depend on history?"
    ),
    "signature": "per-run Spearman(speed_at_reveal, mu) on held-out closed-loop episodes",
    "pass_rule": {
        "history_median_min": 0.8,
        "current_median_max": 0.4,
        "paired_bootstrap": {"resamples": 10000, "ci_percentiles": [2.5, 97.5],
                             "rule": "CI of per-seed (history - current) must exclude 0 (low > 0)"},
        "all_three_conjunctive": True,
    },
    "fail_semantics": {
        "history_lt_0.8": "TEACHER/TASK REWORK -- task or demonstration design goes back; no RL escalation",
        "history_geq_0.8_and_current_gt_0.4": "CURRENT-FRAME LEAK -- gate self-check fails; route to P4 protocol review",
        "medians_ok_ci_contains_0": "UNDERPOWERED -- more seeds/demos and rerun; no claim",
        "history_lt_0.8_and_current_gt_0.4": "LEAK + WEAK TEACHER -- P4 review first, then teacher rework",
    },
    "validity_preconditions": {
        "kept_demo_fraction_min": 0.60,
        "min_reveal_coverage_per_run": 0.50,
        "min_valid_runs_per_arm": 6,
    },
    "auxiliary_non_adjudicating": [
        "history-arm hidden-reset ablation at the commitment step (signature should degrade)",
        "free-prior hedge baseline (medium-bin best fixed plan) signature",
        "teacher closed-loop signature (privileged ceiling)",
        "per-arm panel success vs the gate-3 bar from the final spec",
        "preparation-segment action energy vs the no-probe baseline (S2 analogue)",
    ],
    "design_constants": {
        "arms": {"history": f"GRU(72->{GRU_HIDDEN}) + Linear({GRU_HIDDEN}->3), tanh",
                 "current_frame": f"MLP 72->{'->'.join(map(str, MLP_HIDDEN))}->3, ReLU, tanh out"},
        "parameter_alignment_tolerance": 0.10,
        "hidden_cap": 64,
        "optimizer": f"Adam lr={LR}, epochs={EPOCHS}, batch={BATCH_EPISODES} episodes, MSE, grad clip {GRAD_CLIP}",
        "seeds_per_arm": 8,
        "demos_generated": 400,
        "demo_filter": "keep success episodes only",
        "eval_episodes_per_run": 64,
        "eval_pairing": "identical (mu, env seed) eval set for every run and arm",
        "teacher": "track v0=8 (steps 0..11), full-brake pulse (12..21), commit v_oracle_est(mu) from step 22, reactive swerve post-reveal",
        "seed_streams": {
            "demo_env": f"{G1_SEED}*10 + {DEMO_SEED_OFFSET} + i",
            "demo_mu": f"U({MU_LO},{MU_HI}) from default_rng([{G1_SEED}, 1, i])",
            "eval_env": f"{G1_SEED}*10 + {EVAL_SEED_OFFSET} + j",
            "eval_mu": f"U({MU_LO},{MU_HI}) from default_rng([{G1_SEED}, 2, j])",
            "torch": f"{G1_SEED}*1000 + seed*10 + arm_index",
            "batch_order": f"default_rng([{G1_SEED}, 5, seed]) (shared by both arms)",
        },
    },
}

CLAIM_BOUNDARY = (
    "Feasibility-audit ignition-gate measurement only: scripted per-mu oracle demonstrations "
    "and minutes-scale supervised imitation probes of HISTORY DEPENDENCE on the final B2K2 "
    "commitment family. No driver-performance, repair-success, robustness-result, validation, "
    "ranking, promotion, paper, or self-ID *capability* claim is made."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_family():
    """Rebuild the final-spec task family (design, variant, knobs) from the JSON."""
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_f = load_module(FINAL_SPEC_SCRIPT, "selfid_task_final_spec")
    spec = json.loads(FINAL_SPEC_JSON.read_text(encoding="utf-8"))
    fs = spec["final_spec"]
    env_knobs = fs["env_knobs"]
    fam = fs["scenario_family"]
    knobs = mod_f.Knobs(
        iteration=0,
        reveal_distance=float(env_knobs["perception_reveal_distance_m"]),
        max_steps=int(env_knobs["max_steps"]),
        obstacle_half_width=float(env_knobs["obstacle_half_width_m"]),
        jitter_d_m=float(fam["distance_jitter"]["J_m"]),
        mu1=float(fam["theta_anchors_mu"][0]),
        pass_reward=float(env_knobs["pass_reward"]),
        collision_penalty=float(env_knobs["collision_penalty"]),
        d_knots=tuple(float(x) for x in fam["mu_to_distance_knots"]["d_m"]),
        v_oracle_knots=tuple(float(x) for x in fam["design_oracle_speed_knots"]["v_mps"]),
        note="G1prime (from final spec JSON)",
    )
    design = mod_f.make_design(mod_b, knobs)
    variant = mod_f.make_variant(mod_c, knobs)
    spec_digest = {
        "generated_at_utc": spec.get("generated_at_utc"),
        "all_acceptance_pass": spec.get("all_acceptance_pass"),
        "gate3_bar": spec.get("final_iteration_detail", {}).get("gate3_bar_recomputed"),
        "best_fixed_plan": spec.get("final_iteration_detail", {}).get("medium_bin", {}).get("best_fixed_all_plan"),
        "knobs": {
            "reveal_distance": knobs.reveal_distance, "max_steps": knobs.max_steps,
            "obstacle_half_width": knobs.obstacle_half_width, "jitter_d_m": knobs.jitter_d_m,
            "pass_reward": knobs.pass_reward, "collision_penalty": knobs.collision_penalty,
            "d_knots": list(knobs.d_knots), "v_oracle_knots": list(knobs.v_oracle_knots),
        },
    }
    return mod_b, mod_c, mod_f, knobs, design, variant, spec, spec_digest


# -------------------------------------------------------------------- teacher


class OracleTeacher:
    """Scripted per-mu oracle: v0 hold -> brake probe pulse -> commit v(mu) ->
    reactive swerve. Only the teacher is given mu (through v_mu)."""

    def __init__(self, mod_b, design, v_mu: float):
        plan = mod_b.PlanSpec(name="g1_teacher", v_entry=float(v_mu), brake_to=None,
                              swerve_offset=3.0, swerve_gain=3.0, steer_cap=0.85)
        self.inner = mod_b.CommitmentController(plan, design)

    def reset(self) -> None:
        self.inner.reset()

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def act(self, obs: np.ndarray) -> np.ndarray:
        inner = self.inner
        t = inner.t
        action = inner.act(obs)
        if inner.reveal_step is None and t < COMMIT_STEP:
            vx = float(obs[0]) * 20.0
            if t < PULSE_START:
                throttle, brake = inner._speed_actions(vx, V0)
                action = np.asarray([float(action[0]), throttle, brake], dtype=np.float64)
            else:  # PULSE_START <= t < PULSE_END: full-brake probe pulse
                action = np.asarray([float(action[0]), -1.0, 1.0], dtype=np.float64)
        return action


def demo_mu(i: int) -> float:
    return float(np.random.default_rng([G1_SEED, 1, i]).uniform(MU_LO, MU_HI))


def eval_mu(j: int) -> float:
    return float(np.random.default_rng([G1_SEED, 2, j]).uniform(MU_LO, MU_HI))


def generate_demos(mod_b, mod_f, knobs, design, variant, n_demos: int):
    pool = mod_f.EnvPool(mod_b, design, variant, knobs)
    frames_all: list[np.ndarray] = []
    actions_all: list[np.ndarray] = []
    lengths: list[int] = []
    meta_rows: list[dict[str, Any]] = []
    kept = 0
    try:
        for i in range(n_demos):
            mu = demo_mu(i)
            seed = G1_SEED * 10 + DEMO_SEED_OFFSET + i
            env = pool.env_for(mu, seed)
            teacher = OracleTeacher(mod_b, design, variant.v_oracle_est(mu))
            obs, info = env.reset(seed=seed)
            teacher.reset()
            assert len(np.asarray(obs)) == OBS_DIM
            frames: list[np.ndarray] = []
            actions: list[np.ndarray] = []
            episode_return = 0.0
            terminated = truncated = False
            while not (terminated or truncated):
                o = np.asarray(obs, dtype=np.float64)
                a = teacher.act(o)
                frames.append(o.astype(np.float32))
                actions.append(np.asarray(a, dtype=np.float32))
                obs, r, terminated, truncated, info = env.step(a)
                episode_return += float(r)
            bucket = mod_b.outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            success = bucket == "success_obstacle_pass"
            meta_rows.append({
                "demo_index": i, "seed": seed, "mu": round(mu, 4),
                "outcome_bucket": bucket, "success": success, "steps": len(frames),
                "return": round(episode_return, 2),
                "reveal_step": -1 if teacher.reveal_step is None else int(teacher.reveal_step),
                "speed_at_reveal": round(float(teacher.speed_at_reveal), 3)
                if math.isfinite(teacher.speed_at_reveal) else None,
                "kept": success,
            })
            if success:
                frames_all.append(np.stack(frames))
                actions_all.append(np.stack(actions))
                lengths.append(len(frames))
                kept += 1
    finally:
        pool.close()
    return frames_all, actions_all, lengths, meta_rows, kept


# ------------------------------------------------------------ worker (1 run)


def _build_models(arm: str):
    import torch
    from torch import nn

    if arm == "history":
        class GRUPolicy(nn.Module):
            def __init__(self):
                super().__init__()
                self.gru = nn.GRU(OBS_DIM, GRU_HIDDEN, batch_first=True)
                self.head = nn.Linear(GRU_HIDDEN, 3)

            def forward(self, x):  # B,T,obs -> B,T,3
                out, _ = self.gru(x)
                return torch.tanh(self.head(out))

            def step(self, x, h):  # 1,obs -> (1,3), h
                out, h2 = self.gru(x.view(1, 1, -1), h)
                return torch.tanh(self.head(out.view(1, -1))), h2

        return GRUPolicy()

    class MLPPolicy(nn.Module):
        def __init__(self):
            super().__init__()
            layers: list[Any] = []
            prev = OBS_DIM
            for width in MLP_HIDDEN:
                layers += [nn.Linear(prev, width), nn.ReLU()]
                prev = width
            layers.append(nn.Linear(prev, 3))
            self.net = nn.Sequential(*layers)

        def forward(self, x):
            return torch.tanh(self.net(x))

    return MLPPolicy()


def param_count(model) -> int:
    return int(sum(p.numel() for p in model.parameters()))


class TorchController:
    """Closed-loop adapter exposing the Task-B rollout interface."""

    def __init__(self, torch_mod, model, mean: np.ndarray, std: np.ndarray,
                 recurrent: bool, reset_hidden_at: int | None = None):
        self.torch = torch_mod
        self.model = model
        self.mean, self.std = mean, std
        self.recurrent = recurrent
        self.reset_hidden_at = reset_hidden_at
        self.reset()

    def reset(self) -> None:
        self.t = 0
        self.dist = 0.0
        self.reveal_step: int | None = None
        self.speed_at_reveal = float("nan")
        self.dist_at_reveal = float("nan")
        self.prep_action_sq_sum = 0.0
        self.prep_steps = 0
        self.hidden = None

    def act(self, obs: np.ndarray) -> np.ndarray:
        torch = self.torch
        vx = float(obs[0]) * 20.0
        self.dist += max(vx, 0.0) * DT
        if float(obs[44]) > 0.5 and self.reveal_step is None:
            self.reveal_step = self.t
            self.speed_at_reveal = vx
            self.dist_at_reveal = self.dist
        x = torch.from_numpy(((np.asarray(obs, dtype=np.float64) - self.mean) / self.std).astype(np.float32))
        with torch.no_grad():
            if self.recurrent:
                if self.reset_hidden_at is not None and self.t == self.reset_hidden_at:
                    self.hidden = None  # ablation: forget everything pre-commit
                a, self.hidden = self.model.step(x.view(1, -1), self.hidden)
            else:
                a = self.model(x.view(1, -1))
        action = a.numpy().reshape(-1).astype(np.float64)
        if self.reveal_step is None:
            self.prep_action_sq_sum += float(np.sum(np.square(action)))
            self.prep_steps += 1
        self.t += 1
        return action


def run_one(task: dict[str, Any]) -> dict[str, Any]:
    """Train one (arm, seed) run and evaluate it closed-loop. Torch is imported
    lazily inside the worker (fork-safe)."""
    import torch

    torch.set_num_threads(int(task["torch_threads"]))
    arm, seed = task["arm"], int(task["seed"])
    arm_index = 0 if arm == "history" else 1
    torch.manual_seed(G1_SEED * 1000 + seed * 10 + arm_index)

    data = np.load(task["demo_npz"])
    frames, actions, lengths = data["frames"], data["actions"], data["lengths"]
    mean, std = data["mean"].astype(np.float64), data["std"].astype(np.float64)
    starts = np.concatenate([[0], np.cumsum(lengths)[:-1]])
    n_eps = len(lengths)
    max_len = int(lengths.max())

    padded_x = np.zeros((n_eps, max_len, OBS_DIM), dtype=np.float32)
    padded_y = np.zeros((n_eps, max_len, 3), dtype=np.float32)
    mask = np.zeros((n_eps, max_len), dtype=np.float32)
    for e in range(n_eps):
        s, ln = int(starts[e]), int(lengths[e])
        padded_x[e, :ln] = (frames[s:s + ln] - mean[None, :]) / std[None, :]
        padded_y[e, :ln] = np.clip(actions[s:s + ln], -0.999, 0.999)
        mask[e, :ln] = 1.0
    tx = torch.from_numpy(padded_x)
    ty = torch.from_numpy(padded_y)
    tm = torch.from_numpy(mask)

    model = _build_models(arm)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    order_rng = np.random.default_rng([G1_SEED, 5, seed])  # same batch order in both arms
    epochs, batch = int(task["epochs"]), BATCH_EPISODES
    t_train0 = time.time()
    final_loss = float("nan")
    for _epoch in range(epochs):
        idx = order_rng.permutation(n_eps)
        for b0 in range(0, n_eps, batch):
            sel = idx[b0:b0 + batch]
            xb, yb, mb = tx[sel], ty[sel], tm[sel]
            if arm == "history":
                pred = model(xb)
                loss = (((pred - yb) ** 2).mean(dim=-1) * mb).sum() / mb.sum()
            else:
                flat = mb.reshape(-1) > 0.5
                xf = xb.reshape(-1, OBS_DIM)[flat]
                yf = yb.reshape(-1, 3)[flat]
                pred = model(xf)
                loss = ((pred - yf) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            opt.step()
            final_loss = float(loss.item())
    train_s = time.time() - t_train0

    # ---- closed-loop evaluation on the shared held-out set
    mod_b, mod_c, mod_f, knobs, design, variant, _spec, _dig = load_family()
    pool = mod_f.EnvPool(mod_b, design, variant, knobs)
    model.eval()
    eval_specs = task["eval_specs"]  # list of (j, mu, env_seed)
    rows: list[dict[str, Any]] = []
    try:
        variants = [("main", None)]
        if arm == "history":
            variants.append(("hidden_reset", COMMIT_STEP))
        for tag, reset_at in variants:
            controller = TorchController(torch, model, mean, std,
                                         recurrent=(arm == "history"), reset_hidden_at=reset_at)
            for j, mu, env_seed in eval_specs:
                row = pool.rollout(controller, float(mu), int(env_seed),
                                   stage="g1prime_eval", arm=arm, run_seed=seed,
                                   eval_index=int(j), eval_variant=tag)
                rows.append(row)
    finally:
        pool.close()

    def signature(tag: str) -> dict[str, Any]:
        sub = [r for r in rows if r["eval_variant"] == tag]
        revealed = [r for r in sub if r["reveal_step"] >= 0 and math.isfinite(r["speed_at_reveal"])]
        coverage = len(revealed) / max(len(sub), 1)
        if len(revealed) >= 3:
            rho = mod_f.spearman_tie_corrected([r["speed_at_reveal"] for r in revealed],
                                               [r["mu"] for r in revealed])
        else:
            rho = float("nan")
        prep = [r["prep_action_sq_mean"] for r in sub if math.isfinite(r["prep_action_sq_mean"])]
        return {
            "episodes": len(sub), "revealed": len(revealed),
            "reveal_coverage": round(coverage, 4),
            "spearman_speed_mu": None if not math.isfinite(rho) else round(float(rho), 4),
            "success_rate": round(float(np.mean([1.0 if r["success"] else 0.0 for r in sub])), 4),
            "prep_action_sq_mean": round(float(np.mean(prep)), 4) if prep else None,
        }

    out = {
        "arm": arm, "seed": seed,
        "param_count": param_count(model),
        "final_loss": round(final_loss, 6),
        "train_seconds": round(train_s, 1),
        "main": signature("main"),
        "rows": rows,
    }
    if arm == "history":
        out["hidden_reset"] = signature("hidden_reset")
    return out


# ------------------------------------------------------- scripted baselines


def scripted_baselines(mod_b, mod_c, mod_f, knobs, design, variant, spec,
                       eval_specs) -> dict[str, Any]:
    """Free-prior hedge plan (final-spec medium-bin best fixed) + teacher +
    no-probe baseline, all on the same eval set (numpy only)."""
    detail = spec.get("final_iteration_detail", {})
    medium = detail.get("medium_bin", {})
    hedge_name = medium.get("best_fixed_all_plan", "grid_v8_A")
    cem_params = medium.get("cem_robust", {}).get("params_v_cap_off_gain")
    if hedge_name == "cem_robust" and cem_params:
        hedge_v, cap, off, gain = (float(x) for x in cem_params)
    else:
        try:
            hedge_v = float(hedge_name.split("_v")[1].split("_")[0])
            hedge_tag = hedge_name.split("_")[-1]
        except (IndexError, ValueError):
            hedge_v, hedge_tag = 8.0, "A"
        cap, off, gain = (0.85, 3.0, 3.0) if hedge_name.endswith("A") else (1.0, 3.0, 4.5)
    hedge_plan = mod_b.PlanSpec(name=hedge_name, v_entry=hedge_v, brake_to=None,
                                swerve_offset=off, swerve_gain=gain, steer_cap=cap)
    pool = mod_f.EnvPool(mod_b, design, variant, knobs)
    out: dict[str, Any] = {}
    rows_all: list[dict[str, Any]] = []
    try:
        for tag, build in (
            ("hedge_free_prior", lambda mu: mod_b.CommitmentController(hedge_plan, design)),
            ("teacher_privileged", lambda mu: OracleTeacher(mod_b, design, variant.v_oracle_est(mu))),
        ):
            rows = []
            for j, mu, env_seed in eval_specs:
                controller = build(float(mu))
                row = pool.rollout(controller, float(mu), int(env_seed),
                                   stage="g1prime_baseline", arm=tag, run_seed=-1,
                                   eval_index=int(j), eval_variant=tag)
                rows.append(row)
                rows_all.append(row)
            revealed = [r for r in rows if r["reveal_step"] >= 0 and math.isfinite(r["speed_at_reveal"])]
            rho = mod_f.spearman_tie_corrected([r["speed_at_reveal"] for r in revealed],
                                               [r["mu"] for r in revealed]) if len(revealed) >= 3 else float("nan")
            prep = [r["prep_action_sq_mean"] for r in rows if math.isfinite(r["prep_action_sq_mean"])]
            out[tag] = {
                "plan": hedge_name if tag == "hedge_free_prior" else "OracleTeacher(v_oracle_est(mu))",
                "episodes": len(rows), "revealed": len(revealed),
                "spearman_speed_mu": None if not math.isfinite(rho) else round(float(rho), 4),
                "success_rate": round(float(np.mean([1.0 if r["success"] else 0.0 for r in rows])), 4),
                "prep_action_sq_mean": round(float(np.mean(prep)), 4) if prep else None,
            }
    finally:
        pool.close()
    out["no_probe_prep_energy_baseline"] = out["hedge_free_prior"]["prep_action_sq_mean"]
    out["_rows"] = rows_all
    return out


# ----------------------------------------------------------------- statistics


def paired_bootstrap_ci(diffs: np.ndarray, resamples: int, lo_pct: float, hi_pct: float) -> tuple[float, float]:
    rng = np.random.default_rng(G1_SEED)
    n = len(diffs)
    boots = np.empty(resamples)
    for b in range(resamples):
        boots[b] = float(np.mean(diffs[rng.integers(0, n, n)]))
    return float(np.percentile(boots, lo_pct)), float(np.percentile(boots, hi_pct))


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


# ----------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="pipeline smoke (NOT the gate)")
    parser.add_argument("--demos", type=int, default=400)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--torch-threads", type=int, default=2)
    args = parser.parse_args()
    mode = "quick_pipeline_check" if args.quick else "preregistered_gate"
    if args.quick:
        args.demos, args.seeds, args.eval_episodes, args.epochs, args.workers = 60, 2, 12, 4, 4

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = RUN_DIR / ("smoke" if args.quick else "full")
    out_dir.mkdir(parents=True, exist_ok=True)

    from autodrift.artifacts import utc_timestamp, write_csv_rows

    mod_b, mod_c, mod_f, knobs, design, variant, spec, spec_digest = load_family()

    # [0] pre-registration BEFORE any training/eval (mechanical copy of the docstring block)
    prereg = {
        "protocol": "feasibility_audit_selfid_g1prime_preregistration",
        "written_at_utc": utc_timestamp(),
        "written_before_any_g1prime_training_or_eval": True,
        "mode": mode,
        "criteria": PREREGISTERED_CRITERIA,
        "final_spec_digest": spec_digest,
        "panel": {"demos": args.demos, "seeds": args.seeds,
                  "eval_episodes": args.eval_episodes, "epochs": args.epochs},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if not args.quick:
        PREREG_JSON.write_text(json.dumps(to_jsonable(prereg), indent=2), encoding="utf-8")
        (out_dir / "preregistration.json").write_text(json.dumps(to_jsonable(prereg), indent=2), encoding="utf-8")
        print(f"[0/5] pre-registration written -> {PREREG_JSON}")
    else:
        print("[0/5] quick pipeline check: pre-registration NOT (re)written")

    # [1] demonstrations
    print(f"[1/5] generating {args.demos} teacher demonstrations (continuous mu)")
    frames_all, actions_all, lengths, meta_rows, kept = generate_demos(
        mod_b, mod_f, knobs, design, variant, args.demos)
    kept_fraction = kept / args.demos
    teacher_demo_success = float(np.mean([1.0 if r["success"] else 0.0 for r in meta_rows]))
    print(f"      kept {kept}/{args.demos} ({kept_fraction:.1%}) successful demos")
    write_csv_rows(out_dir / "demo_meta.csv", meta_rows)
    if kept == 0:
        raise SystemExit("no successful demonstrations -- teacher broken")
    frames_cat = np.concatenate(frames_all, axis=0)
    actions_cat = np.concatenate(actions_all, axis=0)
    mean = frames_cat.mean(axis=0)
    std = frames_cat.std(axis=0)
    std[std < 1e-6] = 1.0
    demo_npz = out_dir / "demos.npz"
    np.savez_compressed(demo_npz, frames=frames_cat, actions=actions_cat,
                        lengths=np.asarray(lengths, dtype=np.int64), mean=mean, std=std)
    precondition_demos_ok = kept_fraction >= PREREGISTERED_CRITERIA["validity_preconditions"]["kept_demo_fraction_min"]

    # [2] shared held-out eval set
    eval_specs = [(j, eval_mu(j), G1_SEED * 10 + EVAL_SEED_OFFSET + j) for j in range(args.eval_episodes)]

    # [3] train + evaluate 2 arms x N seeds
    tasks = [{"arm": arm, "seed": s, "demo_npz": str(demo_npz), "epochs": args.epochs,
              "eval_specs": eval_specs, "torch_threads": args.torch_threads}
             for arm in ("history", "current_frame") for s in range(args.seeds)]
    print(f"[2/5] eval set: {args.eval_episodes} held-out episodes (paired across all runs)")
    print(f"[3/5] training {len(tasks)} runs ({args.workers} workers)")
    results: list[dict[str, Any]] = []
    if args.workers <= 1:
        for task in tasks:
            results.append(run_one(task))
            r = results[-1]
            print(f"      {r['arm']:<14} seed {r['seed']} rho={r['main']['spearman_speed_mu']} "
                  f"succ={r['main']['success_rate']} loss={r['final_loss']}")
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool_exec:
            for r in pool_exec.map(run_one, tasks):
                results.append(r)
                print(f"      {r['arm']:<14} seed {r['seed']} rho={r['main']['spearman_speed_mu']} "
                      f"succ={r['main']['success_rate']} loss={r['final_loss']}")

    # parameter alignment check
    params = {arm: next(r["param_count"] for r in results if r["arm"] == arm)
              for arm in ("history", "current_frame")}
    align = abs(params["history"] - params["current_frame"]) / max(params.values())
    align_ok = align <= PREREGISTERED_CRITERIA["design_constants"]["parameter_alignment_tolerance"]

    # [4] scripted baselines on the same eval set
    print("[4/5] scripted baselines (hedge plan + privileged teacher)")
    baselines = scripted_baselines(mod_b, mod_c, mod_f, knobs, design, variant, spec, eval_specs)
    baseline_rows = baselines.pop("_rows")

    # [5] adjudication
    cov_min = PREREGISTERED_CRITERIA["validity_preconditions"]["min_reveal_coverage_per_run"]
    per_seed: dict[str, list[dict[str, Any]]] = {"history": [], "current_frame": []}
    for r in sorted(results, key=lambda r: (r["arm"], r["seed"])):
        sig = r["main"]
        valid = sig["reveal_coverage"] >= cov_min and sig["spearman_speed_mu"] is not None
        entry = {"seed": r["seed"], "spearman": sig["spearman_speed_mu"],
                 "success_rate": sig["success_rate"], "reveal_coverage": sig["reveal_coverage"],
                 "prep_action_sq_mean": sig["prep_action_sq_mean"],
                 "final_loss": r["final_loss"], "valid": valid}
        if r["arm"] == "history":
            entry["hidden_reset_spearman"] = r["hidden_reset"]["spearman_speed_mu"]
            entry["hidden_reset_success"] = r["hidden_reset"]["success_rate"]
        per_seed[r["arm"]].append(entry)

    min_valid = PREREGISTERED_CRITERIA["validity_preconditions"]["min_valid_runs_per_arm"]
    valid_ok = {arm: sum(1 for e in per_seed[arm] if e["valid"]) >= min(min_valid, args.seeds)
                for arm in per_seed}
    hist_rhos = np.asarray([e["spearman"] if e["valid"] else np.nan for e in per_seed["history"]], dtype=np.float64)
    curr_rhos = np.asarray([e["spearman"] if e["valid"] else np.nan for e in per_seed["current_frame"]], dtype=np.float64)
    hist_median = float(np.nanmedian(hist_rhos)) if np.any(np.isfinite(hist_rhos)) else float("nan")
    curr_median = float(np.nanmedian(curr_rhos)) if np.any(np.isfinite(curr_rhos)) else float("nan")
    pair_ok = np.isfinite(hist_rhos) & np.isfinite(curr_rhos)
    diffs = (hist_rhos - curr_rhos)[pair_ok]
    if len(diffs) >= 2:
        boot = PREREGISTERED_CRITERIA["pass_rule"]["paired_bootstrap"]
        ci_lo, ci_hi = paired_bootstrap_ci(diffs, boot["resamples"], *boot["ci_percentiles"])
    else:
        ci_lo = ci_hi = float("nan")

    rule = PREREGISTERED_CRITERIA["pass_rule"]
    c_hist = bool(np.isfinite(hist_median) and hist_median >= rule["history_median_min"])
    c_curr = bool(np.isfinite(curr_median) and curr_median <= rule["current_median_max"])
    c_ci = bool(np.isfinite(ci_lo) and ci_lo > 0.0)
    preconditions_ok = bool(precondition_demos_ok and valid_ok["history"] and valid_ok["current_frame"] and align_ok)
    g1prime_pass = bool(c_hist and c_curr and c_ci and preconditions_ok)

    if not preconditions_ok:
        verdict, route = "VOID", "validity precondition violated -- fix the pipeline and rerun (no claim)"
    elif g1prime_pass:
        verdict, route = "PASS", "proceed to the m1087 stage-chain full-budget RL training pre-registration"
    elif (not c_hist) and (np.isfinite(curr_median) and curr_median > rule["current_median_max"]):
        verdict, route = "FAIL_LEAK_AND_WEAK_TEACHER", PREREGISTERED_CRITERIA["fail_semantics"]["history_lt_0.8_and_current_gt_0.4"]
    elif not c_hist:
        verdict, route = "FAIL_TEACHER_TASK_REWORK", PREREGISTERED_CRITERIA["fail_semantics"]["history_lt_0.8"]
    elif not c_curr:
        verdict, route = "FAIL_CURRENT_FRAME_LEAK", PREREGISTERED_CRITERIA["fail_semantics"]["history_geq_0.8_and_current_gt_0.4"]
    else:
        verdict, route = "FAIL_UNDERPOWERED", PREREGISTERED_CRITERIA["fail_semantics"]["medians_ok_ci_contains_0"]

    # gate-3 bar auxiliary
    gate3_bar = spec.get("final_iteration_detail", {}).get("gate3_bar_recomputed")

    eval_rows = [row for r in results for row in r.pop("rows")] + baseline_rows
    write_csv_rows(out_dir / "eval_rows.csv", eval_rows)

    summary = {
        "protocol": "feasibility_audit_selfid_g1prime_ignition_gate",
        "generated_by": "scripts/feasibility_audit/selfid_g1prime_ignition_gate.py",
        "generated_at_utc": utc_timestamp(),
        "mode": mode,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": {"json": str(PREREG_JSON), "criteria": PREREGISTERED_CRITERIA},
        "final_spec_digest": spec_digest,
        "demos": {
            "generated": args.demos, "kept_success_only": kept,
            "kept_fraction": round(kept_fraction, 4),
            "teacher_demo_success_rate": round(teacher_demo_success, 4),
            "precondition_kept_geq_0.6": bool(precondition_demos_ok),
            "frames_total": int(frames_cat.shape[0]),
        },
        "arms": {
            "parameter_counts": params,
            "parameter_alignment_rel_diff": round(align, 4),
            "parameter_alignment_ok": bool(align_ok),
            "training": {"epochs": args.epochs, "lr": LR, "batch_episodes": BATCH_EPISODES,
                         "optimizer": "Adam", "loss": "masked MSE", "grad_clip": GRAD_CLIP},
        },
        "per_seed": per_seed,
        "adjudication": {
            "history_median_spearman": round(hist_median, 4) if np.isfinite(hist_median) else None,
            "current_frame_median_spearman": round(curr_median, 4) if np.isfinite(curr_median) else None,
            "paired_diff_mean": round(float(np.mean(diffs)), 4) if len(diffs) else None,
            "paired_bootstrap_ci95": [round(ci_lo, 4), round(ci_hi, 4)] if np.isfinite(ci_lo) else None,
            "criterion_history_geq_0.8": c_hist,
            "criterion_current_leq_0.4": c_curr,
            "criterion_ci_excludes_0": c_ci,
            "preconditions_ok": preconditions_ok,
            "valid_runs": {arm: sum(1 for e in per_seed[arm] if e["valid"]) for arm in per_seed},
            "G1PRIME_PASS": g1prime_pass,
            "verdict": verdict,
            "route": route,
        },
        "auxiliary_non_adjudicating": {
            "hidden_reset_ablation": {
                "per_seed_spearman": [e["hidden_reset_spearman"] for e in per_seed["history"]],
                "median": round(float(np.nanmedian(np.asarray(
                    [e["hidden_reset_spearman"] if e["hidden_reset_spearman"] is not None else np.nan
                     for e in per_seed["history"]], dtype=np.float64))), 4),
                "expectation": "signature should degrade vs the un-ablated history arm",
            },
            "baselines": baselines,
            "gate3_bar_from_final_spec": gate3_bar,
            "per_arm_success_vs_gate3_bar": {
                arm: {"median_success": round(float(np.median([e["success_rate"] for e in per_seed[arm]])), 4),
                      "bar": gate3_bar}
                for arm in per_seed
            },
            "prep_energy_vs_no_probe_baseline": {
                "no_probe_baseline": baselines.get("no_probe_prep_energy_baseline"),
                "history_median": round(float(np.median([e["prep_action_sq_mean"] for e in per_seed["history"]])), 4),
                "current_frame_median": round(float(np.median([e["prep_action_sq_mean"] for e in per_seed["current_frame"]])), 4),
                "teacher": baselines.get("teacher_privileged", {}).get("prep_action_sq_mean"),
            },
        },
        "panel": {"seeds_per_arm": args.seeds, "eval_episodes_per_run": args.eval_episodes,
                  "workers": args.workers, "torch_threads": args.torch_threads},
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {
            "run_dir": str(out_dir),
            "demo_meta_csv": str(out_dir / "demo_meta.csv"),
            "demos_npz": str(demo_npz),
            "eval_rows_csv": str(out_dir / "eval_rows.csv"),
            "summary_json": str(SUMMARY_JSON if not args.quick else out_dir / "summary.json"),
        },
    }
    target = SUMMARY_JSON if not args.quick else out_dir / "summary.json"
    target.write_text(json.dumps(to_jsonable(summary), indent=2), encoding="utf-8")
    print(f"[5/5] summary -> {target}")
    print(
        f"HEADLINE: {verdict} | hist median rho={hist_median:.3f} | curr median rho={curr_median:.3f} | "
        f"CI95 diff=({ci_lo:.3f},{ci_hi:.3f}) | demos kept {kept}/{args.demos} | "
        f"elapsed {time.time() - started:.0f}s"
    )


if __name__ == "__main__":
    main()
