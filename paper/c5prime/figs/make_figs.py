"""Generate the two data figures for the C5' paper from committed results.
Fig 2: lever-elimination grouped bars. Fig 3: per-seed drift-avoid frontier scatter.
Outputs vector PDF (for LaTeX \\includegraphics) + PNG preview."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42})
# colorblind-safe (Wong)
C_DRIFT, C_AVOID = "#0072B2", "#D55E00"

# ---- Fig 2: lever elimination ----
labels = ["single-head\nbaseline", "Jacobian\npenalty", "PCGrad", "gated\n(8 seed)", "gated\n(16 seed)"]
drift = [0.769, 0.731, 0.556, 0.925, 0.856]
avoid = [0.775, 0.713, 0.863, 0.758, 0.700]
x = np.arange(len(labels)); w = 0.38
fig, ax = plt.subplots(figsize=(6.4, 3.4))
ax.bar(x - w/2, drift, w, label="drift", color=C_DRIFT)
ax.bar(x + w/2, avoid, w, label="avoidance", color=C_AVOID)
ax.axhline(0.35, ls="--", lw=1, color=C_DRIFT, alpha=0.7)
ax.text(len(labels)-0.5, 0.36, "drift oracle 0.35", color=C_DRIFT, fontsize=7, ha="right", va="bottom")
ax.axhline(1.0, ls=":", lw=1, color=C_AVOID, alpha=0.7)
ax.text(len(labels)-0.5, 0.985, "avoidance floor 1.0", color=C_AVOID, fontsize=7, ha="right", va="top")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("validation success rate"); ax.set_ylim(0, 1.05)
ax.legend(loc="lower left", frameon=False, ncol=2)
ax.set_title("Lever elimination: only gated dual heads expand the frontier", fontsize=10)
fig.savefig(OUT/"fig2_levers.pdf"); fig.savefig(OUT/"fig2_levers.png"); plt.close(fig)

# ---- Fig 3: per-seed drift-avoid frontier ----
gated16 = [[1.0,0.875],[1.0,1.0],[0.625,0.0],[0.875,1.0],[1.0,1.0],[1.0,1.0],[1.0,0.0],[1.0,1.0],
           [1.0,0.0],[1.0,0.0],[0.0,1.0],[1.0,0.875],[0.375,0.625],[1.0,0.25],[0.75,0.625],[1.0,0.75]]
single = [[0.375,0.875],[1.0,1.0],[1.0,0.5],[0.0,1.0],[1.0,0.25],[0.75,0.75],[1.0,1.0],[0.5,0.5]]
g = np.array(gated16); s = np.array(single)
# jitter to separate coincident discrete points
rng = np.random.default_rng(0)
def jit(a): return a + rng.uniform(-0.022, 0.022, size=a.shape)
fig, ax = plt.subplots(figsize=(4.6, 4.4))
ax.axhspan(0.75, 1.06, xmin=(0.75+0.06)/1.12, alpha=0.08, color="green")  # both-high quadrant guide
ax.axvline(0.75, ls=":", lw=0.8, color="gray"); ax.axhline(0.75, ls=":", lw=0.8, color="gray")
ax.scatter(jit(s[:,0]), jit(s[:,1]), s=46, marker="o", facecolors="none", edgecolors="gray",
           label=f"single-head (n={len(s)})")
ax.scatter(jit(g[:,0]), jit(g[:,1]), s=46, marker="^", color="#0072B2", alpha=0.85,
           label=f"gated (n={len(g)})")
ax.text(0.875, 0.965, "both-good\nregion", color="green", fontsize=8, ha="center", va="top")
ax.set_xlabel("drift success (per seed)"); ax.set_ylabel("avoidance success (per seed)")
ax.set_xlim(-0.06, 1.06); ax.set_ylim(-0.06, 1.08)
ax.legend(loc="lower left", frameon=False, fontsize=8)
ax.set_title("Per-seed regime frontier", fontsize=10)
fig.savefig(OUT/"fig3_frontier.pdf"); fig.savefig(OUT/"fig3_frontier.png"); plt.close(fig)

print("wrote fig2_levers.pdf/png, fig3_frontier.pdf/png")
print("both-high seeds: gated %d/%d, single-head %d/%d" % (
    int(((g[:,0]>=0.75)&(g[:,1]>=0.75)).sum()), len(g),
    int(((s[:,0]>=0.75)&(s[:,1]>=0.75)).sum()), len(s)))
