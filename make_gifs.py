#!/usr/bin/env python3
"""
Generate animated GIFs of every DAS-DAD scenario.

  * left  – the DAS-DAD diagram (DAD & DAS curves + the equilibrium that walks
            period-by-period back toward the centred (Ȳ, π*) cross),
  * right – the time paths of output Y and inflation π.

The model and shock values are actually identical to the in-app scenarios.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation

# ----- palette (matches the web tool) -----------------------------------
PAPER   = "#fbfaf7"
INK     = "#1b2230"
ACCENT  = "#4338ca"      # equilibrium / output
DAD_C   = "#1d4ed8"      # demand curve / output line
DAS_C   = "#c0531c"      # supply curve / inflation line
GOLD    = "#d4a017"      # Ȳ / π* reference
MUTED   = "#8a93a6"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#d8d6e0",
    "axes.linewidth": 1.0,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
})

# ----- model parameters (the sensible defaults) --------------------------
YBAR, PISTAR, GAMMA, PHI, KAPPA = 5.0, 5.0, 0.5, 0.5, 0.7
D  = 1 + GAMMA * PHI
A  = 1 - (PHI * GAMMA) / D          # = 1/(1+gamma*phi) = 0.8
B  = ((PHI * GAMMA) / D) * PISTAR
CE = (PHI * KAPPA) / D
CV = 1 - (PHI * GAMMA) / D
K  = 10                              # periods to animate (t .. t+9)

# ----- scenarios (period-indexed shocks; period 1 == t) ------------------
SCENARIOS = [
    ("demand_shock_positive", "Nachfrageschock (Boom & Inflation)",
        {1: 4}, {}),
    ("demand_shock_negative", "Nachfrageschock (Rezession)",
        {1: -4}, {}),
    ("supply_shock_adverse", "Angebotsschock (Stagflation)",
        {}, {1: 4}),
    ("supply_shock_favourable", "Angebotsschock (Günstiger Ölpreis)",
        {}, {1: -4}),
    ("oil_crisis_1970s", "Ölkrise 1970er (Anhaltende Stagflation)",
        {}, {1: 4, 2: 2, 3: 2}),
    ("fiscal_expansion", "Fiskalexpansion (Anhaltender Boom)",
        {1: 4, 2: 2, 3: 2}, {}),
    ("financial_crisis_2008", "Finanzkrise 2008 (Tiefe Rezession)",
        {1: -4, 2: -4, 3: -2}, {}),
    ("covid_19", "COVID-19 (Einbruch, Erholung & Inflationswelle)",
        {1: -4, 2: -2}, {3: 2}),
]


def simulate(e, v):
    pi = [PISTAR]
    y = [YBAR]
    for t in range(1, K + 1):
        en, vn = e.get(t, 0), v.get(t, 0)
        p = A * pi[t - 1] + B + CE * en + CV * vn
        pi.append(p)
        y.append(YBAR - GAMMA * (p - PISTAR) + KAPPA * en)
    return np.array(pi), np.array(y)


def make_gif(slug, title, e, v, outdir):
    pi, y = simulate(e, v)
    xx = np.linspace(0, 10, 200)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 4.0), dpi=85,
                                   gridspec_kw={"width_ratios": [1.05, 1.0]})
    fig.subplots_adjust(left=0.07, right=0.975, top=0.82, bottom=0.13, wspace=0.28)

    # figure-level texts created ONCE and updated each frame
    fig.suptitle(title, color=INK, fontsize=13, fontweight="bold", y=0.975)
    period_text = fig.text(0.5, 0.89, "", color=ACCENT, fontsize=10,
                           ha="center", fontweight="bold")

    def dad(period):
        eps = e.get(period, 0)
        return PISTAR - (1 / GAMMA) * (xx - KAPPA * eps - YBAR)

    def das(period):
        nu = v.get(period, 0)
        prev = pi[period - 1] if period >= 1 else PISTAR
        return prev + PHI * (xx - YBAR) + nu

    def draw(frame):
        axL.clear(); axR.clear()

        # ---------------- left: DAS-DAD diagram ----------------
        axL.set_facecolor(PAPER)
        axL.axvline(YBAR, color=GOLD, lw=1.4, alpha=0.85)
        axL.axhline(PISTAR, color=GOLD, lw=1.4, alpha=0.85)

        # baseline (period-0) curves, faint
        axL.plot(xx, PISTAR - (1 / GAMMA) * (xx - YBAR), color=DAD_C, lw=1, alpha=0.18)
        axL.plot(xx, PISTAR + PHI * (xx - YBAR), color=DAS_C, lw=1, alpha=0.18)

        if frame >= 1:
            axL.plot(xx, dad(frame), color=DAD_C, lw=2.4, alpha=0.95, label="DAD")
            axL.plot(xx, das(frame), color=DAS_C, lw=2.4, alpha=0.95, label="DAS")
            # trace of equilibria so far (the staircase)
            axL.plot(y[:frame + 1], pi[:frame + 1], color=ACCENT, lw=1.6,
                     alpha=0.55, marker="o", ms=3, zorder=4)
        else:
            axL.plot([], [], color=DAD_C, lw=2.4, label="DAD")
            axL.plot([], [], color=DAS_C, lw=2.4, label="DAS")
        # current equilibrium
        axL.scatter([y[frame]], [pi[frame]], s=70, color=ACCENT,
                    edgecolor="white", lw=1.5, zorder=5)

        axL.set_xlim(0, 10); axL.set_ylim(0, 10)
        axL.set_xlabel("Output  $Y$", color=INK)
        axL.set_ylabel("Inflation  $\\pi$", color=INK)
        axL.set_title("DAS–DAD-Diagramm", color=INK, fontsize=11, pad=6)
        axL.tick_params(colors=MUTED, labelsize=8)
        axL.legend(loc="upper right", fontsize=8, frameon=False)

        # ---------------- right: time paths ----------------
        axR.set_facecolor(PAPER)
        t = np.arange(0, K + 1)
        axR.axhline(5, color=GOLD, lw=1.2, ls="--", alpha=0.8)
        axR.text(K, 5.15, "$\\bar{Y}=\\pi^{*}=5$", color=GOLD, fontsize=8,
                 ha="right", va="bottom")
        axR.plot(t[:frame + 1], y[:frame + 1], color=ACCENT, lw=2.2,
                 marker="o", ms=3, label="Output $Y$")
        axR.plot(t[:frame + 1], pi[:frame + 1], color=DAS_C, lw=2.2,
                 marker="o", ms=3, label="Inflation $\\pi$")
        axR.set_xlim(0, K); axR.set_ylim(0, 10)
        axR.set_xlabel("Periode", color=INK)
        axR.set_title("Zeitpfad", color=INK, fontsize=11, pad=6)
        axR.tick_params(colors=MUTED, labelsize=8)
        axR.legend(loc="upper right", fontsize=8, frameon=False)

        # period label (single, updated text artist)
        lbl = "t−1 (Gleichgewicht)" if frame == 0 else (
              "t" if frame == 1 else f"t+{frame - 1}")
        period_text.set_text(f"Periode: {lbl}")

    frames = list(range(0, K + 1)) + [K] * 3   # hold final frame
    anim = animation.FuncAnimation(fig, draw, frames=frames, interval=850)
    path = os.path.join(outdir, f"{slug}.gif")
    anim.save(path, writer=animation.PillowWriter(fps=1.3))
    plt.close(fig)
    print("wrote", path, f"(troughY={y.min():.2f}, peakPi={pi.max():.2f})")

# main exectuable
def main():
    outdir = os.path.join(os.path.dirname(__file__),
                          "media")
    os.makedirs(outdir, exist_ok=True)
    for slug, title, e, v in SCENARIOS:
        make_gif(slug, title, e, v, outdir)


if __name__ == "__main__":
    main()
