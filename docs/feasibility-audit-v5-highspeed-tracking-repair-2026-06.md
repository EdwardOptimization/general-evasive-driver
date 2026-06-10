# Feasibility Audit Track B: v5 候选 — 高速循迹出界修复 (2026-06)

## Scope / claim boundary

人工接管路线 Track B：针对 M3105 incumbent 在可行行上的 5 个已知 0-碰撞出界失败，
诊断机理（B1）、构建 v5 候选覆盖层（B2）、并在四个 64 行面板上与 v4 同跑逐行对比（B3）。

- v5 是**候选**（`ActiveSafetyDriverV5Candidate`），公共部署驱动
  `ActiveSafetyReflexDriver`（M3105 v4 incumbent）**未做任何修改**；promotion 是之后人的决定。
- 本文档只做测量与计数，不做 driver-performance verdict、repair-success、robustness-result、
  validation/ranking/promotion、high-fidelity、paper、self-ID 声明。
- 全部运行确定性（CPU、固定种子、`AutoDriftEnv.reset(seed=...)` 全量重播种）：
  B3 全量复跑得到**字节级一致**的逐行 CSV
  （`runs/feasibility_audit/v5_panel_validation_rows_rerun.csv`），B1 复跑 trace 完全一致。
- 环境重建与 rollout 完全复用 `scripts/feasibility_audit/fresh_panel_retest.py` 的
  env 构建/标签/rollout/outcome 函数（M3088/M3090 测量代码路径）。

## B1 诊断（5 个失败行重放）

脚本：`scripts/feasibility_audit/v5_offtrack_diagnosis.py`；
逐步 trace：`runs/feasibility_audit/v5_offtrack_diagnosis_traces.json`；
摘要：`experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json`。
5 行重放全部复现 `off_track`（与记录一致）。

| 行 | spec | seed | 初速 | mu(初→末) | μg 限速(末) | 终止速 | 机理结论（一句话） |
|---|---|---|---|---|---|---|---|
| feasible-0010 | 0010 | 605541 | 15.8 | 0.69→0.39 | 8.34 | 13.5 | 起步即超摩擦限速 + 早期 μ 阶跃；v4 仅边缘反应式刹车（edge_urgency 在外滑时反而回落到 0，刹车随之松开），全程只降速 2.3 m/s，59 步内横漂 5 m 出界 |
| feasible-0013 | 0014 | 607560 | 19.3 | 0.87→0.42 | 8.63 | 18.1 | 初速 19.3 对限速 8.6（需求 20.7 m/s² 对可用 4.1），37 步出界；任何控制都不可能（见 ceiling probe） |
| feasible-0024 | 0008 | 602631 | 16.5 | 0.78→0.715 | 11.24 | 13.8 | 最接近可救：μ 不深跌，但 v4 的反应式 edge/stability 刹车持续吃掉侧向摩擦预算，在 odist −1.9 m（差 ~0.1 m 到通过点）处出界 |
| feasible-0029 | 0014 | 614660 | 14.9 | 0.78→0.49 | 9.27 | 13.4 | 同 0010 模式（超限速 + μ 阶跃 + 边缘反应式刹车太晚且间歇释放），62 步出界 |
| fresh-0053 | 0005 | 501820 | 7.1 | 0.34（恒定） | 7.79 | 3.5 | **不是**超速也**不是** speed-floor 压刹车：v2 基底在 r=18 圆轨上 road_center_error 恒饱和(=1.0)→转向命令打满(0.99)，叠加重刹 + μ0.34 诱发慢速甩尾（yaw 达路径需求 3–7 倍，β→−π/2），212 步滑向内侧出界；v2 speed-floor 升油门在侧滑中继续注入能量 |

对原假设的判定：高速 4 行中 “speed-floor 保护压制刹车” **不成立**（speed_deficit 全程为 0）；
“edge_excess 触发太晚/太弱” 成立，且更关键的是 edge 信号在外滑过程中回落导致刹车间歇释放。
v4 本地层 local_risk 几乎不触发（max 0.07–0.66，瞬态）。

诊断中同时验证了 obs72-only 曲率估计器（边界 lookahead 32 维 → 中心线 Menger 曲率）：
与特权 `info["curvature"]` 的中位相对误差 = **0.0000**（圆轨上精确）。

### 关键物理反转（决定 B2 设计方向）

任务先验是“减速永远可用，降到摩擦限速即可循迹”。实测推翻了“刹车减速”作为手段：
这些行**出生即超限速**（初速 14.9–19.3 对限速 8.3–11.2），障碍通过点只在前方 ~22 m
（`finish_pass_distance=2.0`，成功 = 在出界前走完这 ~24 m），刹车占用摩擦圆、直接削减侧向抓地，
出界更早。恒值动作扫描显示**零刹车 + 断驱动（coast）在全部 4 行上严格优于一切刹车方案**，
且仅此就能救回 0024。因此 v5 的调速器是“**曲率可行性 grip-priority 调速器**”：
超限速时**切断驱动并释放 v4 的反应式刹车**（把摩擦预算全部让给循迹），而非加刹。

## B2 v5 候选实现

模块：`src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py`
（`DRIVER_ID = active_safety_driver_v5_curvature_speed_governor_candidate`，
`V5_POLICY_CONFIG` sha256 = `2961746369567e5dafdcdbd5b41cb150c60a6fbb872dcf8f773ccca7523b2304`）。

v5 = **原样调用** v4 动作函数（`v4_v2_fallback_no_regression_hard_safety_direct_action`，
零代码复制）+ 两个纯函数覆盖层，全部输入为 obs72 可见量（mu/质量/TTC/标签等特权量一律不用）：

**A. 曲率可行性 grip-priority 调速器**（高速专用）
- 曲率：边界 lookahead 前 6 点中心线 Menger 曲率（带符号）；走廊半宽同步估计。
- 可行速度 `v_feas = sqrt(a_lat_budget / |kappa|)`（mu 不可见，用保守常数预算 4.2 m/s²）。
- 闭环 distress = 0.6·edge_urgency + 0.6·转向饱和度 + 0.4·yaw 响应不足度，降低触发门槛
  （`activation = clip01((overspeed + 0.25·distress − 0.5)/0.5)`）。
- 动作：throttle ≤ −activation（断驱动）；v4 刹车按 activation 释放（满激活时残留 ≤ 0.10）。
- 速度下限 9.0 m/s + 曲率下限 1/60：低速行（spec-0005 类，~5 m/s）**不触发**（已验证）。
- 障碍仲裁：obstacle_urgency 在 [0.50, 0.85] 区间线性让位，≥0.85 完全交还 v4（避障优先）。

**B. 防甩尾（anti-spin/ESC）修整**（1.5–12 m/s 频带，针对 fresh-0053 机理）
- 触发 = yaw 盈余（|yaw| 超出 v·|kappa| + 0.25 rad/s）× 侧滑比（|vy|/v 超 0.18），两者相乘；
- 动作：按风险缩小入弯转向（gain 0.8）、释放刹车（gain 0.8）、风险 >0.5 时油门钳到 0.05；
- 同样受障碍让位因子约束。

参数表（`V5_POLICY_CONFIG["governor"]`）：

| 参数 | 值 | 参数 | 值 |
|---|---|---|---|
| min_speed_mps | 9.0 | esc_min/max_speed_mps | 1.5 / 12.0 |
| kappa_min_1pm | 1/60 | esc_yaw_surplus_margin/scale | 0.25 / 0.60 rad/s |
| curvature_points | 6 | esc_sideslip_ratio_start/scale | 0.18 / 0.25 |
| a_lat_budget_mps2 | 4.2 | esc_steer_cut_gain | 0.80 |
| overspeed_full_scale_mps | 4.0 | esc_brake_release_gain | 0.80 |
| overspeed_trigger | 0.5 | esc_throttle_cap | 0.05 |
| distress 权重 (edge/steer/yaw) | 0.6/0.6/0.4 | esc_spin_risk_floor | 0.05 |
| distress_activation_boost | 0.25 | obstacle_yield_start/full | 0.50 / 0.85 |
| grip_priority_brake_release_gain | 1.0 | governor_throttle_suppression | 1.0 |
| grip_priority_brake_cap | 0.10 | enabled / esc_enabled | true / true |

**退化等价性（已验证）**：`governor.enabled=false` 且 `esc_enabled=false` 时，v5 与 v4 在
8 个面板行 697 个闭环步上动作**逐位相等**（max |Δ| = 0.0）。

## B3 四面板逐行验证

脚本：`scripts/feasibility_audit/v5_panel_validation.py`；
逐行：`experiments/feasibility_audit/v5_panel_validation_rows.csv`（4 面板 × 64 行 × 2 驱动 = 512 行）；
汇总：`experiments/feasibility_audit/v5_panel_validation_summary.json`。
v4 与 v5 同进程、同 env 重建路径、同种子逐行对比。

### v4 / v5 四面板对照

| 面板 | 种子 | 驱动 | success | collision | offtrack | speed_too_low | aeb_feasible | 全部可行行 |
|---|---|---|---|---|---|---|---|---|
| feasible_only（64 全可行）| 601500 扫描（现有 CSV 原种子）| v4 | 60/64 | 0 | 4 | 0 | 55/57 | 60/64 |
| | | **v5** | **61/64** | **0** | 3 | 0 | **56/57** | **61/64** |
| fresh（53 可行 + 11 不可行）| 501500 公式 | v4 | 54/64 | 4 | 6 | 0 | 52/53 | 52/53 |
| | | **v5** | **55/64** | 4 | 5 | 0 | **53/53** | **53/53** |
| old（55 可行 + 9 不可行；硬 no-regression）| 401500 公式 | v4 | 57/64 | 5 | 2 | 0 | 55/55 | 55/55 |
| | | **v5** | **57/64** | 5 | 2 | 0 | **55/55** | **55/55** |
| holdout（64 全可行，新种子）| **701500** 扫描（62 aeb + 2 aes，与全部已用种子不相交）| v4 | 60/64 | 1 | 3 | 0 | 59/62 | 60/64 |
| | | **v5** | **60/64** | **0** | 4 | 0 | 59/62 | 60/64 |

逐行变化（全部四面板、512 个 episode 对比）：
- **v5 修复**：feasible_only-0024（offtrack→success）、fresh-0053（offtrack→success）。
- **v5 回退**：**0 行**（任何面板上没有任何 v4-success 行被 v5 变为失败）。
- holdout-0029（seed 707660，aeb_feasible）：v4 **collision** → v5 offtrack
  （margin −0.046 → +0.333；仍是失败行故不计入修复，但碰撞消失）。
- v5 在全部 192 个可行标签行上 **0 碰撞**（v4 为 1）；fresh 面板的 4 个碰撞全部在
  unavoidable 标签行且 v4/v5 行集完全相同。
- old 面板 v4 同进程重测与 M3105 记录的 64 行逐行 outcome **零失配**（复现校验）。

### old 面板硬 no-regression 细查

- success：v5 = 57 ≥ 57 ✓；无 v4-success 行回退 ✓；7 个失败行 outcome 全部不变 ✓。
- 7 条不可避行 min_clearance_margin（v5 − v4，容差 −1e-3）：

| old 行 | v4 outcome | v4 margin | v5 margin | Δ | 1e-3 guard |
|---|---|---|---|---|---|
| 0007 | collision | −0.1119 | −0.1709 | −0.0590 | **FAIL** |
| 0010 | collision | −0.2089 | −0.1898 | +0.0191 | pass |
| 0013 | offtrack | 4.0018 | 3.9555 | −0.0464 | **FAIL** |
| 0024 | offtrack | 0.1911 | 0.1664 | −0.0247 | **FAIL** |
| 0025 | collision | −0.1642 | −0.0041 | +0.1601 | pass |
| 0026 | collision | −0.2054 | −0.1067 | +0.0987 | pass |
| 0029 | collision | −0.2312 | −0.1928 | +0.0384 | pass |

**诚实结论：margin guard 4/7 通过，3/7 不通过（−0.021…−0.059 m），且经调参证明在保留任何修复的
前提下不可调和**：
1. 这 7 行全部处于调速器目标频带（高速、障碍 11–21 m 内可见），任何行为改变都会让逐 cm 的
   margin 双向漂移（4 行改善 +0.019…+0.160，3 行恶化 ≤0.059）；1e-3 的容差**低于这些速度下
   单步行驶量（0.27–0.36 m/step）**，即低于该测量的离散化量子。
2. 对 obstacle_yield (start, full) 做了 (0.30,0.55)/(0.20,0.45)/(0.35,0.60) 扫描：三个恶化行
   的 Δ 几乎不变（0007 恒为 −0.0587），因为差异在整个接近段累积、并非末段让位可消除；
   而更早让位会撤销 feasible-0024 修复（同一频带）。
3. 安全方向上 v5 并未更差：0007 的撞击速度 17.23 → 16.48 m/s（更低），margin 差为终止步
   离散对齐伪差；5 个碰撞行中 4 行 margin 改善。
4. 如需严格逐位 no-regression，`governor.enabled=false, esc_enabled=false` 可使 v5 全局
   逐位等价 v4（上节已验证）。

### 物理上限证据（为什么 feasible_only 只 +1）

脚本：`scripts/feasibility_audit/v5_offtrack_ceiling_probe.py`；
结果：`experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv`。
对 4 个高速失败行各重放 84 个特权搜索动作日程（恒值 steer×brake 网格、v4 转向 + 恒值/突发刹车、
缩放转向 + vy 阻尼、drift 类日程）：

| 行 | 通过日程数 | 最优日程 | 终止时距通过点 | 判定 |
|---|---|---|---|---|
| feasible-0010 | 0/84 | coast (steer 0.40, 零刹) | 差 ~1.9 m | 探测上限之外 |
| feasible-0013 | 0/84 | coast | **差 ~8.4 m** | 物理不可达（高置信） |
| feasible-0024 | **40/84** | coast | 通过 | 可达 → v5 已修复 |
| feasible-0029 | 0/84 | coast (steer 0.65, 零刹) | 差 ~1.4 m | 探测上限之外 |

这些行出生时即超摩擦限速 5–11 m/s、通过点仅 ~22 m：减速烧不掉超速（刹车权限 4.1 m/s² 且
吃侧向抓地），横漂在通过前必然超出 ±5 m 走廊。0010/0013/0029 与 feasible-only 面板报告中
"aeb_feasible 标签只认证障碍制动可行性、不认证 14–20 m/s 的循迹可行性" 的残留模式一致；
修这 3 行需要改场景生成（可行性过滤加入循迹判据）或允许漂移类控制，超出反射覆盖层范围。

## 目标达成情况（诚实清单）

| 目标 | 结果 | 状态 |
|---|---|---|
| feasible_only 60→64、至少 +3、保持 0 碰撞 | 60→**61**（+1），0 碰撞保持 | **未达标**（+1 < +3；其余 3 行经 84 日程特权探测 0 通过，证明在反射类动作上限之外，权衡不可调和如实报告） |
| fresh 可行行 52/53 → 53/53 | **53/53** | **达标** |
| old 硬 no-regression：success ≥57 | 57/64，0 行回退，outcome 逐行不变 | **达标** |
| old 7 不可避行 margin 恶化 ≤1e-3 | 4/7 通过；3 行 −0.021…−0.059（< 单步离散量子；碰撞撞击速度反而更低；调参证明与修复不可同时满足） | **未达标（不可调和，如实报告）** |
| holdout 防过拟合面板（加分） | 701500 基，v5=v4=60/64 且碰撞 1→0，无回退 | **达标**（无过拟合迹象） |

## 已验证 / 未验证

已验证：
- 5 失败行重放复现（outcome 与记录逐行一致）；old 面板 v4 重测与 M3105 记录 64/64 一致。
- B1/B3 复跑确定性（trace 逐项一致；512 行 CSV 字节级一致）。
- v5 不修改 incumbent：新文件之外零文件改动；v5 关闭覆盖层后与 v4 动作逐位相等（697 步抽查）。
- 曲率估计器仅用 obs72，对特权曲率中位相对误差 0.0000（仅限本面板的圆轨场景）。
- holdout 种子与 old/fresh/feasible_only 全部种子（192 个）不相交（运行时断言）。

未验证 / 边界：
- 0010/0029 的"物理不可达"是 84 日程探测下的上限，不是最优控制证明（0013 差 8.4 m，高置信不可达）。
- 曲率估计器未在非圆轨/变曲率赛道上验证；a_lat_budget=4.2 是经验常数，未对 μ 分布做覆盖性分析。
- 四面板共用同 16 spec×binding 结构；面板外泛化未测。
- ESC 层仅由 1 个低速甩尾行驱动设计（holdout/各面板未出现反例，但样本少）。
- 不做任何 promotion/driver-performance/robustness 结论。

## Artifacts

- `src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py`（新，候选模块）
- `scripts/feasibility_audit/v5_offtrack_diagnosis.py`（B1）
- `scripts/feasibility_audit/v5_offtrack_ceiling_probe.py`（物理上限探测）
- `scripts/feasibility_audit/v5_panel_validation.py`（B3）
- `experiments/feasibility_audit/v5_offtrack_diagnosis_summary.json`
- `experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv`
- `experiments/feasibility_audit/v5_panel_validation_rows.csv` / `v5_panel_validation_summary.json`
- `runs/feasibility_audit/v5_offtrack_diagnosis_traces.json`（+ `_rerun` 确定性副本）
- `runs/feasibility_audit/v5_panel_validation_rows_rerun.csv` / `v5_panel_validation_summary_rerun.json`
