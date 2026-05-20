"""
Scientific diagram generator.
Detects the topic and draws an appropriate matplotlib diagram.
Falls back to asking Groq for a description and making a labeled schematic.
"""

import io
import re
import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Arc, Circle, FancyBboxPatch
from matplotlib.lines import Line2D

logger = logging.getLogger(__name__)


# ── Router ───────────────────────────────────────────────────────────────────

def generate_diagram(topic: str) -> bytes:
    """Return PNG bytes for the best diagram matching `topic`."""
    t = topic.lower()

    if any(k in t for k in ["cell", "plant cell", "animal cell"]):
        return _cell_diagram("plant" in t)
    if any(k in t for k in ["dna", "double helix", "nucleotide"]):
        return _dna_diagram()
    if any(k in t for k in ["photosynthesis"]):
        return _photosynthesis_diagram()
    if any(k in t for k in ["circuit", "resistor", "capacitor", "ohm"]):
        return _circuit_diagram()
    if any(k in t for k in ["wave", "sine", "frequency", "amplitude"]):
        return _wave_diagram()
    if any(k in t for k in ["force", "free body", "newton"]):
        return _free_body_diagram()
    if any(k in t for k in ["periodic", "element", "atomic"]):
        return _atom_diagram()
    if any(k in t for k in ["mitosis", "cell division"]):
        return _mitosis_diagram()
    if any(k in t for k in ["graph", "function", "plot", "parabola", "quadratic"]):
        return _math_function_plot(t)
    if any(k in t for k in ["water cycle", "hydrological"]):
        return _water_cycle_diagram()
    if any(k in t for k in ["heart", "cardiac", "blood"]):
        return _heart_diagram()
    # Generic flowchart / concept map
    return _concept_diagram(topic)


# ── Individual diagram functions ─────────────────────────────────────────────

def _cell_diagram(plant: bool = True) -> bytes:
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.set_facecolor("#F0F8FF")
    fig.patch.set_facecolor("#F0F8FF")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title(f"{'Plant' if plant else 'Animal'} Cell Structure", fontsize=16, fontweight="bold", pad=15)

    if plant:
        # Cell wall (outer rectangle)
        cell_wall = FancyBboxPatch((0.5, 0.5), 9, 6, boxstyle="square,pad=0.1",
                                   linewidth=3, edgecolor="#4CAF50", facecolor="#E8F5E9", zorder=1)
        ax.add_patch(cell_wall)
        ax.text(1.0, 6.3, "Cell Wall", fontsize=9, color="#2E7D32", fontweight="bold")

    # Cell membrane
    mem = FancyBboxPatch((0.9, 0.9), 8.2, 5.2, boxstyle="round,pad=0.2",
                         linewidth=2, edgecolor="#1976D2", facecolor="#E3F2FD", zorder=2)
    ax.add_patch(mem)
    ax.text(1.2, 5.8, "Cell Membrane", fontsize=9, color="#1565C0", fontweight="bold")

    # Nucleus
    nuc = Circle((5, 3.5), 1.2, linewidth=2, edgecolor="#7B1FA2", facecolor="#F3E5F5", zorder=4)
    ax.add_patch(nuc)
    ax.text(5, 3.5, "Nucleus", ha="center", va="center", fontsize=9, fontweight="bold", color="#4A148C")

    # Nucleolus
    nucl = Circle((5, 3.5), 0.4, linewidth=1, edgecolor="#4A148C", facecolor="#CE93D8", zorder=5)
    ax.add_patch(nucl)
    ax.text(5, 3.5, "Nucleolus", ha="center", va="center", fontsize=6, color="white")

    # Mitochondria
    for (x, y) in [(2.5, 4.5), (7.5, 2.5)]:
        mit = patches.Ellipse((x, y), 1.2, 0.6, linewidth=1.5, edgecolor="#E65100",
                               facecolor="#FFE0B2", zorder=3)
        ax.add_patch(mit)
        ax.text(x, y, "Mitochondria", ha="center", va="center", fontsize=7, color="#BF360C")

    # Vacuole (plant only)
    if plant:
        vac = patches.Ellipse((5, 1.8), 2.5, 1.0, linewidth=1.5, edgecolor="#00796B",
                               facecolor="#B2DFDB", zorder=3)
        ax.add_patch(vac)
        ax.text(5, 1.8, "Central Vacuole", ha="center", va="center", fontsize=8, color="#004D40")

    # Chloroplasts (plant only)
    if plant:
        for (x, y) in [(2.0, 2.5), (7.8, 4.5), (2.5, 5.0)]:
            chl = patches.Ellipse((x, y), 0.9, 0.45, linewidth=1.5, edgecolor="#388E3C",
                                   facecolor="#A5D6A7", zorder=3)
            ax.add_patch(chl)
            ax.text(x, y, "Chloroplast", ha="center", va="center", fontsize=6, color="#1B5E20")

    # ER (rough squiggle lines)
    x_er = np.linspace(6.2, 8.5, 30)
    y_er = 3.8 + 0.2 * np.sin(x_er * 6)
    ax.plot(x_er, y_er, color="#F57F17", linewidth=2, zorder=3)
    ax.text(7.3, 4.2, "ER", ha="center", fontsize=8, color="#E65100", fontweight="bold")

    # Golgi apparatus
    for j in range(4):
        g = patches.Arc((3.5, 3.0 + j * 0.18), 1.0, 0.3, angle=0,
                         theta1=0, theta2=180, color="#F44336", linewidth=2, zorder=3)
        ax.add_patch(g)
    ax.text(3.5, 3.9, "Golgi Body", ha="center", fontsize=8, color="#B71C1C", fontweight="bold")

    ax.text(5, 0.3, f"© EduBot AI — {'Plant' if plant else 'Animal'} Cell",
            ha="center", fontsize=8, color="grey")
    return _fig_to_bytes(fig)


def _dna_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.set_facecolor("#0D1117")
    fig.patch.set_facecolor("#0D1117")
    ax.set_xlim(-3, 3)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title("DNA Double Helix Structure", color="white", fontsize=16, fontweight="bold", pad=12)

    t = np.linspace(0, 4 * np.pi, 300)
    y = np.linspace(1, 9, 300)
    x1 = np.sin(t)
    x2 = -np.sin(t)

    ax.plot(x1, y, color="#00E5FF", linewidth=3, alpha=0.9, label="Strand 1")
    ax.plot(x2, y, color="#FF4081", linewidth=3, alpha=0.9, label="Strand 2")

    # Base pairs
    bases = {"A": "#FFEB3B", "T": "#FF9800", "G": "#4CAF50", "C": "#9C27B0"}
    pair_labels = [("A", "T"), ("G", "C"), ("T", "A"), ("C", "G"), ("A", "T"),
                   ("G", "C"), ("T", "A"), ("C", "G"), ("A", "T"), ("G", "C")]
    for i, (b1, b2) in enumerate(pair_labels):
        yi = 1.5 + i * 0.75
        xi1 = np.sin(4 * np.pi * (yi - 1) / 8)
        xi2 = -xi1
        ax.plot([xi1, xi2], [yi, yi], color="white", linewidth=1.5, alpha=0.5, linestyle="--")
        ax.scatter(xi1, yi, color=bases[b1], s=100, zorder=5)
        ax.scatter(xi2, yi, color=bases[b2], s=100, zorder=5)
        ax.text(xi1 + 0.15 * np.sign(xi1), yi, b1, color=bases[b1], fontsize=8, va="center", fontweight="bold")
        ax.text(xi2 + 0.15 * np.sign(xi2), yi, b2, color=bases[b2], fontsize=8, va="center", fontweight="bold")

    legend_elements = [
        mpatches.Patch(color="#FFEB3B", label="Adenine (A)"),
        mpatches.Patch(color="#FF9800", label="Thymine (T)"),
        mpatches.Patch(color="#4CAF50", label="Guanine (G)"),
        mpatches.Patch(color="#9C27B0", label="Cytosine (C)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9,
              facecolor="#1A1A2E", labelcolor="white", edgecolor="grey")
    ax.text(0, 0.4, "Base Pair Rule: A–T, G–C", ha="center", color="white",
            fontsize=9, style="italic")
    return _fig_to_bytes(fig)


def _photosynthesis_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_facecolor("#E8F5E9")
    fig.patch.set_facecolor("#E8F5E9")
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("Photosynthesis", fontsize=18, fontweight="bold", color="#1B5E20", pad=12)

    # Leaf shape
    leaf = mpatches.FancyBboxPatch((3.5, 1.5), 4, 4, boxstyle="round,pad=0.5",
                                   facecolor="#66BB6A", edgecolor="#2E7D32", linewidth=3)
    ax.add_patch(leaf)
    ax.text(5.5, 3.5, "Leaf /\nChloroplast", ha="center", va="center",
            fontsize=11, fontweight="bold", color="white")

    # Inputs
    ax.annotate("☀️ Light Energy", xy=(3.5, 5.5), xytext=(1.0, 6.2),
                fontsize=10, color="#E65100", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#E65100", lw=2))
    ax.annotate("💧 H₂O\n(Water)", xy=(3.5, 3.0), xytext=(0.5, 3.0),
                fontsize=10, color="#1565C0", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#1565C0", lw=2))
    ax.annotate("CO₂\n(Carbon Dioxide)", xy=(4.0, 1.5), xytext=(1.0, 0.8),
                fontsize=10, color="#4E342E", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#4E342E", lw=2))

    # Outputs
    ax.annotate("🌿 C₆H₁₂O₆\n(Glucose)", xy=(7.5, 5.0), xytext=(8.5, 6.0),
                fontsize=10, color="#2E7D32", fontweight="bold",
                arrowprops=dict(arrowstyle="<-", color="#2E7D32", lw=2))
    ax.annotate("O₂ Released\n(Oxygen)", xy=(7.5, 3.5), xytext=(8.5, 3.0),
                fontsize=10, color="#0288D1", fontweight="bold",
                arrowprops=dict(arrowstyle="<-", color="#0288D1", lw=2))

    # Equation
    eq_box = FancyBboxPatch((0.5, 0.1), 10, 0.9, boxstyle="round,pad=0.1",
                             facecolor="#C8E6C9", edgecolor="#388E3C", linewidth=2)
    ax.add_patch(eq_box)
    ax.text(5.5, 0.55,
            "6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂",
            ha="center", va="center", fontsize=11, fontweight="bold", color="#1B5E20")
    return _fig_to_bytes(fig)


def _circuit_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Basic Electric Circuit", fontsize=16, fontweight="bold", pad=12)

    # Wires
    ax.plot([1, 9, 9, 1, 1], [1, 1, 5, 5, 1], "k-", linewidth=2.5)

    # Battery (left side)
    for i, y in enumerate([2.5, 3.0, 3.5]):
        lw = 3 if i % 2 == 0 else 1.5
        ax.plot([0.7, 1.3], [y, y], "b-", linewidth=lw)
    ax.text(0.3, 3.0, "Battery\n(EMF)", ha="center", va="center", fontsize=9, color="#1565C0")
    ax.text(0.3, 2.0, "+ / −", ha="center", fontsize=8, color="grey")

    # Resistor (top)
    rx = np.array([2.5, 2.7, 3.0, 3.3, 3.6, 3.9, 4.2, 4.5, 4.7])
    ry_base = 5.0
    ry = ry_base + np.array([0, 0.3, -0.3, 0.3, -0.3, 0.3, -0.3, 0.3, 0])
    ax.plot(rx, np.full_like(rx, ry_base), "k-", linewidth=2.5)  # connecting wires
    ax.plot(rx, ry, "r-", linewidth=2.5)
    ax.text(3.6, 5.55, "R = Resistor (Ω)", ha="center", fontsize=9, color="#C62828", fontweight="bold")

    # Bulb (bottom)
    bulb = Circle((5, 1.0), 0.5, linewidth=2, edgecolor="#F57F17", facecolor="#FFF9C4")
    ax.add_patch(bulb)
    ax.text(5, 1.0, "💡", ha="center", va="center", fontsize=14)
    ax.text(5, 0.3, "Load (Bulb)", ha="center", fontsize=9, color="#E65100", fontweight="bold")

    # Ammeter
    am = Circle((7.5, 1.0), 0.35, linewidth=2, edgecolor="#6A1B9A", facecolor="#F3E5F5")
    ax.add_patch(am)
    ax.text(7.5, 1.0, "A", ha="center", va="center", fontsize=10, fontweight="bold", color="#4A148C")
    ax.text(7.5, 0.4, "Ammeter", ha="center", fontsize=8, color="#4A148C")

    # Voltmeter
    vm = Circle((9.0, 3.0), 0.35, linewidth=2, edgecolor="#1B5E20", facecolor="#E8F5E9")
    ax.add_patch(vm)
    ax.text(9.0, 3.0, "V", ha="center", va="center", fontsize=10, fontweight="bold", color="#1B5E20")
    ax.text(9.6, 3.0, "Voltmeter", ha="left", fontsize=8, color="#1B5E20")

    # Arrow for current direction
    ax.annotate("", xy=(6, 1), xytext=(4, 1),
                arrowprops=dict(arrowstyle="->", color="orange", lw=2))
    ax.text(5, 0.65, "Current (I)", ha="center", fontsize=8, color="#E65100")

    ax.text(5, 5.7, "Ohm's Law:  V = I × R", ha="center", fontsize=12,
            fontweight="bold", color="#1A237E",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#E8EAF6", edgecolor="#3949AB"))
    return _fig_to_bytes(fig)


def _wave_diagram() -> bytes:
    fig, axes = plt.subplots(2, 1, figsize=(10, 7))
    fig.suptitle("Wave Properties", fontsize=16, fontweight="bold")

    x = np.linspace(0, 4 * np.pi, 500)

    # Wave 1
    axes[0].plot(x, np.sin(x), color="#1565C0", linewidth=2.5)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_title("Transverse Wave")
    axes[0].set_ylabel("Displacement (m)")
    axes[0].set_ylim(-1.6, 1.8)
    # Annotations
    axes[0].annotate("", xy=(np.pi, 1), xytext=(0, 1),
                     arrowprops=dict(arrowstyle="<->", color="red", lw=1.5))
    axes[0].text(np.pi / 2, 1.1, "λ (wavelength)", ha="center", color="red", fontsize=10)
    axes[0].annotate("", xy=(np.pi / 2, 0), xytext=(np.pi / 2, 1),
                     arrowprops=dict(arrowstyle="<->", color="#2E7D32", lw=1.5))
    axes[0].text(np.pi / 2 + 0.3, 0.5, "A (amplitude)", color="#2E7D32", fontsize=10)
    axes[0].grid(alpha=0.3)

    # Wave 2 — different frequency
    axes[1].plot(x, 0.5 * np.sin(3 * x), color="#E65100", linewidth=2.5, label="High frequency")
    axes[1].plot(x, np.sin(x), color="#1565C0", linewidth=2.5, linestyle="--", alpha=0.5, label="Low frequency")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("Frequency Comparison")
    axes[1].set_xlabel("Position (x)")
    axes[1].set_ylabel("Displacement (m)")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    axes[1].text(2, 0.6, "v = f × λ", fontsize=12, fontweight="bold",
                 bbox=dict(boxstyle="round", facecolor="#FFF9C4", edgecolor="#F57F17"))

    plt.tight_layout()
    return _fig_to_bytes(fig)


def _free_body_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor("#FAFAFA")
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.axis("off")
    ax.set_title("Free Body Diagram", fontsize=16, fontweight="bold", pad=12)
    ax.set_aspect("equal")

    # Object
    obj = FancyBboxPatch((-1, -1), 2, 2, boxstyle="round,pad=0.1",
                          facecolor="#BBDEFB", edgecolor="#1565C0", linewidth=3)
    ax.add_patch(obj)
    ax.text(0, 0, "m", ha="center", va="center", fontsize=18, fontweight="bold", color="#1565C0")

    arrow_props = dict(arrowstyle="-|>", lw=2.5, mutation_scale=18)

    # Weight
    ax.annotate("", xy=(0, -3.5), xytext=(0, -1),
                arrowprops={**arrow_props, "color": "#C62828"})
    ax.text(0.3, -2.5, "W = mg\n(Weight)", color="#C62828", fontsize=10, fontweight="bold")

    # Normal
    ax.annotate("", xy=(0, 3.5), xytext=(0, 1),
                arrowprops={**arrow_props, "color": "#2E7D32"})
    ax.text(0.3, 2.5, "N\n(Normal)", color="#2E7D32", fontsize=10, fontweight="bold")

    # Applied force
    ax.annotate("", xy=(3.5, 0), xytext=(1, 0),
                arrowprops={**arrow_props, "color": "#E65100"})
    ax.text(2.2, 0.3, "F (Applied)", color="#E65100", fontsize=10, fontweight="bold")

    # Friction
    ax.annotate("", xy=(-3.5, 0), xytext=(-1, 0),
                arrowprops={**arrow_props, "color": "#6A1B9A"})
    ax.text(-3.8, 0.3, "f (Friction)", color="#6A1B9A", fontsize=10, fontweight="bold")

    ax.text(0, -4.6, "ΣF = ma  (Newton's 2nd Law)", ha="center", fontsize=12,
            fontweight="bold", color="#1A237E",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8EAF6", edgecolor="#3949AB"))
    return _fig_to_bytes(fig)


def _atom_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#0D1117")
    fig.patch.set_facecolor("#0D1117")
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Atom Structure (Bohr Model)", color="white", fontsize=16, fontweight="bold", pad=12)

    # Nucleus
    nuc = Circle((0, 0), 0.8, facecolor="#FF5252", edgecolor="white", linewidth=2, zorder=5)
    ax.add_patch(nuc)
    ax.text(0, 0.05, "Nucleus\n(p⁺, n⁰)", ha="center", va="center", fontsize=8,
            color="white", fontweight="bold", zorder=6)

    # Electron shells
    shell_data = [(1.8, 2, "#FFD700"), (3.0, 8, "#00E5FF"), (4.2, 8, "#69F0AE")]
    for (r, n_e, col) in shell_data:
        orbit = plt.Circle((0, 0), r, fill=False, edgecolor=col, linewidth=1.5, linestyle="--", alpha=0.6)
        ax.add_patch(orbit)
        for j in range(n_e):
            angle = 2 * np.pi * j / n_e
            ex, ey = r * np.cos(angle), r * np.sin(angle)
            e = Circle((ex, ey), 0.18, facecolor=col, edgecolor="white", linewidth=1, zorder=5)
            ax.add_patch(e)
            ax.text(ex, ey, "e⁻", ha="center", va="center", fontsize=5, color="black", zorder=6)

    ax.text(0, -4.7, "Electrons orbit the nucleus in fixed energy shells",
            ha="center", color="white", fontsize=9, style="italic")
    return _fig_to_bytes(fig)


def _mitosis_diagram() -> bytes:
    fig, axes = plt.subplots(1, 5, figsize=(14, 4))
    phases = ["Interphase", "Prophase", "Metaphase", "Anaphase", "Telophase"]
    colors_bg = ["#E3F2FD", "#FFF3E0", "#F3E5F5", "#E8F5E9", "#FCE4EC"]

    for i, (ax, phase, bg) in enumerate(zip(axes, phases, colors_bg)):
        ax.set_facecolor(bg)
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 4)
        ax.axis("off")
        ax.set_title(phase, fontsize=9, fontweight="bold")

        cell = Circle((2, 2), 1.6, facecolor=bg, edgecolor="#1565C0", linewidth=2)
        ax.add_patch(cell)

        if i == 0:  # Interphase — nucleus visible
            nuc = Circle((2, 2), 0.7, facecolor="#CE93D8", edgecolor="#7B1FA2", linewidth=1.5)
            ax.add_patch(nuc)
        elif i == 1:  # Prophase — chromosomes appear
            for dx, dy in [(-0.3, 0.2), (0.3, -0.2), (-0.2, -0.3), (0.2, 0.3)]:
                ax.plot([2 + dx - 0.15, 2 + dx + 0.15], [2 + dy, 2 + dy],
                        color="#E91E63", linewidth=3)
        elif i == 2:  # Metaphase — aligned
            for j in range(4):
                ax.plot([2 - 0.15, 2 + 0.15], [1.4 + j * 0.4, 1.4 + j * 0.4],
                        color="#E91E63", linewidth=3)
            ax.axhline(2, xmin=0.2, xmax=0.8, color="orange", linewidth=1.5, linestyle="--")
        elif i == 3:  # Anaphase — separating
            for j in range(4):
                ax.plot([1.7, 1.9], [1.4 + j * 0.35, 1.4 + j * 0.35], color="#E91E63", linewidth=2.5)
                ax.plot([2.1, 2.3], [1.4 + j * 0.35, 1.4 + j * 0.35], color="#E91E63", linewidth=2.5)
        else:  # Telophase — two nuclei
            for cx in [1.5, 2.5]:
                n = Circle((cx, 2), 0.5, facecolor="#CE93D8", edgecolor="#7B1FA2", linewidth=1.5)
                ax.add_patch(n)

    fig.suptitle("Stages of Mitosis (Cell Division)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    return _fig_to_bytes(fig)


def _math_function_plot(topic: str) -> bytes:
    fig, ax = plt.subplots(figsize=(9, 6))
    x = np.linspace(-5, 5, 500)

    if "parabola" in topic or "quadratic" in topic:
        y = x ** 2
        label = "y = x²  (Parabola)"
        color = "#1565C0"
    elif "cubic" in topic:
        y = x ** 3
        label = "y = x³  (Cubic)"
        color = "#6A1B9A"
    elif "sine" in topic or "sin" in topic:
        y = np.sin(x)
        label = "y = sin(x)"
        color = "#C62828"
    elif "cosine" in topic or "cos" in topic:
        y = np.cos(x)
        label = "y = cos(x)"
        color = "#2E7D32"
    elif "exponential" in topic or "exp" in topic:
        x = np.linspace(-3, 3, 500)
        y = np.exp(x)
        label = "y = eˣ  (Exponential)"
        color = "#E65100"
    else:
        y = x ** 2 - 2 * x - 3
        label = "y = x² − 2x − 3  (Quadratic)"
        color = "#1565C0"

    ax.plot(x, y, color=color, linewidth=2.5, label=label)
    ax.axhline(0, color="black", linewidth=1.2)
    ax.axvline(0, color="black", linewidth=1.2)
    ax.grid(alpha=0.3)
    ax.set_xlabel("x", fontsize=12)
    ax.set_ylabel("y", fontsize=12)
    ax.set_title(f"Function Graph: {label}", fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_ylim(-10, 20)
    plt.tight_layout()
    return _fig_to_bytes(fig)


def _water_cycle_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_facecolor("#E3F2FD")
    fig.patch.set_facecolor("#E3F2FD")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.set_title("The Water Cycle (Hydrological Cycle)", fontsize=16, fontweight="bold", pad=12)

    # Ground
    ax.fill_between([0, 12], [0, 0], [1.0, 1.0], color="#8D6E63", alpha=0.6)
    ax.text(6, 0.5, "Ground / Land Surface", ha="center", fontsize=10, color="white", fontweight="bold")

    # Ocean
    ocean = patches.Ellipse((1.5, 0.9), 2.5, 0.8, facecolor="#1565C0", edgecolor="#0D47A1", linewidth=2)
    ax.add_patch(ocean)
    ax.text(1.5, 0.9, "🌊 Ocean", ha="center", va="center", fontsize=10, color="white", fontweight="bold")

    # Mountain
    mountain = plt.Polygon([[8, 1], [9.5, 4], [11, 1]], facecolor="#6D4C41", edgecolor="#4E342E", linewidth=2)
    ax.add_patch(mountain)
    ax.text(9.5, 2.0, "⛰️ Mountain", ha="center", fontsize=9, color="white", fontweight="bold")

    # Cloud
    for (cx, cy) in [(4, 5.5), (6, 5.8), (8, 5.3)]:
        cl = patches.Ellipse((cx, cy), 2, 0.9, facecolor="#ECEFF1", edgecolor="#90A4AE", linewidth=2)
        ax.add_patch(cl)
    ax.text(6, 5.7, "☁️ Clouds", ha="center", fontsize=10, fontweight="bold", color="#37474F")

    # Evaporation
    ax.annotate("", xy=(4, 5.0), xytext=(2.0, 1.5),
                arrowprops=dict(arrowstyle="->", color="#E65100", lw=2.5,
                                connectionstyle="arc3,rad=-0.3"))
    ax.text(2.2, 3.5, "Evaporation\n☀️", color="#E65100", fontsize=9, fontweight="bold")

    # Condensation
    ax.text(6.5, 4.9, "Condensation\n💧→☁️", color="#1565C0", fontsize=9, fontweight="bold")

    # Precipitation
    ax.annotate("", xy=(8.5, 1.5), xytext=(8, 5.0),
                arrowprops=dict(arrowstyle="->", color="#0D47A1", lw=2.5,
                                connectionstyle="arc3,rad=0.2"))
    ax.text(9.0, 3.0, "🌧️ Precipitation", color="#0D47A1", fontsize=9, fontweight="bold")

    # Runoff
    ax.annotate("", xy=(1.5, 1.2), xytext=(8, 1.2),
                arrowprops=dict(arrowstyle="->", color="#00838F", lw=2.5))
    ax.text(5, 1.4, "Surface Runoff →", ha="center", color="#00838F", fontsize=9, fontweight="bold")

    return _fig_to_bytes(fig)


def _heart_diagram() -> bytes:
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#FFF8F8")
    fig.patch.set_facecolor("#FFF8F8")
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.axis("off")
    ax.set_title("Human Heart — Blood Flow", fontsize=16, fontweight="bold", pad=12)

    # Simple heart representation
    heart_outline = plt.Polygon([
        [0, -4], [-3, 0], [-3, 2], [-2, 3.5], [0, 3], [2, 3.5], [3, 2], [3, 0], [0, -4]
    ], facecolor="#FFCDD2", edgecolor="#C62828", linewidth=3, closed=True)
    ax.add_patch(heart_outline)

    # Chambers
    labels = {
        "Right\nAtrium":  (-2.2,  1.0, "#EF9A9A"),
        "Left\nAtrium":   ( 1.8,  1.0, "#EF9A9A"),
        "Right\nVentricle": (-1.8, -1.5, "#FFCDD2"),
        "Left\nVentricle":  ( 1.5, -1.5, "#FF8A80"),
    }
    for label, (x, y, col) in labels.items():
        box = FancyBboxPatch((x - 1.1, y - 0.7), 2.2, 1.4,
                              boxstyle="round,pad=0.15",
                              facecolor=col, edgecolor="#B71C1C", linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=9, fontweight="bold", color="#B71C1C")

    # Vessels
    ax.annotate("Aorta →", xy=(3, 2.5), xytext=(2.5, 2.5),
                fontsize=10, color="#1565C0", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#1565C0", lw=2))
    ax.annotate("Pulmonary\nArtery →", xy=(-3, 2.5), xytext=(-4.5, 2.5),
                fontsize=9, color="#2E7D32", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=2))
    ax.annotate("Vena Cava ↓", xy=(-1.5, 3), xytext=(-2.5, 4.5),
                fontsize=9, color="#C62828", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#C62828", lw=2))

    ax.text(0, -4.5,
            "Lub-Dub: Heart pumps ~5L of blood/minute",
            ha="center", fontsize=10, color="#C62828", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFEBEE", edgecolor="#E57373"))
    return _fig_to_bytes(fig)


def _concept_diagram(topic: str) -> bytes:
    """Generic concept map / mind-map style diagram."""
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_facecolor("#F8F9FA")
    fig.patch.set_facecolor("#F8F9FA")
    ax.set_xlim(-6, 6)
    ax.set_ylim(-4, 4)
    ax.axis("off")
    ax.set_title(f"Concept Map: {topic[:50]}", fontsize=14, fontweight="bold", pad=12)

    # Central node
    center = FancyBboxPatch((-2, -0.6), 4, 1.2, boxstyle="round,pad=0.2",
                             facecolor="#E8EAF6", edgecolor="#3949AB", linewidth=3)
    ax.add_patch(center)
    ax.text(0, 0, topic[:30], ha="center", va="center", fontsize=12,
            fontweight="bold", color="#1A237E")

    # Satellite nodes
    satellites = [
        ("Definition", -4.5, 2.5, "#E3F2FD", "#1565C0"),
        ("Formula /\nEquation", 4.5, 2.5, "#FFF3E0", "#E65100"),
        ("Applications", 4.5, -2.5, "#E8F5E9", "#2E7D32"),
        ("Key Facts", -4.5, -2.5, "#F3E5F5", "#6A1B9A"),
        ("Related\nTopics", 0, 3.5, "#FCE4EC", "#C62828"),
    ]
    for label, x, y, bg, ec in satellites:
        box = FancyBboxPatch((x - 1.3, y - 0.55), 2.6, 1.1,
                              boxstyle="round,pad=0.15", facecolor=bg, edgecolor=ec, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=9, color=ec, fontweight="bold")
        ax.plot([0, x], [0, y], color=ec, linewidth=1.5, linestyle="--", alpha=0.6, zorder=0)

    ax.text(0, -3.7, "📚 EduBot AI — Diagram generated for study purposes",
            ha="center", fontsize=8, color="grey")
    return _fig_to_bytes(fig)


# ── Helper ───────────────────────────────────────────────────────────────────

def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
