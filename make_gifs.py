#!/usr/bin/env python3
"""
Generate animated GIFs of the DAS-DAD model.

Two things live in here:

1. The eight ready-made scenario GIFs used in the README (run `python make_gifs.py`).

2. A tiny helper, `custom_gif(...)`, for making your OWN gif in a couple of
   lines — handy for dropping a tailored shock into your slides. Example:

       from make_gifs import custom_gif

       custom_gif(
           gamma=0.5,            # how hard policy/demand leans against inflation
           phi=0.5,              # slope of the Phillips curve
           demand={1: 4, 2: 2},  # period -> demand-shock size  (period 1 == t)
           supply={3: 2},        # period -> supply-shock size
           title="My custom shock",
           out="media/my_shock.gif",
       )

   Every argument is optional; anything you leave out falls back to the model's
   default. `demand` / `supply` are dictionaries mapping a shock *period* to a
   shock *size* (positive or negative). Use a single entry for a one-off shock,
   several for a drawn-out one.

Each GIF has two panels that mirror the live tool:
  * left  - the DAS-DAD diagram (DAD & DAS curves + the equilibrium that walks
            period-by-period back toward the centred (Y*, pi*) cross),
  * right - the time paths of output Y and inflation pi.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation

# ----- palette (matches the web tool) -----------------------------------
PAPER  = "#f9f9f9"
INK    = "#1b2230"
ACCENT = "#4338ca"
DAD_C  = "#1d4ed8"
DAS_C  = "#c0531c"
GOLD   = "#d4a017"
MUTED  = "#8a93a6"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#d8d6e0",
    "axes.linewidth": 1.0,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
})

# ----- model defaults (the "sensible" calibration) -----------------------
YBAR, PISTAR = 5.0, 5.0
GAMMA_DEF, PHI_DEF, KAPPA_DEF = 0.5, 0.5, 0.7
K = 10                                   # periods to animate (t .. t+9)


def _coeffs(gamma, phi, kappa):
    """Reduced-form coefficients of the inflation difference equation."""
    d  = 1.0 + gamma * phi
    a  = 1.0 / d                         # inflation persistence  = 1/(1+gamma*phi)
    b  = (gamma * phi / d) * PISTAR
    ce = (phi * kappa) / d
    cv = 1.0 / d
    return a, b, ce, cv


def simulate(demand, supply, gamma=GAMMA_DEF, phi=PHI_DEF, kappa=KAPPA_DEF):
    a, b, ce, cv = _coeffs(gamma, phi, kappa)
    pi, y = [PISTAR], [YBAR]
    for t in range(1, K + 1):
        en, vn = demand.get(t, 0), supply.get(t, 0)
        p = a * pi[t - 1] + b + ce * en + cv * vn
        pi.append(p)
        y.append(YBAR - gamma * (p - PISTAR) + kappa * en)
    return np.array(pi), np.array(y)


def make_gif(slug, title, demand, supply, outdir,
             gamma=GAMMA_DEF, phi=PHI_DEF, kappa=KAPPA_DEF):
    demand = demand or {}
    supply = supply or {}
    pi, y = simulate(demand, supply, gamma, phi, kappa)
    xx = np.linspace(0, 10, 200)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 4.0), dpi=85,
                                   gridspec_kw={"width_ratios": [1.05, 1.0]})
    fig.subplots_adjust(left=0.07, right=0.975, top=0.82, bottom=0.13, wspace=0.28)
    fig.suptitle(title, color=INK, fontsize=13, fontweight="bold", y=0.975)
    period_text = fig.text(0.5, 0.89, "", color=ACCENT, fontsize=10,
                           ha="center", fontweight="bold")

    def dad(period):
        eps = demand.get(period, 0)
        return PISTAR - (1 / gamma) * (xx - kappa * eps - YBAR)

    def das(period):
        nu = supply.get(period, 0)
        prev = pi[period - 1] if period >= 1 else PISTAR
        return prev + phi * (xx - YBAR) + nu

    def draw(frame):
        axL.clear(); axR.clear()
        axL.set_facecolor(PAPER)
        axL.axvline(YBAR, color=GOLD, lw=1.4, alpha=0.85)
        axL.axhline(PISTAR, color=GOLD, lw=1.4, alpha=0.85)
        axL.plot(xx, PISTAR - (1 / gamma) * (xx - YBAR), color=DAD_C, lw=1, alpha=0.18)
        axL.plot(xx, PISTAR + phi * (xx - YBAR), color=DAS_C, lw=1, alpha=0.18)
        if frame >= 1:
            axL.plot(xx, dad(frame), color=DAD_C, lw=2.4, alpha=0.95, label="DAD")
            axL.plot(xx, das(frame), color=DAS_C, lw=2.4, alpha=0.95, label="DAS")
            axL.plot(y[:frame + 1], pi[:frame + 1], color=ACCENT, lw=1.6,
                     alpha=0.55, marker="o", ms=3, zorder=4)
        else:
            axL.plot([], [], color=DAD_C, lw=2.4, label="DAD")
            axL.plot([], [], color=DAS_C, lw=2.4, label="DAS")
        axL.scatter([y[frame]], [pi[frame]], s=70, color=ACCENT,
                    edgecolor="white", lw=1.5, zorder=5)
        axL.set_xlim(0, 10); axL.set_ylim(0, 10)
        axL.set_xlabel("Output  $Y$", color=INK)
        axL.set_ylabel("Inflation  $\\pi$", color=INK)
        axL.set_title("DAS\u2013DAD Diagram", color=INK, fontsize=11, pad=6)
        axL.tick_params(colors=MUTED, labelsize=8)
        axL.legend(loc="upper right", fontsize=8, frameon=False)

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
        axR.set_xlabel("Period", color=INK)
        axR.set_title("Time Path", color=INK, fontsize=11, pad=6)
        axR.tick_params(colors=MUTED, labelsize=8)
        axR.legend(loc="upper right", fontsize=8, frameon=False)

        lbl = "t\u22121 (equilibrium)" if frame == 0 else (
              "t" if frame == 1 else f"t+{frame - 1}")
        period_text.set_text(f"Period: {lbl}")

    frames = list(range(0, K + 1)) + [K] * 3
    anim = animation.FuncAnimation(fig, draw, frames=frames, interval=850)
    path = os.path.join(outdir, f"{slug}.gif")
    anim.save(path, writer=animation.PillowWriter(fps=1.3))
    plt.close(fig)
    print("wrote", path, f"(troughY={y.min():.2f}, peakPi={pi.max():.2f})")
    return path


def custom_gif(title="Custom shock", demand=None, supply=None,
               gamma=GAMMA_DEF, phi=PHI_DEF, kappa=KAPPA_DEF,
               out="media/custom.gif"):
    """Make a single GIF from your own parameters and shocks. Returns the path."""
    outdir = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(outdir, exist_ok=True)
    slug = os.path.splitext(os.path.basename(out))[0]
    return make_gif(slug, title, demand or {}, supply or {}, outdir,
                    gamma=gamma, phi=phi, kappa=kappa)


# ----- the eight README scenarios ----------------------------------------
SCENARIOS = [
    ("demand_shock_positive",  "Positive Demand Shock (Boom & Inflation)",      {1: 4},               {}),
    ("demand_shock_negative",  "Negative Demand Shock (Recession)",             {1: -4},              {}),
    ("supply_shock_adverse",   "Adverse Supply Shock (Stagflation)",            {},                   {1: 4}),
    ("supply_shock_favourable","Favourable Supply Shock (Cheaper Oil)",         {},                   {1: -4}),
    ("oil_crisis_1970s",       "Oil Crisis 1970s (Persistent Stagflation)",     {},                   {1: 4, 2: 2, 3: 2}),
    ("fiscal_expansion",       "Fiscal Expansion (Sustained Boom)",             {1: 4, 2: 2, 3: 2},   {}),
    ("financial_crisis_2008",  "Financial Crisis 2008 (Deep Recession)",        {1: -4, 2: -4, 3: -2},{}),
    ("covid_19",               "COVID-19 (Collapse, Recovery & Inflation Wave)",{1: -4, 2: -2},       {3: 2}),
]


def main():
    outdir = os.path.join(os.path.dirname(__file__), "media")
    os.makedirs(outdir, exist_ok=True)
    for slug, title, demand, supply in SCENARIOS:
        make_gif(slug, title, demand, supply, outdir)


if __name__ == "__main__":
    main()
