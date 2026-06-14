"""
========================================================
Visualization Module
========================================================
Generates static charts from logged sensor data using
matplotlib and seaborn.

Outputs saved to: outputs/charts/

Charts generated:
  1. sensor_timeline.png    — All 5 sensors over time
  2. threshold_analysis.png — Bar chart vs thresholds
  3. pump_timeline.png      — Pump ON/OFF over time
  4. alert_heatmap.png      — Alert frequency heatmap
  5. correlation_matrix.png — Sensor correlation heatmap
  6. scenario_boxplot.png   — Values per scenario
========================================================
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from typing import Union

# ── Output path ──────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR  = os.path.join(BASE_DIR, "outputs", "charts")

# ── Style config ─────────────────────────────────────────────────────────────
PALETTE = {
    "soil_moisture":   "#4CAF50",
    "temperature":     "#FF5722",
    "humidity":        "#2196F3",
    "light_intensity": "#FFC107",
    "water_level":     "#00BCD4",
    "pump_on":         "#4CAF50",
    "pump_off":        "#F44336",
}

sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({
    "figure.facecolor": "#1A1A2E",
    "axes.facecolor":   "#16213E",
    "axes.edgecolor":   "#444",
    "axes.labelcolor":  "#E0E0E0",
    "xtick.color":      "#E0E0E0",
    "ytick.color":      "#E0E0E0",
    "text.color":       "#E0E0E0",
    "grid.color":       "#2A2A4A",
    "grid.alpha":       0.5,
    "font.family":      "sans-serif",
})


def _ensure_charts_dir():
    os.makedirs(CHARTS_DIR, exist_ok=True)


def load_csv(csv_path: str) -> pd.DataFrame:
    """Load a sensor log CSV into a DataFrame."""
    df = pd.read_csv(csv_path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def plot_sensor_timeline(df: pd.DataFrame, save: bool = True) -> str:
    """Plot all 5 sensors over time in a multi-panel chart."""
    _ensure_charts_dir()
    fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)
    fig.patch.set_facecolor("#1A1A2E")
    fig.suptitle("🌱 Sensor Readings Timeline", fontsize=18, fontweight="bold",
                 color="#00E676", y=0.98)

    sensors = [
        ("soil_moisture",   "Soil Moisture (%)",    PALETTE["soil_moisture"]),
        ("temperature",     "Temperature (°C)",     PALETTE["temperature"]),
        ("humidity",        "Humidity (%)",          PALETTE["humidity"]),
        ("light_intensity", "Light Intensity (lux)", PALETTE["light_intensity"]),
        ("water_level",     "Water Level (%)",       PALETTE["water_level"]),
    ]

    x = df["reading_id"] if "reading_id" in df.columns else range(len(df))

    for ax, (col, label, color) in zip(axes, sensors):
        ax.set_facecolor("#16213E")
        if col in df.columns:
            ax.plot(x, df[col], color=color, linewidth=1.8, alpha=0.9)
            ax.fill_between(x, df[col], alpha=0.2, color=color)
            ax.set_ylabel(label, fontsize=10, color=color)
            ax.tick_params(colors="#E0E0E0")

    axes[-1].set_xlabel("Reading #", fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    path = os.path.join(CHARTS_DIR, "sensor_timeline.png")
    if save:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
    return path


def plot_threshold_analysis(df: pd.DataFrame, save: bool = True) -> str:
    """Bar chart comparing average sensor values to safe thresholds."""
    _ensure_charts_dir()

    SAFE_ZONES = {
        "soil_moisture":    (25, 85),
        "temperature":      (10, 38),
        "humidity":         (30, 90),
        "water_level":      (20, 98),
    }

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.patch.set_facecolor("#1A1A2E")
    fig.suptitle("📊 Sensor Values vs Safe Thresholds", fontsize=16,
                 fontweight="bold", color="#00E676")

    sensor_items = list(SAFE_ZONES.items())
    for idx, (sensor, (lo, hi)) in enumerate(sensor_items):
        ax = axes[idx // 2][idx % 2]
        ax.set_facecolor("#16213E")

        if sensor not in df.columns:
            continue

        avg_val = df[sensor].mean()
        color = PALETTE.get(sensor, "#888")

        # Background safe zone
        ax.axhspan(lo, hi, alpha=0.15, color="#4CAF50", label="Safe Zone")
        ax.axhline(lo, color="#FFC107", linestyle="--", linewidth=1, label=f"Min: {lo}")
        ax.axhline(hi, color="#FF5722", linestyle="--", linewidth=1, label=f"Max: {hi}")

        ax.plot(df.index, df[sensor], color=color, linewidth=1.2, alpha=0.8)
        ax.axhline(avg_val, color="white", linestyle=":", linewidth=1.5,
                   label=f"Avg: {avg_val:.1f}")

        ax.set_title(sensor.replace("_", " ").title(), color="#E0E0E0", fontsize=12)
        ax.legend(fontsize=8, facecolor="#1A1A2E", labelcolor="#E0E0E0")
        ax.tick_params(colors="#E0E0E0")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "threshold_analysis.png")
    if save:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
    return path


def plot_pump_timeline(df: pd.DataFrame, save: bool = True) -> str:
    """Step chart showing pump ON/OFF state over time."""
    _ensure_charts_dir()

    if "pump_status" not in df.columns:
        return ""

    pump_numeric = (df["pump_status"] == "ON").astype(int)
    x = df["reading_id"] if "reading_id" in df.columns else range(len(df))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={"height_ratios": [2, 1]})
    fig.patch.set_facecolor("#1A1A2E")
    fig.suptitle("💧 Irrigation Pump Status & Soil Moisture", fontsize=16,
                 fontweight="bold", color="#00E676")

    # Top: Soil moisture with pump overlay
    ax1.set_facecolor("#16213E")
    ax1.plot(x, df["soil_moisture"], color=PALETTE["soil_moisture"],
             linewidth=1.8, label="Soil Moisture (%)")
    ax1.axhline(30, color="#FFC107", linestyle="--", linewidth=1.2, label="Low Threshold (30%)")
    ax1.axhline(65, color="#00BCD4", linestyle="--", linewidth=1.2, label="High Threshold (65%)")
    ax1.fill_between(x, df["soil_moisture"],
                     where=pump_numeric == 1, alpha=0.3, color="#4CAF50", label="Pump ON")
    ax1.set_ylabel("Soil Moisture (%)", color=PALETTE["soil_moisture"])
    ax1.legend(fontsize=9, facecolor="#1A1A2E", labelcolor="#E0E0E0")
    ax1.tick_params(colors="#E0E0E0")

    # Bottom: Pump ON/OFF step chart
    ax2.set_facecolor("#16213E")
    ax2.step(x, pump_numeric, color="#4CAF50", linewidth=2, where="post")
    ax2.fill_between(x, pump_numeric, step="post", alpha=0.4, color="#4CAF50")
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["OFF", "ON"], color="#E0E0E0")
    ax2.set_ylabel("Pump State", color="#E0E0E0")
    ax2.set_xlabel("Reading #")
    ax2.tick_params(colors="#E0E0E0")

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "pump_timeline.png")
    if save:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
    return path


def plot_correlation_matrix(df: pd.DataFrame, save: bool = True) -> str:
    """Heatmap showing correlations between sensor values."""
    _ensure_charts_dir()

    sensors = ["soil_moisture", "temperature", "humidity", "light_intensity", "water_level"]
    available = [s for s in sensors if s in df.columns]
    corr = df[available].corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#1A1A2E")
    ax.set_facecolor("#16213E")

    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
        ax=ax, linewidths=0.5, linecolor="#333",
        annot_kws={"size": 11, "color": "white"},
        cbar_kws={"shrink": 0.8},
    )
    ax.set_title("🔗 Sensor Correlation Matrix", fontsize=14, color="#00E676",
                 pad=15, fontweight="bold")
    ax.tick_params(colors="#E0E0E0", labelsize=9)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "correlation_matrix.png")
    if save:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
    return path


def plot_scenario_distribution(df: pd.DataFrame, save: bool = True) -> str:
    """Pie + bar charts showing scenario distribution."""
    _ensure_charts_dir()

    if "scenario" not in df.columns:
        return ""

    scenario_counts = df["scenario"].value_counts()
    scenario_colors = ["#4CAF50", "#FF5722", "#FFC107", "#2196F3", "#9C27B0", "#00BCD4"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    fig.patch.set_facecolor("#1A1A2E")
    fig.suptitle("📈 Simulation Scenario Distribution", fontsize=15,
                 fontweight="bold", color="#00E676")

    # Pie chart
    ax1.set_facecolor("#16213E")
    wedges, texts, autotexts = ax1.pie(
        scenario_counts.values,
        labels=scenario_counts.index,
        autopct="%1.1f%%",
        colors=scenario_colors[:len(scenario_counts)],
        startangle=140,
        textprops={"color": "#E0E0E0", "fontsize": 10},
        wedgeprops={"edgecolor": "#1A1A2E", "linewidth": 2},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9)
    ax1.set_title("Scenario Breakdown", color="#E0E0E0", fontsize=12)

    # Bar chart
    ax2.set_facecolor("#16213E")
    bars = ax2.bar(
        scenario_counts.index,
        scenario_counts.values,
        color=scenario_colors[:len(scenario_counts)],
        edgecolor="#1A1A2E",
        linewidth=1.5,
    )
    ax2.set_ylabel("Count", color="#E0E0E0")
    ax2.set_xlabel("Scenario", color="#E0E0E0")
    ax2.tick_params(colors="#E0E0E0", axis="both")
    ax2.set_title("Readings per Scenario", color="#E0E0E0", fontsize=12)

    # Value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.3,
                 f"{int(height)}", ha="center", va="bottom",
                 color="#E0E0E0", fontsize=9)

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "scenario_distribution.png")
    if save:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
    return path


def generate_all_charts(csv_path: str) -> dict:
    """
    Generate all visualization charts from a sensor log CSV.
    
    Args:
        csv_path: Path to the sensor_log CSV file
        
    Returns:
        Dictionary of {chart_name: file_path}
    """
    print(f"Loading data from: {csv_path}")
    df = load_csv(csv_path)
    print(f"Loaded {len(df)} readings. Generating charts...")

    charts = {}
    charts["sensor_timeline"]       = plot_sensor_timeline(df)
    charts["threshold_analysis"]    = plot_threshold_analysis(df)
    charts["pump_timeline"]         = plot_pump_timeline(df)
    charts["correlation_matrix"]    = plot_correlation_matrix(df)
    charts["scenario_distribution"] = plot_scenario_distribution(df)

    print(f"\n✓ All charts saved to: {CHARTS_DIR}")
    for name, path in charts.items():
        if path:
            print(f"  [{name}] → {os.path.basename(path)}")

    return charts


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import glob

    # Find the most recent sensor log
    pattern = os.path.join(DATA_DIR, "sensor_log_*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        print("No sensor log CSV found. Run the simulation first:")
        print("  python main.py --demo")
        sys.exit(1)

    latest_csv = files[-1]
    generate_all_charts(latest_csv)
